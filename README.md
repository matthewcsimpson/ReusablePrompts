# agentic-playbooks

A collection of prompts for agentic coding tools (Claude Code, Codex,
and similar) that have filesystem access, shell execution, and git.

Prompts are grouped into folders by purpose. Each folder has its own
README explaining what's inside and how the prompts there fit together.

## Invocation

The canonical prompts are plain markdown files under each collection
folder (e.g. `AuditTesting/audit-test-coverage.prompt.md`). A
generator emits a single `/playbook` router slash command for each
supported tool — type the slug, the router dispatches.

```
/playbook <slug> [optional scope or target]
/playbook --list              # full catalog with descriptions
/playbook --help              # short usage + slug list
```

For multi-variant families (e.g. `dependency-hygiene` has -dotnet /
-npm / -python / -swift / -terraform variants), pass just the family
name. The agent inspects the working directory to pick the matching
stack; if it's ambiguous, it asks before running.

### One-time setup

```bash
git clone https://github.com/matthewcsimpson/agentic-playbooks.git ~/Projects/agentic-playbooks
cd ~/Projects/agentic-playbooks
python3 tools/generate-adapters.py --install-global    # Claude + Codex, any project
```

That writes:

- `~/.claude/commands/playbook.md` — Claude Code router slash command.
- `~/.claude/skills/<slug>/SKILL.md` × 38 — auto-trigger by description
  match (hidden from the `/` picker via `user-invocable: false`).
- `~/.codex/prompts/playbook.md` — Codex CLI router slash command.
- `~/.codex/AGENTS.md` — Codex CLI user-level catalog (sentinel-bounded;
  any pre-existing content is preserved).

Re-run `--install-global` after `git pull` to refresh. Also re-run if
you move the clone to a different path — the global install bakes in
absolute paths to the source prompts. `--uninstall-global` removes
everything it wrote.

### Claude Code

After `--install-global`, from any project:

```
/playbook --list                              # see every available playbook
/playbook --help                              # short usage
/playbook audit-test-coverage
/playbook add-missing-tests for the api routes
/playbook dependency-hygiene
/playbook stack-upgrade-nextjs
```

- **Discovery** — `/playbook --list` prints the full catalog with
  descriptions; `/playbook --help` (or `/playbook` with no slug) prints
  short usage + the slug list.
- **Exact slug** (`audit-test-coverage`, `dependency-hygiene-npm`,
  `db-migration-review-prisma`, …) → dispatches directly.
- **Family name** (`dependency-hygiene`, `stack-upgrade`,
  `db-migration-review`, `post-milestone-audit`) → Claude detects the
  stack from the working directory and runs the matching variant.
- **Smoke-test family** (`post-milestone-smoke-test`) → can't be
  detected from the file tree; Claude asks which artifact you shipped
  (api / cli / ios / web).
- **Natural language** still works — say "audit my test coverage" and
  the matching skill auto-triggers by description.

Without `--install-global`, you can still use Claude Code from inside
this repo — `.claude/commands/playbook.md` is checked in.

### Codex CLI

```
/prompts:playbook audit-test-coverage
/prompts:playbook dependency-hygiene
```

The `/prompts:` prefix is Codex's namespace for user prompts —
mandatory, not optional. Same dispatch rules as above.

If your Codex version doesn't read `~/.codex/prompts/`, fall back to
the project-local `AGENTS.md` catalog (auto-read when Codex launches
in this directory) and ask by name: "run the `audit-test-coverage`
playbook".

### Cursor

Cursor 1.6+ reads slash commands from `.cursor/commands/<name>.md`.
Unlike Claude Code (`~/.claude/`) and Codex CLI (`~/.codex/`), Cursor
has **no stable user-level path** — the router file must live inside
each project you want to invoke `/playbook` from.

**Easiest way to try it — open this repo in Cursor.** The router is
already checked in at `.cursor/commands/playbook.md`. With no extra
setup, from the Cursor chat panel:

```
/playbook --list
/playbook audit-test-coverage
/playbook dependency-hygiene
```

That works because the router's relative paths
(`../../AuditTesting/...`) resolve correctly inside this repo's tree.

**Using `/playbook` from another project — the catch.** The
checked-in router uses paths relative to this repo's layout. Copying
only `.cursor/commands/playbook.md` into another project will fail
when the agent tries to open a prompt — `../../AuditTesting/...` from
that project's `.cursor/commands/` points at directories that don't
exist there.

Until the generator grows a Cursor-specific install mode that writes
absolute paths (Claude and Codex already get this via
`--install-global`), the practical options are:

1. **Run playbooks from inside this repo.** Open the playbooks repo in
   Cursor, run the playbook there, apply the resulting changes to
   your target project. Works today, zero setup.
