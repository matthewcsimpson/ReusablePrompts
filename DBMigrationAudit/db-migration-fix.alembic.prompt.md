---
description: Action findings from db-migration-audit-alembic. Edit Alembic migrations (CONCURRENTLY, splits, NOT VALID), verify via alembic upgrade --sql, commit per migration. Local commits only.
related: [db-migration-audit-alembic]
---

# DB migration fix — Alembic variant

Action findings from a `db-migration-audit-alembic` report against
Alembic migration files.

**This prompt extends [`core/db-migration-fix.core.prompt.md`](./core/db-migration-fix.core.prompt.md).**
Read the core first for the workflow shape (input scoping, per-finding
verification, structural-split discipline, commit-per-migration). This
file supplies the Alembic-specific edits, generation commands, and
verification commands.

---

## Assumed stack

- **Tool**: Alembic.
- **Migrations**: `alembic/versions/<rev>_<slug>.py` — Python files with
  `upgrade()` / `downgrade()` and `op.*` operations.
- **Config**: `alembic.ini` (transactional mode, naming convention).
- **Schema source**: SQLAlchemy `Base.metadata` typically in
  `<app>/db/models.py` or equivalent.

---

## §1 — Locate applied-state before editing

Before editing any migration, check whether it has been applied
anywhere beyond local dev:

```sh
# Local applied state (safe to edit if only local)
alembic current

# If a remote tracks applied migrations, ask the user — Alembic
# does not have a built-in "what's applied in prod" command.
```

If the migration revision appears in `alembic_version` on any shared
database, in-place editing will produce a checksum mismatch and Alembic
will refuse to continue. Switch to `corrective` mode (per the core)
and write a new forward migration:

```sh
alembic revision -m "corrective: <what the new migration compensates for>"
```

Hand-edit the new file's `upgrade()` to reverse / compensate for the
audit finding (drop the bad index and re-create with `CONCURRENTLY`,
extract the inline backfill into a batched job, etc.). The original
migration stays untouched.

---

## §2 — Common edits

### Add `CONCURRENTLY` to index creation (Postgres)

Alembic's `op.create_index(..., concurrently=True)` requires the
migration to run **outside a transaction**. Alembic wraps each
migration in a transaction by default.

Edit pattern:

```python
# In the migration file
revision = "abc123"
down_revision = "def456"

# Add this at the top of the file (outside any function):
def _no_transaction():
    return False

# In alembic/env.py, the configure() call needs
# transaction_per_migration=False — or use the per-revision flag
# below.
```

The cleanest per-revision approach: add to `alembic.ini` or
`alembic/env.py` a check that disables transactions for specific
revisions, and document that revision needs that mode.

Alternatively, use raw SQL:

```python
def upgrade():
    op.execute("COMMIT")
    op.execute("CREATE INDEX CONCURRENTLY ix_users_email ON users(email)")
    op.execute("BEGIN")
```

`op.execute("COMMIT")` mid-migration ends the wrapper transaction;
`BEGIN` opens a new one so subsequent operations behave normally. Note
this in a code comment — it looks wrong on cold read.

### Split schema + backfill + NOT NULL into three migrations

```sh
# Generate three new migrations
alembic revision -m "add nullable orders.tenant_id"
alembic revision -m "backfill orders.tenant_id"
alembic revision -m "set orders.tenant_id not null"
```

Then in the three files:

1. **First migration** — `op.add_column("orders", sa.Column("tenant_id", sa.Integer(), nullable=True))`.
2. **Second migration** — batched UPDATE with progress (do not hold a
   transaction the whole way; commit between batches if Alembic's
   transaction mode allows).
3. **Third migration** — `op.alter_column("orders", "tenant_id", nullable=False)` with `existing_type=...`. For Postgres on a large table, prefer a `NOT VALID` constraint + separate `VALIDATE`:

   ```python
   op.execute("ALTER TABLE orders ADD CONSTRAINT orders_tenant_id_not_null CHECK (tenant_id IS NOT NULL) NOT VALID")
   # later (potentially a separate migration):
   op.execute("ALTER TABLE orders VALIDATE CONSTRAINT orders_tenant_id_not_null")
   ```

   Note that `NOT NULL` + `CHECK (... IS NOT NULL)` are not identical;
   the check-constraint pattern is the production-safe approximation
   when the column already exists.

### Replace `op.drop_column` + `op.add_column` rename with `op.alter_column`

Autogenerate may emit a drop+add when the underlying schema renames.
Replace with:

```python
op.alter_column("users", "old_name", new_column_name="new_name")
```

If the model also added a non-string transformation (type change),
that's a separate finding — handle the rename here, the type change
in a follow-up migration.

### Add FK with index

```python
op.create_index("ix_orders_user_id", "orders", ["user_id"])
op.create_foreign_key(
    "fk_orders_user_id", "orders", "users",
    ["user_id"], ["id"], ondelete="CASCADE"
)
```

Both in the same migration is OK if the index goes first; on a hot
table, split the index into its own concurrent-mode migration first
(see above).

---

## §3 — Verification commands

After each edit:

```sh
# Render the SQL that would run (does not connect to the database)
alembic upgrade <revision> --sql

# Render only the new revisions delta
alembic upgrade head --sql

# Ensure the migration tree is still valid
alembic check        # Alembic ≥1.9
alembic heads        # confirm only one head (unless intentional branching)
```

If `alembic check` or `alembic heads` reports unexpected branching, the
edit broke the migration DAG — revert.

---

## §4 — Structural splits

```sh
# Generate a new revision with a specific down_revision
alembic revision -m "split: backfill orders.tenant_id" --head=<original-rev>

# Then hand-edit the down_revision in the generated file to chain
# correctly.
```

Confirm `alembic heads` shows a single head after the split.

---

## §5 — Constraints (Alembic-specific addenda)

- Do not delete a previously-merged migration revision to "fix" it.
  Alembic tracks state by revision id; deleting a merged revision
  breaks every developer's local `alembic_version`.
- Do not rewrite the `down_revision` chain except as part of a
  deliberate split.
- Do not use `op.execute` for operations Alembic has a native API for
  unless the native API is the problem (e.g. `CONCURRENTLY`).
- If editing `alembic.ini` to enable `transaction_per_migration =
  False`, mention it in the commit message — that flag affects every
  migration, not just the one being fixed.
