# Post-milestone audit

Examine the codebase and produce a post-milestone audit report. Do not
make any code changes — investigate and report only.

---

## Context

This audit runs after every milestone. The goals are:

1. Catch issues introduced by the latest milestone before they
   compound.
2. Catch slow drift in the rest of the codebase that would otherwise
   go unnoticed.
3. Track convention compliance against the project's documented rules
   (typically `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`,
   or `.cursor/rules/**`) so the rules stay enforced.
4. Produce a delta against the previous audit so triaged-and-deferred
   findings don't keep resurfacing as if they were new.

The deliverable is a single markdown report written to
`docs/audits/<latest-tag>.md`. The `docs/` folder should be gitignored
(or whichever working-artefact directory the project uses) — the
report is for reference, not for the repo history.

---

## Step 1 — Establish the audit window

Run these and use the output to scope the audit:

- `git describe --tags --abbrev=0` — the latest tag (this is the
  milestone being audited).
- `git describe --tags --abbrev=0 HEAD~1 2>/dev/null` or
  `git tag --sort=-creatordate | sed -n '2p'` — the previous tag, as
  the baseline.
- `git diff <previous-tag>..<latest-tag> --stat` — the milestone's
  changed files.
- `ls docs/audits/` — list any prior audit reports.

If a prior audit report exists, read the most recent one before
starting. The new report must include a delta section: what was
resolved, what's still present, what's newly introduced.

If no prior audit exists, note that and treat this as the baseline.

---

## Step 2 — Convention compliance check (highest priority)

This is the spine of the audit. Read every rule the project documents
and check each one explicitly. Report violations as ⚠️ ISSUE with file
path and line number.

### Sourcing the rules

Read every file the project uses to document conventions, in priority
order:

- `CLAUDE.md` at the repo root, and any nested `CLAUDE.md` files
  closer to the code you'll touch.
- `AGENTS.md`.
- `.github/copilot-instructions.md`.
- `.github/instructions/**/*.md`.
- `.cursor/rules/**/*` (or `.cursorrules`).
- `README.md` — skim for contribution conventions.

State which files you found and which rules you'll be checking.
Enumerate them as a checklist before scanning the code, so the audit
can be inspected for completeness later.

If the repo has none of these files, say so explicitly. You'll still
proceed with the categories in Step 4, but the spine of the audit
collapses — the user should know that.

### Per-rule sweep

For each documented rule, do a targeted sweep across the codebase and
report every violation. Common rule categories that need this
treatment (the project may have others):

- **Language / spelling** — locale conventions in code, comments,
  strings, identifiers, DB column names.
- **Language choice** — file extension rules (e.g. TypeScript only,
  no `.js`/`.jsx` outside documented exceptions).
- **Code placement** — monorepo placement rules: which packages own
  which kinds of code; which folders are off-limits for which
  imports.
- **Imports** — alias preferences, banned `../` walks, banned
  deep-internal package imports.
- **Routing** — which file owns request handling / middleware /
  routing logic.
- **Database migrations** — immutability rules; use
  `git log --follow` on each migration file to detect edits after
  initial commit.
- **Naming** — variable / function / file / component naming rules.
- **Functions** — declaration style, helper search-before-write, prop
  drilling thresholds.
- **Components** — required file trio, folder structure, prefix
  conventions, colocation rules.
- **Testing** — required colocated tests, test placement, banned
  test-runner flags (`passWithNoTests`).

Some of these are mechanically checkable with grep/AST; some require
reading and judgment. Use the same ⚠️ ISSUE / 💡 CANDIDATE / 💡 EXTRACT
markers as the rest of the audit. A judgment-call placement is a
candidate, not an issue.

---

## Step 3 — Milestone diff focus

Run a deeper look at files changed in this milestone
(`git diff <previous-tag>..<latest-tag> --name-only`). For these
files specifically, check:

- **New components**: do they follow the project's structural rules
  (prefix, file trio, colocation)?
- **New utilities**: placed correctly per the project's monorepo /
  layering rules? Tested?
- **New API routes**: input validated? Auth checked? Error shape
  consistent with the project's error helper? Ownership of resources
  verified before privileged operations?
- **New client / server boundary directives** (e.g. `'use client'`,
  `"use server"`): genuinely needed, or accidental?
- **New env var reads**: client-side reads use the framework's
  public-env prefix and are accessed only in client components?
