# CFO Audit — Wave 1 (sample engagement)

> Every figure traces to the engine. Source: `model/results.json` + `model/trace.json` (contract v1.0).

## OPP-001 — Status Report Assembly Assistant

| Figure | inputs × formula = result | Source |
|---|---|---|
| Labor | 1,400 hrs × $200 = **$280,000** | `model/costs.json#OPP-001.labor_hours`, `.labor_rate` |
| Change mgmt | $280,000 × 0.25 = **$70,000** | `model/costs.json#OPP-001.change_mgmt_pct` |
| Subtotal | 280,000 + 80,000 + 150,000 + 70,000 = **$580,000** | cost_structure |
| Contingency | $580,000 × 0.30 = **$174,000** | `model/costs.json#OPP-001.contingency_pct` |
| **Total** | 580,000 + 174,000 = **$754,000** | cost_structure |

## Wave-1 investment (point estimate)

Sum of member initiative totals = **$1,305,460** (`wave1_aggregate.investment_point`).
