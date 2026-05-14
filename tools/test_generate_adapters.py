#!/usr/bin/env python3
"""Unit tests for the load-bearing helpers in generate-adapters.py.

Run: `python3 tools/test_generate_adapters.py` (from repo root) or
`python3 -m unittest tools.test_generate_adapters`. CI also runs these
before the drift check.

Covers the small, easy-to-break pieces — the frontmatter parser, slug
derivation, family/variant split, grouping, and the sentinel-merge logic
in `write_codex_agents`. The end-to-end generator path is exercised by
`--check` in CI.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "generate_adapters", HERE / "generate-adapters.py"
)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules["generate_adapters"] = gen
SPEC.loader.exec_module(gen)


class ParseFrontmatterTests(unittest.TestCase):
    def test_no_frontmatter_returns_empty(self) -> None:
        self.assertEqual(gen.parse_frontmatter("# heading\n\nbody\n"), {})

    def test_basic_scalar(self) -> None:
        text = "---\ndescription: hello world\n---\n\nbody"
        self.assertEqual(gen.parse_frontmatter(text), {"description": "hello world"})

    def test_inline_list(self) -> None:
        text = "---\nrelated: [a, b, c]\n---\n"
        self.assertEqual(gen.parse_frontmatter(text), {"related": ["a", "b", "c"]})

    def test_empty_inline_list(self) -> None:
        text = "---\nrelated: []\n---\n"
        self.assertEqual(gen.parse_frontmatter(text), {"related": []})

    def test_quoted_strings_are_unwrapped(self) -> None:
        text = "---\ndescription: \"quoted value\"\nname: 'single'\n---\n"
        self.assertEqual(
            gen.parse_frontmatter(text),
            {"description": "quoted value", "name": "single"},
        )

    def test_comments_and_blank_lines_ignored(self) -> None:
        text = "---\n# this is a comment\n\ndescription: ok\n---\n"
        self.assertEqual(gen.parse_frontmatter(text), {"description": "ok"})

    def test_block_scalar_rejected(self) -> None:
        text = "---\ndescription: |\n  multi-line\n---\n"
        with self.assertRaises(SystemExit):
            gen.parse_frontmatter(text)

    def test_line_without_colon_rejected(self) -> None:
        text = "---\ndescription ok\n---\n"
        with self.assertRaises(SystemExit):
            gen.parse_frontmatter(text)


class SlugAndVariantTests(unittest.TestCase):
    def test_slugify_single_variant(self) -> None:
        self.assertEqual(gen.slugify("audit-test-coverage.prompt.md"), "audit-test-coverage")

    def test_slugify_dotted_variant(self) -> None:
        self.assertEqual(
            gen.slugify("dependency-hygiene.npm.prompt.md"),
            "dependency-hygiene-npm",
        )

    def test_derive_family_variant_single(self) -> None:
        self.assertEqual(
            gen.derive_family_variant("audit-test-coverage.prompt.md"),
            ("audit-test-coverage", ""),
        )

    def test_derive_family_variant_multi(self) -> None:
        self.assertEqual(
            gen.derive_family_variant("dependency-hygiene.npm.prompt.md"),
            ("dependency-hygiene", "npm"),
        )

    def test_derive_family_variant_too_many_dots(self) -> None:
        with self.assertRaises(SystemExit):
            gen.derive_family_variant("foo.bar.baz.prompt.md")


class GroupingTests(unittest.TestCase):
    def _p(self, slug: str, collection: str, family: str = "", variant: str = "") -> gen.Prompt:
        return gen.Prompt(
            slug=slug,
            collection=collection,
            rel_path=f"{collection}/{slug}.prompt.md",
            description="x",
            family=family or slug,
            variant=variant,
        )

    def test_group_by_family_sorts_variants(self) -> None:
        prompts = [
            self._p("dependency-hygiene-python", "DependencyHygiene", family="dependency-hygiene", variant="python"),
            self._p("dependency-hygiene-npm", "DependencyHygiene", family="dependency-hygiene", variant="npm"),
        ]
        grouped = gen.group_by_family(prompts)
        self.assertEqual(
            [p.variant for p in grouped["dependency-hygiene"]],
            ["npm", "python"],
        )

    def test_group_by_collection_sorts_slugs(self) -> None:
        prompts = [
            self._p("zeta", "Foo"),
            self._p("alpha", "Foo"),
        ]
        grouped = gen.group_by_collection(prompts)
        self.assertEqual([p.slug for p in grouped["Foo"]], ["alpha", "zeta"])


class CodexAgentsMergeTests(unittest.TestCase):
    def _prompts(self) -> list[gen.Prompt]:
        return [
            gen.Prompt(
                slug="audit-test-coverage",
                collection="AuditTesting",
                rel_path="AuditTesting/audit-test-coverage.prompt.md",
                description="Audit test coverage.",
                family="audit-test-coverage",
            ),
        ]

    def test_creates_file_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "AGENTS.md"
            gen.write_codex_agents(target, self._prompts(), Path(tmp))
            content = target.read_text()
            self.assertIn(gen.GLOBAL_MARKER_BEGIN, content)
            self.assertIn(gen.GLOBAL_MARKER_END, content)
            self.assertIn("audit-test-coverage", content)

    def test_replaces_existing_managed_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "AGENTS.md"
            target.write_text(
                "user preamble\n\n"
                f"{gen.GLOBAL_MARKER_BEGIN}\nstale\n{gen.GLOBAL_MARKER_END}\n"
                "user epilogue\n"
            )
            gen.write_codex_agents(target, self._prompts(), Path(tmp))
            content = target.read_text()
            self.assertIn("user preamble", content)
            self.assertIn("user epilogue", content)
            self.assertNotIn("stale", content)
            self.assertEqual(content.count(gen.GLOBAL_MARKER_BEGIN), 1)
            self.assertIn("audit-test-coverage", content)

    def test_appends_when_markers_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "AGENTS.md"
            target.write_text("hand-written notes\n")
            gen.write_codex_agents(target, self._prompts(), Path(tmp))
            content = target.read_text()
            self.assertTrue(content.startswith("hand-written notes"))
            self.assertIn(gen.GLOBAL_MARKER_BEGIN, content)


if __name__ == "__main__":
    sys.exit(unittest.main(verbosity=2))
