# Data Contract + Artifact Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `model/*.json` + `results.json` to a versioned, verifiable public data contract by adding an engine-emitted audit trace, a stdlib figure-verifier, and a `generate-artifact` skill that renders any artifact from that contract under a mechanical no-new-arithmetic guard.

**Architecture:** The engine gains a second additive output, `model/trace.json`, built by a new `engine/trace.py` that reads the values `engine/compute.py` already returns and formats them into per-figure provenance (it performs no arithmetic of its own). A new `engine/artifact_check.py` verifies an artifact's *figure manifest* (each number tagged with its contract path) against `results.json`. A new standalone `generate-artifact` skill regenerates the contract, renders an artifact referencing figures by path, builds a manifest, and runs the verifier before emitting. `results.json` bytes are untouched.

**Tech Stack:** Python 3 standard library only (no third-party runtime deps); pytest for tests; Markdown skill docs.

## Global Constraints

- **Pure standard library at runtime.** `engine/` and `state/` import NO third-party packages. `pyyaml`/`pytest` are dev/test-only. (Verified by `engine/tests/test_stdlib_core.py`.)
- **`model/results.json` stays byte-identical.** Do not change `engine/compute.py` formulas or `engine/run.py`'s `build_results` output. The trace is a *separate* file.
- **`contract_version` is `"1.0"`** and lives in `trace.json` + `docs/data-contract.md` only — never in `results.json`.
- **Do NOT edit `skills/using-methodology/SKILL.md` or `system-prompt.md`** — they are under a verbatim-sync guard (`tests/test_guards.py`). `model/trace.json` is an engine sidecar and must NOT be added to the keystone's "Engagement Folder Convention" list.
- **`trace.py` performs no arithmetic.** Every number in a trace step or input comes from `compute.py`'s returned values or its declared inputs.
- **No version bump.** This is a Foundation chunk; changes accumulate under CHANGELOG `[Unreleased]` (matching #90/#91), no edit to `.claude-plugin/plugin.json` / `marketplace.json`.
- **Contract path grammar:** result/trace paths are dotted from the `results.json` root (`costs.OPP-001.total`, `wave1_aggregate.payback_years.low`); input source paths are `model/<file>.json#<id>.<field>` (`model/costs.json#OPP-001.labor_hours`).
- **Run tests with the venv:** `.venv/bin/python -m pytest` (bare `python3` lacks `pyyaml`, which the `tests/` guard suite imports).
- Spec: `docs/superpowers/specs/2026-06-20-data-contract-and-artifacts-design.md`.

---

## File Structure

- `engine/trace.py` (new) — `CONTRACT_VERSION` + `build_trace(model_dir) -> dict`: per-figure provenance mirroring `results.json`'s structure. Owns only step-string *formatting*, never arithmetic.
- `engine/run.py` (modify) — `main()` additionally writes `model/trace.json`. `build_results` unchanged.
- `engine/artifact_check.py` (new) — `check_manifest(manifest, results) -> list[str]` and `verify(...) -> bool`: resolve each manifest figure's path in `results.json` and compare values.
- `docs/data-contract.md` (new) — the public API reference for every `results.json` + `trace.json` key, the path grammar, and the versioning policy.
- `skills/generate-artifact/SKILL.md` (new) — the standalone skill.
- `skills/generate-artifact/cfo-audit-template.md` (new) — the one built-in template.
- `sample-pso-delivery/artifacts/cfo-audit.md` + `cfo-audit.manifest.json` (new) — committed sample artifact + manifest for the end-to-end test.
- `engine/tests/test_trace.py` (new) — trace coverage, step soundness, source resolution.
- `engine/tests/test_artifact_check.py` (new) — verifier accept/reject.
- `tests/test_data_contract.py` (new) — contract-doc key coverage + sample-audit end-to-end.
- `tests/test_skills.py` (modify) — allowlist + count for the new skill.
- `CHANGELOG.md` (modify) — `[Unreleased]` entry.
- `skills/conducting-engagement/SKILL.md` (modify) — register the on-demand artifact capability.

---

## Task 1: Engine emits `model/trace.json`

**Files:**
- Create: `engine/trace.py`
- Modify: `engine/run.py` (imports + `main()`)
- Test: `engine/tests/test_trace.py`

**Interfaces:**
- Consumes: `engine.model.load_inputs`, `engine.model.Inputs/CostBlock/Range/PENDING`, and the `engine.compute` functions (`value_range`, `score_composite`, `cost_structure`, `initiative_rom`, `wave1_aggregate`, `wave1_point`, `payback`).
- Produces: `engine.trace.CONTRACT_VERSION` (`"1.0"`), `engine.trace.build_trace(model_dir) -> dict`. The dict has top-level keys `contract_version`, `value`, `scores`, `costs`, `baselines`, `wave1_aggregate`, mirroring `results.json` (minus nothing; baselines are passthrough). `engine.run.main` writes it to `model/trace.json`.

**Provenance entry shapes** (what `build_trace` emits per figure):
- Computed figure: `{"formula": <str>, "result": <number>, "inputs": [{"name","value","source"}...], "steps": [<str>...]}`.
- PENDING figure: `{"formula": <str>, "result": "PENDING"}` (no `inputs`/`steps`).
- Passthrough (`baselines.*` field): `{"formula": "passthrough", "result": <value>, "source": "model/baselines.json#<PROC>.<field>"}`.

- [ ] **Step 1: Write the failing tests**

```python
# engine/tests/test_trace.py
import ast
import operator
import re
from pathlib import Path

from engine.run import build_results
from engine.trace import CONTRACT_VERSION, build_trace

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"

# Leaf figure paths we expect provenance for, derived from results.json structure.
def _numeric_leaf_paths(results: dict) -> set[str]:
    paths = set()
    def walk(node, prefix):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(node, (int, float)) or node == "PENDING":
            paths.add(prefix)
    # Exclude label strings explicitly.
    walk(results, "")
    return {p for p in paths if not p.endswith("rom_label")}

# A figure's provenance is ONE node (a range figure covers both endpoints), so a
# results leaf is "covered" if descending the trace by the same path hits a node
# carrying a "formula" key at or before the leaf.
def _covered(trace: dict, path: str) -> bool:
    cur = trace
    for part in path.split("."):
        if isinstance(cur, dict) and "formula" in cur:
            return True
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return isinstance(cur, dict) and "formula" in cur

def test_contract_version_is_1_0():
    assert CONTRACT_VERSION == "1.0"
    assert build_trace(FIXTURE)["contract_version"] == "1.0"

def test_trace_covers_results():
    results = build_results(FIXTURE)
    trace = build_trace(FIXTURE)
    for path in _numeric_leaf_paths(results):
        assert _covered(trace, path), f"no provenance for {path}"

def test_trace_inputs_trace_to_model():
    trace = build_trace(FIXTURE)
    src_re = re.compile(r"^model/(\w+)\.json#([\w-]+)\.(\w+)$")
    def check(node):
        if isinstance(node, dict):
            if node.get("formula") == "passthrough":
                assert src_re.match(node["source"]), node["source"]
            for inp in node.get("inputs", []):
                src = inp["source"]
                if src.startswith("results:"):
                    continue  # intra-contract reference to an upstream computed figure
                assert src_re.match(src), src
            for v in node.values():
                check(v)
    check(trace)

# Evaluate the arithmetic embedded in each step string and assert it is sound.
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv}
def _eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval").body
    def ev(n):
        if isinstance(n, ast.BinOp):
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.Constant):
            return n.value
        raise ValueError(expr)
    return ev(tree)

def test_trace_steps_are_arithmetically_sound():
    # Only two-`=` steps of the form `name = <expr> = <number>` carry arithmetic;
    # single-value (`tech_cost = 80000`) and descriptive aggregate steps are skipped.
    trace = build_trace(FIXTURE)
    def check(node):
        if isinstance(node, dict):
            for step in node.get("steps", []):
                if step.count("=") < 2:
                    continue
                lhs, rhs = step.split("=", 1)[1].rsplit("=", 1)
                try:
                    expected = float(rhs)
                except ValueError:
                    continue
                expr = lhs.replace("×", "*").replace("÷", "/")  # normalize math glyphs
                assert abs(_eval(expr) - expected) < 0.01, step
            for v in node.values():
                check(v)
    check(trace)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest engine/tests/test_trace.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.trace'`.

- [ ] **Step 3: Implement `engine/trace.py`**

Mirror `build_results`'s orchestration (which opp uses which process/wave) so `test_trace_covers_results` stays green; pull every number from `compute.py`'s returns. The orchestration mirror is intentional and is guarded by the coverage test — do not try to share private state with `run.py`.

```python
"""Per-figure provenance for results.json — the audit trace. No arithmetic here:
every number comes from engine.compute's returned values or its declared inputs.
trace.py only formats the human-readable step strings.
"""
from __future__ import annotations

from engine.compute import (
    cost_structure, initiative_rom, payback, score_composite,
    value_range, wave1_aggregate, wave1_point,
)
from engine.model import PENDING, Range, load_inputs

CONTRACT_VERSION = "1.0"


def _num(x):
    """Render a number without a trailing .0 for whole values (for step strings)."""
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _inp(name, value, file, key, field):
    return {"name": name, "value": value, "source": f"model/{file}.json#{key}.{field}"}


def _pending(formula):
    return {"formula": formula, "result": PENDING}


def _value_prov(opp, v, base_volume, volume):
    # Mirror compute.value_range's guard exactly: PENDING if ANY of the four is None.
    if None in (v.improvement_low, v.improvement_high, volume, v.rate):
        return _pending("value_range")
    r = value_range(v.improvement_low, v.improvement_high, volume, v.rate)
    return {
        "formula": "value_range", "result": {"low": r.low, "high": r.high},
        "inputs": [
            _inp("improvement_low", v.improvement_low, "value", opp, "improvement_low"),
            _inp("improvement_high", v.improvement_high, "value", opp, "improvement_high"),
            _inp("base_volume", base_volume, "baselines", v.process_id, "volume"),
            _inp("volume_fraction", v.volume_fraction, "value", opp, "volume_fraction"),
            _inp("rate", v.rate, "value", opp, "rate"),
        ],
        "steps": [
            f"volume = {_num(base_volume)} × {_num(v.volume_fraction)} = {_num(volume)}",
            f"low = {_num(v.improvement_low)} × {_num(volume)} × {_num(v.rate)} = {_num(r.low)}",
            f"high = {_num(v.improvement_high)} × {_num(volume)} × {_num(v.rate)} = {_num(r.high)}",
        ],
    }


def _score_prov(opp, s):
    result = score_composite(s.dimensions)
    if result == PENDING:
        return _pending("score_composite")
    dims = " + ".join(str(_num(d)) for d in s.dimensions)
    return {
        "formula": "score_composite", "result": result,
        "inputs": [_inp("dimensions", list(s.dimensions), "scores", opp, "dimensions")],
        "steps": [f"score = ({dims}) / 6 = {result}"],
    }


def _cost_prov(opp, c, cb):
    if cb == PENDING:
        return {k: _pending("cost_structure") for k in
                ("labor", "tech_cost", "integration_cost", "change_mgmt",
                 "subtotal", "contingency", "total")}
    src = lambda field: _inp(field, getattr(c, field), "costs", opp, field)
    return {
        "labor": {"formula": "cost_structure", "result": cb.labor,
                  "inputs": [src("labor_hours"), src("labor_rate")],
                  "steps": [f"labor = {_num(c.labor_hours)} × {_num(c.labor_rate)} = {_num(cb.labor)}"]},
        "change_mgmt": {"formula": "cost_structure", "result": cb.change_mgmt,
                        "inputs": [src("change_mgmt_pct")],
                        "steps": [f"change_mgmt = {_num(cb.labor)} × {_num(c.change_mgmt_pct)} = {_num(cb.change_mgmt)}"]},
        "tech_cost": {"formula": "cost_structure", "result": cb.tech_cost,
                      "inputs": [src("tech_cost")], "steps": [f"tech_cost = {_num(cb.tech_cost)}"]},
        "integration_cost": {"formula": "cost_structure", "result": cb.integration_cost,
                             "inputs": [src("integration_cost")],
                             "steps": [f"integration_cost = {_num(cb.integration_cost)}"]},
        "subtotal": {"formula": "cost_structure", "result": cb.subtotal,
                     "inputs": [src("labor_hours"), src("labor_rate"), src("tech_cost"),
                                src("integration_cost"), src("change_mgmt_pct")],
                     "steps": [f"subtotal = {_num(cb.labor)} + {_num(cb.tech_cost)} + "
                               f"{_num(cb.integration_cost)} + {_num(cb.change_mgmt)} = {_num(cb.subtotal)}"]},
        "contingency": {"formula": "cost_structure", "result": cb.contingency,
                        "inputs": [src("contingency_pct")],
                        "steps": [f"contingency = {_num(cb.subtotal)} × {_num(c.contingency_pct)} = {_num(cb.contingency)}"]},
        "total": {"formula": "cost_structure", "result": cb.total,
                  "inputs": [src("contingency_pct")],
                  "steps": [f"total = {_num(cb.subtotal)} + {_num(cb.contingency)} = {_num(cb.total)}"]},
    }


def _rom_prov(cb, rom):
    if rom == PENDING:
        return _pending("initiative_rom")
    return {
        "formula": "initiative_rom", "result": {"low": rom.low, "high": rom.high},
        "inputs": [{"name": "total", "value": cb.total, "source": "results:total"}],
        "steps": [f"low = {_num(cb.total)} × 0.5 = {_num(rom.low)}",
                  f"high = {_num(cb.total)} × 1.5 = {_num(rom.high)}"],
    }


def build_trace(model_dir) -> dict:
    inp = load_inputs(model_dir)
    wave1 = [i.opp_id for i in inp.initiatives if i.wave == 1]

    value = {}
    for opp, v in inp.value.items():
        b = inp.baselines.get(v.process_id)
        base_volume = b.volume if b is not None else None
        volume = None if base_volume is None else base_volume * v.volume_fraction
        value[opp] = _value_prov(opp, v, base_volume, volume)

    scores = {opp: _score_prov(opp, s) for opp, s in inp.scores.items()}

    costs = {}
    rom_by_opp, total_by_opp = {}, {}
    for opp, c in inp.costs.items():
        cb = cost_structure(c.labor_hours, c.labor_rate, c.tech_cost,
                            c.integration_cost, c.change_mgmt_pct, c.contingency_pct)
        rom = initiative_rom(cb)
        rom_by_opp[opp] = rom
        total_by_opp[opp] = PENDING if cb == PENDING else cb.total
        block = _cost_prov(opp, c, cb)
        block["rom"] = _rom_prov(cb, rom)
        costs[opp] = block

    baselines = {
        pid: {field: {"formula": "passthrough", "result": getattr(b, field),
                      "source": f"model/baselines.json#{pid}.{field}"}
              for field in ("volume", "cycle_time_median", "cycle_time_p90", "error_rate", "fte")}
        for pid, b in inp.baselines.items()
    }

    investment = wave1_aggregate([rom_by_opp.get(o, PENDING) for o in wave1])
    investment_point = wave1_point([total_by_opp.get(o, PENDING) for o in wave1])
    value_ranges = []
    for o in wave1:
        vp = value.get(o, {}).get("result")
        value_ranges.append(Range(vp["low"], vp["high"]) if isinstance(vp, dict) else PENDING)
    annual_value = wave1_aggregate(value_ranges)
    pb = payback(investment, annual_value)

    def agg_prov(formula, result, members):
        if result == PENDING:
            return _pending(formula)
        if isinstance(result, Range):
            res = {"low": result.low, "high": result.high}
        else:
            res = result
        return {"formula": formula, "result": res,
                "inputs": [{"name": "wave1_members", "value": members, "source": "results:wave1"}],
                "steps": [f"{formula} over Wave-1 members {members}"]}

    wave1_aggregate_prov = {
        "investment": agg_prov("wave1_aggregate", investment, wave1),
        "investment_point": agg_prov("wave1_point", investment_point, wave1),
        "value": agg_prov("wave1_aggregate", annual_value, wave1),
        "payback_years": agg_prov("payback", pb, wave1),
    }

    return {
        "contract_version": CONTRACT_VERSION,
        "value": value, "scores": scores, "costs": costs,
        "baselines": baselines, "wave1_aggregate": wave1_aggregate_prov,
    }
```

> Step-string convention (matches `test_trace_steps_are_arithmetically_sound`): every emitted step is either two-`=` arithmetic (`name = <expr> = <result>`, glyphs `×`/`÷` allowed) or a single-`=`/descriptive line the test skips. Keep arithmetic steps in that shape.

- [ ] **Step 4: Wire `main()` to write `model/trace.json`**

In `engine/run.py`, add the import and extend `main()` (leave `build_results` untouched):

```python
# add to imports
from engine.trace import build_trace

# inside main(), after writing results.json:
    (model_dir / "trace.json").write_text(
        json.dumps(build_trace(model_dir), indent=2), encoding="utf-8")
```

- [ ] **Step 5: Add a run-level test that the file lands**

Append to `engine/tests/test_trace.py`:

```python
import json, shutil
from engine.run import main

def test_main_writes_trace_json(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    main([str(eng)])
    trace = json.loads((eng / "model" / "trace.json").read_text())
    assert trace["contract_version"] == "1.0"
    assert "costs" in trace
```

- [ ] **Step 6: Run the full engine suite (results.json must stay byte-identical)**

Run: `.venv/bin/python -m pytest engine/ -v`
Expected: PASS, including the existing `test_run.py` golden tests (proving `results.json` is unchanged).

- [ ] **Step 7: Commit**

```bash
git add engine/trace.py engine/run.py engine/tests/test_trace.py
git commit -m "feat(engine): emit model/trace.json audit provenance"
```

---

## Task 2: `docs/data-contract.md` — the public API reference

**Files:**
- Create: `docs/data-contract.md`
- Test: `tests/test_data_contract.py` (the contract-doc portion)

**Interfaces:**
- Consumes: `engine.run.build_results`, `engine.trace.build_trace`, `engine.trace.CONTRACT_VERSION`.
- Produces: a doc that names every top-level `results.json` key and the trace's keys + the `contract_version`. No code symbols.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data_contract.py
from pathlib import Path

from engine.run import build_results
from engine.trace import CONTRACT_VERSION, build_trace

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"
CONTRACT_DOC = REPO / "docs" / "data-contract.md"

def test_contract_doc_lists_all_results_keys():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    for key in build_results(FIXTURE):
        assert key in doc, f"data-contract.md omits results key: {key}"

def test_contract_doc_documents_version():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    assert CONTRACT_VERSION in doc
    assert "trace.json" in doc
    assert "contract_version" in doc
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_data_contract.py -v`
Expected: FAIL — `FileNotFoundError` (doc absent).

- [ ] **Step 3: Write `docs/data-contract.md`**

Document: each `results.json` top-level key (`value`, `scores`, `costs`, `baselines`, `wave1_aggregate`) with its sub-shape and types; the `trace.json` provenance shape (computed / PENDING / passthrough entries); the path grammar (result paths dotted from root; input source paths `model/<file>.json#<id>.<field>`); and the `contract_version` semver policy (patch = doc clarification; minor = additive key, back-compatible; major = removed/renamed/retyped key). State `contract_version` is `1.0`, lives in `trace.json` + this doc, and never in `results.json` (which is byte-stable). Every top-level results key name and the literal strings `trace.json`, `contract_version`, and `1.0` must appear verbatim.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_data_contract.py -v`
Expected: PASS (both contract-doc tests).

- [ ] **Step 5: Commit**

```bash
git add docs/data-contract.md tests/test_data_contract.py
git commit -m "docs(contract): document results.json + trace.json public API (v1.0)"
```

---

## Task 3: `engine/artifact_check.py` — the figure verifier

**Files:**
- Create: `engine/artifact_check.py`
- Test: `engine/tests/test_artifact_check.py`

**Interfaces:**
- Consumes: a `results` dict (from `build_results`), a `manifest` list of `{"value": <number>, "path": <str>}`.
- Produces: `engine.artifact_check.check_manifest(manifest, results) -> list[str]` (empty = all figures trace) and `engine.artifact_check.verify(manifest, results) -> bool`.

- [ ] **Step 1: Write the failing tests**

```python
# engine/tests/test_artifact_check.py
from pathlib import Path

from engine.run import build_results
from engine.artifact_check import check_manifest, verify

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"

def test_clean_manifest_verifies():
    results = build_results(FIXTURE)
    total = results["costs"]["OPP-001"]["total"]
    manifest = [{"value": total, "path": "costs.OPP-001.total"}]
    assert check_manifest(manifest, results) == []
    assert verify(manifest, results) is True

def test_rounding_tolerance():
    results = build_results(FIXTURE)
    total = results["costs"]["OPP-001"]["total"]
    manifest = [{"value": round(total) + 0.004, "path": "costs.OPP-001.total"}]
    assert verify(manifest, results) is True  # equal after 2dp rounding

def test_invented_number_rejected():
    results = build_results(FIXTURE)
    manifest = [{"value": 999999.0, "path": "costs.OPP-001.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "costs.OPP-001.total" in errs[0]
    assert verify(manifest, results) is False

def test_unknown_path_rejected():
    results = build_results(FIXTURE)
    manifest = [{"value": 1.0, "path": "costs.OPP-999.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "unknown path" in errs[0]

def test_pending_figure_rejected():
    results = build_results(FIXTURE)
    results["costs"]["OPP-001"]["total"] = "PENDING"
    manifest = [{"value": 0, "path": "costs.OPP-001.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "PENDING" in errs[0]

def test_range_endpoint_paths():
    results = build_results(FIXTURE)
    low = results["wave1_aggregate"]["investment"]["low"]
    manifest = [{"value": low, "path": "wave1_aggregate.investment.low"}]
    assert verify(manifest, results) is True
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest engine/tests/test_artifact_check.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.artifact_check'`.

- [ ] **Step 3: Implement `engine/artifact_check.py`**

```python
"""Verify an artifact's figure manifest against the engine's results.json.

A manifest entry is {"value": <number>, "path": "<dotted results path>"}.
Every figure an artifact presents must resolve to that exact contract value —
this is the mechanical no-new-arithmetic guard.
"""
from __future__ import annotations

_DP = 2  # money and scores both carry 2 decimal places


def _resolve(results: dict, path: str):
    cur = results
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def check_manifest(manifest, results) -> list[str]:
    errors: list[str] = []
    for entry in manifest:
        path, value = entry["path"], entry["value"]
        try:
            contract = _resolve(results, path)
        except KeyError:
            errors.append(f"unknown path: {path}")
            continue
        if contract == "PENDING":
            errors.append(f"figure is PENDING, must not appear in an artifact: {path}")
            continue
        if isinstance(contract, dict):
            errors.append(f"path resolves to a group, not a figure: {path}")
            continue
        if round(float(value), _DP) != round(float(contract), _DP):
            errors.append(f"value mismatch at {path}: {value} != {contract}")
    return errors


def verify(manifest, results) -> bool:
    return not check_manifest(manifest, results)
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/python -m pytest engine/tests/test_artifact_check.py -v`
Expected: PASS (all six).

- [ ] **Step 5: Commit**

```bash
git add engine/artifact_check.py engine/tests/test_artifact_check.py
git commit -m "feat(engine): figure-manifest verifier for artifact generation"
```

---

## Task 4: `generate-artifact` skill + CFO audit template + sample artifact

**Files:**
- Create: `skills/generate-artifact/SKILL.md`
- Create: `skills/generate-artifact/cfo-audit-template.md`
- Create: `sample-pso-delivery/artifacts/cfo-audit.md`
- Create: `sample-pso-delivery/artifacts/cfo-audit.manifest.json`
- Test: `tests/test_data_contract.py` (append the end-to-end portion)

**Interfaces:**
- Consumes: `engine.run.build_results`, `engine.run.main`, `engine.trace.build_trace`, `engine.artifact_check.verify/check_manifest`.
- Produces: a committed sample audit + manifest the end-to-end test verifies; the skill that operators invoke.

- [ ] **Step 1: Write the failing end-to-end test**

Append to `tests/test_data_contract.py`:

```python
import json, shutil
from engine.run import main
from engine.artifact_check import check_manifest

SAMPLE_MODEL = REPO / "sample-pso-delivery" / "model"
SAMPLE_AUDIT = REPO / "sample-pso-delivery" / "artifacts" / "cfo-audit.md"
SAMPLE_MANIFEST = REPO / "sample-pso-delivery" / "artifacts" / "cfo-audit.manifest.json"

def test_sample_audit_verifies_against_freshly_built_contract(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(SAMPLE_MODEL, eng / "model")
    main([str(eng)])  # regenerate results.json + trace.json from the sample inputs
    results = json.loads((eng / "model" / "results.json").read_text())
    manifest = json.loads(SAMPLE_MANIFEST.read_text())
    assert check_manifest(manifest, results) == []

def test_sample_audit_prose_shows_each_manifest_figure():
    audit = SAMPLE_AUDIT.read_text(encoding="utf-8")
    manifest = json.loads(SAMPLE_MANIFEST.read_text())
    for entry in manifest:
        money = f"{round(float(entry['value'])):,}"  # e.g. 754000.0 -> "754,000"
        assert money in audit, f"audit prose missing figure {entry['path']} ({money})"
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_data_contract.py -v`
Expected: FAIL — sample artifact/manifest files absent.

- [ ] **Step 3: Create the committed sample manifest**

Use the sample's real Wave-1 cost figures (`sample-pso-delivery/model/results.json`). Write `sample-pso-delivery/artifacts/cfo-audit.manifest.json`:

```json
[
  {"value": 280000, "path": "costs.OPP-001.labor"},
  {"value": 70000, "path": "costs.OPP-001.change_mgmt"},
  {"value": 580000, "path": "costs.OPP-001.subtotal"},
  {"value": 174000, "path": "costs.OPP-001.contingency"},
  {"value": 754000, "path": "costs.OPP-001.total"},
  {"value": 1305460, "path": "wave1_aggregate.investment_point"}
]
```

- [ ] **Step 4: Create the committed sample audit `cfo-audit.md`**

Render the CFO "show your work" view so each manifest figure's comma-formatted value appears. Example block (use the trace steps verbatim):

```markdown
# CFO Audit — Wave 1 (sample engagement)

> Every figure traces to the engine. Source: `model/results.json` + `model/trace.json` (contract v1.0).

## OPP-001 — Status Report Assembly Assistant

| Figure | inputs × formula = result | Source |
|---|---|---|
| Labor | 1,400 hrs × $200 = **$280,000** | `model/costs.json#OPP-001.labor_hours`, `.labor_rate` |
| Change mgmt | $280,000 × 0.25 = **$70,000** | `model/costs.json#OPP-001.change_mgmt_pct` |
| Subtotal | 280,000 + 80,000 + 150,000 + 70,000 = **$580,000** | cost_structure |
| Contingency | $580,000 × 0.30 = **$174,000** | `model/costs.json#OPP-001.contingency_pct` |
| **Total** | 580,000 + 174,000 = **$754,000** | cost_structure |

## Wave-1 investment (point estimate)

Sum of member initiative totals = **$1,305,460** (`wave1_aggregate.investment_point`).
```

- [ ] **Step 5: Write `skills/generate-artifact/cfo-audit-template.md`**

A prose template instructing how to render the audit from `trace.json`: one block per figure, `inputs × formula = result` pulled from the trace's `steps`, money shown as `$NNN,NNN`, a `Source` citation from each input's `source` path, and PENDING figures rendered "Pending — awaiting `<input>`". No literal numbers in the template (it is a pattern).

- [ ] **Step 6: Write `skills/generate-artifact/SKILL.md`**

Frontmatter exactly:

```markdown
---
name: ai-process-assessment:generate-artifact
description: On-demand artifact generation from the verified data contract. On a plain-language request ("give me the CFO audit", "a one-pager", "this as a spreadsheet"), regenerates the engine contract, renders the artifact referencing only contract figures, builds a figure manifest, and verifies it before emitting — never inventing or re-deriving a number. Ships the built-in CFO show-your-work audit template.
---
```

Body must specify the render loop:
1. Resolve the engagement folder (from `scope.md`'s `Engagement folder:` field, like `building-deliverable`).
2. **Always regenerate the contract first:** run `python3 <engine_root>/engine/run.py <folder>/` (idempotent; guarantees fresh `results.json` + `trace.json`). Do NOT mtime-check — the engine is cheap and the repo is sync-prone.
3. Load `model/results.json` + `model/trace.json`.
4. Render the requested artifact referencing figures **by contract path**, never typing a literal; for the audit use `cfo-audit-template.md`.
5. Build a figure manifest (`[{"value","path"}]`) of every number in the artifact (values in stored numeric form).
6. Verify: `PYTHONPATH="<engine_root>" python3 -c "from engine.artifact_check import check_manifest; ..."` — block emission on any error; a PENDING figure must not appear.
7. Emit the text floor (`<folder>/artifacts/<name>.md|.csv|.html`) + the `.manifest.json`. For a binary (`.xlsx`/`.pptx`/`.docx`/`.pdf`), hand the verified text payload + manifest to the host surface's file-creation; the binary is rendered 1:1 from already-verified values (the plugin adds no binary writer).

Use the `<engine_root>` / abs-path command conventions already used across the numeric skills.

- [ ] **Step 7: Run the end-to-end tests**

Run: `.venv/bin/python -m pytest tests/test_data_contract.py -v`
Expected: PASS (contract-doc + both sample-audit tests).

- [ ] **Step 8: Commit**

```bash
git add skills/generate-artifact/ sample-pso-delivery/artifacts/ tests/test_data_contract.py
git commit -m "feat(skill): generate-artifact + CFO audit template + sample"
```

---

## Task 5: Wiring — skill registry, Conductor, CHANGELOG

**Files:**
- Modify: `tests/test_skills.py` (allowlist + count)
- Modify: `skills/conducting-engagement/SKILL.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: a green `tests/test_skills.py` with `generate-artifact` registered as a non-phase skill.

- [ ] **Step 1: Update the failing guard expectations**

`generate-artifact` is a standalone non-phase skill, so `tests/test_skills.py` must allow it and bump the count. Edit:

```python
ALLOWLIST_NON_PHASE = {
    "ai-process-assessment:using-methodology",
    "ai-process-assessment:running-sample-engagement",
    "ai-process-assessment:generating-sample-intake",
    "ai-process-assessment:building-checkpoint",
    "ai-process-assessment:conducting-engagement",
    "ai-process-assessment:generate-artifact",
}
```

and:

```python
def test_skill_count(methodology):
    # 14 phase skills + 6 allow-listed non-phase skills (incl. conductor + generate-artifact).
    assert len(methodology.skills) == 20
```

- [ ] **Step 2: Run the skill guards**

Run: `.venv/bin/python -m pytest tests/test_skills.py -v`
Expected: PASS (Task 4 created the well-formed SKILL.md; allowlist + count now match).

- [ ] **Step 3: Register the capability in `conducting-engagement`**

In `skills/conducting-engagement/SKILL.md`, add to the Touchpoint taxonomy / Execution model a should-confirm capability: once `results.json` exists, the Conductor may offer to generate any requested artifact via `ai-process-assessment:generate-artifact` (the on-demand path). Add one line to the **Can-infer / Should-confirm** surface noting artifacts are produced on demand from the verified contract, never by hand. Do not alter the keystone.

- [ ] **Step 4: Add the CHANGELOG entry (no version bump)**

Under `## [Unreleased]` → `### Added` in `CHANGELOG.md`:

```markdown
- **Verifiable data contract + on-demand artifacts.** The engine now emits `model/trace.json` — per-figure provenance (`inputs × formula = result` + source) for every number in `results.json`, documented as a versioned public contract (`docs/data-contract.md`, v1.0). A new `generate-artifact` skill renders any requested artifact (CFO show-your-work audit, one-pager, CSV) from that contract under a mechanical no-new-arithmetic guard; binary formats (`.xlsx`/`.pptx`/`.docx`/`.pdf`) are produced by the host surface, so the plugin stays pure-stdlib.
```

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — all prior tests plus the new trace/verifier/contract tests; `results.json` golden unchanged.

- [ ] **Step 6: Commit**

```bash
git add tests/test_skills.py skills/conducting-engagement/SKILL.md CHANGELOG.md
git commit -m "feat(wiring): register generate-artifact; document contract in CHANGELOG"
```

---

## Self-Review notes (for the implementer/reviewer)

- **Spec coverage:** Task 1 = §3 (trace) + §3.4 formulas; Task 2 = §2.1 paths + §5 versioning + doc; Task 3 = §2.2 manifest + §4.2 verifier; Task 4 = §4.1 audit template + §4.3 render-time guard + §6 test 5; Task 5 = §5 lifecycle wiring. §4.4 (binary boundary) is prose-only in the SKILL.md (no plugin code, by design).
- **`results.json` byte-stability** is guarded by the untouched `engine/tests/test_run.py` golden assertions (Task 1, Step 6).
- **The orchestration mirror** between `run.build_results` and `trace.build_trace` is intentional duplication, guarded by `test_trace_covers_results`. Do not flag it as accidental.
- **Keystone is untouched:** `trace.json` is deliberately NOT added to the Engagement Folder Convention list (would require editing the verbatim-synced keystone).
```
