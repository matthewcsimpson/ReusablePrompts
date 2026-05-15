---
description: Survey a ClickUp List or Folder for duplicate and near-duplicate tasks; cluster, classify, and recommend an action per cluster. Stops before any closure or edit.
---

# Audit duplicate issues — ClickUp variant

Audit a ClickUp List or Folder for duplicate and near-duplicate
tasks.

**This prompt extends [`core/audit-duplicate-issues.core.prompt.md`](./core/audit-duplicate-issues.core.prompt.md).**
Read the core file first for the workflow shape (Step 0
ask-for-target, Step 2 clustering by overlap signal, Step 3
classification taxonomy, Step 4 reporting format, Step 5 execute
only after user confirmation, plus the Constraints). This file
supplies the ClickUp-specific bits: target scope question,
authentication precondition, and the REST API calls for fetching
/ closing / commenting / editing.

The core uses "issue" as a generic term — in ClickUp, every
"issue" in the core's instructions maps to a **task**.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed platform

- ClickUp workspace.
- Personal API token exported as `CLICKUP_API_TOKEN` (format
  `pk_...`). Get one from
  https://app.clickup.com/settings/apps → "Apps" → "API Token".
- Agent has shell execution to call `curl` (or equivalent HTTP
  client).

Before Step 0, verify the token is present and valid:

```
[ -n "$CLICKUP_API_TOKEN" ] || { echo "CLICKUP_API_TOKEN not set"; exit 1; }
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  https://api.clickup.com/api/v2/user
```

A `200` response means the token works. If the token is missing
or any other status comes back, stop and ask the user to set /
rotate `CLICKUP_API_TOKEN`. Do not attempt to obtain a token
from inside the prompt — that's an interactive flow the user
owns.

---

## §0 — Target format

When Step 0 of the core asks for the target, ask **two** questions
in order:

**Q1 — Scope.** "Should I audit a single **List** or a **Folder**
(all Lists inside it)?"

- **List** is the closest analogue to a GitHub repo's issue
  queue — one bucket of tasks.
- **Folder** sweeps every List inside it and treats the union as
  one pool, which catches duplicates that straddle Lists in the
  same project area.

**Q2 — Identifier.** "Do you have the **ID** or the **name**?"

- **ID** is fastest. Find it in the URL:
  - List: `https://app.clickup.com/{workspace}/v/li/{list_id}`
  - Folder: `https://app.clickup.com/{workspace}/v/f/{folder_id}`
- **Name** works too but requires walking the hierarchy. If the
  user gives a name, resolve it like this:
  1. `GET /team` — list the workspaces this token can see.
  2. If multiple workspaces, ask which one.
  3. `GET /team/{team_id}/space` — list spaces in that workspace.
     If multiple, ask which one.
  4. For a **List** name:
     - `GET /space/{space_id}/folder` — list folders.
     - `GET /folder/{folder_id}/list` for each folder, plus
       `GET /space/{space_id}/list` for folderless Lists.
     - Match by name (case-insensitive). If multiple match, list
       the candidates with their parent Folder and ask which.
  5. For a **Folder** name:
     - `GET /space/{space_id}/folder` — match by name. If
       multiple, list with their parent Space and ask which.

Once resolved, **echo the resolved ID and human-readable path
back to the user before fetching tasks**, e.g.
"Auditing List `Backlog` (id `901234567890`) in Space
`Engineering` of Workspace `Acme`." This is the user's last
chance to correct a wrong target before any data is read.

---

## §1 — Verify and fetch (ClickUp API)

All requests carry `Authorization: $CLICKUP_API_TOKEN` and use
base URL `https://api.clickup.com/api/v2`.

### Verify access

For a **List** target:

```
curl -s -H "Authorization: $CLICKUP_API_TOKEN" \
  "https://api.clickup.com/api/v2/list/{list_id}"
```

For a **Folder** target:

```
curl -s -H "Authorization: $CLICKUP_API_TOKEN" \
  "https://api.clickup.com/api/v2/folder/{folder_id}"
```

Each returns the target's metadata including `statuses` (an array
of `{status, type, orderindex, color}`). **Cache the
`statuses` array** — Step 5 needs it to pick a closed-type
status, and ClickUp's status names are list-specific (no
universal "closed").

