# Post-milestone audit — Next.js / TypeScript variant

Audit a Next.js (App Router) + TypeScript codebase after a milestone
tag is cut.

**This prompt extends [`post-milestone-audit.core.prompt.md`](./post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window logic,
convention-source discovery, delta logic, output format, and
constraints. This file supplies the Next.js / TypeScript specifics
for §2 examples, §3 milestone-diff focus, §4 regression sweeps, §4.5
extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: TypeScript (`.ts` / `.tsx`).
- **Framework**: Next.js, App Router (`app/` directory).
- **Server boundary**: React Server Components by default; `'use client'`
  and `"use server"` directives mark explicit boundaries.
- **Styling**: assumes either CSS Modules (`*.module.scss` /
  `*.module.css`), Tailwind, or a CSS-in-JS solution — the
  variant's styling checks adapt to whichever the project uses.
- **Data**: typically Prisma, Drizzle, or a similar ORM. Direct SQL
  is rare.
- **Package manager**: pnpm / npm / yarn (whichever the project
  uses; commands inferred from `package.json`).

If the project deviates from these assumptions, fall back to the
generic categories where the variant's checks don't apply.

---

## §2 — Per-rule sweep (Next.js / TS rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `tsconfig.json` — `strict` settings, path aliases.
- `next.config.js` / `next.config.ts` — image domains, redirects,
  experimental flags.
- `eslint.config.*` / `.eslintrc.*` — active rule plugins (especially
  `eslint-plugin-react`, `eslint-plugin-react-hooks`,
  `@next/eslint-plugin-next`).
- `package.json` `scripts` — to identify the check / lint / test /
  build commands.

Common rule categories the project's docs tend to enforce — sweep
each one that the project actually documents:

- **Language / spelling** — locale conventions in code, comments,
  strings, identifiers, DB column names.
- **File extensions** — TypeScript only (no `.js` / `.jsx` outside
  tooling config exceptions like `eslint.config.js`).
- **Code placement (monorepo)** — which packages own which kinds of
  code; which folders are off-limits for which imports
  (`apps/*/utils` for platform-bound helpers, shared packages for
  pure helpers).
- **Imports** — alias preferences (`@/...` over `../../...`); banned
  deep-internal imports from workspace packages
  (`@org/utils/src/foo/foo` rather than `@org/utils`).
- **Routing** — which file owns request handling: `proxy.ts` vs
  `middleware.ts`; route handler exports (`GET`, `POST`, etc.) vs
  legacy pages-router patterns.
- **Database migrations** — immutability of applied migrations. Use
  `git log --follow` on each migration file to detect edits after
  the initial commit.
- **Naming** — variable / function / file / component conventions,
  single-letter variables, section-prefix codes on components.
- **Functions** — arrow vs `function` declaration; helper
  search-before-write; prop drilling thresholds.
- **Components** — required file trio (`.tsx` +
  `.module.{scss,css}` + optional types/helpers), folder structure,
  prefix conventions, colocation rules, skeleton sibling.
- **Testing** — required colocated tests, Playwright vs unit-test
  placement, banned test-runner flags (`passWithNoTests`).

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New components**: follow the project's structural rules (prefix,
  file trio, colocation, skeleton sibling)? Server vs client boundary
  chosen deliberately (`'use client'` only where necessary)?
- **New utilities**: placed correctly per the project's monorepo /
  layering rules (pure → shared package, platform-bound →
  app-specific)? Tested?
- **New route handlers** (`app/**/route.ts`): input validated (Zod /
  Valibot / similar)? Auth checked via the project's session helper?
  Error shape consistent with the project's error helper? Ownership
  of resources verified before privileged operations?
- **New server actions** (`"use server"`): same checks as route
  handlers — validation, auth, ownership.
- **New `'use client'` / `"use server"` directives**: genuinely
  needed, or accidental? A `'use client'` at the top of a leaf
  component when the parent is already client is redundant.
- **New env var reads**: client-side reads use `NEXT_PUBLIC_*` and
  are accessed only in client components? Server-only env vars never
  imported into client code?
- **New `generateMetadata` / `generateStaticParams`**: present where
  required for SEO / static generation?
- **New `next/image` usage**: `width` / `height` (or `fill` with
  sized parent), `alt` set, `priority` only on above-the-fold?
- **New `next/link` usage**: used instead of bare `<a>` for internal
  navigation?
- **New dependencies in `package.json` files**: justified, pinned
  appropriately, placed in `dependencies` vs `devDependencies`
  correctly?
- **New TODO / FIXME comments**: list every one with file and line.
- **New `console.log` / `console.warn` / `console.error` calls**:
  list every instance.

