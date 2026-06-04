---
name: ai-process-assessment:packaging-usecases
description: Phase 8 — produces self-contained Use Case Brief (UC-NNN) per Wave 1 initiative using Situation-Complication-Resolution-Action structure. Saves individual UC-NNN.md files + _index.md to usecase-briefs/ folder.
---

# Phase 8: Packaging Use Cases

## Role in the system

The brief is the unit of delivery. Each Wave 1 opportunity becomes a self-contained brief that an executive can read in five minutes and act on. Wave 2 items get summary briefs; Wave 3 items get capability-area placeholders. The Situation-Complication-Resolution-Action structure forces business framing before technical solutioning.

## Gate condition

`roadmap.md` must exist and the `opportunity-reviewer` clearance for the roadmap must be logged. This skill creates the `usecase-briefs/` folder containing `_index.md` and individual `UC-NNN.md` files (one per opportunity across all three waves).

## UC-NNN Brief Structure

Every Wave 1 brief contains the following 11 fields:

| Field | Content |
|---|---|
| Opportunity reference | OPP-NNN from `opportunities.md` |
| Opportunity type | RPA / AI Augmentation / AI Automation / Agentic / Data & Analytics |
| Situation | Current state — sourced to `process-map.md` and `baselines.md` |
| Complication | What changed or what's broken — the reason this is on the roadmap now |
| Resolution | The proposed intervention; tied to opportunity type |
| Action | Specific next step with named owner and date |
| Data requirements | What data is needed; sourced to `tech-inventory.md` |
| Success metric | Measurable outcome; sourced to a baseline |
| Risks & mitigations | From scoring + GRC gate output |
| Sourcing recommendation | Build / Buy / Partner / Hybrid with rationale |
| Wave assignment | Wave 1 (with month-X target) |

**SCRA rule: SCRA structure forces the practitioner to articulate the business problem before the technical solution. Action field creates immediate accountability.**

## Phase checklist

- [ ] Confirm `roadmap.md` saved and reviewer cleared
- [ ] Create `usecase-briefs/` folder in the engagement run directory
- [ ] Dispatch one `usecase-brief-drafter` agent per Wave 1 opportunity in a single parallel tool-call batch (pass: OPP entry, relevant process-map.md sections, baselines.md rows, scored-opportunities.md row, roadmap.md entry, GRC conditions if applicable, and UC-NNN assignment — e.g., "Write this as UC-001")
- [ ] Collect returned brief content from agents; write each as `usecase-briefs/UC-NNN.md` — one Write call per brief
- [ ] Run a consistency pass — read each Wave 1 UC file and patch inconsistencies (voice, terminology, owner naming format, Action field) via Edit on the specific file. Do NOT re-draft briefs.
- [ ] Write Wave 2 summary briefs in main context — one file per initiative (`usecase-briefs/UC-008.md` onward). Schema: Opportunity reference, type, situation, hypothesis, expected value range, key dependencies.
- [ ] Write Wave 3 placeholders in main context — one file per initiative. Schema: Opportunity reference, type, capability area, strategic hypothesis, re-scoping trigger.
- [ ] Assemble `usecase-briefs/_index.md` in main context — master index table (UC-NNN, OPP ref, title, type, wave, month target, sourcing, one-line description)
- [ ] Dispatch `opportunity-reviewer` subagent — pass `_index.md` content; reviewer may flag specific UC files for completeness issues
- [ ] Resolve Critical findings by editing the specific `UC-NNN.md` file affected
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:collecting-cost-actuals`

## Workflow

1. Confirm preconditions.
2. Create the `usecase-briefs/` folder. Dispatch `usecase-brief-drafter` agents in parallel — one per Wave 1 opportunity. Pass each agent its OPP entry, the relevant source sections, and its UC-NNN assignment. Do NOT share cross-OPP context between agents. Collect returned brief content.
3. Write each returned brief as `usecase-briefs/UC-NNN.md` — one Write call per brief. Run a consistency pass: normalize voice (direct, present-tense situation / conditional resolution/action), verify owner naming format, confirm wave month targets match roadmap.md. Patch inconsistencies via Edit on the specific file — do NOT re-draft briefs.
4. Action field requires a named owner and a date — not "the team will...".
5. Write Wave 2 summary briefs in main context, one at a time, as separate `UC-NNN.md` files. Wave 2 summary schema: Opportunity reference, type, situation, hypothesis, expected value range, key dependencies. Write Wave 3 placeholders in main context, one at a time, as separate `UC-NNN.md` files. Wave 3 schema: Opportunity reference, type, capability area, strategic hypothesis, re-scoping trigger.
6. Assemble `usecase-briefs/_index.md` — a master table: UC-NNN, OPP ref, title, type, wave, month target, sourcing, one-line description. One row per UC across all three waves.
7. Dispatch reviewer with `_index.md` content. Resolve Critical findings by editing the specific `UC-NNN.md` file affected.
8. All files are written. Final step before any external sharing is the `deliverable-gate`.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "We can collapse Situation and Complication." | They serve different purposes — Situation is current state, Complication is why now. Collapsing them produces briefs that don't motivate action. |
| "Resolution can come before Complication if it's faster." | The order is the discipline. Writing Resolution first invites solution-first thinking; the Complication step is where you confirm you understand the actual problem. |
| "Action can be 'evaluate' or 'discuss'." | Action requires a named owner and a date. Anything softer is a placeholder, not an action. |
| "Wave 2 briefs can be skipped — they'll get rewritten in 6 months." | Wave 2 briefs are commitments at directional depth. Without them, Wave 1 lands without a credible follow-on. |
| "Risks were captured during scoring — we don't need them in the brief." | The brief is read independently of the scoring output. Risks must travel with the recommendation. |
| "Sourcing recommendation is an implementation detail." | Sourcing is the most consequential decision after type. It belongs in the brief, with rationale. |
| "Agent-drafted briefs will have inconsistent voice — better to draft in main context." | Voice drift is real; the consistency pass on the assembled file is its fix. Drafting inline re-introduces the context bloat the WFS pattern exists to prevent. |

## Handoff Protocol

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: Wave 1 briefs written (count), Wave 2 summaries (count), any completeness gaps flagged by reviewer.

## Chain to next skill

→ `ai-process-assessment:collecting-cost-actuals` (Phase 8.5 — collects labor rates, vendor quotes, and IT estimates before the business case)
