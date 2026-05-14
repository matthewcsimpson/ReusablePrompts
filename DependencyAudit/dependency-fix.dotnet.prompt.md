---
description: Action findings from dependency-audit-dotnet. Vuln fixes, bumps by risk band, removals, lockfile re-resolution. Verify build + tests per category, local commits only.
related: [dependency-audit-dotnet]
---

# Dependency fix — .NET variant

Action findings from a `dependency-audit-dotnet` report against a
.NET / NuGet project.

**This prompt extends [`core/dependency-fix.core.prompt.md`](./core/dependency-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
.NET-specific commands, risk hints, and ecosystem gotchas.

---

## Detect project layout

- `*.csproj` with `<PackageReference>` entries → SDK-style project
  (.NET Core / .NET 5+).
- `Directory.Packages.props` → Central Package Management (CPM); all
  versions live in this file, not in individual `*.csproj`.
- `packages.config` → legacy MSBuild project (.NET Framework). Edits
  differ — flag if encountered.
- `global.json` → SDK pinning; bumps to SDK itself are separate from
  package bumps.
- `*.sln` → solution file aggregating projects.

If CPM is in use, all `<PackageVersion>` edits go in
`Directory.Packages.props`. Individual `*.csproj` files only declare
`<PackageReference Include="..." />` without a version.

---

## §1 — Vulnerabilities

```sh
# Per-project (run from each .csproj or solution)
dotnet list package --vulnerable --include-transitive --format json

# Modern (preview, but increasingly common)
dotnet nuget audit
```

Apply targeted fix:

```sh
# Per-project (non-CPM)
dotnet add <ProjectName> package <PackageName> --version <fix-version>

# Central Package Management — edit Directory.Packages.props
# Find the <PackageVersion Include="<dep>" Version="..." />
# Update Version attribute, then:
dotnet restore
```

For transitive vulns without a direct upgrade, use `<PackageReference
... />` on the *direct* dep that pulls in the vulnerable transitive,
or add a direct reference to the patched transitive version:

```xml
<!-- In the .csproj or Directory.Packages.props -->
<PackageReference Include="<vuln-transitive>" Version="<fix-version>" />
```

Note the pin in the commit message.

---

## §2 — Outdated bumps

```sh
# List per-project
dotnet list package --outdated --include-transitive --format json

# Tool-assisted (popular community tool)
dotnet outdated --upgrade <dep>
```

Apply manually for predictability:

```sh
# Non-CPM
dotnet add <Project> package <Package> --version <target>

# CPM — edit Directory.Packages.props, then restore
dotnet restore
```

Risk-band hints:

- `risk:low` — patch bumps + minors on framework-adjacent packages
  (`Microsoft.Extensions.*`, `xunit.*`, `Moq`, analyzers).
- `risk:med` — arbitrary minors for direct deps.
- `risk:high` — majors. Read the package's CHANGELOG / migration guide
  before action. For runtime majors (`Microsoft.AspNetCore.*`,
  `EntityFrameworkCore`), the migration typically requires source
  edits — flag for human review rather than auto-applying.

For `1.0.0-preview*` / `*-rc.*` / `*-beta.*` pre-release versions,
treat any version change as effectively major.

---

## §3 — Unused removals

Re-grep before removal. NuGet packages can be referenced indirectly:

```sh
# Source references (using statements, fully-qualified types)
rg "using\s+<root-namespace>;|<root-namespace>\." --type cs .

# Analyzer / source-generator packages aren't imported in source —
# check project files
rg "<PackageReference.*<dep>" --type xml -g '*.csproj' -g '*.props'

# Tool references (dotnet tools)
rg "<dep>" .config/dotnet-tools.json global.json
```

If grep is clean:

```sh
# Non-CPM
dotnet remove <Project> package <PackageName>

# CPM — remove the <PackageReference> from .csproj files,
# then remove the <PackageVersion> from Directory.Packages.props.
dotnet restore
```

Roslyn analyzers (`Microsoft.CodeAnalysis.*`,
`StyleCop.Analyzers`) have no source references — they apply at
compile time. Don't remove without checking the project's
`.editorconfig` and CI lint config.

---

## §4 — Missing additions

If a package is imported (`using X;`) but not declared:

```sh
# Look up the version already in the dependency graph
dotnet list package --include-transitive --format json | \
  jq '.projects[].frameworks[].topLevelPackages, .projects[].frameworks[].transitivePackages | map(select(.id == "<dep>"))'
```

Pin to the resolved transitive version:

```sh
# Non-CPM
dotnet add <Project> package <PackageName> --version <version>

# CPM — add to Directory.Packages.props
```

Decide which project gets the reference based on where the `using` is
needed. In a multi-project solution, prefer adding to the lowest
project in the graph that uses it (avoid bloating common libraries).

---

## §5 — Lockfile drift

.NET's "lockfile" is opt-in via `<RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>` in the `.csproj`. If lockfiles exist:

```sh
# Verify the lockfile matches
dotnet restore --locked-mode

# Re-generate after manifest changes
dotnet restore --force-evaluate
```

If lockfiles aren't in use, drift is detected differently — by
comparing `packages.lock.json` (if generated for CI use) or by
checking that `dotnet restore` doesn't change versions silently.

---

## §6 — Duplicates

Without CPM, different projects in the same solution can reference
different versions of the same package — that's the .NET equivalent
of npm duplicates:

```sh
# Find version conflicts across projects
dotnet list package --include-transitive --format json | \
  jq -r '[.projects[].frameworks[].topLevelPackages[]] | group_by(.id) | map(select(length > 1)) | .[] | "\(.[0].id): \(map(.requestedVersion) | unique | join(", "))"'
```

The fix is usually one of:

1. Adopt CPM — move all versions to `Directory.Packages.props`. (Big
   change; flag rather than auto-apply.)
2. Unify the version manually across each project's `.csproj`.

For NuGet binding redirects in .NET Framework projects, the duplicate
may live in `app.config` / `web.config`. Surface those separately.

---

## §7 — Verification

After **each** category's action:

```sh
# Restore (lockfile-aware if applicable)
dotnet restore

# Build everything
dotnet build --no-restore --warnaserror

# Test
dotnet test --no-build

# Format / lint if configured
dotnet format --verify-no-changes
```

A clean restore + build (warnings as errors) + passing tests is the
gate.

---

## §8 — Constraints (.NET-specific addenda)

- Do not edit `<TargetFramework>` to "fix" a missing package. The
  framework version is a deliberate project decision; bumping it is
  out of scope for a dep fix.
- Do not remove a package referenced via `<PackageReference>` with
  `IncludeAssets="analyzers"` without checking the project's lint
  rules — those packages contribute only at compile time.
- If the project uses `<PrivateAssets>` to control transitive
  exposure, respect existing settings when re-adding deps.
- For multi-targeted projects (`<TargetFrameworks>net6.0;net8.0</TargetFrameworks>`),
  ensure the bumped version supports all target frameworks. Check
  the package's NuGet.org `Dependencies` tab.
- `global.json`'s SDK version pin is **not** in scope for this fix.
  Bumping the SDK is a separate, project-wide change.
- For solutions with many projects, prefer per-solution commands
  (`dotnet build`, `dotnet test`) over per-project — they catch
  cross-project version conflicts the per-project view misses.
- `Directory.Build.props` may inject implicit package references
  ('legacy' MSBuild). Check it if a "missing" dep seems impossible.
