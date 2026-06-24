# Deterministic Math Engine + Auditable Workbook — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move every calculation in the methodology off the LLM into a deterministic, unit-tested Python engine that emits a canonical `results.json` plus an auditable Excel workbook with live cell formulas; markdown cites computed results and never computes.

**Architecture:** A small pure-Python package `engine/` with four single-purpose units — `model.py` (schemas + validation, no I/O), `compute.py` (pure formula functions, the single source of formula truth), `workbook.py` (`openpyxl` writer; inputs as literal cells, everything downstream as `=formulas`), and `run.py` (the only I/O boundary: read `model/*.json` → validate → compute → write `results.json` + `financial-model.xlsx`). A pytest golden-number suite proves the formulas, including a Lattice-sample integration fixture. Then phases P9→P8.5→P6→P5→P4 are wired one at a time to write `model/<phase>.json` and cite `results.json`, the deliverable-gate gains a determinism check, and packaging (INSTALL, keystone rule, version bump) lands last.

**Tech Stack:** Python 3.11+, `openpyxl` (workbook writer, runtime dep), `formulas` (headless formula evaluator, test/CI dep only), `pytest`. Methodology skill/agent edits are Markdown.

**Spec of record:** [`docs/superpowers/specs/2026-06-05-deterministic-math-engine-design.md`](../specs/2026-06-05-deterministic-math-engine-design.md). Issue: #9.

---

## Conventions used throughout this plan

- All paths are relative to repo root `/Users/daveraffaele/Desktop/plugins/ai-process-assessment`.
- Run tests from repo root. The engine suite lives in `engine/tests/`; the repo methodology suite lives in `tests/`. After Task 23 both are on `testpaths`.
- Money values are rounded to 2 decimals via `round(x, 2)`; ratios (scores, payback years) to 2 decimals. Float asserts use `pytest.approx`.
- `Range` is `(low, high)`. A missing input yields the sentinel string `"PENDING"` in place of a `Range`/`float` — never a fabricated number.
- Commit after every task. Branch: `feature/deterministic-math-engine` (already created).

---

# PART 1 — Core engine + golden tests (spec §10 step 1)

Build the pure formula layer and prove it against known numbers. No methodology wiring yet.

### Task 1: Package skeleton + Range/PENDING + dependency declarations

**Files:**
- Create: `engine/__init__.py`
- Create: `engine/model.py`
- Create: `engine/tests/__init__.py`
- Create: `engine/tests/test_model.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependencies**

Edit `requirements.txt` to read exactly:

```
pytest>=8.0
pyyaml>=6.0
openpyxl>=3.1
formulas>=1.2
```

(`openpyxl` is a runtime dep for the workbook writer; `formulas` is used only by the workbook-equality test but is simplest to pin here.)

- [ ] **Step 2: Write the failing test**

Create `engine/tests/__init__.py` (empty). Create `engine/tests/test_model.py`:

```python
from engine.model import PENDING, Range


def test_range_holds_low_and_high():
    r = Range(low=10.0, high=20.0)
    assert r.low == 10.0
    assert r.high == 20.0


def test_range_is_frozen():
    import dataclasses
    import pytest
    r = Range(1.0, 2.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.low = 5.0  # type: ignore[misc]


def test_pending_is_the_sentinel_string():
    assert PENDING == "PENDING"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine'`.

- [ ] **Step 4: Write minimal implementation**

Create `engine/__init__.py`:

```python
"""Deterministic math engine for the AI process-assessment methodology.

The model performs no arithmetic in prose. Every number is either a sourced
input recorded in model/*.json or a value computed here and read from results.json.
"""
```

Create `engine/model.py`:

```python
"""Input + result schemas and the shared Range/PENDING types. No I/O lives here."""
from __future__ import annotations

from dataclasses import dataclass

# Sentinel for a result that cannot be computed because an input is missing.
# Never replaced by a fabricated number — surfaced as-is in results.json and the workbook.
PENDING = "PENDING"


@dataclass(frozen=True)
class Range:
    low: float
    high: float
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_model.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt engine/__init__.py engine/model.py engine/tests/__init__.py engine/tests/test_model.py
git commit -m "feat(engine): package skeleton, Range type, PENDING sentinel, deps"
```

---

### Task 2: `value_range` — value-hypothesis ranges (P5)

**Files:**
- Create: `engine/compute.py`
- Create: `engine/tests/test_compute.py`

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_compute.py`:

```python
import pytest

from engine.compute import value_range
from engine.model import Range


def test_value_range_multiplies_improvement_by_volume_by_rate():
    # low  = 0.2 * 1000 * 50 = 10_000 ; high = 0.4 * 1000 * 50 = 20_000
    assert value_range(0.2, 0.4, 1000, 50) == Range(10_000.0, 20_000.0)


def test_value_range_rounds_money_to_two_decimals():
    r = value_range(0.333, 0.667, 100, 3)
    assert r.low == pytest.approx(99.9)    # 0.333*100*3 = 99.9
    assert r.high == pytest.approx(200.1)  # 0.667*100*3 = 200.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py::test_value_range_multiplies_improvement_by_volume_by_rate -v`
Expected: FAIL — `ImportError: cannot import name 'value_range'`.

- [ ] **Step 3: Write minimal implementation**

Create `engine/compute.py`:

```python
"""Pure formula functions — the single source of formula truth. No I/O, no LLM.

Every methodology calculation site routes through one of these functions. A missing
required input returns PENDING (never a fabricated number).
"""
from __future__ import annotations

from engine.model import PENDING, Range

_MONEY_DP = 2


def _money(x: float) -> float:
    return round(x, _MONEY_DP)


def value_range(improvement_low, improvement_high, volume, rate):
    """Value-hypothesis range: improvement-fraction × volume × rate (P5).

    Returns PENDING if any input is None.
    """
    if None in (improvement_low, improvement_high, volume, rate):
        return PENDING
    return Range(
        _money(improvement_low * volume * rate),
        _money(improvement_high * volume * rate),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): value_range — P5 value-hypothesis ranges"
```

---

### Task 3: `score_composite` — 6-dimension mean (P6)

**Files:**
- Modify: `engine/compute.py`
- Modify: `engine/tests/test_compute.py`

- [ ] **Step 1: Write the failing test**

Append to `engine/tests/test_compute.py`:

```python
from engine.compute import score_composite


def test_score_composite_is_mean_of_six_dimensions():
    assert score_composite([3, 4, 5, 2, 4, 3]) == 3.5  # 21/6 = 3.5


def test_score_composite_rounds_to_two_decimals():
    assert score_composite([4, 4, 4, 4, 4, 5]) == 4.17  # 25/6 = 4.1666...


def test_score_composite_requires_exactly_six_dimensions():
    with pytest.raises(ValueError):
        score_composite([3, 4, 5])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py -k score_composite -v`
Expected: FAIL — `ImportError: cannot import name 'score_composite'`.

- [ ] **Step 3: Write minimal implementation**

Append to `engine/compute.py`:

```python
def score_composite(dimensions):
    """Composite score = mean of exactly six dimensions, rounded to 2 dp (P6)."""
    if dimensions is None or any(d is None for d in dimensions):
        return PENDING
    if len(dimensions) != 6:
        raise ValueError(f"expected 6 dimensions, got {len(dimensions)}")
    return round(sum(dimensions) / 6, 2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -k score_composite -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): score_composite — P6 six-dimension mean"
```

---

### Task 4: `cost_structure` — cost roll-up (P8.5 / P9)

**Files:**
- Modify: `engine/model.py`
- Modify: `engine/compute.py`
- Modify: `engine/tests/test_compute.py`

**Note on signature:** the spec §6.3 gives an illustrative `cost_structure(hours, rate, change_mgmt_pct, contingency_pct)`. This plan implements the full business-case cost-category set (spec §7 / building-business-case cost table): labor + technology + integration form the base, change-management is a % of labor, contingency is a % of the subtotal. This is faithful to acceptance criterion "computes ... cost structures" and to the deliverable's cost block.

- [ ] **Step 1: Add the CostBlock result type**

Append to `engine/model.py`:

```python
@dataclass(frozen=True)
class CostBlock:
    labor: float
    tech_cost: float
    integration_cost: float
    change_mgmt: float
    subtotal: float
    contingency: float
    total: float
```

- [ ] **Step 2: Write the failing test**

Append to `engine/tests/test_compute.py`:

```python
from engine.compute import cost_structure
from engine.model import CostBlock


def test_cost_structure_rolls_up_all_categories():
    # labor = 800*200 = 160_000 ; cm = 160_000*0.25 = 40_000
    # subtotal = 160_000 + 40_000(tech) + 30_000(integ) + 40_000(cm) = 270_000
    # contingency = 270_000*0.15 = 40_500 ; total = 310_500
    cb = cost_structure(
        labor_hours=800, labor_rate=200,
        tech_cost=40_000, integration_cost=30_000,
        change_mgmt_pct=0.25, contingency_pct=0.15,
    )
    assert cb == CostBlock(
        labor=160_000.0, tech_cost=40_000.0, integration_cost=30_000.0,
        change_mgmt=40_000.0, subtotal=270_000.0,
        contingency=40_500.0, total=310_500.0,
    )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py -k cost_structure -v`
Expected: FAIL — `ImportError: cannot import name 'cost_structure'`.

- [ ] **Step 4: Write minimal implementation**

Append to `engine/compute.py` (add `CostBlock` to the model import line at the top: `from engine.model import CostBlock, PENDING, Range`):

```python
def cost_structure(labor_hours, labor_rate, tech_cost, integration_cost,
                   change_mgmt_pct, contingency_pct):
    """Cost roll-up for an initiative (P8.5/P9).

    labor = hours*rate ; change_mgmt = labor*pct ;
    subtotal = labor + tech + integration + change_mgmt ;
    contingency = subtotal*pct ; total = subtotal + contingency.
    Returns PENDING if any input is None.
    """
    args = (labor_hours, labor_rate, tech_cost, integration_cost,
            change_mgmt_pct, contingency_pct)
    if any(a is None for a in args):
        return PENDING
    labor = labor_hours * labor_rate
    change_mgmt = labor * change_mgmt_pct
    subtotal = labor + tech_cost + integration_cost + change_mgmt
    contingency = subtotal * contingency_pct
    total = subtotal + contingency
    return CostBlock(
        labor=_money(labor),
        tech_cost=_money(tech_cost),
        integration_cost=_money(integration_cost),
        change_mgmt=_money(change_mgmt),
        subtotal=_money(subtotal),
        contingency=_money(contingency),
        total=_money(total),
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -k cost_structure -v`
Expected: PASS (1 passed).

- [ ] **Step 6: Commit**

```bash
git add engine/model.py engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): cost_structure — full business-case cost roll-up"
```

---

### Task 5: `initiative_rom` — AACE Class 5 ±50% range

**Files:**
- Modify: `engine/compute.py`
- Modify: `engine/tests/test_compute.py`

- [ ] **Step 1: Write the failing test**

Append to `engine/tests/test_compute.py`:

```python
from engine.compute import AACE_CLASS5_LABEL, initiative_rom


def test_initiative_rom_is_plus_minus_fifty_percent_of_total():
    cb = cost_structure(800, 200, 40_000, 30_000, 0.25, 0.15)  # total 310_500
    rom = initiative_rom(cb)
    assert rom == Range(155_250.0, 465_750.0)


def test_initiative_rom_passes_pending_through():
    assert initiative_rom(PENDING) == PENDING


def test_aace_label_text():
    assert AACE_CLASS5_LABEL == "ROM estimate, AACE Class 5 (±50%)"
```

Add this import to the top of `engine/tests/test_compute.py` (it imports only `Range` so far): `from engine.model import PENDING, Range`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py -k initiative_rom -v`
Expected: FAIL — `ImportError: cannot import name 'initiative_rom'`.

- [ ] **Step 3: Write minimal implementation**

Append to `engine/compute.py`:

```python
AACE_CLASS5_LABEL = "ROM estimate, AACE Class 5 (±50%)"


def initiative_rom(cost_block):
    """ROM range for an initiative: total ±50% (AACE Class 5).

    The label travels with the figure in results.json (see run.py).
    Returns PENDING if the cost block is PENDING.
    """
    if cost_block == PENDING:
        return PENDING
    return Range(_money(cost_block.total * 0.5), _money(cost_block.total * 1.5))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -k initiative_rom -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): initiative_rom — AACE Class 5 +/-50% range"
