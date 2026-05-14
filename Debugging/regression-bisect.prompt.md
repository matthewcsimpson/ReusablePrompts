---
description: Given last-known-good, symptom, and reproduction steps, drive a disciplined git bisect to the breaking commit and propose a fix.
---

# Bisect a regression

Given "this worked at tag / commit X, broken at HEAD, here's how
to reproduce," drive a disciplined bisect: pick a midpoint, run the
repro, narrow, repeat until the breaking commit is found, then
read the diff and propose a fix.

Different shape from the other prompts here — this is an active
loop, not a single-shot audit.

## Inputs

The user supplies:

- **Last known good** — a tag, branch, or commit SHA where the
  behaviour worked.
- **Symptom** — what's broken, concretely. Error message, failing
  test name, observable behaviour that has changed.
- **Reproduction** — the exact commands or steps that demonstrate
  the symptom on HEAD. Ideally a failing test or a single command
  that produces a non-zero exit on failure.

If any of these are missing, ask before proceeding. Bisecting
without a clean repro burns commits and produces unreliable
results.

## Step 1 — Verify the inputs

- Check out HEAD and run the reproduction. Confirm the symptom
  reproduces.
- Check out the last-known-good commit and run the reproduction.
  Confirm the symptom does *not* reproduce.
- Return to HEAD.

If either check fails — HEAD doesn't reproduce, or last-known-good
*also* reproduces — surface that and stop. The bisect can't
proceed from inconsistent endpoints; the user needs to refine
either the repro or the good commit.

If the working tree has uncommitted changes, stash them
(`git stash push -m "bisect-pause"`) and restore at the end.
Bisect doesn't tolerate dirty trees.

## Step 2 — Establish the range

Run:

- `git rev-list <last-good>..HEAD --count` — number of commits in
  range.
- `git rev-list <last-good>..HEAD --reverse` — ordered list,
  oldest first.

If the count is small (under ~10), report it and offer to read
each commit in order rather than bisecting. For small ranges,
linear scanning is often faster than bisect's overhead.

Otherwise proceed with `git bisect`.

## Step 3 — Drive `git bisect`

```bash
git bisect start
git bisect bad HEAD
git bisect good <last-good>
```

At each step:

1. `git bisect` checks out the midpoint.
2. Run the reproduction. Capture stdout / stderr and the exit
   code.
3. Mark `git bisect good` (symptom not present) or
   `git bisect bad` (symptom present).
4. If the midpoint can't be tested (build broken, missing
   dependency from before a tooling change, unrelated test
   failure), use `git bisect skip` and continue.
5. Loop until `git bisect` reports the first bad commit.

Capture each step's commit SHA, the repro outcome (good / bad /
skip), and any notable output. The user will want to audit the
trace.

## Step 4 — Read the breaking commit

Once bisect converges, run `git show <breaking-commit>` and read
both the diff and the commit message.

Ask:

- Is the breakage **intentional** (the commit's purpose) or a
  **side effect** of an unrelated change?
- What in the diff would cause this specific symptom? Be
  specific: cite the line / change.
- Are there related changes elsewhere in the commit that also
  need attention?
- If the bisect landed on a **merge commit**, the cause may be
  in one of the parents and needs a follow-up bisect inside the
  merged branch. Surface this and stop — don't guess which parent.

## Step 5 — Propose a fix

Two cases:

**Side effect** — the breakage was unintended. Propose a minimal
patch that preserves the commit's intended change and restores
the broken behaviour. State the patch as a diff (concrete lines,
not a description). Note any other call sites that may need the
same adjustment.

**Intentional** — the breakage was the point. Surface that and
stop. The "fix" is a product or architectural decision (revert,
adapt callers, accept the new behaviour), not a code patch the
prompt should propose without context.

## Step 6 — Clean up

```bash
git bisect reset
```

Confirm the working tree is back at HEAD. If you stashed changes
in Step 1, restore them (`git stash pop`).

## Step 7 — Report

Output a single block:

```
Regression bisect

Last good: <commit / tag>
First bad: <commit SHA> — <one-line subject>
Bisect span: <n> commits
Bisect steps run: <n> (good: <n>, bad: <n>, skip: <n>)

Cause: <one- to two-sentence diagnosis>

Proposed fix:

<unified diff or "see notes — break is intentional">

Notes:
- <risks, caveats, related call sites>
- <whether the fix needs a test added to lock the behaviour>
```

## Constraints

- Do not modify any code without user approval — output the
  patch, let the user apply.
- Always `git bisect reset` before exiting, even if the user
  cancels or the bisect can't complete. Leaving the repo in a
  bisect state breaks the user's next git operation.
- If you stashed uncommitted changes at Step 1, always restore
  them at Step 6.
- Don't shortcut the bisect by skimming the commit log for a
  "suspicious-looking" commit. Run the actual bisect; the
  surprising commit is the common case.
- If a midpoint fails for a reason unrelated to the symptom
  (build broken, infra issue), use `git bisect skip` — don't
  conflate "can't test" with "good" or "bad."
