---
name: ai-process-assessment:running-sample-engagement
description: Guided entry point for the bundled demo engagement. Runs the fictional Lattice Consulting (PSO delivery team) sample intake through the full methodology — Phases 1–11 plus both gates — using sample intake files in place of live interviews. Not a bypass; preserves every gate and session boundary.
---

# Running the Sample Engagement

## What this skill is

A guided **entry point** for the bundled demo engagement. It runs the methodology end-to-end on fictional intake data so a new user can see all eleven phases and both gates work without a live client. It is **not** a shortcut, a fast-path, or an auto-runner. The only thing it changes about a normal engagement is the *source of phase inputs*: wherever a phase would interview a live human, you read a bundled sample intake file instead. Everything else — gate conditions, reviewer dispatches, approval pauses, session boundaries, the GRC gate — runs exactly as in a real engagement.

The sample subject is **Lattice Consulting Group**, a fictional professional-services firm assessing its own delivery team. See `samples/pso-delivery-team/README.md` for the scenario.

## What it is NOT

- **Not auto-chaining.** You still stop at every phase boundary, surface output, and wait for explicit approval before the next phase.
- **Not gate-skipping.** The Baseline, Value & Challenge gate, the GRC gate, the reviewer clearances, and the deliverable gate all run normally.
- **Not a data fabricator.** Phases 1–4 use only what is in the intake files. If something genuinely is not in the intake, log it as a gap exactly as you would in a real engagement — do not invent it. (The intake is built to be sufficient; you should not need to.)
- **Not a single-session run.** Respect the session boundaries. Each phase instructs you to start a fresh session for the next one.

## Setup

At session start:

1. **Locate the intake files.** They ship with the plugin at `samples/pso-delivery-team/intake/`. Confirm the four intake files and the README are present:
   - `samples/pso-delivery-team/intake/engagement-request.md`
   - `samples/pso-delivery-team/intake/org-context.md`
   - `samples/pso-delivery-team/intake/systems-and-data.md`
   - `samples/pso-delivery-team/intake/interview-notes.md`
   - `samples/pso-delivery-team/README.md`
   If they are missing, halt and tell the user where the plugin's `samples/` folder is expected.
2. **Fix the engagement name.** This run uses the engagement name **`sample-pso-delivery`**. The Phase 1 skill will create `sample-pso-delivery/` and write the `Engagement folder:` field into `scope.md`. Do not improvise a different name — downstream the run is expected to live at `sample-pso-delivery/`.
3. **Read the scenario README** (`samples/pso-delivery-team/README.md`) so you understand the case before scoping it.
4. **Write the sample-run marker.** Create the engagement folder (`sample-pso-delivery/`) if it does not already exist, then use the Write tool to create `sample-pso-delivery/.sample-run.md` with exactly this content:

   ```markdown
   ---
   sample: pso-delivery-team
   intake_root: samples/pso-delivery-team/intake
   ---

   # Sample Run Marker

   This file signals that this engagement folder contains a sample run of the
   `pso-delivery-team` scenario. Phase skills check for this file at Session
   Start and substitute bundled intake files for live elicitation.

   ## Phase Intake Map

   | Phase | Intake file (relative to intake_root) |
   |---|---|
   | 1 — Scoping | engagement-request.md |
   | 2 — Context | org-context.md |
   | 3 — Tech & Data | systems-and-data.md |
   | 4 — Discovery | interview-notes.md |
   ```

   This marker persists across session boundaries so every phase skill can detect the sample context without user action.

Then hand off to Phase 1 — do **not** do Phase 1's work in this skill.

## Phase → intake-file mapping

When you run each phase skill, substitute the live-interview step with reading the mapped intake file. Phases 5–11 take **no** new external input — they operate only on prior phase outputs, exactly as normal.

