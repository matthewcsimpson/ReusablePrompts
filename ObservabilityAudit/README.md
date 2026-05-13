# ObservabilityAudit

A read-only audit of how the codebase logs, traces, and surfaces
errors at runtime. Asks the questions a static-type checker can't:
*does production speak when something goes wrong, and does it tell
the truth?*

Stack-agnostic — the audit's questions (swallowed errors, missing
correlation IDs, log-level mismatches, PII in logs, unhealthy health
checks) are universal across languages and runtimes. The prompt
adapts to whichever logging / tracing / metrics SDK the project
uses.

| Prompt | Scope |
|---|---|
| `observability-audit.prompt.md` | Errors, logging, tracing, metrics, health, sensitive data. One audit, one report. |

## What it looks for

- **Swallowed errors** — empty catches, catch-and-log-only patterns
  that hide failure from downstream callers.
- **Inconsistent log levels** — `error` for routine events, `info`
  for things that should be `warn`.
- **Missing correlation** — request IDs / trace IDs / user IDs not
  propagated through async boundaries.
- **Sensitive data in logs** — credentials, tokens, full request
  bodies containing PII.
- **Unstructured logging** — string interpolation where structured
  fields would let downstream tools filter.
- **Unhealthy health checks** — endpoints that return 200 without
  actually checking downstream dependencies.
- **Untraced outbound calls** — DB / HTTP / queue calls outside a
  span, so the trace tree has gaps.
- **Metrics emitted but unused** — cost without value.
- **Critical paths emitting nothing** — value without cost.

## Required tool capabilities

- File read across the repo.
- Shell execution for grep / static analysis.
- No runtime access needed — the audit is purely static. (A
  companion prompt that exercises behaviour at runtime would belong
  in [`MilestoneSmoke/`](../MilestoneSmoke/).)

Designed for Claude Code and Codex CLI; anything with the same
capability set should work.

## Output discipline

Writes to `docs/audits/observability.md`. The `docs/audits/` folder
should be gitignored — these are working artefacts, not tracked
history. Re-runs overwrite the file in place.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns. No core / variant split — it's a single file.
