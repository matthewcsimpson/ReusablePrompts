---
description: Audit a Terraform infrastructure-as-code repo after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance.
related: [post-milestone-fix]
---

# Post-milestone audit — Terraform variant

Audit a Terraform (infrastructure-as-code) repo after a milestone
tag is cut.

**This prompt extends [`core/post-milestone-audit.core.prompt.md`](./core/post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window
logic, convention-source discovery, delta logic, output format,
and constraints. This file supplies the Terraform / IaC specifics
for §2 examples, §3 milestone-diff focus, §4 regression sweeps,
§4.5 extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Tool**: Terraform 1.x (or OpenTofu — the file syntax and
  workflow are the same).
- **Providers**: typically AWS, Azure, or Google Cloud — possibly
  several in the same repo.
- **Modules**: locally defined modules under `modules/` and / or
  registry modules from `terraform-aws-modules`, `Azure/`, etc.
- **State**: remote backend (S3 + DynamoDB, Azure Storage, GCS,
  Terraform Cloud, etc.) — never local for shared infra.
- **Workspace pattern**: workspaces or env-per-folder (e.g.
  `envs/prod/`, `envs/staging/`).
- **Conventions documented in**: README, `CLAUDE.md` / `AGENTS.md`
  (yes, IaC repos benefit from these too), tagging /
  naming docs.

If the project mixes Terraform with Pulumi, Crossplane, or CDK
files, fall back to the generic categories where the Terraform
checks don't apply.

---

## §2 — Per-rule sweep (Terraform rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `*.tf` files in the root and each environment / module folder
  — surface the provider versions, backend config, locals,
  variables, outputs.
- `versions.tf` (or equivalent) — provider version constraints
  and `required_version` for Terraform itself.
- `.terraform-version` / `.tool-versions` — pinned Terraform
  version for tooling (tfenv / asdf).
- `*.tfvars` and `*.tfvars.json` — but flag if any `*.tfvars`
  with real values are committed (only `*.tfvars.example`
  should be).
- `.tflint.hcl`, `.tfsec.yml`, `.checkov.yml` — static-analysis
  config that the repo's docs may rely on.

Common rule categories the project's docs tend to enforce:

- **Provider version pinning** — `required_providers` blocks
  with `~>` constraints (allow patch updates, lock major /
  minor).
- **Terraform version pinning** — `required_version` in every
  root module.
- **Backend configuration** — remote backend declared in every
  root module; no local-only state files for shared infra.
- **State file safety** — `terraform.tfstate*` files never
  committed (covered by `.gitignore` and the audit verifies).
- **Variable typing and validation** — every input variable has
  `type = ...` and `validation { ... }` blocks where the input
  is sensitive to invalid data.
- **Sensitive markers** — credentials / connection strings /
  keys marked `sensitive = true` on variables and outputs.
- **Naming conventions** — resource names follow a documented
  prefix / environment-tagged pattern (`<env>-<service>-<role>`).
- **Tagging / labelling** — every taggable resource carries a
  consistent set (`Environment`, `Owner`, `CostCenter`,
  `ManagedBy = "Terraform"`, etc.).
- **Module structure** — `main.tf`, `variables.tf`, `outputs.tf`,
  `versions.tf`, `README.md` in every module; locals separated
  from main.tf where logic is non-trivial.
- **IAM least privilege** — policies scoped to specific actions
  / resources; no `*` action on resource policies; no
  `Principal = "*"` without explicit justification.
- **Lifecycle protections** — `prevent_destroy = true` on
  stateful resources (databases, storage with persistent data);
  `create_before_destroy` where rolling replacements matter.

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New resources**: tagged consistently? Naming follows the
  project's convention? Sensitive attributes (passwords,
  connection strings) sourced from variables / data sources
  rather than hardcoded? Lifecycle protections applied if the
  resource holds persistent data?
- **New variables**: `type` declared? `description` populated?
  `default` only where genuinely defaulted (not hiding required
  config)? `sensitive = true` when appropriate? `validation`
  blocks for inputs with constrained ranges?
- **New modules**: locally defined modules under `modules/`
  follow the documented structure? Module README updated?
  Module versions pinned when sourced remotely?
- **New `count` / `for_each` patterns**: idempotent (changing
  the count without reshuffling identity)? `for_each` over
  resource maps preferred to `count` where the elements have
  meaningful keys.
