---
description: Action findings from dependency-audit-npm. Detects npm / pnpm / yarn (classic or berry), respects Corepack, uses overrides / resolutions for transitive vulns. Local commits only.
related: [dependency-audit-npm]
---

# Dependency fix — npm variant

Action findings from a `dependency-audit-npm` report against a
JavaScript / TypeScript project (npm, pnpm, or yarn).

**This prompt extends [`core/dependency-fix.core.prompt.md`](./core/dependency-fix.core.prompt.md).**
Read the core first for the workflow shape (input scoping, per-category
verification, commit discipline, constraints). This file supplies the
npm-specific commands, risk hints, and ecosystem gotchas.

---

## Detect package manager

Use the **lockfile** to decide:

- `package-lock.json` → npm
- `pnpm-lock.yaml` → pnpm
- `yarn.lock` → yarn (classic; berry if `.yarnrc.yml` with `nodeLinker`)

If `package.json` has a `packageManager` field, prefer the pinned
manager (Corepack). The commands below are written per manager.

---

## §1 — Vulnerabilities

Look up the fix version:

```sh
npm audit --json --omit=dev | jq '.vulnerabilities'
pnpm audit --json --prod  | jq '.advisories'
yarn npm audit --recursive --severity moderate --json
yarn audit --json   # yarn classic
```

Apply the targeted fix (do **not** use `--force`):

```sh
# npm
npm install <dep>@<fix-version>

# pnpm
pnpm add <dep>@<fix-version>

# yarn classic
yarn add <dep>@<fix-version>

# yarn berry
yarn add <dep>@<fix-version>
```

For transitive vulns with no direct upgrade path, use overrides /
resolutions:

```jsonc
// package.json
{
  "overrides":    { "<vuln-dep>": "<fix-version>" },     // npm 8+, pnpm
  "resolutions":  { "<vuln-dep>": "<fix-version>" }      // yarn
}
```

Note the override in the commit message — pinning is documented in
package.json but the *reason* lives in the commit trail.

---

## §2 — Outdated bumps

```sh
# npm
npm install <dep>@<target>                 # one dep
npm update <dep>                           # within semver range
npx npm-check-updates -u --filter <dep>    # bypass range (major bumps)
npm install

# pnpm
pnpm add <dep>@<target>                    # one dep
pnpm update <dep>                          # within semver range
pnpm add <dep>@latest                      # bypass range

# yarn classic
yarn upgrade <dep>@<target>
yarn upgrade-interactive

# yarn berry
yarn up <dep>@<target>
yarn up <dep>@latest
```

Risk-band hints:

- `risk:low` (default) — patch bumps + minors on framework-internal
  packages (`@types/*`, `@babel/*`, internal monorepo packages).
- `risk:med` — arbitrary minor bumps for direct deps.
- `risk:high` — any major bump. Action **one at a time**; each gets
  its own commit. Read the package's CHANGELOG for the major being
  taken; if it lists breaking changes that touch your codebase, stop
  and flag.

For `0.x.y` deps, treat minor bumps as effectively major — pre-1.0
semver permits breaking changes.

---

## §3 — Unused removals

Re-grep before removal:

```sh
# Confirm absence across all relevant file types
rg "from ['\"]<dep>['\"]|require\\(['\"]<dep>['\"]\\)" \
   --type-add 'cfg:*.{json,yaml,yml,toml}' \
   -t js -t ts -t jsx -t tsx -t cfg \
   .

# Plugin-discovery files (don't skip these)
rg "<dep>" \
   next.config.* vite.config.* webpack.config.* \
   .eslintrc* .prettierrc* tsup.config.* \
   .husky/ .github/workflows/ \
   package.json
```

If grep is clean, uninstall:

```sh
# npm
npm uninstall <dep>

# pnpm
pnpm remove <dep>

# yarn classic
yarn remove <dep>

# yarn berry
yarn remove <dep>
```

These commands update both `package.json` and the lockfile.

---

## §4 — Missing additions

Find the version already resolved transitively:

```sh
# npm
npm ls <dep>

# pnpm
pnpm why <dep>

# yarn
yarn why <dep>          # both classic and berry
```

If a transitive resolution exists, pin to that version's caret range
(`^<version>`). Otherwise, resolve `latest` first to a concrete
version, then pin its caret range:

```sh
npm view <dep> version           # prints the latest published version
pnpm view <dep> version
yarn info <dep> version          # classic
yarn npm info <dep> --json | jq -r '.["dist-tags"].latest'    # berry
```

Use the resolved version (e.g. `^4.17.21`), not the literal string
`latest` — `latest` is a dist-tag, not a semver range, and `^latest`
is not a valid specifier.

```sh
npm install <dep>@^<version>
pnpm add <dep>@^<version>
yarn add <dep>@^<version>
yarn add <dep>@^<version>     # berry
```

Decide `dependencies` vs `devDependencies` from where the import
appears (source = `dependencies`; tests / scripts / configs =
`devDependencies`).

---

## §5 — Lockfile drift

```sh
# Re-lock without touching the manifest
npm install --package-lock-only
pnpm install --lockfile-only
yarn install --no-progress              # yarn classic
yarn install --mode=update-lockfile     # yarn berry
```

If re-lock pulls in unexpected version changes, that's the manifest
allowing them — surface it.

---

## §6 — Duplicates

```sh
npm dedupe
pnpm dedupe
yarn dedupe                  # berry only
# yarn classic has no equivalent; bump the offending sibling instead
```

Then re-check:

```sh
npm ls <dep>          # should show one version
pnpm why <dep>
yarn why <dep>
```

For state-holding libs (React, React DOM, state managers, ORM
clients), a dedupe pass is high-value — multiple versions cause
runtime bugs.

---

## §7 — Verification

After **each** category's action:

```sh
# Re-install from lockfile (cleanest check)
npm ci
pnpm install --frozen-lockfile
yarn install --frozen-lockfile      # classic
yarn install --immutable             # berry

# Then the project's checks (infer exact commands from package.json scripts)
npm run typecheck      # if present
npm run lint
npm test
npm run build          # final, after everything else
```

For a monorepo, scope to the affected workspace where feasible:

```sh
pnpm --filter <pkg> typecheck
pnpm --filter <pkg> test
```

A clean install + passing checks is the gate.

---

## §8 — Constraints (npm-specific addenda)

- Do not use `npm audit fix --force`. It performs unsafe major bumps.
- If the project uses Corepack (`packageManager` field set), invoke
  the pinned manager — do not fall back to whatever is on PATH.
- A peer-dep mismatch surfacing after a bump is a finding in its own
  right. If the mismatch is between a dep and a peer in the same
  workspace, you may be able to bump the peer. If it's an upstream
  package's peer requirement, you may need to revert.
- For monorepos with `npm`'s native workspaces, prefer
  `npm install <dep> -w <workspace>` over hand-editing
  workspace-level `package.json` files.
- `npm install` without `--save-exact` adds the dep with `^` by
  default. Match the existing manifest convention (some projects pin
  exactly).
- If the project uses Renovate / Dependabot, bumps that match what
  those bots would propose are fine; **don't** action bumps the bots
  haven't proposed without an explicit reason — the bot is the
  project's source of truth on what's safe.
