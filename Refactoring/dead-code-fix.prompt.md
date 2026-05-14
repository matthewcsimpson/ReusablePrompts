---
description: Action the in-scope findings from the most recent dead-code-audit report. Deletes dead code, verifies the build, commits locally per category. Does not push or open a PR.
related: [dead-code-audit]
---

# Dead code fix

Action the in-scope findings from the most recent `dead-code-audit`
report. Delete the dead code, verify the build still passes, commit
locally per category. Do not push or open a PR.

---

## Inputs

The user supplies:

- **Categories in scope** — any combination of `hard`, `likely`,
  `conditionally`. Default is `hard` only — the audit's "Hard dead"
  bucket is where the LLM was confident enough that mechanical
  deletion is safe. Action `likely` only when the user explicitly
  opts in; treat `conditionally` as opt-in plus a confirmation that
  the dependent deprecated path is also being removed.
- **Specific findings to skip** — optional. The user may have
  triaged the report manually and flagged some entries as
  load-bearing despite the audit's recommendation.

If the user hasn't specified, ask before doing anything else. Don't
guess scope. The audit is opinionated; the fix should be conservative.

---

## Step 1 — Locate the audit

Read `docs/audits/dead-code.md`. If the directory or the report
doesn't exist, surface that and stop — run `/playbook dead-code-audit`
first.

If multiple dead-code reports exist (e.g. timestamped), use the most
recent unless the user named one explicitly.

---

## Step 2 — Filter to scope

For each finding in the report, action it only if **all** of:

- It's under a section matching the in-scope categories (`Hard dead`,
  `Likely dead`, `Conditionally dead`).
- It's not in the user-supplied skip list.
- A pre-deletion grep still confirms zero callers. Re-verify — the
  audit may have been written days ago and the codebase may have
  moved.

Skip anything under `Test-only production code` and `Pattern
observations` — those are diagnostic, not deletion candidates.

---

## Step 3 — Delete each finding, verify, commit

Work through findings grouped by **category** (exports, components,
env vars, branches, deprecated paths). Within each category:

1. Make the deletion. Remove the symbol and any now-orphaned imports
   it pulled in. Don't leave commented-out code or "removed because…"
   trail comments — the commit message carries the why.
2. Run the project's type-check and lint commands (e.g.
   `pnpm check-types && pnpm lint`, `npm run typecheck`,
   `mypy . && ruff check`, `cargo check && cargo clippy`). Infer the
   exact commands from the project manifest.
3. Run the test suite. A passing build with failing tests is not
   acceptable — dead code that the type checker accepted may still
   have been runtime-exercised by tests.
4. If any check fails: revert the deletion in this working tree (do
   not commit it), record the finding under "Skipped — broke checks"
   with the failing command and a one-line guess at why. Move on.
5. If checks pass: stage and commit. One commit per category, or per
   clearly-related cluster within a category. Conventional commit
   message referencing what was removed.

**Grouping rule:** one commit per logical category, not per file. If
five unused exports across five files all fell out of the same dead
deprecated path, they go in one commit ("remove deprecated session
helpers"). If two unused exports come from unrelated features, they
go in two commits.

---

## Step 4 — Env vars and config

Env-var findings (variables in `.env.example` / config schemas never
read) need separate handling — there's no compile-time check that
proves they're dead:

- Grep the variable name across the **whole** repo, including
  deployment configs (`docker-compose*.yml`, `terraform/`, `k8s/`,
  CI workflow files). A var read by deploy infrastructure but not
  application code is not dead.
- If the var is referenced anywhere outside source code, skip it and
  record under "Skipped — referenced outside application code".

Only delete env vars when grep across the whole tree comes back
empty.

---

## Step 5 — Run the full check suite

When all in-scope findings are actioned, run the project's full check
suite from a clean state:

- Type-check
- Lint
- Test
- Build (scoped to the primary app if the project is a monorepo)

A passing check suite is the gate for declaring the fix pass complete.

---

## Step 6 — Report

Output a short summary:

- **Findings actioned** — count per category, with file paths.
- **Findings skipped within scope** — with reason per finding
  ("broke checks: `mypy` reported …", "referenced outside application
  code", "user opted to keep").
- **Approximate LOC removed** — sum across commits.
- **Final check result** — pass / fail with the failing command.
- **Suggested PR title and body summary** — draft for a human to
  paste, not to open.

---

## Constraints

- Do not push to the remote.
- Do not open a PR.
- Do not action `Likely dead` or `Conditionally dead` unless the user
  explicitly opted in. They exist as separate buckets in the audit
  precisely because they need human judgment.
- Do not "improve" code adjacent to the deletion (rename remaining
  symbols, tidy formatting, restructure imports beyond what the
  deletion forced). Scope creep here turns a low-risk fix pass into
  a review burden.
- Do not delete re-export barrels, even if no internal caller imports
  them — they define a public API surface.
- Do not delete stub functions that raise `NotImplemented` /
  `unimplemented!()` / `todo!()` — they're intentional placeholders.
- If a deletion requires changing a public API (exported from the
  package, referenced in a published `.d.ts`, surfaced in OpenAPI),
  stop and flag for human review rather than completing the change.
