---
name: ai-process-assessment:packaging-usecases
description: Phase 8 — produces self-contained Use Case Brief (UC-NNN) per Wave 1 initiative using Situation-Complication-Resolution-Action structure. Saves usecase-briefs.md.
---

# Phase 8: Packaging Use Cases

## Role in the system

The brief is the unit of delivery. Each Wave 1 opportunity becomes a self-contained brief that an executive can read in five minutes and act on. Wave 2 items get summary briefs; Wave 3 items get capability-area placeholders. The Situation-Complication-Resolution-Action structure forces business framing before technical solutioning.

## Gate condition

`roadmap.md` must exist and the `opportunity-reviewer` clearance for the roadmap must be logged. This skill creates `usecase-briefs.md`.

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
- [ ] Dispatch one `usecase-brief-drafter` agent per Wave 1 opportunity in a single parallel tool-call batch (pass: OPP entry, relevant process-map.md sections, baselines.md rows, scored-opportunities.md row, roadmap.md entry, GRC conditions if applicable, and staging file path: `<engagement-folder>/_staging/phase8/UC-NNN.md`)
- [ ] Collect one-line summaries from agents (UC-NNN, OPP-NNN, wave, any flags). Full briefs are in staging files.
- [ ] Assemble via Bash: `cat docs/engagements/<name>/_staging/phase8/UC-*.md > docs/engagements/<name>/usecase-briefs.md`
- [ ] Verify: `wc -l docs/engagements/<name>/usecase-briefs.md`
- [ ] Run a consistency pass on the assembled file — read the file once with offset/limit and patch inconsistencies (voice, terminology, owner naming format) via Edit tool. Do NOT re-draft briefs.
- [ ] Cleanup: `rm -rf docs/engagements/<name>/_staging/phase8`
- [ ] For each Wave 2 initiative, write a summary brief (Opportunity reference, type, situation, hypothesis, expected value range, dependencies)
- [ ] For Wave 3, list capability areas with the trigger that promotes them
- [ ] Dispatch `opportunity-reviewer` subagent for brief completeness review
- [ ] Resolve Critical findings
- [ ] Save to `docs/engagements/<engagement>/usecase-briefs.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:building-business-case`

## Workflow

1. Confirm preconditions.
2. Dispatch `usecase-brief-drafter` agents in parallel — one per Wave 1 opportunity. Pass each agent its OPP entry, the relevant sections from the source files, and its staging file path (`_staging/phase8/UC-NNN.md`). Do NOT share cross-OPP context between agents. Collect one-line summaries only.
3. Assemble: `cat _staging/phase8/UC-*.md > usecase-briefs.md`. Verify with `wc -l`. Cleanup `_staging/phase8`. Run a consistency pass on the assembled file: normalize voice (direct, present-tense situation / conditional resolution/action), verify owner naming format, confirm wave month targets match roadmap.md. Do NOT re-draft briefs — patch inconsistencies only via Edit tool.
4. Action field requires a named owner and a date — not "the team will...".
5. Wave 2 summary briefs follow a thinner schema; Wave 3 are placeholders with promotion triggers.
6. Dispatch reviewer. Resolve Critical findings.
7. Save. Final step before any external sharing is the `deliverable-gate`.

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

→ `ai-process-assessment:building-business-case` (Phase 9 — produces the Wave 1 ROM business case before the deliverable gate)
