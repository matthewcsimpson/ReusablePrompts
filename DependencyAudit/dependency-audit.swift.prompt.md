---
description: Audit a Swift / Xcode project (Swift Package Manager and/or CocoaPods) for outdated versions, vulnerabilities, unused or missing declarations, and duplicates.
related: [dependency-fix-swift]
---

# Dependency audit — Swift variant

Audit a Swift / Xcode project using Swift Package Manager (SPM),
CocoaPods, or both.

**This prompt extends [`core/dependency-audit.core.prompt.md`](./core/dependency-audit.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Steps 2–6 audit categories, Step 7 report
format, and the Constraints). This file supplies the Swift-specific
commands, manifest paths, and ecosystem gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: Swift.
- **Manifest**:
  - SPM library / package: `Package.swift`.
  - SPM in Xcode project: dependencies listed in the `.xcodeproj` /
    `.xcworkspace` (no `Package.swift` at the root). The resolved
    versions live in `.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`
    or `<Project>.xcworkspace/xcshareddata/swiftpm/Package.resolved`.
  - CocoaPods: `Podfile` (+ `Podfile.lock`).
  - Carthage (legacy): `Cartfile` (+ `Cartfile.resolved`). Audit but
    flag the choice as worth migrating.
- **Lockfile**: `Package.resolved`, `Podfile.lock`, or
  `Cartfile.resolved` respectively.

Swift ecosystems often use *both* SPM and CocoaPods. Audit each
separately and merge into a single report — note in the header which
dep manager owns which packages.

The Swift ecosystem lacks a first-party vulnerability scanner. The
audit relies on the GitHub Advisory Database (queried via `gh api`
or Trivy) and manual review. State this limitation in the report
header.

---

## §1 — Inventory commands

```sh
# SPM manifest at root (library/package)
ls -1 Package.swift 2>/dev/null

# Xcode project / workspace
find . -maxdepth 3 \( -name '*.xcodeproj' -o -name '*.xcworkspace' \) \
  -not -path '*/Pods/*'

# Resolved SPM versions (Xcode-managed SPM)
find . -name 'Package.resolved' -not -path '*/Pods/*' \
  -not -path '*/build/*' -not -path '*/DerivedData/*'

# CocoaPods
ls -1 Podfile Podfile.lock 2>/dev/null

# Carthage (legacy)
ls -1 Cartfile Cartfile.resolved 2>/dev/null

# Xcode version (matters for SPM resolution behaviour)
xcodebuild -version 2>/dev/null
```

---

## §2 — Outdated

### SPM

```sh
swift package show-dependencies --format json    # SPM-managed package
```

For Xcode-managed SPM (no root `Package.swift`), the resolved
versions are in `Package.resolved`. There's no first-party "outdated"
command — diff each pin against its upstream:

```sh
# Pull pins from Package.resolved
jq '.pins[] | {package: .identity, version: .state.version, url: .location}' \
  "$(find . -name 'Package.resolved' -not -path '*/build/*' | head -n1)"
```

For each pin, check the upstream repo for the latest release tag:

```sh
gh api repos/<owner>/<repo>/releases/latest --jq '.tag_name'
```

### CocoaPods

```sh
pod outdated
```

Output groups pods by gap. CocoaPods reports `Pod` vs `latest` per
spec repo.

---

## §3 — Vulnerabilities

There is no first-party SPM auditor. Two practical paths:

```sh
# Trivy understands Package.resolved and Podfile.lock
trivy fs --scanners vuln --format json .
```

```sh
# Query GitHub Advisory DB per package (best-effort)
gh api graphql -F query='
query($pkg: String!) {
  securityVulnerabilities(first: 20, package: $pkg, ecosystem: SWIFT) {
    nodes { severity advisory { ghsaId summary } vulnerableVersionRange firstPatchedVersion { identifier } }
  }
}' -F pkg=<package>
```

For CocoaPods, the GitHub Advisory DB ecosystem is `RUBYGEMS` — but
that doesn't cover pods. CocoaPods CVE coverage is thin; rely on
Trivy and on each pod's release notes.

Capture for each finding:

