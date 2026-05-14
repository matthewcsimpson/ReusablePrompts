---
description: Action findings from dependency-audit-terraform. Bumps providers / modules / backends, multi-platform re-lock (darwin / linux), gates on terraform plan showing 0 resource changes. Local commits only.
related: [dependency-audit-terraform]
---

# Dependency fix — Terraform variant

Action findings from a `dependency-audit-terraform` report against a
Terraform / OpenTofu codebase.

**This prompt extends [`core/dependency-fix.core.prompt.md`](./core/dependency-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
Terraform-specific commands, risk hints, and ecosystem gotchas.

---

## Detect Terraform / OpenTofu

- `.terraform.lock.hcl` → standard provider lock (Terraform 0.14+).
- `versions.tf` → typical location for `required_providers` /
  `required_version`.
- `.terraform/` → cached provider binaries (gitignored).
- `*.tofu` files or an OpenTofu CI workflow → OpenTofu. Commands map
  one-to-one (`tofu` instead of `terraform`).

Identify whether the codebase is a single root module or a multi-root
setup (one root per environment / stack). Commands below run **per
root module** — pass `-chdir=<path>` or `cd` into each.

---

## §1 — Vulnerabilities

Terraform's official tooling has no built-in CVE check. Use:

```sh
# Static scanners
tfsec
trivy config <path>
checkov -d <path>
```

Most "vulnerabilities" in Terraform are *misconfigurations* (open
security groups, unencrypted volumes), not version-CVEs. Those are
out of scope for this fix — flag them and let the user run a
security audit separately.

For **provider** vulnerabilities (rare but real), bump:

```hcl
# versions.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"   # was ">= 5.30.0", pinned past a vuln release
    }
  }
}
```

Then:

```sh
terraform init -upgrade
terraform providers lock
```

---

## §2 — Outdated bumps

```sh
# What's installed vs what's available
terraform providers
terraform version
terraform init -upgrade -plugin-dir=...  # if using mirrored plugins

# Module versions — manual lookup; the registry is the source of truth.
# For each `module "x" { source = "X" version = "Y" }` block, check the
# upstream's tags or registry page.
```

Apply by editing the `version` constraint, then init:

```hcl
# versions.tf or main.tf
required_providers {
  aws = {
    source  = "hashicorp/aws"
    version = ">= 5.50.0, < 6.0.0"
  }
}

# Module version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.4"      # was "~> 5.2"
}
```

```sh
terraform init -upgrade
```

Risk-band hints:

- `risk:low` — patch bumps to providers and modules within an
  existing minor.
- `risk:med` — minor bumps. Most providers (AWS, GCP, Azure) ship
  new resources / attributes in minors without breaking; some
  deprecate attributes.
- `risk:high` — major provider bumps (e.g. `aws` 4→5). Read the
  provider's upgrade guide; many require `terraform state mv` /
  resource rewrites. Flag rather than auto-apply.

For Terraform-CLI bumps (`required_version`), that's a project-wide
change — out of scope for a deps pass, surface and skip.

---

## §3 — Unused removals

In Terraform, "unused" usually means:

- A `provider` block declared but no resource uses it.
- A `module` block declared but the module's outputs / resources are
  not referenced.
- An import of a module that's now superseded.

Re-grep:

```sh
# Are any resources / data sources using this provider?
rg "^resource\s+\"<provider>_" --type tf .
rg "^data\s+\"<provider>_" --type tf .

# Is the module's output / name referenced?
rg "module\.<module-name>\." --type tf .
```

If unreferenced, remove the block. Then:

```sh
# Re-lock providers (in case removing one changes the resolution)
terraform init -upgrade
terraform providers lock

# Validate
terraform validate
```

If removal causes a state mismatch, you may need:

```sh
terraform state rm '<resource-path>'   # destructive on state, not on cloud
```

**Confirm with the user** before any `state rm` — removing a resource
from state without destroying it is a deliberate operational choice.

---

## §4 — Missing additions

If a Terraform file references a provider not declared in
`required_providers`:

```sh
# Find unrecognised provider prefixes
terraform validate    # surfaces them as errors
```

Add to `versions.tf`:

```hcl
required_providers {
  newone = {
    source  = "<registry>/<namespace>/<provider>"
    version = "~> X.Y"
  }
}
```

Then:

```sh
terraform init
terraform providers lock
```

For modules, the `source` and `version` fields must both be set
unless using a local path. The audit will have flagged missing
`version` pins separately — fix them by pinning to the registry's
current.

---

## §5 — Lockfile drift

```sh
# .terraform.lock.hcl drift — terraform reports during init
terraform init     # warns if lockfile and required_providers disagree

# Refresh the lockfile across all platforms the project supports
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64
```

The multi-platform lock is important — CI usually runs Linux, devs
run macOS, and the lockfile must cover both. A single-platform lock
breaks CI on a different OS.

---

## §6 — Duplicates

In a multi-root setup, the same provider may be pinned at different
versions across roots. The audit will have surfaced this. The fix:

```sh
# Find each root's pin
rg "^\s*aws\s*=\s*\{" --type tf -A3

# Unify the version constraint across all roots' versions.tf,
# then per root:
terraform init -upgrade
terraform providers lock -platform=...
```

For modules pulled in via different paths but resolving to the same
upstream, ensure the version constraints don't diverge silently.

---

## §7 — Verification

After **each** category's action, per root module:

```sh
# Validate syntax + provider compatibility
terraform validate

# Plan against the actual state — surfaces resource diffs
terraform plan -out=tfplan
terraform show -json tfplan | jq '.resource_changes | map(.change.actions) | flatten | unique'

# A "no changes" plan after a bump is the gate — bumps shouldn't
# silently move infrastructure. If `terraform plan` produces
# unexpected changes, the bump altered defaults or computed values;
# investigate before committing.

# Format / lint
terraform fmt -check -recursive
tflint                                  # if configured
```

A `terraform plan` showing 0 resource changes after a deps fix is the
correct outcome. Non-zero changes need explanation in the commit
message ("provider 5.40 changed default for X — accepted").

**Do not** run `terraform apply`. The fix prompt edits configuration
files; applying is the user's call after review.

---

## §8 — Constraints (Terraform-specific addenda)

- Do not run `terraform apply` under any circumstances. The output
  is plans and config edits.
- Do not edit `.terraform.lock.hcl` by hand. Always regenerate via
  `terraform providers lock`.
- Do not delete `.terraform/` to "fix" a problem unless `terraform
  init` instructed you to. The cache may have legitimate content.
- Major provider bumps that require `state mv` / `state rm` /
  resource rewrites are **out of scope** for this fix prompt.
  Surface them with the provider's upgrade-guide link and stop.
- `required_version` bumps (Terraform CLI itself) are out of scope.
- `terraform_remote_state` data sources may reference outputs that
  changed between versions of the producer's Terraform. A bump on
  a producer module is also a change to consumers — flag the
  cross-root impact.
- Workspace-aware projects (`terraform workspace`) apply changes per
  workspace; verify the plan in each.
- For OpenTofu users (`tofu` command), all the above commands map
  1:1. Do not silently switch from `terraform` to `tofu` or vice
  versa without the user's direction.
