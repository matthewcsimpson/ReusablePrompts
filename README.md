# ReusablePrompts

A collection of prompts for agentic coding tools (Claude Code, Codex,
and similar) that have filesystem access, shell execution, and git.

Prompts are grouped into folders by purpose. Each folder has its own
README explaining what's inside and how the prompts there fit together.

## Invocation

These are plain markdown files — no tool-specific format. Pick whichever
pattern fits how you work:

1. **Clone and reference.** Clone this repo somewhere local and point
   your agent at the file:

   ```
   git clone https://github.com/matthewcsimpson/ReusablePrompts.git ~/code/ReusablePrompts
   # then in your agent:
   #   follow ~/code/ReusablePrompts/AuditTesting/audit-test-coverage.prompt.md
   ```

   Best when you'll use the prompts across many projects and want a
   single source of truth you can `git pull` to update.

2. **Copy into the target project.** Copy the prompt file into the repo
   you're working on (e.g. `prompts/audit-test-coverage.prompt.md` or
   `.claude/commands/audit-test-coverage.md` for Claude Code slash
   commands). Commit it alongside the project's other tooling.

   Best when the project's contributors should be able to run the same
   prompt without cloning anything extra, or when you want the prompt
   versioned with the project it audits.

3. **Paste into chat.** Open the prompt file, copy its contents, paste
   into the agent chat, add your target / context underneath.

   Best for one-off use or for tools without filesystem access to this
   repo.

## Target tools

These prompts assume an agentic CLI with file read, shell execution,
and git (branch + commit). Designed against Claude Code and Codex CLI;
anything with the same capability set should work.

## Best with documented conventions

Most prompts here look for project-specific LLM instructions —
`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`,
`.cursor/rules/**` — to understand the conventions they should
enforce or honour. The audit prompts use those rules as the *spine*
of the audit; the test-writing prompts read them to match local
style rather than guess.

A repo with no LLM instructions still works — the prompts fall back
to generic categories — but the project-specific spine collapses. A
short, opinionated `CLAUDE.md` is usually a higher-leverage
investment than tuning the prompts themselves.

If you find an audit catching gaps that documented rules *could*
have prevented, add the rule and re-run. Treat the prompts as a
feedback loop on your convention documentation, not just on the
code.

## Current contents

### `AuditTesting/`

A pair of prompts for working on a repo's test suite.

- `audit-test-coverage.prompt.md` — read-only survey that ranks the
  most important coverage gaps and suggests cases for each.
- `add-missing-tests.prompt.md` — takes one target from the audit (or
  one you name directly) and writes tests for it, matching the
  project's existing conventions.

See [`AuditTesting/README.md`](AuditTesting/README.md) for the full
workflow.

### `MilestoneSmoke/`

Behavioural smoke-test prompts that run after a milestone tag is
cut. Variants target different runtime surfaces (web, …). Run
this before `MilestoneAudit/` so behavioural regressions surface
before static drift.

- `post-milestone-smoke-test.web.prompt.md` — drives the
  milestone's flows through a browser MCP. Web apps only.
- `core/post-milestone-smoke-test.core.prompt.md` — shared
  scaffold (not invoked directly).

See [`MilestoneSmoke/README.md`](MilestoneSmoke/README.md).

### `MilestoneAudit/`

Static-drift audit prompts plus the follow-up fix. Pair with
`MilestoneSmoke/`. Filenames carry a stack tag (`.nextjs`,
`.python`) when a prompt is tied to a particular stack.

- `post-milestone-audit.nextjs.prompt.md` — audit variant for
  Next.js + TypeScript projects.
- `post-milestone-audit.python.prompt.md` — audit variant for
  Python projects (FastAPI / Django / Flask / CLI / library).
- `core/post-milestone-audit.core.prompt.md` — shared scaffold
  (not invoked directly).
- `post-milestone-fix.prompt.md` — actions the audit findings
  matching the labels and sections you specify. Commits locally
  only. Stack-agnostic.

See [`MilestoneAudit/README.md`](MilestoneAudit/README.md) for
the full workflow, how to pick an audit variant, and how to add
a new one.

### `PRWorkflow/`

Pre-merge checks for a pull request branch.

