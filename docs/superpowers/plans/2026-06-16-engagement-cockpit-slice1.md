# Engagement Cockpit — Slice 1 (Read-Only Cockpit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local web cockpit that reads one engagement folder and shows live phase/gate status, the parsed financial model, and every deliverable in one navigable place — with zero Claude invocation.

**Architecture:** A thin Python (FastAPI) backend exposes a pure `read_state(engagement_dir)` snapshot as JSON, watches the folder and pushes updated snapshots over SSE, and serves a dependency-free vanilla-JS single-page frontend. State is *derived from the filesystem* using the methodology's existing phase map — the cockpit reads state, it does not own methodology logic. This is Slice 1 of three; Slice 2 (drive phases via `claude -p`) and Slice 3 (edit-through-engine) are separate plans built on this foundation.

**Tech Stack:** Python 3.13, FastAPI, uvicorn, watchfiles, pytest, vanilla JS/HTML/CSS.

**Spec:** `docs/superpowers/specs/2026-06-16-engagement-cockpit-design.md`

---

## Snapshot Schema (the contract every task shares)

`read_state(engagement_dir: Path) -> dict` returns exactly this shape. Every later task depends on these keys — do not rename them.

```python
{
  "engagement": "pso-delivery-team",        # folder name
  "path": "/abs/path/to/engagement",
  "progress": {"done": 4, "total": 12},     # phases done / total phases (gates excluded)
  "phases": [
    {
      "id": "1",
      "name": "Scope",
      "skill": "ai-process-assessment:scoping-engagement",
      "output": "scope.md",                 # relative path whose existence == done
      "status": "done",                     # "done" | "available" | "blocked"
      "blocked_reason": None,               # str when status == "blocked", else None
    },
    # ... 12 phase entries total (1,2,3,4,5,6,7,8,8.5,9,10,11)
  ],
  "gates": [
    {
      "id": "grc",
      "name": "Governance & Risk (Gate A)",
      "output": "grc/_index.md",
      "status": "not-required",             # "not-required" | "required" | "done"
      "reason": None,                       # str when required/done, else None
    },
    {
      "id": "deliverable",
      "name": "Deliverable Gate (Gate B)",
      "output": "evidence-log.md",
      "status": "not-run",                  # "not-run" | "done"
      "reason": None,
    },
  ],
  "model": {
    "results": {...} | None,                # parsed model/results.json, or None if absent
    "inputs_present": {                     # which model/*.json input files exist
      "baselines": True, "value": False, "scores": True,
      "initiatives": False, "costs": False,
    },
  },
}
```

---

## File Structure

- Create: `cockpit/__init__.py` — package marker
- Create: `cockpit/phases.py` — `Phase` dataclass + `PHASES`, `GATES` tables + helpers (the encoded state machine)
- Create: `cockpit/state.py` — `read_state(engagement_dir)` pure snapshot builder
- Create: `cockpit/server.py` — `create_app(engagement_dir)` FastAPI app (state API, file reader, SSE, static)
- Create: `cockpit/watch.py` — `snapshot_events(engagement_dir)` async generator for SSE
- Create: `cockpit/__main__.py` — `python -m cockpit <engagement-dir>` launcher
- Create: `cockpit/web/index.html`, `cockpit/web/app.js`, `cockpit/web/styles.css` — frontend
- Create: `cockpit/tests/__init__.py`, `cockpit/tests/conftest.py` — fixture-folder builder
- Create: `cockpit/tests/test_phases.py`, `test_state.py`, `test_server.py`
- Modify: `requirements.txt` — add fastapi, uvicorn, watchfiles, httpx

---

## Task 1: Scaffold package and dependencies

**Files:**
- Create: `cockpit/__init__.py`
- Create: `cockpit/tests/__init__.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Create the package markers**

`cockpit/__init__.py`:
```python
"""Engagement Cockpit — local read-only control surface over an engagement folder."""
```

`cockpit/tests/__init__.py`:
```python
```
(empty file)

- [ ] **Step 2: Add dependencies to requirements.txt**

Append these lines to `requirements.txt`:
```
fastapi>=0.110
uvicorn>=0.29
watchfiles>=0.21
httpx>=0.27
```

- [ ] **Step 3: Install**

Run: `pip install -r requirements.txt`
Expected: installs fastapi, uvicorn, watchfiles, httpx without error.

- [ ] **Step 4: Verify import works**

Run: `python -c "import fastapi, uvicorn, watchfiles, httpx; print('ok')"`
Expected: prints `ok`

- [ ] **Step 5: Commit**

```bash
git add cockpit/__init__.py cockpit/tests/__init__.py requirements.txt
git commit -m "chore(cockpit): scaffold package and add web deps"
```

---

## Task 2: Phase & gate table (the encoded state machine)

**Files:**
- Create: `cockpit/phases.py`
- Test: `cockpit/tests/test_phases.py`

- [ ] **Step 1: Write the failing test**

`cockpit/tests/test_phases.py`:
```python
from cockpit.phases import PHASES, GATES, Phase


