---
description: Audit a NestJS (TypeScript) codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
related: [post-milestone-fix]
---

# Post-milestone audit — NestJS variant

Audit a NestJS (TypeScript) codebase after a milestone tag is cut.

**This prompt extends [`core/post-milestone-audit.core.prompt.md`](./core/post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window
logic, convention-source discovery, delta logic, output format,
and constraints. This file supplies the NestJS specifics for §2
examples, §3 milestone-diff focus, §4 regression sweeps, §4.5
extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Framework**: NestJS (the framework's modules / controllers /
  providers / DI conventions). Often paired with `@nestjs/swagger`,
  `@nestjs/typeorm` or `@nestjs/prisma`, `@nestjs/jwt`, etc.
- **Language**: TypeScript with `strict` mode expected.
- **Validation**: `class-validator` + `class-transformer` on DTOs;
  global or controller-level `ValidationPipe`.
- **Data**: TypeORM, Prisma, or Mongoose.
- **Tests**: Jest with `@nestjs/testing`.
- **Build / package**: pnpm / npm / yarn (commands inferred from
  `package.json`).

This variant is for **backend NestJS services**. For Next.js
front-end work see the `.nextjs` variant; for a NestJS app that
also serves SSR via Universal, follow this variant and use the
`.nextjs` Routing / styling sections for the rendering layer.

---

## §2 — Per-rule sweep (NestJS rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `nest-cli.json` — generators / build config.
- `tsconfig.json` — `strict`, `experimentalDecorators`,
  `emitDecoratorMetadata`, path aliases.
- `package.json` scripts — `start:dev`, `build`, `test`, `lint`
  commands.
- `eslint.config.*` / `.eslintrc.*` — active rule plugins,
  especially around `@typescript-eslint`.

Common rule categories the project's docs tend to enforce:

- **Module structure** — one module per feature; modules
  `exports` only what other modules consume; `imports` curated
  rather than wildcard.
- **Controller / Service / Repository layering** — controllers
  delegate to services; services don't touch HTTP types;
  repositories own ORM concerns. Controllers are thin.
- **Decorator order** — `@Controller`, `@UseGuards`,
  `@UseInterceptors`, `@UsePipes`, `@UseFilters` order consistent
  across handlers.
- **DTO discipline** — request bodies typed as DTO classes with
  `class-validator` decorators; response shapes typed (or
  documented via `@ApiResponse` if Swagger is in use).
- **DI scope** — providers without an explicit `@Injectable({
  scope })` are Singleton; request-scoped providers used only
  when the dependency on `REQUEST` is real.
- **Configuration** — `ConfigService` / `@nestjs/config` rather
  than direct `process.env`; schema validation on startup
  (`validationSchema` option).
- **Migrations** — TypeORM `migration:generate` /
  `migration:create` output; immutable after applied. Use
  `git log --follow` on each `Migrations/*.ts` to detect edits.
- **Logging** — Nest's `Logger` (constructor-injected or
  `new Logger(ContextName)`) over `console`.
- **Testing** — controllers tested with `@nestjs/testing`'s
  `Test.createTestingModule`; mocked providers via
  `.overrideProvider(...).useValue(...)`.

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New controllers**: `@UseGuards()` applied with the right
  auth guard? DTOs typed with `class-validator`? OpenAPI
  decorators (`@ApiTags`, `@ApiOperation`, `@ApiResponse`)
  present if the project uses Swagger? Resource ownership
  verified before privileged operations?
- **New services / providers**: `@Injectable()` decorator
  present? Scope set appropriately (default Singleton,
  request-scope only when needed)? Constructor-injected
  dependencies typed as interfaces / abstract classes where the
  project uses contract-first patterns?
- **New modules**: `imports`, `providers`, `controllers`,
  `exports` balanced? No circular module dependencies?
- **New DTOs**: every property has a `class-validator` decorator
  (`@IsString()`, `@IsNumber()`, `@IsOptional()`, etc.)? Nested
  DTOs use `@ValidateNested()` + `@Type(() => SubDto)`?
- **New guards / interceptors / pipes / filters**: registered
  via `@UseGuards` / `@UseInterceptors` / `@UsePipes` /
  `@UseFilters` at the right scope (controller vs handler vs
  global)?
- **New server actions / event handlers** (`@EventPattern`,
  `@MessagePattern`, `@OnEvent`): same input-validation /
  error-handling discipline as HTTP endpoints?
- **New env reads**: routed through `ConfigService` with
  validation? Server-only variables not leaked to client-bundled
  code (if applicable)?
- **New ORM migrations**: `up()` and `down()` both implemented?
  Idempotent? Indexes added where new query patterns demand?
