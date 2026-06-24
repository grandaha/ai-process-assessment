# Data Architecture Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the deterministic engine the single arithmetic executor across every phase by giving every numeric input one structured owning phase, one write site, and a real engine consumer — eliminating prose→JSON re-transcription, dead JSON outputs, and premature engine runs.

**Architecture:** The methodology already declares "no arithmetic in prose, engine is the only math executor" (`skills/using-methodology/SKILL.md:67`). The engine reads `model/*.json` and writes `results.json` + `financial-model.xlsx`. This plan closes five places where the implementation drifted from that doctrine: (A) `baselines.json` is written but never read — wire it in and make `value.json` resolve volume from it; (B) wave assignments are decided in Phase 7 but only structured in Phase 9 — move the `initiatives.json` write to Phase 7; (C) Phase 9 re-writes upstream files — make it read-only with single-write ownership; (D) Phase 5 runs the full engine and emits a premature workbook — add a `--no-workbook` flag; (E) cost percentages are documented as engine constants but are per-row inputs — fix the docs.

**Tech Stack:** Python 3 (stdlib + `openpyxl`), `pytest`, markdown skill/agent specs. Engine lives in `engine/`; methodology phases live in `skills/*/SKILL.md` and `agents/*.md`.

**Delivery:** One GitHub milestone, one issue per task-group (A–E), implemented in dependency order on a single branch / PR. Task-group A is the schema root and must land first (D depends on A's `value.json` schema). B precedes C. E is independent.

---

## File Structure

**Engine (code + tests) — changed by Groups A, D:**
- `engine/model.py` — add `BaselineInput` dataclass; add `baselines` to `Inputs`; load `baselines.json`; change `ValueInput` to reference a process baseline (`process_id` + `volume_fraction`) instead of a literal `volume`.
- `engine/run.py` — resolve each opp's volume from its referenced baseline (`baseline.volume × volume_fraction`) before calling `value_range`; echo raw baselines into `results.json`; add a `--no-workbook` flag so a phase can compute `results.json` without emitting the CFO workbook.
- `engine/workbook.py` — write the *resolved* volume literal into the Inputs tab (the `ValueInput` no longer carries `volume`).
- `engine/compute.py` — unchanged (`value_range` stays a pure `improvement × volume × rate`; the percentages stay inputs).
- `engine/tests/fixtures/lattice/model/baselines.json` — new fixture.
- `engine/tests/fixtures/lattice/model/value.json` — re-shaped to the new schema.
- `engine/tests/test_loaders.py`, `test_model.py`, `test_run.py`, `test_workbook.py` — updated expectations.

**Methodology specs (docs only) — changed by Groups A, B, C, E:**
- `skills/discovering-processes/SKILL.md` — Phase 4: `baselines.json` schema gains `process_id`; correct the determinism claim to match what the engine actually computes (Group A).
- `skills/identifying-opportunities/SKILL.md` — Phase 5: `value.json` references baseline volume; run engine with `--no-workbook` (Groups A, D).
- `skills/prioritizing-roadmap/SKILL.md` — Phase 7: write `model/initiatives.json` as the structured output of wave assignment (Group B).
- `skills/building-business-case/SKILL.md` — Phase 9: read-only — verify the four input files exist, run the engine, never re-write inputs (Group C).
- `agents/business-case-analyst.md` — correct "engine parameters" wording for the cost percentages (Group E).
- `skills/collecting-cost-actuals/SKILL.md` — Phase 8.5: confirm it remains the sole writer of `costs.json` (Group C cross-check).
- `skills/using-methodology/SKILL.md` — single-write ownership table (Group C).

---

## Group A — Engine reads `baselines.json`; `value.json` resolves volume from it

**Fixes F1 (dead JSON / false determinism claim) and F5 (`volume` duplicated and drift-prone).**

Design: `value.json` stops carrying a literal `volume`. Instead each entry carries `process_id` (the baseline it draws from) and an optional `volume_fraction` (default `1.0`, for opportunities that address only a slice of a process's volume). The engine resolves `volume = baseline.volume × volume_fraction` and feeds that to the unchanged `value_range`. A missing baseline → `None` volume → `PENDING` (correct surfacing). Raw baselines are echoed into `results.json` so `baselines.md` figures are cited from a computed source, making the determinism claim true.

### Task A1: `BaselineInput` dataclass + loader

**Files:**
- Modify: `engine/model.py`
- Test: `engine/tests/test_loaders.py`

- [ ] **Step 1: Write the failing test**

Add to `engine/tests/test_loaders.py`:

```python
def test_baseline_input_from_dict():
    from engine.model import BaselineInput
    bi = BaselineInput.from_dict({
        "process_id": "PROC-01", "volume": 8000, "cycle_time_median": 5,
        "cycle_time_p90": 12, "error_rate": 0.03, "fte": 2.4,
        "source": "Ops interview R2",
    })
    assert bi.process_id == "PROC-01"
    assert bi.volume == 8000
    assert bi.fte == 2.4


def test_baseline_input_allows_missing_numeric_as_none():
    from engine.model import BaselineInput
    bi = BaselineInput.from_dict({"process_id": "PROC-09", "volume": None})
    assert bi.volume is None
    assert bi.source is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_loaders.py::test_baseline_input_from_dict -v`
Expected: FAIL with `ImportError: cannot import name 'BaselineInput'`

- [ ] **Step 3: Add the dataclass**

In `engine/model.py`, after the `CostInput` dataclass (before `Initiative`), add:

```python
@dataclass(frozen=True)
class BaselineInput:
    process_id: str
    volume: float | None
    cycle_time_median: float | None
    cycle_time_p90: float | None
    error_rate: float | None
    fte: float | None
    source: str | None

    @classmethod
    def from_dict(cls, d):
        return cls(d["process_id"], d.get("volume"), d.get("cycle_time_median"),
                   d.get("cycle_time_p90"), d.get("error_rate"), d.get("fte"),
                   d.get("source"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_loaders.py::test_baseline_input_from_dict engine/tests/test_loaders.py::test_baseline_input_allows_missing_numeric_as_none -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add engine/model.py engine/tests/test_loaders.py
git commit -m "feat(engine): add BaselineInput dataclass"
```

### Task A2: Re-shape `ValueInput` to reference a baseline

**Files:**
- Modify: `engine/model.py:29-40`
- Test: `engine/tests/test_loaders.py`

- [ ] **Step 1: Update the failing test**

Replace `test_value_input_from_dict` in `engine/tests/test_loaders.py` with:

```python
def test_value_input_references_baseline_with_default_fraction():
    vi = ValueInput.from_dict({
        "opp_id": "OPP-001", "improvement_low": 0.5,
        "improvement_high": 0.7, "process_id": "PROC-01", "rate": 100,
    })
    assert vi.opp_id == "OPP-001"
    assert vi.process_id == "PROC-01"
    assert vi.volume_fraction == 1.0  # default when omitted
    assert vi.rate == 100


def test_value_input_keeps_explicit_fraction():
    vi = ValueInput.from_dict({
        "opp_id": "OPP-007", "improvement_low": 0.3, "improvement_high": 0.5,
        "process_id": "PROC-04", "volume_fraction": 0.4, "rate": 80,
    })
    assert vi.volume_fraction == 0.4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_loaders.py::test_value_input_references_baseline_with_default_fraction -v`
Expected: FAIL with `AttributeError: 'ValueInput' object has no attribute 'process_id'`

- [ ] **Step 3: Re-shape the dataclass**

Replace `engine/model.py:29-40` (the `ValueInput` dataclass) with:

```python
@dataclass(frozen=True)
class ValueInput:
    opp_id: str
    improvement_low: float | None
    improvement_high: float | None
    process_id: str | None
    volume_fraction: float
    rate: float | None

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("improvement_low"), d.get("improvement_high"),
                   d.get("process_id"), d.get("volume_fraction", 1.0), d.get("rate"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_loaders.py::test_value_input_references_baseline_with_default_fraction engine/tests/test_loaders.py::test_value_input_keeps_explicit_fraction -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add engine/model.py engine/tests/test_loaders.py
git commit -m "feat(engine): ValueInput references baseline volume via process_id + volume_fraction"
```

### Task A3: Load `baselines.json` into `Inputs`

**Files:**
- Modify: `engine/model.py:84-106`
- Test: `engine/tests/test_loaders.py`

- [ ] **Step 1: Update the failing test**

Replace `test_load_inputs_reads_model_folder` in `engine/tests/test_loaders.py` with:

```python
def test_load_inputs_reads_model_folder(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "baselines.json").write_text(json.dumps([{
        "process_id": "PROC-01", "volume": 1000, "cycle_time_median": 4,
        "cycle_time_p90": 9, "error_rate": 0.02, "fte": 1.5,
        "source": "R2"}]))
    (model / "value.json").write_text(json.dumps([{
        "opp_id": "OPP-001", "improvement_low": 0.2, "improvement_high": 0.4,
        "process_id": "PROC-01", "rate": 50}]))
    (model / "scores.json").write_text(json.dumps([{
        "opp_id": "OPP-001", "dimensions": [3, 4, 5, 2, 4, 3]}]))
    (model / "costs.json").write_text(json.dumps([{
        "opp_id": "OPP-001", "labor_hours": 800, "labor_rate": 200,
        "tech_cost": 40000, "integration_cost": 30000,
        "change_mgmt_pct": 0.25, "contingency_pct": 0.15}]))
    (model / "initiatives.json").write_text(json.dumps([{
        "opp_id": "OPP-001", "name": "Status Reporting Assistant", "wave": 1}]))
    inp = load_inputs(model)
    assert [i.opp_id for i in inp.initiatives] == ["OPP-001"]
    assert inp.baselines["PROC-01"].volume == 1000
    assert inp.value["OPP-001"].process_id == "PROC-01"
    assert inp.scores["OPP-001"].dimensions == [3, 4, 5, 2, 4, 3]
    assert inp.costs["OPP-001"].tech_cost == 40000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_loaders.py::test_load_inputs_reads_model_folder -v`
Expected: FAIL with `AttributeError: 'Inputs' object has no attribute 'baselines'`

- [ ] **Step 3: Add `baselines` to `Inputs` and the loader**

In `engine/model.py`, change the `Inputs` dataclass (currently `engine/model.py:84-89`) to:

```python
@dataclass(frozen=True)
class Inputs:
    initiatives: list
    value: dict
    scores: dict
    costs: dict
    baselines: dict
```

Then in `load_inputs` (currently `engine/model.py:99-106`), add the baselines read and include it in the returned `Inputs`:

```python
def load_inputs(model_dir) -> "Inputs":
    """Read model/*.json into validated dataclasses. Missing files load as empty."""
    model_dir = Path(model_dir)
    initiatives = [Initiative.from_dict(d) for d in _read_json(model_dir / "initiatives.json")]
    value = {d["opp_id"]: ValueInput.from_dict(d) for d in _read_json(model_dir / "value.json")}
    scores = {d["opp_id"]: ScoreInput.from_dict(d) for d in _read_json(model_dir / "scores.json")}
    costs = {d["opp_id"]: CostInput.from_dict(d) for d in _read_json(model_dir / "costs.json")}
    baselines = {d["process_id"]: BaselineInput.from_dict(d)
                 for d in _read_json(model_dir / "baselines.json")}
    return Inputs(initiatives=initiatives, value=value, scores=scores, costs=costs,
                  baselines=baselines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_loaders.py -v`
Expected: PASS (all loader tests)

- [ ] **Step 5: Commit**

```bash
git add engine/model.py engine/tests/test_loaders.py
git commit -m "feat(engine): load baselines.json into Inputs"
```

### Task A4: Resolve volume from baseline in `run.py`; echo baselines into results

**Files:**
- Modify: `engine/run.py:23-68`
- Test: `engine/tests/test_run.py`

- [ ] **Step 1: Write the failing test**

Add to `engine/tests/test_run.py`:

```python
def test_value_resolves_volume_from_baseline():
    # Golden fixture: OPP-001 references PROC-01 (volume 8000), fraction 1.0,
    # improvement 0.5/0.7, rate 100 -> 0.5*8000*100, 0.7*8000*100
    res = build_results(FIXTURE)
    assert res["value"]["OPP-001"] == {"low": 400_000.0, "high": 560_000.0}


def test_value_pending_when_baseline_missing(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    # Drop the baselines file entirely -> volume unresolved -> PENDING
    (eng / "model" / "baselines.json").unlink()
    res = build_results(eng / "model")
    assert res["value"]["OPP-001"] == "PENDING"


def test_results_echo_baselines(tmp_path):
    res = build_results(FIXTURE)
    assert res["baselines"]["PROC-01"]["volume"] == 8000


def test_volume_fraction_scales_resolved_volume(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    value = json.loads((eng / "model" / "value.json").read_text())
    value[0]["volume_fraction"] = 0.5  # OPP-001 now addresses half of PROC-01
    (eng / "model" / "value.json").write_text(json.dumps(value))
    res = build_results(eng / "model")
    assert res["value"]["OPP-001"] == {"low": 200_000.0, "high": 280_000.0}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_run.py::test_results_echo_baselines -v`
Expected: FAIL with `KeyError: 'baselines'`

- [ ] **Step 3: Resolve volume and echo baselines**

In `engine/run.py`, replace the value loop (currently `engine/run.py:27-30`) with:

```python
    value = {}
    for opp, v in inp.value.items():
        b = inp.baselines.get(v.process_id)
        base_vol = b.volume if b is not None else None
        volume = None if base_vol is None else base_vol * v.volume_fraction
        value[opp] = _range_out(value_range(v.improvement_low, v.improvement_high,
                                            volume, v.rate))
```

Then add a `baselines` echo to the returned dict. Change the `return {` block (currently `engine/run.py:59-68`) to include it:

```python
    return {
        "value": value,
        "scores": scores,
        "costs": costs,
        "baselines": {
            pid: {
                "volume": b.volume, "cycle_time_median": b.cycle_time_median,
                "cycle_time_p90": b.cycle_time_p90, "error_rate": b.error_rate,
                "fte": b.fte, "source": b.source,
            }
            for pid, b in inp.baselines.items()
        },
        "wave1_aggregate": {
            "investment": _range_out(investment),
            "value": _range_out(annual_value),
            "payback_years": _range_out(pb),
        },
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_run.py -v`
Expected: PASS (existing golden + 4 new tests; note this depends on fixture updates in Task A5 — if `test_value_resolves_volume_from_baseline` fails here, complete A5 first then re-run)

- [ ] **Step 5: Commit**

```bash
git add engine/run.py engine/tests/test_run.py
git commit -m "feat(engine): resolve value volume from referenced baseline; echo baselines into results"
```

### Task A5: Update the `lattice` fixture to the new schema

**Files:**
- Create: `engine/tests/fixtures/lattice/model/baselines.json`
- Modify: `engine/tests/fixtures/lattice/model/value.json`

- [ ] **Step 1: Create the baselines fixture**

Write `engine/tests/fixtures/lattice/model/baselines.json`:

```json
[
  {"process_id": "PROC-01", "volume": 8000, "cycle_time_median": 6, "cycle_time_p90": 14, "error_rate": 0.04, "fte": 2.4, "source": "Lattice ops interview R2"},
  {"process_id": "PROC-02", "volume": 5000, "cycle_time_median": 3, "cycle_time_p90": 8, "error_rate": 0.02, "fte": 1.1, "source": "Lattice ops interview R2"}
]
```

- [ ] **Step 2: Re-shape the value fixture**

Replace `engine/tests/fixtures/lattice/model/value.json` with:

```json
[
  {"opp_id": "OPP-001", "improvement_low": 0.5, "improvement_high": 0.7, "process_id": "PROC-01", "volume_fraction": 1.0, "rate": 100},
  {"opp_id": "OPP-002", "improvement_low": 0.2, "improvement_high": 0.4, "process_id": "PROC-02", "volume_fraction": 1.0, "rate": 100}
]
```

- [ ] **Step 3: Run the full engine test suite to verify the golden values still hold**

Run: `python -m pytest engine/tests/test_run.py engine/tests/test_loaders.py -v`
Expected: PASS — `test_build_results_matches_golden` still passes (resolved volumes are 8000 and 5000, so value, aggregate, and payback are unchanged); the 4 Task A4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add engine/tests/fixtures/lattice/model/baselines.json engine/tests/fixtures/lattice/model/value.json
git commit -m "test(engine): update lattice fixture to baseline-referenced value schema"
```

### Task A6: Write the resolved volume into the workbook Inputs tab

**Files:**
- Modify: `engine/workbook.py:33-48`
- Test: `engine/tests/test_workbook.py`

- [ ] **Step 1: Write the failing test**

Add to `engine/tests/test_workbook.py` (import `load_inputs`, `build_results`, `write_workbook`, and `openpyxl` as the existing tests in that file do; mirror their fixture-loading style):

```python
def test_inputs_tab_writes_resolved_volume(tmp_path):
    import openpyxl
    from engine.model import load_inputs
    from engine.run import build_results
    from engine.workbook import write_workbook
    from pathlib import Path
    fixture = Path(__file__).parent / "fixtures" / "lattice" / "model"
    inputs = load_inputs(fixture)
    results = build_results(fixture)
    out = tmp_path / "wb.xlsx"
    write_workbook(inputs, results, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Inputs"]
    # Header row 1; OPP-001 is row 2; volume is column E (index 5).
    assert ws.cell(row=2, column=1).value == "OPP-001"
    assert ws.cell(row=2, column=5).value == 8000  # resolved PROC-01 volume * 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_workbook.py::test_inputs_tab_writes_resolved_volume -v`
Expected: FAIL with `AttributeError: 'ValueInput' object has no attribute 'volume'` (raised inside `write_workbook` via the old `getattr(v, "improvement_low"...)`/volume access)

- [ ] **Step 3: Resolve volume in the workbook writer**

In `engine/workbook.py`, add a module-level helper after `_q` (after `engine/workbook.py:15`):

```python
def _resolved_volume(v, baselines):
    """Volume the engine actually used: baseline.volume * volume_fraction. None -> blank."""
    if v is None:
        return None
    b = baselines.get(v.process_id)
    if b is None or b.volume is None:
        return None
    return b.volume * v.volume_fraction
```

Then in the Inputs-tab row loop (currently `engine/workbook.py:39-47`), replace the value-derived cells. The old line reads:

```python
            getattr(v, "improvement_low", None), getattr(v, "improvement_high", None),
            getattr(v, "volume", None), getattr(v, "rate", None),
```

Replace with:

```python
            getattr(v, "improvement_low", None), getattr(v, "improvement_high", None),
            _resolved_volume(v, inputs.baselines), getattr(v, "rate", None),
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_workbook.py -v`
Expected: PASS (new test + all existing workbook/equality tests — the Value-tab formula references column E, which now holds the resolved literal, so `test_workbook_equality` still matches `results.json`)

- [ ] **Step 5: Run the entire engine suite**

Run: `python -m pytest engine/ -v`
Expected: PASS (all tests green)

- [ ] **Step 6: Commit**

```bash
git add engine/workbook.py engine/tests/test_workbook.py
git commit -m "feat(engine): write resolved value volume into workbook Inputs tab"
```

### Task A7: Update Phase 4 and Phase 5 specs to the new schema + honest determinism claim

**Files:**
- Modify: `skills/discovering-processes/SKILL.md:44`
- Modify: `skills/identifying-opportunities/SKILL.md:44`

- [ ] **Step 1: Fix the Phase 4 baselines claim and schema**

In `skills/discovering-processes/SKILL.md`, replace the paragraph at line 44 (the "Recording baselines for the engine" body) with:

```markdown
Capture each baseline as raw, sourced inputs in the engagement's `model/baselines.json` — one object per process, keyed by `process_id`: `volume`, `cycle_time_median`, `cycle_time_p90`, `error_rate`, `fte`, and `source`. Use the same `process_id` values that `process-map.md` assigns, so downstream phases can reference a baseline by id. Do not multiply or annualize any figure in prose — record the raw measured value and its source only. The engine reads `model/baselines.json`, echoes every baseline into `model/results.json` under `baselines.<process_id>`, and resolves the value-hypothesis volume for each opportunity from it (Phase 5). `baselines.md` remains the human-readable, source-cited narrative; every numeric figure it states must equal its `results.json` source, so the figures are deterministic and auditable. A figure that appears only in `baselines.md` with no `baselines.json` source is a defect the deliverable-gate must catch.
```

- [ ] **Step 2: Fix the Phase 5 value schema**

In `skills/identifying-opportunities/SKILL.md`, replace the paragraph at line 44 (the "Value range (engine-computed)" body) with:

```markdown
The value hypothesis is written *before* the number (hypothesis-before-value discipline is unchanged). The numeric range itself is **not** multiplied in prose. Record `{"opp_id": "...", "improvement_low": x, "improvement_high": y, "process_id": "PROC-NN", "volume_fraction": f, "rate": r}` to the engagement's `model/value.json`. Do **not** restate a `volume`: the engine resolves it as `baselines.<process_id>.volume × volume_fraction`, so volume is never hand-copied. Set `volume_fraction` to `1.0` when the opportunity addresses the whole process; use a smaller fraction (with a one-line rationale in `opportunities/OPP-NNN.md`) when it addresses only a slice. `process_id` must name a process that exists in `model/baselines.json`, and `rate` must trace to a sourced figure. Then run `python -m engine.run <engagement-folder>/ --no-workbook` (see Phase-5 note below) and cite the resulting `results.json` `value.<OPP-ID>` range in `opportunities/OPP-NNN.md`.
```

(The `--no-workbook` flag is added in Group D, Task D1. If executing strictly in order, this paragraph references it ahead of its implementation — that is intentional; D1 lands in the same PR.)

- [ ] **Step 3: Verify no stale `volume`/literal references remain in these two files**

Run: `grep -n '"volume"' skills/discovering-processes/SKILL.md skills/identifying-opportunities/SKILL.md`
Expected: no output (the only structured `volume` is now inside `baselines.json`, described in prose, not as a `value.json` field)

- [ ] **Step 4: Commit**

```bash
git add skills/discovering-processes/SKILL.md skills/identifying-opportunities/SKILL.md
git commit -m "docs(phase4,phase5): baseline-referenced value schema; honest determinism claim"
```

---

## Group B — Phase 7 writes `initiatives.json`

**Fixes F2 (wave assignments decided in Phase 7 but only structured in Phase 9).**

`prioritizing-roadmap` is the phase that decides wave membership. It must emit `model/initiatives.json` as the structured output of that decision, for every opportunity it sequences (not just Wave 1 — the engine filters `wave == 1` itself).

### Task B1: Add the `initiatives.json` write to Phase 7

**Files:**
- Modify: `skills/prioritizing-roadmap/SKILL.md` (add a section after the "Roadmap Wave Definitions" table, around line 41; add a checklist item; add a workflow step)

- [ ] **Step 1: Add the recording section**

In `skills/prioritizing-roadmap/SKILL.md`, after the Roadmap Wave Definitions table (after line 41), insert:

```markdown
## Recording wave assignments for the engine

Wave assignment is a numeric input the engine consumes. As the final wave set is locked, write `model/initiatives.json` — one object per sequenced opportunity: `{"opp_id": "OPP-NNN", "name": "<initiative name>", "wave": N}` where `N` is `1` (Foundation), `2` (Scale), or `3` (Optimize). Include every sequenced opportunity, not only Wave 1 — the engine filters `wave == 1` for the business case itself. `roadmap.md` remains the human-readable narrative; `model/initiatives.json` is the engine's input and the single source of truth for wave membership. Phase 9 reads this file; it does not recreate it. Do not run the engine in Phase 7 — this phase only writes the file.
```

- [ ] **Step 2: Add the checklist item**

In the `## Phase checklist` of `skills/prioritizing-roadmap/SKILL.md`, add this item immediately after the "Map enablers and dependencies for every Wave 1 initiative" line (line 67):

```markdown
- [ ] Write `model/initiatives.json` — one `{opp_id, name, wave}` per sequenced opportunity (the structured output of wave assignment; engine source of truth for wave membership)
```

- [ ] **Step 3: Add the workflow step**

In the `## Workflow` of `skills/prioritizing-roadmap/SKILL.md`, between the enabler-mapping step (`5. Map enablers...`) and the structural-annotation step (`6. Structural annotation.`), insert:

```markdown
6. **Record wave assignments.** Write `model/initiatives.json` with one `{opp_id, name, wave}` object per sequenced opportunity. This is the structured output of the sequencing decision — do not defer it to Phase 9.
```

Renumber the subsequent workflow steps (the existing `6. Structural annotation` becomes `7.`, `7. Run opportunity-reviewer` becomes `8.`, `8. Save and chain forward` becomes `9.`).

- [ ] **Step 4: Verify**

Run: `grep -n "initiatives.json" skills/prioritizing-roadmap/SKILL.md`
Expected: at least 3 matches (section, checklist, workflow)

- [ ] **Step 5: Commit**

```bash
git add skills/prioritizing-roadmap/SKILL.md
git commit -m "docs(phase7): write initiatives.json as structured output of wave assignment"
```

---

## Group C — Single-write ownership; Phase 9 read-only

**Fixes F4 (double-writes of `value.json`/`costs.json`; Phase 9 re-transcription).** Decision: Phase 9 is read-only and never re-writes inputs.

Single-write ownership after this group:
| File | Sole writer |
|---|---|
| `baselines.json` | Phase 4 (discovering-processes) |
| `value.json` | Phase 5 (identifying-opportunities) |
| `scores.json` | Phase 6 (scoring-opportunities) |
| `initiatives.json` | Phase 7 (prioritizing-roadmap) |
| `costs.json` | Phase 8.5 (collecting-cost-actuals) |

### Task C1: Make Phase 9 read-only — verify inputs, run engine, never write inputs

**Files:**
- Modify: `skills/building-business-case/SKILL.md:22-33` (Deterministic math section)
- Modify: `skills/building-business-case/SKILL.md:130` (checklist item)
- Modify: `skills/building-business-case/SKILL.md:144-146` (workflow steps 4–5)

- [ ] **Step 1: Rewrite the Deterministic math section**

Replace `skills/building-business-case/SKILL.md:22-33` (from the `## Deterministic math` heading through the numbered list ending at line 33) with:

```markdown
## Deterministic math (engine-computed — no prose arithmetic)

Phase 9 performs **no arithmetic in prose** and **writes no input files**. Every numeric input was already structured by its owning phase: `value.json` (Phase 5), `costs.json` (Phase 8.5), `initiatives.json` (Phase 7), `baselines.json` (Phase 4), `scores.json` (Phase 6). Phase 9 reads them, runs the engine, and cites the results.

1. **Verify the inputs exist — do not create or re-write them.** Confirm `model/value.json`, `model/costs.json`, `model/initiatives.json`, and `model/baselines.json` are present in the engagement folder. If any is missing, halt and name the owning phase that must produce it (value → Phase 5; costs → Phase 8.5; initiatives → Phase 7; baselines → Phase 4). Do not transcribe figures from prose into a missing file — return to the owning phase. A figure recorded as `null` in an existing file is expected (it renders PENDING); a missing *file* is a gate failure.
2. **Run the engine:** `python -m engine.run <engagement-folder>/`. This reads the input files, writes `model/results.json`, and produces `financial-model.xlsx` (the CFO-facing workbook is a Phase 9 deliverable).
3. Populate every figure in `business-case.md` by citing `results.json` (per-initiative `costs.*.rom`, `value.*`, and `wave1_aggregate.investment` / `value` / `payback_years`). The ROM label `AACE Class 5 (±50%)` comes from `results.json` `rom_label`.
4. Any `results.json` value equal to `"PENDING"` renders as **PENDING** in the business case with a note on what input is missing — never a fabricated number.
```

- [ ] **Step 2: Fix the checklist item**

In `skills/building-business-case/SKILL.md`, replace the checklist item at line 130:

```markdown
- [ ] Write `model/{costs,value,initiatives}.json` and run `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`
```

with:

```markdown
- [ ] Verify `model/{value,costs,initiatives,baselines}.json` exist (do NOT write them — they are owned by Phases 5/8.5/7/4); halt naming the owning phase if any file is missing
- [ ] Run `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`
```

- [ ] **Step 3: Fix workflow step 4**

In `skills/building-business-case/SKILL.md`, replace workflow step 4 (line 145) — the sentence beginning "Write the structured numeric inputs to `model/costs.json`..." — with:

```markdown
4. Verify `model/value.json`, `model/costs.json`, `model/initiatives.json`, and `model/baselines.json` exist (owned by Phases 5/8.5/7/4 respectively) — do NOT write or re-write them. If any is missing, halt and name the owning phase. Then run `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`. Then, for each Wave 1 initiative from `roadmap.md`, dispatch one `business-case-analyst` subagent. Pass only that initiative's data; the agent cites its figures from `model/results.json`.
```

- [ ] **Step 4: Verify no write instruction remains in Phase 9**

Run: `grep -nE "[Ww]rite (the )?(structured )?(numeric )?(inputs )?(to )?(model/)?(costs|value|initiatives)\.json" skills/building-business-case/SKILL.md`
Expected: no output (Phase 9 no longer instructs writing any input file)

- [ ] **Step 5: Commit**

```bash
git add skills/building-business-case/SKILL.md
git commit -m "docs(phase9): read-only inputs; verify-and-run, never re-transcribe"
```

### Task C2: Confirm Phase 8.5 is the sole `costs.json` writer; add the ownership table to the methodology keystone

**Files:**
- Modify: `skills/using-methodology/SKILL.md` (after line 69, the source-of-truth paragraph)
- Read-only check: `skills/collecting-cost-actuals/SKILL.md:102`

- [ ] **Step 1: Confirm Phase 8.5 still owns `costs.json`**

Run: `grep -n "costs.json" skills/collecting-cost-actuals/SKILL.md`
Expected: line 102 present — Phase 8.5 records `costs.json`. No change needed; this is the confirmation that the sole-writer rule already holds for costs.

- [ ] **Step 2: Add the single-write ownership table to the keystone**

In `skills/using-methodology/SKILL.md`, immediately after line 69 (the paragraph ending "...renders as **PENDING**, never a fabricated number."), insert:

```markdown
**Single-write ownership.** Each `model/*.json` input is written exactly once, by the phase that owns the decision behind it. No later phase re-writes an input file; later phases read it. This is what makes the engine's output reproducible and the deliverable-gate's markdown ↔ `results.json` check meaningful.

| Input file | Sole writing phase |
|---|---|
| `model/baselines.json` | Phase 4 — discovering-processes |
| `model/value.json` | Phase 5 — identifying-opportunities |
| `model/scores.json` | Phase 6 — scoring-opportunities |
| `model/initiatives.json` | Phase 7 — prioritizing-roadmap |
| `model/costs.json` | Phase 8.5 — collecting-cost-actuals |

`model/results.json` and `financial-model.xlsx` are derived outputs, regenerated by `python -m engine.run` — never hand-edited.
```

- [ ] **Step 3: Verify**

Run: `grep -n "Single-write ownership" skills/using-methodology/SKILL.md`
Expected: 1 match

- [ ] **Step 4: Commit**

```bash
git add skills/using-methodology/SKILL.md
git commit -m "docs(methodology): codify single-write ownership of model/*.json inputs"
```

---

## Group D — Phase 5 value-only engine run (`--no-workbook`)

**Fixes F3 (Phase 5 runs the full engine and emits a premature `financial-model.xlsx`).** Same defect class as the Phase 6 fix. Add a flag so a phase can compute `results.json` without the CFO workbook. Depends on Group A (value schema).

### Task D1: Add `--no-workbook` to the engine entry point

**Files:**
- Modify: `engine/run.py:71-85` (the `main` function)
- Test: `engine/tests/test_run.py`

- [ ] **Step 1: Write the failing test**

Add to `engine/tests/test_run.py`:

```python
def test_no_workbook_flag_skips_xlsx_but_writes_results(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    rc = main([str(eng), "--no-workbook"])
    assert rc == 0
    assert (eng / "model" / "results.json").exists()
    assert not (eng / "financial-model.xlsx").exists()


def test_default_run_still_writes_workbook(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    main([str(eng)])
    assert (eng / "financial-model.xlsx").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_run.py::test_no_workbook_flag_skips_xlsx_but_writes_results -v`
Expected: FAIL — the `--no-workbook` arg is treated as the engagement path, raising an error or writing the workbook anyway

- [ ] **Step 3: Implement the flag**

Replace the `main` function in `engine/run.py` (currently `engine/run.py:71-85`) with:

```python
def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    flags = {a for a in argv if a.startswith("--")}
    positional = [a for a in argv if not a.startswith("--")]
    if not positional:
        print("usage: python -m engine.run <engagement-folder>/ [--no-workbook]", file=sys.stderr)
        return 2
    engagement = Path(positional[0])
    model_dir = engagement / "model"
    results = build_results(model_dir)
    (model_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if "--no-workbook" not in flags:
        write_workbook(load_inputs(model_dir), results, engagement / "financial-model.xlsx")
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_run.py -v`
Expected: PASS (both new tests + existing run tests)

- [ ] **Step 5: Commit**

```bash
git add engine/run.py engine/tests/test_run.py
git commit -m "feat(engine): add --no-workbook flag for intermediate (Phase 5) runs"
```

### Task D2: Add a Phase-5 note explaining the workbook boundary

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md` (add a short note after the value-range paragraph edited in Task A7)

- [ ] **Step 1: Add the note**

In `skills/identifying-opportunities/SKILL.md`, immediately after the "Value range (engine-computed)" paragraph (the one edited in Task A7, Step 2), insert:

```markdown
**Phase-5 note — `--no-workbook`.** Phase 5 runs the engine only to compute the value ranges into `results.json`; it must **not** emit the CFO workbook. Always pass `--no-workbook`: `python -m engine.run <engagement-folder>/ --no-workbook`. `financial-model.xlsx` is a Phase 9 deliverable produced once costs, scores, and wave assignments exist — running the full engine here would write a workbook full of PENDING cost and score cells.
```

- [ ] **Step 2: Verify**

Run: `grep -n -- "--no-workbook" skills/identifying-opportunities/SKILL.md`
Expected: at least 2 matches (the value-range paragraph from A7 + this note)

- [ ] **Step 3: Commit**

```bash
git add skills/identifying-opportunities/SKILL.md
git commit -m "docs(phase5): run engine with --no-workbook; no premature financial-model.xlsx"
```

---

## Group E — Cost percentages: inputs, not "engine parameters"

**Fixes F6 (contract ambiguity).** The fixtures show `change_mgmt_pct` and `contingency_pct` varying per OPP (0.25 vs 0.20), so they are per-initiative inputs in `costs.json`, sourced from methodology default ranges — not engine constants. Fix the wording. Engine and `costs.json` schema are unchanged. Docs-only; independent of all other groups.

### Task E1: Correct the "engine parameters" wording in the analyst spec

**Files:**
- Modify: `agents/business-case-analyst.md:30`

- [ ] **Step 1: Rewrite the sentence**

In `agents/business-case-analyst.md`, replace line 30 (the sentence beginning "The methodology defaults the engine applies (change management 20–30%...") with:

```markdown
Change management (methodology default 20–30% of confirmed implementation labor) and contingency (default 15–20% of subtotal) are **per-initiative inputs** recorded in `model/costs.json` as `change_mgmt_pct` and `contingency_pct` by Phase 8.5 — the analyst neither multiplies them nor sets them. They default to the methodology ranges but may be tuned per initiative in `costs.json`; the engine applies whatever value the file carries. All other cost categories — implementation labor hours, labor rates, technology and licensing costs, integration costs — also originate in `cost-actuals.md` / `model/costs.json`. If any is absent or `null`, the engine renders the figure as PENDING.
```

- [ ] **Step 2: Verify the misleading phrase is gone**

Run: `grep -n "engine parameters" agents/business-case-analyst.md`
Expected: no output

- [ ] **Step 3: Commit**

```bash
git add agents/business-case-analyst.md
git commit -m "docs(phase9): cost percentages are per-initiative inputs, not engine constants"
```

---

## Final verification (run after all groups land)

- [ ] **Full engine suite green**

Run: `python -m pytest engine/ -v`
Expected: PASS — all tests, including `test_build_results_matches_golden` (golden value/aggregate/payback unchanged) and every new test added in Groups A and D.

- [ ] **No phase except the owner writes its input file**

Run:
```bash
grep -rnE "write[_ ].*value\.json|value\.json.*write" skills/ | grep -iv "identifying-opportunities"
grep -rnE "costs\.json" skills/building-business-case/SKILL.md
grep -rn "initiatives.json" skills/building-business-case/SKILL.md
```
Expected: the first two return no "write" instruction outside the owning phase; the third shows Phase 9 only *reads/verifies* `initiatives.json` (no write verb).

- [ ] **Determinism doctrine intact**

Run: `grep -n "no arithmetic in prose" skills/using-methodology/SKILL.md`
Expected: 1 match (the keystone rule is still present and now backed by the ownership table).

- [ ] **Sample engagement dry-run sanity (optional but recommended)**

If a sample engagement folder with `model/` inputs exists, run `python -m engine.run <that-folder>/` and confirm `results.json` populates `value`, `scores`, `costs`, `baselines`, and `wave1_aggregate` with no unexpected PENDING where inputs are present.

---

## Self-Review

**Spec coverage:**
- F1 (baselines.json dead / false claim) → Group A (A1–A5 wire it in; A7 fixes the claim). ✅
- F5 (volume duplicated/drift) → Group A (A2 removes literal volume; A4 resolves from baseline). ✅
- F2 (initiatives.json written in P9 not P7) → Group B. ✅
- F4 (double-writes; P9 re-transcription) → Group C (C1 read-only P9; C2 ownership table). ✅
- F3 (P5 premature workbook) → Group D. ✅
- F6 (constants vs inputs) → Group E. ✅
- F7 (P1–P3 correctly have no JSON) → no task needed; explicitly out of scope. ✅

**Type consistency:** `BaselineInput` fields (A1) match the loader (A3), the run.py echo (A4), the workbook helper (A6), and the fixture (A5). `ValueInput` new fields `process_id`/`volume_fraction` (A2) match run.py resolution (A4), workbook `_resolved_volume` (A6), fixture (A5), and the Phase-5 spec (A7). `--no-workbook` flag string is identical across run.py (D1), the test (D1), and both spec edits (A7, D2).

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N". Every code step shows complete code; every doc step shows exact replacement text; every verify step shows the exact command and expected output.
