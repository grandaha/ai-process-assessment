---
name: ai-process-assessment:scoring-opportunities
description: Phase 6 — applies multi-dimensional scoring rubric (7 dimensions, 5-point scale, evidence-gated) plus build/buy/partner classification. Dispatches opportunity-reviewer subagent before save. Saves scored-opportunities.md.
---

# Phase 6: Scoring Opportunities

## Role in the system

Scoring converts a typed opportunity log into a ranked portfolio. The rubric is multi-dimensional on purpose — a single composite score hides the trade-offs that determine sequencing. Every dimension must be sourced; intuition is not a source.

## Gate condition

`opportunities.md` must exist. The GRC gate must be cleared for any opportunity with a non-Green GRC flag. This skill creates `scored-opportunities.md`.

## Scoring Rubric

Score each opportunity across all seven dimensions on a 1–5 scale. Cite the source for each score.

| Dimension | What it measures | Required source |
|---|---|---|
| Value Potential | Magnitude of value if realized. For Chain Automation type: cite checkpoints eliminated × effort per checkpoint × volume. Do not aggregate step-level savings linearly — chain value is non-linear. | `baselines.md` |
| Technical Feasibility | Buildability given current systems and skills | `tech-inventory.md` |
| Data Readiness | Whether data needed exists, is accessible, and is fit for purpose | `tech-inventory.md` (data asset catalog) |
| Org Change Readiness | Whether the affected team can absorb the change | `context.md` |
| Strategic Alignment | Fit with stated strategic priorities | `context.md` |
| Time to Value | Speed from start to first measurable outcome | `tech-inventory.md` + `process-map.md` |
| Risk | Aggregate execution and post-deployment risk | GRC gate output + `context.md` |
| Execution Horizon | Whether value is achievable within existing job boundaries (Short-run) or requires redesigning how tasks are bundled across workers (Long-run). Short-run is faster and smaller. Long-run is larger but requires org design work as a dependency. | `process-map.md` chain scan + `context.md` |

**Categorical rule: Each dimension score must cite a source (`process-map.md`, `baselines.md`, `tech-inventory.md`, `context.md`, or GRC gate output). No dimension may be scored from intuition.**

**Execution Horizon is a required field on every scored opportunity entry: Short-run / Long-run with one-sentence rationale. This field is consumed by Phase 7 sequencing.**

## Build/Buy/Partner Classification

Required for every scored opportunity. Inputs:

- **Build capacity** — internal skills, available bandwidth
- **Vendor maturity** — does a credible product exist for this use case
- **Strategic differentiation** — does owning this capability differentiate the business
- **TCO horizon** — total cost of ownership over 3-year window for each path

Output one of: **Build / Buy / Partner / Hybrid**, with rationale citing the four inputs.

## Phase checklist

- [ ] Confirm `opportunities.md` exists and GRC gate cleared for flagged items
- [ ] Dispatch one `opportunity-scorer` agent per opportunity in a single parallel tool-call batch (pass: OPP entry, relevant process-map.md sections, baselines.md rows, tech-inventory.md sections, context.md sections, GRC gate output if applicable)
- [ ] Collect returned scored entries; assemble into scored-opportunities.md
- [ ] Apply Build/Buy/Partner classification per opportunity
- [ ] Compute composite score AND retain dimensional scores (composite alone is insufficient)
- [ ] Dispatch the `opportunity-reviewer` subagent for independent review
- [ ] Resolve any Critical findings before save
- [ ] Save to `docs/engagements/<engagement>/scored-opportunities.md`
- [ ] Log reviewer clearance in `evidence-log.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:prioritizing-roadmap`

## Workflow

1. Confirm `opportunities.md` exists and GRC clearance is recorded for all flagged opportunities.
2. Dispatch `opportunity-scorer` agents in parallel — one per opportunity. Pass each agent only its own OPP entry and the relevant sections from the four source files. Do NOT share cross-OPP context between agents. Collect returned scored entries.
3. Verify that each returned entry includes a Build/Buy/Partner classification — `opportunity-scorer` produces this. Do not re-derive B/B/P in main context. Assemble the verified entries into the scored-opportunities.md draft.
4. Run the full scored set through the `opportunity-reviewer` subagent. Pass it the document content under review only.
5. Resolve all Critical findings. Important findings should be addressed; Minor findings are noted.
6. Save and chain forward.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Composite score is enough — we can drop the dimensions." | Composite hides trade-offs. A high-value, low-readiness opportunity scores the same as a medium-everything opportunity. The dimensions ARE the decision input. |
| "We can score from intuition for the small ones." | The rule is categorical for a reason. Once intuition is permitted for "small" items, the boundary moves. |
| "Risk is low because leadership wants this." | Leadership desire is not risk reduction. Risk is regulatory exposure, model failure consequence, and change absorption — none of which are softened by sponsorship. |
| "We'll figure out Build/Buy/Partner later." | B/B/P is an input to sequencing and brief writing. Deferring it pushes the same decision into less-prepared phases. |
| "The reviewer subagent slows us down." | The reviewer is the durability mechanism for this phase. Skipping it is how scored portfolios pass through to delivery with sourcing gaps. |
| "Scoring in main context lets me calibrate scores across OPPs — parallel agents can't do that." | Cross-OPP calibration happens during the consistency review of the assembled file, not during drafting. The `opportunity-reviewer` subagent is the calibration gate. Scoring inline re-introduces context bloat. |
| "The value estimate is the sum of each step's individual time savings." | For Chain Automation opportunities, value comes primarily from eliminating human verification checkpoints, not from accelerating individual steps. Linear step-count aggregation is the wrong model. Cite checkpoints eliminated and effort per checkpoint from the chain scan. |

## Handoff Protocol

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: top 3 scored opportunities with scores, score distribution, any critical reviewer findings and how resolved.

## Chain to next skill

→ `ai-process-assessment:prioritizing-roadmap` (after `scored-opportunities.md` is saved and reviewer cleared)
