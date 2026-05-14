---
description: Run a playbook from the agentic-playbooks library by slug.
argument-hint: <playbook-slug> [user scope or target]
---

You are dispatching to a playbook from the agentic-playbooks library.

The user invoked `/playbook` followed by a slug and an optional
free-form instruction. Parse their message:

1. The first whitespace-delimited token after `/playbook` is the
   playbook **slug**.
2. Everything after that token is the **user scope** — pass it to the
   playbook as additional context / target.

## Dispatch rules

**(a) Help / list flags.** Handle these before any other dispatch:

- If the first token is `--help` or `-h`, **or** the user invoked
  `/playbook` with no arguments at all, print a short usage message
  followed by a compact list of available playbook slugs grouped
  into *single-variant* and *multi-variant families*. Mention the
  `--list` flag for full descriptions. Do not run any playbook.
- If the first token is `--list` or `-l`, print the **full catalog**
  below (every slug with its one-line description, grouped by
  single-variant and multi-variant families with their detection
  signals). Do not run any playbook.

Both flags render directly in the chat — no file is read, no work is
performed.

**(b) Exact slug match.** If the slug is an exact key in the catalog
below (e.g. `audit-test-coverage`, `dependency-hygiene-npm`), open
that file and follow it verbatim. Use the user scope as the target /
additional context the playbook should apply to.

**(c) Family match — auto-detect variant.** If the slug matches a
multi-variant family (e.g. `dependency-hygiene`, `stack-upgrade`),
inspect the working directory for the detection signals listed below.
Pick the variant whose signals match the project's stack and run that
variant's file. If multiple match (a polyglot repo), or none match,
list the candidate variants and ask the user which to run before
proceeding. Never silently pick a variant when the stack is ambiguous.

**(d) Smoke-test variants are usage-driven, not file-tree-driven.**
Variants `-api`, `-cli`, `-ios`, `-web` of `post-milestone-smoke-test`
cannot be inferred from the file tree alone. If the user invokes the
family name `post-milestone-smoke-test` without a variant, ask which
artifact they just shipped (web app, HTTP API, CLI binary, iOS app).

**(e) Unknown slug.** If the slug matches nothing, list the closest
catalog entries (by prefix match on the slug) and ask the user to
clarify. Do not guess. Suggest `/playbook --list` to see all options.

Always treat the linked `.prompt.md` body as authoritative — do not
summarise, paraphrase, or skip steps unless the playbook itself says to.

## Catalog — single-variant playbooks (dispatch directly)

- **`add-missing-tests`** — Write missing tests for a single component, module, or feature, matching the project's existing test conventions.
  File: `../../AuditTesting/add-missing-tests.prompt.md`
  Related: `audit-test-coverage`
- **`audit-claude-md`** — Audit the project's LLM instruction files for vague rules, missing examples, drifted compliance, and mechanical-enforcement opportunities.
  File: `../../DocsHygiene/audit-claude-md.prompt.md`
- **`audit-test-coverage`** — Survey a repository's test coverage from scratch, identify the most important gaps, and present a ranked list of recommendations.
  File: `../../AuditTesting/audit-test-coverage.prompt.md`
  Related: `add-missing-tests`
- **`dead-code-audit`** — Find code that isn't used — exports never imported, components never rendered, branches never reached, env vars never read, permanently-on/off flags. Read-only.
  File: `../../Refactoring/dead-code-audit.prompt.md`
  Related: `dead-code-fix`, `duplicate-logic`
- **`dead-code-fix`** — Action the in-scope findings from the most recent dead-code-audit report. Deletes dead code, verifies the build, commits locally per category. Does not push or open a PR.
  File: `../../Refactoring/dead-code-fix.prompt.md`
  Related: `dead-code-audit`
- **`doc-code-drift`** — Read-only audit that finds places where documentation says one thing and the code does another (outdated commands, renamed env vars, drifted signatures, dead links).
  File: `../../DocsHygiene/doc-code-drift.prompt.md`
- **`duplicate-code-fix`** — Action user-selected clusters from the most recent duplicate-logic report. Migrate callers to the recommended winner, delete losers, verify, commit per cluster. Local commits only.
  File: `../../Refactoring/duplicate-code-fix.prompt.md`
  Related: `duplicate-logic`
