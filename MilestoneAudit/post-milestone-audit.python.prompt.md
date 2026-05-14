---
description: Audit a Python codebase after a milestone tag is cut — drift, regressions, extraction signals, and convention compliance against documented rules.
related: [post-milestone-fix]
---

# Post-milestone audit — Python variant

Audit a Python codebase after a milestone tag is cut.

**This prompt extends [`core/post-milestone-audit.core.prompt.md`](./core/post-milestone-audit.core.prompt.md).**
Read the core file first for the workflow shape, audit-window logic,
convention-source discovery, delta logic, output format, and
constraints. This file supplies the Python specifics for §2
examples, §3 milestone-diff focus, §4 regression sweeps, §4.5
extraction signals, and the §5 drift counter.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: Python 3.10+. Type hints expected on public APIs.
- **Framework**: any of FastAPI, Django, Flask, or a CLI / library /
  worker codebase. The variant's checks adapt — sweep only the
  categories that apply.
- **Dependency manager**: `pyproject.toml`-based — Poetry, uv,
  Hatch, PDM, or pip-tools. `requirements.txt`-only projects also
  work; commands inferred from whichever manifest is present.
- **Testing**: pytest.
- **Linting / formatting**: ruff is the default expectation; black
  + isort + flake8 + pylint also covered if configured.
- **Typing**: mypy or pyright.
- **Migrations**: Alembic (SQLAlchemy) or Django migrations.

If the project deviates from these assumptions, fall back to the
generic categories where the variant's checks don't apply.

---

## §2 — Per-rule sweep (Python rule categories to look for)

Beyond the convention sources listed in the core, also read:

- `pyproject.toml` — `[project]`, `[tool.ruff]`, `[tool.black]`,
  `[tool.mypy]`, `[tool.pytest.ini_options]` sections. These often
  carry inline convention rules.
- `setup.cfg` / `tox.ini` — legacy config that may still hold lint /
  type-check settings.
- `.pre-commit-config.yaml` — the set of pre-commit hooks indicates
  enforced conventions.
- `Makefile` / `justfile` / `scripts/` — to identify the check /
  lint / test / build commands.

Common rule categories the project's docs tend to enforce — sweep
each one that the project actually documents:

- **Language / spelling** — locale conventions in code, comments,
  docstrings, identifiers, DB column names.
- **Type hints** — required on public functions / methods; banned
  `Any`; required return annotations.
- **Code placement** — which package owns which kinds of code
  (e.g. `app/`, `core/`, `lib/`, `cli/`); which folders are
  off-limits for which imports.
- **Imports** — absolute vs relative imports; banned
  cross-layer imports (e.g. `cli/` importing from `web/`);
  `__all__` requirements on public modules.
- **Routing / handlers** — where request handling lives (e.g.
  FastAPI `routers/`, Django `views.py`, Flask blueprints);
  authentication / dependency-injection patterns.
- **Database migrations** — immutability of applied migrations. Use
  `git log --follow` on each migration file (Alembic
  `versions/*.py` or Django `migrations/*.py`) to detect edits
  after the initial commit.
- **Naming** — variable / function / file / class conventions;
  PEP 8 expectations; project-specific prefixes / suffixes.
- **Functions** — pure-function preference where possible; max
  argument count; helper search-before-write.
- **Classes** — single-responsibility expectations; dataclass /
  Pydantic / attrs preferences; `__init__` placement.
- **Testing** — required colocated `test_*.py`; fixture placement
  (`conftest.py` hierarchy); banned skip markers.

---

## §3 — Milestone diff focus

For files changed in this milestone, check:

- **New API endpoints** (FastAPI router, Django view, Flask blueprint
  handler): input validation via Pydantic / serializers / forms?
  Auth checked via the project's dependency / decorator? Error
  shape consistent with the project's error helper? Ownership of
  resources verified before privileged operations?
- **New models** (SQLAlchemy / Django / Pydantic): naming, type
  hints, validators, default values handled correctly (no mutable
  defaults)?
- **New CLI commands** (click / typer / argparse): help text,
  error handling, exit codes consistent with the rest of the CLI?
- **New utilities**: type-hinted? Colocated `test_*.py`?
- **New env var reads**: validated at startup (Pydantic Settings /
  dynaconf / similar) rather than scattered `os.environ.get(...)`?
- **New dependencies in `pyproject.toml`**: justified, version
  constraints sensible, placed in the right group (`dependencies`
  vs `optional-dependencies.dev` / `[tool.poetry.group.dev]` /
  equivalent)?
- **New `print()` calls in production code**: list every instance —
  these are the Python equivalent of `console.log` leaks.
- **New `breakpoint()` / `pdb.set_trace()` / `import pdb`**: list
  every instance.
- **New TODO / FIXME / XXX comments**: list every one with file and
  line.

---

## §4 — Full-sweep regression check

### Type quality
- `Any` annotations used where a specific type fits.
- `# type: ignore` / `# pyright: ignore` without an explanatory
  comment.
