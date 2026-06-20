"""Input + result schemas and the shared Range/PENDING types. No I/O lives here."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Sentinel for a result that cannot be computed because an input is missing.
# Never replaced by a fabricated number — surfaced as-is in results.json.
PENDING = "PENDING"


@dataclass(frozen=True)
class Range:
    low: float
    high: float


@dataclass(frozen=True)
class CostBlock:
    labor: float
    tech_cost: float
    integration_cost: float
    change_mgmt: float
    subtotal: float
    contingency: float
    total: float


@dataclass(frozen=True)
class ValueInput:
    opp_id: str
    improvement_low: float | None
    improvement_high: float | None
    process_id: str | None
    volume_fraction: float
    rate: float | None

    @classmethod
    def from_dict(cls, d):
        # An absent key OR an explicit JSON null both mean "whole process" (1.0);
        # a literal 0.0 is preserved. `.get(k, 1.0)` mishandles explicit null,
        # and `... or 1.0` would wrongly coalesce a valid 0.0.
        fraction = d.get("volume_fraction")
        fraction = 1.0 if fraction is None else fraction
        return cls(d["opp_id"], d.get("improvement_low"), d.get("improvement_high"),
                   d.get("process_id"), fraction, d.get("rate"))


@dataclass(frozen=True)
class ScoreInput:
    opp_id: str
    dimensions: list

    @classmethod
    def from_dict(cls, d):
        dims = d.get("dimensions") or []
        if len(dims) != 6:
            raise ValueError(f"{d.get('opp_id')}: expected 6 dimensions, got {len(dims)}")
        return cls(d["opp_id"], list(dims))


@dataclass(frozen=True)
class CostInput:
    opp_id: str
    labor_hours: float | None
    labor_rate: float | None
    tech_cost: float | None
    integration_cost: float | None
    change_mgmt_pct: float | None
    contingency_pct: float | None

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("labor_hours"), d.get("labor_rate"),
                   d.get("tech_cost"), d.get("integration_cost"),
                   d.get("change_mgmt_pct"), d.get("contingency_pct"))


@dataclass(frozen=True)
class BaselineInput:
    process_id: str
    volume: float | None
    cycle_time_median: float | None
    cycle_time_p90: float | None
    error_rate: float | None
    fte: float | None
    source: str | None

    @classmethod
    def from_dict(cls, d):
        return cls(d["process_id"], d.get("volume"), d.get("cycle_time_median"),
                   d.get("cycle_time_p90"), d.get("error_rate"), d.get("fte"),
                   d.get("source"))


@dataclass(frozen=True)
class Initiative:
    opp_id: str
    name: str
    wave: int

    @classmethod
    def from_dict(cls, d):
        return cls(d["opp_id"], d.get("name", d["opp_id"]), int(d.get("wave", 1)))


@dataclass(frozen=True)
class Inputs:
    initiatives: list
    value: dict
    scores: dict
    costs: dict
    baselines: dict


def _read_json(path: Path):
    import json
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs(model_dir) -> "Inputs":
    """Read model/*.json into validated dataclasses. Missing files load as empty."""
    model_dir = Path(model_dir)
    initiatives = [Initiative.from_dict(d) for d in _read_json(model_dir / "initiatives.json")]
    value = {d["opp_id"]: ValueInput.from_dict(d) for d in _read_json(model_dir / "value.json")}
    scores = {d["opp_id"]: ScoreInput.from_dict(d) for d in _read_json(model_dir / "scores.json")}
    costs = {d["opp_id"]: CostInput.from_dict(d) for d in _read_json(model_dir / "costs.json")}
    baselines = {d["process_id"]: BaselineInput.from_dict(d)
                 for d in _read_json(model_dir / "baselines.json")}
    return Inputs(initiatives=initiatives, value=value, scores=scores, costs=costs,
                  baselines=baselines)
