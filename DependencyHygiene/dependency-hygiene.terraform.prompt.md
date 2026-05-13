# Dependency hygiene — Terraform variant

Audit a Terraform / OpenTofu codebase's provider, module, and
backend dependencies.

**This prompt extends [`core/dependency-hygiene.core.prompt.md`](./core/dependency-hygiene.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Steps 2–6 audit categories, Step 7 report
format, and the Constraints). This file supplies the Terraform-
specific commands, manifest paths, and ecosystem gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Tool**: Terraform 1.x or OpenTofu (commands largely
  interchangeable; `terraform` below means whichever the project
  uses — detect from CI / wrapper scripts).
- **Manifest**: `terraform { required_providers { … } }` block,
  conventionally in `versions.tf` or `providers.tf` per module.
- **Lockfile**: `.terraform.lock.hcl` per workspace root. Pins
  provider versions and checksums.
- **Modules**: declared via `module "x" { source = "…" version = "…" }`
  blocks. The `source` can be a registry, git, local path, or S3.

Terraform's "deps" are a different shape from language ecosystems:

- **Providers** — third-party plugins (hashicorp/aws, etc.).
- **Modules** — reusable HCL packaged from a registry, git, or
  local path.
- **Backends** — state storage; not versioned per se, but a backend
  change is a dep change.
- **Terraform / OpenTofu CLI itself** — pinned via
  `required_version`.

All four belong in this audit.

---

## §1 — Inventory commands

```sh
# Workspace roots — directories containing terraform { ... } blocks
grep -rlE '^\s*terraform\s*\{' --include='*.tf' .

# Provider declarations
grep -rhE '(required_providers|source\s*=)' --include='*.tf' . | sort -u

# Module declarations
grep -rhE '^\s*module\s+"' --include='*.tf' . | sort -u

# Lockfiles per workspace
find . -name '.terraform.lock.hcl' -not -path '*/.terraform/*'

# CLI version pin
grep -rhE 'required_version' --include='*.tf' . | sort -u

# Tool version actually in use
terraform version
```

Report each workspace root as its own entry in the inventory — a
monorepo with several Terraform workspaces gets one audit pass per
workspace (run separately) or a merged report (note clearly).

---

## §2 — Outdated

### Providers

`terraform init -upgrade` is the upgrade command but it mutates the
lockfile. To check what *would* upgrade without writing:

```sh
terraform providers              # current resolved versions per workspace
terraform providers lock         # generate fresh lockfile contents in a temp dir
```

For each provider, query the registry for the latest release:

```sh
curl -s "https://registry.terraform.io/v1/providers/<namespace>/<name>" \
  | jq '.version, .versions[-3:]'
```

(For OpenTofu, swap `registry.terraform.io` for `registry.opentofu.org`.)

Categorise:

- Major-behind: provider major version gap (note: providers don't
  strictly follow semver — read the changelog).
- Minor-behind / patch-behind.

### Modules

For each `module` block with a registry source, query the registry:

```sh
curl -s "https://registry.terraform.io/v1/modules/<namespace>/<name>/<provider>" \
  | jq '.version'
```

For git-sourced modules, list current ref vs upstream HEAD:

```sh
# Given a git source like git::https://github.com/org/repo.git?ref=v1.2.0
gh api repos/<owner>/<repo>/releases/latest --jq '.tag_name'
```

Local path modules don't have versions — skip them.

### Terraform / OpenTofu CLI

Compare the project's `required_version` against the latest stable
on the project's tool. EOL'd minor versions are ⚠️ HIGH (no security
patches).

---

## §3 — Vulnerabilities

Terraform has no first-party advisory feed. Use Trivy and the
GitHub Advisory DB for module / provider source repos:

```sh
trivy config --severity HIGH,CRITICAL .       # misconfig + some CVE for providers
tfsec . --format json                         # legacy / community equivalent
```

`tfsec` and `trivy config` find policy violations more than CVEs
(IAM-overbroad, public buckets, etc.). Surface them as a *separate*
section from CVE-style advisories — they're related but not the
same shape.

For provider CVEs, the GitHub repo of the provider is the practical
source:

```sh
gh api repos/hashicorp/terraform-provider-<name>/security-advisories
```

If a provider repo lists advisories newer than the project's pinned
version, flag them.