- Missing return type annotations on exported functions / methods.
- `cast(...)` calls suppressing legitimate errors.
- Missing parameter type hints on public APIs.

### Framework patterns

**FastAPI** (if applicable):
- Routes without `response_model` set where typing would help.
- `Depends()` used inconsistently for auth.
- Sync handlers where async would be appropriate (or vice versa).
- Missing `status_code` on routes returning non-200 success codes.

**Django** (if applicable):
- Fat views that should delegate to services / managers.
- Signals overused where explicit calls would be clearer.
- Missing `select_related` / `prefetch_related` on querysets that
  cross relationships.
- `Model.objects.all()` followed by Python-side filtering.

**Flask** (if applicable):
- Routes registered on the app directly rather than a blueprint.
- Mixed-concern blueprints (auth + business logic in one).
- Missing error handlers.

### Data and ORM
- N+1 queries (loops issuing queries; missing eager loading).
- Raw SQL with f-string interpolation (SQL injection risk).
- Missing indexes on commonly-filtered columns.
- Migrations missing a `down` / reverse implementation where the
  project's docs require it.
- Queries over-fetching columns (`.values()` / `.only()` / `select`
  not used where it should be).

### Routing / handlers
- Inconsistent URL prefix conventions.
- Handler naming that doesn't match the project's docs.
- Missing pagination on list endpoints.

### Error handling
- Bare `except:` clauses.
- `except Exception:` without re-raise or specific handling.
- Empty `except` bodies (silently swallowed errors).
- Missing logging context (`logger.exception` vs `logger.error`).
- Inconsistent API error response shapes.

### Security (regression check only)
- SQL injection risks: raw queries with f-string / `.format()`
  interpolation of untrusted input.
- Template injection: `Template(user_input)` or
  `render_template_string` with user input.
- Secrets in code or in `.env.example` (real values, not
  placeholders).
- User-identifying IDs taken from request body / query params
  rather than the authenticated session.
- Mass-assignment risks: Pydantic model accepting unexpected
  fields, Django form without explicit `fields` list.
- Missing `@login_required` / equivalent on privileged views.

### Style
- Mutable default arguments (`def foo(items=[])`).
- Long functions (>50 lines) or files (>500 lines) — soft signals.
- Missing docstrings on public modules / classes / functions where
  the project's docs require them.
- Star imports (`from x import *`).
- Unused imports (often caught by ruff but worth a count).

### Dependency hygiene
- Circular imports.
- Dev-only dependencies imported in production code paths.
- Duplicate logic between modules suggesting a missing shared
  utility.
- Unpinned dependencies where the project's docs require pinning.

---

## §4.5 — Extraction

Python equivalent of the UI-stack §4.5 — the structural unit is the
module / class / function rather than the component.

### Module decomposition

- Any module file longer than ~500 lines.
- Any module containing multiple unrelated concerns (e.g. HTTP
  handlers + ORM models + utility functions in one file).
- Any `__init__.py` that has accumulated logic beyond re-exports.

### Function decomposition

- Any function longer than ~50 lines.
- Any function with more than ~5 parameters (often a sign of a
  missing dataclass / config object).
- Any function with deeply nested conditional logic (>3 levels).
- Any function mixing pure logic and I/O — split so the pure part
  is testable in isolation.

### Class decomposition

- Any class with more than ~10 public methods (often a god class).
- Any class mixing data and behaviour for two unrelated domains.
- Any class with mutable class-level state where instance-level
  would be safer.

### Logic extraction

- Any block of computation appearing in two or more handlers /
  views — should be a shared helper.
- Any data-shaping logic (mapping, filtering, grouping) repeated
  across modules — should be a utility function.
- Any imperative validation logic that could be a Pydantic
  validator / Django form clean method.

### Promotion candidates

- Any helper module used by two or more top-level packages that
  could move to a shared `lib/` or `common/`.
- Any constant defined in two or more modules — should move to a
  shared `constants.py` or `config.py`.
- Any model / schema used by two or more domains — should move to
  a shared schemas module.

### Demotion / scope-creep candidates

- Any shared helper that has acquired a framework-specific import
  (e.g. a `lib/` module importing from `django.*` or `fastapi.*`)
  — should move to the framework-specific layer.
- Any "utility" that has grown into business logic — should move
  to the appropriate domain module.

---

## §5 — Drift counter (Python rule set)

| Rule | Violations |
|---|---|
| `print()` calls in production code | N |
| `breakpoint()` / `pdb.set_trace()` | N |
| `# type: ignore` without comment | N |
| `Any` type annotations | N |
| Missing return type on public functions | N |
| Mutable default arguments | N |
| Bare `except:` clauses | N |
| `except Exception:` without re-raise | N |
| Star imports (`from x import *`) | N |
| TODO / FIXME / XXX comments | N |
| Functions > 50 lines | N |
| Files > 500 lines | N |
| Missing docstrings on public APIs (if required by docs) | N |

Adapt the rows to match what the project actually documents — add
rows for rules the project enforces that aren't in this default
list, and drop rows for conventions it doesn't have.
