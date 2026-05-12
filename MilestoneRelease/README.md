# MilestoneRelease

Three prompts that form a milestone-release workflow: drive the app to
catch behavioural regressions, audit the codebase for drift, then
action a triaged subset of the findings.

| Order | Prompt | Mode | What it does |
|---|---|---|---|
| 1 | `post-milestone-smoke-test.prompt.md` | Browser-driven, observation-only | Discovers user-facing changes from the milestone's closed issues, drives them through a browser MCP, records pass / fail / blocked per flow |
| 2 | `post-milestone-audit.prompt.md` | Read-only | Surveys the codebase for convention violations, milestone-diff issues, regression drift, and extraction candidates. Writes a single report file |
| 3 | `post-milestone-fix.prompt.md` | Writes code | Reads the audit report and actions findings matching the triage labels and sections you supply. Commits locally — does not push or open a PR |

## Typical workflow

1. Tag the milestone (`git tag v0.x.y && git push --tags`).
2. Run **smoke test** first — behavioural regressions surface before
   the audit's static findings drown them out.
3. Run **audit** — produces `docs/audits/<tag>.md`.
4. Triage the audit (override the `Suggested:` labels where needed).
5. Run **fix** with the labels and sections you want actioned.
6. Review the local commits, push, open a PR yourself.

## Triage vocabulary

The audit emits a triage suggestion for every ⚠️ ISSUE, and the fix
prompt filters by it:

- `fix-now` — ship in the current cycle.
- `fix-soon` — schedule before the next milestone.
- `defer` — real but not worth fixing yet.
- `accept` — known and not worth changing.

These labels are the contract between the audit and the fix prompt.
If you swap one prompt out, keep the vocabulary or update both.

## Output discipline

All three prompts write to a `docs/` subtree:

- `docs/audits/<tag>.md`
- `docs/smoke-tests/<tag>.md`
- `docs/smoke-tests/screenshots/<tag>/<n>.png`

The `docs/` folder should be gitignored. These are working artefacts,
not tracked history. The audit specifically uses prior reports to
compute a delta — so keeping them locally matters, but committing
them invites churn.

If the project tracks ephemeral artefacts somewhere else, adjust the
paths in the prompts before running.

## Required tool capabilities

All three prompts assume an agentic CLI with:

- File read across the repo.
- Shell execution (git, the project's type-check / lint / test /
  build commands).
- Git branch and commit (fix prompt only).
- File write under `docs/` (smoke and audit prompts).

The smoke prompt additionally requires:

- A browser-control MCP tool (Playwright MCP recommended).
- A running dev server reachable from the browser.
- Seeded test accounts documented somewhere the project can reach.

Designed for Claude Code and Codex CLI. Anything with the same
capability set should work.

## Adapting to a project

The audit prompt's spine is convention compliance — it reads the
project's `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/**` and sweeps
the codebase for each documented rule. The more specific those files
are, the sharper the audit. If a project has nothing documented, the
audit falls back to the generic categories in Step 4 (TypeScript
quality, framework patterns, security regression, etc.) but loses the
project-specific spine.

A reasonable adaptation pattern:

1. First run: audit catches whatever it can from generic categories.
2. Look at what slipped through. Add rules to `CLAUDE.md`.
3. Second run: audit catches the new rules too.

Treat the audit as a feedback loop on the convention documentation,
not just on the code.

## Scope rules baked into the prompts

- Smoke and audit are observation-only. Neither writes code.
- Fix actions only the user-supplied labels and sections — scope
  creep is the failure mode it's defending against.
- Fix stops after committing locally. Pushing and opening a PR are
  human decisions.
- Extraction candidates (💡 EXTRACT) are not actioned by the fix
  prompt unless explicitly triaged as `fix-now` — extraction work
  belongs in its own focused prompts.
