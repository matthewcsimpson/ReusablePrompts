# Refactoring

Read-only audits that surface refactor opportunities. Neither prompt
actions changes — they produce ranked reports the user (or a
follow-up prompt) can act on selectively.

| Prompt | What it finds |
|---|---|
| `duplicate-logic.prompt.md` | Functions / modules / components doing the same job under different names. Clusters them, recommends a winner per cluster, and notes the migration risk. |
| `dead-code-audit.prompt.md` | Exports never imported, components never rendered, env vars never read, branches the type system can't reach, code hiding behind permanently-on / off feature flags. Classified Hard / Likely / Conditionally dead. |

## Why these aren't "fix" prompts

Both prompts deliberately stop at the report. Refactor decisions
benefit from human judgment per cluster (which version to keep,
whether to consolidate at all), and bulk-applying an LLM's
recommendations across many files compounds small errors. The
intended flow is: run the audit, triage the findings, action one
cluster / file at a time with focused prompts or by hand.

## LLM value-add over static tools

Both prompts pair well with the project's existing static tools
(`knip`, `ts-prune`, `vulture`, `unused`, etc.) rather than
replacing them. The LLM adds:

- **Semantic similarity** that text-based dedup tools miss.
- **Dead branches** the type system can prove unreachable but the
  static tool flagged "in use."
- **Deprecated-path-only callers** — code that's "used" but only
  by code that's itself dead.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns and the assumed tool capabilities. Both prompts
need file read and shell execution; git is optional.
