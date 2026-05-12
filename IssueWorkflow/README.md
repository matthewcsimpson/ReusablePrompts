# IssueWorkflow

Prompts for managing the issue tracker — finding duplicates,
triaging stale items, cleaning up the backlog.

| Prompt | What it does |
|---|---|
| `audit-duplicate-issues.prompt.md` | Surveys open issues for duplicates and near-duplicates, clusters them, classifies each cluster (hard duplicate / overlapping / foundation + follow-up / related / false positive), recommends an action. Stops for explicit user confirmation before any closure or edit. |

## Platform scope

These prompts are **GitHub-specific** — they use the `gh` CLI
throughout. For other issue trackers (GitLab, Linear, Jira),
separate platform variants would be needed; none exist in this
repo yet.

## Required tool capabilities

- The `gh` CLI is installed.
- The user is already authenticated (`gh auth status` reports a
  logged-in account). The prompts don't run interactive auth flows
  themselves.
- The agent has shell execution to call `gh`.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns. Each prompt in this folder asks the user for
the target `OWNER/REPO` at the start of the run — there's no need
to be inside the target repo's working directory.