If verification returns `401` / `403` / `404`, surface the
status code and stop. The user may need to rotate the token,
join the workspace, or correct the ID.

### Fetch open tasks

For a **List** target, paginate until an empty page:

```
curl -s -H "Authorization: $CLICKUP_API_TOKEN" \
  "https://api.clickup.com/api/v2/list/{list_id}/task?archived=false&include_closed=false&page=0&subtasks=true&include_markdown_description=true"
```

Increment `page` (0, 1, 2, …) until the `tasks` array comes
back empty. ClickUp returns up to 100 tasks per page.

For a **Folder** target:

1. `GET /folder/{folder_id}/list` to get every List in the
   folder.
2. For each List, run the per-List fetch above.
3. Concatenate the results into one task pool. Tag each task
   with its source List name so the report can show "this
   cluster spans Lists X and Y."

Each task in the response has at minimum: `id`, `name` (title),
`text_content` / `markdown_description` (body), `tags` (array of
`{name, ...}`), `status` (`{status, type, ...}`), `assignees`,
`list` (parent), `url`. Map to the core's required fields:

| Core field | ClickUp field |
|---|---|
| Issue number / ID | `id` (also `custom_id` if the workspace uses one) |
| Title | `name` |
| Body | `markdown_description` (fall back to `text_content`) |
| Labels / tags | `tags[].name` |
| Milestone / cycle / iteration | `list.name` (ClickUp Lists fill this role) |
| Assignees | `assignees[].username` |

ClickUp does not have pull requests, so no PR exclusion is
needed.

Report the task count to the user before clustering — same
discipline the core asks for.

---

## §5 — Execute (ClickUp API)

ClickUp closures are status changes, not a separate "close"
action. Pick one closed-type status from the cached `statuses`
array (Step 1):

```
# from cached statuses, pick the entry where type == "closed"
# if multiple closed-type statuses exist (e.g. "Closed" and
# "Cancelled"), ask the user which to use *before* the first
# closure — store the answer and reuse for the rest of the run.
```

If the target list has **no** closed-type status configured,
surface that and stop the closure step. Do not invent a status
name — closures will silently no-op.

### Closures

ClickUp does not bundle close-and-comment in one call, so do it
in two steps, comment first so the trail is in place even if the
status update fails:

```
# 1. Comment with the navigable trail (use task_id, not custom_id)
curl -s -X POST \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/task/{task_id}/comment" \
  -d '{"comment_text": "Closing as duplicate of #{other_id}. See that task for current scope."}'

# 2. Set status to the closed-type status from Step 1
curl -s -X PUT \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/task/{task_id}" \
  -d '{"status": "<closed_status_name>"}'
```

Never close silently — the comment is the navigable trail.

### Body porting

When the keep-task's description should absorb content from the
close-task, do it *before* the closure. ClickUp's `description`
field is markdown:

```
curl -s -X PUT \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/task/{keep_task_id}" \
  -d '{"description": "<merged markdown>"}'
```

The full description is replaced by what you `PUT` — read the
existing one, merge in the close-task's content, then write the
combined result back.

### Cross-linking related-but-distinct tasks

Append a `## Related` section to each task's description.
ClickUp doesn't auto-resolve `#123` syntax across workspaces, so
include the URL too:

```
curl -s -X PUT \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.clickup.com/api/v2/task/{task_id}" \
  -d '{"description": "<existing description>\n\n## Related\n- [{other_task_id}]({other_task_url})"}'
```

The task `url` field from the fetch is the navigable link.

### Optional — the `duplicate` tag

If the workspace uses a `duplicate` tag convention, apply it to
the task being closed *before* changing status, so the
provenance survives even if status filters hide closed tasks:

```
curl -s -X POST \
  -H "Authorization: $CLICKUP_API_TOKEN" \
  "https://api.clickup.com/api/v2/task/{task_id}/tag/duplicate"
```

If the tag doesn't exist yet in the Space, this returns an
error — surface it and skip the tagging step rather than
creating a tag silently.

---

## Rate limits

ClickUp's API rate-limits at 100 requests / minute per token
on the free / personal tier. Pagination of a busy List can chew
through this fast. If a request returns `429`, back off for the
duration in the `X-RateLimit-Reset` header (Unix seconds) and
retry. If it happens repeatedly, surface it — the audit can be
re-run from where it stopped.
