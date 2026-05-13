# DependencyHygiene

A bundled dependency audit — outdated versions, known vulnerabilities,
unused / missing declarations, lockfile drift, and duplicate versions —
in one report.

These are usually run as separate tools at separate times (`npm
outdated`, `npm audit`, `depcheck`, etc.). The hygiene prompt
consolidates them into one pass with a single prioritised report, so a
transitive CVE on a leaf dep can outrank a missing major version on a
core lib instead of living in a different terminal window.

Variants carry an ecosystem tag (`.npm`, `.python`, `.dotnet`,
`.swift`, `.terraform`) because the commands, manifest formats, and
lockfile shapes differ entirely across package managers. The `.core`
file is the shared scaffold and isn't invoked directly.

| Variant | Manifest | Headline tools |
|---|---|---|
| `dependency-hygiene.npm.prompt.md` | `package.json` (+ npm / pnpm / yarn lockfile) | `npm outdated`, `npm audit`, `npm dedupe`, `knip` / `depcheck` |
| `dependency-hygiene.python.prompt.md` | `pyproject.toml` / `requirements*.txt` | `pip list --outdated`, `pip-audit`, `deptry` |
| `dependency-hygiene.dotnet.prompt.md` | `*.csproj` / `Directory.Packages.props` | `dotnet list package --outdated/--vulnerable/--deprecated` |
| `dependency-hygiene.swift.prompt.md` | `Package.swift` / `Podfile` | `swift package show-dependencies`, `pod outdated` |
| `dependency-hygiene.terraform.prompt.md` | `versions.tf` / `required_providers` | `terraform providers`, `tfsec` / `trivy` |
| `core/dependency-hygiene.core.prompt.md` | Shared scaffold | Not invoked directly. |

## Picking a variant

Pick the variant matching the project's primary package manager. In a
polyglot repo, run multiple variants (one per ecosystem) — the report
header includes the ecosystem tag, so reports don't collide.

If your ecosystem isn't listed (Go modules, Cargo, RubyGems, Composer,
…):

1. Copy the closest variant.
2. Rename to `dependency-hygiene.<ecosystem>.prompt.md`.
3. Replace the commands, manifest paths, and ecosystem gotchas.
4. Leave the `core/` reference intact.
5. Update this README's variant table and open a PR.

## Required tool capabilities

- File read across the repo.
- Shell execution for the ecosystem's CLI.
- No write capability needed — the audit does not modify manifests or
  lockfiles.

Designed for Claude Code and Codex CLI; anything with the same
capability set should work.

## Output discipline

Writes to `docs/audits/dependencies.md`. The `docs/audits/` folder
should be gitignored — these are working artefacts, not tracked
history. Re-runs overwrite the file in place.

## Invocation

See the [root README](../README.md#invocation) for the three supported
patterns. For paste-mode, paste the core file first, then the variant
— the variant references the core for the workflow shape.
