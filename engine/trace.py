"""Per-figure provenance for results.json — the audit trace. No arithmetic here:
every number comes from engine.compute's returned values or its declared inputs.
trace.py only formats the human-readable step strings.
"""
from __future__ import annotations

from engine.compute import (
    cost_structure, initiative_rom, payback, score_composite,
    value_range, wave1_aggregate, wave1_point,
)
from engine.model import PENDING, Range, load_inputs

CONTRACT_VERSION = "1.0"


def _num(x):
    """Render a number without a trailing .0 for whole values (for step strings)."""
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _inp(name, value, file, key, field):
    return {"name": name, "value": value, "source": f"model/{file}.json#{key}.{field}"}


def _pending(formula):
    return {"formula": formula, "result": PENDING}


def _value_prov(opp, v, base_volume, volume):
    # Mirror compute.value_range's guard exactly: PENDING if ANY of the four is None.
    if None in (v.improvement_low, v.improvement_high, volume, v.rate):
        return _pending("value_range")
    r = value_range(v.improvement_low, v.improvement_high, volume, v.rate)
    return {
        "formula": "value_range", "result": {"low": r.low, "high": r.high},
        "inputs": [
            _inp("improvement_low", v.improvement_low, "value", opp, "improvement_low"),
            _inp("improvement_high", v.improvement_high, "value", opp, "improvement_high"),
            _inp("base_volume", base_volume, "baselines", v.process_id, "volume"),
            _inp("volume_fraction", v.volume_fraction, "value", opp, "volume_fraction"),
            _inp("rate", v.rate, "value", opp, "rate"),
        ],
        "steps": [
            f"volume={_num(base_volume)} × {_num(v.volume_fraction)} = {_num(volume)}",
            f"low={_num(v.improvement_low)} × {_num(volume)} × {_num(v.rate)} = {_num(r.low)}",
            f"high={_num(v.improvement_high)} × {_num(volume)} × {_num(v.rate)} = {_num(r.high)}",
        ],
    }


def _score_prov(opp, s):
    result = score_composite(s.dimensions)
    if result == PENDING:
        return _pending("score_composite")
    dims = " + ".join(str(_num(d)) for d in s.dimensions)
    return {
        "formula": "score_composite", "result": result,
        "inputs": [_inp("dimensions", list(s.dimensions), "scores", opp, "dimensions")],
        "steps": [f"score=({dims}) / 6 = {result}"],
    }


def _cost_prov(opp, c, cb):
    if cb == PENDING:
        return {k: _pending("cost_structure") for k in
                ("labor", "tech_cost", "integration_cost", "change_mgmt",
                 "subtotal", "contingency", "total")}
    src = lambda field: _inp(field, getattr(c, field), "costs", opp, field)
    return {
        "labor": {"formula": "cost_structure", "result": cb.labor,
                  "inputs": [src("labor_hours"), src("labor_rate")],
                  "steps": [f"labor={_num(c.labor_hours)} × {_num(c.labor_rate)} = {_num(cb.labor)}"]},
        "change_mgmt": {"formula": "cost_structure", "result": cb.change_mgmt,
                        "inputs": [src("change_mgmt_pct")],
                        "steps": [f"change_mgmt={_num(cb.labor)} × {_num(c.change_mgmt_pct)} = {_num(cb.change_mgmt)}"]},
        "tech_cost": {"formula": "cost_structure", "result": cb.tech_cost,
                      "inputs": [src("tech_cost")], "steps": [f"tech_cost={_num(cb.tech_cost)}"]},
        "integration_cost": {"formula": "cost_structure", "result": cb.integration_cost,
                             "inputs": [src("integration_cost")],
                             "steps": [f"integration_cost={_num(cb.integration_cost)}"]},
        "subtotal": {"formula": "cost_structure", "result": cb.subtotal,
                     "inputs": [src("labor_hours"), src("labor_rate"), src("tech_cost"),
                                src("integration_cost"), src("change_mgmt_pct")],
                     "steps": [f"subtotal={_num(cb.labor)} + {_num(cb.tech_cost)} + "
                               f"{_num(cb.integration_cost)} + {_num(cb.change_mgmt)} = {_num(cb.subtotal)}"]},
        "contingency": {"formula": "cost_structure", "result": cb.contingency,
                        "inputs": [src("contingency_pct")],
                        "steps": [f"contingency={_num(cb.subtotal)} × {_num(c.contingency_pct)} = {_num(cb.contingency)}"]},
        "total": {"formula": "cost_structure", "result": cb.total,
                  "inputs": [src("contingency_pct")],
                  "steps": [f"total={_num(cb.subtotal)} + {_num(cb.contingency)} = {_num(cb.total)}"]},
    }


