"""Pure formula functions — the single source of formula truth. No I/O, no LLM.

Every methodology calculation site routes through one of these functions. A missing
required input returns PENDING (never a fabricated number).
"""
from __future__ import annotations

from engine.model import CostBlock, PENDING, Range

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


def score_composite(dimensions):
    """Composite score = mean of exactly six dimensions, rounded to 2 dp (P6)."""
    if dimensions is None or any(d is None for d in dimensions):
        return PENDING
    if len(dimensions) != 6:
        raise ValueError(f"expected 6 dimensions, got {len(dimensions)}")
    return round(sum(dimensions) / 6, 2)


def cost_structure(labor_hours, labor_rate, tech_cost, integration_cost,
                   change_mgmt_pct, contingency_pct):
    """Cost roll-up for an initiative (P8.5/P9).

    labor = hours*rate ; change_mgmt = labor*pct ;
    subtotal = labor + tech + integration + change_mgmt ;
    contingency = subtotal*pct ; total = subtotal + contingency.
    Returns PENDING if any input is None.
    """
    args = (labor_hours, labor_rate, tech_cost, integration_cost,
            change_mgmt_pct, contingency_pct)
    if any(a is None for a in args):
        return PENDING
    labor = labor_hours * labor_rate
    change_mgmt = labor * change_mgmt_pct
    subtotal = labor + tech_cost + integration_cost + change_mgmt
    contingency = subtotal * contingency_pct
    total = subtotal + contingency
    return CostBlock(
        labor=_money(labor),
        tech_cost=_money(tech_cost),
        integration_cost=_money(integration_cost),
        change_mgmt=_money(change_mgmt),
        subtotal=_money(subtotal),
        contingency=_money(contingency),
        total=_money(total),
    )
