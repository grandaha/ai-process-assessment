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
