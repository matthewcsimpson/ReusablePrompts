# Post-milestone smoke test — web variant

Drive a web app through a browser MCP server after a milestone tag is
cut. Discover the flows from the milestone's closed issues / tickets,
execute them against a running app, observe console + network during
the runs, and write a pass/fail report.

Do not modify any code. The smoke run is observation and execution —
fixes go in their own follow-up issues.

## Scope

This prompt is **web-app-only**. It assumes:

- The app is reachable through a browser (HTML / JS / network — not
  a CLI, daemon, mobile binary, or library).
- A browser-control MCP tool is available (Playwright MCP
  recommended).
- A running dev server is reachable from the browser.

For CLI tools, libraries, mobile apps, or background workers, this
prompt doesn't apply — those need a different smoke-test shape.
None exists in this repo yet; consider opening an issue or adding
one.

---

## Context

This smoke test runs immediately after a milestone tag is cut, before
the post-milestone audit. The audit catches static drift; it does not
run the code. This step does — by driving the milestone's headline
flows in a real browser, so behavioural regressions surface before
they propagate into the next milestone.

The deliverable is a single markdown report written to
`docs/smoke-tests/<latest-tag>.md`. The `docs/` folder should be
gitignored (or whichever working-artefact directory the project uses)
— the report is a working artefact, not a tracked file.

---

## Prerequisites

The session running this prompt must have:

- A browser-control MCP tool available (Playwright MCP, Puppeteer MCP,
  or chrome-devtools MCP — any tool offering: navigate to URL, fill
  input, click element by role/text/selector, read element text and
  attributes, capture screenshot, read console output, read network
  response codes).
- A running dev server reachable from the browser (typically
  `http://localhost:3000` or similar). If the server isn't running,
  surface that as a blocker and stop — do not attempt to start it from
  this prompt.

If the browser tool is unavailable, surface that and stop. The smoke
test is meaningful only when it actually runs.

### One-time setup — Playwright MCP (recommended)

```bash
# 1. Register the server if it's not already in the user-scope config.
if ! claude mcp list 2>/dev/null | grep -q "^playwright:"; then
  claude mcp add playwright npx @playwright/mcp@latest --scope user
else
  echo "playwright MCP already registered — skipping."
fi

# 2. Install Chromium (idempotent).
npx playwright install chromium

# 3. Verify. The output should list `playwright: ✓ Connected`.
claude mcp list
```

Run these in a regular terminal, not inside an active Claude Code
session. After registering, **start a fresh Claude Code session** from
the repo root before pasting this prompt — MCP servers are loaded at
session start.

Open the new session with an explicit cue so the agent routes through
the MCP tool rather than shell-driven Playwright:

> Use Playwright MCP to navigate to http://localhost:3000 and take a
> screenshot.

Once that confirms the tool is wired up, paste this prompt into the
same session.

## Test accounts

The project must document seeded dev accounts in a known location
(e.g. `docs/test-accounts.md`, a section in `CLAUDE.md`, or passed
into this prompt directly). The expected shape is a table of alias /
email / password rows.

When a flow needs two interacting users (friending, sharing,
comparison), use the first two. When a flow needs a brand-new
unseeded account, surface that explicitly — sign-up flows produce
write-side data the run can't easily reset, so create new accounts
only when the flow specifically tests sign-up itself.

If no test accounts are documented, surface that and stop — guessing
credentials will burn the run.

---

## Step 1 — Establish the milestone window

Run these and use the output to scope the run:

- `git describe --tags --abbrev=0` — the latest tag (the milestone
  being tested).
- `git tag --sort=-creatordate | sed -n '2p'` — the previous tag, as
  the baseline.
- Identify the milestone / sprint / ticket batch matching the latest
  tag. The default mechanism is GitHub milestones:
  - `gh api repos/:owner/:repo/milestones --jq '.[] | select(.title | startswith("v<latest-tag-base>"))'`
  - `gh issue list --state closed --milestone "<milestone title>" --limit 100 --json number,title,labels,closedAt`
  If the project uses Linear, Jira, or another tracker, swap in the
  equivalent: pull the list of completed tickets associated with the
  milestone tag.

If the milestone can't be inferred from the tag, surface that and ask
before proceeding.

---

## Step 2 — Bucket closed issues by feature surface

Read each closed issue's body and bucket it into one of:

- **User-facing feature** — surfaces the user can interact with (a
  new page, modal, flow, button, badge, visibility flag, settings
  tab). These become smoke flows.
- **Behind-the-scenes** — schema migrations, refactors, build/CI
  changes, internal utilities, dependency upgrades, copy edits. These
  do not need their own flows; they will be exercised transitively.
- **Process / docs** — issue housekeeping, README/wiki updates,
  milestone-gate audits. Skip entirely.

Skipped items go in an "Excluded from smoke test" section of the
report so a reviewer can sanity-check the bucketing.

---

## Step 3 — Plan each smoke flow

For each user-facing feature, write a numbered flow plan with:

