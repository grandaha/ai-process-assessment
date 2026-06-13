---
name: ai-process-assessment:running-sample-engagement
description: Guided entry point for a sample engagement. Asks whether to use the bundled PSO demo or generate a new scenario for any business model, then runs the full methodology — Phases 1–11 plus both gates — using sample intake files in place of live interviews. Not a bypass; preserves every gate and session boundary.
---

# Running the Sample Engagement

## Step 0 — Choose your scenario

Before any setup, ask the user which scenario to use:

> **Which sample scenario would you like to run?**
>
> **A. Professional services — Lattice Consulting Group (bundled)**
> The pre-built PSO delivery team demo. Intake files are already present in `samples/pso-delivery-team/intake/`. Best for a quick first run.
>
> **B. Generate a new scenario for a different business model**
> Synthesize a complete set of intake files tailored to an industry and team you choose. Invoke `ai-process-assessment:generating-sample-intake` now. When the generator completes, it will write the intake files and confirm the engagement name and intake root — then return here and continue from **Setup** below, substituting that engagement name and intake root wherever you see `sample-pso-delivery` and `samples/pso-delivery-team/intake`.

**If the user chooses A:** proceed directly to **Setup** below. All steps apply exactly as written.

**If the user chooses B:** chain to `ai-process-assessment:generating-sample-intake` in this session. Do not continue to Setup until the generator confirms it is complete and provides the engagement name (`sample-<slug>`) and intake root (`samples/<slug>/intake`). Then return here and substitute those values throughout Setup and the Phase → intake-file mapping.

---

## What this skill is

A guided **entry point** for a sample engagement. It runs the methodology end-to-end on fictional intake data so a new user can see all eleven phases and both gates work without a live client. It is **not** a shortcut, a fast-path, or an auto-runner. The only thing it changes about a normal engagement is the *source of phase inputs*: wherever a phase would interview a live human, you read a sample intake file instead. Everything else — gate conditions, reviewer dispatches, approval pauses, session boundaries, the GRC gate — runs exactly as in a real engagement.

For the bundled PSO scenario, the sample subject is **Lattice Consulting Group**, a fictional professional-services firm assessing its own delivery team. See `samples/pso-delivery-team/README.md` for that scenario. For a generated scenario, see `samples/<slug>/README.md`.

## What it is NOT

- **Not auto-chaining.** You still stop at every phase boundary, surface output, and wait for explicit approval before the next phase.
- **Not gate-skipping.** The Baseline, Value & Challenge gate, the GRC gate, the reviewer clearances, and the deliverable gate all run normally.
- **Not a data fabricator.** Phases 1–4 use only what is in the intake files. If something genuinely is not in the intake, log it as a gap exactly as you would in a real engagement — do not invent it. (The intake is built to be sufficient; you should not need to.)
- **Not a single-session run.** Respect the session boundaries. Each phase instructs you to start a fresh session for the next one.

## Setup

> **Generated scenario (stop here first):** If you are running a generated scenario (chosen B in Step 0), the generator has already written the intake files and `.sample-run.md` marker. Skip steps 1 and 4 below entirely. Substitute your scenario's engagement name for `sample-pso-delivery` and its intake root for `samples/pso-delivery-team/intake` everywhere in the remaining steps and in the Phase → intake-file mapping. Then proceed directly to step 3 (read the README) and the Phase 1 handoff.

At session start:

1. **Locate the PSO intake files** *(PSO path only — skip if running a generated scenario).* They ship with the plugin at `samples/pso-delivery-team/intake/`. Confirm the four intake files and the README are present:
   - `samples/pso-delivery-team/intake/engagement-request.md`
   - `samples/pso-delivery-team/intake/org-context.md`
   - `samples/pso-delivery-team/intake/systems-and-data.md`
   - `samples/pso-delivery-team/intake/interview-notes.md`
   - `samples/pso-delivery-team/README.md`
   If they are missing, halt and tell the user where the plugin's `samples/` folder is expected.
2. **Fix the engagement name.** This run uses the engagement name **`sample-pso-delivery`**. The Phase 1 skill will create `sample-pso-delivery/` and write the `Engagement folder:` field into `scope.md`. Do not improvise a different name — downstream the run is expected to live at `sample-pso-delivery/`.
3. **Read the scenario README** (`samples/pso-delivery-team/README.md`) so you understand the case before scoping it.
4. **Write the sample-run marker** *(PSO path only — skip if running a generated scenario; the generator already wrote it).* Create the engagement folder (`sample-pso-delivery/`) if it does not already exist, then use the Write tool to create `sample-pso-delivery/.sample-run.md` with exactly this content:

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
| 1 — Scoping | `ai-process-assessment:scoping-engagement` | `[intake_root]/engagement-request.md` (use engagement name confirmed in setup) |
| 2 — Context | `ai-process-assessment:mapping-context` | `[intake_root]/org-context.md` |
| 3 — Tech & Data | `ai-process-assessment:inventorying-tech-data` | `[intake_root]/systems-and-data.md` |
| 4 — Discovery | `ai-process-assessment:discovering-processes` | `[intake_root]/interview-notes.md` (four rounds + baselines are all in this file; reconcile all conflicts as instructed) |
| 5 — Opportunities | `ai-process-assessment:identifying-opportunities` | *(no new input — uses `processes/PROC-NNN.md` files)* |
| Gate A — GRC | `ai-process-assessment:governance-risk-gate` | *(fires for any non-Green GRC flag — it will fire on at least one opportunity in every sample scenario)* |
| 6 — Scoring | `ai-process-assessment:scoring-opportunities` | *(no new input)* |
| 7 — Roadmap | `ai-process-assessment:prioritizing-roadmap` | *(no new input)* |
| 8 — Use Case Briefs | `ai-process-assessment:packaging-usecases` | *(no new input)* |
| 8.5 — Cost Actuals | `ai-process-assessment:collecting-cost-actuals` | *(no live stakeholders — see note below)* |
| 9 — Business Case | `ai-process-assessment:building-business-case` | *(no new input)* |
| Gate B — Deliverable | `ai-process-assessment:deliverable-gate` | *(runs before Phase 10; checks the artifacts produced through Phase 9 and records clearance in `evidence-log.md`)* |
| 10 — Exec Summary | `ai-process-assessment:building-executive-summary` | *(no new input; requires Gate B clearance in `evidence-log.md` before it may begin)* |
| 11 — Deliverable | `ai-process-assessment:building-deliverable` | *(renders `deliverable.html`)* |

