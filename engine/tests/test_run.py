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