```

---

### Task 6: `wave1_aggregate` — sum of ROM ranges

**Files:**
- Modify: `engine/compute.py`
- Modify: `engine/tests/test_compute.py`

- [ ] **Step 1: Write the failing test**

Append to `engine/tests/test_compute.py`:

```python
from engine.compute import wave1_aggregate


def test_wave1_aggregate_sums_lows_and_highs():
    agg = wave1_aggregate([Range(100, 300), Range(200, 600)])
    assert agg == Range(300.0, 900.0)


def test_wave1_aggregate_skips_pending_members_but_flags_via_empty():
    # PENDING members are excluded from the sum; an all-PENDING list returns PENDING.
    assert wave1_aggregate([PENDING, PENDING]) == PENDING
    assert wave1_aggregate([Range(100, 300), PENDING]) == Range(100.0, 300.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py -k wave1_aggregate -v`
Expected: FAIL — `ImportError: cannot import name 'wave1_aggregate'`.

- [ ] **Step 3: Write minimal implementation**

Append to `engine/compute.py`:

```python
def wave1_aggregate(rom_ranges):
    """Aggregate Wave-1 range = sum of member ranges. PENDING members are excluded;
    an all-PENDING (or empty) list returns PENDING."""
    present = [r for r in rom_ranges if r != PENDING]
    if not present:
        return PENDING
    return Range(
        _money(sum(r.low for r in present)),
        _money(sum(r.high for r in present)),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -k wave1_aggregate -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): wave1_aggregate — sum of Wave-1 ROM ranges"
```

---

### Task 7: `payback` — investment ÷ annual value (in years)

**Files:**
- Modify: `engine/compute.py`
- Modify: `engine/tests/test_compute.py`

**Convention:** payback is reported as a range of years. Best case = `investment.low / annual_value.high`; worst case = `investment.high / annual_value.low`. Rounded to 2 dp.

- [ ] **Step 1: Write the failing test**

Append to `engine/tests/test_compute.py`:

```python
from engine.compute import payback


def test_payback_years_best_and_worst_case():
    pb = payback(Range(10_000, 30_000), Range(20_000, 40_000))
    # best  = 10_000/40_000 = 0.25 ; worst = 30_000/20_000 = 1.5
    assert pb == Range(0.25, 1.5)


def test_payback_pending_when_either_input_pending():
    assert payback(PENDING, Range(1, 2)) == PENDING
    assert payback(Range(1, 2), PENDING) == PENDING


def test_payback_pending_on_zero_value():
    # No value => payback undefined => PENDING, never division-by-zero.
    assert payback(Range(10_000, 30_000), Range(0, 0)) == PENDING
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_compute.py -k payback -v`
Expected: FAIL — `ImportError: cannot import name 'payback'`.

- [ ] **Step 3: Write minimal implementation**

Append to `engine/compute.py`:

```python
def payback(investment, annual_value):
    """Payback period as a range of years.

    best  = investment.low  / annual_value.high
    worst = investment.high / annual_value.low
    Returns PENDING if either input is PENDING or annual value is non-positive.
    """
    if investment == PENDING or annual_value == PENDING:
        return PENDING
    if annual_value.low <= 0 or annual_value.high <= 0:
        return PENDING
    return Range(
        round(investment.low / annual_value.high, 2),
        round(investment.high / annual_value.low, 2),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_compute.py -k payback -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/compute.py engine/tests/test_compute.py
git commit -m "feat(engine): payback — investment/value payback range in years"
```

---

### Task 8: Input schemas, validation, and JSON loaders

**Files:**
- Modify: `engine/model.py`
- Create: `engine/tests/test_loaders.py`

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_loaders.py`:

```python
import json

import pytest

from engine.model import (
    CostInput, ScoreInput, ValueInput, load_inputs,
)


def test_value_input_from_dict():
    vi = ValueInput.from_dict({
        "opp_id": "OPP-001", "improvement_low": 0.5,
        "improvement_high": 0.7, "volume": 8000, "rate": 100,
    })
    assert vi.opp_id == "OPP-001"
    assert vi.improvement_high == 0.7


def test_score_input_rejects_wrong_dimension_count():
    with pytest.raises(ValueError):
        ScoreInput.from_dict({"opp_id": "OPP-001", "dimensions": [1, 2, 3]})


def test_cost_input_allows_missing_numeric_as_none_for_pending():
    ci = CostInput.from_dict({"opp_id": "OPP-001", "labor_hours": None,
                              "labor_rate": 200, "tech_cost": 0,
                              "integration_cost": 0, "change_mgmt_pct": 0.25,
                              "contingency_pct": 0.15})
    assert ci.labor_hours is None  # surfaces as PENDING downstream


def test_load_inputs_reads_model_folder(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "value.json").write_text(json.dumps([{
        "opp_id": "OPP-001", "improvement_low": 0.2, "improvement_high": 0.4,
        "volume": 1000, "rate": 50}]))
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
    assert inp.value["OPP-001"].volume == 1000
    assert inp.scores["OPP-001"].dimensions == [3, 4, 5, 2, 4, 3]
    assert inp.costs["OPP-001"].tech_cost == 40000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_loaders.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_inputs'`.

- [ ] **Step 3: Write minimal implementation**

Append to `engine/model.py`:

```python
from pathlib import Path  # add to existing imports at top of file


@dataclass(frozen=True)
class ValueInput:
    opp_id: str
    improvement_low: float
    improvement_high: float
    volume: float
    rate: float

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("improvement_low"), d.get("improvement_high"),
                   d.get("volume"), d.get("rate"))


@dataclass(frozen=True)
class ScoreInput:
    opp_id: str
    dimensions: list

    @classmethod
    def from_dict(cls, d):
        dims = d.get("dimensions") or []
        if len(dims) != 6:
            raise ValueError(f"{d.get('opp_id')}: expected 6 dimensions, got {len(dims)}")
        return cls(d["opp_id"], list(dims))


@dataclass(frozen=True)
class CostInput:
    opp_id: str
    labor_hours: float | None
    labor_rate: float | None
    tech_cost: float | None
    integration_cost: float | None
    change_mgmt_pct: float | None
    contingency_pct: float | None

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("labor_hours"), d.get("labor_rate"),
                   d.get("tech_cost"), d.get("integration_cost"),
                   d.get("change_mgmt_pct"), d.get("contingency_pct"))


@dataclass(frozen=True)
class Initiative:
    opp_id: str
    name: str
    wave: int

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("name", d["opp_id"]), int(d.get("wave", 1)))


@dataclass(frozen=True)
class Inputs:
    initiatives: list
    value: dict
    scores: dict
    costs: dict


def _read_json(path: Path):
    import json
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs(model_dir) -> "Inputs":
    """Read model/*.json into validated dataclasses. Missing files load as empty."""
    model_dir = Path(model_dir)
    initiatives = [Initiative.from_dict(d) for d in _read_json(model_dir / "initiatives.json")]
    value = {d["opp_id"]: ValueInput.from_dict(d) for d in _read_json(model_dir / "value.json")}
    scores = {d["opp_id"]: ScoreInput.from_dict(d) for d in _read_json(model_dir / "scores.json")}
    costs = {d["opp_id"]: CostInput.from_dict(d) for d in _read_json(model_dir / "costs.json")}
    return Inputs(initiatives=initiatives, value=value, scores=scores, costs=costs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_loaders.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/model.py engine/tests/test_loaders.py
git commit -m "feat(engine): input schemas, validation, model/*.json loaders"
```

---

### Task 9: PENDING-propagation guard test (cross-cutting)

**Files:**
- Create: `engine/tests/test_pending.py`

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_pending.py`:

```python
"""Guard: a missing input never fabricates a number — it surfaces PENDING end-to-end."""
from engine.compute import (
    cost_structure, initiative_rom, payback, score_composite,
    value_range, wave1_aggregate,
)
from engine.model import PENDING, Range


def test_value_range_pending_on_missing_rate():
    assert value_range(0.2, 0.4, 1000, None) == PENDING


def test_score_composite_pending_on_missing_dimension():
    assert score_composite([3, 4, 5, None, 4, 3]) == PENDING


def test_cost_structure_pending_chains_to_rom():
    cb = cost_structure(None, 200, 0, 0, 0.25, 0.15)
    assert cb == PENDING
    assert initiative_rom(cb) == PENDING


def test_aggregate_and_payback_survive_partial_pending():
    agg = wave1_aggregate([Range(100, 300), PENDING])
    assert agg == Range(100.0, 300.0)
    assert payback(agg, PENDING) == PENDING
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_pending.py -v`
Expected: PASS (4 passed) — the PENDING behavior was built into each function in Tasks 2–7, so this guard should pass immediately. If any fails, fix the named function before continuing.

- [ ] **Step 3: Commit**

```bash
git add engine/tests/test_pending.py
git commit -m "test(engine): cross-cutting PENDING-propagation guard"
```

---

### Task 10: Lattice golden integration fixture + test (spec §8, §10 step 1)

**Files:**
- Create: `engine/tests/fixtures/lattice/model/value.json`
- Create: `engine/tests/fixtures/lattice/model/scores.json`
- Create: `engine/tests/fixtures/lattice/model/costs.json`
- Create: `engine/tests/fixtures/lattice/model/initiatives.json`
- Create: `engine/tests/test_lattice_golden.py`

**Fixture provenance:** two Wave-1 initiatives anchored to the Lattice PSO sample (`samples/pso-delivery-team/intake/interview-notes.md`) — A = Status Reporting Assistant (PROC-03, the strongest chain candidate; ~720 reports/mo, 5.5 FTE, 60–70% gather/reformat), B = Time-Entry Anomaly Flagging (PROC-04). Numbers are rounded to clean values so the golden arithmetic is exactly verifiable; they are test data, not the engagement's final figures.

Hand-computed expected results:

```
Initiative A (OPP-001):
  value  = 0.5..0.7 × 8000 × 100  -> Range(400_000, 560_000)
  score  = mean([4,4,5,3,4,4]) = 24/6 = 4.0
  cost   = labor 800×200=160_000; tech 40_000; integ 30_000;
           cm 160_000×0.25=40_000; subtotal 270_000;
           cont 270_000×0.15=40_500; total 310_500
  rom    = 310_500 ±50% -> Range(155_250, 465_750)

Initiative B (OPP-002):
  value  = 0.2..0.4 × 5000 × 100  -> Range(100_000, 200_000)
  score  = mean([3,3,4,3,3,2]) = 18/6 = 3.0
  cost   = labor 400×200=80_000; tech 20_000; integ 10_000;
           cm 80_000×0.20=16_000; subtotal 126_000;
           cont 126_000×0.15=18_900; total 144_900
  rom    = 144_900 ±50% -> Range(72_450, 217_350)

Wave-1 aggregate:
  investment = (155_250+72_450, 465_750+217_350) = Range(227_700, 683_100)
  value      = (400_000+100_000, 560_000+200_000) = Range(500_000, 760_000)
  payback(years) = (227_700/760_000, 683_100/500_000)
               = Range(0.30, 1.37)   # rounded 2dp: 0.299605->0.30, 1.3662->1.37
```

- [ ] **Step 1: Create the fixture model files**

`engine/tests/fixtures/lattice/model/initiatives.json`:

```json
[
  {"opp_id": "OPP-001", "name": "Status Reporting Assistant", "wave": 1},
  {"opp_id": "OPP-002", "name": "Time-Entry Anomaly Flagging", "wave": 1}
]
```

`engine/tests/fixtures/lattice/model/value.json`:

```json
[
  {"opp_id": "OPP-001", "improvement_low": 0.5, "improvement_high": 0.7, "volume": 8000, "rate": 100},
  {"opp_id": "OPP-002", "improvement_low": 0.2, "improvement_high": 0.4, "volume": 5000, "rate": 100}
]
```

`engine/tests/fixtures/lattice/model/scores.json`:

```json
[
  {"opp_id": "OPP-001", "dimensions": [4, 4, 5, 3, 4, 4]},
  {"opp_id": "OPP-002", "dimensions": [3, 3, 4, 3, 3, 2]}
]
```

`engine/tests/fixtures/lattice/model/costs.json`:

```json
[
  {"opp_id": "OPP-001", "labor_hours": 800, "labor_rate": 200, "tech_cost": 40000, "integration_cost": 30000, "change_mgmt_pct": 0.25, "contingency_pct": 0.15},
  {"opp_id": "OPP-002", "labor_hours": 400, "labor_rate": 200, "tech_cost": 20000, "integration_cost": 10000, "change_mgmt_pct": 0.20, "contingency_pct": 0.15}
]
```

- [ ] **Step 2: Write the failing test**

Create `engine/tests/test_lattice_golden.py`:

```python
from pathlib import Path

from engine.compute import (
    cost_structure, initiative_rom, payback, score_composite,
    value_range, wave1_aggregate,
)
from engine.model import Range, load_inputs

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"


def test_lattice_end_to_end_golden_numbers():
    inp = load_inputs(FIXTURE)

    v1 = value_range(**_value_args(inp, "OPP-001"))
    v2 = value_range(**_value_args(inp, "OPP-002"))
    assert v1 == Range(400_000.0, 560_000.0)
    assert v2 == Range(100_000.0, 200_000.0)

    assert score_composite(inp.scores["OPP-001"].dimensions) == 4.0
    assert score_composite(inp.scores["OPP-002"].dimensions) == 3.0

    cb1 = cost_structure(**_cost_args(inp, "OPP-001"))
    cb2 = cost_structure(**_cost_args(inp, "OPP-002"))
    assert cb1.total == 310_500.0
    assert cb2.total == 144_900.0

    rom1 = initiative_rom(cb1)
    rom2 = initiative_rom(cb2)
    assert rom1 == Range(155_250.0, 465_750.0)
    assert rom2 == Range(72_450.0, 217_350.0)

    investment = wave1_aggregate([rom1, rom2])
    annual_value = wave1_aggregate([v1, v2])
    assert investment == Range(227_700.0, 683_100.0)
    assert annual_value == Range(500_000.0, 760_000.0)

    assert payback(investment, annual_value) == Range(0.30, 1.37)


def _value_args(inp, opp):
    v = inp.value[opp]
    return dict(improvement_low=v.improvement_low, improvement_high=v.improvement_high,
                volume=v.volume, rate=v.rate)


def _cost_args(inp, opp):
    c = inp.costs[opp]
    return dict(labor_hours=c.labor_hours, labor_rate=c.labor_rate,
                tech_cost=c.tech_cost, integration_cost=c.integration_cost,
                change_mgmt_pct=c.change_mgmt_pct, contingency_pct=c.contingency_pct)
```

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_lattice_golden.py -v`
Expected: PASS (1 passed). If a number is off, the bug is in the named `compute` function — fix it there, not in the fixture.

- [ ] **Step 4: Run the whole engine suite**

Run: `python -m pytest engine/tests -v`
Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/tests/fixtures engine/tests/test_lattice_golden.py
git commit -m "test(engine): Lattice golden integration fixture + end-to-end assertions"
```

---

# PART 2 — Workbook writer + run CLI (spec §10 step 2)

### Task 11: `run.py` — compute and emit `results.json`

**Files:**
- Create: `engine/run.py`
- Create: `engine/tests/test_run.py`

`results.json` shape (canonical numbers; ranges as `{"low":..,"high":..}` or the string `"PENDING"`):

```json
{
  "value":   {"OPP-001": {"low":400000.0,"high":560000.0}, ...},
  "scores":  {"OPP-001": 4.0, ...},
  "costs":   {"OPP-001": {"labor":..., "total":310500.0, "rom":{"low":155250.0,"high":465750.0}, "rom_label":"ROM estimate, AACE Class 5 (±50%)"}, ...},
  "wave1_aggregate": {
     "investment": {"low":227700.0,"high":683100.0},
     "value":      {"low":500000.0,"high":760000.0},
     "payback_years": {"low":0.30,"high":1.37}
  }
}
```

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_run.py`:

```python
import json
import shutil
from pathlib import Path

from engine.run import build_results, main

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"


def test_build_results_matches_golden():
    res = build_results(FIXTURE)
    assert res["value"]["OPP-001"] == {"low": 400_000.0, "high": 560_000.0}
    assert res["scores"]["OPP-001"] == 4.0
    assert res["costs"]["OPP-001"]["total"] == 310_500.0
    assert res["costs"]["OPP-001"]["rom"] == {"low": 155_250.0, "high": 465_750.0}
    assert res["costs"]["OPP-001"]["rom_label"] == "ROM estimate, AACE Class 5 (±50%)"
    assert res["wave1_aggregate"]["investment"] == {"low": 227_700.0, "high": 683_100.0}
    assert res["wave1_aggregate"]["payback_years"] == {"low": 0.30, "high": 1.37}


def test_main_writes_results_json(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    main([str(eng)])
    written = json.loads((eng / "model" / "results.json").read_text())
    assert written["scores"]["OPP-002"] == 3.0


def test_missing_cost_input_renders_pending(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    costs = json.loads((eng / "model" / "costs.json").read_text())
    costs[0]["labor_hours"] = None  # break OPP-001 labor
    (eng / "model" / "costs.json").write_text(json.dumps(costs))
    res = build_results(eng / "model")
    assert res["costs"]["OPP-001"]["rom"] == "PENDING"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_run.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.run'`.

- [ ] **Step 3: Write minimal implementation**

Create `engine/run.py`:

```python
"""CLI / module entry: read model/*.json -> compute -> write results.json + .xlsx.

This is the only I/O boundary. Usage: python -m engine.run <engagement-folder>/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.compute import (
    AACE_CLASS5_LABEL, cost_structure, initiative_rom, payback,
    score_composite, value_range, wave1_aggregate,
)
from engine.model import PENDING, Range, load_inputs


def _range_out(r):
    return PENDING if r == PENDING else {"low": r.low, "high": r.high}


def build_results(model_dir) -> dict:
    inp = load_inputs(model_dir)
    wave1 = [i.opp_id for i in inp.initiatives if i.wave == 1]

    value = {}
    for opp, v in inp.value.items():
        value[opp] = _range_out(value_range(v.improvement_low, v.improvement_high,
                                            v.volume, v.rate))

    scores = {opp: score_composite(s.dimensions) for opp, s in inp.scores.items()}

    costs = {}
    rom_by_opp = {}
    for opp, c in inp.costs.items():
        cb = cost_structure(c.labor_hours, c.labor_rate, c.tech_cost,
                            c.integration_cost, c.change_mgmt_pct, c.contingency_pct)
        rom = initiative_rom(cb)
        rom_by_opp[opp] = rom
        if cb == PENDING:
            costs[opp] = {"total": PENDING, "rom": PENDING, "rom_label": AACE_CLASS5_LABEL}
        else:
            costs[opp] = {
                "labor": cb.labor, "tech_cost": cb.tech_cost,
                "integration_cost": cb.integration_cost, "change_mgmt": cb.change_mgmt,
                "subtotal": cb.subtotal, "contingency": cb.contingency, "total": cb.total,
                "rom": _range_out(rom), "rom_label": AACE_CLASS5_LABEL,
            }

    investment = wave1_aggregate([rom_by_opp.get(o, PENDING) for o in wave1])
    value_ranges = []
    for o in wave1:
        vr = value.get(o, PENDING)
        value_ranges.append(PENDING if vr == PENDING else Range(vr["low"], vr["high"]))
    annual_value = wave1_aggregate(value_ranges)
    pb = payback(investment, annual_value)

    return {
        "value": value,
        "scores": scores,
        "costs": costs,
        "wave1_aggregate": {
            "investment": _range_out(investment),
            "value": _range_out(annual_value),
            "payback_years": _range_out(pb),
        },
    }


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: python -m engine.run <engagement-folder>/", file=sys.stderr)
        return 2
    engagement = Path(argv[0])
    model_dir = engagement / "model"
    results = build_results(model_dir)
    (model_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Workbook (wired in Task 12). Import here so Task 11 tests pass before workbook exists.
    try:
        from engine.workbook import write_workbook
        write_workbook(load_inputs(model_dir), results, engagement / "financial-model.xlsx")
    except ImportError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_run.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/run.py engine/tests/test_run.py
git commit -m "feat(engine): run.py CLI — compute and emit results.json"
```

---

### Task 12: `workbook.py` — live-formula `.xlsx`

**Files:**
- Create: `engine/workbook.py`
- Create: `engine/tests/test_workbook.py`

**Cross-app rule (spec §6.4):** use only plain arithmetic, `SUM`, and cell/sheet references; no Excel-only functions, named ranges, or tables. Set `wb.calc_properties.fullCalcOnLoad = True` so Apple Numbers / Google Sheets recompute on open/import.

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_workbook.py`:

```python
from pathlib import Path

import openpyxl

from engine.model import load_inputs
from engine.run import build_results
from engine.workbook import write_workbook

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"


def test_workbook_has_expected_tabs_and_formulas(tmp_path):
    inp = load_inputs(FIXTURE)
    res = build_results(FIXTURE)
    out = tmp_path / "financial-model.xlsx"
    write_workbook(inp, res, out)

    wb = openpyxl.load_workbook(out)  # data_only=False -> formula strings
    for tab in ("Inputs", "Value (P5)", "Scores (P6)", "Costs (P8.5)",
                "Business Case (P9)", "Wave-1 Aggregate"):
        assert tab in wb.sheetnames

    # Downstream cells must be formulas (start with "="), not literals.
    value_tab = wb["Value (P5)"]
    formula_cells = [c.value for row in value_tab.iter_rows() for c in row
                     if isinstance(c.value, str) and c.value.startswith("=")]
    assert formula_cells, "Value tab must contain at least one =formula"


def test_workbook_sets_full_calc_on_load(tmp_path):
    inp = load_inputs(FIXTURE)
    res = build_results(FIXTURE)
    out = tmp_path / "wb.xlsx"
    write_workbook(inp, res, out)
    wb = openpyxl.load_workbook(out)
    assert wb.calculation.fullCalcOnLoad is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest engine/tests/test_workbook.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.workbook'`.

- [ ] **Step 3: Write minimal implementation**

Create `engine/workbook.py`:

```python
"""openpyxl writer: inputs as literal cells, every downstream value as a live =formula.

Cross-app safe: plain arithmetic, SUM, and A1/sheet references only. No Excel-only
functions, named ranges, or tables. fullCalcOnLoad=True so Numbers/Sheets recompute.
"""
from __future__ import annotations

from pathlib import Path

import openpyxl


def _q(sheet_name: str) -> str:
    # Sheet names with spaces/parens must be single-quoted in references.
    return f"'{sheet_name}'"


def write_workbook(inputs, results, out_path) -> Path:
    out_path = Path(out_path)
    wb = openpyxl.Workbook()
    wb.calculation.fullCalcOnLoad = True

    ws_in = wb.active
    ws_in.title = "Inputs"
    wave1 = [i for i in inputs.initiatives if i.wave == 1]

    # --- Inputs tab: literal cells. One row per Wave-1 initiative. ---
    ws_in.append(["OPP-ID", "Name",
                  "impr_low", "impr_high", "volume", "rate",
                  "labor_hours", "labor_rate", "tech_cost", "integration_cost",
                  "change_mgmt_pct", "contingency_pct",
                  "d1", "d2", "d3", "d4", "d5", "d6"])
    row_of = {}
    for idx, init in enumerate(wave1, start=2):
        opp = init.opp_id
        v = inputs.value.get(opp)
        c = inputs.costs.get(opp)
        s = inputs.scores.get(opp)
        ws_in.append([
            opp, init.name,
            getattr(v, "improvement_low", None), getattr(v, "improvement_high", None),
            getattr(v, "volume", None), getattr(v, "rate", None),
            getattr(c, "labor_hours", None), getattr(c, "labor_rate", None),
            getattr(c, "tech_cost", None), getattr(c, "integration_cost", None),
            getattr(c, "change_mgmt_pct", None), getattr(c, "contingency_pct", None),
            *(s.dimensions if s else [None] * 6),
        ])
        row_of[opp] = idx

    IN = _q("Inputs")

    # --- Value (P5): improvement × volume × rate ---
    ws_v = wb.create_sheet("Value (P5)")
    ws_v.append(["OPP-ID", "value_low", "value_high"])
    for opp, r in row_of.items():
        ws_v.append([opp,
                     f"={IN}!C{r}*{IN}!E{r}*{IN}!F{r}",   # impr_low*volume*rate
                     f"={IN}!D{r}*{IN}!E{r}*{IN}!F{r}"])  # impr_high*volume*rate

    # --- Scores (P6): mean of 6 dims ---
    ws_s = wb.create_sheet("Scores (P6)")
    ws_s.append(["OPP-ID", "composite"])
    for opp, r in row_of.items():
        ws_s.append([opp, f"=SUM({IN}!M{r}:R{r})/6"])

    # --- Costs (P8.5): roll-up ---
    ws_c = wb.create_sheet("Costs (P8.5)")
    ws_c.append(["OPP-ID", "labor", "change_mgmt", "subtotal", "contingency",
                 "total", "rom_low", "rom_high"])
    cost_row = {}
    for i, (opp, r) in enumerate(row_of.items(), start=2):
        # labor=G*H ; cm=labor*K ; subtotal=labor+I+J+cm ; cont=subtotal*L ; total=subtotal+cont
        ws_c.append([
            opp,
            f"={IN}!G{r}*{IN}!H{r}",                              # B labor
            f"=B{i}*{IN}!K{r}",                                   # C change_mgmt
            f"=B{i}+{IN}!I{r}+{IN}!J{r}+C{i}",                    # D subtotal
            f"=D{i}*{IN}!L{r}",                                   # E contingency
            f"=D{i}+E{i}",                                        # F total
            f"=F{i}*0.5",                                         # G rom_low
            f"=F{i}*1.5",                                         # H rom_high
        ])
        cost_row[opp] = i

    # --- Business Case (P9): per-initiative ROM (references Costs tab) ---
    ws_bc = wb.create_sheet("Business Case (P9)")
    ws_bc.append(["OPP-ID", "rom_low", "rom_high", "value_low", "value_high"])
    CO = _q("Costs (P8.5)")
    VA = _q("Value (P5)")
    for i, opp in enumerate(row_of, start=2):
        cr = cost_row[opp]
        ws_bc.append([opp,
                      f"={CO}!G{cr}", f"={CO}!H{cr}",
                      f"={VA}!B{i}", f"={VA}!C{i}"])

    # --- Wave-1 Aggregate: SUMs + payback ---
    ws_a = wb.create_sheet("Wave-1 Aggregate")
    n = len(row_of)
    last = 1 + n  # rows 2..last in Business Case
    BC = _q("Business Case (P9)")
    ws_a.append(["metric", "low", "high"])
    ws_a.append(["investment", f"=SUM({BC}!B2:B{last})", f"=SUM({BC}!C2:C{last})"])
    ws_a.append(["annual_value", f"=SUM({BC}!D2:D{last})", f"=SUM({BC}!E2:E{last})"])
    # payback best = investment.low/value.high ; worst = investment.high/value.low
    ws_a.append(["payback_years", "=B2/C3", "=C2/B3"])

    wb.save(out_path)
    return out_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest engine/tests/test_workbook.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add engine/workbook.py engine/tests/test_workbook.py
git commit -m "feat(engine): workbook.py — live-formula cross-app .xlsx writer"
```

---

### Task 13: Formula-vs-results equality test (spec §6.4, §8)

**Files:**
- Create: `engine/tests/test_workbook_equality.py`

**Why:** `openpyxl` stores formula *strings*, not computed values. This test evaluates the workbook headlessly with the `formulas` package and asserts the evaluated results equal `results.json` — proving the two sources of truth agree.

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_workbook_equality.py`:

```python
from pathlib import Path

import pytest

from engine.model import load_inputs
from engine.run import build_results
from engine.workbook import write_workbook

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"
formulas = pytest.importorskip("formulas")


def test_workbook_results_equal_results_json(tmp_path):
    inp = load_inputs(FIXTURE)
    res = build_results(FIXTURE)
    out = tmp_path / "financial-model.xlsx"
    write_workbook(inp, res, out)

    xl = formulas.ExcelModel().loads(str(out)).finish()
    sol = xl.calculate()

    def cell(sheet, a1):
        for k, v in sol.items():
            ku = k.upper()
            if ku.endswith(f"'{sheet.upper()}'!{a1}") or ku.endswith(f"{sheet.upper()}!{a1}"):
                return float(v.value[0, 0])
        raise KeyError(f"{sheet}!{a1}")

    # Wave-1 aggregate investment low/high must equal results.json.
    inv = res["wave1_aggregate"]["investment"]
    assert cell("Wave-1 Aggregate", "B2") == pytest.approx(inv["low"])
    assert cell("Wave-1 Aggregate", "C2") == pytest.approx(inv["high"])
    pb = res["wave1_aggregate"]["payback_years"]
    assert cell("Wave-1 Aggregate", "B4") == pytest.approx(pb["low"], abs=0.01)
    assert cell("Wave-1 Aggregate", "C4") == pytest.approx(pb["high"], abs=0.01)
```

- [ ] **Step 2: Run test to verify it passes (or skips)**

Run: `python -m pytest engine/tests/test_workbook_equality.py -v`
Expected: PASS. If `formulas` cannot be imported, the test SKIPS (acceptable on a constrained env) — but in CI it must be installed and PASS. If the `formulas` cell-key matching is brittle, adjust the `cell()` helper's key-matching to the exact key format `formulas` emits (inspect `sol.keys()`), keeping the equality assertions intact.

- [ ] **Step 3: Run the whole engine suite + round-trip note**

Run: `python -m pytest engine/tests -v`
Expected: ALL PASS.

Then run the cross-app round-trip smoke check manually (spec §10): generate the fixture workbook with
`python -c "from pathlib import Path; from engine.model import load_inputs; from engine.run import build_results; from engine.workbook import write_workbook; m=Path('engine/tests/fixtures/lattice/model'); write_workbook(load_inputs(m), build_results(m), 'financial-model.smoke.xlsx')"`,
open `financial-model.smoke.xlsx` in Apple Numbers and import it into Google Sheets, confirm the Wave-1 Aggregate recomputes in both, then delete the smoke file. Record the result in the PR description.

- [ ] **Step 4: Commit**

```bash
git add engine/tests/test_workbook_equality.py
git commit -m "test(engine): workbook formula results equal results.json (headless)"
```

---

# PART 3 — Phase wiring (spec §10 step 3)

Wire phases one at a time, P9 first (highest value), validating the engine against the fixture after each. Each task: (a) edit the SKILL.md/agent to write `model/<phase>.json`, run the engine, and cite `results.json`; (b) remove in-prose arithmetic instructions; (c) add an anti-regression guard to `tests/test_guards.py`.

**Shared guard scaffold** — before Task 14, add this section header to `tests/test_guards.py` so each phase task appends one guard:

```python
# --- Deterministic-math guards (defends: issue #9 — no prose arithmetic) ---
# Each wired phase must (a) instruct writing model/<phase>.json, (b) cite results.json,
# (c) NOT instruct the model to perform arithmetic in prose.
import re as _re  # already imported at top; keep single import in practice
```

(If `re` is already imported at the top of the file, skip the re-import — just add the comment banner.)

### Task 14: Wire Phase 9 — `building-business-case` + `business-case-analyst`

**Files:**
- Modify: `skills/building-business-case/SKILL.md`
- Modify: `agents/business-case-analyst.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_phase9_cites_engine_not_prose_math():
    skill = (REPO_ROOT / "skills" / "building-business-case" / "SKILL.md").read_text()
    assert "model/costs.json" in skill
    assert "python -m engine.run" in skill
    assert "results.json" in skill
    agent = (REPO_ROOT / "agents" / "business-case-analyst.md").read_text()
    assert "results.json" in agent
    # The analyst no longer computes ROM ranges itself.
    assert "compute" not in agent.lower() or "engine" in agent.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_phase9_cites_engine_not_prose_math -v`
Expected: FAIL — assertions on missing strings.

- [ ] **Step 3: Edit the skill**

In `skills/building-business-case/SKILL.md`, after the "## Session Start" gate block, add a new section:

```markdown
## Deterministic math (engine-computed — no prose arithmetic)

Phase 9 performs **no arithmetic in prose**. Every figure is computed by the engine and read back from `model/results.json`.

1. After confirming inputs from `cost-actuals.md` and the Wave-1 `opportunities/OPP-NNN.md` value hypotheses, write the structured inputs to the engagement's `model/` folder:
   - `model/costs.json` — one object per Wave-1 OPP-ID: `labor_hours`, `labor_rate`, `tech_cost`, `integration_cost`, `change_mgmt_pct`, `contingency_pct`. A figure not yet available is recorded as `null` (renders PENDING — never invent it).
   - `model/value.json` — `improvement_low`, `improvement_high`, `volume`, `rate` per OPP-ID (from the verbatim value hypothesis; do not re-derive).
   - `model/initiatives.json` — `opp_id`, `name`, `wave` per Wave-1 OPP-ID.
2. Run the engine: `python -m engine.run <engagement-folder>/`. This writes `model/results.json` and `financial-model.xlsx`.
3. Populate every figure in `business-case.md` by citing `results.json` (per-initiative `costs.*.rom`, `value`, and `wave1_aggregate.investment` / `value` / `payback_years`). The ROM label `AACE Class 5 (±50%)` comes from `results.json` `rom_label`.
4. Any `results.json` value equal to `"PENDING"` renders as **PENDING** in the business case with a note on what input is missing — never a fabricated number.
```

Then, in the existing "### Per-initiative cost structure format" area and the "Wave 1 Aggregate" description, replace any instruction that has the model compute a figure with "cite the corresponding `results.json` value." Specifically, change the cost-block intro line to: "Each `[range]` and the **Initiative ROM range** are read from `model/results.json` (`costs.<OPP-ID>`), not computed here."

- [ ] **Step 4: Edit the agent**

In `agents/business-case-analyst.md`, find the section describing how it produces cost/value figures and replace the compute instruction with:

```markdown
## Source of every number

This analyst performs **no arithmetic**. All figures — labor roll-ups, change-management and contingency lines, the initiative ROM range, the Wave-1 aggregate, and payback — are computed by the deterministic engine and read from `model/results.json`. The analyst composes the prose cost-structure and value-case blocks *around* those engine outputs. PENDING discipline now lives in the engine: a `"PENDING"` value in `results.json` is surfaced verbatim with a note on the missing input; it is never replaced with an estimate.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_phase9_cites_engine_not_prose_math -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/building-business-case/SKILL.md agents/business-case-analyst.md tests/test_guards.py
git commit -m "feat(phase9): cite engine results.json; analyst stops computing (#9)"
```

---

### Task 15: Wire Phase 8.5 — `collecting-cost-actuals`

**Files:**
- Modify: `skills/collecting-cost-actuals/SKILL.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_phase85_writes_cost_inputs_for_engine():
    skill = (REPO_ROOT / "skills" / "collecting-cost-actuals" / "SKILL.md").read_text()
    assert "model/costs.json" in skill
    assert "null" in skill  # missing inputs recorded as null -> PENDING
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_phase85_writes_cost_inputs_for_engine -v`
Expected: FAIL.

- [ ] **Step 3: Edit the skill**

In `skills/collecting-cost-actuals/SKILL.md`, add a section after the worksheet-capture instructions:

```markdown
## Recording captured costs for the engine

As each cost actual is confirmed, record it in structured form in the engagement's `model/costs.json` (one object per Wave-1 OPP-ID with `labor_hours`, `labor_rate`, `tech_cost`, `integration_cost`, `change_mgmt_pct`, `contingency_pct`). Any value not yet collected is recorded as `null` — it will render as PENDING in the business case and the workbook until supplied. Do not enter placeholder or estimated numbers in place of `null`. `cost-actuals.md` remains the human-readable record; `model/costs.json` is the engine's input.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_phase85_writes_cost_inputs_for_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/collecting-cost-actuals/SKILL.md tests/test_guards.py
git commit -m "feat(phase8.5): record cost actuals to model/costs.json (#9)"
```

---

### Task 16: Wire Phase 6 — `scoring-opportunities` + `opportunity-scorer`

**Files:**
- Modify: `skills/scoring-opportunities/SKILL.md`
- Modify: `agents/opportunity-scorer.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_phase6_composite_from_engine():
    skill = (REPO_ROOT / "skills" / "scoring-opportunities" / "SKILL.md").read_text()
    assert "model/scores.json" in skill
    agent = (REPO_ROOT / "agents" / "opportunity-scorer.md").read_text()
    assert "model/scores.json" in agent
    assert "composite" in agent.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_phase6_composite_from_engine -v`
Expected: FAIL.

- [ ] **Step 3: Edit skill + agent**

In `skills/scoring-opportunities/SKILL.md`, add after the scoring-rubric section:

```markdown
## Composite score (engine-computed)

The composite is **not** averaged by the model in prose. Each scorer records its six dimension scores for an OPP-ID into the engagement's `model/scores.json` (`{"opp_id": "...", "dimensions": [d1..d6]}`). After all opportunities are scored, run `python -m engine.run <engagement-folder>/`; the composite for each OPP-ID is read from `results.json` `scores.<OPP-ID>` and stamped into `scores/OPP-NNN.md` and `scores/_index.md`.
```

In `agents/opportunity-scorer.md`, replace any instruction to compute/average the composite with:

```markdown
## Composite

Record the six dimension scores; do not average them. Write `{"opp_id": "<id>", "dimensions": [d1, d2, d3, d4, d5, d6]}` to `model/scores.json`. The composite is computed by the deterministic engine and read from `results.json` — the agent never performs the mean in prose.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_phase6_composite_from_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/scoring-opportunities/SKILL.md agents/opportunity-scorer.md tests/test_guards.py
git commit -m "feat(phase6): composite score from engine; scorer records dims (#9)"
```

---

### Task 17: Wire Phase 5 — `identifying-opportunities`

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_phase5_value_inputs_to_engine():
    skill = (REPO_ROOT / "skills" / "identifying-opportunities" / "SKILL.md").read_text()
    assert "model/value.json" in skill
    assert "results.json" in skill
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_phase5_value_inputs_to_engine -v`
Expected: FAIL.

- [ ] **Step 3: Edit the skill**

In `skills/identifying-opportunities/SKILL.md`, add after the value-hypothesis section:

```markdown
## Value range (engine-computed)

The value hypothesis is written *before* the number (hypothesis-before-value discipline is unchanged). The numeric range itself is **not** multiplied in prose. Record `{"opp_id": "...", "improvement_low": x, "improvement_high": y, "volume": v, "rate": r}` to the engagement's `model/value.json`, run `python -m engine.run <engagement-folder>/`, and cite the resulting `results.json` `value.<OPP-ID>` range in `opportunities/OPP-NNN.md`. `volume` and `rate` must each trace to a `baselines.md` row.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_phase5_value_inputs_to_engine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/identifying-opportunities/SKILL.md tests/test_guards.py
git commit -m "feat(phase5): value ranges from engine model/value.json (#9)"
```

---

### Task 18: Wire Phase 4 — `discovering-processes`

**Files:**
- Modify: `skills/discovering-processes/SKILL.md`
- Modify: `tests/test_guards.py`

**Scope note:** Phase 4 derived figures (e.g. `180×4=720/mo` monthly-volume roll-ups, FTE roll-ups). Record raw baseline inputs to `model/baselines.json`; any derived volume is computed by the engine, not in prose. (Per spec §11, this is independent of the #6 Phase-4 normalization and works with either structure.)

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_phase4_no_prose_volume_math():
    skill = (REPO_ROOT / "skills" / "discovering-processes" / "SKILL.md").read_text()
    assert "model/baselines.json" in skill
    # No instruction to multiply volumes in prose.
    assert "results.json" in skill
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_phase4_no_prose_volume_math -v`
Expected: FAIL.

- [ ] **Step 3: Edit the skill**

In `skills/discovering-processes/SKILL.md`, add after the baseline-capture section:

```markdown
## Recording baselines for the engine

Capture each baseline as raw, sourced inputs in the engagement's `model/baselines.json` (per process: `volume`, `cycle_time_median`, `cycle_time_p90`, `error_rate`, `fte`, and the source). Any *derived* figure (e.g. a monthly volume that is `per-period × periods`, or an FTE roll-up) is computed by the engine, not multiplied in prose. `baselines.md` remains the human-readable, source-cited narrative; `model/baselines.json` feeds the engine and downstream `results.json` so every derived figure is deterministic and auditable.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_phase4_no_prose_volume_math -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/discovering-processes/SKILL.md tests/test_guards.py
git commit -m "feat(phase4): record raw baselines to model/baselines.json (#9)"
```

---

# PART 4 — Deliverable-gate determinism check (spec §10 step 4)

### Task 19: Determinism check in the deliverable-gate

**Files:**
- Modify: `skills/deliverable-gate/SKILL.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_deliverable_gate_has_determinism_check():
    gate = (REPO_ROOT / "skills" / "deliverable-gate" / "SKILL.md").read_text()
    assert "results.json" in gate
    assert "determinism" in gate.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py::test_deliverable_gate_has_determinism_check -v`
Expected: FAIL.

- [ ] **Step 3: Edit the gate**

In `skills/deliverable-gate/SKILL.md`, add a fifth integrity dimension under "## Four Integrity Dimensions" (rename the heading to "## Five Integrity Dimensions") :

```markdown
- **Determinism integrity** — every numeric figure in every markdown deliverable equals its source in `model/results.json`. No number is computed in prose. A figure that does not match `results.json` (or that has no `results.json` source) blocks the gate. PENDING values must appear as PENDING, never as an invented number.
```

And add a checklist item under "## Phase checklist":

```markdown
- [ ] Run Determinism integrity check — for each numeric figure in `business-case.md`, `executive-summary.md` (if present), and `roadmap.md`, confirm it equals the corresponding `model/results.json` value; block on any mismatch or unsourced number
```

Add a rationalization row:

```markdown
| "The model's arithmetic looks right — no need to check results.json." | LLM prose arithmetic is non-deterministic and compounds. The engine is the only source of truth; the gate verifies equality, it does not re-trust the model. |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py::test_deliverable_gate_has_determinism_check -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/deliverable-gate/SKILL.md tests/test_guards.py
git commit -m "feat(gate-b): determinism check — markdown figures == results.json (#9)"
```

---

# PART 5 — Packaging & rollout (spec §10 step 5)

### Task 20: Deliverable workbook link + keystone rule

**Files:**
- Modify: `skills/building-deliverable/SKILL.md`
- Modify: `skills/using-methodology/SKILL.md`
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_keystone_states_no_prose_arithmetic_rule():
    keystone = (REPO_ROOT / "skills" / "using-methodology" / "SKILL.md").read_text()
    assert "no arithmetic in prose" in keystone.lower() or "no prose arithmetic" in keystone.lower()
    assert "results.json" in keystone
    assert "model/" in keystone  # engagement folder convention includes model/


def test_deliverable_links_workbook():
    deliv = (REPO_ROOT / "skills" / "building-deliverable" / "SKILL.md").read_text()
    assert "financial-model.xlsx" in deliv
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py -k "keystone_states or deliverable_links" -v`
Expected: FAIL.

- [ ] **Step 3: Edit the keystone**

In `skills/using-methodology/SKILL.md`, add a new section after "## Master Rationalization Table":

```markdown
## Deterministic Math Rule

> **The model performs no arithmetic in prose, in any phase.** Every number is either a directly-sourced input recorded in `model/*.json`, or a value computed by the deterministic engine (`python -m engine.run <engagement>/`) and read back from `model/results.json`. A figure that is neither is a defect the deliverable-gate must catch.

`model/*.json` is the single source of truth for every number; `results.json` and `financial-model.xlsx` are both derived from it. The deliverable-gate enforces markdown ↔ `results.json` equality. A missing input renders as **PENDING**, never a fabricated number.
```

Add two rows to the "## Engagement Folder Convention" list (after `business-case.md`):

```markdown
- `model/` — structured numeric inputs (`value.json`, `scores.json`, `costs.json`, `baselines.json`, `initiatives.json`) and the engine output `results.json`
- `financial-model.xlsx` — auditable workbook with live formulas (Apple Numbers / Google Sheets compatible)
```

Add a rationalization row to the keystone's Master Rationalization Table:

```markdown
| "I'll just compute this one figure inline — it's simple." | No number is computed in prose, ever. Even a one-line multiply is non-deterministic across runs and breaks auditability. Record the input in `model/*.json` and read the result from `results.json`. |
```

- [ ] **Step 4: Edit building-deliverable**

In `skills/building-deliverable/SKILL.md`, add to the assembly/output instructions:

```markdown
## Financial model artifact

Link `financial-model.xlsx` as a downloadable artifact in the HTML deliverable (e.g. in the investment/roadmap section), and pull all headline figures from `model/results.json` — renderers cite computed results, they never recompute. The workbook lets a skeptical reviewer inspect and flex the math.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py -k "keystone_states or deliverable_links" -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/using-methodology/SKILL.md skills/building-deliverable/SKILL.md tests/test_guards.py
git commit -m "feat(rollout): keystone no-prose-math rule, model/ convention, workbook link (#9)"
```

---

### Task 21: INSTALL/README Python step + pytest testpaths + version bump

**Files:**
- Modify: `INSTALL.md`
- Modify: `README.md`
- Modify: `pytest.ini`
- Modify: `.claude-plugin/plugin.json` (version)
- Modify: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guard test**

Append to `tests/test_guards.py`:

```python
def test_pytest_includes_engine_tests():
    cfg = (REPO_ROOT / "pytest.ini").read_text()
    assert "engine/tests" in cfg


def test_install_has_python_setup_step():
    install = (REPO_ROOT / "INSTALL.md").read_text()
    assert "pip install -r requirements.txt" in install
    assert "engine" in install.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_guards.py -k "pytest_includes or install_has" -v`
Expected: FAIL.

- [ ] **Step 3: Update pytest.ini**

Replace the testpaths block in `pytest.ini` with:

```ini
[pytest]
testpaths = tests engine/tests
python_files = test_*.py
python_functions = test_*
```

- [ ] **Step 4: Update INSTALL.md and README.md**

In `INSTALL.md`, add a "Python engine setup" step near the environment setup:

```markdown
### Python math engine (required for any shipped number)

The methodology computes every number with a deterministic Python engine (`engine/`). Set it up once:

```bash
pip install -r requirements.txt   # openpyxl, pytest, formulas
python -m pytest engine/tests -q  # verify the golden-number suite passes
```

Each numeric phase writes structured inputs to the engagement's `model/*.json`, then runs `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`. Without a code-execution environment the methodology still runs, but figures render "pending engine."
```

In `README.md`, add a short "Deterministic math engine" subsection pointing to `engine/` and the no-prose-arithmetic rule (one paragraph, mirroring the keystone rule).

- [ ] **Step 5: Bump version**

In `.claude-plugin/plugin.json`, change `"version": "2.4.0"` to `"version": "2.5.0"`.

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_guards.py -k "pytest_includes or install_has" -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add INSTALL.md README.md pytest.ini .claude-plugin/plugin.json tests/test_guards.py
git commit -m "chore: engine install step, testpaths, v2.5.0 (#9)"
```

---

### Task 22: Full-suite verification + sample re-validation

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `python -m pytest -q`
Expected: ALL PASS (repo methodology suite + engine suite). Capture the summary line.

- [ ] **Step 2: Engine smoke run against the Lattice fixture**

Run:
```bash
python -c "from engine.run import main; main(['engine/tests/fixtures/lattice'])"
cat engine/tests/fixtures/lattice/model/results.json
```
Expected: `results.json` shows `wave1_aggregate.investment = {low:227700.0, high:683100.0}`, `payback_years = {low:0.3, high:1.37}`, and `financial-model.xlsx` is written next to the fixture. Then remove the generated `results.json` and `financial-model.xlsx` from the fixture dir if they are not meant to be committed (the committed fixture is inputs only):
```bash
git status --porcelain engine/tests/fixtures
```
If `results.json`/`.xlsx` appear as untracked, delete them (they are generated, not fixtures).

- [ ] **Step 3: Confirm no prose-arithmetic instructions remain**

Run:
```bash
python -m pytest tests/test_guards.py -k "phase or determinism or keystone or deliverable_links or pytest_includes or install" -v
```
Expected: ALL PASS — confirms every wired phase cites the engine.

- [ ] **Step 4: Final commit (if any cleanup occurred)**

```bash
git add -A
git commit -m "test: full-suite green for deterministic math engine (#9)" || echo "nothing to commit"
```

---

## Self-review checklist (run after execution, before PR)

Cross-check against spec §12 acceptance criteria:

- [ ] No phase instructs prose arithmetic; all numbers trace to `model/*.json` or `results.json` — Tasks 14–20 + guards.
- [ ] Engine computes value ranges, score composites, cost structures, ROM ranges, Wave-1 aggregate, payback with passing golden suite incl. Lattice integration — Tasks 2–10.
- [ ] A run produces `results.json` + `financial-model.xlsx` with live formulas; changing an Inputs cell reflows downstream — Tasks 11–12 (verify reflow manually in the §10 round-trip).
- [ ] Workbook formula results equal `results.json` (headless) — Task 13.
- [ ] Workbook opens/recomputes in Apple Numbers and after Google Sheets import; cross-app functions + `fullCalcOnLoad` — Task 12 + Task 13 Step 3 manual smoke.
- [ ] Deliverable-gate blocks on any markdown figure ≠ `results.json` — Task 19.
- [ ] Missing inputs render PENDING in both `results.json` and the workbook — Tasks 8/9/11 + workbook `None` cells.

**Out of scope (do NOT implement):** native Google Sheets backend; NPV/DCF; replacing non-numeric extraction headers; Phase-4 normalization (#6); the optional `--to-sheets` converter (spec §10 step 6 — deferred).
