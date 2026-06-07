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
