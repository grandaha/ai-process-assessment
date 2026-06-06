# Design — Deterministic Math Engine + Auditable Workbook

**Date:** 2026-06-05
**Status:** Approved design (pre-implementation)
**Author:** Dave Raffaele (with Claude)

---

## 1. Problem

Every number in a methodology engagement is currently produced by the model doing arithmetic in prose: value-hypothesis ranges (`improvement × volume × rate`), score composites (mean of six dimensions), cost roll-ups (`hours × rate`), and the Phase 9 business case (implementation labor, change-management %, contingency %, ROM ranges, Wave-1 aggregate, payback). LLM in-prose arithmetic is non-deterministic and error-prone, and the errors compound through multi-step calculations. The numbers cannot be trusted, audited, or independently re-derived.

## 2. Goal

Move **every calculation in the methodology** off the model and into a deterministic, unit-tested Python engine. Emit an auditable Excel workbook with **live cell formulas** so a reviewer (e.g. a skeptical CFO) can inspect and flex the math. Markdown deliverables cite computed results; they never compute.

## 3. Settled decisions

| Decision | Choice | Rationale |
|---|---|---|
| Workbook format | **Excel `.xlsx`** via `openpyxl` — single authoritative artifact | No auth, deterministic, portable, ships in the plugin, reproduces offline. Must round-trip cleanly into **Google Sheets** and **Apple Numbers** (see §6.4). An optional thin `--to-sheets` converter is in scope; a native Google Sheets *backend* is not (§11). |
| Math model | **Live cell formulas** | Inputs in cells; results are `=formulas`. Auditable and re-flexable, not just relocated. |
| Environment | **Code-execution required for any shipped number** | Determinism is the point. Methodology still runs without it but marks numbers "pending engine." |
| Scope | **Full engagement** — every calculation site | Per the directive: anywhere calculations are being done. |
| Source of truth | **Approach A — JSON model authoritative** | `model/*.json` is canonical; markdown and workbook are both derived. The single alternative (scrape existing extraction headers) leans on brittle bash parsing (bug #1) and keeps prose as a competing source. |

## 4. Core principle (the enforceable rule)

> **The model performs no arithmetic in prose, in any phase.** Every number is either (a) a directly-sourced input recorded as structured data, or (b) a value computed by the engine and read back from `results.json`. A figure that is neither is a defect the deliverable-gate must catch.

`model/*.json` is the single source of truth for every number. Markdown prose is narrative that *cites* computed results. The engine output (`results.json`) and the workbook (`financial-model.xlsx`) are both derived from the same inputs. The deliverable-gate enforces markdown ↔ `results.json` equality.

## 5. Calculation-site inventory

| Phase | Calculation today (LLM-in-prose) | After |
|---|---|---|
| 1 Scope | none | — |
| 2 Context | derived stat figures (e.g. "$2M per utilization point") | recorded as a model input and cited — not a prose multiplication (no dedicated skill rewrite; governed by the §4 rule) |
| 3 Tech inventory | none | — |
| 4 Baselines | derived volumes (`180×4=720/mo`), FTE roll-ups | engine |
| 5 Value hypothesis | `improvement × volume × rate` ranges | engine |
| 6 Scoring | composite = mean of 6 dimensions | engine |
| 7 Roadmap | capacity-load sums (if any) | engine |
| 8 Use case briefs | restated baseline/target figures | cite results |
| 8.5 Cost actuals | `hours × rate` | engine |
| 9 Business case | labor, change-mgmt %, contingency %, ROM ranges, aggregate, payback | engine |
| 10 Exec summary | restated headline figures | cite results (never recompute) |
| 11 Deliverable | restated figures in renderers | cite results |
| Gate A GRC | none | — |
| Gate B Deliverable-gate | — | **new:** determinism check (markdown == results.json) |

## 6. Architecture

### 6.1 Data flow

```
LLM elicits numbers ─► model/<phase>.json ─► python -m engine.run <engagement>/
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                         ▼                        ▼
                   model/results.json     financial-model.xlsx       validation
                   (canonical numbers)    (live formulas, tabs)      (schema + PENDING)
                          │
                          ▼
            LLM stamps figures from results.json into markdown prose
                          │
                          ▼
            deliverable-gate verifies markdown numbers == results.json
```

### 6.2 Components (small, single-purpose units)

| Unit | Purpose | I/O |
|---|---|---|
| `engine/model.py` | Input + result schemas (dataclasses): `Baseline`, `ValueInput`, `ScoreInput`, `CostInput`, `Initiative`, `Results`. Validation lives here. | none |
| `engine/compute.py` | Pure functions — the single source of formula truth. No I/O, no LLM. | none |
| `engine/workbook.py` | `openpyxl` writer: inputs as cells, everything else as live `=formulas`. | writes `.xlsx` |
| `engine/run.py` | CLI / module entry: read `model/*.json` → validate → compute → write `results.json` + `financial-model.xlsx`. The only I/O boundary. | reads/writes |
| `engine/tests/` | pytest golden-number suite incl. the Lattice sample fixture. | — |
| `requirements.txt` | `openpyxl`, `pytest`. | — |

### 6.3 Engine API (compute.py — illustrative signatures)

```python
def value_range(improvement_low, improvement_high, volume, rate) -> Range
def score_composite(dimensions: list[float]) -> float          # mean of 6, documented rounding
def cost_structure(hours, rate, change_mgmt_pct, contingency_pct) -> CostBlock
def initiative_rom(cost_block) -> Range                         # AACE Class 5 ±50% label attached
def wave1_aggregate(rom_ranges: list[Range]) -> Range
def payback(investment: Range, annual_value: Range) -> Range
```

Rules baked into the engine, not the LLM: AACE Class 5 (±50%) labels; change-management default 20–30% of confirmed labor; contingency 15–20% of subtotal; one-time vs recurring kept separate; **missing input → `PENDING` result, never a fabricated number** (moves the current `business-case-analyst` PENDING discipline into code).

### 6.4 Workbook layout (`financial-model.xlsx`)

Tabs: **Inputs** · **Value (P5)** · **Scores (P6)** · **Costs (P8.5)** · **Business Case (P9)** · **Wave-1 Aggregate**. Inputs are literal cells; every downstream tab uses `=formulas` referencing the Inputs tab (`=Inputs!B4*Inputs!C4`, `=SUM(...)`, `=investment/annual_value`). Opening the file recalculates; changing an input flows through. `engine/workbook.py` writes formula strings; `engine/compute.py` produces the canonical values for `results.json`; the two must agree (enforced by a test).

**Implementation note:** `openpyxl` writes formula *strings* and does **not** cache computed values — reading a formula cell back yields the string, not the result. The formula-vs-results equality test therefore evaluates the workbook with a formula evaluator (e.g. the `formulas` or `pycel` package) rather than reading cells. That evaluator is a test/CI dependency, not a runtime one.

**Cross-application compatibility (required, not optional).** The author of this engagement does not run Microsoft Excel; the `.xlsx` must open and recompute correctly in **Apple Numbers** (macOS, free) and **Google Sheets** (via import). Two concrete requirements: (1) use only formula functions common to Excel, Sheets, and Numbers — plain arithmetic, `SUM`, cell/sheet references; avoid Excel-only functions, named ranges, and tables; (2) set `workbook.calcPr.fullCalcOnLoad = True` so any of the three apps recalculates on open/import rather than showing stale/blank formula cells. A round-trip smoke check (open in Numbers; import into Sheets) is part of acceptance.

**Optional `--to-sheets` converter.** A thin post-hoc adapter that uploads the canonical `.xlsx` to Google Drive and lets Drive convert it to a native Google Sheet (Drive's `xlsx→Sheets` conversion preserves arithmetic formulas). This is a convenience layer on top of the one authoritative artifact — it is **not** a second formula-writing backend and introduces no second source of truth. Auth (Drive API) is required only for this optional step, never for the core engine.

## 7. Per-phase integration changes

- **Skills (P4, P5, P6, P8.5, P9):** add a step — after eliciting numbers, write the phase's `model/<phase>.json`, run `python -m engine.run`, and cite `results.json` in the markdown. Remove all in-prose arithmetic instructions.
- **`agents/business-case-analyst.md`:** stops computing. It composes prose around engine outputs; PENDING logic now lives in the engine.
- **`agents/opportunity-scorer.md`:** records 6 dimension scores to `model/scores.json`; composite comes from the engine, not the agent.
- **`skills/deliverable-gate/SKILL.md`:** new determinism check — every number in markdown deliverables must equal its `results.json` source; mismatch blocks the gate.
- **`skills/building-deliverable` + section-renderers:** pull headline figures from `results.json`; link `financial-model.xlsx` as a downloadable artifact in the HTML.
- **`skills/using-methodology/SKILL.md`:** document the no-prose-arithmetic rule, the `model/` layer, and the engine in the keystone.
- **Engagement folder convention:** add `model/` (inputs + `results.json`) and `financial-model.xlsx`.

## 8. Testing & trust

The engine is **tested code, not generated-per-run** — that is what earns trust. `engine/tests/` holds golden-number tests: known inputs → asserted outputs for each `compute.py` function, plus an integration test that runs the **Lattice PSO sample (#7)** end-to-end and asserts the business-case totals and payback. A formula change that breaks a golden number fails CI. A second test asserts workbook formula results equal `results.json` values.

## 9. Packaging / deployment impact

- Adds `engine/` and `requirements.txt`; `INSTALL.md` gains a Python-setup step (`pip install -r requirements.txt`).
- **Option A (Claude Code):** full path — Bash runs the engine.
- **Option B (Claude.ai Projects):** requires the analysis/code tool for numbers; without it, methodology runs but figures render "pending engine."
- Requires a code-execution environment for any shipped number (accepted decision).
- **No spreadsheet application is needed to *verify* the engine** — correctness is proven by the headless test suite (§8). Spreadsheet apps are only for *human* audit of the workbook, where Apple Numbers or a Google Sheets import suffice (no Microsoft Excel required).
- The optional `--to-sheets` converter adds a Drive-API dependency only when explicitly invoked.

## 10. Build order

1. `engine/model.py` + `compute.py` + golden tests — prove formulas against the Lattice sample. (No methodology wiring yet.)
2. `engine/workbook.py` + `run.py` — produce `results.json` + `.xlsx`; add the formula-vs-results equality test.
3. Wire phases one at a time (P9 first — highest value — then P8.5, P6, P5, P4), validating against the sample after each.
4. Deliverable-gate determinism check.
5. `building-deliverable` workbook link + `using-methodology` rule + `INSTALL.md` + version bump.
6. *(Optional, can defer)* `--to-sheets` converter + its Drive-API setup docs.

After step 2, run the cross-app round-trip smoke check: open `financial-model.xlsx` in Apple Numbers and import it into Google Sheets; confirm formulas recompute in both.

## 11. Out of scope

- A **native Google Sheets backend** (a second formula-writer that targets the Sheets API directly). The `.xlsx` is the single authoritative artifact; Sheets is reached by import or the optional `--to-sheets` converter, not by a parallel writer.
- NPV / discounted cash-flow modeling — the methodology stays ROM (AACE Class 5); the engine does not become a finance model.
- Replacing non-numeric extraction headers (`<!-- index -->` for type/flags) — only numeric data moves to the model.
- Phase 4 normalization (issue #6) — independent; this design works with either Phase-4 structure.

## 12. Acceptance criteria

- No methodology phase instructs the model to perform arithmetic in prose; all numbers trace to `model/*.json` (input) or `results.json` (computed).
- `engine/` computes value ranges, score composites, cost structures, ROM ranges, Wave-1 aggregate, and payback deterministically, with a passing golden-number suite including the Lattice integration test.
- A run produces `model/results.json` and `financial-model.xlsx` with live formulas; changing an Inputs cell reflows the downstream tabs.
- `financial-model.xlsx` formula results equal `results.json` values (tested headless, no spreadsheet app).
- `financial-model.xlsx` opens and recomputes correctly in **Apple Numbers** and after **Google Sheets import** — uses only cross-app formula functions and sets `fullCalcOnLoad`.
- The deliverable-gate blocks on any markdown figure that does not match `results.json`.
- Missing inputs render as `PENDING` in both `results.json` and the workbook — never as a fabricated number.