- **New dependencies in `package.json` / equivalent manifest**:
  justified, and placed in `dependencies` vs `devDependencies`
  correctly?
- **New TODO / FIXME comments**: list every one with file and line.
- **New `console.log` / `console.warn` / `console.error` calls**: list
  every instance.

This section gets the most attention because milestone-fresh code is
where mistakes are most fixable.

---

## Step 4 — Full-sweep regression check

For the rest of the codebase (files unchanged this milestone), do a
lighter pass for slow drift. Use the two-tier reporting model:

- **Actionable findings**: list in full. These are specific issues
  with a specific fix at a specific location.
- **Pattern observations**: when a single rule produces many
  instances of the same kind, report the count and the 3 worst
  examples rather than enumerating every instance. The drift counter
  in Step 5 captures the totals; this section captures the worst
  offenders.

A finding goes in "actionable" if a follow-up prompt could plausibly
fix it in isolation. A finding goes in "pattern observations" if
fixing it would mean a sweep across many files — those are better
handled as a single sweep prompt than as 40 individual entries.

### TypeScript / language quality
- Non-null assertions (`!`).
- Type assertions (`as SomeType`) suppressing legitimate errors.
- Implicit `any` that should be tightened.
- Other language-specific footguns (unwraps, casts, force-unwraps,
  etc., for whichever language the project uses).

### Framework patterns
- Misplaced client / server boundary directives.
- Effect hooks that could be derived state or event handlers.
- Prop / context drilling deeper than 2 levels.
- Framework-recommended idioms not being used where they apply.

### Routing and pages
- Pages missing required metadata (e.g. `generateMetadata`, OpenGraph
  tags, sitemap entries).
- Hardcoded URLs that should be env vars.
- Image / media components missing dimensions or accessibility
  attributes.

### Data and API
- ORM queries over-fetching fields.
- N+1 query patterns.
- API routes leaking ORM error shapes to the client.

### Styling
- Hardcoded values (colours, spacing, sizing) that should be tokens /
  variables / theme references.
- `!important` declarations.
- Inline `style` props (other than dynamically setting CSS custom
  properties).

### Error handling
- Empty catch blocks or catch-and-log-only.
- Missing try/catch on async route handlers.
- Inconsistent API error response shapes.

### Security (regression check only)
- Routes performing privileged operations without verifying resource
  ownership.
- User IDs taken from request body / query params rather than the
  auth session.
- Server-only env vars accessed in client components.
- User-generated content rendered without sanitisation.

### Dependency hygiene
- Circular imports.
- `devDependencies` used in production code paths.
- Duplicate logic between packages suggesting a missing shared
  utility.

---

## Step 4.5 — Extraction and componentisation

This section asks "is this code at the right altitude?" — independent
of whether it works correctly. The goal is to surface refactor
opportunities that the other sections miss because they pass the
mechanical rules.

For each finding, name the specific candidate (file path, function /
component name, line range) and describe what should be extracted,
where it should go, and why.

### Component decomposition

- Any component file longer than ~250 lines, or with a render
  function longer than ~80 lines. Length isn't automatically wrong,
  but it's a signal worth surfacing.
- Any render function containing nested conditional sub-trees that
  are really separate components in disguise — e.g.
  `{isEditing ? <EditView /> : <DisplayView />}` where each branch
  contains non-trivial inline content.
- Any component containing structurally identical content to another
  component, where a shared primitive would absorb both.
- Any component with three or more state hooks that together describe
  a single coherent piece of state — usually a single reducer or
  custom hook.
- Any component with an effect body longer than ~20 lines, or three
  or more effects — typically a custom hook is hiding in there.

### Logic extraction

