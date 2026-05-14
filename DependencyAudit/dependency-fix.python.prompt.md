---
description: Action findings from dependency-audit-python. Vuln fixes, bumps by risk band, removals, lockfile re-resolution. Verify build + tests per category, local commits only.
related: [dependency-audit-python]
---

# Dependency fix — Python variant

Action findings from a `dependency-audit-python` report against a
Python project (pip, uv, Poetry, or pdm).

**This prompt extends [`core/dependency-fix.core.prompt.md`](./core/dependency-fix.core.prompt.md).**
Read the core first for the workflow shape. This file supplies the
Python-specific commands, risk hints, and ecosystem gotchas.

---

## Detect package manager

- `uv.lock` → uv
- `poetry.lock` + `pyproject.toml` with `[tool.poetry]` → Poetry
- `pdm.lock` → pdm
- `requirements*.txt` (no other lockfile) → pip + pip-tools (or raw
  pip)
- `Pipfile.lock` → Pipenv (rare; treat as pip-tools-shaped)

If multiple coexist, the *committed* lockfile wins. If unclear, ask
the user — installing with the wrong manager produces broken state.

---

## §1 — Vulnerabilities

```sh
# Look up advisories with reachability hints
pip-audit --format=json
uv pip-audit            # if available; else fall back to pip-audit
poetry self add poetry-plugin-export && poetry export -f requirements.txt | pip-audit -r /dev/stdin
```

Apply targeted fix (avoid `--fix` flags that perform unsafe upgrades):

```sh
# uv
uv add '<dep>>=<fix-version>'

# Poetry
poetry add '<dep>>=<fix-version>'

# pdm
pdm add '<dep>>=<fix-version>'

# pip-tools (requirements.in)
# Edit the relevant `requirements*.in`, then re-compile:
pip-compile requirements.in
pip-compile requirements-dev.in
pip-sync requirements.txt requirements-dev.txt
```

For deeply transitive vulns where no direct dep can fix it, pin the
transitive in the constraints:

```toml
# pyproject.toml — uv / pdm / Poetry all support this idiom
[tool.uv]
override-dependencies = ["<vuln-dep>>=<fix-version>"]
```

Document the pin in the commit message.

---

## §2 — Outdated bumps

```sh
# uv
uv lock --upgrade-package <dep>
uv sync

# Poetry
poetry update <dep>

# pdm
pdm update <dep>

# pip-tools
# Edit the version range in requirements*.in, then:
pip-compile --upgrade-package <dep> requirements.in
pip-sync requirements.txt requirements-dev.txt
```

Risk-band hints:

- `risk:low` — patch bumps + minors on stdlib-adjacent libs (`pytest`,
  `mypy`, `ruff`). Pre-1.0 deps in patch range too.
- `risk:med` — arbitrary minors for direct deps.
- `risk:high` — majors. Action one at a time. For majors of
  frameworks (Django, FastAPI, SQLAlchemy, Pydantic), read the
  upgrade guide; if it requires source-code changes, stop and flag.

Pre-1.0 (`0.x.y`) projects: minor bumps are effectively major.
`pydantic` 1→2 is the canonical example — minor bump, total rewrite.

---

## §3 — Unused removals

Re-grep before removal:

```sh
# Code references
rg "(import|from) <module-name>" --type py .

# Plugin discovery (pytest plugins, Django apps, entry points)
rg "<dep>" pyproject.toml setup.py setup.cfg \
   pytest.ini conftest.py .pre-commit-config.yaml \
   .github/workflows/ Makefile tox.ini

# Console scripts (the dep may be invoked by name from CI / Makefile)
rg "(pytest|black|ruff|mypy|alembic|<dep-cli-name>)" Makefile .github/workflows/
```

The **module name** is not always the **package name** (`PyYAML`
imports as `yaml`, `pillow` as `PIL`). Use the audit's mapping or
check the dist-info.

Then uninstall:

```sh
uv remove <dep>
poetry remove <dep>
pdm remove <dep>

# pip-tools
# Remove from requirements*.in, then:
pip-compile requirements.in
pip-sync requirements.txt requirements-dev.txt
```

---

## §4 — Missing additions

Find the resolved version:

```sh
uv pip show <dep>
poetry show <dep>
pdm list <dep>
pip show <dep>
```

If transitively present, pin its caret-equivalent:

```sh
uv add '<dep>>=<version>,<<next-major>'
poetry add '<dep>^<version>'
pdm add '<dep>>=<version>,<<next-major>'

# pip-tools — add to requirements*.in with version spec
echo '<dep>>=<version>,<<next-major>' >> requirements.in
pip-compile requirements.in
pip-sync requirements.txt requirements-dev.txt
```

Decide test/dev vs production from the import location:

- `<package>/**` imports → main deps
- `tests/**` or `*_test.py` imports → dev / test deps group

---

## §5 — Lockfile drift

```sh
# uv — verify lockfile is current
uv lock --check
uv sync

# Poetry
poetry lock --no-update
poetry install

# pdm
pdm lock --check
pdm sync

# pip-tools — recompile if pyproject.toml / .in files changed
pip-compile requirements.in
pip-compile requirements-dev.in
pip-sync requirements.txt requirements-dev.txt
```

---

## §6 — Duplicates

Python's flat namespace means duplicates rarely happen the way npm
duplicates do (no nested node_modules). But duplicate version
*declarations* across `pyproject.toml`, `requirements.txt`,
`setup.py`, and `setup.cfg` are common:

```sh
# Find every place a dep is declared
rg "<dep>" pyproject.toml requirements*.txt requirements*.in \
   setup.py setup.cfg constraints*.txt
```

If multiple files declare different versions, the lockfile resolved
**one** of them — the others are stale. Remove the duplicates so the
single source of truth is the manifest the package manager actually
reads.

---

## §7 — Verification

After **each** category's action:

```sh
# Reinstall from lockfile
uv sync --frozen
poetry install --no-update
pdm sync --no-self
pip-sync requirements.txt requirements-dev.txt

# Then project checks
mypy <package>            # if configured
ruff check
pytest -q
python -m build           # if the project is a package
```

A clean install + passing checks is the gate.

---

## §8 — Constraints (Python-specific addenda)

- Do not use `pip install --upgrade` without a version specifier
  unless you mean "latest, breaking-changes-and-all". Pin to a
  specific version or range.
- Do not run `pip-audit --fix`. It bypasses the constraints file and
  upgrades aggressively.
- A `pyproject.toml` with `[tool.poetry]` and a `requirements.txt`
  side-by-side often means the project exports requirements for
  Docker. Don't edit `requirements.txt` directly — regenerate it via
  `poetry export`. Document this in the report.
- C-extension packages (`numpy`, `scipy`, `pandas`, `lxml`,
  `cryptography`, `psycopg2`) may pin to specific Python versions.
  Bumping them can change the wheel selected; verify the wheel
  exists for the project's Python version.
- For projects with extras (`pip install package[dev,test]`), the
  audit may have surfaced findings across multiple extras — apply
  fixes in the correct extras group. `uv add --group dev <dep>` and
  similar.
- Editable installs (`pip install -e .`) hide path-based
  installations from `pip list`. Don't treat an editable workspace
  package as missing.
