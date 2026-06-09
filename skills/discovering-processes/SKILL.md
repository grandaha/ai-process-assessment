---
name: ai-process-assessment:discovering-processes
description: Phase 4 — evidence-gathering core. Maps processes via four-round interview sequence (sponsor → operator → adjacent → clarification), captures volume/cycle time/error rate/FTE for every process. Enforces the Baseline, Value & Challenge gate. Saves process-map.md and baselines.md.
---

# Phase 4: Discovering Processes

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `tech-inventory.md`, `context.md` — confirm each exists.
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently, extract the `intake_root` field from its YAML frontmatter, and note the Phase Intake Map. At all four interview rounds in the Workflow below, read `<intake_root>/interview-notes.md` instead of conducting live stakeholder interviews.

Gate condition: `tech-inventory.md` must be present before proceeding.

## Role in the system

This is the evidence-gathering core of the methodology. Everything downstream — opportunity identification, scoring, sequencing, brief writing — cites this phase's output. Two artifacts come out: `process-map.md` describes how work actually happens, and `baselines.md` captures the metrics that ground every later value claim.

## Gate condition

`tech-inventory.md` must exist. The engagement's `evidence-log.md` should be active and used to record interview rounds. This skill creates `process-map.md` AND `baselines.md`.

## Baseline, Value & Challenge Gate

This is the single most load-bearing rule in the methodology.

For every process mapped, `baselines.md` MUST contain at minimum:

- **Volume** — transactions per unit time (e.g., "1,200 invoices/month")
- **Cycle time** — median and P90 (e.g., "median 4h, P90 18h")
- **Error / exception rate** — what fraction of transactions deviate from happy path
- **FTE effort estimate** — current human effort consumed (e.g., "2.4 FTE-equivalent")

**No value claim may be made in any subsequent phase without citing a baseline from this file.**

If a baseline cannot be sourced (estimated by an operator, pulled from a system, sampled), the process does not advance to Phase 5. It is logged as "baseline unavailable" with a remediation action.

**Challenge clause (second-order check).** For every process mapped, `process-map.md` MUST also carry a **challenge hypothesis** (see Key Outputs). Automate a broken process and you get a faster broken process — this clause forces the question of whether the process structure itself is the constraint before any automation is typed. A process with no challenge hypothesis does not advance to Phase 5: it is logged as "challenge hypothesis unavailable" with a remediation action (return to the sponsor for the three structural questions), identically to a missing baseline. The hypothesis *surfaces* the redesign question; it does not solve it, and the signal it produces downstream annotates — it never blocks opportunity creation.

## Recording baselines for the engine

Capture each baseline as raw, sourced inputs in the engagement's `model/baselines.json` (per process: `volume`, `cycle_time_median`, `cycle_time_p90`, `error_rate`, `fte`, and the source). Any *derived* figure (e.g. a monthly volume that is `per-period × periods`, or an FTE roll-up) is computed by the engine, not multiplied in prose. `baselines.md` remains the human-readable, source-cited narrative; `model/baselines.json` feeds the engine and downstream `results.json` so every derived figure is deterministic and auditable.

## Four-Round Interview Sequence

1. **Sponsor — strategic framing + structural challenge.** What does this process exist to achieve? What would success look like to the business? Then ask the three **structural challenge** questions, once per process the engagement will map. Ask the sponsor, not the operator — the operator will defend the current structure:
   - **Is the process boundary right?** Does the process exist because of a legacy constraint (system limitation, org structure, manual handoff) that AI could eliminate entirely — making the process *unnecessary* rather than faster?
   - **Is the actor model right?** Does the current allocation of steps to roles reflect what those roles should own, or what they were forced to own by capability limits that no longer apply?
   - **Is the sequence right?** Does the order of steps reflect a logical dependency, or a historical artifact of how information used to flow?
2. **Operator — actual execution.** Walk through the process as it actually runs. Capture the workarounds, the exceptions, the "we always have to..." moments.
3. **Adjacent — upstream and downstream.** Talk to the people who feed this process and the people who consume its output. Their pain often defines the real opportunity.
4. **Clarification — resolve conflicts.** Where rounds 1–3 disagree, return with specific questions and reconcile. Document the resolved version AND the disagreement.

