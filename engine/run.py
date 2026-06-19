"""CLI / module entry: read model/*.json -> compute -> write results.json + .xlsx.

This is the only I/O boundary. Usage: python -m engine.run <engagement-folder>/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.compute import (
    AACE_CLASS5_LABEL, cost_structure, initiative_rom, payback,
    score_composite, value_range, wave1_aggregate, wave1_point,
)
from engine.model import PENDING, Range, load_inputs
from engine.workbook import write_workbook


def _range_out(r):
    return PENDING if r == PENDING else {"low": r.low, "high": r.high}


def build_results(model_dir) -> dict:
    inp = load_inputs(model_dir)
    wave1 = [i.opp_id for i in inp.initiatives if i.wave == 1]

    value = {}
    for opp, v in inp.value.items():
        b = inp.baselines.get(v.process_id)
        base_vol = b.volume if b is not None else None
        volume = None if base_vol is None else base_vol * v.volume_fraction
        value[opp] = _range_out(value_range(v.improvement_low, v.improvement_high,
                                            volume, v.rate))

    scores = {opp: score_composite(s.dimensions) for opp, s in inp.scores.items()}

    costs = {}
    rom_by_opp = {}
    total_by_opp = {}
    for opp, c in inp.costs.items():
        cb = cost_structure(c.labor_hours, c.labor_rate, c.tech_cost,
                            c.integration_cost, c.change_mgmt_pct, c.contingency_pct)
        rom = initiative_rom(cb)
        rom_by_opp[opp] = rom
        total_by_opp[opp] = PENDING if cb == PENDING else cb.total
        if cb == PENDING:
            costs[opp] = {"total": PENDING, "rom": PENDING, "rom_label": AACE_CLASS5_LABEL}
        else:
            costs[opp] = {
                "labor": cb.labor, "tech_cost": cb.tech_cost,
                "integration_cost": cb.integration_cost, "change_mgmt": cb.change_mgmt,
                "subtotal": cb.subtotal, "contingency": cb.contingency, "total": cb.total,
                "rom": _range_out(rom), "rom_label": AACE_CLASS5_LABEL,
            }

    investment = wave1_aggregate([rom_by_opp.get(o, PENDING) for o in wave1])
    investment_point = wave1_point([total_by_opp.get(o, PENDING) for o in wave1])
    value_ranges = []
    for o in wave1:
        vr = value.get(o, PENDING)
        value_ranges.append(PENDING if vr == PENDING else Range(vr["low"], vr["high"]))
    annual_value = wave1_aggregate(value_ranges)
    pb = payback(investment, annual_value)

    return {
        "value": value,
        "scores": scores,
        "costs": costs,
        "baselines": {
            pid: {
                "volume": b.volume, "cycle_time_median": b.cycle_time_median,
                "cycle_time_p90": b.cycle_time_p90, "error_rate": b.error_rate,
                "fte": b.fte, "source": b.source,
            }
            for pid, b in inp.baselines.items()
        },
        "wave1_aggregate": {
            "investment": _range_out(investment),
            "investment_point": investment_point,
            "value": _range_out(annual_value),
            "payback_years": _range_out(pb),
        },
    }


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    flags = {a for a in argv if a.startswith("--")}
    positional = [a for a in argv if not a.startswith("--")]
    if not positional:
        print("usage: python -m engine.run <engagement-folder>/ [--no-workbook]", file=sys.stderr)
        return 2
    engagement = Path(positional[0])
    model_dir = engagement / "model"
    results = build_results(model_dir)
    (model_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if "--no-workbook" not in flags:
        write_workbook(load_inputs(model_dir), results, engagement / "financial-model.xlsx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
