# Pre-PR checklist

Before opening a pull request, sanity-check the branch is ready to
merge. Run the gates the reviewer will run, plus a few things
reviewers can't easily verify (committed secrets, `.only` / `.skip`
left in tests, unjustified disabled lint rules).

Output a pass / fail checklist and a draft PR body. Does not push,
does not open the PR — the user decides when to ship.

## Inputs

None required. The prompt works against the current branch's diff
relative to the project's default branch (typically `main`).

If the user wants to compare against a different base (`develop`,
a feature branch), they specify it.

## Step 1 — Establish the branch window

Run:

- `git symbolic-ref refs/remotes/origin/HEAD` to find the default
  branch. Fallback to `main`, then `master`.
- `git fetch origin <default-branch>`.
- `git log --oneline <default-branch>..HEAD` for the commits on
  this branch.
- `git diff <default-branch>...HEAD --stat` for the change scope.

If the branch has no commits ahead of the default, surface that
and stop — there's nothing to PR.

## Step 2 — Run the project's check suite

Infer the commands from the project manifest:

- Type-check (`tsc --noEmit`, `mypy`, `pyright`, `cargo check`, etc.).
- Lint (`eslint`, `ruff`, `golangci-lint`, etc.).
- Test (`npm test` / `pnpm test` / `pytest` / `cargo test` /
  `go test ./...`).
- Build (`pnpm build`, `cargo build`, `go build ./...`) — where
  the project has it.

Report pass / fail for each. Capture the failing command and the
first relevant error lines verbatim so the user can act on them.

If any fail, that's a blocker — the PR isn't ready. Stop the
audit after surfacing the failures; the rest is noise until the
build is green.

## Step 3 — Check the commits

For every commit on the branch (`git log <default-branch>..HEAD`):

- **Message style** — matches the project's commit convention.
  Read 5–10 recent commits on the default branch
  (`git log <default-branch> -10 --oneline`) to learn the local
  style (conventional commits, ticket prefixes, plain prose, etc.).
- **Atomic** — each commit is a coherent unit. Flag obvious squash
  candidates (cleanup commits, "fix typo" follow-ups, work-in-
  progress reverts).
- **No secrets in diff** — scan commit content for what looks like
  an API key, token, password, or `.env` content.

## Step 4 — Check the changed code

For files in the diff (`git diff <default-branch>...HEAD`):

- **No leftover debug** — new occurrences of `console.log`,
  `print()` in production paths, `debugger`, `breakpoint()`,
  `pdb.set_trace()`, `dd()`, `dbg!()`, `fmt.Println` in non-CLI
  code, etc.
- **No test focus markers** — `.only`, `.skip`, `xit`,
  `xdescribe`, `it.only`, `fdescribe`, `@pytest.mark.focus`,
  `#[ignore]` added without justification.
- **No suppressed errors without reason** — new `@ts-ignore`,
  `# type: ignore`, `// eslint-disable-next-line`,
  `# noqa: <code>` without an explanatory comment on the same line
  or above.
- **New TODO / FIXME / XXX** — list every one with file and line.
  These may belong in a tracked issue rather than the codebase.
- **Tests added for changed logic** — any new function, route, or
  meaningful branch should have a corresponding test change. Flag
  specific symbols that changed without a test touching them.

## Step 5 — Check the project structure

- **No committed secrets** — scan the diff for `.env*` files,
  files matching `*secret*`, `*credential*`, `*.pem`, `*.key`,
  `*.crt`, `id_rsa*`. If any are tracked, flag them as a blocker.
- **Dependencies** — new entries in `package.json` /
  `pyproject.toml` / `Cargo.toml` / `go.mod` /
  `requirements.txt`? Justified by the diff? Placed in the right
  group (`dependencies` vs `devDependencies` /
  `optional-dependencies.dev` / equivalent)?
- **Lockfile** — if dependencies changed, the lockfile updated
  too?
- **Breaking changes** — any removed exports, renamed public
  APIs, changed function signatures, removed config options,
  database migrations that won't roll back cleanly?

## Step 6 — Draft a PR body

Read 3–5 recent merged PRs on the default branch
(`gh pr list --state merged --limit 5 --base <default>`, then
`gh pr view <n>` on each) to learn the local PR-body style.

Draft a PR body that matches it. The common shape is:

- **Summary** — 1–3 bullet points covering what changed and why
  (not how — the diff is how).
- **Test plan** — bulleted checklist of how to verify, derived
  from the actual changes.
- **Breaking changes** (if any) — explicit callout with migration
  guidance.

## Step 7 — Report

Output a single block:

```
PR pre-flight: <PASS | PASS-WITH-WARNINGS | BLOCKED>

Branch: <branch-name>
Default branch: <default-branch>
Commits ahead: <count>
Files changed: <count>

Checks:
- Type-check:    ✅ / ❌ / ⏭ (skipped — no script)
- Lint:          ✅ / ❌ / ⏭
- Tests:         ✅ / ❌ / ⏭
- Build:         ✅ / ❌ / ⏭

Hygiene:
- Commit style:       ✅ / ⚠️ (<one-line details>)
- No secrets in diff: ✅ / ❌ (<details>)
- No debug left:      ✅ / ⚠️ (<details>)
- No .only / .skip:   ✅ / ⚠️ (<details>)
- Tests for changes:  ✅ / ⚠️ (<details>)
- Deps justified:     ✅ / ⚠️ (<details>)
- Breaking changes:   ✅ / ⚠️ (<details — listed if any>)

Suggested PR title: <title>

Suggested PR body:
<markdown body matching the project's style>

Suggested next step: <"open the PR with `gh pr create ...`" | "fix X then re-run" | etc.>
```

Verdict logic:

- Any `❌` → **BLOCKED**. The PR isn't ready.
- Any `⚠️` but no `❌` → **PASS-WITH-WARNINGS**. User can ship as
  is or address first.
- All `✅` → **PASS**.

## Constraints

- Do not modify any code.
- Do not amend any commits.
- Do not push.
- Do not open the PR — surface the title / body so the user
  copy-pastes or runs `gh pr create` themselves.
- If the check suite fails, stop after Step 2. Running the rest
  of the audit on a failing build wastes the user's time.
- Don't flag stylistic differences in commit messages if the
  project's history shows mixed styles. Match the dominant pattern,
  not a strict template.
