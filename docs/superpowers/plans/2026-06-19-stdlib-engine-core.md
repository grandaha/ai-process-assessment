# Stdlib-Only Engine + State Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the engine's compute path and the `state/` helpers run on **bare stdlib Python** — no `pyyaml`, `openpyxl`, or `formulas` imported on the core path — so the auditable numbers run in any code sandbox (Claude Code, Cowork, Claude.ai), while the Excel workbook still works where `openpyxl` is present.

**Architecture:** Three contained changes guided by one import-blocking guard test: (1) `state/conductor_state.py` stops importing `pyyaml` and stores `.conductor.md` frontmatter as JSON via stdlib; (2) `engine/run.py` imports the workbook lazily and degrades gracefully when `openpyxl` is absent; (3) the phantom `formulas` dependency is removed. Golden numbers stay byte-identical; the workbook is preserved where `openpyxl` exists (full removal is a later plan).

**Tech Stack:** Python 3 stdlib (`json`, `subprocess`, `importlib`), pytest.

## Global Constraints

- **Stdlib-only core:** after this plan, importing `engine.run`, `engine.compute`, `engine.model`, and all of `state/` must NOT require `yaml`, `openpyxl`, or `formulas`. The `engine.run … --no-workbook` path and every `state/*` call must run with those three modules unavailable.
- **Golden numbers unchanged:** `model/results.json` output must remain byte-identical (the existing golden suite must stay green).
- **Workbook preserved where possible:** with `openpyxl` installed, the default `engine.run <folder>/` still writes `financial-model.xlsx`. Full workbook removal is a separate (data-contract) plan — do NOT delete `engine/workbook.py` here.
- **`.conductor.md` format:** stored as `---`-fenced JSON. Engagement folders are gitignored and ephemeral; no migration of existing files is required, but `read_conductor` must degrade to `{}` on an unparseable body (legacy YAML or corruption) rather than raising.
- **Commit message trailer:** end each commit with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

---

### Task 1: Stdlib-core guard tests (RED)

One test file proves the whole refactor: it runs the core in a subprocess with `yaml`/`openpyxl`/`formulas` import-blocked.

**Files:**
- Create: `engine/tests/test_stdlib_core.py`

**Interfaces:**
- Consumes: `engine.run.main(argv: list[str]) -> int`; `state.conductor_state.write_conductor(root: Path, data: dict) -> None` / `read_conductor(root: Path) -> dict`; the golden fixture at `engine/tests/fixtures/lattice/model/*.json`.
- Produces: nothing (test-only).

- [ ] **Step 1: Write the failing tests**

Create `engine/tests/test_stdlib_core.py`:

```python
"""Proves the compute/state core runs with no third-party deps available.

Each test runs a subprocess that installs a meta_path blocker for
yaml/openpyxl/formulas, then exercises the core. This is the AC-2/AC-4 guard:
the numbers must run in any bare-Python code sandbox.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"

_BLOCKER = '''
import sys
_BLOCKED = {"yaml", "openpyxl", "formulas"}
class _Block:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in _BLOCKED:
            raise ImportError("blocked for stdlib-core test: " + name)
        return None
sys.meta_path.insert(0, _Block())
'''


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", _BLOCKER + script],
        cwd=REPO, capture_output=True, text=True,
    )


def _seed_model(tmp_path: Path) -> Path:
    model = tmp_path / "model"
    model.mkdir()
    for f in FIXTURE.glob("*.json"):
        (model / f.name).write_text(f.read_text())
    return model


def test_engine_run_core_path_needs_no_third_party_deps(tmp_path):
    model = _seed_model(tmp_path)
    script = f'''
from engine.run import main
rc = main([{str(tmp_path)!r}, "--no-workbook"])
assert rc == 0, rc
import json
r = json.load(open({str(model / "results.json")!r}))
assert r["wave1_aggregate"]["investment_point"] is not None
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout


def test_engine_run_default_path_degrades_without_openpyxl(tmp_path):
    model = _seed_model(tmp_path)
    script = f'''
from engine.run import main
rc = main([{str(tmp_path)!r}])  # no --no-workbook
assert rc == 0, rc
from pathlib import Path
assert (Path({str(model)!r}) / "results.json").exists()
assert not (Path({str(tmp_path)!r}) / "financial-model.xlsx").exists()
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout


def test_conductor_state_needs_no_yaml(tmp_path):
    script = f'''
from pathlib import Path
from state.conductor_state import write_conductor, read_conductor
root = Path({str(tmp_path)!r})
write_conductor(root, {{"register": "operator", "autonomy": {{"should_confirm": True}}}})
got = read_conductor(root)
assert got["register"] == "operator"
assert got["autonomy"]["should_confirm"] is True
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest engine/tests/test_stdlib_core.py -v`
Expected: FAIL — `test_conductor_state_needs_no_yaml` errors with "blocked … yaml" (conductor_state imports yaml at module top); both `engine_run` tests error with "blocked … openpyxl" (run.py imports `engine.workbook` → openpyxl at module top).