def _rom_prov(cb, rom):
    if rom == PENDING:
        return _pending("initiative_rom")
    return {
        "formula": "initiative_rom", "result": {"low": rom.low, "high": rom.high},
        "inputs": [{"name": "total", "value": cb.total, "source": "results:total"}],
        "steps": [f"low={_num(cb.total)} × 0.5 = {_num(rom.low)}",
                  f"high={_num(cb.total)} × 1.5 = {_num(rom.high)}"],
    }


def build_trace(model_dir) -> dict:
    inp = load_inputs(model_dir)
    wave1 = [i.opp_id for i in inp.initiatives if i.wave == 1]

    value = {}
    for opp, v in inp.value.items():
        b = inp.baselines.get(v.process_id)
        base_volume = b.volume if b is not None else None
        volume = None if base_volume is None else base_volume * v.volume_fraction
        value[opp] = _value_prov(opp, v, base_volume, volume)

    scores = {opp: _score_prov(opp, s) for opp, s in inp.scores.items()}

    costs = {}
    rom_by_opp, total_by_opp = {}, {}
    for opp, c in inp.costs.items():
        cb = cost_structure(c.labor_hours, c.labor_rate, c.tech_cost,
                            c.integration_cost, c.change_mgmt_pct, c.contingency_pct)
        rom = initiative_rom(cb)
        rom_by_opp[opp] = rom
        total_by_opp[opp] = PENDING if cb == PENDING else cb.total
        block = _cost_prov(opp, c, cb)
        block["rom"] = _rom_prov(cb, rom)
        costs[opp] = block

    baselines = {
        pid: {field: {"formula": "passthrough", "result": getattr(b, field),
                      "source": f"model/baselines.json#{pid}.{field}"}
              for field in ("volume", "cycle_time_median", "cycle_time_p90", "error_rate", "fte")}
        for pid, b in inp.baselines.items()
    }

    investment = wave1_aggregate([rom_by_opp.get(o, PENDING) for o in wave1])
    investment_point = wave1_point([total_by_opp.get(o, PENDING) for o in wave1])
    value_ranges = []
    for o in wave1:
        vp = value.get(o, {}).get("result")
        value_ranges.append(Range(vp["low"], vp["high"]) if isinstance(vp, dict) else PENDING)
    annual_value = wave1_aggregate(value_ranges)
    pb = payback(investment, annual_value)

    def agg_prov(formula, result, members):
        if result == PENDING:
            return _pending(formula)
        if isinstance(result, Range):
            res = {"low": result.low, "high": result.high}
        else:
            res = result
        return {"formula": formula, "result": res,
                "inputs": [{"name": "wave1_members", "value": members, "source": "results:wave1"}],
                "steps": [f"{formula} over Wave-1 members {members}"]}

    wave1_aggregate_prov = {
        "investment": agg_prov("wave1_aggregate", investment, wave1),
        "investment_point": agg_prov("wave1_point", investment_point, wave1),
        "value": agg_prov("wave1_aggregate", annual_value, wave1),
        "payback_years": agg_prov("payback", pb, wave1),
    }

    return {
        "contract_version": CONTRACT_VERSION,
        "value": value, "scores": scores, "costs": costs,
        "baselines": baselines, "wave1_aggregate": wave1_aggregate_prov,
    }
