---
description: Audit a .NET / C# codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
related: [post-milestone-fix]
---

# Post-milestone audit — .NET / C# variant

Audit a .NET (C#) codebase after a milestone tag is cut.

**This prompt extends [`core/post-milestone-audit.core.prompt.md`](./core/post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window
logic, convention-source discovery, delta logic, output format,
and constraints. This file supplies the .NET / C# specifics for
§2 examples, §3 milestone-diff focus, §4 regression sweeps, §4.5
extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: C# 10+ (records, file-scoped namespaces, nullable
  reference types).
- **Runtime**: .NET 6+ (LTS or current).
- **Framework**: ASP.NET Core for web / API; minimal APIs or MVC
  controllers; or worker services / console apps.
- **Data**: typically Entity Framework Core with code-first
  migrations.
- **DI**: Microsoft.Extensions.DependencyInjection.
- **Logging**: Microsoft.Extensions.Logging (often with Serilog
  underneath).
- **Tests**: xUnit, NUnit, or MSTest.
- **Build**: `dotnet` CLI with `.sln` / `.csproj` project files.
- **Package manager**: NuGet.

If the project deviates (Blazor Server / WASM, MAUI, Unity), fall
back to the generic categories where the variant's checks don't
apply.

---

## §2 — Per-rule sweep (.NET / C# rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `*.csproj` files — `Nullable`, `TreatWarningsAsErrors`,
  `LangVersion`, `TargetFramework`, package references.
- `Directory.Build.props` / `Directory.Packages.props` — repo-wide
  build settings, centralised package versions.
- `.editorconfig` — code style rules enforced by the IDE and
  `dotnet format`.
- `global.json` — SDK version pin.
- `appsettings*.json` and any custom config providers — to
  identify settings used in code.

Common rule categories the project's docs tend to enforce —
sweep each one that's actually documented:

- **Language / spelling** — locale conventions in code, comments,
  identifiers, DB column names.
- **File / type structure** — one public type per file; file name
  matches type name; file-scoped namespaces (`namespace Foo;`)
  vs block-scoped.
- **Nullable reference types** — `#nullable enable` at file or
  project level; consistent use of `?` for nullable.
- **Async patterns** — `Task` / `Task<T>` return types named with
  `Async` suffix; no `async void` outside event handlers; no
  blocking on tasks (`.Result`, `.Wait()`, `.GetAwaiter().GetResult()`).
- **DI registration** — services registered in the composition
  root (e.g. `Program.cs` / `Startup.cs`), lifetimes chosen
  deliberately (Singleton / Scoped / Transient).
- **Configuration access** — `IOptions<T>` / `IOptionsSnapshot<T>`
  preferred over raw `IConfiguration`; options validated at
  startup.
- **Migrations** — EF Core migrations immutable after applied;
  use `git log --follow` on each `Migrations/*.cs` file to detect
  edits after initial commit.
- **Naming** — PascalCase for public, camelCase for parameters /
  locals, `_camelCase` for private fields, `I` prefix for
  interfaces.
- **Logging** — `ILogger<T>` via DI; structured logging
  (`logger.LogInformation("User {UserId} signed in", userId)`)
  rather than string concatenation.
- **Testing** — required colocated test projects; test naming
  convention (e.g. `MethodName_Condition_Expectation`); no
  `[Skip]` without comment.

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New controllers / minimal-API endpoints**: `[Authorize]` /
  policy applied? Input validated (data annotations / FluentValidation)?
  Return type uses the project's `Result<T>` / `IResult` / problem-details
  convention? Resource ownership verified before privileged
  operations?
- **New services**: registered in the DI container? Lifetime
  chosen appropriately (Singleton for stateless, Scoped for
  per-request, Transient for cheap-to-create)? Captive
  dependencies avoided (Singleton holding a Scoped dependency)?
- **New DbContext models or migrations**: migration `Up()` and
  `Down()` both implemented? Foreign keys named consistently?
  Indexes added where the query patterns demand them?
- **New `async` methods**: return `Task` or `Task<T>` named with
  `Async` suffix? `CancellationToken` parameter where the call
  chain has one? No `.Result` / `.Wait()`?
- **New `using` statements with `IDisposable`** — disposed
  correctly (`using` declaration or block)?
- **New settings reads** (`IConfiguration` / `IOptions<T>`) —
  registered via `services.Configure<T>()` and validated?
- **New dependencies in `.csproj`** — justified by the diff?
  Centralised in `Directory.Packages.props` if the project uses
  it?
- **New TODO / HACK / FIXME comments**: list every one with file
  and line.
- **New `Console.WriteLine` / `Debug.WriteLine`**: list every
  instance — these are the .NET equivalent of `console.log`
  leaks.

---

## §4 — Full-sweep regression check

### Language quality
- Nullable warnings suppressed without justification
  (`#pragma warning disable nullable`, `!` null-forgiving operator).
- `dynamic` used where a typed alternative fits.
- Reflection used where a source generator or typed API exists.
- `var` used where the type isn't obvious from the right-hand
  side.
- Missing `sealed` on classes that aren't intended for inheritance
  (perf + clarity).

### Async patterns
- `.Result` / `.Wait()` / `.GetAwaiter().GetResult()` in
  production code paths (deadlock risk in ASP.NET Core).
- `async void` outside event handlers.
- Missing `ConfigureAwait(false)` in library code (if the project
  documents this).
- `Task.Run` wrapping CPU work in handlers (use only for
  genuinely CPU-bound work, not to "fix" sync code).
- Forgotten `await` (returning `Task` without awaiting where the
  result is needed).

### DI / lifetimes
- Captive dependencies: Singleton holding Scoped or Transient.
- Service locator pattern (resolving from `IServiceProvider` in
  business code instead of constructor injection).
- Static state where DI would be cleaner.

### EF Core / data
- N+1 queries: loops issuing per-item queries; missing
  `.Include()` / `.ThenInclude()`.
- `.ToList()` materialised too early, forcing client-side
  filtering.
- Missing `AsNoTracking()` on read-only queries.
- Raw SQL via `FromSqlRaw` with string interpolation (SQL
  injection); use `FromSqlInterpolated` or parameters.
- Migrations executed against prod with `MigrateAsync` at app
  startup without a deployment-gate.

### Routing / API design
- Routes inconsistent with the project's URL convention.
- Missing model binding source attributes (`[FromBody]`,
  `[FromRoute]`, `[FromQuery]`) where the framework can't infer.
- Endpoints returning ORM entities directly (versus DTOs).

### Error handling
- Bare `catch` without filter or rethrow.
- `catch (Exception)` swallowing without logging.
- Custom exceptions without `[Serializable]` if the project's
  contract requires it.
- Exceptions used for control flow.

### Security (regression check only)
- Endpoints performing privileged operations without verifying
  resource ownership.
- User IDs taken from request body / query rather than
  `User.FindFirstValue(ClaimTypes.NameIdentifier)` /
  equivalent.
- Secrets in `appsettings.json` rather than user secrets / key
  vault / environment.
- SQL injection via raw query interpolation.
- Insufficient anti-forgery handling on cookie-auth endpoints.

### Logging
- `Console.WriteLine` / `Debug.WriteLine` in production paths.
- Unstructured logging: string-concatenated messages instead of
  structured templates with `{Placeholders}`.
- `logger.LogError(ex.Message)` instead of `logger.LogError(ex, "context")`
  (loses stack trace).

### Dependency hygiene
- Conflicting package versions across projects (not centralised).
- Transitive dependencies pinned at the top level "just in case."
- `PackageReference` versions floating (`*`) outside test
  projects.

---

## §4.5 — Extraction

### Class / file decomposition

- Any class file longer than ~500 lines.
- Any class with more than ~10 public members (often a god
  class).
- Any controller / handler mixing HTTP concerns with business
  logic — should delegate to a service.
- Any service mixing two unrelated domains.

### Method decomposition

- Any method longer than ~50 lines.
- Any method with more than ~5 parameters (often a missing
  request / options object).
- Any method with deeply nested conditionals (>3 levels).
- Any method mixing pure logic and I/O — split so the pure part
  is unit-testable.

### Logic extraction

- Any block of computation appearing in two or more handlers /
  services — should be a shared helper or extension method.
- Any data-shaping logic (LINQ projections building DTOs)
  repeated across endpoints — extract to a mapper.
- Any inline validation logic that could be a FluentValidator or
  data-annotations attribute.

### Promotion candidates

- Any helper class used by two or more projects in the solution
  — should move to a shared library (`Common`, `Domain`, or
  similar).
- Any constant defined in two or more files — promote to a
  shared static class.

### Demotion / scope-creep candidates

- Any shared library class that has acquired
  framework-specific imports (e.g. `Microsoft.AspNetCore.*` in a
  `Common` project) — should move to the API layer.

---

## §5 — Drift counter (.NET / C# rule set)

| Rule | Violations |
|---|---|
| `Console.Write*` / `Debug.Write*` in production paths | N |
| `.Result` / `.Wait()` / `.GetAwaiter().GetResult()` | N |
| `async void` outside event handlers | N |
| `!` null-forgiving operator usages | N |
| `dynamic` usages | N |
| Bare `catch` clauses | N |
| `catch (Exception)` without rethrow / structured handling | N |
| `var` where type isn't obvious | N |
| TODO / HACK / FIXME comments | N |
| Files > 500 lines | N |
| Methods > 50 lines | N |
| Methods with > 5 parameters | N |

Adapt the rows to match what the project actually documents.
