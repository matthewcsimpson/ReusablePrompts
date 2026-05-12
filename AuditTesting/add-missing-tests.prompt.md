# Add missing tests for a specific target

Write the missing tests for a single component, module, or feature.
Self-contained — makes no assumptions about a curated strategy document or
a prior audit.

If you need to identify *what* is worth testing first, run
`audit-test-coverage.prompt.md` and hand the chosen target into this
prompt.

## Inputs

The user should tell you one of:
- A file path to test (e.g. `components/Cart/cart.tsx`).
- A feature or domain to cover (e.g. "the checkout flow").

If they don't specify, ask before doing anything else. Don't guess a
target.

## Your job

### 1. Establish context

Read, in this order:

- LLM instructions at the repo root and any nested in directories you'll
  touch: `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`,
  `.cursor/rules/**`. These define naming, layout, and language rules
  you must honour.
- The project manifest (`package.json` / `pyproject.toml` / equivalent)
  to identify the test runner and scripts.
- 2–3 existing tests in the same domain as your target. Mirror their
  style exactly: file naming, location pattern (colocated vs.
  `__tests__/` vs. top-level), mock setup, assertion library.
- The source file(s) being tested. Note: exports, side effects, early
  returns, thrown errors, network calls, dependencies that need
  mocking.

### 2. Identify what to cover

For the target, list:

- **Success cases** — what the code is supposed to do when inputs are
  valid. One case per distinct behaviour, not one per line.
- **Failure cases** — what happens with invalid inputs, missing
  preconditions, network errors, permission denied, edge cases. Read
  the code for early returns and `throw` statements — those are your
  failure cases, ready-made.

State the list to the user **before writing** if either:
- You're testing more than one file in this session, or
- The target has more than ~6 cases total.

Sanity-check the plan first. For small single-file targets, you can
proceed straight to writing.

### 3. Write the tests

- Match the project's existing convention exactly. File location,
  naming, imports, mock setup. If `__tests__/` is the pattern, use it.
  If colocated siblings are the pattern, do that. Do not introduce a
  new convention.
- One concern per test. Names that read like sentences
  (`"returns null when the user is unauthenticated"`).
- Mock at module boundaries, not internals. Mock `fetch`, framework
  hooks, third-party SDKs — not the component's own state.
- Assert on observable behaviour: return values, rendered output, calls
  made. Do not assert on internal state shape.
- Honour the LLM instructions: TypeScript rules, import style, naming
  rules (no single-letter variables, etc.), framework-specific
  conventions (automatic JSX runtime, server vs. client components,
  etc.).
- No snapshot tests of UI trees. Snapshots are acceptable for stable
  structured data (normalised view-models, JSON responses) only.

### 4. Verify

Run the project's test command, scoped to the new file if the runner
supports it. Confirm green before declaring done. If the runner does
not support scoping cleanly, run the full suite.

If a test fails because the source has a bug, **do not silently fix
the source.** Surface the failing case to the user and ask how to
proceed. The audit was about coverage; a bug fix is a separate
decision.

### 5. Report

- Target tested (file path or feature).
- New test file(s) created (paths).
- Cases covered — success / failure counts plus the one-line case
  names.
- Run output: pass count, runtime.
- Anything you noticed that should become a future test or a refactor
  but you didn't action.

## Scope discipline

- **One target per session.** Don't expand into adjacent files unless
  they're a direct dependency that must be mocked or stubbed.
- Don't refactor source under test unless the refactor is trivial and
  obviously correct. Flag and ask otherwise.
- Don't add coverage thresholds, snapshot tests for UI, or
  `passWithNoTests`.
- Don't touch CI configuration or test runner config.

## Branch hygiene

If the repo's LLM instructions specify a branching convention (e.g.
"one branch per ticket"), follow it. Otherwise use a descriptive branch
name like `add-tests-<target>` off the project's main branch.