---

## §4 — Full-sweep regression check

### TypeScript quality
- Non-null assertions (`!`).
- Type assertions (`as SomeType`) suppressing legitimate errors.
- Implicit `any` that should be tightened.
- `@ts-ignore` / `@ts-expect-error` without an explanatory comment.
- Missing return types on exported functions.

### React patterns
- Client components that could be server components (no state, no
  effects, no event handlers, no browser APIs).
- `useEffect` hooks that could be derived state or event handlers.
- `useState` chains describing one coherent piece of state (usually
  a `useReducer` or custom hook in disguise).
- Prop drilling deeper than 2 levels (consider context or
  composition).
- Missing `key` props on lists.

### Next.js patterns
- Pages missing `generateMetadata` or static metadata.
- Hardcoded URLs that should be env-derived.
- `next/image` missing dimensions or with `unoptimized` where it
  shouldn't be.
- Misuse of caching directives (`cache: 'no-store'` everywhere,
  `revalidate` not set on routes that would benefit).
- Use of `middleware.ts` for logic that belongs in route handlers or
  a dedicated proxy.

### Data and API
- ORM queries over-fetching fields (`select`/`include` not used
  where it should be).
- N+1 query patterns (loops issuing queries).
- API routes leaking ORM error shapes to the client.
- Missing pagination on list endpoints.

### SCSS / styling
- Hardcoded colour values that should be CSS custom properties or
  theme tokens.
- Magic spacing / sizing numbers that should be SCSS variables /
  Tailwind tokens.
- `!important` declarations.
- Inline `style` props (other than dynamically setting CSS custom
  properties).

### Error handling
- Empty catch blocks or catch-and-log-only.
- Missing try/catch on async route handlers.
- Inconsistent API error response shapes.

### Security (regression check only)
- Route handlers performing privileged operations without verifying
  resource ownership.
- `userId` taken from request body or query params rather than the
  auth session.
- Server-only env vars accessed in client components.
- User-generated content rendered without sanitisation.

### Dependency hygiene
- Circular imports.
- `devDependencies` used in production code paths.
- Duplicate logic between packages suggesting a missing shared
  utility.

---

## §4.5 — Extraction

### Component decomposition

- Any component file longer than ~250 lines, or with a render
  function longer than ~80 lines. Length isn't automatically wrong,
  but it's a signal worth surfacing.
- Any render function containing nested conditional sub-trees that
  are really separate components in disguise.
- Any component containing JSX structurally identical to JSX in
  another component, where a shared primitive would absorb both.
- Any component with three or more `useState` calls that together
  describe a single coherent piece of state.
- Any component with a `useEffect` body longer than ~20 lines, or
  three or more `useEffect`s — typically a custom hook is hiding
  inside.

### Logic extraction

- Any function defined inside a component body that is pure (no
  closure over component state) and longer than a few lines —
  should be hoisted to module scope or moved to a `.helpers.ts` /
  `.utils.ts`.
- Any data-shaping logic (mapping, filtering, grouping, sorting,
  deriving display values) appearing at the top of two or more
  components — should be a shared helper.
- Any inline JSX expressions performing non-trivial computation —
  should be a `useMemo` or extracted helper.
- Any block of imperative logic inside a `useEffect` that has no
  dependency on React lifecycle — usually a plain async function
  called from the effect.

### Promotion candidates

- Any component used by two or more sections that could move to a
  shared UI package.
- Any helper that is pure and could move to a shared utility
  package.
- Any constant defined in two or more files — should move to a
  shared types or constants module.

### Demotion / scope-creep candidates

- Any shared UI component that has accumulated section-specific
  props — should move back to its section.
- Any shared helper that has acquired an import from `next/*` or
  browser APIs — should move to the platform-specific layer
  (`apps/web/utils` or equivalent).

---

## §5 — Drift counter (Next.js / TS rule set)

| Rule | Violations |
|---|---|
| `function` declarations (where arrow expected) | N |
| Single-letter variables | N |
| `../` imports (where alias expected) | N |
| `console.log/warn/error` in production | N |
| `!important` in styling | N |
| Non-null assertions (`!`) | N |
| `as`-cast type assertions | N |
| `@ts-ignore` / `@ts-expect-error` without comment | N |
| TODO / FIXME comments | N |
| Components missing required prefix / file trio | N |
| Misplaced utilities (platform-bound in shared package, or pure helper in app-specific) | N |

Adapt the rows to match what the project actually documents — add
rows for rules the project enforces that aren't in this default
list, and drop rows for conventions it doesn't have.