- [ ] **Step 3: Commit the failing tests**

```bash
git add engine/tests/test_stdlib_core.py
git commit -m "test: stdlib-core guard — core must run without yaml/openpyxl/formulas (failing)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Replace pyyaml with stdlib JSON in conductor_state.py

**Files:**
- Modify: `state/conductor_state.py`
- Test: `state/tests/test_conductor_state.py` (existing round-trip test must stay green), `engine/tests/test_stdlib_core.py::test_conductor_state_needs_no_yaml`

**Interfaces:**
- Produces (unchanged signatures): `read_conductor(root: Path) -> dict`, `write_conductor(root: Path, data: dict) -> None`, `record_input_hashes(root: Path) -> dict`, `CONDUCTOR_FILE = ".conductor.md"`.

- [ ] **Step 1: Rewrite the module to use stdlib `json`**

Replace the entire body of `state/conductor_state.py` with:

```python
"""Read/write the Conductor's private state file, <engagement>/.conductor.md.

Interaction context only — never engagement content. Content state is always
derived from the engagement files via state.state.read_state(); this file holds
register, autonomy, version stamp, deferred processes, and the model-input hashes
that power staleness detection (state.staleness).

The frontmatter body is JSON (stdlib only) fenced by '---' lines, so the core
runs without third-party deps in any code sandbox.
"""
from __future__ import annotations

import json
from pathlib import Path

from state.staleness import hash_inputs

CONDUCTOR_FILE = ".conductor.md"


def read_conductor(root: Path) -> dict:
    path = Path(root) / CONDUCTOR_FILE
    if not path.exists():
        return {}
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    rest = text[len("---\n"):]
    end = rest.rfind("\n---")
    if end == -1:
        return {}
    body = rest[:end].strip()
    if not body:
        return {}
    try:
        loaded = json.loads(body)
    except json.JSONDecodeError:
        return {}  # legacy/corrupt frontmatter — treat as empty; caller re-stamps
    return loaded if isinstance(loaded, dict) else {}


def write_conductor(root: Path, data: dict) -> None:
    body = json.dumps(data, indent=2)
    (Path(root) / CONDUCTOR_FILE).write_text(f"---\n{body}\n---\n")


def record_input_hashes(root: Path) -> dict:
    data = read_conductor(root)
    data["model_input_hashes"] = hash_inputs(root)
    write_conductor(root, data)
    return data
```

- [ ] **Step 2: Run the conductor-state tests**

Run: `.venv/bin/python -m pytest state/tests/test_conductor_state.py engine/tests/test_stdlib_core.py::test_conductor_state_needs_no_yaml -v`
Expected: PASS — round-trip equality still holds (data dicts survive a JSON round-trip), and the no-yaml guard passes.

- [ ] **Step 3: Commit**

```bash
git add state/conductor_state.py
git commit -m "refactor(state): store .conductor.md as stdlib JSON, drop pyyaml import

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Lazy, graceful workbook import in run.py

**Files:**
- Modify: `engine/run.py` (remove the top-level `from engine.workbook import write_workbook`; import it lazily in `main`)
- Test: `engine/tests/test_stdlib_core.py` (both `engine_run` tests), `engine/tests/test_run.py` (existing workbook tests must stay green with openpyxl present)

**Interfaces:**
- Produces (unchanged): `engine.run.main(argv: list[str] | None = None) -> int`, `engine.run.build_results(model_dir) -> dict`.

- [ ] **Step 1: Remove the eager workbook import**

In `engine/run.py`, delete this line near the top:

```python
from engine.workbook import write_workbook
```

(Leave the other imports — `engine.compute`, `engine.model` — untouched.)

