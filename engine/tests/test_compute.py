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
