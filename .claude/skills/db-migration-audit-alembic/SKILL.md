---
name: db-migration-audit-alembic
description: Pre-merge safety audit for Alembic database migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
user-invocable: false
---

Follow the instructions in [`DBMigrationAudit/db-migration-audit.alembic.prompt.md`](../../../DBMigrationAudit/db-migration-audit.alembic.prompt.md).

Related: `/playbook db-migration-fix-alembic`.
