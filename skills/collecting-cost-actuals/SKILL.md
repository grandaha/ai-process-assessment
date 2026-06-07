---
name: ai-process-assessment:collecting-cost-actuals
description: Phase 8.5 — required gate between Phase 8 and Phase 9. Reads roadmap.md, usecase-briefs/_index.md + Wave 1 UC-NNN.md files, and scores/_index.md + per-initiative scores/OPP-NNN.md files to generate a stakeholder data collection worksheet, then walks the consultant through capturing labor rates, implementation hours, vendor quotes, and IT integration estimates. Writes cost-actuals.md to the engagement folder. Phase 9 will not run without this file.
updated: 2026-06-03T19:43
---

# Phase 8.5: Collecting Cost Actuals

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `roadmap.md` and `usecase-briefs/_index.md` — confirm both exist.
3. Read each Wave 1 UC-NNN.md file listed in `_index.md` to build the collection checklist.

Gate condition: `usecase-briefs/_index.md` must be present before proceeding.

## Role in the system

Produces `cost-actuals.md` by walking the consultant through cost data collection for each Wave 1 initiative. The consultant gathers data from stakeholders (IT, Finance, vendors) before or during this phase. The skill captures what is available, marks the rest PENDING, and writes the file. Phase 9 does not run without this file.

Business cases require real input. A figure labeled PENDING in the business case is honest. A fabricated figure labeled as an estimate is not.

## Gate condition

`usecase-briefs/_index.md` must exist in the engagement folder. This skill creates `cost-actuals.md`.

## Required source files

| File | What it provides |
|---|---|
| `roadmap.md` | Wave 1 initiative list, B/B/P per initiative, enabler list and owners |
| `usecase-briefs/_index.md` + Wave 1 `UC-NNN.md` files | Resolution and data requirements fields per initiative — identifies who does the build work. Read the index first to identify Wave 1 UC file names, then read only those individual files. |
| `scores/_index.md` + `scores/OPP-NNN.md` per Wave 1 initiative | B/B/P classification per initiative with rationale; read `scores/_index.md` to identify Wave 1 OPP-IDs, then read each `scores/OPP-NNN.md` for B/B/P detail |

If any of these three files is missing, halt and report which file is absent.

## Workflow