- Source (Trivy, GH Advisory DB, manual).
- Severity.
- Package + current version + fix version.

State explicitly in the Summary that Swift vulnerability detection
is best-effort; some CVEs will be missed.

---

## §4 — Unused / missing

There is no `deptry` equivalent for Swift. Manual approach:

```sh
# Every imported module
grep -rhE '^\s*(import|@import)\s+\w+' --include='*.swift' . \
  | sed -E 's/(@import|import)\s+([a-zA-Z0-9_.]+).*/\2/' \
  | sort -u

# SPM declared products (Package.swift)
grep -E '\.package\(|\.product\(' Package.swift 2>/dev/null

# Podfile declared pods
grep -E "^\s*pod\s+'" Podfile 2>/dev/null | sed -E "s/.*pod\s+'([^']+)'.*/\1/"
```

Cross-reference. Watch out for:

- SPM package products vs library modules — one package can vend
  multiple library products with different names. The import name
  is what matters, not the package name in `.package(...)`.
- Pods that vend multiple subspecs — `import Firebase` could
  resolve to several pods.
- Modules used only by resource bundles or via Objective-C bridging
  headers — those don't appear as `import` statements.

---

## §5 — Lockfile drift

### SPM

```sh
swift package resolve --force-resolved-versions
git diff --exit-code Package.resolved
```

A non-empty diff means the lockfile is out of sync with the manifest
(or with the upstream's branch refs if any pin uses a branch).

### CocoaPods

```sh
pod install --deployment        # fails if Podfile.lock out of sync
```

The `--deployment` flag is the CI equivalent — it refuses to update
the lockfile and exits non-zero on drift.

---

## §6 — Duplicates / version conflicts

For SPM:

```sh
# Package.resolved shouldn't have duplicates (SPM forces one resolution),
# but two packages depending on incompatible version ranges of the same
# transitive will surface as a resolution failure during `swift package resolve`.
# Capture and report any resolution warnings.
swift package resolve 2>&1 | grep -iE 'warning|conflict|incompatible'
```

For CocoaPods:

```sh
pod install 2>&1 | grep -iE 'conflict|warning|incompatible'
```

Common cross-tool conflict: the same library installed via SPM in
Xcode AND via CocoaPods. Surface this — it's a real footgun, and
both will compile but link in unpredictable ways.

---

## §7 — Swift-specific report rows

Add to the audit header:

- Dep managers in use: `SPM | CocoaPods | Carthage | combinations`
- Xcode version: from `xcodebuild -version`.
- Swift version: from `swift --version` if available.
- iOS / macOS deployment target: pull from project settings if
  reachable (`grep IPHONEOS_DEPLOYMENT_TARGET *.xcodeproj/project.pbxproj`).

Vulnerability detection coverage caveat: state explicitly in the
Summary that Swift / iOS vulnerability scanning is best-effort —
unlike npm / NuGet / PyPI, there's no first-party advisory feed.

Recommendations should specify the dep manager:

- "Update `Alamofire` SPM pin from `5.8.0` to `5.9.1` (edit
  `Package.resolved` via Xcode → Package Dependencies → Update)."
- "Update `Firebase/Auth` pod from `10.20` to `10.27` in `Podfile`,
  run `pod install`."

---

## Constraints (Swift-specific addenda)

- Don't flag pods consumed only via Objective-C bridging headers as
  unused — they won't appear as `import` statements in Swift
  sources.
- Carthage projects should be flagged as worth migrating to SPM (or
  at least mention it once in the Summary), but the audit should
  still cover them.
- The Xcode-managed SPM workflow stores resolved versions inside the
  `.xcworkspace`; never recommend deleting `Package.resolved` "to
  re-resolve" — that bypasses the lockfile and creates the drift
  this audit is meant to catch.
- A finding of "iOS / macOS deployment target far below current"
  belongs in the audit even though it isn't strictly a dep — it
  shapes which dep versions are even usable.
- Swift's vulnerability picture is thinner than other ecosystems.
  Don't claim "no vulnerabilities" when the truth is "no
  vulnerabilities detected by the tools that exist." Phrase it
  carefully.
