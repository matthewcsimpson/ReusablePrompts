---
description: Action findings from db-migration-audit-prisma. Edit Prisma migration SQL (CONCURRENTLY, splits, RENAME COLUMN), verify via prisma migrate diff, commit per migration. Local commits only.
related: [db-migration-audit-prisma]
---

# DB migration fix — Prisma variant

Action findings from a `db-migration-audit-prisma` report against
Prisma Migrate migration files.

**This prompt extends [`core/db-migration-fix.core.prompt.md`](./core/db-migration-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
Prisma-specific edits, generation commands, and verification commands.

---

## Assumed stack

- **ORM**: Prisma (`@prisma/client`, `prisma` CLI).
- **Schema source**: `prisma/schema.prisma`.
- **Migrations**: `prisma/migrations/<timestamp>_<name>/migration.sql`
  — raw SQL.
- **Lock**: `prisma/migrations/migration_lock.toml`.

---

## §1 — Locate applied-state before editing

Prisma migrations are tracked in the `_prisma_migrations` table per
database. Editing an applied migration file changes its **checksum**,
and Prisma will refuse to continue with a checksum mismatch error.

```sh
# Render the migration history Prisma believes is applied locally
prisma migrate status
```

If status shows the migration as Applied on any shared environment,
in-place editing will produce a checksum mismatch and Prisma will
refuse to deploy with `P3009`. Switch to `corrective` mode (per the
core) and generate a new migration:

```sh
prisma migrate dev --create-only --name corrective_<name>
```

Hand-edit the new `migration.sql` to reverse / compensate for the
audit finding (drop the bad index, re-create with `CONCURRENTLY`,
etc.). The original migration stays untouched. Confirm `prisma
migrate status` shows the new corrective as Pending before
committing.

If the migration is still in `--create-only` state (generated but not
applied), `in-place` mode is correct — hand-editing the SQL is fine.

---

## §2 — Common edits

### Add `CONCURRENTLY` to index creation (Postgres)

Prisma wraps the migration in a transaction. Postgres refuses
`CONCURRENTLY` inside a transaction.

The Prisma-recommended pattern: generate the migration with
`--create-only`, then hand-edit:

```sql
-- migration.sql

-- Original (unsafe under load):
-- CREATE INDEX "Users_email_idx" ON "Users"("email");

-- Prisma wraps in BEGIN/COMMIT; we exit the transaction first.
COMMIT;

CREATE INDEX CONCURRENTLY "Users_email_idx" ON "Users"("email");

BEGIN;
```

Add a `-- @prisma-concurrent` comment marker so the audit re-run
recognises the intentional pattern.

### Split schema + backfill + NOT NULL

Prisma has no `down`. To split, generate three create-only migrations:

```sh
# 1. Add nullable column to schema.prisma, then:
prisma migrate dev --create-only --name add_nullable_tenant_id

# 2. Hand-write the backfill SQL — Prisma won't autogenerate it.
# Create directory manually:
mkdir -p prisma/migrations/$(date +%Y%m%d%H%M%S)_backfill_tenant_id
# And write the migration.sql with batched UPDATEs.

# 3. Change schema.prisma to make column non-null, then:
prisma migrate dev --create-only --name set_tenant_id_not_null
```

Update `migration_lock.toml` if the provider changes (rare); leave
alone otherwise.

For the third migration on Postgres, prefer:

```sql
-- Add a NOT VALID check constraint first
ALTER TABLE "Orders"
ADD CONSTRAINT "Orders_tenantId_not_null"
CHECK ("tenantId" IS NOT NULL) NOT VALID;

-- Then in a follow-up migration:
ALTER TABLE "Orders" VALIDATE CONSTRAINT "Orders_tenantId_not_null";

-- Finally:
ALTER TABLE "Orders" ALTER COLUMN "tenantId" SET NOT NULL;
```

The `NOT NULL` alter is fast once the `CHECK` constraint is validated
(Postgres ≥12).

### Replace `DROP COLUMN` + `ADD COLUMN` rename with `RENAME COLUMN`

If the schema delta shows `@map("old_name")` added to a renamed field:

```sql
-- Original (loses data):
-- ALTER TABLE "Users" DROP COLUMN "oldName";
-- ALTER TABLE "Users" ADD COLUMN "newName" TEXT;

-- Fixed:
ALTER TABLE "Users" RENAME COLUMN "oldName" TO "newName";
```

Hand-edit the `migration.sql` directly; the checksum updates when
Prisma next reads it.

### Add FK with index

```sql
CREATE INDEX "Orders_userId_idx" ON "Orders"("userId");

ALTER TABLE "Orders"
ADD CONSTRAINT "Orders_userId_fkey"
FOREIGN KEY ("userId") REFERENCES "Users"("id")
ON DELETE CASCADE
ON UPDATE CASCADE;
```

For hot tables, split the index into a concurrent-mode migration
first (see above), then the FK in a follow-up.

---

## §3 — Verification commands

After each edit:

```sh
# Diff the migration SQL against the schema.prisma source of truth
prisma migrate diff \
  --from-migrations prisma/migrations \
  --to-schema-datamodel prisma/schema.prisma \
  --script

# Should produce empty output if the migrations match the schema.

# Validate the migration is well-formed
prisma validate
```

If `prisma migrate diff` produces non-empty SQL, the migration and
the schema have drifted — either the edit needs to be reverted, or
the schema needs a matching change (which is itself a finding to
confirm with the user).

Do not run `prisma migrate dev` after editing — it will attempt to
apply the migration to the shadow database and may reset history.

---

## §4 — Structural splits

```sh
# Create-only generates the migration file but does not apply it
prisma migrate dev --create-only --name <name>

# To split an existing migration, hand-create the migration
# directories with timestamp names that sort between the existing
# migrations:
mkdir -p prisma/migrations/$(date +%Y%m%d%H%M%S)_<name>
```

Prisma reads the timestamp prefix to determine order. Use shell-
generated timestamps so the order is unambiguous.

---

## §5 — Constraints (Prisma-specific addenda)

- Do not edit `migration_lock.toml` unless the database provider is
  actually changing.
- Do not edit a migration that's in `_prisma_migrations` on any
  shared environment. The checksum mismatch will block deploy.
- Do not regenerate the migration via `prisma migrate dev` after
  hand-editing — it will overwrite your changes. Use `prisma
  migrate resolve --applied` only if the migration has been
  manually applied and you need to mark it.
- Do not delete migrations from `prisma/migrations/`. Prisma tracks
  the full history; deletions break every developer's local state.
- If a fix requires changing `schema.prisma`, that's a separate
  edit — surface it for the user to action, since it affects the
  Prisma client generation and may need a `prisma generate` run.
- Prisma's shadow database (used during `migrate dev`) doesn't
  exactly match production engine settings. The audit may have
  caught engine-specific issues that the shadow won't reproduce —
  trust the audit, not a clean shadow-database run.
