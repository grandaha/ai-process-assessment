---
name: ai-process-assessment:building-business-case
description: Phase 9 — produces a Wave 1 ROM business case (business-case.md) sourced from methodology artifacts. Not a financial model. Scoped to Wave 1 only — Wave 2 is directional, Wave 3 is intent.
---

# Phase 9: Building the Business Case

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read the following files and confirm each exists:
   - `cost-actuals.md`
   - `usecase-briefs/_index.md`
   - `roadmap.md`
   - `processes/_index.md`
   - `opportunities/_index.md`
   - `scores/_index.md`

Gate condition: All six files must be present. `cost-actuals.md` must have no unresolved PENDING items for Wave 1 initiatives.

## Deterministic math (engine-computed — no prose arithmetic)

Phase 9 performs **no arithmetic in prose** and **writes no input files**. Every numeric input was already structured by its owning phase: `value.json` (Phase 5), `costs.json` (Phase 8.5), `initiatives.json` (Phase 7), `baselines.json` (Phase 4), `scores.json` (Phase 6). Phase 9 reads them, runs the engine, and cites the results.

1. **Verify the inputs exist — do not create or re-write them.** Confirm `model/value.json`, `model/costs.json`, `model/initiatives.json`, `model/baselines.json`, and `model/scores.json` are present in the engagement folder. If any is missing, halt and name the owning phase that must produce it (value → Phase 5; costs → Phase 8.5; initiatives → Phase 7; baselines → Phase 4; scores → Phase 6). Do not transcribe figures from prose into a missing file — return to the owning phase. A figure recorded as `null` in an existing file is expected (it renders PENDING); a missing *file* is a gate failure.
2. **Run the engine:** `python -m engine.run <engagement-folder>/`. This reads the input files and writes `model/results.json`.
3. Populate every figure in `business-case.md` by citing `results.json` (per-initiative `costs.*.rom`, `value.*`, and `wave1_aggregate.investment` / `investment_point` / `value` / `payback_years`). The ROM label `AACE Class 5 (±50%)` comes from `results.json` `rom_label`.
4. Any `results.json` value equal to `"PENDING"` renders as **PENDING** in the business case with a note on what input is missing — never a fabricated number.

## Role in the system

The business case answers "what does Wave 1 cost and what is it worth?" — sourced entirely from methodology artifacts already produced. It is not a financial model. It is a ROM estimate (AACE Class 5, ±50%) that gives decision-makers a magnitude check before the deliverable gate.

Wave 1 is the only wave where a business case is possible. Wave 1 is fully specified — named owners, success metrics, enablers, sourcing recommendations. Wave 2 is directional; Wave 3 is strategic intent. Extending cost estimation to Wave 2 or Wave 3 produces false precision and is not permitted.

Phase 9 produces no new analysis. Every value claim traces to a source file from Phases 1–8. If a claim cannot be sourced, it does not appear in the business case.

## Gate condition

`usecase-briefs/_index.md` must exist and the `opportunity-reviewer` clearance for the briefs must be logged in `evidence-log.md`. `cost-actuals.md` must also exist in the engagement folder — this file is produced by Phase 8.5 (`ai-process-assessment:collecting-cost-actuals`). If `cost-actuals.md` is absent, halt immediately and invoke `ai-process-assessment:collecting-cost-actuals` before returning to this phase. This skill creates `business-case.md`.

## Scope constraint

**Wave 1 only.** Do not produce cost or value estimates for Wave 2 or Wave 3 initiatives. Wave 2 summary entries are directional — no business case. Wave 3 is strategic intent — no business case.

## Required source files

All five must be present. If any is missing, the skill halts and reports which file is absent.

| File | What it provides |
|---|---|
| `roadmap.md` | Wave 1 initiative list, sequencing, enablers |
| `usecase-briefs/_index.md` + Wave 1 `UC-NNN.md` files | Fully specified Wave 1 briefs (SCRA structure, sourcing recommendations). Read the index to identify Wave 1 UC file names, then read only those files. |
| `processes/_index.md` + `processes/PROC-NNN.md` per process | Current-state baseline metrics — the value denominator |
| `opportunities/_index.md` + `opportunities/OPP-NNN.md` per Wave 1 initiative | Value hypotheses (written before value — must be honored as written, not re-derived); read `opportunities/_index.md` to identify Wave 1 OPP-IDs, then read each `opportunities/OPP-NNN.md` for the verbatim value hypothesis |
| `scores/_index.md` + `scores/OPP-NNN.md` per Wave 1 initiative | Build/Buy/Partner classification per initiative with rationale; read `scores/_index.md` to confirm Wave 1 OPP-IDs, then read each `scores/OPP-NNN.md` for B/B/P classification and rationale |

