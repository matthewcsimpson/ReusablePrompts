---
name: db-migration-audit-typeorm
description: Pre-merge safety audit for TypeORM migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
user-invocable: false
---

Follow the instructions in [`DBMigrationAudit/db-migration-audit.typeorm.prompt.md`](../../../DBMigrationAudit/db-migration-audit.typeorm.prompt.md).

Related: `/playbook db-migration-fix-typeorm`.