def test_twelve_phases_in_methodology_order():
    ids = [p.id for p in PHASES]
    assert ids == ["1", "2", "3", "4", "5", "6", "7", "8", "8.5", "9", "10", "11"]


def test_first_phase_has_no_predecessor():
    assert PHASES[0].predecessor is None
    assert PHASES[0].output == "scope.md"


def test_each_later_phase_predecessor_is_prior_output():
    for prev, cur in zip(PHASES, PHASES[1:]):
        assert cur.predecessor == prev.output


def test_phase_5_outputs_opportunities_index():
    phase5 = next(p for p in PHASES if p.id == "5")
    assert phase5.output == "opportunities/_index.md"
    assert phase5.skill == "ai-process-assessment:identifying-opportunities"


def test_gates_present():
    gate_ids = [g.id for g in GATES]
    assert gate_ids == ["grc", "deliverable"]
    grc = GATES[0]
    assert grc.output == "grc/_index.md"
    assert GATES[1].output == "evidence-log.md"


def test_phase_is_frozen_dataclass():
    p = PHASES[0]
    try:
        p.id = "x"
        assert False, "Phase should be immutable"
    except Exception:
        pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest cockpit/tests/test_phases.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cockpit.phases'`

- [ ] **Step 3: Write the implementation**

`cockpit/phases.py`:
```python
"""The methodology's phase map, encoded as data.

Source of truth: skills/using-methodology/SKILL.md phase table. Phase progress is
derived purely from file existence; this module holds no logic, only the schema.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    skill: str
    output: str            # relative path whose existence means the phase is done
    predecessor: str | None  # relative path that must exist for the phase to be available


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    output: str            # relative path whose existence means the gate has run


PHASES: list[Phase] = [
    Phase("1", "Scope", "ai-process-assessment:scoping-engagement", "scope.md", None),
    Phase("2", "Context", "ai-process-assessment:mapping-context", "context.md", "scope.md"),
    Phase("3", "Tech & Data", "ai-process-assessment:inventorying-tech-data", "tech-inventory.md", "context.md"),
    Phase("4", "Discovery", "ai-process-assessment:discovering-processes", "processes/_index.md", "tech-inventory.md"),
    Phase("5", "Opportunities", "ai-process-assessment:identifying-opportunities", "opportunities/_index.md", "processes/_index.md"),
    Phase("6", "Scoring", "ai-process-assessment:scoring-opportunities", "scores/_index.md", "opportunities/_index.md"),
    Phase("7", "Roadmap", "ai-process-assessment:prioritizing-roadmap", "roadmap.md", "scores/_index.md"),
    Phase("8", "Use-Case Briefs", "ai-process-assessment:packaging-usecases", "usecase-briefs/_index.md", "roadmap.md"),
    Phase("8.5", "Cost Actuals", "ai-process-assessment:collecting-cost-actuals", "cost-actuals.md", "usecase-briefs/_index.md"),
    Phase("9", "Business Case", "ai-process-assessment:building-business-case", "business-case.md", "cost-actuals.md"),
    Phase("10", "Executive Summary", "ai-process-assessment:building-executive-summary", "executive-summary.md", "business-case.md"),
    Phase("11", "Deliverable", "ai-process-assessment:building-deliverable", "deliverable.html", "executive-summary.md"),
]

GATES: list[Gate] = [
    Gate("grc", "Governance & Risk (Gate A)", "grc/_index.md"),
    Gate("deliverable", "Deliverable Gate (Gate B)", "evidence-log.md"),
]

# Maps a model/*.json input stem to the human key surfaced in the snapshot.
MODEL_INPUTS: dict[str, str] = {
    "baselines": "baselines",
    "value": "value",
    "scores": "scores",
    "initiatives": "initiatives",
    "costs": "costs",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest cockpit/tests/test_phases.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add cockpit/phases.py cockpit/tests/test_phases.py
git commit -m "feat(cockpit): encode methodology phase map as data"
```