---

## §4 — Unused / missing

```sh
# Declared providers
grep -rhE 'source\s*=\s*"[^"]+"' --include='*.tf' . | sort -u

# Resources / data sources used
grep -rhE '^\s*(resource|data)\s+"[a-z0-9_]+"' --include='*.tf' . \
  | sed -E 's/^\s*(resource|data)\s+"([a-z0-9_]+)".*/\2/' | sort -u
```

Each resource type's prefix (`aws_`, `google_`, `azurerm_`, …) maps
to a provider. A declared provider with no matching resources / data
sources is unused. Surface as a candidate; verify by also checking:

- `provider` blocks with explicit aliases — sometimes a provider is
  used via alias rather than via resources.
- Terraform functions that reference providers (rare but possible
  with `provider_meta`).

Modules: a `module` block exists in source by definition — modules
can't be "unused" in this static sense. But check for stale module
versions where the upstream module has been deprecated / archived
(`gh api repos/<owner>/<repo> --jq '.archived'`).

---

## §5 — Lockfile drift

```sh
terraform init -lockfile=readonly         # fails if lockfile would need updating
terraform providers lock -platform=<platforms> # for multi-platform pins
```

The `-lockfile=readonly` flag treats the existing lockfile as
authoritative. A failure is ⚠️ ISSUE — `required_providers`
constraints have changed but the lockfile wasn't refreshed.

Also worth checking: `.terraform.lock.hcl` should contain checksums
for **every platform the project deploys from**. A lockfile generated
on a single developer's macOS but applied from a Linux CI runner is
a drift source — the lockfile fails to validate.

```sh
grep -E '^\s*h1:|^\s*zh:' .terraform.lock.hcl | wc -l
```

If only one platform is pinned, recommend regenerating with
`-platform=linux_amd64 -platform=darwin_arm64 -platform=…` covering
every place `terraform` is run.

---

## §6 — Duplicates / version conflicts

Multiple modules can transitively pin different versions of the same
provider. `terraform init` resolves this to a single version, but
the resolution may not be what you'd expect:

```sh
terraform providers           # shows the resolution tree
```

For each provider, list the required_providers constraints from
every module that requests it. If two modules pin
mutually-incompatible ranges, surface as ⚠️ ISSUE.

Workspaces in the same repo using different versions of the same
provider is *not* a conflict — each workspace resolves
independently. But it is worth listing in the report as a
consistency observation.

---

## §7 — Terraform-specific report rows

Add to the audit header:

- Tool: `Terraform <version> | OpenTofu <version>`.
- `required_version` constraint.
- Workspaces audited: <list>.
- Backends in use: <list> (s3, gcs, azurerm, remote, …).

Recommendations should specify the workspace:

- "Bump `hashicorp/aws` from `5.30` to `5.70` in
  `infra/prod/versions.tf`. Run `terraform init -upgrade` in that
  directory."
- "Migrate the git-pinned `vpc` module in `infra/staging/main.tf`
  from `ref=v3.14.0` to `ref=v5.5.3`. Read the v4 changelog before
  applying — there's a known breaking change in subnet output
  shape."

---

## Constraints (Terraform-specific addenda)

- Never run `terraform apply`, `terraform init -upgrade`, or
  `terraform providers lock` against the real backend. The audit
  is read-only. `terraform init -lockfile=readonly` and
  `terraform providers` (no flags) are safe.
- A backend that has changed type (e.g. local → S3) without
  `terraform init -migrate-state` is its own ⚠️ HIGH — surface it
  but don't act.
- Don't recommend "use the latest provider version" blindly —
  Terraform providers can have major-version breaking changes that
  require resource imports / state migrations (e.g. AWS provider
  v4→v5 renamed many resource attribute paths). Always recommend
  reading the upstream upgrade guide and call out provider migrations
  that require state operations.
- Module versions sourced from local paths can't be audited for
  staleness — flag in the inventory if local-path modules dominate
  (it's a sign the project is missing a registry / module shared
  layer).
- `tfsec` / `trivy config` policy findings (overbroad IAM,
  unencrypted volumes, public S3) are *important* but not "dep
  hygiene" findings. Surface them in a separate Policy section so
  they don't drown out actual version / vulnerability findings.