## Subagent Dispatch

Interview-round synthesis is offloaded to subagents to keep the main context clean. The main context owns the gate decisions; subagents own the per-round write-up.

- **When:** After raw notes for an interview round are captured, dispatch one `process-mapper` subagent per round to synthesize that round into structured `process-map.md` content. Rounds are independent — dispatch them in a single parallel tool-call batch where notes for more than one round are ready.
- **Pass to each subagent:** engagement folder path, round number, and the raw notes for that round only. The agent reads `tech-inventory.md` itself to extract relevant sections, and applies the `process-map.md`/`baselines.md` field schemas defined in its own agent spec (which mirror the Key Outputs below). It derives its own `_staging/phase4/round-N.md` output path from the engagement folder path and round number. Do not pass any file content to the subagent.
- **Return:** Write structured entries to `<engagement-folder>/_staging/phase4/round-N.md`. Return a one-line summary only: "Round N complete: N processes mapped, N baselines captured." The orchestrator assembles `process-map.md` and `baselines.md` from staging files — it does NOT receive entry content from the subagent.
- **What stays in main context:** The Baseline, Value & Challenge gate, the chain scan across the assembled map, the conflict-resolution decision from Round 4, and **synthesizing the per-process challenge hypothesis** from the Round-1 `Sponsor structural input` (one paragraph per process: structurally sound, or the single surfaced redesign question). These are cross-round judgments and must not be delegated.

## Phase checklist

- [ ] Confirm `tech-inventory.md` exists
- [ ] Round 1: Sponsor interview(s) — strategic framing; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 2: Operator interview(s) — actual execution; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 3: Adjacent interview(s) — upstream / downstream; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 4: Clarification — resolve conflicts; record named participants in `evidence-log.md` stakeholder interview log
- [ ] For every process, capture volume, cycle time (median + P90), error/exception rate, FTE effort
- [ ] For every step in each process, assign AI capability flag (Green / Yellow / Red)
- [ ] Run chain scan — identify consecutive Green runs; record in process-map.md; flag high-fragmentation processes
- [ ] Apply the Baseline, Value & Challenge gate — flag any process missing baselines
- [ ] For every process, synthesize a challenge hypothesis from the sponsor's structural input; flag any process missing one as "challenge hypothesis unavailable"
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
| AI capability per step | For each step in the sequence: AI-capable (Green), Uncertain (Yellow), or Not AI-capable (Red). Record what makes a step hard for AI (judgment, unstructured input, regulatory requirement, etc.). |
| Chain scan | Identify every run of consecutive Green steps. Record the run as [step i → step j] and count how many current human verification points the run would eliminate if chained. Flag processes where Green steps are interleaved with Red steps as high-fragmentation. |
| Challenge hypothesis | One paragraph per process, authored by the orchestrator at assembly from the sponsor's Round-1 structural answers. Either "structurally sound — [why]" or the single surfaced redesign question (boundary / actor model / sequence) with its basis. Surfaces the question; does not solve it. |

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
| "These AI-capable steps are scattered through the process, but we can still automate each one individually." | Scattered AI-capable steps each require their own human verification checkpoint. Linear step-count aggregation overstates value. Record the fragmentation — it determines achievable chain length and is a direct input to opportunity scoring. |
| "The process works — we just need to automate the slow steps." | Automate a broken process and you get a faster broken process. The challenge hypothesis forces the second-order question — is the boundary, actor model, or sequence itself the constraint? — before any automation is typed. Surface it; the client decides. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `process-map.md` or `baselines.md` in this response. State the file paths only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: processes mapped (count), baselines captured, any "baseline unavailable" flags, stakeholder interview log completeness.

**Session boundary:** After the user approves `process-map.md` and `baselines.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:identifying-opportunities` to begin Phase 5. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:identifying-opportunities` (after `process-map.md` and `baselines.md` are saved)