- **New dependencies in `package.json`**: justified by the diff?
  `@nestjs/*` packages pinned to the same major version?
- **New TODO / FIXME comments**: list every one.
- **New `console.log` / `console.warn` / `console.error`** in
  production paths: list every instance — should use Nest's
  `Logger`.

---

## §4 — Full-sweep regression check

### TypeScript quality
- Non-null assertions (`!`).
- Type assertions (`as SomeType`) suppressing legitimate errors.
- Implicit `any` that should be tightened.
- `@ts-ignore` / `@ts-expect-error` without an explanatory
  comment.
- Missing return types on exported functions / controller
  handlers.

### NestJS patterns
- Controllers with business logic that should live in services
  (anything beyond extracting the request, calling a service,
  formatting the response).
- Services depending on `REQUEST` directly without
  request-scoped registration.
- Bare `throw new Error(...)` instead of `throw new HttpException(...)`
  / specific `BadRequestException` / `NotFoundException` / etc.
- DTOs without `class-validator` decorators that rely on
  TypeScript types alone (TypeScript types vanish at runtime).
- `ValidationPipe` not registered globally (or per-controller
  inconsistently).
- Cross-cutting concerns implemented in service methods that
  should be guards / interceptors (auth, caching, logging,
  transformation).
- Missing Swagger decorators on public endpoints (if the
  project surfaces OpenAPI).

### Data and ORM
- N+1 queries (relations loaded in loops instead of with
  `relations: [...]` / `selectInLoader` / Prisma `include`).
- Over-fetching: not using `select` to narrow columns.
- Raw SQL with f-string / template-literal interpolation of
  user input.
- Repositories returning ORM entities all the way to the
  controller (instead of mapping to DTOs at the service
  boundary).

### Async / error handling
- Unhandled promise rejections (calls without `await` in async
  contexts).
- Bare `try { } catch (e) { console.log(e); }` swallowing.
- Exceptions caught at the wrong layer (service logs and
  rethrows generic, controller catches without context).
- Missing `try` / `catch` on async event / message handlers
  where the framework won't crash the worker.

### Security (regression check only)
- Endpoints performing privileged operations without verifying
  ownership of the resource (current user can access the
  requested ID).
- User IDs taken from request body / query rather than the auth
  guard's resolved user.
- Secrets in `.env.example` (real values) or committed config
  files.
- Missing CSRF / rate-limiting on auth-sensitive endpoints.
- User-generated content reflected without sanitisation /
  escaping in any rendered output.

### Logging
- `console.log` / `console.warn` / `console.error` in
  production paths.
- Unstructured log messages: concatenated strings instead of
  structured context (`logger.log('User signed in', { userId })`
  or the project's chosen shape).

### Dependency hygiene
- Circular imports between modules.
- `devDependencies` imported in production paths.
- Conflicting versions of `@nestjs/*` packages.

---

## §4.5 — Extraction

### Controller / service decomposition

- Any controller file longer than ~250 lines, or any individual
  handler longer than ~30 lines (controllers should be thin).
- Any service file longer than ~400 lines.
- Any service mixing two unrelated domains (e.g. user CRUD +
  notification dispatch).
- Any controller with three or more handlers that share the same
  validation / loading boilerplate — extract a custom decorator
  or interceptor.

### Logic extraction

- Any function defined inside a service method that is pure (no
  closure over `this`) and longer than a few lines — hoist to a
  module-level helper or a dedicated `*.helpers.ts`.
- Any data-shaping logic (mapping entities to DTOs) duplicated
  across services — extract to a shared mapper.
- Any inline validation logic that could be a `class-validator`
  custom decorator.

### Promotion candidates

- Any helper used by two or more feature modules — promote to a
  shared `common/` module.
- Any constant defined in multiple modules — promote to
  `common/constants.ts`.
- Any DTO used by both an HTTP and a message-pattern handler —
  promote out of the feature folder to `common/dto/`.

### Demotion / scope-creep candidates

- Any `common/` helper that has acquired imports from a specific
  feature module — should move back into that feature.

---

## §5 — Drift counter (NestJS rule set)

| Rule | Violations |
|---|---|
| `console.log/warn/error` in production paths | N |
| Bare `throw new Error(...)` (instead of HttpException) | N |
| DTOs without `class-validator` decorators | N |
| Controllers with business logic | N |
| Non-null assertions (`!`) | N |
| `as`-cast type assertions | N |
| `@ts-ignore` / `@ts-expect-error` without comment | N |
| TODO / FIXME comments | N |
| Controllers > 250 lines | N |
| Services > 400 lines | N |
| Handlers > 30 lines | N |

Adapt the rows to match what the project actually documents.
