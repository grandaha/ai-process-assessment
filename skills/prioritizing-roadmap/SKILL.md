---
name: ai-process-assessment:prioritizing-roadmap
description: Phase 7 — sequences scored opportunities into Foundation/Scale/Optimize waves under four constraints: dependency, capacity, quick-win, alignment. Saves roadmap.md.
---

# Phase 7: Prioritizing the Roadmap

## Role in the system

Scoring produces a ranked list. Sequencing produces a roadmap. They are not the same. A high-scoring opportunity that depends on an unbuilt enabler does not belong in Wave 1. This phase applies four sequencing constraints in order to produce Foundation / Scale / Optimize waves.

## Gate condition

`scored-opportunities.md` must exist and the `opportunity-reviewer` clearance must be logged in `evidence-log.md`. This skill creates `roadmap.md`.

## Four Sequencing Constraints (apply in order)

1. **Dependency ordering** — no initiative begins before its enablers exist. An opportunity that requires a missing enabler is either deferred or its enabler is sequenced ahead of it.
2. **Capacity-load check** — no wave is overloaded beyond org absorption rate. Capacity is the limit, not the score.
3. **Quick-win requirement** — at least one opportunity in Wave 1 must produce a measurable outcome by month 3. Programs without early visible wins lose air cover.
4. **Strategic alignment weighting** — used only as the tiebreaker among options that pass the prior three constraints.

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

## Phase checklist

- [ ] Confirm `scored-opportunities.md` saved and reviewer cleared
- [ ] Apply Constraint 1 (Dependency ordering) — flag opportunities with unmet enablers
- [ ] Apply Constraint 2 (Capacity-load check) — confirm each wave is absorbable
- [ ] Apply Constraint 3 (Quick-win requirement) — confirm at least one Wave 1 opportunity has a measurable month-3 outcome
- [ ] Apply Constraint 4 (Strategic alignment) — break ties only after constraints 1–3 are satisfied
- [ ] Map enablers and dependencies for every Wave 1 initiative
- [ ] Dispatch `opportunity-reviewer` subagent for sequencing review
- [ ] Resolve Critical findings
- [ ] Save to `docs/engagements/<engagement>/roadmap.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:packaging-usecases`

## Workflow

1. Confirm preconditions.
2. Build the candidate Wave 1 set from the top of the scored list.
3. Apply constraints 1–3 in order. Each may evict or import an item.
4. Use Constraint 4 only on remaining ties.
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

## Handoff Protocol

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: wave assignments summary, quick-win confirmed (name it), any capacity or dependency flags.

## Chain to next skill

→ `ai-process-assessment:packaging-usecases` (after `roadmap.md` is saved and reviewer cleared)
