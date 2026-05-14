# Refactoring

Read-only audits that surface refactor opportunities, paired with
opt-in fix prompts that action the in-scope findings.

| Audit | What it finds | Action prompt |
|---|---|---|
| `dead-code-audit.prompt.md` | Exports never imported, components never rendered, env vars never read, branches the type system can't reach, code hiding behind permanently-on / off feature flags. Classified Hard / Likely / Conditionally dead. | `dead-code-fix.prompt.md` |
| `duplicate-logic.prompt.md` | Functions / modules / components doing the same job under different names. Clusters them, recommends a winner per cluster, and notes the migration risk. | `duplicate-code-fix.prompt.md` |

The fix prompts deliberately default to a **narrow** scope:

- `dead-code-fix` defaults to `Hard dead` only. Action `Likely` /
  `Conditionally dead` only when the user explicitly opts in.
- `duplicate-code-fix` defaults to `risk:low` clusters and asks the
  user which to action. It verifies the build between each cluster
  rather than bulk-applying all of them.

Both fix prompts commit locally only — they don't push or open a PR.
The intended flow is: run the audit, read the report, decide which
findings are worth acting on, invoke the fix prompt with that scope.

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