| Phase | Skill | Instead of interviewing a human, read… |
|---|---|---|
| 1 — Scoping | `ai-process-assessment:scoping-engagement` | `intake/engagement-request.md` (use engagement name `sample-pso-delivery`) |
| 2 — Context | `ai-process-assessment:mapping-context` | `intake/org-context.md` |
| 3 — Tech & Data | `ai-process-assessment:inventorying-tech-data` | `intake/systems-and-data.md` |
| 4 — Discovery | `ai-process-assessment:discovering-processes` | `intake/interview-notes.md` (four rounds + baselines are all in this file; reconcile the three conflicts as instructed) |
| 5 — Opportunities | `ai-process-assessment:identifying-opportunities` | *(no new input — uses `processes/PROC-NNN.md` files)* |
| Gate A — GRC | `ai-process-assessment:governance-risk-gate` | *(fires for any non-Green GRC flag — it will fire on the deliverable-content and commercial-data opportunities)* |
| 6 — Scoring | `ai-process-assessment:scoring-opportunities` | *(no new input)* |
| 7 — Roadmap | `ai-process-assessment:prioritizing-roadmap` | *(no new input)* |
| 8 — Use Case Briefs | `ai-process-assessment:packaging-usecases` | *(no new input)* |
| 8.5 — Cost Actuals | `ai-process-assessment:collecting-cost-actuals` | *(no live stakeholders — see note below)* |
| 9 — Business Case | `ai-process-assessment:building-business-case` | *(no new input)* |
| Gate B — Deliverable | `ai-process-assessment:deliverable-gate` | *(runs before Phase 10; checks the artifacts produced through Phase 9 and records clearance in `evidence-log.md`)* |
| 10 — Exec Summary | `ai-process-assessment:building-executive-summary` | *(no new input; requires Gate B clearance in `evidence-log.md` before it may begin)* |
| 11 — Deliverable | `ai-process-assessment:building-deliverable` | *(renders `deliverable.html`)* |

### Note on Phase 8.5 (Cost Actuals)

In a real engagement, Phase 8.5 collects cost data from live stakeholders (labor rates, implementation hours, vendor quotes, IT estimates). In the sample, there are no live stakeholders. Use the firm-level anchors present in the intake — blended bill rate **$225/hr**, fully-loaded cost **~$130K/FTE-year**, the per-process FTE baselines — as the sourced basis, and label any estimate without an internal-actuals basis as a ROM (AACE Class 5, ±50%) exactly as the business-case methodology requires. Do not invent vendor quotes; where a real engagement would have one and the sample does not, record it as an open cost item, which is itself a faithful demonstration of the gate.

## How to run it

1. Confirm setup (above).
2. Invoke `ai-process-assessment:scoping-engagement`. At the live-interview step, read `intake/engagement-request.md` and scope from it. Use engagement name `sample-pso-delivery`.
3. At the end of each phase, follow that phase's normal Handoff Protocol: name the files written, summarize key findings, state the next phase, and **wait for the user's explicit approval**. Then honor the **session boundary** — instruct the user to start a fresh session and invoke the next phase skill, substituting the mapped intake file for the live interview.
4. Continue through Gate A (GRC will fire), scoring, roadmap, briefs, cost actuals, business case, **then Gate B (the deliverable gate, which runs before Phase 10 and must record clearance in `evidence-log.md`)**, exec summary, and finally `building-deliverable`, which renders `deliverable.html`.
5. The run is complete when `sample-pso-delivery/` contains every phase output and `deliverable.html` is rendered.

## Expected outcome (so you can tell whether the run was faithful)

- A populated `sample-pso-delivery/` with every phase's output file present.
- Seven mapped processes (PROC-01…PROC-07) with baselines; the three intake conflicts reconciled in `processes/PROC-NNN.md` files with both the resolved value and the disagreement recorded.
- The GRC gate having fired on at least the deliverable-content (QA) and commercial-data (SOW) opportunities.
- Every value claim in Phases 5–9 citing a baseline from `processes/PROC-NNN.md` — **no orphan value hypotheses**.
- A rendered `deliverable.html` that can serve as the reference example output.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "It's just a sample — I can run all phases in one session." | The point of the sample is to exercise the *real* flow, including session boundaries. Collapsing them tests something the real engagement never does. |
| "It's fake data, so I can skip the GRC gate." | The sample is built specifically so the GRC gate fires. Skipping it defeats the demonstration. |
| "The intake doesn't have a vendor quote — I'll make one up." | Invent nothing. A missing cost input is logged as an open item, which is exactly how the real methodology behaves. |
| "I'll pre-fill the phase outputs to save time." | There is no answer key on purpose. The phases must interpret the raw intake, or the run proves nothing. |
| "I can pick a cleaner engagement name." | The run is expected at `sample-pso-delivery/`. Use that name. |

## Handoff Protocol

This skill does not produce a phase output of its own. After setup, hand off to Phase 1:

1. Confirm the intake files are present and the engagement name is `sample-pso-delivery`.
2. State that the next step is `ai-process-assessment:scoping-engagement`, reading `intake/engagement-request.md` in place of a live sponsor interview.
3. **Wait for the user to proceed.** From here on, every phase transition is a normal human-approved gate.

## Chain to next skill

→ `ai-process-assessment:scoping-engagement` (Phase 1, reading `samples/pso-delivery-team/intake/engagement-request.md`)
