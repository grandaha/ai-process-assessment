from engine.model import PENDING, Range


def test_range_holds_low_and_high():
    r = Range(low=10.0, high=20.0)
    assert r.low == 10.0
    assert r.high == 20.0


def test_range_is_frozen():
    import dataclasses
    import pytest
    r = Range(1.0, 2.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.low = 5.0  # type: ignore[misc]


def test_pending_is_the_sentinel_string():
    assert PENDING == "PENDING"
