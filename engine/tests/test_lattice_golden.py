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
    b = inp.baselines.get(v.process_id)
    volume = None if b is None or b.volume is None else b.volume * v.volume_fraction
    return dict(improvement_low=v.improvement_low, improvement_high=v.improvement_high,
                volume=volume, rate=v.rate)


def _cost_args(inp, opp):
    c = inp.costs[opp]
    return dict(labor_hours=c.labor_hours, labor_rate=c.labor_rate,
                tech_cost=c.tech_cost, integration_cost=c.integration_cost,
                change_mgmt_pct=c.change_mgmt_pct, contingency_pct=c.contingency_pct)