2. **Hand-edit a copied router.** Copy
   `.cursor/commands/playbook.md` into the target project's
   `.cursor/commands/` folder, then open it and replace every
   `../../<Collection>/...` path with the absolute path to this repo
   (e.g. `/Users/you/Projects/agentic-playbooks/AuditTesting/...`).
   Re-do the edit when the catalog changes.
3. **Use a tool that supports global install.** Claude Code and Codex
   CLI both pick up `--install-global` and work from any project
   without per-project setup. Cursor lacks the user-level path that
   would make this possible.

### GitHub Copilot Chat (VS Code)

VS Code Copilot Chat reads `.github/prompts/<name>.prompt.md` as a
slash command. There's no global install path — copy this repo's
`.github/prompts/playbook.prompt.md` into your target project's
`.github/prompts/` folder. Then in Copilot Chat:

```
/playbook audit-test-coverage
/playbook dependency-hygiene
```

The `.github/copilot-instructions.md` catalog is also written and
provides natural-language fallback for older Copilot versions.

### Without filesystem access (paste into chat)

Open the prompt file, copy its contents, paste into the agent chat, add
your target / context underneath. Works for any tool, no install
required.

### Copy a prompt into a target project

If you want a specific prompt versioned alongside the project it
audits, copy the `.prompt.md` (and its `core/` sibling if it's a
variant) into that project's `prompts/` folder. The global adapters
aren't needed when the prompt travels with the target project.

## Target tools

These prompts assume an agentic CLI with file read, shell execution,
and git (branch + commit). Designed against Claude Code and Codex CLI;
anything with the same capability set should work.

## A note on token usage

These playbooks are deliberately thorough — they read across a repo,
chase references, and produce structured reports. Expect them to be
**token-heavy** compared to a one-shot prompt. A full
`post-milestone-audit`, `dependency-hygiene`, or `stack-upgrade` run
on a non-trivial repo can consume a large fraction of a context
window and (on metered plans) a non-trivial chunk of usage.

Practical tips to keep the cost in check:

- **Scope the run.** Pass a target ("audit just `src/api/`",
  "dependency-hygiene for the `web/` workspace only") instead of
  letting the prompt sweep the whole repo.
- **Run audits before fixes.** Read-only audits are cheaper than the
  follow-up fix pass — review the audit first, then action only the
  findings worth fixing.
- **Prefer the smallest model that works.** Many of the read-only
  audits work well on a mid-tier model; reserve the top tier for the
  prompts that need deeper reasoning (e.g. `regression-bisect`,
  `duplicate-logic`).
- **Watch the context window.** On very large repos, expect to
  `/compact` (or the equivalent) once or twice through a long audit.

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
cut. Variants target different runtime surfaces. Run this before
`MilestoneAudit/` so behavioural regressions surface before
static drift.

- `post-milestone-smoke-test.web.prompt.md` — drives the
  milestone's flows through a browser MCP. Web apps.
- `post-milestone-smoke-test.api.prompt.md` — exercises HTTP
  endpoints against a running API instance with `curl` /
  `httpie`.
- `post-milestone-smoke-test.cli.prompt.md` — invokes CLI
  commands with concrete args; observes exit code / stdout /
  stderr / side effects.
- `post-milestone-smoke-test.ios.prompt.md` — drives an iOS
  app through the iOS Simulator via Maestro or XCUITest.
- `core/post-milestone-smoke-test.core.prompt.md` — shared
  scaffold (not invoked directly).

See [`MilestoneSmoke/README.md`](MilestoneSmoke/README.md).

### `MilestoneAudit/`

Static-drift audit prompts plus the follow-up fix. Pair with
`MilestoneSmoke/`. Filenames carry a stack tag (`.nextjs`,
`.nestjs`, `.python`, `.dotnet`, `.react-native`, `.swift`,
`.terraform`) when a prompt is tied to a particular stack.

- `post-milestone-audit.nextjs.prompt.md` — Next.js +
  TypeScript front-end / SSR.
- `post-milestone-audit.nestjs.prompt.md` — NestJS backend
  services.
- `post-milestone-audit.python.prompt.md` — Python (FastAPI /
  Django / Flask / CLI / library).
- `post-milestone-audit.dotnet.prompt.md` — .NET / C# (ASP.NET
  Core, EF Core, worker services).
- `post-milestone-audit.react-native.prompt.md` — React Native
  / Expo (cross-platform mobile, JS layer).
- `post-milestone-audit.swift.prompt.md` — Swift / Xcode
  (native iOS / macOS / watchOS / tvOS).
- `post-milestone-audit.terraform.prompt.md` — Terraform /
  OpenTofu infrastructure-as-code.
- `core/post-milestone-audit.core.prompt.md` — shared scaffold
  (not invoked directly).
- `post-milestone-fix.prompt.md` — actions the audit findings
  matching the labels and sections you specify. Commits locally
  only. Stack-agnostic.

