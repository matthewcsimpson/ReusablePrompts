# MilestoneSmoke

Behavioural smoke-test prompts that run after every milestone.
Pair with the sibling [`MilestoneAudit/`](../MilestoneAudit/)
folder, which catches static drift.

Variants target different runtime mediums (web app, API, CLI,
etc.) — the variant you pick depends on what the project exposes.
The user-runnable variants sit at the top of this folder; the
shared scaffold lives in `core/`.

| Prompt | Scope |
|---|---|
| `post-milestone-smoke-test.web.prompt.md` | Web app driven through a browser MCP |
| `post-milestone-smoke-test.api.prompt.md` | HTTP API exercised with `curl` / `httpie` against a running instance |
| `post-milestone-smoke-test.cli.prompt.md` | Non-interactive CLI invoked with concrete args, observing exit code / stdout / stderr / side-effects |
| `post-milestone-smoke-test.ios.prompt.md` | iOS app driven through the iOS Simulator via Maestro or XCUITest |
| `core/post-milestone-smoke-test.core.prompt.md` | Shared scaffold. Not invoked directly. |

## Typical workflow

1. Tag the milestone (`git tag v0.x.y && git push --tags`).
2. Run the **smoke variant** that matches your project's runtime
   surface — produces `docs/smoke-tests/<tag>.md` and any
   artefacts under `docs/smoke-tests/<tag>/`.
3. Run [`MilestoneAudit/`](../MilestoneAudit/) for static drift
   after the smoke test confirms behaviour is intact.

The smoke runs first because the audit is static — it doesn't
notice that an endpoint 500s or a button does nothing. The smoke
catches that; the audit catches everything else.

## Picking a smoke variant

- **Web app** (browser-driven flows):
  `post-milestone-smoke-test.web.prompt.md`.
- **HTTP API** (REST / GraphQL / RPC over HTTP):
  `post-milestone-smoke-test.api.prompt.md`.
- **CLI** (non-interactive binary or script):
  `post-milestone-smoke-test.cli.prompt.md`.
- **iOS** (native app, driven through the iOS Simulator):
  `post-milestone-smoke-test.ios.prompt.md`.
- **Other surfaces** (Android, macOS / watchOS / tvOS, TUI,
  REPL, daemon / background worker): no variant exists yet —
  open a PR to add one, or open an issue if you'd like the
  project to add it.

All variants extend `core/post-milestone-smoke-test.core.prompt.md`
that holds the parts that don't change between mediums (milestone
window, issue bucketing, flow planning shape, pass / fail /
blocked vocabulary, report shape, constraints). The variant
supplies what's medium-specific.

**Invocation note**: if you're pasting a variant into a chat
without filesystem access to the repo, paste the core file first,
then the variant. For clone-and-reference or copy-into-project
invocation, this is transparent.

## Pass / Fail / Blocked

Every flow ends in one of three states, defined the same way
across every variant:

- **Pass** — every step ran, every pass criterion held, no new
  findings.
- **Fail** — a pass criterion didn't hold, or a step couldn't
  complete because of a behavioural defect.
- **Blocked** — a step couldn't complete because of a setup gap
  (test data missing, server returned 503, tool error). Distinct
  from fail; not a regression in the milestone.

This matters for the report's summary and for triaging follow-ups
afterwards.

## Output discipline

Each variant writes:

- A single markdown report at `docs/smoke-tests/<tag>.md`.
- Variant-specific artefacts (screenshots, response logs, command
  transcripts) under `docs/smoke-tests/<tag>/` or similar paths
  the variant specifies.

The `docs/` folder should be gitignored. These are working
artefacts.

## Required tool capabilities

Common across variants:

- File read across the repo.
- Shell execution (git, project test / build commands).
- File write under `docs/`.
- Some way to identify the milestone's closed tickets (default:
  `gh` for GitHub milestones; Linear / Jira equivalents otherwise).

Variant-specific (see each variant's Prerequisites section):

- **Web**: browser-control MCP tool (Playwright MCP recommended),
  running dev server, seeded test accounts.
- **API**: running API instance, `curl` / `httpie`, documented
  test credentials (API key, bearer token, OAuth client, or
  seeded user).
- **CLI**: built / installed binary, documented test fixtures.
- **iOS**: Xcode + iOS Simulator booted, a built `.app` bundle,
  Maestro (recommended) or XCUITest, documented test accounts.

### Adding a new smoke variant

If your project's runtime surface isn't covered:

1. Copy the closest existing variant.
2. Rename to `post-milestone-smoke-test.<medium>.prompt.md`.
3. Replace the **Scope**, **Prerequisites**, **Test data**, §2
   user-facing definition, §3 step shape, §4 mechanics, §5
   cross-cutting checks, and §6 observation fields with
   medium-appropriate content.
4. Leave the reference to
   `core/post-milestone-smoke-test.core.prompt.md` intact — the
   core stays shared.
5. Update this README's variant table.