---

## Task 3: State reader — phase status

**Files:**
- Create: `cockpit/state.py`
- Test: `cockpit/tests/conftest.py`, `cockpit/tests/test_state.py`

- [ ] **Step 1: Write the fixture builder**

`cockpit/tests/conftest.py`:
```python
import pytest


@pytest.fixture
def engagement(tmp_path):
    """Return a builder that creates files inside a temp engagement folder.

    Usage:
        path = engagement("scope.md", "context.md")        # empty files
        path = engagement(**{"model/scores.json": "[]"})   # file with content
    """
    root = tmp_path / "acme-engagement"
    root.mkdir()

    def build(*empty_files, **files_with_content):
        for rel in empty_files:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("")
        for rel, content in files_with_content.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        return root

    return build
```

- [ ] **Step 2: Write the failing test**

`cockpit/tests/test_state.py`:
```python
from cockpit.state import read_state


def test_empty_engagement_only_phase1_available(engagement):
    root = engagement()  # no files
    snap = read_state(root)
    by_id = {p["id"]: p for p in snap["phases"]}
    assert by_id["1"]["status"] == "available"
    assert by_id["2"]["status"] == "blocked"
    assert by_id["2"]["blocked_reason"] == "Waiting on Scope (scope.md)"
    assert snap["progress"] == {"done": 0, "total": 12}


def test_done_phase_unlocks_next(engagement):
    root = engagement("scope.md")
    by_id = {p["id"]: p for p in read_state(root)["phases"]}
    assert by_id["1"]["status"] == "done"
    assert by_id["2"]["status"] == "available"
    assert by_id["3"]["status"] == "blocked"


def test_progress_counts_done_phases(engagement):
    root = engagement("scope.md", "context.md", "tech-inventory.md")
    assert read_state(root)["progress"] == {"done": 3, "total": 12}


def test_folder_index_counts_as_done(engagement):
    root = engagement("scope.md", "context.md", "tech-inventory.md",
                      "processes/_index.md")
    by_id = {p["id"]: p for p in read_state(root)["phases"]}
    assert by_id["4"]["status"] == "done"
    assert by_id["5"]["status"] == "available"


def test_snapshot_top_level_fields(engagement):
    root = engagement()
    snap = read_state(root)
    assert snap["engagement"] == "acme-engagement"
    assert snap["path"] == str(root)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest cockpit/tests/test_state.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cockpit.state'`

- [ ] **Step 4: Write the implementation**

`cockpit/state.py`:
```python
"""Pure snapshot builder: an engagement folder -> a state dict.

No Claude, no network, no mutation. The cockpit's correctness lives here, so it is
a pure function of the filesystem and the encoded phase map.
"""
from __future__ import annotations

from pathlib import Path

from cockpit.phases import GATES, MODEL_INPUTS, PHASES


def _phase_status(root: Path) -> list[dict]:
    out = []
    for phase in PHASES:
        done = (root / phase.output).exists()
        if done:
            status, reason = "done", None
        elif phase.predecessor is None or (root / phase.predecessor).exists():
            status, reason = "available", None
        else:
            pred = next(p for p in PHASES if p.output == phase.predecessor)
            status = "blocked"
            reason = f"Waiting on {pred.name} ({phase.predecessor})"
        out.append({
            "id": phase.id,
            "name": phase.name,
            "skill": phase.skill,
            "output": phase.output,
            "status": status,
            "blocked_reason": reason,
        })
    return out


def read_state(engagement_dir) -> dict:
    root = Path(engagement_dir)
    phases = _phase_status(root)
    done = sum(1 for p in phases if p["status"] == "done")
    return {
        "engagement": root.name,
        "path": str(root),
        "progress": {"done": done, "total": len(PHASES)},
        "phases": phases,
        "gates": _gate_status(root),
        "model": _model_section(root),
    }
```

