# StackUpgrade

Plan a framework / runtime / language version bump. Reads the
upstream release notes, catalogues breaking changes, scans the repo
for affected patterns, surveys available codemods, and produces a
migration plan ranked by risk.

Read-only and stack-agnostic in shape — but the *content* of "what
changed between version N and N+1" is inherently per-stack, so the
collection ships variants keyed to the same stack tags as
[`MilestoneAudit/`](../MilestoneAudit/).

Pairs with [`post-milestone-fix.prompt.md`](../MilestoneAudit/post-milestone-fix.prompt.md)
— the upgrade prompt produces a plan; the fix prompt actions
individual steps. Or run the plan manually and use this prompt to
re-scan after each step.

| Variant | Scope |
|---|---|
| `stack-upgrade.nextjs.prompt.md` | Next.js (App Router and Pages Router majors) |
| `stack-upgrade.nestjs.prompt.md` | NestJS (backend TS framework) |
| `stack-upgrade.python.prompt.md` | Python language version (3.x → 3.y) |
| `stack-upgrade.dotnet.prompt.md` | .NET TFM (6 → 8, 8 → 9, …) |
| `stack-upgrade.react-native.prompt.md` | React Native / Expo SDK bumps |
| `stack-upgrade.swift.prompt.md` | Swift / Xcode / iOS SDK bumps |
| `stack-upgrade.terraform.prompt.md` | Terraform / OpenTofu CLI + major provider bumps |
| `core/stack-upgrade.core.prompt.md` | Shared scaffold — workflow, output format, constraints. Not invoked directly. |

## When to run this

Before starting the upgrade — not during, not after. The deliverable
is a *plan* with concrete file-level findings, a list of codemods
to run, manual changes the codemods miss, and a risk assessment
per breaking change.

For dependency-version bumps (libraries, not framework / runtime),
use [`DependencyAudit/`](../DependencyAudit/) instead. This
prompt is for the spine of the stack — the framework, the language
version, the SDK.

## Picking a variant

Pick the variant matching the version you're upgrading:

- **Next.js 14 → 15**: `stack-upgrade.nextjs.prompt.md`.
- **Python 3.11 → 3.12**: `stack-upgrade.python.prompt.md`.
- **.NET 6 → 8** (or 8 → 9): `stack-upgrade.dotnet.prompt.md`.
- **NestJS 9 → 10**: `stack-upgrade.nestjs.prompt.md`.
- **React Native 0.72 → 0.74** (or Expo SDK 49 → 51):
  `stack-upgrade.react-native.prompt.md`.
- **Swift 5 → 6 / Xcode 15 → 16 / iOS 17 → 18**:
  `stack-upgrade.swift.prompt.md`.
- **Terraform 1.5 → 1.10 / AWS provider 4 → 5**:
  `stack-upgrade.terraform.prompt.md`.

If your stack isn't listed (Go, Rust, Ruby, Java, PHP, Salesforce,
…):

1. Copy the closest variant.
2. Rename to `stack-upgrade.<stack>.prompt.md`.
3. Replace the **Release notes sources**, **Breaking-change
   categories**, and **Codemod survey** sections.
4. Leave the `core/` reference intact.
5. Update this README's variant table and open a PR.

## Required tool capabilities

- File read across the repo.
- Shell execution for grep / static analysis / codemod dry-runs.
- Web access useful but not required — release notes are often
  also discoverable via the package's local docs or via the CLI's
  `--changelog` output.

Designed for Claude Code and Codex CLI; anything with the same
capability set should work.

## Output discipline

Writes to `docs/upgrades/<stack>-<from>-<to>.md`. The `docs/`
folder should be gitignored — these are working artefacts, not
tracked history. Re-runs overwrite the file in place.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns. For paste-mode, paste the core file first, then
the variant — the variant references the core for the workflow
shape.