## Output structure of `business-case.md`

The file contains exactly these sections, in this order:

1. **Wave 1 Scope** — number of initiatives, horizon, one-sentence total scope statement
2. **Per-initiative cost structure** — one block per Wave 1 initiative (see format below)
3. **Per-initiative value case** — one block per Wave 1 initiative (see format below)
4. **Wave 1 Aggregate** — total investment range *and* the central point estimate, total value range, rough payback horizon. The point estimate is `model/results.json` `wave1_aggregate.investment_point` (the engine's sum of the member initiative totals); **cite it — never add the per-initiative totals together in prose** (that free-floating sum is an arithmetic-in-prose defect the deliverable-gate blocks on). State the ROM band from `wave1_aggregate.investment` and the central figure from `wave1_aggregate.investment_point` side by side.
5. **Key Assumptions** — every assumption stated explicitly, labeled as assumption
6. **What Would Tighten This Estimate** — missing data items, required vendor quotes, internal rates needed
7. **ROM Accuracy** — AACE Class 5 ±50% by default; tighten to ±20–30% only if internal actuals from a `cost-actuals.md` file are present

### Per-initiative cost structure format

For each Wave 1 initiative, produce one labeled block. Each `[range]` and the **Initiative ROM range** are read from `model/results.json` (`costs.<OPP-ID>`), not computed here.

| Cost category | Estimate | Basis |
|---|---|---|
| Implementation labor | [range] | Build: labor-hours estimated / Buy: vendor quote required / Partner: integration estimate |
| Technology & licensing | [range] | SaaS/API costs; separate one-time from recurring |
| Integration & data engineering | [range] | From enabler mapping in roadmap.md and tech-inventory.md |
| Change management | [range] | Default 20–30% of implementation labor unless engagement context overrides |
| Contingency | [range] | 15–20% of subtotal |
| **Initiative ROM range** | **[low — high]** | **ROM estimate, AACE Class 5 (±50%)** |

**Mandatory labels — must appear on every cost block:**
- Every dollar figure must carry: "ROM estimate, AACE Class 5 (±50%)" unless internal actuals override
- Buy or Partner initiatives without vendor quotes must flag: "Requires vendor quote — figure is benchmark-based"
- One-time and recurring costs must be explicitly separated — never blended into a single figure
- Every block must include: "Budget the production figure — pilots typically run 3–5x below production cost"

### Per-initiative value case format

For each Wave 1 initiative:

- **Named baseline:** cite the exact baseline entry from `processes/PROC-NNN.md` — no floating figures
- **Value hypothesis:** verbatim from `opportunities/OPP-NNN.md` — not re-derived or paraphrased
- **Expected improvement:** drawn from the value hypothesis, not invented
- **Annual value calculation:** read from `model/results.json` (`value.<OPP-ID>`) — the engine computes improvement × volume × rate; every component is named and sourced in prose but not multiplied here

## What this skill cannot do

State the following explicitly in the `business-case.md` output under the Key Assumptions section:

- This document does not produce vendor quotes. Buy and Partner initiatives require procurement engagement before cost estimates can be tightened.
- This document does not know internal labor rates. Any figure involving internal labor is benchmark-based and must be replaced with internal actuals before use in budget submissions.
- This is not a business case for finance approval. A definitive business case requires NPV modeling, finance review, and procurement data. This document is an AACE Class 5 ROM estimate.

## Seeding hook (v2)

If a `cost-actuals.md` file exists in the engagement folder, reference its entries for matching initiative types and tighten the ROM band accordingly. If absent (the default), use the ROM framework and flag all figures as benchmark-based. This hook is forward-compatible — do not require `cost-actuals.md`; only use it if present.

## Subagent Dispatch

Per-initiative cost and value analysis is independent across Wave 1 initiatives — they parallelize cleanly.

- **When:** After confirming all five source files exist, dispatch one `business-case-analyst` subagent per Wave 1 initiative in a single parallel tool-call batch.
- **Pass to each subagent:** engagement folder path and UC-NNN file path for this initiative. The agent reads its own roadmap.md entry, UC-NNN.md, processes/PROC-NNN.md baseline rows, opportunities/OPP-NNN.md value hypothesis, scores/OPP-NNN.md B/B/P classification, and cost-actuals.md rows itself. Do not pass file content to the subagent.
- **Return:** The agent writes its cost structure block and value case block to `<engagement-folder>/_staging/phase9/<initiative-id>.md`. Returns one-line summary: "initiative-id: ROM $X–$Y, value category." The orchestrator assembles `business-case.md` from staging files — it does NOT receive block content from subagents.
- **What stays in main context:** Assembly of returned blocks, reading the Wave 1 aggregate (investment, value, payback) from `model/results.json` `wave1_aggregate` (engine-computed — never summed in prose), mandatory label verification, and Key Assumptions compilation.

**Note:** Dispatch is the primary path. Do not fall back to main context unless dispatch explicitly fails and you cannot recover.

## Phase checklist

- [ ] Confirm `usecase-briefs/_index.md` saved and reviewer cleared
- [ ] Confirm cost-actuals.md exists in the engagement folder — halt and invoke Phase 8.5 if absent
- [ ] Confirm all five source files exist
- [ ] Verify `model/{value,costs,initiatives,baselines,scores}.json` exist (do NOT write them — they are owned by Phases 5/8.5/7/4/6); halt naming the owning phase if any file is missing
- [ ] Run `python -m engine.run <engagement-folder>/` to produce `model/results.json`
- [ ] Dispatch one `business-case-analyst` subagent per Wave 1 initiative in a single parallel batch (or run in main context if agent definition not yet present)
- [ ] Collect returned cost/value blocks
- [ ] Read the Wave 1 aggregate (investment, value, payback) from `model/results.json` `wave1_aggregate` — engine-computed, never summed in prose
- [ ] Verify: every figure has a ROM label; every Buy/Partner initiative flags missing vendor quote; one-time and recurring costs are separated; pilot-to-production warning is present on every cost block
- [ ] Confirm `Key Assumptions` contains the three cannot-do statements
- [ ] Confirm `What Would Tighten This Estimate` names specific missing inputs, not vague categories
- [ ] Save to `<engagement>/business-case.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:deliverable-gate`

## Workflow

1. Confirm preconditions: `usecase-briefs/_index.md` exists and reviewer cleared.
2. Confirm `cost-actuals.md` exists in the engagement folder. If absent: halt. Do not proceed. Invoke `ai-process-assessment:collecting-cost-actuals` (Phase 8.5) and complete it before returning to this phase.
3. Confirm all five source files present.
4. Verify `model/value.json`, `model/costs.json`, `model/initiatives.json`, `model/baselines.json`, and `model/scores.json` exist (owned by Phases 5/8.5/7/4/6 respectively) — do NOT write or re-write them. If any is missing, halt and name the owning phase. Then run `python -m engine.run <engagement-folder>/` to produce `model/results.json`. Then, for each Wave 1 initiative from `roadmap.md`, dispatch one `business-case-analyst` subagent. Pass only that initiative's data; the agent cites its figures from `model/results.json`.
5. Collect returned blocks. In main context: verify mandatory labels, read the Wave 1 aggregate (investment, value, payback) from `model/results.json` `wave1_aggregate` (the engine sums the low/high ranges and computes payback — never compute in prose), compile Key Assumptions from all initiative blocks.
6. Add the three cannot-do statements to Key Assumptions.
7. Add What Would Tighten This Estimate — list specific missing inputs (vendor quotes for Buy/Partner initiatives, internal labor rate, integration complexity from IT).
8. Add ROM Accuracy section: AACE Class 5 ±50% by default.
9. Save and chain to deliverable gate.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "We can produce a real budget — we have enough data." | The methodology produces ROM ranges, not a business case. A business case requires internal labor rates, vendor quotes, and finance review. Label it correctly or it will be used as a commitment it was never designed to be. |
| "Wave 2 and Wave 3 need cost estimates too." | Wave 2 is directional; Wave 3 is intent. Neither has the specification depth needed for even a ROM estimate. Extending the business case to Wave 2 or Wave 3 produces false precision. |
| "We don't need a separate skill — roadmap.md can hold the budget." | Sequencing and cost estimation are different reasoning tasks. A model doing both in one phase produces shallow work on both. The separation is the discipline. |
| "The value hypothesis was written before we knew the full picture — we should re-derive it." | The value hypothesis was written before value was estimated precisely because the methodology requires that order. Re-deriving it in Phase 9 reverses the discipline. Use it as written. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `business-case.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, surface the phase output to the user:

1. **Name the file written** and its path
2. **Summarize key findings** in 3–5 bullets — Wave 1 aggregate investment range, aggregate value range, rough payback horizon, any initiatives flagged for missing vendor quotes
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision.

Key findings to surface for this phase: Wave 1 aggregate ROM range (low/high), aggregate annual value range, rough payback horizon, count of initiatives requiring vendor quotes before estimates can be tightened.

**Session boundary:** After the user approves `business-case.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:deliverable-gate` to begin Gate B. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:deliverable-gate` (Gate B — four-dimension integrity check before any external sharing)