- `pre-pr-checklist.prompt.md` — runs the project's check suite,
  scans the diff for things reviewers can't easily catch (leftover
  debug, focus markers, secrets, unjustified suppressions, missing
  tests), and drafts a PR body. Does not push or open the PR.

See [`PRWorkflow/README.md`](PRWorkflow/README.md).

### `IssueWorkflow/`

Issue-tracker maintenance. Filenames carry a platform tag
(`.github`) — variants for other trackers (GitLab, Linear, Jira)
would sit alongside.

- `audit-duplicate-issues.github.prompt.md` — GitHub variant.
  Surveys open issues for duplicates, clusters them, classifies,
  and recommends an action per cluster. Asks for the target
  `OWNER/REPO` at the start of the run. Stops for confirmation
  before any closure or edit.
- `core/audit-duplicate-issues.core.prompt.md` — shared scaffold
  (not invoked directly).

See [`IssueWorkflow/README.md`](IssueWorkflow/README.md).

### `Refactoring/`

Read-only audits that surface refactor opportunities.

- `duplicate-logic.prompt.md` — finds functions / modules /
  components doing the same job under different names; clusters
  and recommends a winner per cluster.
- `dead-code-audit.prompt.md` — finds exports / components / env
  vars / branches that aren't used. Classifies Hard / Likely /
  Conditionally dead. Pairs with the project's static tool when
  one is configured.

See [`Refactoring/README.md`](Refactoring/README.md).

### `DocsHygiene/`

Audits that keep documentation honest.

- `audit-claude-md.prompt.md` — audits the project's LLM
  instruction files (vague rules, missing examples, drifted
  compliance, mechanical-enforcement opportunities).
- `doc-code-drift.prompt.md` — finds where READMEs / docs / inline
  comments disagree with the actual code.

See [`DocsHygiene/README.md`](DocsHygiene/README.md).

### `Debugging/`

Active-loop debugging prompts (different shape from the audit
prompts elsewhere — these drive a workflow that converges on an
answer).

- `regression-bisect.prompt.md` — given last-known-good, symptom,
  and a reproduction, drives `git bisect` to the breaking commit
  and proposes a fix.

See [`Debugging/README.md`](Debugging/README.md).

## Contributing

Contributions are welcome — both new prompts and improvements to
existing ones.

### Conventions

- **File naming.** Prompt files use `<name>.prompt.md` in
  kebab-case (e.g. `audit-test-coverage.prompt.md`). Folder READMEs
  are plain `README.md`.
- **Folder organisation.** Group prompts by workflow domain (e.g.
  `AuditTesting/`, `MilestoneAudit/`), not by action verb. A new
  workflow domain gets its own folder with a `README.md` that
  explains the workflow and links any companion prompts.
- **Prompt structure.** Aim for the shape used by the existing
  prompts: a short purpose statement, inputs the user must supply,
  numbered steps, an output / report format, and a Constraints
  section that names the failure modes the prompt is defending
  against.
- **Be project-agnostic.** Don't name a specific framework,
  package manager, or repo unless the prompt is genuinely tied to
  one. Reach for the project's `CLAUDE.md` / `AGENTS.md` /
  `.cursor/rules/**` for project-specific rules at runtime instead
  of hard-coding them.

### Proposing a change

1. Open an issue describing the prompt or change you want to make.
   Quick agreement on scope up front saves rework.
2. Fork the repo or create a feature branch
   (`add-<thing>` / `improve-<thing>` / `docs-<thing>`).
3. Make the change. If you're adding a new prompt, add or update the
   folder `README.md` and the entry in the root `README.md` so it's
   discoverable.
4. Open a PR against `main` with a summary and a short test plan
   (e.g. "ran against repo X, audit produced N findings, top-3
   ranked first").
5. The PR will be merged once the change is reviewed. `main` is
   protected — PRs only, no direct pushes.

### Reporting a prompt that didn't work

If a prompt produced a bad result, open an issue with: the prompt
file, the project you ran it against (or a description if private),
the actual output, and what you expected. Concrete failure cases
are the most useful contribution — they're what sharpens these
prompts over time.

## License

MIT — see [`LICENSE`](LICENSE).

## Status

Work in progress. More prompt collections will be added over time.
