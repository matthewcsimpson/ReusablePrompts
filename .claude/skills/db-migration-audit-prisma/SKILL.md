---
name: db-migration-audit-prisma
description: Pre-merge safety audit for Prisma Migrate migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
user-invocable: false
---

Follow the instructions in [`DBMigrationAudit/db-migration-audit.prisma.prompt.md`](../../../DBMigrationAudit/db-migration-audit.prisma.prompt.md).

Related: `/playbook db-migration-fix-prisma`.