- **Title** — short imperative ("Sign in as <alias> and finish
  onboarding").
- **Issue refs** — `#N` links to the closed issues this flow
  exercises.
- **Setup** — accounts, prior state, URL to start at.
- **Steps** — concrete browser actions: `Navigate to /...`,
  `Fill #username with "..."`, `Click button "Continue"`, `Wait for
  /<route>`. Each step must be executable by the browser MCP without
  follow-up interpretation. Avoid narrative ("then the user signs
  in") — every step is an action the tool will perform.
- **Pass criteria** — observable conditions that indicate success:
  URL the page lands on, text or role the page surfaces, absence of
  an error banner. Be specific.
- **Probe** — 0–2 short bullets identifying a regression worth
  specifically checking during the flow (e.g. "after the username
  submit, refresh and confirm the user lands on step 2 not step 1").
  Each probe is a sub-flow that gets its own pass/fail.

Order flows from highest-value (closest to the milestone's headline)
to lowest. Authentication and signup go first; obscure edge cases go
last. Cap the list at ~10 flows; combine related sub-flows into a
single multi-step entry rather than splitting.

---

## Step 4 — Execute each flow

For each planned flow, in order:

1. Reset the browser state for the run — close any open tabs, clear
   cookies for the dev origin if the flow needs an unauthed start.
   (Two consecutive flows that both run as the same user don't need a
   reset between them; only reset when the next flow's preconditions
   differ.)
2. Walk the steps using the browser MCP. After each step, confirm the
   expected DOM state before the next step. If a step fails (selector
   not found, navigation didn't fire, unexpected modal blocking),
   record where it failed and stop the flow — do not work around it.
   Move on to the next flow.
3. While the flow runs, observe:
   - **Console** — every error and unexpected warning logged in the
     browser console. A single known-deferred warning is fine; new
     ones are findings.
   - **Network** — every 4xx / 5xx, and any request whose duration
     exceeds ~1.5s without an obvious reason (cold cache, real
     upload). Capture the URL and status.
4. At the end of the flow, evaluate the pass criteria: pass / fail /
   blocked.
   - **Pass** — every step ran, every pass criterion held, no new
     console / network findings.
   - **Fail** — a pass criterion didn't hold, or a step couldn't
     complete because of a behavioural defect.
   - **Blocked** — a step couldn't complete because of a setup gap
     (data missing, dev server returned 503, MCP tool error).
     Distinct from fail; not a regression in the milestone.
5. Capture a screenshot at the moment of decision (success state for
   pass, last-good-state for fail/blocked) and link it from the
   report. Save under `docs/smoke-tests/screenshots/<tag>/<flow-number>.png`.

For each probe (Step 3 sub-bullet), run it as its own mini-flow
against the same flow's setup. Probes get their own pass/fail row in
the report.

---

## Step 5 — Cross-cutting observations

After the per-feature flows, do one targeted run for the cross-cutting
concerns the per-feature runs don't cover well on their own:

- **Layout shell** — visit the top 3–5 most-used signed-in routes.
  For each: no console errors, primary chrome (header / sidebar /
  footer) renders, no obvious style breakage.
- **Anonymous viewer** — sign out. Visit the public routes (landing,
  public profile page, any catalogue / browse view). For each: no
  auth-required redirect on a route that should be public, no 500s.

Every observation is its own pass/fail row.

---

## Step 6 — Write the report

Write the report to `docs/smoke-tests/<latest-tag>.md`. Structure:

```
# Smoke Test — <tag>

Date: <today>
Milestone: <milestone title>
Tag window: <previous-tag>..<latest-tag>
Closed issues in window: <count>

## Summary

<2-3 sentence verdict — overall health, biggest concern, biggest win
since last milestone>

| Result | Count |
|---|---|
| ✅ Pass | N |
| ❌ Fail | N |
| ⏸ Blocked | N |

## Smoke flows

### 1. <Title>

- Issue refs: #N, #M
- Setup: ...
- Steps run: <numbered list of what was actually executed>
- Outcome: ✅ Pass / ❌ Fail / ⏸ Blocked
- Observations:
  - Console: <empty | "1 new error: ..." | etc.>
  - Network: <empty | "POST /api/foo returned 500" | etc.>
  - Screenshot: `docs/smoke-tests/screenshots/<tag>/1.png`
- Probes:
  - <probe description> — ✅/❌
- Fix-now issue title (if Fail): <one-line draft suitable for
  `gh issue create --title`>

### 2. <Title>
...

## Cross-cutting observations

- Layout shell — ✅/❌
  - <details if not pass>
- Anonymous viewer — ✅/❌
  - <details if not pass>

## Excluded from smoke test

<List of closed issues bucketed as behind-the-scenes / process /
docs, with a one-line reason for each.>

## Recommended follow-ups

For every ❌ Fail and every cross-cutting failure, propose a draft
issue:

- ❌ <flow title> — `<draft fix-now issue title>` — <one-sentence
  repro>
```

---

## Constraints

- Do not modify any code. The smoke test only observes and executes.
- Do not write findings to any file other than
  `docs/smoke-tests/<latest-tag>.md` and screenshots under
  `docs/smoke-tests/screenshots/<tag>/`.
- If `docs/smoke-tests/` does not exist, create it.
- Each flow must reference at least one issue / ticket from the
  milestone — that's the trace from "we shipped this" to "we tested
  this."
- Steps must be specific browser actions (URL, selector, action).
  Narrative steps are not acceptable; rewrite them or surface that
  the flow can't be executed.
- A flow that can't be executed because of a setup gap (test data,
  dev server state) is **blocked**, not failed. Do not mark it pass
  to keep the run clean.
- Do not open issues for failures. The recommended-follow-ups section
  drafts the titles so a human (or follow-up prompt) can open them in
  a separate step.
