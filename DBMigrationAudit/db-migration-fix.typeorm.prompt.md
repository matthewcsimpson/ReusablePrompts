---
description: Action findings from db-migration-audit-typeorm. Edit TypeORM migration classes (raw SQL, splits), verify via typeorm migration:show + tsc, commit per migration. Local commits only.
related: [db-migration-audit-typeorm]
---

# DB migration fix — TypeORM variant

Action findings from a `db-migration-audit-typeorm` report against
TypeORM migration files.

**This prompt extends [`core/db-migration-fix.core.prompt.md`](./core/db-migration-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
TypeORM-specific edits, generation commands, and verification commands.

---

## Assumed stack

- **ORM**: TypeORM (`typeorm`).
- **Migrations**: TypeScript classes implementing `MigrationInterface`
  with `up(queryRunner: QueryRunner)` and `down(queryRunner: QueryRunner)`.
- **Location**: typically `src/migrations/` or `db/migrations/`;
  configured in DataSource options or `ormconfig.*`.
- **DataSource**: a `DataSource` instance, usually in
  `src/data-source.ts` or `src/ormconfig.ts`.

---

## §1 — Locate applied-state before editing

TypeORM stores applied migrations in a `migrations` table (or
configurable name).

```sh
# Show which migrations the database has applied
typeorm migration:show -d <data-source-file>

# Or via npm script if the project wraps it
npm run typeorm migration:show
```

If the migration appears as applied (✓) on any shared environment, do
not edit — write a new corrective migration. Confirm with the user.

---

## §2 — Common edits

### Add `CONCURRENTLY` via `queryRunner.query` raw SQL

TypeORM's `createIndex` does not support `CONCURRENTLY`. Drop to raw
SQL:

```typescript
public async up(queryRunner: QueryRunner): Promise<void> {
    // Exit TypeORM's wrapping transaction explicitly. TypeORM wraps
    // each migration; Postgres refuses CONCURRENTLY inside a
    // transaction.
    await queryRunner.commitTransaction();
    await queryRunner.query(
        `CREATE INDEX CONCURRENTLY "IX_Users_Email" ON "Users" ("email")`
    );
    await queryRunner.startTransaction();
}

public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.commitTransaction();
    await queryRunner.query(`DROP INDEX CONCURRENTLY "IX_Users_Email"`);
    await queryRunner.startTransaction();
}
```

Alternative: set `transaction: false` in the DataSource migration
options — but that applies to **all** migrations, which may not be
desired.

### Split schema + backfill + NOT NULL

```sh
# Generate three migrations
typeorm migration:create src/migrations/AddNullableTenantId
typeorm migration:create src/migrations/BackfillTenantId
typeorm migration:create src/migrations/SetTenantIdNotNull
```

Then in each:

1. **First** — `await queryRunner.addColumn("Orders", new TableColumn({ name: "tenantId", type: "int", isNullable: true }))`.
2. **Second** — batched `queryRunner.query("UPDATE \"Orders\" SET \"tenantId\" = ... WHERE id BETWEEN ? AND ?")` with explicit batch boundaries.
3. **Third** — `await queryRunner.changeColumn("Orders", "tenantId", new TableColumn({ name: "tenantId", type: "int", isNullable: false }))`.

For Postgres on a large table, prefer raw SQL with `NOT VALID` check
constraint:

```typescript
await queryRunner.query(`
    ALTER TABLE "Orders"
    ADD CONSTRAINT "Orders_tenantId_not_null"
    CHECK ("tenantId" IS NOT NULL) NOT VALID
`);
// Then in a follow-up migration:
await queryRunner.query(`
    ALTER TABLE "Orders" VALIDATE CONSTRAINT "Orders_tenantId_not_null"
`);
```

### Replace drop-add column rename

TypeORM's `renameColumn` does the right thing in most engines:

```typescript
await queryRunner.renameColumn("Users", "oldName", "newName");
```

If the audit cited a paired `dropColumn` + `addColumn`, replace both
with the rename.

### Add FK with index

```typescript
await queryRunner.createIndex("Orders", new TableIndex({
    name: "IX_Orders_userId",
    columnNames: ["userId"]
}));

await queryRunner.createForeignKey("Orders", new TableForeignKey({
    name: "FK_Orders_userId",
    columnNames: ["userId"],
    referencedTableName: "Users",
    referencedColumnNames: ["id"],
    onDelete: "CASCADE"
}));
```

For hot tables, split the index into its own concurrent-mode migration
first.

### Remove `synchronize: true`

If the audit caught a DataSource with `synchronize: true` enabled in
non-dev environments, this isn't a migration edit — it's a config
edit. Set `synchronize: false` and surface the change separately, with
a clear commit message ("config: disable TypeORM synchronize").

---

## §3 — Verification commands

After each edit:

```sh
# Dry-run the pending migrations to see the SQL
typeorm migration:show -d <data-source>

# Generate a fresh migration off the current entities and diff
typeorm migration:generate src/migrations/CheckDrift -d <data-source>
# (delete the generated file afterwards if it was a no-op check)

# Compile to catch TypeScript errors
npx tsc --noEmit
```

A successful `tsc --noEmit` after the edit confirms the migration class
still compiles. If `migration:generate` produces a non-empty migration,
the entities and migrations have drifted — investigate before
committing.

---

## §4 — Structural splits

```sh
# Generate a new migration with a name that sorts AFTER the original
typeorm migration:create src/migrations/<NextStep>

# TypeORM sorts migrations by the timestamp in the class name.
# The generated file's class name will look like `NextStep1234567890`.
# If you need to insert between two existing migrations, hand-edit the
# class-name timestamp suffix.
```

Confirm the order with `typeorm migration:show`.

---

## §5 — Constraints (TypeORM-specific addenda)

- Do not change the migration's **class name** without renaming the
  file to match. TypeORM matches by class name; mismatch causes
  silent skip.
- Do not change the timestamp suffix on the class name of an applied
  migration. TypeORM uses it as the migration identifier in the
  `migrations` table.
- Do not enable `synchronize: true` to "fix" schema drift. That's
  the source of several of the audit's likely findings, not a fix.
- Do not use `entitySkipConstructor` or other DataSource flags to
  work around a migration error — they hide the symptom and let
  drift compound.
- If the project uses `migrationsTransactionMode: "each"` /
  `"all"` / `"none"`, mention it in the report. The fix's
  `CONCURRENTLY` pattern depends on which mode is active.
- The `queryRunner.commitTransaction()` + `queryRunner.startTransaction()`
  pattern is unusual on cold read — leave a one-line comment in the
  code explaining why, so future readers don't "tidy up" the
  transaction-juggling.
