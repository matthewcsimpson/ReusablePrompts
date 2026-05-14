---
description: Audit a Swift / Xcode codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
related: [post-milestone-fix]
---

# Post-milestone audit — Swift / Xcode variant

Audit a Swift codebase built in Xcode after a milestone tag is cut.

**This prompt extends [`core/post-milestone-audit.core.prompt.md`](./core/post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window
logic, convention-source discovery, delta logic, output format,
and constraints. This file supplies the Swift / Xcode specifics
for §2 examples, §3 milestone-diff focus, §4 regression sweeps,
§4.5 extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: Swift 5.5+ (Swift Concurrency available).
- **Build system**: Xcode 14+ (`.xcodeproj` or `.xcworkspace`),
  or `Package.swift` for Swift Package Manager (SwiftPM) modules.
- **Target platforms**: iOS / macOS / watchOS / tvOS / visionOS.
  Server-side Swift (Vapor) shares the language but has different
  patterns — fall back to the generic categories where this
  variant's UI / framework checks don't apply.
- **UI framework**: SwiftUI, UIKit (iOS) / AppKit (macOS), or a
  mix.
- **Async**: Swift Concurrency (`async` / `await` / actors)
  preferred, with Combine and GCD also present in older code.
- **Dependencies**: SwiftPM (`Package.swift`), CocoaPods
  (`Podfile` / `Podfile.lock`), or Carthage (`Cartfile.resolved`).
- **Linting / formatting**: SwiftLint, SwiftFormat, or
  `swift-format`.
- **Testing**: XCTest (often `XCTestCase` subclasses), sometimes
  swift-testing for newer projects.
- **Dead-code detection**: Periphery (if configured).

If the project deviates substantially (Server-side Swift, Vapor,
Hummingbird), fall back to the generic categories where the
variant's UI-flavoured checks don't apply.

---

## §2 — Per-rule sweep (Swift / Xcode rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `Package.swift` and / or `*.xcodeproj/project.pbxproj` —
  targets, build settings, dependency graph.
- `Package.resolved` and / or `Podfile.lock` —
  dependency-version lock; verify committed.
- `.swiftlint.yml`, `.swiftformat`, `.swift-format` —
  configured style rules.
- `Info.plist` (per target) — bundle identifiers, permission
  descriptions, supported orientations / interface modes.
- `*.entitlements` — capabilities (push, app groups, sign-in
  with Apple, etc.).
- `*.xcconfig` — build settings extracted from the project file
  (preferred over storing settings in `.pbxproj`).

Common rule categories the project's docs tend to enforce —
sweep each one that's actually documented:

- **Language / spelling** — locale conventions in identifiers,
  comments, and user-facing strings (also check `Localizable.strings`).
- **Optional safety** — no force-unwrap (`!`) outside test code
  or unconditionally-true cases; no force-cast (`as!`); no
  force-try (`try!`) outside test code.
- **Concurrency** — Swift Concurrency over GCD for new code;
  `@MainActor` on UI types; `Sendable` conformance where
  declared; avoid `Task { @MainActor in ... }` boilerplate when
  the enclosing context could be annotated instead.
- **Memory** — `[weak self]` in escaping closures that outlive
  the call; `weak` delegate references for non-protocol-typed
  delegates that would otherwise retain; `unowned` only when
  the lifetime contract is explicit.
- **Type layout** — value types (`struct`, `enum`) preferred for
  model code; classes reserved for identity / shared state /
  ObjC interop / inheritance hierarchies.
- **File / type structure** — one public type per file; file
  name matches the type name; extensions in separate files
  per convention if the project documents it.
- **Naming** — Swift API design guidelines: types
  `UpperCamelCase`, properties / methods `lowerCamelCase`,
  no `_` prefix for private (private + name shadowing instead),
  no Hungarian notation.
- **UIKit / SwiftUI boundaries** — state ownership rules; which
  layer owns navigation; reactive layer (Combine / async
  sequences) chosen consistently.
- **Auto Layout / view code** — Storyboard / XIB / programmatic
  consistency per project docs; missing
  `translatesAutoresizingMaskIntoConstraints = false` on
  code-built UIKit views.
- **Privacy** — `Info.plist` permission descriptions
  (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`,
  `NSPhotoLibraryUsageDescription`, etc.) present when the
  matching API is used; required reason API declarations
  (`PrivacyInfo.xcprivacy`) if the project targets recent App
  Store policy.
- **Testing** — required colocated test targets; test
  function naming (`test<Behaviour>_<Condition>_<Expectation>`
  or similar); no XCTSkip / `XCTAssertNil`-as-stub without a
  comment.

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New types** (`struct` / `class` / `enum` / `actor` /
  `protocol`): named per Swift API guidelines? Public surface
  intentional (`public` / `internal` / `fileprivate` /
  `private` chosen deliberately)? `Sendable` conformance
  considered for concurrency-bridging types?
- **New SwiftUI views**: `@State` / `@StateObject` /
  `@ObservedObject` / `@Binding` / `@Environment` /
  `@EnvironmentObject` usage matches ownership rules? View body
  not doing heavy work each render? `accessibilityLabel` /
  `accessibilityIdentifier` set on interactive elements?
- **New UIKit view controllers**: lifecycle methods
  (`viewDidLoad`, `viewWillAppear`, etc.) implemented per
  project pattern? Memory released in `deinit` / when needed?
  Subviews using Auto Layout (no autoresizing masks)?
  Accessibility traits set?
- **New `async` / `await` code**: `@MainActor` on UI types?
  `Task` cancellation handled? No mixing GCD with structured
  concurrency unless intentional?
- **New Combine pipelines**: stored in `Set<AnyCancellable>` /
  released on deinit? No retain cycles via captured `self`?
- **New API surface** (network calls, persistence, file I/O):
  errors typed (`throws -> Result<>` / dedicated `Error` types)
  rather than swallowed?
- **New `Info.plist` keys / entitlements**: permission strings
  human-readable and explain the use; entitlements requested
  match the actual API usage.
- **New dependencies** (`Package.swift`, `Podfile`,
  `Cartfile`): justified? Pinned to the project's preferred
  level (exact, range, branch)? Lock file (`Package.resolved`,
  `Podfile.lock`, `Cartfile.resolved`) committed?
- **New TODO / FIXME / MARK: – TODO comments**: list every one
  with file and line.
- **New `print()` / `NSLog()` / `debugPrint()`** in production
  paths: list every instance — these are the Swift equivalent
  of `console.log` leaks.

---

## §4 — Full-sweep regression check

### Language quality
- Force-unwrap (`!`) outside test code or unconditional
  contexts.
- Force-cast (`as!`) where conditional cast (`as?`) with a
  proper fallback would be safe.
- Force-try (`try!`) outside test / app-fatal contexts.
- Implicitly unwrapped optionals (`String!`) declared on stored
  properties without justification.
- `@objc` on Swift-only code paths (only needed for ObjC interop
  or KVO / runtime usage).
- `NSObject` inheritance where a pure Swift type would suffice.

### Concurrency
- GCD (`DispatchQueue.main.async`) in code paths where
  `@MainActor` annotation or `await MainActor.run` would be
  idiomatic Swift Concurrency.
- `Task { ... }` discarded without storing the handle when
  cancellation matters.
- Closures captured strongly causing retain cycles
  (look for `escaping` closures that don't include
  `[weak self]`).
- `Task.detached` used where a child task would do.
- Combine subscriptions not stored in a `Set<AnyCancellable>`
  or stored but never cleaned up.

### Memory
- Strong delegate references (when not `weak`).
- Closures in long-lived contexts capturing `self` without
  `[weak self]` / `[unowned self]`.
- Retain cycles between view models / coordinators / view
  controllers.
- `unowned` captures where the contract isn't visibly safe.

### SwiftUI patterns
- `@ObservedObject` declared on a view that owns the object
  (should be `@StateObject`).
- `@State` for data that shouldn't be local (should hoist to
  parent or store in a view model).
- View body computing values that should be `@State` or
  derived properties.
- Missing `id` on `ForEach` with mutable data (causes diffing
  bugs).
- Missing `equatable()` / `EquatableView` where re-render is
  expensive.

### UIKit patterns
- View controllers > 400 lines (god view controller).
- Auto Layout constraints added without
  `translatesAutoresizingMaskIntoConstraints = false`.
- Direct frame manipulation where Auto Layout would do.
- Storyboard segues used where programmatic navigation would
  be clearer (or vice versa per project convention).
- Cell reuse identifiers not extracted to constants.

### Error handling
- Bare `try?` discarding errors silently in production paths.
- `catch { }` swallowing.
- `fatalError` / `preconditionFailure` in non-fatal contexts.
- Custom errors not adopting `LocalizedError` when surfaced to
  users.

### Privacy / security
- Permission API usage without the matching `Info.plist`
  description.
- `URLSession` calls with HTTP (not HTTPS) without an explicit
  ATS exception documented.
- Sensitive data in `UserDefaults` / unencrypted files
  (should be Keychain).
- Hardcoded API keys / tokens in source.
- WebView (`WKWebView` / `UIWebView`) loading user-controlled
  URLs without validation.

### Style / structure
- Single file > 500 lines.
- Function bodies > 50 lines.
- Type bodies (class / struct / enum) > 300 lines.
- SwiftLint violations (run `swiftlint` and treat warnings as
  findings).
- Force-unwrap rules covered above.

### Dependency hygiene
- Locked dependencies (`Package.resolved` / `Podfile.lock` /
  `Cartfile.resolved`) committed?
- Mixed dependency managers without clear domain split
  (e.g. SwiftPM for one target, CocoaPods for another with no
  documented reason).
- Frameworks bundled but not referenced.

### Xcode project hygiene
- `.pbxproj` merge conflicts in the milestone window — flag as
  high-confidence findings.
- Build settings differing across targets without reason
  (especially `SWIFT_VERSION`, deployment target, signing).
- Capabilities enabled but not used (push, background modes).
- `Info.plist` referenced from build settings vs included
  directly — consistent with project convention.

---

## §4.5 — Extraction

### Type / file decomposition

- Any view controller longer than ~400 lines.
- Any SwiftUI view file longer than ~300 lines.
- Any `struct` / `class` with > 10 stored properties (often
  a missing sub-type — a value object / coordinator / view
  model).
- Any source file mixing two unrelated types (extract one to
  its own file).
- Any view controller mixing view code, networking, and
  persistence concerns.

### Function decomposition

- Any function longer than ~50 lines.
- Any function with more than ~5 parameters (often a missing
  request / options struct).
- Any deeply nested optional chaining (>3 levels) — extract a
  guard-let block at the top.
- Any function mixing pure logic and I/O — split.

### View extraction

- Any SwiftUI view body containing nested conditional
  sub-trees that are really separate views in disguise
  (`if isEditing { ... } else { ... }` where each branch has
  non-trivial content).
- Any `var body: some View` longer than ~80 lines.
- Any `UITableViewCell` / `UICollectionViewCell` with `>= 3`
  configure-style methods (extract a view model).

### Logic extraction

- Any block of pure computation appearing in two or more views
  / controllers — extract a helper or extension.
- Any data-shaping logic (mapping model → display) repeated
  across views — extract a presenter / view-model layer.
- Any inline string formatting building user-facing copy —
  extract to `Localizable.strings`.

### Promotion candidates

- Any helper used by two or more targets (e.g. main app +
  widget extension) — promote to a shared framework / SwiftPM
  module.
- Any constant defined in two or more files — promote to a
  shared `Constants` namespace / module.
- Any model used by both UI and API layers — make sure it
  lives in a shared target.

### Demotion / scope-creep candidates

- Any shared framework type that's grown UI-specific
  properties (frames, colors) — should move back to the UI
  layer.
- Any "utility" that has accumulated business logic — move to
  the appropriate feature module.

---

## §5 — Drift counter (Swift / Xcode rule set)

| Rule | Violations |
|---|---|
| Force-unwrap `!` in production code | N |
| Force-cast `as!` | N |
| Force-try `try!` outside tests | N |
| `print()` / `NSLog()` / `debugPrint()` in production paths | N |
| Closures capturing `self` strongly (potential retain cycles) | N |
| GCD `DispatchQueue` calls where Swift Concurrency fits | N |
| `@objc` annotations on Swift-only code | N |
| TODO / FIXME comments | N |
| Files > 500 lines | N |
| Functions > 50 lines | N |
| View controllers > 400 lines | N |
| SwiftUI view bodies > 80 lines | N |
| SwiftLint warnings (if configured) | N |

Adapt the rows to match what the project actually documents.
