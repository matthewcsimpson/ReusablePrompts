# IssueWorkflow

Prompts for managing the issue tracker — finding duplicates,
triaging stale items, cleaning up the backlog.

Filenames carry a platform tag (`.github`) when a prompt is tied
to a specific tracker. The `.core` files are shared scaffolds that
the platform variants reference; they're not invoked directly.

| Prompt | Scope | What it does |
|---|---|---|
| `audit-duplicate-issues.github.prompt.md` | GitHub | Extends the core with the GitHub-specific commands (`gh repo view`, `gh issue list`, `gh issue close`, `gh issue edit`) and the `OWNER/REPO` target format. |
| `audit-duplicate-issues.clickup.prompt.md` | ClickUp | Extends the core with ClickUp REST API calls (List / Folder targets, status-based closures, comment-then-close ordering, markdown description porting). |
| `core/audit-duplicate-issues.core.prompt.md` | Shared scaffold | Workflow shape, clustering signals, classification taxonomy, output format, constraints. Not invoked directly. |

## Picking a variant

- **GitHub**: `audit-duplicate-issues.github.prompt.md`.
- **ClickUp**: `audit-duplicate-issues.clickup.prompt.md`.
- **GitLab / Linear / Jira / other**: copy the closest variant,
  rename to `.gitlab` / `.linear` / `.jira`, adapt the §0 target
  format and §1 / §5 commands. Open an issue / PR if you'd like
  the variant upstreamed.

The `/playbook` router treats `audit-duplicate-issues` as a
usage-driven family (no file-tree auto-detect — a repo can have
`.github/` for Actions but use ClickUp for tickets). Invoking the
family name without a variant prompts for which tracker; passing
the full slug bypasses the prompt.

## Required tool capabilities

The **GitHub variant** assumes:

- The `gh` CLI is installed.
- The user is already authenticated (`gh auth status` reports a
  logged-in account). The prompts don't run interactive auth
  flows themselves.
- The agent has shell execution to call `gh`.

The **ClickUp variant** assumes:

- A personal API token exported as `CLICKUP_API_TOKEN` (format
  `pk_...`). Get one from
  https://app.clickup.com/settings/apps. The prompt verifies the
  token by calling `GET /user` before doing anything else.
- The agent has shell execution to call `curl` (or equivalent
  HTTP client).

Future platform variants will list their own preconditions.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns. Each variant asks the user for the target at
the start of the run — there's no need to be inside the target
repo's working directory.

**Paste-mode caveat**: if pasting a variant into a chat without
filesystem access, paste the core file first, then the variant.
For clone-and-reference or copy-into-project invocation, the
agent reads both files itself.
