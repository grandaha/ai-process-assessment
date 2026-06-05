---
name: ai-process-assessment:packaging-usecases
description: Phase 8 — produces self-contained Use Case Brief (UC-NNN) per Wave 1 initiative using Situation-Complication-Resolution-Action structure. Saves individual UC-NNN.md files + _index.md to usecase-briefs/ folder.
---

# Phase 8: Packaging Use Cases

## Session Start

This skill runs as a standalone session. At session start:
1. Confirm the engagement folder path with the user if not already provided.
2. Read `roadmap.md` and `scores/_index.md` — confirm both exist.
3. Check `evidence-log.md` — confirm opportunity-reviewer clearance from Phase 7.

Gate condition: `roadmap.md` present; reviewer clearance logged in `evidence-log.md`.

## Role in the system

The brief is the unit of delivery. Each Wave 1 opportunity becomes a self-contained brief that an executive can read in five minutes and act on. Wave 2 items get summary briefs; Wave 3 items get capability-area placeholders. The Situation-Complication-Resolution-Action structure forces business framing before technical solutioning.

## Gate condition

`roadmap.md` must exist and the `opportunity-reviewer` clearance for the roadmap must be logged. This skill creates the `usecase-briefs/` folder containing `_index.md` and individual `UC-NNN.md` files (one per opportunity across all three waves).

## UC-NNN Brief Structure

Every Wave 1 brief contains the following 11 fields:

| Field | Content |
|---|---|
| Opportunity reference | OPP-NNN from `opportunities/OPP-NNN.md` |
| Opportunity type | RPA / AI Augmentation / AI Automation / Agentic / Data & Analytics |
| Situation | Current state — sourced to `process-map.md` and `baselines.md` |
| Complication | What changed or what's broken — the reason this is on the roadmap now |
| Resolution | The proposed intervention; tied to opportunity type |
| Action | Specific next step with named owner and date |
| Data requirements | What data is needed; sourced to `tech-inventory.md` |
| Success metric | Measurable outcome; sourced to a baseline |
| Risks & mitigations | From `scores/OPP-NNN.md` (scoring rationale) + `grc/OPP-NNN.md` (conditions, if file exists) |
| Sourcing recommendation | Build / Buy / Partner / Hybrid with rationale |
| Wave assignment | Wave 1 (with month-X target) |

**SCRA rule: SCRA structure forces the practitioner to articulate the business problem before the technical solution. Action field creates immediate accountability.**

## Phase checklist

- [ ] Confirm `roadmap.md` saved and reviewer cleared
- [ ] Create `usecase-briefs/` folder in the engagement run directory
- [ ] Dispatch one `usecase-brief-drafter` agent per Wave 1 opportunity in a single parallel tool-call batch. Pass: engagement folder path, OPP-ID, and UC-NNN assignment. The agent reads `opportunities/OPP-NNN.md`, `scores/OPP-NNN.md`, and `grc/OPP-NNN.md` (if it exists) directly — do not pass file content to the subagent.
- [ ] Each agent writes its brief directly to `<engagement-folder>/usecase-briefs/UC-NNN.md`. Returns one-line confirmation: "UC-NNN written." Orchestrator collects confirmations only — does NOT receive brief content. After all confirmations received, verify each UC-NNN.md file exists on disk.
- [ ] Run a consistency pass — read each Wave 1 UC file and patch inconsistencies (voice, terminology, owner naming format, Action field) via Edit on the specific file. Do NOT re-draft briefs.
- [ ] Write Wave 2 summary briefs in main context — one file per initiative (`usecase-briefs/UC-008.md` onward). Schema: Opportunity reference, type, situation, hypothesis, expected value range, key dependencies.
- [ ] Write Wave 3 placeholders in main context — one file per initiative. Schema: Opportunity reference, type, capability area, strategic hypothesis, re-scoping trigger.
- [ ] Assemble `usecase-briefs/_index.md` in main context — master index table (UC-NNN, OPP ref, title, type, wave, month target, sourcing, one-line description)
- [ ] Dispatch `opportunity-reviewer` subagent — pass `_index.md` content; reviewer may flag specific UC files for completeness issues
- [ ] Resolve Critical findings by editing the specific `UC-NNN.md` file affected
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:collecting-cost-actuals`

## Workflow

1. Confirm preconditions.
2. Create the `usecase-briefs/` folder. Dispatch `usecase-brief-drafter` agents in parallel — one per Wave 1 opportunity. Pass each agent: engagement folder path, OPP-ID, UC-NNN assignment. The agent reads `opportunities/OPP-NNN.md`, `scores/OPP-NNN.md`, and `grc/OPP-NNN.md` (if it exists) directly. Do NOT share cross-OPP context between agents.
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

**Output rule:** Do NOT reproduce the contents of any UC-NNN.md brief in this response. State each file path and a one-sentence summary per brief only. Do not echo brief content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: Wave 1 briefs written (count), Wave 2 summaries (count), any completeness gaps flagged by reviewer.

**Session boundary:** After the user approves the usecase-briefs folder, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:collecting-cost-actuals` to begin Phase 8.5. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:collecting-cost-actuals` (Phase 8.5 — collects labor rates, vendor quotes, and IT estimates before the business case)
