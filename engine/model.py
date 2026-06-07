"""Input + result schemas and the shared Range/PENDING types. No I/O lives here."""
from __future__ import annotations

from dataclasses import dataclass

# Sentinel for a result that cannot be computed because an input is missing.
# Never replaced by a fabricated number — surfaced as-is in results.json and the workbook.
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