- Any function defined inside a component body that is pure (no
  closure over component state) and longer than a few lines — should
  be hoisted to module scope or moved to a `.helpers.ts` (or whatever
  the project's helper convention is).
- Any data-shaping logic (mapping, filtering, grouping, sorting,
  deriving display values) appearing at the top of two or more
  components — should be a shared helper.
- Any inline expressions performing non-trivial computation — should
  be a memo or extracted helper for readability and testability.
- Any block of imperative logic inside an effect that has no
  dependency on framework lifecycle — usually a candidate for a plain
  async function called from the effect.

### Promotion candidates

- Any component used by two or more sections that could move to a
  shared UI package.
- Any component with no section-specific behaviour, no
  framework-specific imports, no browser API usage — even if
  currently single-use, a candidate for the shared UI package if it's
  a reusable primitive.
- Any helper that is pure and could move to a shared utility package.
- Any constant defined in two or more files — should move to a shared
  types or constants module.

### Demotion / scope-creep candidates

- Any shared component that has accumulated section-specific props —
  should move back to its section.
- Any shared helper that has acquired an import from
  framework-specific or browser APIs — should move to the
  platform-specific layer.

### Output format for this section

For each candidate, structure the entry as:

- 💡 **EXTRACT** — `path/to/file.tsx:120-180`, `componentName.handleSubmit` — Describe what's there, what it should become, and where it should live. **Suggested:** `fix-soon` / `defer`.

Use ⚠️ ISSUE only when the current placement is a documented-rule
violation. Otherwise, extraction recommendations are 💡 CANDIDATE /
💡 EXTRACT — they're judgment calls, not rule violations.

---

## Step 5 — Convention drift counter

Produce a small numeric table at the end of the report. Adapt the
rule list to whatever the project documents — the entries below are
common categories to start from, not a fixed list.

| Rule | Violations |
|---|---|
| `function` declarations (where arrow expected) | N |
| Single-letter variables | N |
| `../` imports (where alias expected) | N |
| `console.log/warn/error` in production | N |
| `!important` in styling | N |
| Non-null assertions / force unwraps | N |
| Type assertions suppressing errors | N |
| TODO / FIXME comments | N |
| Components missing required prefix | N |
| Misplaced utilities | N |

If a prior audit exists, show the previous count alongside, with an
arrow:

| Rule | Previous | Current | Δ |
|---|---|---|---|
| `function` declarations | 3 | 7 | ↑ 4 |

A rising number is itself a finding worth calling out in the summary.

---

## Step 6 — Delta against prior audit

If a prior audit exists, produce three lists:

- ✅ **Resolved since last audit** — findings that are no longer
  present.
- ⚠️ **Still present** — findings carried over. For each, note
  whether it was previously triaged as `defer` or `accept` (those are
  not failures; they're just carried), or whether it was `fix-soon`
  or `fix-now` and didn't get done (those are failures).
- 🆕 **Newly introduced** — findings that did not exist in the
  previous audit.

The "newly introduced" list is the most important section of the
entire report. Anything new should be heavily scrutinised because the
milestone introduced it deliberately or accidentally.

---

## Output format

Write the full report to `docs/audits/<latest-tag>.md`. Structure:

```
# Audit — <tag>

Date: <today>
Audit window: <previous-tag>..<latest-tag>
Files changed in window: <count>
Convention sources read: <list of files>

## Summary

<2-3 sentence verdict — overall health, biggest concern, biggest win
since last audit>

## Convention drift counter

<table from Step 5>

## Convention compliance

<grouped by rule, ⚠️ ISSUE / 💡 CANDIDATE entries>

## Milestone diff findings

<grouped by Step 3 category>

## Full-sweep regression findings

<grouped by Step 4 category — actionable findings listed in full,
pattern observations aggregated with top 3 worst>

## Extraction and componentisation

<grouped by Step 4.5 category — 💡 EXTRACT entries>

## Delta against <previous-tag> audit

<three lists from Step 6>

## Triage recommendations

<For every ⚠️ ISSUE in the report, suggest one of:
  - fix-now: ship a fix in the current sprint
  - fix-soon: schedule before next milestone
  - defer: real but not worth fixing yet
  - accept: known and not worth changing
The user will override these, but a recommendation forces the auditor
to commit to a view.>
```

Each finding entry uses this shape:

- ⚠️ ISSUE — `path/to/file.ts:42` — Description in one sentence. **Suggested:** `fix-soon`.
- 💡 CANDIDATE — `path/to/file.ts:42` — Description in one sentence. **Suggested:** `defer`.
- 💡 EXTRACT — `path/to/file.tsx:120-180` — Description. **Suggested:** `fix-soon`.

If a category has no findings, mark it ✅ PASS.

---

## Constraints

- Do not modify any code.
- Do not write findings to any file other than
  `docs/audits/<latest-tag>.md`.
- If `docs/audits/` does not exist, create it.
- Every ⚠️ ISSUE must include a file path and line number.
  "Throughout the codebase" is not acceptable — pick the worst
  offender.
- Every ⚠️ ISSUE must include a triage recommendation.
- Pattern observations in Step 4 must include a count and the 3
  worst examples — do not enumerate every instance.
