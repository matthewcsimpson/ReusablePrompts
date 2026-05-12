# Audit duplicate issues

Find duplicate and near-duplicate open issues in a GitHub repository.
Cluster them, classify each cluster, recommend an action per cluster,
and stop before executing — destructive operations (closing, editing)
only happen after explicit user confirmation.

## Scope

This prompt is **GitHub-specific**. It uses the `gh` CLI throughout
and assumes the user is already authenticated (`gh auth status`
reports a logged-in account).

For GitLab, Linear, Jira, or other trackers, this prompt doesn't
apply — those would need their own variants. None exist in this
repo yet.

## Step 0 — Ask for the target repo

Before doing anything else, ask the user:

> Which repository should I audit? (`OWNER/REPO`, e.g.
> `acme-corp/website`)

Do not guess; do not default to the current working directory's
git remote unless the user explicitly says "the repo I'm in." A
wrong target burns context and risks acting on the wrong issues.

Optionally also ask:
- Maximum number of clusters to report (default ~15).

## Step 1 — Verify the repo and fetch open issues

Confirm access:

```
gh repo view OWNER/REPO --json name,owner,isPrivate,viewerPermission
```

If this fails (repo not found, no access), surface the error and
stop. The user may need to re-authenticate or correct the name.

Then fetch issues:

```
gh issue list --repo OWNER/REPO --state open --limit 500 --json number,title,labels,milestone,body
```

If there are >500 open issues, paginate (`--paginate`). `gh issue
list` already excludes pull requests by default.

Report the count so the user knows the scope.

## Step 2 — Cluster candidates

Group issues by overlap signal. Don't rely on title alone:

- **Title similarity** — normalise titles (lowercase, strip
  punctuation, ignore prefixes like `Bug:`, `Fix:`, `[chore]`,
  emoji). Cluster titles that match after normalisation.
- **Body overlap** — same files / components / endpoints
  mentioned, same user-facing symptom, same acceptance criteria.
- **Label overlap** — multiple issues tagged with the same
  combination of feature / area labels describing the same work.
- **Cross-references** — if issue A's body mentions "see also #B",
  treat the pair as a candidate.
- **Meta / sub-issue pattern** — one umbrella ticket vs. several
  granular ones is *not* a duplicate. Flag separately so the user
  can decide whether to keep both, restructure, or convert one
  into a task list on the other.

## Step 3 — Classify each cluster

For each candidate cluster, classify as one of:

- **Hard duplicate** — same intent, same scope. One is clearly
  redundant. Recommend closing the thinner one as a duplicate of
  the more developed one.
- **Overlapping scope** — both have legitimate content but cover
  the same work. Recommend merging the better content into one
  and closing the other.
- **Foundation + follow-up** — one issue covers setup, the other
  covers extensions / non-goals of the first. Recommend
  re-scoping the follow-up to explicitly depend on the
  foundation, and link both ways.
- **Related but distinct** — overlapping vocabulary, different
  work. Recommend cross-links only, no closures.
- **False positive** — surface-level similarity. Drop from the
  report.

## Step 4 — Report findings

Output a single table first:

| Cluster | Issues | Classification | Recommendation |
|---|---|---|---|
| PWA setup | #252, #279 | Foundation + follow-up | Re-scope #279 as follow-up to #252, link both ways |

For each cluster, follow the table with 2–4 lines giving:

- **Overlap signal** — be specific. "Both mention `apps/web/proxy.ts`
  and the redirect 401 symptom" beats "similar topic."
- **Recommended action** — concrete, citing issue numbers.
- **Caveats** — assignments, active milestones, comments from
  users other than the repo owner.

Hard cap at ~15 clusters per pass (or whatever the user supplied
in Step 0). If there are more, surface the top N by confidence and
offer a second pass.

Then **stop**. Do not act until the user picks which clusters to
action and how.

## Step 5 — Execute user-selected actions

Once the user picks, execute only what they confirmed:

### Closures

```
gh issue close <number> --repo OWNER/REPO --reason "not planned" --comment "Closing as duplicate of #<other>. See that issue for current scope."
```

Never close silently. The comment leaves a navigable trail for
anyone who follows a notification back.

### Body porting

When the keep-issue's body lacks content from the close-issue
that's worth preserving, port it across *before* closing the
duplicate:

```
gh issue edit <keep> --repo OWNER/REPO --body "<merged body>"
```

### Cross-linking related-but-distinct issues

Append a `## Related` section to each issue body — body links are
more durable than comments and show in the issue's header
reference list:

```
gh issue edit <n> --repo OWNER/REPO --body "<existing body>\n\n## Related\n- #<other>"
```

After each action, report the issue number actioned and the
command used so the user can audit the trail.

## Constraints

- Treat the open-issues list as authoritative for this run. Don't
  try to infer duplicates from closed issues unless the user asks.
- If the repo uses a `duplicate` label, check existing issues
  already tagged with it before re-flagging — they may have
  already been reviewed.
- Don't recommend closing an issue that has comments from users
  other than the repo owner without flagging the social cost —
  their input gets buried in a closed thread.
- If two issues are duplicates but one is assigned or in an
  active milestone, prefer keeping that one even if the other has
  a better body. Port the body across; don't move the milestone
  or assignment.
- Don't propose more than ~15 clusters per pass. If there are
  more, surface the top 15 by confidence and offer a second pass.
- Do not close, edit, or comment on any issue without user
  confirmation. Closures are hard to reverse from the user's
  perspective (notifications fire, the issue drops out of the
  open queue) and silent edits hide the trail.
- If `gh auth status` reports unauthenticated, stop and ask the
  user to authenticate. Do not attempt to authenticate from
  inside the prompt — that's an interactive flow.
