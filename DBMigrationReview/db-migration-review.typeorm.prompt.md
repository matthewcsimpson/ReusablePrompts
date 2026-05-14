---
description: Pre-merge safety review for TypeORM migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
---

# DB migration review — TypeORM variant

Review database migrations written for TypeORM.

**This prompt extends [`core/db-migration-review.core.prompt.md`](./core/db-migration-review.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Step 2 unsafe-operation catalogue, Step
3 severity model, Step 4 report format, and the Constraints). This
file supplies the TypeORM-specific file paths, parsing strategy,
and ORM gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **ORM**: TypeORM (commonly in NestJS / Express projects).
- **Migrations**: TypeScript files in the configured migrations
  directory (commonly `src/migrations/` or
  `src/database/migrations/`). Each file exports a class
  implementing `MigrationInterface` with `up(qr: QueryRunner)` and
  `down(qr: QueryRunner)` methods.
- **Schema source of truth**: entity classes
  (`*.entity.ts` files with `@Entity`, `@Column` decorators).
- **Database**: from `DataSource` config (`type`, often in
  `ormconfig.ts`, `data-source.ts`, or a NestJS module).

The biggest TypeORM-specific risk lives outside the migration
files: **`synchronize: true`**. If the project's `DataSource` has
`synchronize: true` in any environment that touches production
data, every migration in this audit is irrelevant — TypeORM rewrites
the schema on app start, bypassing migrations entirely. Check for
this first.

---

## §1 — Inventory commands

```sh
# Migrations in this PR
git diff --name-only origin/main...HEAD \
  -- 'src/**/migrations/*.ts' 'src/migrations/*.ts' '**/migrations/*-*.ts'

# `synchronize: true` audit — CRITICAL if production-adjacent
grep -rnE 'synchronize\s*:\s*true' --include='*.ts' .

# DataSource config / engine
grep -rnE "type\s*:\s*['\"]" --include='*.ts' . | grep -iE 'postgres|mysql|sqlite|mssql|mariadb'

# Entity changes (often the intent that the migration expresses)
git diff origin/main...HEAD -- 'src/**/*.entity.ts'
```

If `synchronize: true` is found in a non-test config, surface it in
the Verdict and recommend it be removed before any further migration
review is meaningful.

---

## §2 — Operation catalogue (TypeORM specifics)

The core's catalogue applies. TypeORM offers two APIs in the `up`
and `down` methods:

- `qr.query("RAW SQL")` — escape hatch; review the SQL by the
  catalogue directly.
- `qr.createTable`, `qr.addColumn`, `qr.createIndex`,
  `qr.createForeignKey`, etc. — TypeORM's typed builders; review
  the resulting operation by what TypeORM emits.

### Common TypeORM-emitted patterns and their actual SQL

| TypeORM call | What it emits |
|---|---|
| `qr.addColumn(table, new TableColumn({ name, type, isNullable: false }))` | `ALTER TABLE ... ADD COLUMN ... NOT NULL` — fails on a populated table without a default. |
| `qr.createIndex(table, new TableIndex({ ... }))` | `CREATE INDEX` (never `CONCURRENTLY`). |
| `qr.changeColumn(table, oldName, newColumn)` | `ALTER TABLE ... ALTER COLUMN ...` — may include type changes, default changes, name changes in a single call. Hard to reason about. |
| `qr.renameColumn(table, old, new)` | `ALTER TABLE ... RENAME COLUMN` — rolling-deploy breaker. |
| `qr.dropColumn(table, name)` | `ALTER TABLE ... DROP COLUMN` — rolling-deploy breaker. |
| `qr.createForeignKey(...)` | `ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY` — fails on bad data, no index on referencing column. |

### `qr.query` raw SQL inside migrations

Raw SQL is the most common pattern for concurrent index creation
(TypeORM's builders can't emit `CONCURRENTLY`). Review the SQL by
the core catalogue.

Watch for `qr.query` blocks that mix DDL and `UPDATE` / `INSERT` —
this is the "schema + backfill in one migration" anti-pattern from
the core, common in TypeORM because raw queries are the path of
least resistance.

### Default-name foreign keys / indexes

TypeORM generates constraint names if not supplied. The
auto-generated names are stable per migration but verbose
(`FK_a1b2c3d4...`). If the migration's `up` creates a FK with a
generated name, the `down` must drop it by the same name — easy to
break by hand-editing.

### `qr.startTransaction` / `qr.commitTransaction`

TypeORM wraps each migration in a transaction by default. Concurrent
indexes need the transaction skipped — the workaround is to use a
custom `transaction` mode or split the index into its own migration
with explicit transaction handling.

If the migration calls `qr.startTransaction` manually, that's a
yellow flag — usually a sign the author hit the transaction issue
and worked around it incorrectly.

---

## §3 — `down()` review

TypeORM has a `down()` method; every migration *should* have one,
but many don't bother. The core's "Rollback / downgrade review"
section applies. Specific TypeORM checks:

- ⚠️ **Empty `down()`** — body is just a comment or empty block.
  The migration is forward-only by negligence, not by policy.
- ⚠️ **`down()` not symmetric** — `up` does 5 operations; `down`
  reverses 3. Partial rollback corrupts state.
- ⚠️ **`down()` references generated names** — if `up` lets
  TypeORM generate a FK / index name, `down` must use the same
  name. Hand-edited names cause runtime failures.

---

## §4 — TypeORM-specific report header rows

Add to the audit header:

- ORM: `TypeORM <version from package.json>`.
- Engine: from `DataSource.type`.
- `synchronize`: <true | false | not found>.
- `migrationsTransactionMode`: <each | all | none | default>.

If `synchronize: true` is set in any environment that connects to a
real database, **the Verdict must lead with that finding** at
⚠️ CRITICAL — it nullifies the rest of the review.

---

## Constraints (TypeORM-specific addenda)

- `synchronize: true` in any non-test, non-local environment is
  always ⚠️ CRITICAL. The project ships schema changes on app
  start without review.
- A migration with no `down()` (or an empty one) is not necessarily
  a violation — some projects deliberately ban down migrations —
  but it must be flagged so the reviewer confirms it matches policy.
- Don't recommend wholesale replacing `qr.createIndex` with raw
  SQL "for safety" — the typed builder is fine for non-concurrent
  cases. The rule is: index on a hot / large table → raw SQL with
  `CONCURRENTLY`; other indexes → typed builder is fine.
- TypeORM's `dropForeignKey` requires the constraint name. If the
  `down()` tries to drop a FK with a hardcoded name that doesn't
  match what `up()` created, the down will silently fail or skip.
  Cross-check names between `up` and `down`.
- The migrations directory often gets confused with seed data and
  fixtures in TypeORM projects. Verify the files in scope are
  actual migrations (extend `MigrationInterface`), not seeders.
