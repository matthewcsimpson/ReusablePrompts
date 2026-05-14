---
description: Action findings from db-migration-audit-ef-core. Edit EF Core migrations (raw SQL for CONCURRENTLY, splits), verify via dotnet ef migrations script, commit per migration. Local commits only.
related: [db-migration-audit-ef-core]
---

# DB migration fix — EF Core variant

Action findings from a `db-migration-audit-ef-core` report against
Entity Framework Core migration files.

**This prompt extends [`core/db-migration-fix.core.prompt.md`](./core/db-migration-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
EF-Core-specific edits, generation commands, and verification commands.

---

## Assumed stack

- **ORM**: Entity Framework Core (EF Core).
- **Migrations**: `<Project>/Migrations/<timestamp>_<Name>.cs` — C#
  classes extending `Migration` with `Up(MigrationBuilder)` and
  `Down(MigrationBuilder)`.
- **Designer file**: `<Project>/Migrations/<timestamp>_<Name>.Designer.cs`
  — auto-generated snapshot of the model at the migration's time.
- **Model snapshot**: `<Project>/Migrations/<DbContext>ModelSnapshot.cs`
  — current model state.
- **DbContext**: project class extending `DbContext`.

---

## §1 — Locate applied-state before editing

```sh
# What migrations does the database think are applied?
dotnet ef migrations list

# If a remote tracks the DB, the user needs to confirm. EF Core's
# __EFMigrationsHistory table is the source of truth.
```

If the migration appears in `__EFMigrationsHistory` on any shared
database, the safe path is **a new corrective migration**, not an
in-place edit.

---

## §2 — Common edits

### Add raw SQL to use `CONCURRENTLY` (Postgres) / `LOCK=NONE` (MySQL)

EF Core's `CreateIndex` builder does not natively support
`CONCURRENTLY`. Drop down to `migrationBuilder.Sql(...)`:

```csharp
protected override void Up(MigrationBuilder migrationBuilder)
{
    // Postgres
    migrationBuilder.Sql(
        "CREATE INDEX CONCURRENTLY \"IX_Users_Email\" ON \"Users\" (\"Email\");",
        suppressTransaction: true
    );
}

protected override void Down(MigrationBuilder migrationBuilder)
{
    migrationBuilder.Sql(
        "DROP INDEX CONCURRENTLY \"IX_Users_Email\";",
        suppressTransaction: true
    );
}
```

`suppressTransaction: true` is critical — without it, EF Core wraps
the migration in a transaction and Postgres refuses
`CONCURRENTLY`.

### Split schema + backfill + NOT NULL

```sh
# Generate three migrations
dotnet ef migrations add AddNullableTenantId
dotnet ef migrations add BackfillTenantId
dotnet ef migrations add SetTenantIdNotNull
```

Then in each:

1. **First** — `AddColumn` with `nullable: true`.
2. **Second** — `migrationBuilder.Sql("UPDATE Orders SET TenantId = ...")` for the backfill. For large tables, prefer a batched script rather than a single UPDATE; mention this in a comment.
3. **Third** — `AlterColumn` to `nullable: false`. For Postgres on a large table, prefer raw SQL with `NOT VALID` check constraint + separate validate.

Update the model (the source of `nullable`) on the **third** migration so the snapshot reflects the final state.

### Replace drop-add column rename

EF Core emits `DropColumn` + `AddColumn` when it can't infer a rename
(no `[Column("OldName")]` mapping in the prior model, for example).
The fix is to use `RenameColumn`:

```csharp
migrationBuilder.RenameColumn(
    name: "OldName",
    table: "Users",
    newName: "NewName"
);
```

Then re-run `dotnet ef migrations script` to confirm the snapshot
aligns.

### Add FK with index

```csharp
migrationBuilder.CreateIndex(
    name: "IX_Orders_UserId",
    table: "Orders",
    column: "UserId"
);

migrationBuilder.AddForeignKey(
    name: "FK_Orders_Users_UserId",
    table: "Orders",
    column: "UserId",
    principalTable: "Users",
    principalColumn: "Id",
    onDelete: ReferentialAction.Cascade
);
```

Both in the same migration is fine; on a hot table, split the index
into a CONCURRENTLY migration first.

---

## §3 — Verification commands

After each edit:

```sh
# Render the SQL that would run (does not connect to the database)
dotnet ef migrations script --idempotent

# Render only since a specific migration
dotnet ef migrations script <FromMigration> <ToMigration>

# Validate that the model snapshot is consistent with the migrations
dotnet ef migrations has-pending-model-changes
```

If `has-pending-model-changes` reports drift, the model and the
migration disagree — re-check the edit. If `script` produces SQL that
doesn't match the audit's expected fix, revert and retry.

The Designer.cs and ModelSnapshot.cs files are auto-generated; do not
hand-edit them. If the migration edit invalidates them, regenerate via
`dotnet ef migrations add --force` (only on un-applied migrations).

---

## §4 — Structural splits

```sh
# Remove the last un-applied migration (must be the most recent)
dotnet ef migrations remove

# Add new migrations in the desired sequence
dotnet ef migrations add AddNullableX
dotnet ef migrations add BackfillX
dotnet ef migrations add SetXNotNull
```

`dotnet ef migrations remove` only works on the latest un-applied
migration. Splitting an older one requires removing forward in the
chain — confirm scope with the user before doing that.

---

## §5 — Constraints (EF-Core-specific addenda)

- Do not hand-edit `Designer.cs` or `ModelSnapshot.cs` — they're
  auto-generated. Regenerate via the CLI.
- Do not remove a migration that has been applied to any database.
  The compiler doesn't enforce this; the runtime fails on the next
  `Database.Migrate()` call.
- Do not change the migration class name without also updating the
  filename, `[Migration]` attribute, and any references in the
  ModelSnapshot.
- If the project uses `Database.EnsureCreated()` instead of
  migrations (common in test harnesses), flag — migration fixes
  may not run in that environment.
- Don't use `migrationBuilder.Sql(...)` with `suppressTransaction:
  true` casually. It's needed for `CONCURRENTLY`; everywhere else,
  the default transactional behaviour is what you want.
