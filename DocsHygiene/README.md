# DocsHygiene

Audits that keep the project's documentation honest, paired with a
narrow-scope fix prompt that actions the drift findings.

| Prompt | What it does |
|---|---|
| `agent-instructions-audit.prompt.md` | Read-only audit of the project's agent / LLM instruction files (`CLAUDE.md`, `AGENTS.md`, Cursor rules, Copilot instructions, and any nested variants). Auto-detects which files are present and audits them all. Flags vague rules, missing examples, rules the code no longer follows, conflicting rules across files, and rules that could move from doc-only to mechanical enforcement (hooks, lint, pre-commit). |
| `doc-code-drift-audit.prompt.md` | Read-only audit. Documentation versus the code: install / run commands that don't match the manifest, env vars renamed since the doc was written, function signatures that shifted, file paths that no longer exist, example snippets that no longer compile against the current API. |
| `doc-code-drift-fix.prompt.md` | Actions findings from the drift audit. Defaults to `hard` drifts only (provably wrong docs); updates docs to match current code, verifies links / snippets, commits locally per drift type. Does not push. |

## Why this folder exists

Documentation rots silently. Linters check the code; nothing checks
whether the docs still describe it. These prompts close that gap.

Pair them with the broader principle the root README spells out:
the prompts in this repo treat documentation as a *feedback loop*,
not just static reference. Run `agent-instructions-audit` when you find
an audit catching gaps the docs *could* have prevented. Run
`doc-code-drift-audit` after a milestone where many APIs moved, then
`doc-code-drift-fix` to action the hard drifts.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns and the assumed tool capabilities. Both prompts
need file read and shell execution; git is optional.
