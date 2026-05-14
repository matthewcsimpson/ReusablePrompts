# AGENTS.md

Index of reusable prompts in the agentic-playbooks library, for
agent-aware tools (Codex CLI, OpenCode, Aider, and others that
auto-read `AGENTS.md`).

**Invocation pattern** — every supported tool exposes one router slash
command that takes a slug:

- Codex CLI: `/prompts:playbook <slug> [user scope]`
- Natural language (any agent that reads this file): "run the
  `<slug>` playbook against <target>".

For multi-variant families (e.g. `dependency-hygiene`), pass just the
family name and the agent will inspect the working directory to pick
the right variant.

Canonical sources live in the per-collection folders. The router
shims under `.claude/`, `.cursor/`, `.github/`, and this file are
generated from those sources by `tools/generate-adapters.py`.

## AuditTesting

- **`add-missing-tests`** — Write missing tests for a single component, module, or feature, matching the project's existing test conventions.
  Path: `AuditTesting/add-missing-tests.prompt.md`
  Related: `audit-test-coverage`
- **`audit-test-coverage`** — Survey a repository's test coverage from scratch, identify the most important gaps, and present a ranked list of recommendations.
  Path: `AuditTesting/audit-test-coverage.prompt.md`
  Related: `add-missing-tests`

## DBMigrationReview

- **`db-migration-review-alembic`** — Pre-merge safety review for Alembic database migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
  Path: `DBMigrationReview/db-migration-review.alembic.prompt.md`
- **`db-migration-review-ef-core`** — Pre-merge safety review for Entity Framework Core migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
  Path: `DBMigrationReview/db-migration-review.ef-core.prompt.md`
- **`db-migration-review-prisma`** — Pre-merge safety review for Prisma Migrate migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
  Path: `DBMigrationReview/db-migration-review.prisma.prompt.md`
- **`db-migration-review-typeorm`** — Pre-merge safety review for TypeORM migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
  Path: `DBMigrationReview/db-migration-review.typeorm.prompt.md`

## Debugging

- **`regression-bisect`** — Given last-known-good, symptom, and reproduction steps, drive a disciplined git bisect to the breaking commit and propose a fix.
  Path: `Debugging/regression-bisect.prompt.md`

## DependencyHygiene

- **`dependency-hygiene-dotnet`** — Audit a .NET / NuGet project for outdated versions, known vulnerabilities, unused or missing declarations, lockfile drift, and duplicate versions.
  Path: `DependencyHygiene/dependency-hygiene.dotnet.prompt.md`
- **`dependency-hygiene-npm`** — Audit a JavaScript / TypeScript project (npm, pnpm, or yarn) for outdated versions, vulnerabilities, unused or missing declarations, lockfile drift, and duplicates.
  Path: `DependencyHygiene/dependency-hygiene.npm.prompt.md`
- **`dependency-hygiene-python`** — Audit a Python project (pip, uv, Poetry, or pdm) for outdated versions, vulnerabilities, unused or missing declarations, lockfile drift, and duplicates.
  Path: `DependencyHygiene/dependency-hygiene.python.prompt.md`
- **`dependency-hygiene-swift`** — Audit a Swift / Xcode project (Swift Package Manager and/or CocoaPods) for outdated versions, vulnerabilities, unused or missing declarations, and duplicates.
  Path: `DependencyHygiene/dependency-hygiene.swift.prompt.md`
- **`dependency-hygiene-terraform`** — Audit a Terraform / OpenTofu codebase's provider, module, and backend dependencies for outdated versions, vulnerabilities, and duplicate version pins.
  Path: `DependencyHygiene/dependency-hygiene.terraform.prompt.md`

## DocsHygiene

- **`audit-claude-md`** — Audit the project's LLM instruction files for vague rules, missing examples, drifted compliance, and mechanical-enforcement opportunities.
  Path: `DocsHygiene/audit-claude-md.prompt.md`
- **`doc-code-drift`** — Read-only audit that finds places where documentation says one thing and the code does another (outdated commands, renamed env vars, drifted signatures, dead links).
  Path: `DocsHygiene/doc-code-drift.prompt.md`

## IssueWorkflow

- **`audit-duplicate-issues-github`** — Survey a GitHub repository's open issues for duplicates and near-duplicates; cluster, classify, and recommend an action per cluster. Stops before any closure or edit.
  Path: `IssueWorkflow/audit-duplicate-issues.github.prompt.md`

## MilestoneAudit

