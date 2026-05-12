# DocsHygiene

Audits that keep the project's documentation honest. Both prompts
are read-only and report findings; neither modifies any docs or
code.

| Prompt | What it audits |
|---|---|
| `audit-claude-md.prompt.md` | The project's LLM instruction files (`CLAUDE.md`, `AGENTS.md`, Cursor rules, Copilot instructions). Flags vague rules, missing examples, rules the code no longer follows, conflicting rules, and rules that could move from doc-only to mechanical enforcement (hooks, lint, pre-commit). |
| `doc-code-drift.prompt.md` | Documentation versus the code: install / run commands that don't match the manifest, env vars renamed since the doc was written, function signatures that shifted, file paths that no longer exist, example snippets that no longer compile against the current API. |

## Why this folder exists

Documentation rots silently. Linters check the code; nothing checks
whether the docs still describe it. These prompts close that gap.

Pair them with the broader principle the root README spells out:
the prompts in this repo treat documentation as a *feedback loop*,
not just static reference. Run `audit-claude-md` when you find an
audit catching gaps the docs *could* have prevented. Run
`doc-code-drift` after a milestone where many APIs moved.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns and the assumed tool capabilities. Both prompts
need file read and shell execution; git is optional.
