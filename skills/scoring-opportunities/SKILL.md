---
name: ai-process-assessment:scoring-opportunities
description: Phase 6 — applies multi-dimensional scoring rubric (7 dimensions, 5-point scale, evidence-gated) plus build/buy/partner classification. Dispatches opportunity-reviewer subagent before save. Saves scored-opportunities.md.
---

# Phase 6: Scoring Opportunities

## Session Start

This skill runs as a standalone session. At session start:
1. Confirm the engagement folder path with the user if not already provided.
2. Read `opportunities.md` and confirm it exists.
3. Check `evidence-log.md` — confirm GRC gate clearance is recorded for any flagged opportunities.

Gate condition: `opportunities.md` present; all non-Green GRC flags resolved in `evidence-log.md`.

## Role in the system

Scoring converts a typed opportunity log into a ranked portfolio. The rubric is multi-dimensional on purpose — a single composite score hides the trade-offs that determine sequencing. Every dimension must be sourced; intuition is not a source.

## Gate condition

`opportunities.md` must exist. The GRC gate must be cleared for any opportunity with a non-Green GRC flag. This skill creates `scored-opportunities.md`.

## Scoring Rubric

Score each opportunity across all seven dimensions on a 1–5 scale. Cite the source for each score. Use the scale anchors below — do not interpret the scale without them.

| Dimension | What it measures | Required source |
|---|---|---|
| Value Potential | Magnitude of value if realized. For Chain Automation type: cite checkpoints eliminated × effort per checkpoint × volume. Do not aggregate step-level savings linearly — chain value is non-linear. | `baselines.md` |
| Technical Feasibility | Buildability given current systems and skills | `tech-inventory.md` |
| Data Readiness | Whether data needed exists, is accessible, and is fit for purpose | `tech-inventory.md` (data asset catalog) |
| Org Change Readiness | Whether the affected team can absorb the change | `context.md` |
| Strategic Alignment | Fit with stated strategic priorities | `context.md` |
| Time to Value | Speed from start to first measurable outcome | `tech-inventory.md` + `process-map.md` |
| Risk | Aggregate execution and post-deployment risk — **higher score = lower risk** | GRC gate output + `context.md` |
| Execution Horizon | Whether value is achievable within existing job boundaries (Short-run) or requires redesigning how tasks are bundled across workers (Long-run). Short-run is faster and smaller. Long-run is larger but requires org design work as a dependency. **Long-run is NOT a long timeline or complex prerequisites — it specifically means the opportunity cannot deliver value until someone's job or role boundary is redesigned. A long GRC clearance track or missing integration is a dependency (Constraint 1), not a Long-run classification.** | `process-map.md` chain scan + `context.md` |

### Scale Anchors (apply to all 7 dimensions)

**Value Potential**
- 1 — No supporting baseline; value is speculative or negligible
- 2 — Directional claim only; no named metric supports magnitude
- 3 — Moderate value; partially baselined; recovers meaningful cost or cycle time
- 4 — High value; strong baseline; recovers significant cost or time (>$100K/yr or >1 FTE or meaningful cycle-time compression across high volume)
- 5 — Very high value; strong baseline; major cost or strategic impact (>$500K/yr, or directly addresses the largest identified cost driver in the engagement)

**Technical Feasibility**
- 1 — Not feasible given current stack; requires capabilities that do not exist
- 2 — Major barriers; significant new capability required beyond the current stack
- 3 — Feasible but requires new integrations (8–12 week security review) or substantial new configuration
- 4 — Mostly in existing stack; Workday config changes only (6–10 week lead time); no new integration required
- 5 — Uses existing licensed features; minimal configuration; no new integration; quickest deployment path

**Data Readiness**
- 1 — Critical gaps; data does not exist, is inaccessible, or is fundamentally unfit for purpose
- 2 — Poor quality or major gaps in key datasets; significant remediation required before deployment
- 3 — Moderate quality; data exists with known gaps; usable with documented limitations
- 4 — Good quality; minor gaps that do not block deployment
- 5 — Good quality, real-time, complete; no relevant gaps for this use case

**Org Change Readiness**
- 1 — Active resistance; change will fail without a major multi-year intervention
- 2 — Meaningful resistance; targeted change management program required; key skeptical stakeholders with real veto risk
- 3 — Mixed; some champions, some skeptics; standard change management needed; no active blockers
- 4 — Favorable; key stakeholders aligned; limited adoption friction expected
- 5 — High readiness; champion-driven; team actively wants the change

**Strategic Alignment**
- 1 — No alignment with any stated strategic priority
- 2 — Tangential or indirect alignment to one priority
- 3 — Directly supports one stated strategic priority
- 4 — Directly supports two stated strategic priorities
- 5 — Core to three or more stated priorities, including CEO- or Board-level initiatives

**Time to Value**
- 1 — 12+ months to first measurable outcome; major prerequisites on the critical path
- 2 — 9–12 months; significant dependencies or prerequisites
- 3 — 6–9 months including IT lead time and any prerequisite work
- 4 — 3–6 months; uses existing stack with known lead times
- 5 — Under 3 months or measurable within one quarter; minimal dependencies

