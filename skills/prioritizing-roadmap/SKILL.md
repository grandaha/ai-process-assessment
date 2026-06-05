---
name: ai-process-assessment:prioritizing-roadmap
description: Phase 7 — sequences scored opportunities into Foundation/Scale/Optimize waves under five constraints: dependency, capacity, quick-win, alignment, job boundary impact. Saves roadmap.md.
---

# Phase 7: Prioritizing the Roadmap

## Session Start

This skill runs as a standalone session. At session start:
1. Confirm the engagement folder path with the user if not already provided.
2. Read `scores/_index.md` — confirm it exists.
3. Check `evidence-log.md` — confirm opportunity-reviewer clearance from Phase 6.

Gate condition: `scores/_index.md` present; reviewer clearance logged in `evidence-log.md`.

## Role in the system

Scoring produces a ranked list. Sequencing produces a roadmap. They are not the same. A high-scoring opportunity that depends on an unbuilt enabler does not belong in Wave 1. This phase applies four sequencing constraints in order to produce Foundation / Scale / Optimize waves.

## Gate condition

`scores/_index.md` must exist and the `opportunity-reviewer` clearance must be logged in `evidence-log.md`. This skill creates `roadmap.md`.

## Five Sequencing Constraints (apply in order)

1. **Dependency ordering** — no initiative begins before its enablers exist. An opportunity that requires a missing enabler is either deferred or its enabler is sequenced ahead of it.
2. **Capacity-load check** — no wave is overloaded beyond org absorption rate. Capacity is the limit, not the score.
3. **Quick-win requirement** — at least one opportunity in Wave 1 must produce a measurable outcome by month 3. Programs without early visible wins lose air cover. An opportunity flagged Long-run in `scores/OPP-NNN.md` is not eligible for the quick-win slot unless its org design dependency is already resolved.
4. **Strategic alignment weighting** — used only as the tiebreaker among options that pass the prior three constraints.
5. **Job boundary impact** — Short-run opportunities (AI deployable within existing job and role structures) are eligible for Wave 1. Long-run opportunities (value requires redesigning how tasks are bundled across workers) belong in Wave 2 at earliest. A Long-run item placed in Wave 1 requires a documented org design workstream as a named dependency — without it, the opportunity is sequenced to Wave 2.

## Roadmap Wave Definitions

| Wave | Horizon | Specification depth |
|---|---|---|
| Foundation | 0–6 months | Fully specified — owners, success metrics, enablers, sourcing, milestones |
| Scale | 6–18 months | Directional — type, scope, expected value range, key dependencies |
| Optimize | 18–36 months | Strategic intent only — capability area, hypothesis, signal that triggers re-scoping |

## Enabler & Dependency Mapping

Each Wave 1 initiative MUST list its enablers. Unresolved enabler dependencies disqualify Wave 1 placement without documented remediation. If an enabler is missing, either:

- Sequence the enabler itself as a Wave 1 initiative, OR
- Move the dependent opportunity to Wave 2 with the enabler in Wave 1, OR
- Document a remediation plan with named owner and completion date

## Subagent Dispatch

Sequencing is a whole-portfolio judgment and stays in the main context — the five constraints interact, so they cannot be parallelized per opportunity. Only the independent review is delegated.

- **When:** After the candidate waves are built and enablers are mapped, dispatch the `opportunity-reviewer` subagent over the assembled `roadmap.md` draft for sequencing review.
- **Pass to the subagent:** engagement folder path. The reviewer reads `roadmap.md` and `scores/_index.md` (plus individual `scores/OPP-NNN.md` files as needed) itself. Do not pass document content.
- **Return:** The reviewer appends findings to `<engagement-folder>/evidence-log.md` directly. Returns one-line summary: "N Critical, N Important, N Minor findings." The orchestrator does NOT receive full review content.
- **What stays in main context:** All five sequencing constraints, wave assignment, enabler/dependency resolution, and Critical-finding resolution. The constraint logic is never delegated — only its review.

## Phase checklist

- [ ] Confirm `scores/_index.md` exists and reviewer cleared from Phase 6
- [ ] Apply Constraint 1 (Dependency ordering) — flag opportunities with unmet enablers
- [ ] Apply Constraint 2 (Capacity-load check) — confirm each wave is absorbable
- [ ] Apply Constraint 3 (Quick-win requirement) — confirm at least one Wave 1 opportunity has a measurable month-3 outcome
- [ ] Apply Constraint 4 (Strategic alignment) — break ties only after constraints 1–3 are satisfied
- [ ] Apply Constraint 5 (Job boundary impact) — flag Long-run opportunities; confirm org design workstream exists before placing in Wave 1
- [ ] Map enablers and dependencies for every Wave 1 initiative
- [ ] For any Wave 2/3 item with conditional placement, flag it explicitly in the wave summary table row — not only in dependency notes
- [ ] For every cross-wave dependency (e.g., Wave 2 item depends on Wave 1 item being live), state a minimum operational maturity threshold (e.g., "OPP-NNN must be in stable production for ≥60 days before this item is scoped")
- [ ] For cascading timelines (Wave 2 start date derived from Wave 1 go-live date), document the slip risk explicitly: if Wave 1 item slips N months, Wave 2 item's earliest start slides by the same N
- [ ] For Wave 3 re-scoping triggers, verify each trigger is a measurable operational state — not a budget event, procurement approval, or funding decision. If a budget dependency exists, call it a precondition separate from the trigger.
- [ ] Dispatch `opportunity-reviewer` subagent for sequencing review
- [ ] Resolve Critical findings
- [ ] Save to `docs/engagements/<engagement>/roadmap.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:packaging-usecases`

## Workflow

1. Confirm preconditions.
2. Build the candidate Wave 1 set from the top of the scored list.
3. Apply constraints 1–3 in order. Each may evict or import an item.
4. Use Constraint 4 only on remaining ties.
5. Apply Constraint 5 — check Execution Horizon flag (from `scores/OPP-NNN.md`) on each Wave 1 candidate. Move Long-run items to Wave 2 unless org design dependency is documented and sequenced.
5. Map enablers for the final Wave 1. Resolve gaps using one of the three options above.
6. Run `opportunity-reviewer`. Resolve Critical findings.
7. Save and chain forward.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Top-scored opportunities go in Wave 1." | Score ranks; constraints sequence. A top-scored item with unmet enablers is a Wave 2 item. |
| "Capacity will sort itself out." | Wave overload is the most common roadmap failure mode. Capacity is the constraint, not the aspiration. |
| "Quick wins are nice but optional." | Quick wins are the air cover that buys you Waves 2 and 3. They are not optional. |
| "Strategic alignment is the most important factor." | Strategic alignment is the tiebreaker among feasible options, not a substitute for dependency or capacity logic. |
| "Wave 3 doesn't need real specification." | Wave 3 is strategic intent — but the trigger that promotes a Wave 3 item to Wave 2 must be named, or the wave decays into a wishlist. |
| "This opportunity scores high — it goes in Wave 1." | Check the Execution Horizon flag. A Long-run opportunity requires job or role boundary redesign before value is realized. High score does not override the org design dependency. Place in Wave 2 unless the redesign workstream is already funded and sequenced ahead of it. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `roadmap.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: wave assignments summary, quick-win confirmed (name it), any capacity or dependency flags.

**Session boundary:** After the user approves `roadmap.md` and the reviewer is cleared, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:packaging-usecases` to begin Phase 8. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:packaging-usecases` (after `roadmap.md` is saved and reviewer cleared)
