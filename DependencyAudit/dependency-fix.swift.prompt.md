---
description: Action findings from dependency-audit-swift. Vuln fixes, bumps by risk band, removals via SPM / CocoaPods. Verify build + tests per category, local commits only.
related: [dependency-audit-swift]
---

# Dependency fix — Swift variant

Action findings from a `dependency-audit-swift` report against a
Swift / Xcode project (Swift Package Manager and/or CocoaPods).

**This prompt extends [`core/dependency-fix.core.prompt.md`](./core/dependency-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
Swift-specific commands, risk hints, and ecosystem gotchas.

---

## Detect package manager

- `Package.swift` → Swift Package Manager (SPM).
- `Package.resolved` → SPM lockfile (committed to repo).
- `Podfile` + `Podfile.lock` → CocoaPods.
- Both → hybrid project; deps live in both manifests, fix is
  per-manager.
- `Cartfile` → Carthage (less common now; treat as CocoaPods-shaped).

Xcode-only projects without `Package.swift` use `*.xcodeproj`'s
embedded SPM references (in the `Project.xcodeproj/project.pbxproj`
file). Edits there are XML-shaped; prefer using Xcode's GUI or the
`xcodebuild -resolvePackageDependencies` command rather than hand-
editing pbxproj.

---

## §1 — Vulnerabilities

Swift / iOS doesn't have a built-in vulnerability tool comparable to
`npm audit`. The audit relies on external sources (CVE feeds,
package advisories).

Apply fix by adjusting the version range:

```sh
# SPM — edit Package.swift's dependency declaration
# From:
#   .package(url: "https://...", from: "1.2.0")
# To:
#   .package(url: "https://...", from: "1.2.3")
# Or for a specific range:
#   .package(url: "https://...", exact: "1.2.3")
# Then:
swift package update <dep>

# CocoaPods — edit Podfile
# From:
#   pod 'Alamofire', '~> 5.6'
# To:
#   pod 'Alamofire', '~> 5.6.4'
# Then:
pod update <PodName>
```

For deeply transitive vulns, SPM and CocoaPods differ:

- **SPM**: less flexible. You may need to add the transitive as a
  *direct* dependency to force the version, then ensure the
  intermediate dep resolves against it.
- **CocoaPods**: the parent's podspec dictates the transitive version
  range. Pinning the transitive in the Podfile only works if the
  range allows it.

---

## §2 — Outdated bumps

```sh
# SPM — see what's outdated
swift package update --dry-run

# Update one dep within its declared range
swift package update <dep>

# Bump beyond the range — edit Package.swift first, then update
swift package update <dep>

# Resolve to ensure Package.resolved reflects the change
swift package resolve

# CocoaPods
pod outdated
pod update <PodName>
```

Risk-band hints:

- `risk:low` — patch bumps + minors on app-framework packages (Apple
  first-party-ish, Combine, async-algorithms).
- `risk:med` — arbitrary minors for direct deps.
- `risk:high` — majors. iOS deps often have aggressive deployment-
  target requirements; a major bump may require raising the project's
  `IPHONEOS_DEPLOYMENT_TARGET`. Flag rather than auto-bump.

For Apple-ecosystem packages tied to Xcode / Swift versions
(`swift-syntax`, `swift-format`), pin to the version matching the
project's Swift toolchain — bumping past the toolchain causes
mysterious build failures.

---

## §3 — Unused removals

Re-grep before removal. Swift module imports are simple but module
names don't always match package names:

```sh
# Source imports
rg "import\s+<ModuleName>" --type swift .

# Module name is in the .target.product(name:) of Package.swift,
# not the package name itself
grep -A5 "<package-name>" Package.swift

# Resource bundles
rg "<dep>" *.xcassets *.bundle *.xcprivacy

# Build scripts referencing pod / SPM by name
rg "<dep>" Podfile *.sh .github/workflows/
```

Then remove:

```sh
# SPM — remove from Package.swift's dependencies array AND from
# any target's dependencies that listed it
# Then:
swift package resolve

# CocoaPods — remove the `pod` line from Podfile, then:
pod install
```

`pod install` updates `Podfile.lock`. SPM updates
`Package.resolved`.

---

## §4 — Missing additions

If `import X` exists but the dep isn't declared:

```sh
# Find the package URL by searching GitHub / Swift Package Index
# Then add to Package.swift:
#
# dependencies: [
#     ...,
#     .package(url: "https://github.com/owner/repo", from: "1.0.0"),
# ],
#
# And to the relevant target:
#
# targets: [
#     .target(name: "MyApp", dependencies: [
#         .product(name: "X", package: "repo"),
#     ]),
# ]

swift package resolve

# CocoaPods:
# Add `pod 'X', '~> 1.0'` to the relevant target in Podfile, then:
pod install
```

The module name (in the `import` statement) often differs from the
package name. Use the package's README to find the product name.

---

## §5 — Lockfile drift

```sh
# SPM — verify Package.resolved matches Package.swift
swift package resolve

# If Package.resolved has uncommitted changes, the manifest's ranges
# allow newer versions than were locked.

# CocoaPods
pod install                          # Re-resolves and updates Podfile.lock
pod update                           # Aggressively bumps within ranges
```

If `Package.resolved` is gitignored (sometimes done for libraries
that don't pin), there's no drift to detect — note that in the
report.

---

## §6 — Duplicates

Duplicates in Swift surface as version conflicts at resolve time:

```sh
# SPM — explicit error during resolve if two paths require
# incompatible versions
swift package resolve

# CocoaPods — explicit error during install
pod install
```

The fix is usually one of:

1. Bump a sibling that's blocking the higher version.
2. Pin the conflicted dep explicitly in the top-level Podfile / a
   direct SPM dependency.

For app + extension targets in a single Xcode project, ensure the
same versions are linked into both — version skew between app and
extension is a runtime hazard.

---

## §7 — Verification

After **each** category's action:

```sh
# Resolve / install
swift package resolve
pod install

# Build
swift build
# or for an Xcode project
xcodebuild \
  -project <Project>.xcodeproj \
  -scheme <Scheme> \
  -configuration Debug \
  -sdk iphonesimulator \
  build

# Test
swift test
xcodebuild \
  -project <Project>.xcodeproj \
  -scheme <Scheme> \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  test
```

A clean resolve + build + tests is the gate. Xcode caches aggressively
— if a bump seems to not take effect, clear `DerivedData`:

```sh
rm -rf ~/Library/Developer/Xcode/DerivedData/<ProjectName>-*
```

---

## §8 — Constraints (Swift-specific addenda)

- Do not edit `Package.resolved` directly. Always re-run
  `swift package resolve` / `swift package update`. Hand edits cause
  hash mismatches.
- Do not edit `Podfile.lock` directly. Re-run `pod install`.
- Do not regenerate the entire Podfile.lock with `pod update` (no
  arg) when actioning targeted fixes — it bumps every pod.
- For projects using XCFrameworks bundled inside SPM packages,
  bumping the SPM dep may change binary compatibility — verify on
  a clean build.
- `IPHONEOS_DEPLOYMENT_TARGET` / `MACOSX_DEPLOYMENT_TARGET` changes
  are out of scope for a dep fix. If a bump requires raising the
  target, flag.
- Swift Macros (Swift 5.9+) have their own targets in
  `Package.swift`. Bumping `swift-syntax` may require coordinated
  bumps across multiple macro packages.
- Apple's first-party packages (`swift-async-algorithms`,
  `swift-collections`, `swift-system`) are pinned to Swift
  toolchain versions; check the README before bumping.
- CocoaPods deprecation: if the project hasn't migrated to SPM,
  surface CocoaPods deprecation as an aside but don't action a
  migration — that's a project-wide decision.