See [`MilestoneAudit/README.md`](MilestoneAudit/README.md) for
the full workflow, how to pick an audit variant, and how to add
a new one.

### `StackUpgrade/`

Per-stack version-bump planners. Reads upstream release notes,
scans the repo for affected patterns, surveys available codemods,
and produces a risk-ranked migration plan. Pair with
`MilestoneAudit/`'s `post-milestone-fix.prompt.md` to action the
plan.

- `stack-upgrade.nextjs.prompt.md` — Next.js version bumps.
- `stack-upgrade.nestjs.prompt.md` — NestJS major upgrades.
- `stack-upgrade.python.prompt.md` — Python language version
  (3.x → 3.y).
- `stack-upgrade.dotnet.prompt.md` — .NET TFM (6 → 8, 8 → 9, …).
- `stack-upgrade.react-native.prompt.md` — React Native / Expo
  SDK bumps.
- `stack-upgrade.swift.prompt.md` — Swift / Xcode / iOS SDK.
- `stack-upgrade.terraform.prompt.md` — Terraform / OpenTofu CLI
  + major provider bumps.
- `core/stack-upgrade.core.prompt.md` — shared scaffold (not
  invoked directly).

See [`StackUpgrade/README.md`](StackUpgrade/README.md).

### `PRWorkflow/`

Pre-merge checks for a pull request branch.

- `pre-pr-checklist.prompt.md` — runs the project's check suite,
  scans the diff for things reviewers can't easily catch (leftover
  debug, focus markers, secrets, unjustified suppressions, missing
  tests), and drafts a PR body. Does not push or open the PR.

See [`PRWorkflow/README.md`](PRWorkflow/README.md).

### `DBMigrationReview/`

Pre-merge safety review for database migration files. Catches
unsafe-under-production-load operations: NOT NULL on a populated
table, non-concurrent index on a hot table, FK without an index,
renames that break a rolling deploy. Run on a PR branch before
merge.

- `db-migration-review.prisma.prompt.md` — Prisma migrations.
- `db-migration-review.typeorm.prompt.md` — TypeORM migrations.
- `db-migration-review.alembic.prompt.md` — Alembic migrations.
- `db-migration-review.ef-core.prompt.md` — EF Core migrations.
- `core/db-migration-review.core.prompt.md` — shared scaffold
  (unsafe-operation catalogue, severity model, output format).
  Not invoked directly.

See [`DBMigrationReview/README.md`](DBMigrationReview/README.md).

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

### `DependencyHygiene/`

A bundled dependency audit — outdated versions, known
vulnerabilities, unused / missing declarations, lockfile drift, and
duplicate versions — in one prioritised report. Variants are
ecosystem-specific because the commands and manifest shapes differ.

- `dependency-hygiene.npm.prompt.md` — npm / pnpm / yarn.
- `dependency-hygiene.python.prompt.md` — pip / uv / Poetry / pdm.
- `dependency-hygiene.dotnet.prompt.md` — NuGet.
- `dependency-hygiene.swift.prompt.md` — SPM + CocoaPods.
- `dependency-hygiene.terraform.prompt.md` — provider / module
  versions.
- `core/dependency-hygiene.core.prompt.md` — shared scaffold (not
  invoked directly).

See [`DependencyHygiene/README.md`](DependencyHygiene/README.md).

### `ObservabilityAudit/`

Read-only audit of how the codebase logs, traces, and surfaces
errors at runtime. Stack-agnostic — the questions (swallowed
errors, missing correlation IDs, log-level mismatches, PII in
logs, dishonest health checks) are universal.

- `observability-audit.prompt.md` — single stack-agnostic prompt.

See [`ObservabilityAudit/README.md`](ObservabilityAudit/README.md).

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
4. **Regenerate adapters.** Every user-invocable `.prompt.md` carries
   YAML frontmatter (`description:` + optional `related:`). After
   adding or editing a prompt, run:

   ```
   python3 tools/generate-adapters.py
   ```

   Commit the regenerated `.claude/`, `.cursor/`, `.github/prompts/`,
   `.github/copilot-instructions.md`, and `AGENTS.md` alongside the
   prompt change. CI re-runs the generator with `--check` and fails on
   drift.

   If you added a new multi-variant family, add the variant token to
   `VARIANT_SIGNALS` in `tools/generate-adapters.py` with its detection
   signals — otherwise the generator fails fast on unknown variants.
5. Open a PR against `main` with a summary and a short test plan
   (e.g. "ran against repo X, audit produced N findings, top-3
   ranked first").
6. The PR will be merged once the change is reviewed. `main` is
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

Stable at [v1.0.0](https://github.com/matthewcsimpson/agentic-playbooks/releases/tag/v1.0.0).
New collections and stack variants continue to be added as new
project shapes come up — see the per-folder READMEs for guidance
on adding a variant.