**Risk (higher score = lower risk)**
- 1 — Very high risk; unresolved regulatory or legal exposure; high failure consequence; Red GRC flag
- 2 — High risk; complex conditions; significant EEOC or compliance exposure; Yellow GRC with multiple governance dependencies
- 3 — Moderate risk; Yellow GRC cleared with conditions; conditions are manageable but require active governance
- 4 — Low risk; Green GRC; limited failure consequence; failure is detectable and recoverable
- 5 — Minimal risk; Green GRC; no regulatory exposure; no candidate PII; failure is trivially reversible

**Categorical rule: Each dimension score must cite a source (`process-map.md`, `baselines.md`, `tech-inventory.md`, `context.md`, or GRC gate output). No dimension may be scored from intuition.**

**Execution Horizon is a required field on every scored opportunity entry: Short-run / Long-run with one-sentence rationale. This field is consumed by Phase 7 sequencing.**

## Build/Buy/Partner Classification

Required for every scored opportunity. Inputs:

- **Build capacity** — internal skills, available bandwidth
- **Vendor maturity** — does a credible product exist for this use case
- **Strategic differentiation** — does owning this capability differentiate the business
- **TCO horizon** — total cost of ownership over 3-year window for each path

Output one of: **Build / Buy / Partner / Hybrid**, with rationale citing the four inputs.

## Subagent Dispatch

This phase already runs two subagents. This section names the pattern so it reads consistently with the other phases — the operational detail lives in the Phase checklist and Workflow below, which are authoritative.

- **Scorer dispatch (`opportunity-scorer`):** One subagent per opportunity, dispatched in a single parallel tool-call batch. Each receives: engagement folder path, OPP-ID, and staging file path: `<engagement-folder>/_staging/phase6/OPP-NNN.md`. The agent reads its own OPP entry from `opportunities.md` and the relevant sections of `process-map.md`, `baselines.md`, `tech-inventory.md`, and `context.md` itself. Do not pass file content to the subagent. No cross-OPP context is shared. Each scorer writes its full entry to the staging file and returns only a one-line summary (composite score and B/B/P classification).
- **Reviewer dispatch (`opportunity-reviewer`):** One subagent over the fully assembled `scored-opportunities.md` draft, for independent cross-OPP calibration and consistency review. Pass to the reviewer: engagement folder path. The reviewer reads `scored-opportunities.md` itself. Do not pass document content. Return: The reviewer appends findings to `<engagement-folder>/evidence-log.md` directly. Returns one-line summary to main context: "N Critical, N Important, N Minor findings." The orchestrator does NOT receive full review content.
- **Assembly:** After all scorer agents complete, assemble via Bash: `cat docs/engagements/<name>/_staging/phase6/OPP-*.md > docs/engagements/<name>/scored-opportunities.md`. Verify with: `wc -l scored-opportunities.md`. Cleanup: `rm -rf _staging/phase6`.
- **What stays in main context:** One-line summaries from each scorer agent (OPP-NNN, composite score, B/B/P), resolution of reviewer Critical findings, and the save + evidence-log clearance. Do not re-derive scores or B/B/P inline.

See the Phase checklist and Workflow sections for the authoritative step sequence and ordering.

## Phase checklist

- [ ] Confirm `opportunities.md` exists and GRC gate cleared for flagged items
- [ ] Dispatch one `opportunity-scorer` agent per opportunity in a single parallel tool-call batch (pass: OPP entry, relevant process-map.md sections, baselines.md rows, tech-inventory.md sections, context.md sections, GRC gate output if applicable)
- [ ] Collect one-line summaries from scorer agents (OPP-NNN, composite, B/B/P). Full scored entries are in staging files.
- [ ] Assemble via Bash: `cat docs/engagements/<name>/_staging/phase6/OPP-*.md > docs/engagements/<name>/scored-opportunities.md`
- [ ] Verify: `wc -l docs/engagements/<name>/scored-opportunities.md`
- [ ] Cleanup: `rm -rf docs/engagements/<name>/_staging/phase6`
- [ ] Compute composite score AND retain dimensional scores (composite alone is insufficient)
- [ ] Dispatch the `opportunity-reviewer` subagent for independent review
- [ ] Resolve any Critical findings before save
- [ ] Save to `docs/engagements/<engagement>/scored-opportunities.md`
- [ ] Log reviewer clearance in `evidence-log.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:prioritizing-roadmap`

## Workflow

1. Confirm `opportunities.md` exists and GRC clearance is recorded for all flagged opportunities.
2. Dispatch `opportunity-scorer` agents in parallel — one per opportunity. Pass each agent its OPP entry, the relevant sections from the four source files, and its staging file path (`_staging/phase6/OPP-NNN.md`). Do NOT share cross-OPP context between agents. Collect one-line summaries only — do NOT request the full scored entry back.
3. After all agents complete, assemble: `cat _staging/phase6/OPP-*.md > scored-opportunities.md`. Verify with `wc -l`. Cleanup `_staging/phase6`. B/B/P is in the staging files and the assembled output — do not re-derive in main context.
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

**Output rule:** Do NOT reproduce the contents of `scored-opportunities.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: top 3 scored opportunities with scores, score distribution, any critical reviewer findings and how resolved.

**Session boundary:** After the user approves `scored-opportunities.md` and the reviewer is cleared, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:prioritizing-roadmap` to begin Phase 7. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:prioritizing-roadmap` (after `scored-opportunities.md` is saved and reviewer cleared)