- **New `terraform_remote_state` / `data` sources**: pointed at
  the correct backend and key? Read-only consumption (not
  writes via side effects)?
- **New provider configurations**: aliases for multi-region /
  multi-account setups documented and used consistently?
- **New `local` blocks**: doing computation rather than just
  alias-flattening — flag if the local does substantial work
  (might justify a module or external script).
- **Committed state**: `terraform.tfstate` /
  `terraform.tfstate.backup` / `.terraform/` accidentally
  tracked? Flag as a critical issue regardless of milestone
  scope.
- **New TODO / FIXME comments in `.tf` files**: list every one.

---

## §4 — Full-sweep regression check

### Provider / state hygiene
- Provider versions unpinned or pinned loosely (`>=` rather than
  `~>`).
- Terraform version not pinned in `required_version`.
- Backend config drifted between environments (e.g. one env uses
  a state file in a different bucket).
- Multiple backend definitions in the same root module.

### Resource hygiene
- Resources without tags / labels (where the cloud supports
  them).
- Hardcoded values that should be variables or data sources
  (regions, account IDs, ARNs, project IDs, subscription IDs).
- Sensitive values stored as plain strings (passwords, API
  keys, tokens, connection strings).
- Missing `prevent_destroy` on stateful resources
  (production databases, object storage with user data,
  key-vaults).
- Stateful resources without backup / replication configured
  per the project's documented disaster-recovery posture.

### IAM and security
- Policies with `Action = "*"` or `Resource = "*"` without
  documented justification.
- Public S3 buckets / storage accounts / blob containers
  without explicit `BlockPublicAccess` / public-access
  controls.
- Security groups / firewall rules opening `0.0.0.0/0` to
  privileged ports (22, 3389, db ports).
- IAM users / service principals created where roles or
  managed identities would do.

### Modules and reuse
- Same resource block repeated across environments — should be
  a module.
- Modules without a README documenting inputs / outputs /
  examples.
- Modules with more than ~20 input variables (too granular —
  consider object types or sub-modules).
- Modules sourced from `git::` without a `?ref=` pinning a tag
  or commit.

### Workspaces / environments
- Environment-specific values leaking into shared code (string
  comparisons against workspace names in resource bodies
  rather than via `var.environment`).
- Test / staging configuration that escalates to production
  privileges (cross-account role assumptions without scope).

### Style and structure
- `.tf` files longer than ~500 lines (consider splitting by
  resource category).
- Inconsistent quoting / formatting (`terraform fmt` not run).
- Comments explaining WHAT the code does (the code is the
  declaration); comments explaining WHY are fine.
- `null` defaults where the variable should be required.

### Dependency hygiene
- Modules duplicating logic that a shared module could absorb.
- Resources implicitly depending on each other via reference
  but logically depending in another order — explicit
  `depends_on` missing when needed.

---

## §4.5 — Extraction

### Module decomposition

- Any root module's `main.tf` longer than ~500 lines (signal:
  split by resource category, or extract a module).
- Any resource pattern repeated in two or more places (same
  resource type with similar inputs, just different names) —
  candidate for a module.
- Any environment folder copying root-module bodies — should
  reuse a module with environment-specific inputs.

### Local / computation extraction

- Any `local` block doing non-trivial computation (object
  shaping, conditional logic) that recurs in multiple modules
  — extract to a shared module's `locals.tf` or to a separate
  module that publishes the computed value as an output.

### Variable consolidation

- Any module with 20+ flat input variables — consider grouping
  related inputs into an `object` type variable.

### Promotion candidates

- Any locally-defined module that's been stable for a while and
  is used by two or more callers — candidate for promotion to
  a shared module registry (private terraform registry,
  org-wide module repo).

---

## §5 — Drift counter (Terraform rule set)

| Rule | Violations |
|---|---|
| Resources missing tags / labels | N |
| Hardcoded regions / accounts / project IDs | N |
| `*` actions / resources in IAM / RBAC policies | N |
| Open `0.0.0.0/0` to privileged ports | N |
| Unpinned provider versions | N |
| Modules sourced from `git::` without `?ref=` | N |
| TODO / FIXME comments in `.tf` files | N |
| `.tf` files > 500 lines | N |
| Modules with > 20 input variables | N |
| Stateful resources without `prevent_destroy` | N |

Adapt the rows to match what the project actually documents.