**Step 1 — Analysis pass**
Read all source files. For B/B/P data, read `scores/_index.md` to identify Wave 1 OPP-IDs, then read each `scores/OPP-NNN.md` for Build/Buy/Partner classification and rationale. For each Wave 1 initiative, determine:
- Labor type(s) involved: who does the build work (derived from the brief's Resolution and Data requirements fields — e.g., IT admin, enterprise AI team, domain specialist, PM)
- Whether B/B/P is Buy or Partner (requires vendor quote)
- Whether the initiative has enabler dependencies listed in roadmap.md (requires IT integration estimate)

Also compile the full list of enablers from roadmap.md with their named owners.

**Step 2 — Produce and surface the Data Collection Worksheet**

Generate a structured worksheet showing exactly what needs to be collected, from whom. Present it to the user before starting data capture. Use this format:

```
Data Collection Worksheet — [Engagement Name]

LABOR RATES — get from Finance or HR (fully burdened $/hr)
  □ [Role 1 — e.g., IT admin / systems configuration]
  □ [Role 2 — e.g., Enterprise AI / ML engineering team]
  □ [additional roles identified from briefs]

IMPLEMENTATION HOURS — get from the team lead named in each brief
  □ [OPP-NNN Initiative Title] — [labor type from brief] — owner: [named from roadmap.md or brief]
  □ [one item per Wave 1 initiative]

VENDOR QUOTES — get from Procurement or the vendor directly (Buy/Partner initiatives only)
  □ [OPP-NNN Initiative Title] — [vendor/product] — one-time cost + annual cost
  □ [one item per Buy or Partner initiative]

IT INTEGRATION ESTIMATES — get from IT/Engineering (for enablers with named dependencies)
  □ [Enabler ID — description] — hours estimate + one-time cost — owner: [named from roadmap.md]
  □ [one item per enabler]
```

After surfacing the worksheet, tell the user:

> "Collect what you can from the stakeholders above, then come back. I'll capture each data point and write cost-actuals.md. For anything you don't have yet, say 'pending' and I'll mark it — Phase 9 will surface those gaps clearly rather than estimate around them."

**Step 3 — Interactive data capture**

Walk through each section of the worksheet one at a time. For each line item:
- Name the item explicitly and state who it should come from
- Ask for the figure
- Accept a specific value or "pending" / "don't have it"
- If pending, record which stakeholder is the source

Do not rush. Do not skip items. Do not assume a value because one similar item was provided.

**Step 4 — Write cost-actuals.md**

Write `cost-actuals.md` to the engagement folder. Use the format below. Pre-populate with the engagement's actual initiative names, labor types, and owner names from the source files — not generic placeholders.

**Output rule:** Do NOT reproduce the contents of `cost-actuals.md` in this response. Confirm totals and PENDING item count only. State the file path — do not echo file content.

**Step 5 — Surface summary**

After writing, show the user:
- Count of confirmed vs. PENDING line items
- The specific PENDING items and who needs to provide them
- Statement: Phase 9 can proceed now. PENDING items will appear as flagged gaps in the business case, not as estimated figures.

## Recording captured costs for the engine

As each cost actual is confirmed, record it in structured form in the engagement's `model/costs.json` (one object per Wave-1 OPP-ID with `labor_hours`, `labor_rate`, `tech_cost`, `integration_cost`, `change_mgmt_pct`, `contingency_pct`). Any value not yet collected is recorded as `null` — it will render as PENDING in the business case and the workbook until supplied. Do not enter placeholder or estimated numbers in place of `null`. `cost-actuals.md` remains the human-readable record; `model/costs.json` is the engine's input.

## Output format of `cost-actuals.md`

```markdown
# Cost Actuals — [Engagement Name]

**Generated:** [YYYY-MM-DD]
**Collected by:** [name, if provided]

---

## Labor Rates (Fully Burdened $/hr)

| Role | Rate ($/hr) | Status | Source |
|---|---|---|---|
| [Role from briefs] | [figure or PENDING] | Confirmed / PENDING | [Finance / stakeholder name] |

---

## Initiative Implementation Hours

| Initiative | Labor type | Hours estimate | Status | Source |
|---|---|---|---|---|
| [OPP-NNN — Title] | [labor type from brief] | [hours or PENDING] | Confirmed / PENDING | [owner name] |

---

## Vendor Quotes

| Initiative | Vendor / product | One-time ($) | Annual ($) | Status | Quote date |
|---|---|---|---|---|---|
| [OPP-NNN — Title] | [vendor] | [figure or PENDING] | [figure or PENDING] | Confirmed / PENDING | [date or blank] |

---

## IT Integration Estimates

| Enabler | Work item | Labor (hrs) | One-time ($) | Status | Source |
|---|---|---|---|---|---|
| [Enabler ID] | [description] | [hours or PENDING] | [$ or PENDING] | Confirmed / PENDING | [IT lead name] |

---

## Override Notes

[Any additional actuals not captured in the tables above — each on its own line with amount, date, and source]
```

## Rationalization table

| Rationalization | Correct reframe |
|---|---|
| "We don't have time — just use benchmarks." | A business case on invented numbers is a liability, not a deliverable. The collection worksheet takes one stakeholder meeting. Fabricated figures take weeks to undo when Finance asks for the source. |
| "We can come back and update later." | Phase 9 surfaces PENDING gaps clearly. An honest PENDING is more defensible in a budget meeting than a fabricated range that collapses under one question. |
| "Close enough is fine for an estimate." | AACE Class 5 already gives ±50% tolerance. The point of collecting actuals is to narrow that range, not to validate made-up inputs. Real hours × real rates = a real estimate. |

## Phase checklist

- [ ] Confirm `usecase-briefs/_index.md` exists
- [ ] Confirm `roadmap.md` and `scores/_index.md` exist
- [ ] Complete analysis pass — identify labor types, Buy/Partner flags, enabler dependencies per initiative
- [ ] Surface Data Collection Worksheet to user; wait for acknowledgment before starting capture
- [ ] Complete interactive capture — all sections, all line items; no skipped items
- [ ] Write `cost-actuals.md` to engagement folder — pre-populated with engagement-specific names
- [ ] Surface confirmed vs. PENDING summary to user
- [ ] Confirm Phase 9 is authorized to proceed

## Chain to next skill

→ `ai-process-assessment:building-business-case` (Phase 9)

**Session boundary:** After Phase 9 is authorized to proceed, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:building-business-case` to begin Phase 9. Do not continue methodology work in this session.
