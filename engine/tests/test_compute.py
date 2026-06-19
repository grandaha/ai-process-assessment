import pytest

from engine.compute import value_range
from engine.model import PENDING, Range


def test_value_range_multiplies_improvement_by_volume_by_rate():
    # low  = 0.2 * 1000 * 50 = 10_000 ; high = 0.4 * 1000 * 50 = 20_000
    assert value_range(0.2, 0.4, 1000, 50) == Range(10_000.0, 20_000.0)


def test_value_range_rounds_money_to_two_decimals():
    r = value_range(0.333, 0.667, 100, 3)
    assert r.low == pytest.approx(99.9)    # 0.333*100*3 = 99.9
    assert r.high == pytest.approx(200.1)  # 0.667*100*3 = 200.1


from engine.compute import score_composite


def test_score_composite_is_mean_of_six_dimensions():
    assert score_composite([3, 4, 5, 2, 4, 3]) == 3.5  # 21/6 = 3.5


def test_score_composite_rounds_to_two_decimals():
    assert score_composite([4, 4, 4, 4, 4, 5]) == 4.17  # 25/6 = 4.1666...


def test_score_composite_requires_exactly_six_dimensions():
    with pytest.raises(ValueError):
        score_composite([3, 4, 5])


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


from engine.compute import AACE_CLASS5_LABEL, initiative_rom


def test_initiative_rom_is_plus_minus_fifty_percent_of_total():
    cb = cost_structure(800, 200, 40_000, 30_000, 0.25, 0.15)  # total 310_500
    rom = initiative_rom(cb)
    assert rom == Range(155_250.0, 465_750.0)


def test_initiative_rom_passes_pending_through():
    assert initiative_rom(PENDING) == PENDING


def test_aace_label_text():
    assert AACE_CLASS5_LABEL == "ROM estimate, AACE Class 5 (±50%)"


from engine.compute import wave1_aggregate


def test_wave1_aggregate_sums_lows_and_highs():
    agg = wave1_aggregate([Range(100, 300), Range(200, 600)])
    assert agg == Range(300.0, 900.0)


def test_wave1_aggregate_skips_pending_members_but_flags_via_empty():
    # PENDING members are excluded from the sum; an all-PENDING list returns PENDING.
    assert wave1_aggregate([PENDING, PENDING]) == PENDING
    assert wave1_aggregate([Range(100, 300), PENDING]) == Range(100.0, 300.0)


def test_wave1_aggregate_empty_list_is_pending():
    assert wave1_aggregate([]) == PENDING


from engine.compute import wave1_point


def test_wave1_point_sums_member_totals():
    # Point estimate = sum of member totals; equals the midpoint of the ±50% band.
    assert wave1_point([310_500.0, 144_900.0]) == 455_400.0


def test_wave1_point_skips_pending_members_but_empty_is_pending():
    assert wave1_point([PENDING, PENDING]) == PENDING
    assert wave1_point([]) == PENDING
    assert wave1_point([310_500.0, PENDING]) == 310_500.0


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
