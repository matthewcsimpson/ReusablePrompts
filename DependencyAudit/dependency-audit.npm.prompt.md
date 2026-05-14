---
description: Audit a JavaScript / TypeScript project (npm, pnpm, or yarn) for outdated versions, vulnerabilities, unused or missing declarations, lockfile drift, and duplicates.
related: [dependency-fix-npm]
---

# Dependency audit — npm variant

Audit a JavaScript / TypeScript project using npm, pnpm, or yarn.

**This prompt extends [`core/dependency-audit.core.prompt.md`](./core/dependency-audit.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Steps 2–6 audit categories, Step 7 report
format, and the Constraints). This file supplies the npm-specific
commands, manifest paths, and ecosystem gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: JavaScript or TypeScript.
- **Package manager**: detect from lockfile —
  - `package-lock.json` → npm.
  - `pnpm-lock.yaml` → pnpm.
  - `yarn.lock` → yarn (classic if no `.yarnrc.yml` with `nodeLinker`;
    berry otherwise).
- **Manifest**: `package.json` (one per workspace if a monorepo).
- **Workspaces**: npm / pnpm / yarn workspaces; check
  `package.json#workspaces` or `pnpm-workspace.yaml`.

If multiple lockfiles for the same ecosystem are present, that is a
finding in its own right — report it and stop until the user picks
the canonical one.

---

## §1 — Inventory commands

```sh
# Manifest discovery (excluding installed packages and build output)
find . -name 'package.json' \
  -not -path '*/node_modules/*' \
  -not -path '*/.next/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*'

# Lockfile presence
ls -1 package-lock.json pnpm-lock.yaml yarn.lock 2>/dev/null

# Engines and packageManager pinning (worth reporting in inventory)
jq '.engines, .packageManager' package.json
```

---

## §2 — Outdated

```sh
npm outdated --json --long              # npm
pnpm outdated --format=json --recursive # pnpm (monorepo-aware)
yarn outdated --json                    # yarn classic
yarn upgrade-interactive --dry          # yarn berry (no clean JSON; parse output)
```

Each row has `current`, `wanted`, `latest`. The audit reports the gap
from `current` → `latest`; `wanted` is informational (it's what the
range allows, not the upstream truth).

Major-behind is calculated from semver majors; for `0.x.y` versions,
treat a minor bump as effectively-major (semver allows breaking
changes pre-1.0).

---

## §3 — Vulnerabilities

```sh
npm audit --json --omit=dev             # production-only first pass
npm audit --json                        # all-scopes second pass

pnpm audit --json --prod
pnpm audit --json

yarn npm audit --recursive --severity moderate    # yarn berry
yarn audit --json                                  # yarn classic
```

The JSON includes a `findings` array with the dep chain. Record the
**top-level dep that pulls in the vulnerable transitive** — that's
what the user has to upgrade, not the leaf.

For pinned overrides / resolutions:

```sh
jq '.overrides, .resolutions, .pnpm.overrides' package.json
```

List any active overrides in the report. They are often the
documented remediation for a CVE the registry hasn't released a fix
for yet — calling them out preserves that context.

---

## §4 — Unused / missing

Prefer `knip` if the project configures it; otherwise fall back to
`depcheck`:

```sh
npx knip --reporter json        # if knip is in devDependencies
npx depcheck --json             # fallback
```

Both miss usages behind:

- Dynamic imports (`import('foo')` with a non-literal arg).
- Plugin discovery (Next.js plugins, webpack loaders, ESLint /
  Prettier / Stylelint shareable configs, Husky / lint-staged
  scripts).
- Runtime registration (decorators, NestJS modules referenced by
  string).
- Codegen / build tooling referenced only from npm scripts.

For each candidate the tool flags, confirm by grep across the whole
repo (`**/*.{ts,tsx,js,jsx,mjs,cjs,json,yaml,yml}` plus config files
like `next.config.*`, `vite.config.*`, `tsup.config.*`). False
positives here are common.

---

## §5 — Lockfile drift

```sh
npm ci --dry-run                        # npm — fails if lockfile out of sync
pnpm install --frozen-lockfile          # pnpm
yarn install --frozen-lockfile          # yarn classic
yarn install --immutable                # yarn berry
```

A non-zero exit is ⚠️ ISSUE — the manifest was edited but the
lockfile wasn't updated. Common after manual merge-conflict
resolution or after a `package.json` edit that wasn't followed by an
install.

---

## §6 — Duplicates

```sh
npm dedupe --dry-run
pnpm dedupe --check
yarn dedupe --check                     # berry only; classic has no equivalent
```

Then specifically check the high-impact packages:

```sh
npm ls react react-dom 2>/dev/null      # adapt to the project's stateful libs
npm ls @apollo/client urql react-query @tanstack/react-query 2>/dev/null
```

Multiple versions of React (or any state-holding lib) cause runtime
bugs that *look* like application bugs — duplicate hooks, broken
context, mysterious "invalid hook call" errors. Treat as ⚠️ HIGH
even if no other lint flags it.

---

## §7 — npm-specific report rows

Add to the audit header:

- Package manager detected: `npm | pnpm | yarn (classic | berry)`
- Workspaces: yes / no, count
- `engines.node`: <value or "unset">
- `packageManager`: <value or "unset"> — Corepack pin

In Recommendations, prefer workspace-qualified instructions:

- "Bump `react` from `18.2.0` to `18.3.1` in
  `apps/web/package.json`."

over:

- "Upgrade React." — ambiguous in a monorepo.

---

## Constraints (npm-specific addenda)

- `npm audit` overreports — many advisories are dev-only or
  unreachable. Report tool severity and your reachability assessment
  separately; do not downgrade severity unilaterally.
- Do not recommend `npm audit fix --force`. It performs unsafe major
  bumps. The user runs the upgrade deliberately.
- A `peerDependencies` mismatch surfaced by `npm ls` is a finding,
  not noise — flag it under Duplicates / version conflicts.
- If the project uses Corepack (`packageManager` field set), all
  commands above must respect that pin. Don't invoke the wrong
  package manager just because its binary happens to be on PATH.
