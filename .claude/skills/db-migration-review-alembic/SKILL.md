---
name: db-migration-review-alembic
description: Pre-merge safety review for Alembic database migrations — catches NOT NULL on populated tables, non-concurrent indexes, FK without index, rename-on-deploy hazards.
user-invocable: false
---

Follow the instructions in [`DBMigrationReview/db-migration-review.alembic.prompt.md`](../../../DBMigrationReview/db-migration-review.alembic.prompt.md).
