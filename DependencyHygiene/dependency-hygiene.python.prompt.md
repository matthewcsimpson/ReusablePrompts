---
description: Audit a Python project (pip, uv, Poetry, or pdm) for outdated versions, vulnerabilities, unused or missing declarations, lockfile drift, and duplicates.
---

# Dependency hygiene — Python variant

Audit a Python project using pip, uv, Poetry, or pdm.

**This prompt extends [`core/dependency-hygiene.core.prompt.md`](./core/dependency-hygiene.core.prompt.md).**
Read the core first for the workflow shape (Step 0 convention
sourcing, Step 1 inventory, Steps 2–6 audit categories, Step 7 report
format, and the Constraints). This file supplies the Python-specific
commands, manifest paths, and ecosystem gotchas.

If pasting into a chat without filesystem access, paste the core
first, then this variant.

---

## Assumed stack

- **Language**: Python.
- **Manifest**: detect by file presence —
  - `pyproject.toml` with `[project]` table → PEP 621.
  - `pyproject.toml` with `[tool.poetry]` → Poetry.
  - `pyproject.toml` with `[tool.pdm]` → pdm.
  - `requirements.txt` (+ optional `requirements-dev.txt` /
    `constraints.txt`) → pip-tools or hand-managed.
  - `Pipfile` → pipenv (older; treat similarly to Poetry for
    purposes of this audit).
- **Lockfile**: `uv.lock`, `poetry.lock`, `pdm.lock`, `Pipfile.lock`,
  or a pinned `requirements.txt` derived from `requirements.in`.
- **Tool of choice**: prefer `uv` (faster, growing standard); fall
  back to project tool.

If multiple manifest styles coexist (e.g. `pyproject.toml` AND a
non-derived `requirements.txt`), flag it before continuing — the
sources of truth disagree.

---

## §1 — Inventory commands

```sh
# Manifest presence
ls -1 pyproject.toml setup.py setup.cfg requirements*.txt Pipfile* 2>/dev/null

# Lockfile presence
ls -1 uv.lock poetry.lock pdm.lock Pipfile.lock 2>/dev/null

# Python version pin
grep -E 'requires-python|python\s*=' pyproject.toml 2>/dev/null

# Resolved env (sanity check)
python -V
pip --version
```

If a virtual environment isn't active, the audit's `pip` commands
will reflect global packages — flag this and stop until the user
activates the project's environment (or run inside `uv run` /
`poetry run` / `pdm run`).

---

## §2 — Outdated

```sh
uv pip list --outdated --format json     # uv
pip list --outdated --format json        # pip
poetry show --outdated --no-ansi         # Poetry
pdm outdated                             # pdm
```

The output gives current vs latest. Categorise by semver, treating
PEP 440 prereleases (`rc`, `b`, `a`) as a separate axis: don't flag a
project as "behind" because the upstream has prereleases newer than
the current stable.

For top-level vs transitive, prefer the tool's own dependency tree:

```sh
uv pip tree
pipdeptree                  # if installed
poetry show --tree
```

---

## §3 — Vulnerabilities

```sh
pip-audit --format json                  # PyPA's auditor; reads installed env
pip-audit --requirement requirements.txt --format json   # against a requirements file
```

`pip-audit` reads from PyPI's advisory DB and OSV. Capture for each
advisory:

- `id` (e.g. `GHSA-xxxx-xxxx-xxxx`, `PYSEC-2024-xxx`).
- `severity` if present (often unset in the OSV feed; fall back to
  CVSS if a CVE is linked).
- Affected dep, current version, fix version.

Reachability assessment is especially nuanced in Python — many
advisories cover code paths that the project doesn't use (e.g. the
XML parsing path of a library used only for JSON). State your
assessment as a separate field.

Also check:

```sh
safety check --json                      # if `safety` is in dev deps
```

`safety` and `pip-audit` overlap but neither is a strict superset —
if both are available, run both and dedupe by `id`.

---

## §4 — Unused / missing

```sh
deptry .                                 # PEP 621 / Poetry / pdm
```

`deptry` reports:

- `DEP001` — missing (imported but not declared).
- `DEP002` — unused (declared but not imported).
- `DEP003` — transitive (imported but only declared transitively).
- `DEP004` — misplaced dev dep.

For codebases without deptry, fall back to a manual scan:

```sh
# Find every import statement in source
grep -rhE '^\s*(from|import)\s+\w+' --include='*.py' . | sed -E 's/(from|import)\s+([a-zA-Z0-9_]+).*/\2/' | sort -u
```

Cross-reference against the manifest's declared deps. Watch out for:

- Mapping discrepancies between import name and package name
  (`from PIL import Image` — package is `Pillow`; `from yaml import
  load` — package is `PyYAML`; `from sklearn import …` — package is
  `scikit-learn`).
- Pytest plugins, Alembic, gunicorn — used by config / CLI, not
  imported. Static tools flag these as unused; they're not.

---

## §5 — Lockfile drift

```sh
uv lock --check                          # uv — non-zero exit on drift
poetry lock --check                      # Poetry
pdm lock --check                         # pdm
pip-compile --dry-run requirements.in    # pip-tools — output diff = drift
```

For hand-managed `requirements.txt` (no `.in` source file), drift
detection isn't really meaningful — the file IS the spec. Note this
in the audit and skip the check.

---

## §6 — Duplicates / version conflicts

```sh
pip check                                # reports installed conflicts
uv pip check
```

Python's flat dependency resolution means duplicates are rarer than
in npm, but unsatisfiable constraints surface here. Any `pip check`
output is ⚠️ ISSUE.

Also check for the classic Python pitfall — different versions of
the same package installed across multiple environments
(system Python + venv + tooling-managed Python). If the project pins
`requires-python` strictly, mention any installed package compiled
against a different Python ABI.

---

## §7 — Python-specific report rows

Add to the audit header:

- Tool detected: `uv | pip | poetry | pdm | pipenv`
- `requires-python`: <value or "unset">
- Venv path: <path or "global env">

Recommendations should be tool-specific:

- "Bump `requests` from `2.28.0` to `2.31.0` via
  `uv add requests@^2.31`" (or `poetry add`, `pip install -U`,
  depending on tool).
- For pinned `requirements.txt` flows: "Re-pin
  `requirements.in` → `requirements.txt` with `pip-compile -U
  requests`."

---

## Constraints (Python-specific addenda)

- Don't flag scripts / CLI entry points (`gunicorn`, `alembic`,
  `pytest`, `ruff`, `mypy`) as unused — they're invoked by name from
  shell or `[project.scripts]`, not by import.
- When `requires-python` is unset, note it as a finding — it makes
  reproducible installs harder and locks the project into whatever
  Python the developer happened to have.
- A `pip install` against a Poetry / uv / pdm project (e.g. CI
  scripts that bypass the tool) is a finding worth surfacing —
  causes lockfile drift on the next tool-managed install.
- `pip-audit` against the installed env vs against a requirements
  file can yield different results (env may include packages not in
  the manifest). Run both and reconcile.
