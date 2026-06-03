---
name: ai-process-assessment:building-business-case
description: Phase 9 — produces a Wave 1 ROM business case (business-case.md) sourced from methodology artifacts. Not a financial model. Scoped to Wave 1 only — Wave 2 is directional, Wave 3 is intent.
---

# Phase 9: Building the Business Case

## Role in the system

The business case answers "what does Wave 1 cost and what is it worth?" — sourced entirely from methodology artifacts already produced. It is not a financial model. It is a ROM estimate (AACE Class 5, ±50%) that gives decision-makers a magnitude check before the deliverable gate.

Wave 1 is the only wave where a business case is possible. Wave 1 is fully specified — named owners, success metrics, enablers, sourcing recommendations. Wave 2 is directional; Wave 3 is strategic intent. Extending cost estimation to Wave 2 or Wave 3 produces false precision and is not permitted.

Phase 9 produces no new analysis. Every value claim traces to a source file from Phases 1–8. If a claim cannot be sourced, it does not appear in the business case.

## Gate condition

`usecase-briefs.md` must exist and the `opportunity-reviewer` clearance for the briefs must be logged in `evidence-log.md`. This skill creates `business-case.md`.

## Scope constraint

**Wave 1 only.** Do not produce cost or value estimates for Wave 2 or Wave 3 initiatives. Wave 2 summary entries are directional — no business case. Wave 3 is strategic intent — no business case.

## Required source files

All five must be present. If any is missing, the skill halts and reports which file is absent.

| File | What it provides |
|---|---|
| `roadmap.md` | Wave 1 initiative list, sequencing, enablers |
| `usecase-briefs.md` | Fully specified Wave 1 briefs (SCRA structure, sourcing recommendations) |
| `baselines.md` | Current-state metrics — the value denominator |
| `opportunities.md` | Value hypotheses (written before value — must be honored as written, not re-derived) |
| `scored-opportunities.md` | Build/Buy/Partner classifications per initiative |

## Output structure of `business-case.md`

The file contains exactly these sections, in this order:

1. **Wave 1 Scope** — number of initiatives, horizon, one-sentence total scope statement
2. **Per-initiative cost structure** — one block per Wave 1 initiative (see format below)
3. **Per-initiative value case** — one block per Wave 1 initiative (see format below)
4. **Wave 1 Aggregate** — total investment range, total value range, rough payback horizon
5. **Key Assumptions** — every assumption stated explicitly, labeled as assumption
6. **What Would Tighten This Estimate** — missing data items, required vendor quotes, internal rates needed
7. **ROM Accuracy** — AACE Class 5 ±50% by default; tighten to ±20–30% only if internal actuals from a `cost-actuals.md` file are present

### Per-initiative cost structure format

For each Wave 1 initiative, produce one labeled block:

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

- **Named baseline:** cite the exact baseline entry from `baselines.md` — no floating figures
- **Value hypothesis:** verbatim from `opportunities.md` — not re-derived or paraphrased
- **Expected improvement:** drawn from the value hypothesis, not invented
- **Annual value calculation:** improvement × volume × rate — every component named and sourced

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
- **Pass to each subagent:** Only that initiative's data — roadmap.md entry, usecase-briefs.md brief, baselines.md relevant rows, opportunities.md value hypothesis, scored-opportunities.md B/B/P classification, and the relevant rows from cost-actuals.md (if the file exists). Do not share other initiatives' data between subagents.
- **Return:** A fully-formed cost structure block and value case block for that initiative, following the formats above.
- **What stays in main context:** Assembly of returned blocks, Wave 1 aggregate computation (sum ranges, compute payback), mandatory label verification, and Key Assumptions compilation.

**Note:** Dispatch is the primary path. Do not fall back to main context unless dispatch explicitly fails and you cannot recover.

## Phase checklist

- [ ] Confirm `usecase-briefs.md` saved and reviewer cleared
- [ ] Check for cost-actuals.md in the engagement folder; extract relevant rows if present
- [ ] Confirm all five source files exist
- [ ] Dispatch one `business-case-analyst` subagent per Wave 1 initiative in a single parallel batch (or run in main context if agent definition not yet present)
- [ ] Collect returned cost/value blocks
- [ ] Assemble Wave 1 aggregate (sum ranges, compute rough payback) in main context
- [ ] Verify: every figure has a ROM label; every Buy/Partner initiative flags missing vendor quote; one-time and recurring costs are separated; pilot-to-production warning is present on every cost block
- [ ] Confirm `Key Assumptions` contains the three cannot-do statements
- [ ] Confirm `What Would Tighten This Estimate` names specific missing inputs, not vague categories
- [ ] Save to `docs/engagements/<engagement>/business-case.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:deliverable-gate`

## Workflow

1. Confirm preconditions: `usecase-briefs.md` exists and reviewer cleared.
2. Check for `cost-actuals.md` in the engagement folder. If present, extract: (a) internal labor rates by role, (b) vendor quotes by initiative, (c) IT integration estimates by enabler — these will be passed to each subagent at dispatch. If absent, surface this non-blocking notice to the user and proceed: *"No cost-actuals.md found in the engagement folder. Phase 9 will run on AACE Class 5 benchmark labor rates (±50%). To tighten estimates, copy `templates/cost-actuals-template.md` to this engagement folder, fill in internal rates and any vendor quotes received, and re-run Phase 9."*
3. Confirm all five source files present.
4. For each Wave 1 initiative from `roadmap.md`, dispatch one `business-case-analyst` subagent. Pass only that initiative's data.
5. Collect returned blocks. In main context: verify mandatory labels, assemble aggregate (sum low/high ranges separately, compute payback as aggregate investment range ÷ annual value range), compile Key Assumptions from all initiative blocks.
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

Before invoking the next skill, surface the phase output to the user:

1. **Name the file written** and its path
2. **Summarize key findings** in 3–5 bullets — Wave 1 aggregate investment range, aggregate value range, rough payback horizon, any initiatives flagged for missing vendor quotes
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision.

Key findings to surface for this phase: Wave 1 aggregate ROM range (low/high), aggregate annual value range, rough payback horizon, count of initiatives requiring vendor quotes before estimates can be tightened.

## Chain to next skill

→ `ai-process-assessment:deliverable-gate` (Gate B — four-dimension integrity check before any external sharing)
