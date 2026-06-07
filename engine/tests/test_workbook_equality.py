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
    pb = res["wave1_aggregate"]["payback_years"]
    assert cell("Wave-1 Aggregate", "B4") == pytest.approx(pb["low"], abs=0.01)
    assert cell("Wave-1 Aggregate", "C4") == pytest.approx(pb["high"], abs=0.01)
