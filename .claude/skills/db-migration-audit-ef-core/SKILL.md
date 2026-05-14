---
name: db-migration-audit-ef-core
description: Pre-merge safety audit for Entity Framework Core migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
user-invocable: false
---

Follow the instructions in [`DBMigrationAudit/db-migration-audit.ef-core.prompt.md`](../../../DBMigrationAudit/db-migration-audit.ef-core.prompt.md).

Related: `/playbook db-migration-fix-ef-core`.
