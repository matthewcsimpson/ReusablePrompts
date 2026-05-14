---
description: Audit the project's LLM instruction files for vague rules, missing examples, drifted compliance, and mechanical-enforcement opportunities.
---

# Audit CLAUDE.md (or equivalent)

Read the project's LLM instruction files and audit them: which
rules are vague, missing concrete examples, no longer followed by
the code, contradictory, or candidates for mechanical enforcement.
Output a triaged list of doc fixes.

This is the meta-prompt the other audits hint at. When an audit
catches a rule the codebase didn't follow, the real fix may be to
sharpen the rule's wording — not just the code.

## Inputs

None required. The prompt finds and audits whichever LLM
instruction files are present.

## Step 1 — Locate instruction files

Find every file in:

- `CLAUDE.md` at the root and any nested `CLAUDE.md` files.
- `AGENTS.md`.
- `.github/copilot-instructions.md`.
- `.github/instructions/**/*.md`.
- `.cursor/rules/**/*` (or `.cursorrules`).

List which files exist and which you'll be auditing.

If none exist, stop — there's nothing to audit. Surface that and
recommend starting from a minimal `CLAUDE.md` skeleton (language,
naming, testing, contribution).

## Step 2 — Enumerate rules

For each rule in each file, extract:

- The rule's text (paraphrased to one line is fine).
- Its category / section heading (Language, TypeScript, Testing,
  Naming, etc.).
- Whether it has a concrete example (`color` not `colour`) or is
  abstract ("use sensible names").

Number the rules so the report can refer to them.

## Step 3 — Audit each rule

For each rule, evaluate:

1. **Clarity** — could a new contributor (or an LLM) understand
   and apply it without context? "Use idiomatic code" fails. "Use
   arrow functions over `function` declarations except for
   hoisted named exports" passes.

2. **Concreteness** — is there an example or a counter-example?
   Rules without examples are at risk; flag and propose one.

3. **Compliance** — sample 5–10 files relevant to the rule's
   scope. How often is the rule actually followed?
   - **Strong** (≥90%): the rule is enforced (mechanically or
     culturally). Worth keeping as-is.
   - **Mixed** (50–89%): the rule has drifted. Either the rule is
     unrealistic or enforcement has lapsed.
   - **Weak** (<50%): either the rule is wrong (codebase has
     superseded it) or it's been forgotten. Recommend retire,
     reword, or re-enforce.

4. **Mechanical enforcement** — could this rule be enforced by a
   hook (Claude Code, pre-commit), an ESLint / ruff / golangci
   rule, or a CI check? If yes, note the mechanism. Mechanical
   enforcement is stronger than doc-only.

5. **Conflict** — does this rule contradict another rule in the
   same file or a different LLM-instruction file? Does it
   contradict the actual code in a way that suggests it's been
   superseded?

## Step 4 — Identify gaps

Read 3–5 recent merged PRs (`gh pr list --state merged --limit 5`,
then `gh pr view <n>` on each). For each, ask: did the diff
conform to the documented rules, or did it introduce a pattern
the docs don't mention? Patterns recurring across multiple PRs
without documentation are missing rules — the project has a
convention, it just hasn't written it down.

## Step 5 — Report

Output to `docs/audits/claude-md-audit.md`. Structure:

```
# CLAUDE.md audit

Date: <today>
Files audited: <list>
Rules enumerated: <count>

## Rule-by-rule findings

### Rule 1 (Section: <heading>): <one-line text>

- Clarity: ✅ / ⚠️ (proposed rewording: "<text>")
- Concreteness: ✅ / ⚠️ (proposed example: "<example>")
- Compliance: Strong (10/10) / Mixed (6/10) / Weak (2/10)
- Mechanically enforceable: yes via <mechanism> / no
- Conflict: none / conflicts with Rule N: <details>

**Suggested action**: keep / reword / add example / enforce
mechanically / retire

### Rule 2: ...

## Missing rules (observed but undocumented)

Patterns observed in code or recent PRs that aren't documented:

- <pattern> — observed in <files / PRs> — recommend adding under
  <section> as: "<proposed rule text>"

## Mechanical enforcement opportunities

Rules currently doc-only that could be moved to lint / hooks:

- Rule N (<text>) — propose: <hook / ESLint rule / pre-commit
  check>

## Summary

- Rules in strong shape: <n>
- Rules needing rewording / examples: <n>
- Rules drifted (compliance Mixed or Weak): <n>
- Missing rules suggested: <n>
- Mechanical enforcement opportunities: <n>
```

## Constraints

- Do not modify `CLAUDE.md` or any other instruction file. Output
  proposed changes; let the user accept or reject each.
- Be specific. "Make this rule clearer" is rejected; propose the
  new wording.
- If a rule has Strong compliance, that's worth noting — not
  every rule needs a fix. Don't manufacture work.
- When suggesting mechanical enforcement, point at a concrete
  mechanism (a specific hook event, a specific ESLint rule name)
  rather than "enforce this somehow."
- Don't audit rules you can't verify from the code (e.g. "every
  PR must have a linked issue" — that's a process rule, not a
  code rule). Note them as out-of-scope for this audit.