- **`duplicate-logic`** — Find functions, modules, or components doing the same job under different names. Cluster, identify a winner, propose consolidations. Read-only — does not action.
  File: `../../Refactoring/duplicate-logic.prompt.md`
  Related: `duplicate-code-fix`, `dead-code-audit`
- **`observability-audit`** — Read-only audit of how a codebase logs, traces, and surfaces errors — swallowed errors, missing correlation IDs, log-level mismatches, PII in logs, dishonest health checks.
  File: `../../ObservabilityAudit/observability-audit.prompt.md`
- **`post-milestone-fix`** — Action the in-scope findings from the most recent post-milestone audit report. Commits locally; does not push or open a PR.
  File: `../../MilestoneAudit/post-milestone-fix.prompt.md`
  Related: `post-milestone-audit-dotnet`, `post-milestone-audit-nestjs`, `post-milestone-audit-nextjs`, `post-milestone-audit-python`, `post-milestone-audit-react-native`, `post-milestone-audit-swift`, `post-milestone-audit-terraform`
- **`pre-pr-checklist`** — Before opening a pull request, run the project's check suite, scan the diff for things reviewers can't easily catch (debug code, secrets, missing tests), and draft a PR body.
  File: `../../PRWorkflow/pre-pr-checklist.prompt.md`
- **`regression-bisect`** — Given last-known-good, symptom, and reproduction steps, drive a disciplined git bisect to the breaking commit and propose a fix.
  File: `../../Debugging/regression-bisect.prompt.md`

## Catalog — multi-variant collections (detect stack, then dispatch)

### `audit-duplicate-issues`

Variants:

- `audit-duplicate-issues-github` — GitHub-hosted issue tracker
  File: `../../IssueWorkflow/audit-duplicate-issues.github.prompt.md`
  Detect: `.github/` directory, `gh` CLI authenticated for an `origin` remote on github.com

### `db-migration-review`

Variants:

- `db-migration-review-alembic` — Alembic (Python + SQLAlchemy migrations)
  File: `../../DBMigrationReview/db-migration-review.alembic.prompt.md`
  Detect: `alembic.ini`, `alembic/` directory
- `db-migration-review-ef-core` — Entity Framework Core (.NET)
  File: `../../DBMigrationReview/db-migration-review.ef-core.prompt.md`
  Detect: `Microsoft.EntityFrameworkCore*` in a `*.csproj`, `Migrations/` folder under a .NET project
- `db-migration-review-prisma` — Prisma
  File: `../../DBMigrationReview/db-migration-review.prisma.prompt.md`
  Detect: `prisma/schema.prisma`, `prisma` in `package.json`
- `db-migration-review-typeorm` — TypeORM
  File: `../../DBMigrationReview/db-migration-review.typeorm.prompt.md`
  Detect: `typeorm` in `package.json`, `ormconfig.{js,json,ts}`

### `dependency-hygiene`

Variants:

- `dependency-hygiene-dotnet` — .NET / C#
  File: `../../DependencyHygiene/dependency-hygiene.dotnet.prompt.md`
  Detect: `*.csproj`, `*.sln`, `global.json`, `Directory.Packages.props`
- `dependency-hygiene-npm` — JavaScript / TypeScript (npm / pnpm / yarn)
  File: `../../DependencyHygiene/dependency-hygiene.npm.prompt.md`
  Detect: `package.json` *and* no Next.js / NestJS / React-Native indicators
- `dependency-hygiene-python` — Python
  File: `../../DependencyHygiene/dependency-hygiene.python.prompt.md`
  Detect: `pyproject.toml`, `requirements.txt`, `Pipfile`, `setup.py`
- `dependency-hygiene-swift` — Swift / iOS / macOS
  File: `../../DependencyHygiene/dependency-hygiene.swift.prompt.md`
  Detect: `Package.swift`, `*.xcodeproj/`, `*.xcworkspace/`
- `dependency-hygiene-terraform` — Terraform / OpenTofu
  File: `../../DependencyHygiene/dependency-hygiene.terraform.prompt.md`
  Detect: `*.tf`, `*.tofu`

### `post-milestone-audit`

Variants:

