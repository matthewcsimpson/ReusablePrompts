# Audit duplicate issues — GitHub variant

Audit a GitHub repository's open issues for duplicates and
near-duplicates.

**This prompt extends [`core/audit-duplicate-issues.core.prompt.md`](./core/audit-duplicate-issues.core.prompt.md).**
Read the core file first for the workflow shape (Step 0
ask-for-target, Step 2 clustering by overlap signal, Step 3
classification taxonomy, Step 4 reporting format, Step 5 execute
only after user confirmation, plus the Constraints). This file
supplies the GitHub-specific bits: target format, authentication
precondition, and the `gh` commands for fetching / closing /
editing.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed platform

- GitHub repository.
- `gh` CLI installed and on PATH.
- User is already authenticated (`gh auth status` reports a
  logged-in account).
- Agent has shell execution to call `gh`.

Before Step 0, run `gh auth status`. If it reports unauthenticated,
stop and ask the user to authenticate. Do not attempt to run
`gh auth login` from inside the prompt — that's an interactive
flow.

---

## §0 — Target format

When Step 0 of the core asks for the target, the format is
`OWNER/REPO` (e.g. `acme-corp/website`).

Phrase the question as:

> Which repository should I audit? (`OWNER/REPO`, e.g.
> `acme-corp/website`)

---

## §1 — Verify and fetch (GitHub commands)

Verify access:

```
gh repo view OWNER/REPO --json name,owner,isPrivate,viewerPermission
```

If this fails (repo not found, no access), surface the error and
stop. The user may need to re-authenticate or correct the name.

Fetch issues:

```
gh issue list --repo OWNER/REPO --state open --limit 500 --json number,title,labels,milestone,body,assignees
```

If there are more than 500 open issues, add `--paginate` to fetch
all pages. `gh issue list` already excludes pull requests.

---

## §5 — Execute (GitHub commands)

### Closures

```
gh issue close <number> --repo OWNER/REPO --reason "not planned" --comment "Closing as duplicate of #<other>. See that issue for current scope."
```

The `--reason "not planned"` flag marks the issue as closed without
implying completion. The `--comment` leaves a navigable trail —
never close silently.

### Body porting

When the keep-issue's body should absorb content from the
close-issue, do it *before* the closure:

```
gh issue edit <keep> --repo OWNER/REPO --body "<merged body>"
```

### Cross-linking related-but-distinct issues

Append a `## Related` section to each issue body. Body links show
in the issue's header reference list, which makes them more
discoverable than comment-only links:

```
gh issue edit <n> --repo OWNER/REPO --body "<existing body>\n\n## Related\n- #<other>"
```
