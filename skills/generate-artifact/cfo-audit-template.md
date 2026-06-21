# CFO Audit Template — "Show Your Work" View

This template describes how to render a CFO audit artifact from `trace.json`. Do not copy literal numbers from this file — every figure must be resolved from the engine contract at render time.

## Structure

The audit renders one block per initiative that has cost figures in `results.json`, followed by the Wave-1 aggregate summary.

### Per-initiative block

For each initiative with cost data, render a section heading with the initiative ID and name, then a table with one row per cost figure:

```
## <OPP-ID> — <initiative name>

| Figure | inputs × formula = result | Source |
|---|---|---|
| Labor | <labor_hours> hrs × $<labor_rate> = **$<labor>** | `model/costs.json#<OPP-ID>.labor_hours`, `.labor_rate` |
| Change mgmt | $<labor> × <change_mgmt_pct> = **$<change_mgmt>** | `model/costs.json#<OPP-ID>.change_mgmt_pct` |
| Subtotal | <labor> + <tech_cost> + <integration_cost> + <change_mgmt> = **$<subtotal>** | cost_structure |
| Contingency | $<subtotal> × <contingency_pct> = **$<contingency>** | `model/costs.json#<OPP-ID>.contingency_pct` |
| **Total** | <subtotal> + <contingency> = **$<total>** | cost_structure |
```

**Formatting rules:**
- All money values rendered as `$NNN,NNN` (comma-separated thousands, no decimal places for whole numbers).
- Each figure cell shows: input values × formula = **bold result**.
- The Source cell cites the `trace.json` step's `source` path for each input — use the dotted path exactly as it appears in the trace.
- A PENDING figure is rendered as: `Pending — awaiting \`<input path>\`` — do NOT include a PENDING value in the manifest or emit the artifact; block emission and report which input is missing.

### Wave-1 aggregate block

After all per-initiative blocks, render the aggregate:

```
## Wave-1 investment (point estimate)

Sum of member initiative totals = **$<investment_point>** (`wave1_aggregate.investment_point`).
```

The `investment_point` value is resolved from `results.json` at path `wave1_aggregate.investment_point`.

## Render loop

1. Load `model/results.json` and `model/trace.json`.
2. For each initiative in the trace with cost steps, resolve each figure by its contract path (e.g., `costs.OPP-001.labor`). Never type a literal number — always read from the resolved contract value.
3. Format money as `$NNN,NNN` using Python `f"${round(value):,}"` or equivalent.
4. Cite the `source` field from the matching trace step for each input.
5. Build the figure manifest: one entry per rendered number, `{"value": <stored numeric>, "path": "<dotted results path>"}`.
6. Run `artifact_check.check_manifest(manifest, results)` — if any errors are returned, block emission and report each error. Do not emit the artifact with unverified figures.
7. Write `<engagement>/artifacts/cfo-audit.md` and `<engagement>/artifacts/cfo-audit.manifest.json`.