- `post-milestone-audit-dotnet` — .NET / C#
  File: `../../MilestoneAudit/post-milestone-audit.dotnet.prompt.md`
  Detect: `*.csproj`, `*.sln`, `global.json`, `Directory.Packages.props`
- `post-milestone-audit-nestjs` — NestJS backend
  File: `../../MilestoneAudit/post-milestone-audit.nestjs.prompt.md`
  Detect: `nest-cli.json` or `@nestjs/core` in `package.json`
- `post-milestone-audit-nextjs` — Next.js
  File: `../../MilestoneAudit/post-milestone-audit.nextjs.prompt.md`
  Detect: `next.config.{js,ts,mjs}` or `next` in `package.json`
- `post-milestone-audit-python` — Python
  File: `../../MilestoneAudit/post-milestone-audit.python.prompt.md`
  Detect: `pyproject.toml`, `requirements.txt`, `Pipfile`, `setup.py`
- `post-milestone-audit-react-native` — React Native / Expo
  File: `../../MilestoneAudit/post-milestone-audit.react-native.prompt.md`
  Detect: `app.json` with Expo/RN config, or `react-native` / `expo` in `package.json`
- `post-milestone-audit-swift` — Swift / iOS / macOS
  File: `../../MilestoneAudit/post-milestone-audit.swift.prompt.md`
  Detect: `Package.swift`, `*.xcodeproj/`, `*.xcworkspace/`
- `post-milestone-audit-terraform` — Terraform / OpenTofu
  File: `../../MilestoneAudit/post-milestone-audit.terraform.prompt.md`
  Detect: `*.tf`, `*.tofu`

Related across the family: `post-milestone-fix`

### `post-milestone-smoke-test`

Variants:

- `post-milestone-smoke-test-api` — HTTP API smoke test
  File: `../../MilestoneSmoke/post-milestone-smoke-test.api.prompt.md`
  Detect: usage context — ask the user which artifact applies.
- `post-milestone-smoke-test-cli` — CLI binary smoke test
  File: `../../MilestoneSmoke/post-milestone-smoke-test.cli.prompt.md`
  Detect: usage context — ask the user which artifact applies.
- `post-milestone-smoke-test-ios` — iOS Simulator smoke test
  File: `../../MilestoneSmoke/post-milestone-smoke-test.ios.prompt.md`
  Detect: usage context — ask the user which artifact applies.
- `post-milestone-smoke-test-web` — Web app smoke test (browser MCP)
  File: `../../MilestoneSmoke/post-milestone-smoke-test.web.prompt.md`
  Detect: usage context — ask the user which artifact applies.

### `stack-upgrade`

Variants:

- `stack-upgrade-dotnet` — .NET / C#
  File: `../../StackUpgrade/stack-upgrade.dotnet.prompt.md`
  Detect: `*.csproj`, `*.sln`, `global.json`, `Directory.Packages.props`
- `stack-upgrade-nestjs` — NestJS backend
  File: `../../StackUpgrade/stack-upgrade.nestjs.prompt.md`
  Detect: `nest-cli.json` or `@nestjs/core` in `package.json`
- `stack-upgrade-nextjs` — Next.js
  File: `../../StackUpgrade/stack-upgrade.nextjs.prompt.md`
  Detect: `next.config.{js,ts,mjs}` or `next` in `package.json`
- `stack-upgrade-python` — Python
  File: `../../StackUpgrade/stack-upgrade.python.prompt.md`
  Detect: `pyproject.toml`, `requirements.txt`, `Pipfile`, `setup.py`
- `stack-upgrade-react-native` — React Native / Expo
  File: `../../StackUpgrade/stack-upgrade.react-native.prompt.md`
  Detect: `app.json` with Expo/RN config, or `react-native` / `expo` in `package.json`
- `stack-upgrade-swift` — Swift / iOS / macOS
  File: `../../StackUpgrade/stack-upgrade.swift.prompt.md`
  Detect: `Package.swift`, `*.xcodeproj/`, `*.xcworkspace/`
- `stack-upgrade-terraform` — Terraform / OpenTofu
  File: `../../StackUpgrade/stack-upgrade.terraform.prompt.md`
  Detect: `*.tf`, `*.tofu`

Related across the family: `post-milestone-fix`
