# AuditTesting

Two prompts that work as a pair to find and fill gaps in a repo's test
suite.

| Prompt | Mode | What it does |
|---|---|---|
| `audit-test-coverage.prompt.md` | Read-only | Surveys the repo, classifies source files as Covered / Partial / Missing, and returns a ranked list of the top gaps with suggested cases. |
| `add-missing-tests.prompt.md` | Writes code | Takes one target (file or feature) and writes tests for it, matching the project's existing conventions. Verifies green before reporting done. |

## Typical workflow

1. Run `audit-test-coverage.prompt.md` against the repo.
2. Pick a target from the ranked list it returns.
3. Hand that target to `add-missing-tests.prompt.md`.
4. Repeat from step 2 as long as the audit findings stay fresh.

Each run is stateless — the audit makes no assumptions about prior runs
or persisted strategy docs, so you can re-run it any time the codebase
has moved.

## How to invoke

See the [root README](../README.md#invocation) for the three supported
patterns (clone-and-reference, copy-into-project, paste-into-chat) and
the assumed tool capabilities.

## Scope rules baked into the prompts

- The audit is read-only — it will not write tests or modify source.
- The executor sticks to one target per session and will not refactor
  source under test, change CI config, or add coverage thresholds.
- Neither prompt persists findings to disk unless you explicitly ask.
