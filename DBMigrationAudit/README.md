# DBMigrationAudit

Pre-merge safety audit for database migration files. Catches the
unsafe-under-production-load operations that look fine in isolation
but break a live system: NOT NULL on a populated table, a non-
concurrent index on a hot table, an FK without an index, a rename
that breaks a rolling deploy.

Run this on a PR branch before merge, after the migration has been
written but before it's been applied anywhere beyond a local dev
database.

Variants carry an ORM tag (`.prisma`, `.typeorm`, `.alembic`,
`.ef-core`) because migration file shapes differ entirely across
ORMs — but the **unsafe operations themselves are universal**. The
core captures the operation catalogue and the audit framework;
each variant supplies the parser and the ORM-specific gotchas.

| Variant | Migration shape |
|---|---|
| `db-migration-audit.prisma.prompt.md` | SQL-ish migration files in `prisma/migrations/`, declarative `schema.prisma` deltas |
| `db-migration-audit.typeorm.prompt.md` | TypeScript classes implementing `MigrationInterface` (`up()` / `down()`) |
| `db-migration-audit.alembic.prompt.md` | Python files in `alembic/versions/`, `op.*` operations, `upgrade()` / `downgrade()` |
| `db-migration-audit.ef-core.prompt.md` | C# classes extending `Migration`, `MigrationBuilder` API, `Up()` / `Down()` |
| `core/db-migration-audit.core.prompt.md` | Shared scaffold — unsafe-operation catalogue, severity model, output format. Not invoked directly. |

## Picking a variant

Pick the variant matching the project's ORM. The unsafe-operation
list is identical; the variant adapts the file paths, parsing
strategy, and per-ORM idioms (Prisma's `@@map` rename behaviour,
TypeORM's `synchronize: true` footgun, Alembic's autogenerate
limits, EF Core's annotations-driven schema).

If your ORM isn't listed (Knex, Sequelize, Liquibase, Flyway,
Django, ActiveRecord, raw SQL files, …):

1. Copy the closest variant.
2. Rename to `db-migration-audit.<orm>.prompt.md`.
3. Replace the file-path conventions, parsing strategy, and ORM-
   specific notes. Keep the operation catalogue in the core.
4. Leave the `core/` reference intact.
5. Update this README's variant table and open a PR.

## What it catches

The audit ranks findings by *blast radius under production load*,
not by syntactic concern. A NOT NULL on an empty table is fine; on
a populated table it's an outage. The audit is context-aware in
that sense.

- ⚠️ **Locks the table** — operations that block writes (or reads)
  for the duration of the migration. Disaster on a hot table.
- ⚠️ **Breaks rolling deploys** — schema state that the previous
  application version cannot tolerate. The window between "old
  pods serving" and "new pods serving" becomes an error window.
- ⚠️ **Backfills inside a migration transaction** — long-running
  UPDATEs that hold locks far longer than expected.
- ⚠️ **No downgrade path** — destructive operations with no `down`
  / `downgrade` implementation, or where the down is silently
  lossy.
- ⚠️ **Missing index on FK** — adds an FK constraint without an
  index on the referencing column. Reads slow; deletes on the
  parent table take exclusive locks.
- ⚠️ **Constraint added without a precheck** — UNIQUE, CHECK, FK
  added against existing data without verifying conformance first.
- 💡 **Migration that should have been two migrations** — schema
  + backfill in one go; the safe shape is split into separate
  steps.

## Required tool capabilities

- File read across the repo.
- Shell execution for grep / migration directory listing.
- No database connection needed — the audit is purely static. The
  user is responsible for actually running the migration in a
  staging environment.

Designed for Claude Code and Codex CLI; anything with the same
capability set should work.

## Output discipline

The report goes to the PR / commit conversation (the user pastes it
or the agent posts it). It does not write to disk by default —
migration audits are point-in-time artefacts and don't benefit
from a tracked history.

Optionally writes to `docs/audits/migrations/<migration-id>.md` if
the project tracks migration audits.

## Invocation

See the [root README](../README.md#invocation) for the three
supported patterns. For paste-mode, paste the core file first, then
the variant — the variant references the core for the operation
catalogue.
