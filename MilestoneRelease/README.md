# MilestoneRelease

A milestone-release workflow: drive the app to catch behavioural
regressions, audit the codebase for drift, then action a triaged
subset of the findings.

Some steps have framework-specific variants. Filenames carry a scope
tag (`.web`, `.nextjs`, `.python`) when a prompt is tied to a
particular stack. Untagged prompts are stack-agnostic.

| Order | Prompt | Scope | What it does |
|---|---|---|---|
| 1 | `post-milestone-smoke-test.web.prompt.md` | Web apps only | Drives the milestone's user-facing flows through a browser MCP, records pass / fail / blocked per flow |
| 2a | `post-milestone-audit.core.prompt.md` | Shared scaffold | Not invoked directly. Holds the workflow shape, convention-source discovery, delta logic, output format, and constraints |
| 2b | `post-milestone-audit.nextjs.prompt.md` | Next.js + TypeScript | Extends the core with Next.js / React / TS-specific milestone-diff focus, regression sweeps, extraction signals, and drift counter |
| 2b | `post-milestone-audit.python.prompt.md` | Python (FastAPI / Django / Flask / CLI) | Extends the core with Python-specific milestone-diff focus, regression sweeps, extraction signals, and drift counter |
| 3 | `post-milestone-fix.prompt.md` | Stack-agnostic | Reads the audit report and actions findings matching the triage labels and sections you supply. Commits locally — does not push or open a PR |

## Picking an audit variant

The audit comes in framework-flavoured variants because the
*regression categories* and *extraction signals* differ
substantially across stacks — a "useEffect body too long" check is
meaningless in Python; a "missing `select_related`" check is
meaningless in Next.js.

- **Next.js + TypeScript**:
  `post-milestone-audit.nextjs.prompt.md`.
- **Python (FastAPI / Django / Flask / CLI / library)**:
  `post-milestone-audit.python.prompt.md`.
- **Other stack (Go, Rust, Ruby, Java, …)**: copy the closest
  variant, adapt the framework-specific sections, and consider
  opening a PR to add the new variant here.

Both variants extend a shared `post-milestone-audit.core.prompt.md`
that holds the parts that don't change between stacks (audit-window
logic, sourcing convention docs, delta against prior audit, output
format, constraints). The variant prompt tells the agent to read the
core file first.

**Invocation note:** if you're pasting a variant into a chat without
filesystem access to the repo, paste the core file first, then the
variant. For clone-and-reference or copy-into-project invocation,
this is transparent — the agent reads both files itself.

## Typical workflow

1. Tag the milestone (`git tag v0.x.y && git push --tags`).
2. Run **smoke test** (`.web` variant for web apps; no variant
   exists yet for other shapes) — behavioural regressions surface
   before the audit's static findings drown them out.
3. Run the **audit variant** that matches your stack — produces
   `docs/audits/<tag>.md`.
4. Triage the audit (override the `Suggested:` labels where needed).
5. Run **fix** with the labels and sections you want actioned.
6. Review the local commits, push, open a PR yourself.

## Triage vocabulary

The audit emits a triage suggestion for every ⚠️ ISSUE, and the fix
prompt filters by it:

- `fix-now` — ship in the current cycle.
- `fix-soon` — schedule before the next milestone.
- `defer` — real but not worth fixing yet.
- `accept` — known and not worth changing.

These labels are the contract between the audit and the fix prompt.
If you swap one prompt out, keep the vocabulary or update both.

## Output discipline

All three prompts write to a `docs/` subtree:

- `docs/audits/<tag>.md`
- `docs/smoke-tests/<tag>.md`
- `docs/smoke-tests/screenshots/<tag>/<n>.png`

The `docs/` folder should be gitignored. These are working artefacts,
not tracked history. The audit specifically uses prior reports to
compute a delta — so keeping them locally matters, but committing
them invites churn.

If the project tracks ephemeral artefacts somewhere else, adjust the
paths in the prompts before running.

## Required tool capabilities

All three prompts assume an agentic CLI with:

- File read across the repo.
- Shell execution (git, the project's type-check / lint / test /
  build commands).
- Git branch and commit (fix prompt only).
- File write under `docs/` (smoke and audit prompts).

The smoke prompt additionally requires:

- A browser-control MCP tool (Playwright MCP recommended).
- A running dev server reachable from the browser.
- Seeded test accounts documented somewhere the project can reach.

Designed for Claude Code and Codex CLI. Anything with the same
capability set should work.

## Adapting to a project

The audit's spine is convention compliance — the variant reads the
project's `CLAUDE.md` / `AGENTS.md` / `.cursor/rules/**` and sweeps
the codebase for each documented rule. The more specific those files
are, the sharper the audit. If a project has nothing documented, the
audit falls back to the variant's regression categories (type quality,
framework patterns, security regression, etc.) but loses the
project-specific spine.

A reasonable adaptation pattern:

1. First run: audit catches whatever it can from the variant's
   regression categories.
2. Look at what slipped through. Add rules to `CLAUDE.md`.
3. Second run: audit catches the new rules too.

Treat the audit as a feedback loop on the convention documentation,
not just on the code.

### Adding a new audit variant

If the existing variants don't fit your stack, add a new one:

1. Copy the closest variant (e.g. `.nextjs` for a TS-on-Express
   project, `.python` for a Ruby / Go project).
2. Rename to `post-milestone-audit.<stack>.prompt.md`.
3. Replace the **Assumed stack**, **§3**, **§4**, **§4.5**, and
   **§5** sections with stack-appropriate content.
4. Leave the reference to `post-milestone-audit.core.prompt.md`
   intact — the core stays shared.
5. Update this README's variant table and "Picking an audit
   variant" section.

## Scope rules baked into the prompts

- Smoke and audit are observation-only. Neither writes code.
- Fix actions only the user-supplied labels and sections — scope
  creep is the failure mode it's defending against.
- Fix stops after committing locally. Pushing and opening a PR are
  human decisions.
- Extraction candidates (💡 EXTRACT) are not actioned by the fix
  prompt unless explicitly triaged as `fix-now` — extraction work
  belongs in its own focused prompts.
