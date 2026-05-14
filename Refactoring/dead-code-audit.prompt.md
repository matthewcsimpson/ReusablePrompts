---
description: Find code that isn't used — exports never imported, components never rendered, branches never reached, env vars never read, permanently-on/off flags. Read-only.
related: [dead-code-fix, duplicate-logic]
---

# Dead code audit

Find code that isn't used: exports never imported, components never
rendered, branches never reached, env vars never read, features
hidden behind permanently-on / off flags. Read-only audit — does
not delete anything; surfaces findings so the user can act.

The LLM adds semantic dead-code detection that static tools miss:

- Branches that can't be reached given the type / range of inputs.
- Deprecated paths kept "just in case" but unused for many
  releases.
- Permanently-on or permanently-off feature flags hiding alive- or
  dead-by-default code.
- Functions kept for an envisioned use that never arrived.

## Inputs

Optional:
- A specific directory or package to scope to.
- Whether to include or exclude test files (default: exclude —
  test-only code is rarely dead).

## Step 1 — Run the static dead-code tool, if one is configured

Infer from the project manifest:

- **TypeScript / JavaScript**: `knip`, `ts-prune`, `unimport`,
  `depcheck`.
- **Python**: `vulture`.
- **Rust**: `cargo +nightly udeps`, `unused` from clippy.
- **Go**: `unused` from `golangci-lint`, `deadcode`.

If a tool is configured (referenced in `package.json` scripts,
`pyproject.toml`, `Cargo.toml`, a `Makefile`, or a CI workflow),
run it and collect its output. If not, note that and proceed —
the LLM pass still finds value even without the static baseline.

## Step 2 — Augment with semantic checks

For each static candidate, and for files the tool didn't cover
(config files, scripts, re-export barrels, generated code that
slipped into the source tree), verify:

- **Truly unused** — grep the symbol name across the whole repo,
  not just source. Confirm no callers anywhere.
- **Used only by tests** — flag separately. Production-only test
  fixtures aren't strictly dead but bloat the codebase.
- **Used only behind a flag** — read flag defaults and any
  override paths. A feature flag permanently `false` masks dead
  code; a flag permanently `true` means the "off" branch is dead.

Then look for classes of dead code the static tool can't catch:

- **Dead branches** — conditions that can't be true given the
  type / range of inputs (e.g. `if (typeof x === 'undefined')` on
  a parameter typed as `string`; `if not items:` on a parameter
  typed `list[Item]` always provided).
- **Deprecated paths** — code reachable only through APIs marked
  `@deprecated` that already have replacements callers have
  migrated to.
- **Env vars never read** — grep `.env*` files and config schemas
  for variables not referenced anywhere in code.
- **Components never rendered** — components (or equivalents in
  the project's framework) that no other file imports as a JSX /
  template element.

## Step 3 — Classify findings

For each finding:

- **Hard dead** — confidently unused; safe to remove without
  reading more context.
- **Likely dead** — appears unused but the LLM isn't 100%. Reasons
  for uncertainty: dynamic imports, re-export aliasing, usage
  from a sibling repository, runtime registration patterns
  (decorators, route plugins).
- **Conditionally dead** — only used by deprecated / disabled
  code paths. Remove together if the deprecated path is also
  being removed.

## Step 4 — Report

Output to `docs/audits/dead-code.md` (or inline if `docs/` isn't
configured). Structure:

```
# Dead code audit

Date: <today>
Scope: <whole repo | directory>
Static tool: <name | "none"> — <n> candidates flagged
LLM-only candidates: <n>

## Hard dead (safe to remove)

- `path/to/file.ts:foo` — exported function, zero callers across
  the repo.
- `path/to/Component.tsx` — never imported.
- `BAR_ENV` in `.env.example` — not read anywhere in code.

## Likely dead (verify before removing)

- `path/to/api-client.ts:legacyMethod` — only called by
  `path/to/old-route.ts`, which is flagged `@deprecated` and has
  a documented replacement at `path/to/new-route.ts`.

## Conditionally dead

- ...

## Test-only production code

- `path/to/factories.ts:makeUserFixture` — only referenced from
  `__tests__/`. Either move to a test utility folder or accept as
  a deliberate fixture.

## Pattern observations

If a single category produced many findings, list count + top 3.
```

End with the approximate LOC that would be removed if all "Hard
dead" items were deleted.

## Constraints

- Do not delete any code. Surface findings; let the user pick
  which to remove and run a focused removal pass.
- Don't flag re-export barrels as dead — they exist to define a
  public API surface even when no internal caller imports them
  directly.
- Don't flag stub functions that throw `NotImplemented` /
  `unimplemented!` / `todo!` — they're intentional placeholders.
- Be honest about uncertainty. "Probably dead but I can't see
  every caller" belongs in **Likely dead**, not **Hard dead**.