### Note on Phase 8.5 (Cost Actuals)

In a real engagement, Phase 8.5 collects cost data from live stakeholders (labor rates, implementation hours, vendor quotes, IT estimates). In the sample, there are no live stakeholders. Use the firm-level anchors present in the intake's Consolidated Baseline Table (blended labor rate, FTE fully-loaded cost, the per-process FTE baselines) as the sourced basis, and label any estimate without an internal-actuals basis as a ROM (AACE Class 5, ±50%) exactly as the business-case methodology requires. Do not invent vendor quotes; where a real engagement would have one and the sample does not, record it as an open cost item, which is itself a faithful demonstration of the gate.

## How to run it

1. Complete Step 0 (scenario chooser). If generating a new scenario, wait for `generating-sample-intake` to complete before proceeding.
2. Confirm setup (above). For a generated scenario, verify the `.sample-run.md` marker was written by the generator and skip writing it again.
3. Invoke `ai-process-assessment:scoping-engagement`. At the live-interview step, read `[intake_root]/engagement-request.md` and scope from it. Use the engagement name confirmed in setup (`sample-pso-delivery` for PSO; `sample-<slug>` for a generated scenario).
4. At the end of each phase, follow that phase's normal Handoff Protocol: name the files written, summarize key findings, state the next phase, and **wait for the user's explicit approval**. Then honor the **session boundary** — instruct the user to start a fresh session and invoke the next phase skill, substituting the mapped intake file for the live interview.
5. Continue through Gate A (GRC will fire), scoring, roadmap, briefs, cost actuals, business case, **then Gate B (the deliverable gate, which runs before Phase 10 and must record clearance in `evidence-log.md`)**, exec summary, and finally `building-deliverable`, which renders `deliverable.html`.
6. The run is complete when the engagement folder contains every phase output and `deliverable.html` is rendered.

## Expected outcome (so you can tell whether the run was faithful)

- A populated engagement folder with every phase's output file present.
- All in-scope processes mapped (PROC-01…PROC-0N) with baselines; all intake conflicts reconciled in `processes/PROC-NNN.md` files with both the resolved value and the disagreement recorded.
- The GRC gate having fired on at least one opportunity (PSO: deliverable-content and commercial-data; generated scenarios: whichever process touches the High-sensitivity data asset).
- Every value claim in Phases 5–9 citing a baseline from `processes/PROC-NNN.md` — **no orphan value hypotheses**.
- A rendered `deliverable.html` that can serve as the reference example output.

**PSO-specific:** Seven processes (PROC-01…PROC-07); three conflicts; GRC fires on deliverable-content (QA) and commercial-data (SOW) opportunities.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "It's just a sample — I can run all phases in one session." | The point of the sample is to exercise the *real* flow, including session boundaries. Collapsing them tests something the real engagement never does. |
| "It's fake data, so I can skip the GRC gate." | The sample is built specifically so the GRC gate fires. Skipping it defeats the demonstration. |
| "The intake doesn't have a vendor quote — I'll make one up." | Invent nothing. A missing cost input is logged as an open item, which is exactly how the real methodology behaves. |
| "I'll pre-fill the phase outputs to save time." | There is no answer key on purpose. The phases must interpret the raw intake, or the run proves nothing. |
| "I can pick a cleaner engagement name." | For PSO: the run is expected at `sample-pso-delivery/`. For generated scenarios: use the `sample-<slug>` name the generator confirmed. Do not improvise. |

## Handoff Protocol

This skill does not produce a phase output of its own. After setup, hand off to Phase 1:

1. Confirm the intake files are present at `[intake_root]/` and state the engagement name (`sample-pso-delivery` for PSO; `sample-<slug>` for a generated scenario).
2. State that the next step is `ai-process-assessment:scoping-engagement`, reading `[intake_root]/engagement-request.md` in place of a live sponsor interview.
3. **Wait for the user to proceed.** From here on, every phase transition is a normal human-approved gate.

## Chain to next skill

→ `ai-process-assessment:generating-sample-intake` (if running a generated scenario — invoke first, then return here)  
→ `ai-process-assessment:scoping-engagement` (Phase 1, reading `[intake_root]/engagement-request.md`)
