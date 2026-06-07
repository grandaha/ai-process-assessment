"""Pure formula functions — the single source of formula truth. No I/O, no LLM.

Every methodology calculation site routes through one of these functions. A missing
required input returns PENDING (never a fabricated number).
"""
from __future__ import annotations

from engine.model import PENDING, Range

_MONEY_DP = 2


def _money(x: float) -> float:
    return round(x, _MONEY_DP)


def value_range(improvement_low, improvement_high, volume, rate):
    """Value-hypothesis range: improvement-fraction × volume × rate (P5).

    Returns PENDING if any input is None.
    """
    if None in (improvement_low, improvement_high, volume, rate):
        return PENDING
    return Range(
        _money(improvement_low * volume * rate),
        _money(improvement_high * volume * rate),
    )
