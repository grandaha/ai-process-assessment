---
name: ai-process-assessment:discovering-processes
description: Phase 4 — evidence-gathering core. Maps processes via four-round interview sequence (sponsor → operator → adjacent → clarification), captures volume/cycle time/error rate/FTE for every process. Enforces Baseline & Value Hypothesis gate. Saves process-map.md and baselines.md.
---

# Phase 4: Discovering Processes

## Role in the system

This is the evidence-gathering core of the methodology. Everything downstream — opportunity identification, scoring, sequencing, brief writing — cites this phase's output. Two artifacts come out: `process-map.md` describes how work actually happens, and `baselines.md` captures the metrics that ground every later value claim.

## Gate condition

`tech-inventory.md` must exist. The engagement's `evidence-log.md` should be active and used to record interview rounds. This skill creates `process-map.md` AND `baselines.md`.

## Baseline & Value Hypothesis Gate

This is the single most load-bearing rule in the methodology.

For every process mapped, `baselines.md` MUST contain at minimum:

- **Volume** — transactions per unit time (e.g., "1,200 invoices/month")
- **Cycle time** — median and P90 (e.g., "median 4h, P90 18h")
- **Error / exception rate** — what fraction of transactions deviate from happy path
- **FTE effort estimate** — current human effort consumed (e.g., "2.4 FTE-equivalent")

**No value claim may be made in any subsequent phase without citing a baseline from this file.**

If a baseline cannot be sourced (estimated by an operator, pulled from a system, sampled), the process does not advance to Phase 5. It is logged as "baseline unavailable" with a remediation action.

## Four-Round Interview Sequence

1. **Sponsor — strategic framing.** What does this process exist to achieve? What would success look like to the business?
2. **Operator — actual execution.** Walk through the process as it actually runs. Capture the workarounds, the exceptions, the "we always have to..." moments.
3. **Adjacent — upstream and downstream.** Talk to the people who feed this process and the people who consume its output. Their pain often defines the real opportunity.
4. **Clarification — resolve conflicts.** Where rounds 1–3 disagree, return with specific questions and reconcile. Document the resolved version AND the disagreement.

## Phase checklist

- [ ] Confirm `tech-inventory.md` exists
- [ ] Round 1: Sponsor interview(s) — strategic framing; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 2: Operator interview(s) — actual execution; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 3: Adjacent interview(s) — upstream / downstream; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 4: Clarification — resolve conflicts; record named participants in `evidence-log.md` stakeholder interview log
- [ ] For every process, capture volume, cycle time (median + P90), error/exception rate, FTE effort
- [ ] Apply Baseline & Value Hypothesis gate — flag any process missing baselines
- [ ] Save `process-map.md`
- [ ] Save `baselines.md`
- [ ] Confirm `evidence-log.md` stakeholder interview log is complete — one row per session, every participant named
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:identifying-opportunities`

## Key outputs

### process-map.md

| Field | Content |
|---|---|
| Process name and ID | Stable identifier referenced by later phases |
| Trigger | What initiates the process |
| Steps | Actual steps as executed (not as documented) |
| Actors | Roles, systems, and external parties involved |
| Decision points | Where humans exercise judgment; what informs the call |
| Exceptions | Common deviations and how they're handled |
| Upstream / downstream | What feeds this; what consumes its output |
| Conflicts | Where interview rounds disagreed; resolution |

### baselines.md

| Field | Content |
|---|---|
| Process ID | Reference to `process-map.md` |
| Volume | Transactions per unit time, with source |
| Cycle time | Median and P90, with source |
| Error / exception rate | Fraction off happy path, with source |
| FTE effort | Current human effort estimate, with source |
| Source confidence | High (system-pulled) / Medium (sampled) / Low (estimated) |

## Stakeholder Interview Log

After each interview round, append rows to the `## Stakeholder Interview Log` section of `evidence-log.md`. This section is rendered directly in the Evidence tab of the deliverable — it is the auditable record of who contributed to the engagement.

**Required format in `evidence-log.md`:**

```markdown
## Stakeholder Interview Log

| Name | Role | Round | Date | Topics Covered |
|---|---|---|---|---|
| Jennifer Walsh | VP HR Operations | R1 — Sponsor | 2026-05-01 | Strategic framing, constraints, baseline estimates |
| Maria Santos | Sr. Director, HRBPs | R2 — Operator | 2026-05-03 | Req review process, HRBP touchpoints, change mgmt posture |
| [Name] | [Role] | R2 — Operator | [Date] | [Topics] |
```

**Rules:**
- Every participant must be named — no role-only rows (e.g., "3 Recruiters" is not acceptable)
- If a participant requests anonymity, record their role and a note: e.g., "Anonymous — Senior Recruiter (anonymized at participant request)"
- One row per session; if the same person appears in multiple rounds, add a row for each round
- Date is the actual session date, not the phase date
- Topics Covered is a short phrase — enough to reconstruct what was asked

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The sponsor described the process — we don't need to interview operators." | Sponsors describe the process as it should run. Operators describe how it does run. The gap is the opportunity. |
| "Baselines are nice-to-have; we can estimate value." | Estimated value without a baseline is a guess that survives until delivery. Baselines are a hard gate — no value claim survives without one. |
| "Cycle time is hard to get — we'll use 'a few days'." | "A few days" is unfalsifiable. Median + P90 forces honesty and exposes long-tail pain. |
| "FTE effort estimates are sensitive — we'll skip them." | FTE is the most credible value lever to a CFO. Capture it with appropriate framing, not by omission. |
| "Two interview rounds is enough." | Two rounds gives you the sponsor's view and the operator's view but no triangulation. Adjacent and clarification rounds catch what the first two miss. |
| "Recording participant names is administrative overhead — we know who we talked to." | The stakeholder interview log is the only record that survives the engagement. Without it, the deliverable cannot answer "who did you talk to?" — the first question any skeptical executive will ask. Record as you go; reconstructing it from memory at the end is error-prone and often incomplete. |

## Handoff Protocol

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: processes mapped (count), baselines captured, any "baseline unavailable" flags, stakeholder interview log completeness.

## Chain to next skill

→ `ai-process-assessment:identifying-opportunities` (after `process-map.md` and `baselines.md` are saved)