- [ ] **Step 2: Make the workbook write lazy and graceful**

In `engine/run.py`, replace the tail of `main`:

```python
    if "--no-workbook" not in flags:
        write_workbook(load_inputs(model_dir), results, engagement / "financial-model.xlsx")
    return 0
```

with:

```python
    if "--no-workbook" not in flags:
        try:
            from engine.workbook import write_workbook
            write_workbook(load_inputs(model_dir), results, engagement / "financial-model.xlsx")
        except ImportError:
            print(
                "note: openpyxl not available — skipped financial-model.xlsx "
                "(every number is in model/results.json)",
                file=sys.stderr,
            )
    return 0
```

- [ ] **Step 3: Run the stdlib-core engine tests + existing run tests**

Run: `.venv/bin/python -m pytest engine/tests/test_stdlib_core.py engine/tests/test_run.py -v`
Expected: PASS — core path and graceful-degrade path pass under the blocker; with openpyxl present, the existing `test_run.py` workbook assertions still pass.

- [ ] **Step 4: Commit**

```bash
git add engine/run.py
git commit -m "refactor(engine): lazy workbook import; degrade gracefully without openpyxl

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Drop the phantom `formulas` dependency

`formulas` is listed in `requirements.txt` but imported nowhere. Remove it.

**Files:**
- Modify: `requirements.txt`
- Test: `engine/tests/test_stdlib_core.py` (already blocks `formulas`; confirms nothing needs it)

- [ ] **Step 1: Remove the line**

In `requirements.txt`, delete:

```
formulas>=1.3.4
```

Resulting file:

```
pytest>=9.0.3
pyyaml>=6.0.3
openpyxl>=3.1.5
```

(`pyyaml` and `openpyxl` stay — `pyyaml` is still used elsewhere in `state/` test tooling and skill-frontmatter parsing in `tests/`; `openpyxl` still powers the workbook where present. Only `formulas` was unused.)

- [ ] **Step 2: Verify the suite is unaffected**

Run: `.venv/bin/python -c "import formulas" 2>&1 | head -1` → confirm it's not imported by the app (this just shows the module may still be installed locally; the guard test proves the code doesn't need it).
Run: `.venv/bin/python -m pytest engine/tests/test_stdlib_core.py -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore(deps): drop unused 'formulas' dependency

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: Full suite + CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run the entire suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — all tests, including the 3 new stdlib-core tests (prior count + 3), with golden numbers unchanged.

- [ ] **Step 2: Add the CHANGELOG entry**

In `CHANGELOG.md`, under `## [Unreleased]`, add:

```markdown
### Changed
- **Engine + state core is now stdlib-only.** `engine.run` (compute path) and all
  `state/` helpers run with no third-party imports: `.conductor.md` is stored as
  stdlib JSON (was pyyaml), the Excel workbook is imported lazily and skipped
  gracefully when `openpyxl` is absent (numbers still land in `model/results.json`),
  and the unused `formulas` dependency was removed. This lets the auditable numbers
  run in any code sandbox (Claude Code, Cowork, Claude.ai). The workbook still
  generates where `openpyxl` is installed. Guarded by `engine/tests/test_stdlib_core.py`.
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): stdlib-only engine + state core

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage (foundation milestone, engine portability slice of §3.A + §3.C):**
- §3.A "stdlib-only core: drop phantom formulas" → Task 4 ✓
- §3.A "lazy-import the workbook so engine.run needs no third-party deps" → Task 3 ✓
- §3.A "replace pyyaml in conductor_state.py with stdlib" → Task 2 ✓
- §3.A "numbers run with bare python, no venv, no pip" (AC-2/AC-4) → Task 1 guard ✓
- §3.C "xlsx becomes capability-gated" (lazy/graceful) → Task 3 ✓ (full *removal* deferred to the data-contract plan, as scoped)
- Out of scope here (later plans): `bin/` wrapper, session-start hook, conversational onboarding, data-contract schema doc, `generate-artifact` skill, full workbook deletion, clean-machine CI smoke. Noted in spec §5.

**Placeholder scan:** none — every step has exact paths, full code, and exact commands.

**Type consistency:** `main(argv)->int`, `build_results(model_dir)->dict`, `read_conductor/write_conductor/record_input_hashes`, `CONDUCTOR_FILE` all match their existing signatures; no renamed symbols.
