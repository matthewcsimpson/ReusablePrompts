# PRWorkflow

Prompts that surround the act of opening a pull request — pre-merge
checks, PR-body drafting, the kinds of things you want to be sure
of before asking a reviewer to look.

| Prompt | Mode | What it does |
|---|---|---|
| `pre-pr-checklist.prompt.md` | Read-only audit + draft | Runs the project's check suite against the branch, scans the diff for the classes of mistake reviewers can't easily catch (leftover debug, focus markers, secrets, unjustified suppressions, untested changes), and drafts a PR body matching the project's recent merged-PR style. Does not push or open the PR. |

## When to use

Run after you think the branch is done, before you run
`gh pr create`. Catches the things you'd find anyway in CI — but
in-session so you don't burn the CI cycle, and with hygiene checks
CI doesn't run.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns and the assumed tool capabilities. This prompt
needs file read, shell execution, and git.
