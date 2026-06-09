import json

import pytest

from engine.model import (
    BaselineInput, CostInput, ScoreInput, ValueInput, load_inputs,
)


def test_baseline_input_from_dict():
    bi = BaselineInput.from_dict({
        "process_id": "PROC-01", "volume": 8000, "cycle_time_median": 5,
        "cycle_time_p90": 12, "error_rate": 0.03, "fte": 2.4,
        "source": "Ops interview R2",
    })
    assert bi.process_id == "PROC-01"
    assert bi.volume == 8000
    assert bi.fte == 2.4


def test_baseline_input_allows_missing_numeric_as_none():
    bi = BaselineInput.from_dict({"process_id": "PROC-09", "volume": None})
    assert bi.volume is None
    assert bi.source is None


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


def test_value_input_null_fraction_defaults_to_one():
    # An explicit JSON null must behave like an absent key (default 1.0),
    # not propagate None into the engine's volume multiplication.
    vi = ValueInput.from_dict({
        "opp_id": "OPP-001", "improvement_low": 0.5, "improvement_high": 0.7,
        "process_id": "PROC-01", "volume_fraction": None, "rate": 100,
    })
    assert vi.volume_fraction == 1.0


def test_value_input_preserves_zero_fraction():
    # A literal 0.0 is a real (if degenerate) value — it must survive, not
    # silently coalesce to 1.0 (which a bare `or 1.0` would do).
    vi = ValueInput.from_dict({
        "opp_id": "OPP-001", "improvement_low": 0.5, "improvement_high": 0.7,
        "process_id": "PROC-01", "volume_fraction": 0.0, "rate": 100,
    })
    assert vi.volume_fraction == 0.0


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