- **`post-milestone-audit-dotnet`** — Audit a .NET / C# codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
  Path: `MilestoneAudit/post-milestone-audit.dotnet.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-nestjs`** — Audit a NestJS (TypeScript) codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
  Path: `MilestoneAudit/post-milestone-audit.nestjs.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-nextjs`** — Audit a Next.js (App Router) + TypeScript codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance.
  Path: `MilestoneAudit/post-milestone-audit.nextjs.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-python`** — Audit a Python codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
  Path: `MilestoneAudit/post-milestone-audit.python.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-react-native`** — Audit a React Native / Expo codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
  Path: `MilestoneAudit/post-milestone-audit.react-native.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-swift`** — Audit a Swift / Xcode codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
  Path: `MilestoneAudit/post-milestone-audit.swift.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-audit-terraform`** — Audit a Terraform infrastructure-as-code repo after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance.
  Path: `MilestoneAudit/post-milestone-audit.terraform.prompt.md`
  Related: `post-milestone-fix`
- **`post-milestone-fix`** — Action the in-scope findings from the most recent post-milestone audit report. Commits locally; does not push or open a PR.
  Path: `MilestoneAudit/post-milestone-fix.prompt.md`
  Related: `post-milestone-audit-dotnet`, `post-milestone-audit-nestjs`, `post-milestone-audit-nextjs`, `post-milestone-audit-python`, `post-milestone-audit-react-native`, `post-milestone-audit-swift`, `post-milestone-audit-terraform`

## MilestoneSmoke

- **`post-milestone-smoke-test-api`** — Drive a running HTTP API after a milestone tag is cut — hit headline endpoints with concrete requests, assert response shape and auth behaviour, write a pass/fail/blocked report.
  Path: `MilestoneSmoke/post-milestone-smoke-test.api.prompt.md`
- **`post-milestone-smoke-test-cli`** — Drive a CLI binary after a milestone tag is cut — invoke headline commands, observe exit code / stdout / stderr / side effects, write a pass/fail/blocked report.
  Path: `MilestoneSmoke/post-milestone-smoke-test.cli.prompt.md`
- **`post-milestone-smoke-test-ios`** — Drive an iOS app through the iOS Simulator after a milestone tag is cut — execute headline user flows, observe device log and screenshots, write a pass/fail/blocked report.
  Path: `MilestoneSmoke/post-milestone-smoke-test.ios.prompt.md`
- **`post-milestone-smoke-test-web`** — Drive a web app through a browser MCP server after a milestone tag is cut — exercise headline flows, write a pass/fail/blocked report.
  Path: `MilestoneSmoke/post-milestone-smoke-test.web.prompt.md`

## ObservabilityAudit

- **`observability-audit`** — Read-only audit of how a codebase logs, traces, and surfaces errors — swallowed errors, missing correlation IDs, log-level mismatches, PII in logs, dishonest health checks.
  Path: `ObservabilityAudit/observability-audit.prompt.md`

## PRWorkflow

- **`pre-pr-checklist`** — Before opening a pull request, run the project's check suite, scan the diff for things reviewers can't easily catch (debug code, secrets, missing tests), and draft a PR body.
  Path: `PRWorkflow/pre-pr-checklist.prompt.md`

## Refactoring

- **`dead-code-audit`** — Find code that isn't used — exports never imported, components never rendered, branches never reached, env vars never read, permanently-on/off flags. Read-only.
  Path: `Refactoring/dead-code-audit.prompt.md`
  Related: `duplicate-logic`
- **`duplicate-logic`** — Find functions, modules, or components doing the same job under different names. Cluster, identify a winner, propose consolidations. Read-only — does not action.
  Path: `Refactoring/duplicate-logic.prompt.md`
  Related: `dead-code-audit`

## StackUpgrade

- **`stack-upgrade-dotnet`** — Plan a .NET TFM upgrade (e.g. .NET 6 → 8, 8 → 9) — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.dotnet.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-nestjs`** — Plan a NestJS major version upgrade — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.nestjs.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-nextjs`** — Plan a Next.js version upgrade — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.nextjs.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-python`** — Plan a Python language version upgrade (e.g. 3.10 → 3.12) — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.python.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-react-native`** — Plan a React Native / Expo SDK upgrade — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.react-native.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-swift`** — Plan a Swift / Xcode / iOS SDK upgrade — read release notes, scan for affected patterns, survey codemods, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.swift.prompt.md`
  Related: `post-milestone-fix`
- **`stack-upgrade-terraform`** — Plan a Terraform / OpenTofu CLI or major provider upgrade (e.g. AWS provider 4 → 5) — read release notes, scan for patterns, produce a risk-ranked migration plan.
  Path: `StackUpgrade/stack-upgrade.terraform.prompt.md`
  Related: `post-milestone-fix`
