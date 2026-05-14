---
description: Audit a .NET / NuGet project for outdated versions, known vulnerabilities, unused or missing declarations, lockfile drift, and duplicate versions.
related: [dependency-fix-dotnet]
---

# Dependency audit — .NET variant

Audit a .NET / C# project using NuGet.

**This prompt extends [`core/dependency-audit.core.prompt.md`](./core/dependency-audit.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Steps 2–6 audit categories, Step 7 report
format, and the Constraints). This file supplies the .NET-specific
commands, manifest paths, and ecosystem gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Runtime**: .NET (Core 6+, including .NET 6 / 7 / 8 / 9).
- **Manifest**: `*.csproj` (or `*.fsproj` / `*.vbproj`); optionally
  `Directory.Packages.props` for Central Package Management.
- **Lockfile**: `packages.lock.json` per project (only present when
  `RestorePackagesWithLockFile` is set in the project).
- **Solution**: optional `*.sln` listing the projects.

The audit is more useful when CPM (`Directory.Packages.props`) is in
use — versions are managed in one place rather than scattered across
`.csproj` files. Note in the inventory whether CPM is enabled.

---

## §1 — Inventory commands

```sh
# Solution + project discovery
find . -name '*.sln' -not -path '*/bin/*' -not -path '*/obj/*'
find . \( -name '*.csproj' -o -name '*.fsproj' -o -name '*.vbproj' \) \
  -not -path '*/bin/*' -not -path '*/obj/*'

# Central Package Management
ls -1 Directory.Packages.props 2>/dev/null

# Lockfile presence per project
find . -name 'packages.lock.json' -not -path '*/bin/*' -not -path '*/obj/*'

# Target frameworks (worth reporting)
grep -hE '<TargetFramework[s]?>' $(find . -name '*.csproj' -not -path '*/bin/*') | sort -u
```

---

## §2 — Outdated

```sh
dotnet list package --outdated --format json
dotnet list package --outdated --include-transitive --format json
```

Categorise:

- **Major-behind direct** — top of the priority list.
- **Minor-behind direct** — secondary, unless on a security-sensitive
  package (auth, ASP.NET Core, EF Core).
- **Patch-behind direct** — group and report count.
- **Transitive** — list top 10 worst; transitive bumps usually follow
  a direct upgrade.

Also catch deprecated packages, which `--outdated` won't surface:

```sh
dotnet list package --deprecated --format json
```

`Deprecated` is its own category — a deprecated package isn't merely
old, it has been formally end-of-lifed. Treat as ⚠️ HIGH regardless
of version gap.

---

## §3 — Vulnerabilities

```sh
dotnet list package --vulnerable --format json
dotnet list package --vulnerable --include-transitive --format json
```

The output includes severity (`Low | Moderate | High | Critical`)
and an advisory URL. Capture for each finding:

- Severity (tool-reported).
- Package + current version.
- Fix version per `dotnet`'s remediation hint (or `no fix yet`).
- Direct vs transitive.

For transitive vulnerabilities, identify the top-level package that
brings them in — `dotnet list package --include-transitive` doesn't
give the chain, but `dotnet nuget why` does:

```sh
dotnet nuget why <project> <vulnerable-package>
```

Reachability assessment is often easier in .NET than in dynamic
languages: ASP.NET pipelines and EF Core surfaces are well-defined,
so "is this code path actually invoked" is answerable for many
advisories. State your assessment as a separate field.

---

## §4 — Unused / missing

There's no widely-adopted equivalent of `depcheck` for .NET. Use a
combination:

```sh
# Every PackageReference declared
grep -rhE '<PackageReference' --include='*.csproj' . \
  | sed -E 's/.*Include="([^"]+)".*/\1/' | sort -u

# Cross-reference against `using` directives and full-namespace usages
grep -rhE '^\s*using\s+\w' --include='*.cs' . \
  | sed -E 's/using\s+([a-zA-Z0-9_.]+);.*/\1/' | sort -u
```

Match package names to root namespaces (`Newtonsoft.Json` →
`Newtonsoft.Json`; `Serilog` → `Serilog`; `Microsoft.Extensions.*`
maps to several). A package with no matching `using` *and* no
runtime registration (`builder.Services.Add*`, `app.Use*`) in the
project is a candidate for ⚠️ ISSUE — but verify carefully.

Watch for packages that are intentionally pulled in for their
build-time effect, not for runtime API surface:

- Source generators (`Microsoft.Extensions.Logging.Abstractions`'s
  `LoggerMessage` generator, `Mapster`, `MediatR.SourceGenerators`).
- MSBuild SDKs and tasks.
- Analyzers (`Microsoft.CodeAnalysis.NetAnalyzers`,
  `StyleCop.Analyzers`).

These look unused by namespace inspection but absolutely are. Don't
flag them.

---

## §5 — Lockfile drift

If the project uses `packages.lock.json`:

```sh
dotnet restore --locked-mode
```

A failure with `NU1004` means the lockfile is out of date relative
to the project files — ⚠️ ISSUE.

If the project does *not* use lockfiles, note it. For an
"app-shaped" project (not a library), recommend enabling
`RestorePackagesWithLockFile` — reproducible restores are otherwise
not guaranteed.

---

## §6 — Duplicates / version conflicts

```sh
dotnet list package --include-transitive --format json | \
  jq '[.projects[].frameworks[].topLevelPackages[], .projects[].frameworks[].transitivePackages[]] | group_by(.id) | map(select(length > 1)) | .[] | {id: .[0].id, versions: [.[].resolvedVersion] | unique}'
```

This surfaces packages where multiple resolved versions exist across
projects in the solution. Pay particular attention to:

- `Microsoft.Extensions.*` family (logging, DI, options) — version
  skew here causes runtime DI failures.
- `System.Text.Json` — known for breaking-change pain between
  majors.
- ASP.NET Core runtime packages — should generally match the
  TargetFramework, not float.

Also check `NU1605` / `NU1608` warnings from a clean restore — those
are NuGet's own version-conflict signals.

---

## §7 — .NET-specific report rows

Add to the audit header:

- TargetFramework(s) in use.
- Central Package Management: enabled / disabled.
- Lockfile mode: enabled / disabled per project.
- LTS vs current: .NET 6 EOL'd Nov 2024; .NET 8 is current LTS.
  Flag projects on an EOL or near-EOL TFM.

Recommendations should be project-qualified in a multi-project
solution:

- "Bump `Serilog` from `3.1.1` to `4.0.0` in `src/Api/Api.csproj`."

If CPM is enabled, the bump happens once in
`Directory.Packages.props` — call that out so the user doesn't edit
the project file by mistake.

---

## Constraints (.NET-specific addenda)

- Don't flag analyzers, source generators, or MSBuild SDK packages
  as unused based on `using` directives alone — they have no runtime
  imports.
- A `TargetFramework` past EOL is its own ⚠️ HIGH finding, separate
  from the dep audit. Surface it in the Summary.
- `dotnet list package --vulnerable` reports against the *resolved*
  graph, not the manifest. If projects in the solution have
  different resolved versions, run it per-project, not at the
  solution level.
- The NuGet floating-version syntax (`1.2.*`, `[1.2,2.0)`) means
  "outdated" depends on what the float resolves to today. Note any
  floating versions as a separate finding — they undermine
  reproducible builds.