Note: `_gate_status` and `_model_section` are added in Tasks 4 and 5. For this task, add temporary stubs at the bottom of the file so the module imports:
```python
def _gate_status(root: Path) -> list[dict]:
    return []


def _model_section(root: Path) -> dict:
    return {"results": None, "inputs_present": {}}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest cockpit/tests/test_state.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Commit**

```bash
git add cockpit/state.py cockpit/tests/conftest.py cockpit/tests/test_state.py
git commit -m "feat(cockpit): derive phase status from folder contents"
```

---

## Task 4: State reader — gate status (GRC trigger detection)

**Files:**
- Modify: `cockpit/state.py` (replace the `_gate_status` stub)
- Test: `cockpit/tests/test_state.py` (add tests)

GRC gate logic (from `skills/identifying-opportunities/SKILL.md`): `opportunities/_index.md`
is a markdown table whose columns are `OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural`. The **GRC** value (column index 5, zero-based, after splitting a row on `|` and dropping the leading/trailing empties) is `Green`, `Yellow`, or `Red`. Any `Yellow`/`Red` makes the gate **required**. If `grc/_index.md` exists, the gate is **done**.

- [ ] **Step 1: Write the failing tests**

Add to `cockpit/tests/test_state.py`:
```python
OPPS_HEADER = (
    "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
    "|--------|---------|------|-------------|----------------|-----|------------|\n"
)


def test_grc_not_required_when_no_opportunities(engagement):
    root = engagement()
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "not-required"


def test_grc_not_required_when_all_green(engagement):
    body = "| OPP-001 | PROC-001 | RPA | Green | Green | Green | None |\n"
    root = engagement(**{"opportunities/_index.md": OPPS_HEADER + body})
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "not-required"


def test_grc_required_when_non_green_flag(engagement):
    body = (
        "| OPP-001 | PROC-001 | RPA | Green | Green | Green | None |\n"
        "| OPP-002 | PROC-002 | Agentic | Yellow | Green | Red | None |\n"
    )
    root = engagement(**{"opportunities/_index.md": OPPS_HEADER + body})
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "required"
    assert gates["grc"]["reason"] == "1 opportunity flagged Yellow/Red"


def test_grc_done_when_grc_index_exists(engagement):
    body = "| OPP-002 | PROC-002 | Agentic | Yellow | Green | Red | None |\n"
    root = engagement(**{
        "opportunities/_index.md": OPPS_HEADER + body,
        "grc/_index.md": "cleared",
    })
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "done"


def test_deliverable_gate_done_when_evidence_log_exists(engagement):
    root = engagement("evidence-log.md")
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["deliverable"]["status"] == "done"
    assert read_state(engagement())  # absent -> not-run path covered below


def test_deliverable_gate_not_run_when_absent(engagement):
    gates = {g["id"]: g for g in read_state(engagement())["gates"]}
    assert gates["deliverable"]["status"] == "not-run"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cockpit/tests/test_state.py -k grc -v`
Expected: FAIL (gates list is empty from the stub, so `gates["grc"]` raises KeyError)

- [ ] **Step 3: Replace the `_gate_status` stub in `cockpit/state.py`**

Delete the stub `_gate_status` and add this. Also add the helper above it:
```python
def _count_non_green_grc(index_path: Path) -> int:
    """Count opportunity rows whose GRC flag is Yellow or Red."""
    count = 0
    for line in index_path.read_text().splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != 7:
            continue
        grc = cells[5].lower()
        if cells[0].lower() in ("opp-id", "") or set(cells[5]) <= {"-"}:
            continue  # header or separator row
        if grc in ("yellow", "red"):
            count += 1
    return count


