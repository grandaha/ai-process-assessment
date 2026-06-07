import json
import shutil
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
        # formulas emits keys like "'[fm.xlsx]WAVE-1 AGGREGATE'!B2"; match on the
        # sheet-name + cell suffix (sheet name may be prefixed by [workbook]).
        for k, v in sol.items():
            ku = k.upper()
            if ku.endswith(f"{sheet.upper()}'!{a1}") or ku.endswith(f"{sheet.upper()}!{a1}"):
                return float(v.value[0, 0])
        raise KeyError(f"{sheet}!{a1}")

    # Wave-1 aggregate investment low/high must equal results.json.
    inv = res["wave1_aggregate"]["investment"]
    assert cell("Wave-1 Aggregate", "B2") == pytest.approx(inv["low"])
    assert cell("Wave-1 Aggregate", "C2") == pytest.approx(inv["high"])
    av = res["wave1_aggregate"]["value"]
    assert cell("Wave-1 Aggregate", "B3") == pytest.approx(av["low"])
    assert cell("Wave-1 Aggregate", "C3") == pytest.approx(av["high"])
    pb = res["wave1_aggregate"]["payback_years"]
    assert cell("Wave-1 Aggregate", "B4") == pytest.approx(pb["low"], abs=0.01)
    assert cell("Wave-1 Aggregate", "C4") == pytest.approx(pb["high"], abs=0.01)


def test_workbook_aggregate_matches_results_when_one_initiative_pending(tmp_path):
    # Break OPP-002's labor_hours -> its cost is PENDING -> excluded from aggregate.
    model = tmp_path / "model"
    shutil.copytree(FIXTURE, model)
    costs = json.loads((model / "costs.json").read_text())
    for c in costs:
        if c["opp_id"] == "OPP-002":
            c["labor_hours"] = None
    (model / "costs.json").write_text(json.dumps(costs))

    inp = load_inputs(model)
    res = build_results(model)
    # results.json must exclude OPP-002 from the investment aggregate.
    assert res["costs"]["OPP-002"]["rom"] == "PENDING"
    inv = res["wave1_aggregate"]["investment"]
    assert inv == {"low": 155_250.0, "high": 465_750.0}  # OPP-001 only

    out = tmp_path / "financial-model.xlsx"
    write_workbook(inp, res, out)
    xl = formulas.ExcelModel().loads(str(out)).finish()
    sol = xl.calculate()

    def cell(sheet, a1):
        for k, v in sol.items():
            ku = k.upper()
            if ku.endswith(f"{sheet.upper()}'!{a1}") or ku.endswith(f"{sheet.upper()}!{a1}"):
                return float(v.value[0, 0])
        raise KeyError(f"{sheet}!{a1}")

    # Workbook aggregate must equal results.json (OPP-002 PENDING -> ignored by SUM).
    assert cell("Wave-1 Aggregate", "B2") == pytest.approx(inv["low"])
    assert cell("Wave-1 Aggregate", "C2") == pytest.approx(inv["high"])
