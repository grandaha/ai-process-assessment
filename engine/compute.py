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
    # Round at each step from rounded predecessors so each displayed total
    # equals the sum of the rounded line items above it (no penny drift).
    labor = _money(labor_hours * labor_rate)
    change_mgmt = _money(labor * change_mgmt_pct)
    subtotal = _money(labor + tech_cost + integration_cost + change_mgmt)
    contingency = _money(subtotal * contingency_pct)
    total = _money(subtotal + contingency)
    return CostBlock(
        labor=labor,
        tech_cost=_money(tech_cost),
        integration_cost=_money(integration_cost),
        change_mgmt=change_mgmt,
        subtotal=subtotal,
        contingency=contingency,
        total=total,
    )


AACE_CLASS5_LABEL = "ROM estimate, AACE Class 5 (±50%)"


def initiative_rom(cost_block):
    """ROM range for an initiative: total ±50% (AACE Class 5).

    The label travels with the figure in results.json (see run.py).
    Returns PENDING if the cost block is PENDING.
    """
    if cost_block == PENDING:
        return PENDING
    return Range(_money(cost_block.total * 0.5), _money(cost_block.total * 1.5))


def wave1_aggregate(rom_ranges):
    """Aggregate Wave-1 range = sum of member ranges. PENDING members are excluded;
    an all-PENDING (or empty) list returns PENDING."""
    present = [r for r in rom_ranges if r != PENDING]
    if not present:
        return PENDING
    return Range(
        _money(sum(r.low for r in present)),
        _money(sum(r.high for r in present)),
    )


def wave1_point(totals):
    """Wave-1 point-estimate investment = sum of member initiative totals.

    The deterministic central estimate that sits at the midpoint of the ±50%
    ROM band (see ``wave1_aggregate``). Mirrors that function's membership rule:
    PENDING members are excluded; an all-PENDING (or empty) list returns PENDING.
    This gives the business case a sourced point total to cite instead of summing
    initiative totals in prose.
    """
    present = [t for t in totals if t != PENDING]
    if not present:
        return PENDING
    return _money(sum(present))


def payback(investment, annual_value):
    """Payback period as a range of years.

    best  = investment.low  / annual_value.high
    worst = investment.high / annual_value.low
    Returns PENDING if either input is PENDING or annual value is non-positive.
    """
    if investment == PENDING or annual_value == PENDING:
        return PENDING
    if annual_value.low <= 0 or annual_value.high <= 0:
        return PENDING
    return Range(
        round(investment.low / annual_value.high, 2),
        round(investment.high / annual_value.low, 2),
    )