def _gate_status(root: Path) -> list[dict]:
    # Gate A — GRC
    opps_index = root / "opportunities" / "_index.md"
    grc_done = (root / "grc" / "_index.md").exists()
    if grc_done:
        grc = {"status": "done", "reason": "GRC review recorded in grc/_index.md"}
    elif opps_index.exists() and (n := _count_non_green_grc(opps_index)) > 0:
        noun = "opportunity" if n == 1 else "opportunities"
        grc = {"status": "required", "reason": f"{n} {noun} flagged Yellow/Red"}
    else:
        grc = {"status": "not-required", "reason": None}

    # Gate B — Deliverable
    deliverable_done = (root / "evidence-log.md").exists()
    deliverable = (
        {"status": "done", "reason": "Clearance recorded in evidence-log.md"}
        if deliverable_done
        else {"status": "not-run", "reason": None}
    )

    return [
        {"id": "grc", "name": GATES[0].name, "output": GATES[0].output, **grc},
        {"id": "deliverable", "name": GATES[1].name, "output": GATES[1].output, **deliverable},
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest cockpit/tests/test_state.py -v`
Expected: PASS (all state tests pass)

- [ ] **Step 5: Commit**

```bash
git add cockpit/state.py cockpit/tests/test_state.py
git commit -m "feat(cockpit): detect GRC and deliverable gate status"
```

---

## Task 5: State reader — model/results section

**Files:**
- Modify: `cockpit/state.py` (replace the `_model_section` stub)
- Test: `cockpit/tests/test_state.py` (add tests)

- [ ] **Step 1: Write the failing tests**

Add to `cockpit/tests/test_state.py`:
```python
import json


def test_model_results_none_when_absent(engagement):
    snap = read_state(engagement())
    assert snap["model"]["results"] is None
    assert snap["model"]["inputs_present"] == {
        "baselines": False, "value": False, "scores": False,
        "initiatives": False, "costs": False,
    }


def test_model_results_parsed_when_present(engagement):
    results = {"investment": {"low": 100, "high": 200}}
    root = engagement(**{
        "model/results.json": json.dumps(results),
        "model/scores.json": "[]",
    })
    snap = read_state(root)
    assert snap["model"]["results"] == results
    assert snap["model"]["inputs_present"]["scores"] is True
    assert snap["model"]["inputs_present"]["costs"] is False


def test_model_results_none_when_corrupt(engagement):
    root = engagement(**{"model/results.json": "{not json"})
    assert read_state(root)["model"]["results"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cockpit/tests/test_state.py -k model -v`
Expected: FAIL (stub returns `inputs_present == {}`)

- [ ] **Step 3: Replace the `_model_section` stub in `cockpit/state.py`**

Add `import json` at the top of the file, then replace the stub:
```python
def _model_section(root: Path) -> dict:
    results_path = root / "model" / "results.json"
    results = None
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text())
        except (json.JSONDecodeError, OSError):
            results = None
    inputs_present = {
        key: (root / "model" / f"{stem}.json").exists()
        for stem, key in MODEL_INPUTS.items()
    }
    return {"results": results, "inputs_present": inputs_present}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest cockpit/tests/test_state.py -v`
Expected: PASS (all state tests pass)

- [ ] **Step 5: Commit**

```bash
git add cockpit/state.py cockpit/tests/test_state.py
git commit -m "feat(cockpit): surface parsed financial model in snapshot"
```

---

## Task 6: Server — state API and static frontend

**Files:**
- Create: `cockpit/server.py`
- Test: `cockpit/tests/test_server.py`

- [ ] **Step 1: Write the failing test**

`cockpit/tests/test_server.py`:
```python
from fastapi.testclient import TestClient

from cockpit.server import create_app


def _client(engagement_root):
    return TestClient(create_app(engagement_root))


def test_state_endpoint_returns_snapshot(engagement):
    root = engagement("scope.md")
    r = _client(root).get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["engagement"] == "acme-engagement"
    assert body["progress"]["done"] == 1


def test_index_html_served_at_root(engagement):
    r = _client(engagement()).get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest cockpit/tests/test_server.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'cockpit.server'`

- [ ] **Step 3: Write the implementation**

`cockpit/server.py`:
```python
"""FastAPI app for the cockpit. One app instance is bound to one engagement folder."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cockpit.state import read_state

WEB_DIR = Path(__file__).parent / "web"


def create_app(engagement_dir) -> FastAPI:
    root = Path(engagement_dir).resolve()
    app = FastAPI(title="Engagement Cockpit")

    @app.get("/api/state")
    def state() -> dict:
        return read_state(root)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
    return app
```

Create the `web/` directory and placeholder files so `StaticFiles` and `FileResponse` resolve (real content lands in Task 9):
```bash
mkdir -p cockpit/web
printf '<!doctype html><title>Cockpit</title><h1>Engagement Cockpit</h1>' > cockpit/web/index.html
touch cockpit/web/app.js cockpit/web/styles.css
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest cockpit/tests/test_server.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add cockpit/server.py cockpit/tests/test_server.py cockpit/web/
git commit -m "feat(cockpit): serve state API and static shell"
```

---

## Task 7: Server — read a single deliverable file

**Files:**
- Modify: `cockpit/server.py` (add `/api/file` route)
- Test: `cockpit/tests/test_server.py` (add tests)

The reader view fetches deliverable contents by relative path. The route must refuse
path traversal outside the engagement folder.

- [ ] **Step 1: Write the failing tests**

Add to `cockpit/tests/test_server.py`:
```python
def test_file_endpoint_returns_contents(engagement):
    root = engagement(**{"scope.md": "# Scope\nHello"})
    r = _client(root).get("/api/file", params={"path": "scope.md"})
    assert r.status_code == 200
    assert r.json() == {"path": "scope.md", "content": "# Scope\nHello"}


def test_file_endpoint_404_for_missing(engagement):
    r = _client(engagement()).get("/api/file", params={"path": "nope.md"})
    assert r.status_code == 404


def test_file_endpoint_rejects_traversal(engagement):
    r = _client(engagement()).get("/api/file", params={"path": "../secret.md"})
    assert r.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cockpit/tests/test_server.py -k file -v`
Expected: FAIL (404 for all — route does not exist yet)

- [ ] **Step 3: Add the route to `cockpit/server.py`**

Add these imports at the top:
```python
from fastapi import HTTPException, Query
```
Add inside `create_app`, before the `app.mount(...)` line:
```python
    @app.get("/api/file")
    def file(path: str = Query(...)) -> dict:
        target = (root / path).resolve()
        if root not in target.parents and target != root:
            raise HTTPException(status_code=400, detail="path escapes engagement folder")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return {"path": path, "content": target.read_text()}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest cockpit/tests/test_server.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add cockpit/server.py cockpit/tests/test_server.py
git commit -m "feat(cockpit): read deliverable files with traversal guard"
```

---

## Task 8: Live updates — folder watcher and SSE endpoint

**Files:**
- Create: `cockpit/watch.py`
- Modify: `cockpit/server.py` (add `/api/events`)
- Test: `cockpit/tests/test_server.py` (add SSE test)

- [ ] **Step 1: Write the watcher**

`cockpit/watch.py`:
```python
"""Async snapshot stream: yields a JSON snapshot now, then again on every change."""
from __future__ import annotations

import json
from pathlib import Path

from watchfiles import awatch

from cockpit.state import read_state


async def snapshot_events(engagement_dir):
    """Yield SSE 'data:' frames: the current snapshot, then one per filesystem change."""
    root = Path(engagement_dir)
    yield _frame(root)
    async for _changes in awatch(root):
        yield _frame(root)


def _frame(root: Path) -> str:
    return f"data: {json.dumps(read_state(root))}\n\n"
```

- [ ] **Step 2: Write the failing test (initial snapshot is delivered)**

Add to `cockpit/tests/test_server.py`:
```python
import json as _json


def test_events_stream_emits_initial_snapshot(engagement):
    root = engagement("scope.md")
    with _client(root).stream("GET", "/api/events") as r:
        assert r.status_code == 200
        first_line = next(line for line in r.iter_lines() if line.startswith("data:"))
    payload = _json.loads(first_line[len("data:"):].strip())
    assert payload["progress"]["done"] == 1
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest cockpit/tests/test_server.py -k events -v`
Expected: FAIL (404 — `/api/events` not defined)

- [ ] **Step 4: Add the SSE route to `cockpit/server.py`**

Add the import:
```python
from fastapi.responses import FileResponse, StreamingResponse
```
(replace the existing `from fastapi.responses import FileResponse` line)

Add the import for the watcher near the top:
```python
from cockpit.watch import snapshot_events
```
Add inside `create_app`, before `app.mount(...)`:
```python
    @app.get("/api/events")
    def events() -> StreamingResponse:
        return StreamingResponse(
            snapshot_events(root), media_type="text/event-stream"
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest cockpit/tests/test_server.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Commit**

```bash
git add cockpit/watch.py cockpit/server.py cockpit/tests/test_server.py
git commit -m "feat(cockpit): push live snapshots over SSE on folder changes"
```

---

## Task 9: Frontend — phase-map board and deliverable reader

**Files:**
- Modify: `cockpit/web/index.html`, `cockpit/web/app.js`, `cockpit/web/styles.css`

This task is presentation; verification is manual (Task 10 runs it). No unit test —
the data layer it consumes is already tested.

- [ ] **Step 1: Write `cockpit/web/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Engagement Cockpit</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <header>
    <h1 id="engagement-name">Engagement Cockpit</h1>
    <div id="progress" class="progress"></div>
  </header>
  <main>
    <section id="board" class="board" aria-label="Phase status"></section>
    <section id="reader" class="reader" aria-label="Deliverable reader">
      <p class="hint">Select a completed phase to read its output.</p>
    </section>
  </main>
  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write `cockpit/web/app.js`**

```javascript
const board = document.getElementById("board");
const reader = document.getElementById("reader");
const nameEl = document.getElementById("engagement-name");
const progressEl = document.getElementById("progress");

function render(snapshot) {
  nameEl.textContent = snapshot.engagement;
  const { done, total } = snapshot.progress;
  progressEl.textContent = `${done} / ${total} phases complete`;

  board.innerHTML = "";
  for (const phase of snapshot.phases) {
    const card = document.createElement("button");
    card.className = `card status-${phase.status}`;
    card.disabled = phase.status !== "done";
    card.innerHTML =
      `<span class="phase-id">${phase.id}</span>` +
      `<span class="phase-name">${phase.name}</span>` +
      `<span class="badge">${phase.status}</span>` +
      (phase.blocked_reason ? `<span class="reason">${phase.blocked_reason}</span>` : "");
    if (phase.status === "done") {
      card.addEventListener("click", () => openFile(phase));
    }
    board.appendChild(card);
  }

  const gates = document.createElement("div");
  gates.className = "gates";
  for (const gate of snapshot.gates) {
    const g = document.createElement("div");
    g.className = `gate gate-${gate.status}`;
    g.textContent = `${gate.name}: ${gate.status}` + (gate.reason ? ` — ${gate.reason}` : "");
    gates.appendChild(g);
  }
  board.appendChild(gates);
}

async function openFile(phase) {
  reader.innerHTML = `<p class="hint">Loading ${phase.output}…</p>`;
  if (phase.output.endsWith(".html")) {
    reader.innerHTML = `<iframe class="deliverable" src="/api/file-raw?path=${encodeURIComponent(phase.output)}"></iframe>`;
    return;
  }
  const r = await fetch(`/api/file?path=${encodeURIComponent(phase.output)}`);
  if (!r.ok) {
    reader.innerHTML = `<p class="hint">Could not load ${phase.output}.</p>`;
    return;
  }
  const { content } = await r.json();
  const pre = document.createElement("pre");
  pre.className = "markdown";
  pre.textContent = content;
  reader.innerHTML = `<h2>${phase.name} — ${phase.output}</h2>`;
  reader.appendChild(pre);
}

const source = new EventSource("/api/events");
source.onmessage = (e) => render(JSON.parse(e.data));
source.onerror = () => fetch("/api/state").then((r) => r.json()).then(render);
```

Note: the HTML deliverable uses `/api/file-raw` (added in Step 4) so the iframe gets
real `text/html`, not JSON.

- [ ] **Step 3: Write `cockpit/web/styles.css`**

```css
:root {
  --done: #1b8a5a; --available: #2f6feb; --blocked: #9aa3af;
  --required: #c9760b; --bg: #0f1115; --panel: #171a21; --text: #e6e9ef;
}
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.5 system-ui, sans-serif; background: var(--bg); color: var(--text); }
header { display: flex; align-items: baseline; gap: 1rem; padding: 1rem 1.5rem; border-bottom: 1px solid #222; }
h1 { font-size: 1.1rem; margin: 0; }
.progress { color: #9aa3af; }
main { display: grid; grid-template-columns: 360px 1fr; gap: 1rem; padding: 1rem 1.5rem; }
.board { display: flex; flex-direction: column; gap: .5rem; }
.card { display: grid; grid-template-columns: 2rem 1fr auto; align-items: center; gap: .5rem;
  text-align: left; padding: .6rem .8rem; border: 1px solid #262b35; border-radius: 8px;
  background: var(--panel); color: var(--text); cursor: default; }
.card[disabled] { opacity: .6; }
.card.status-done { cursor: pointer; border-left: 4px solid var(--done); }
.card.status-available { border-left: 4px solid var(--available); }
.card.status-blocked { border-left: 4px solid var(--blocked); }
.phase-id { font-weight: 700; color: #9aa3af; }
.badge { font-size: .75rem; text-transform: uppercase; color: #9aa3af; }
.reason { grid-column: 1 / -1; font-size: .8rem; color: #9aa3af; }
.gates { margin-top: .5rem; display: flex; flex-direction: column; gap: .35rem; }
.gate { padding: .5rem .8rem; border-radius: 8px; background: var(--panel); font-size: .85rem; }
.gate-required { border-left: 4px solid var(--required); }
.gate-done { border-left: 4px solid var(--done); }
.reader { background: var(--panel); border-radius: 8px; padding: 1rem 1.25rem; min-height: 60vh; }
.markdown { white-space: pre-wrap; font: 13px/1.6 ui-monospace, monospace; }
.deliverable { width: 100%; height: 75vh; border: 0; background: #fff; border-radius: 6px; }
.hint { color: #9aa3af; }
```

- [ ] **Step 4: Add a raw-file route so the HTML deliverable renders in the iframe**

Add to `cockpit/server.py` inside `create_app`, before `app.mount(...)`:
```python
    @app.get("/api/file-raw")
    def file_raw(path: str = Query(...)) -> FileResponse:
        target = (root / path).resolve()
        if root not in target.parents and target != root:
            raise HTTPException(status_code=400, detail="path escapes engagement folder")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(target)
```

- [ ] **Step 5: Add a test for the raw route**

Add to `cockpit/tests/test_server.py`:
```python
def test_file_raw_serves_html(engagement):
    root = engagement(**{"deliverable.html": "<h1>Deck</h1>"})
    r = _client(root).get("/api/file-raw", params={"path": "deliverable.html"})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Deck" in r.text
```

Run: `pytest cockpit/tests/test_server.py -v`
Expected: PASS (7 passed)

- [ ] **Step 6: Commit**

```bash
git add cockpit/web/ cockpit/server.py cockpit/tests/test_server.py
git commit -m "feat(cockpit): phase-map board and deliverable reader UI"
```

---

## Task 10: Launcher, end-to-end smoke, and docs

**Files:**
- Create: `cockpit/__main__.py`
- Create: `cockpit/README.md`

- [ ] **Step 1: Write the launcher**

`cockpit/__main__.py`:
```python
"""Launch the cockpit against an engagement folder.

Usage: python -m cockpit <engagement-folder> [--port 8765]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from cockpit.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="cockpit")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if not args.engagement.is_dir():
        parser.error(f"not a directory: {args.engagement}")

    app = create_app(args.engagement)
    print(f"Cockpit for '{args.engagement.name}' → http://127.0.0.1:{args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest cockpit/ -v`
Expected: PASS (all cockpit tests green)

- [ ] **Step 3: Manual smoke test against the sample engagement**

Create a throwaway engagement with a couple of phase files and launch:
```bash
mkdir -p /tmp/cockpit-smoke/acme
printf '# Scope\nDecision: should we automate intake?\n' > /tmp/cockpit-smoke/acme/scope.md
printf '# Context\n' > /tmp/cockpit-smoke/acme/context.md
python -m cockpit /tmp/cockpit-smoke/acme --port 8765
```
Open http://127.0.0.1:8765 in a browser. Expected:
- Header shows `acme` and `2 / 12 phases complete`.
- Phase 1 (Scope) and Phase 2 (Context) are green/clickable; Phase 3 is available; Phases 4–11 are blocked with "Waiting on …" reasons.
- Clicking Scope renders the markdown in the reader pane.
- In another terminal, `printf '# Tech\n' > /tmp/cockpit-smoke/acme/tech-inventory.md` — the board updates to `3 / 12` within ~1s without a refresh (SSE live update).

Stop with Ctrl-C.

- [ ] **Step 4: Write `cockpit/README.md`**

```markdown
# Engagement Cockpit (Slice 1 — read-only)

A local dashboard over a single engagement folder. Shows live phase/gate status,
the parsed financial model, and every deliverable in one place. Read-only: it does
not run Claude or edit files (those are Slice 2 and Slice 3).

## Run

    pip install -r requirements.txt
    python -m cockpit path/to/engagement-folder --port 8765

Open http://127.0.0.1:8765.

## How it works

Phase status is derived purely from file existence, using the methodology's phase
map (`skills/using-methodology/SKILL.md`). The backend (`cockpit/state.py`) is a
pure function of the folder; the server watches the folder and pushes updates over
SSE. See `docs/superpowers/specs/2026-06-16-engagement-cockpit-design.md`.

## Test

    pytest cockpit/
```

- [ ] **Step 5: Commit**

```bash
git add cockpit/__main__.py cockpit/README.md
git commit -m "feat(cockpit): launcher and read-only cockpit docs"
```

---

## Done — Slice 1 acceptance

- `pytest cockpit/` is green.
- `python -m cockpit <folder>` serves a board that shows correct done/available/blocked
  status for all 12 phases + 2 gates, renders deliverables, and updates live over SSE.
- No Claude invocation, no file mutation — purely a read layer.

**Next:** Slice 2 (drive phases via headless `claude -p` bridge) and Slice 3
(edit-through-engine) each get their own plan, built on this snapshot contract.
```
