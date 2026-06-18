---
name: ai-process-assessment:conducting-engagement
description: Front door and autonomous driver — on a natural-language request ("help me find AI opportunities", "assess this client/team"), drives the full 11-phase methodology end-to-end — derives state from the engagement folder, interviews only for gaps, dispatches phases, runs the engine, and stops only at genuine human-decision points. Honors using-methodology as the rulebook.
---

# Conducting an Engagement

<EXTREMELY-IMPORTANT>
You are the driver. The human should never need to know the phase names, the file
layout, or which skill to invoke. You derive what's next from the engagement folder
and take the next action yourself, pausing only at the touchpoints in the table below.
You honor `ai-process-assessment:using-methodology` as the rulebook — you never skip a
phase or compute a number in prose. CLAUDE.md overrides this skill only where it says so.
</EXTREMELY-IMPORTANT>

## When this skill runs

On any natural-language opener that means "assess / find AI opportunities / evaluate
automation" for a team, client, process, or use case. You become the front door — no
magic phrase required.

## Intake (first contact only)

1. **Infer register, confirm in one line.** From how they phrased the request, infer
   **consultant** (domain-fluent, relaying interviews they ran) or **operator** (their
   own team, no methodology training). Confirm in a single sentence and move on — never
   a cold multiple-choice quiz. Example: "Sounds like you're assessing your own team —
   I'll keep it plain and explain as we go; tell me if you'd rather I move fast."
2. **Set autonomy preset** (default **guided**): guided = confirm each phase transition
   and every checkpoint/gate; autonomous = drive without per-step confirmation, stopping
   only at must-ask points. (Slice 1 runs should-confirm in guided mode.)
3. **Run Phase 1** inline (`ai-process-assessment:scoping-engagement`) — this creates the
   engagement folder, `scope.md`, and the gitignore entry.
4. **Stamp `.conductor.md`** with `register`, `autonomy.should_confirm`,
   `methodology_version` (read from `.claude-plugin/plugin.json`), and empty
   `open_decisions` / `deferred_processes`. Use:
   `python -c "from cockpit.conductor_state import write_conductor; ..."`.

## The drive loop

Repeat until Phase 11 is done and Gate B is cleared:

0. **Resolve the active engagement:** the folder containing a `.conductor.md` whose work
   is incomplete. None → run Intake. More than one incomplete → ask which.
1. **Read state:** `python -m cockpit.state <folder>` → JSON snapshot.
2. **Reconcile overrides:** apply `cockpit.overrides.parse_overrides(CLAUDE.md)` +
   `reconcile(...)` so authorized skips don't block. An override row only fires if its
   Override cell contains the phase's output filename (e.g. `context.md`) or skill dir
   name (e.g. `mapping-context`); a row that names the phase only in prose is silently
   ignored. If a Methodology Overrides row clearly intends a phase but carries no such
   token, surface it and ask the human to add it (must-ask) — never proceed as if the
   phase were unskipped.
3. **Check staleness:** load `model_input_hashes` from `.conductor.md`; if
   `cockpit.staleness.changed_inputs(folder, recorded)` is non-empty, a model input
   changed — re-run the engine and re-drive the affected portfolio phases forward
   (see "Staleness" below) before doing anything else.
4. **Pick the next step:** the first phase whose status is `available`/`overridden`.
   Respect the convergence gate (below) before any portfolio phase.
5. **Gather gaps, then execute** per the execution model below.
6. **After a step that wrote a `model/*.json` input,** run `python -m engine.run <folder>/`
   then `cockpit.conductor_state.record_input_hashes(folder)`.
7. **At a checkpoint insertion point** (per the `building-checkpoint` registry: after
   Phase 2 `scope`, Phase 4 `baseline`, Phase 7 `portfolio`): offer to generate it
   (should-confirm); its stakeholder **outcome** is must-ask.
8. **If a gate triggers** (GRC non-green in `opportunities/_index.md`, or before any
   external share): run the gate; surface the result.
9. **Record this step's structural-class decisions** to the decision log (below).
10. **Pause** at the right touchpoint (table below); otherwise continue.

## Execution model — who talks to the human (§4.4)

- **Interview-heavy phases run inline in your own context:** Phase 1 (scoping), Phase 4
  (discovery), Phase 8.5 (cost actuals). Conduct their questioning yourself, write the
  output file, then drop the transcript and keep only the state snapshot.
- **Headless phases you dispatch to a subagent:** Phases 2, 3, 5, 6, 7, 9, 10, 11, the
  checkpoints, and the GRC/deliverable gates. A subagent cannot ask the human, so before
  dispatch you must have every input it needs on disk. Hand the subagent the engagement
  folder path and the phase skill to run; receive a one-line confirmation; re-read state.
- **Input contract:** before dispatching a headless phase, confirm its predecessor files
  exist and gather any human-supplied value it needs via a targeted inline question — a
  **must-ask** if it's a decision (e.g., Build/Buy/Partner), a **should-confirm** if it's
  draftable.

## Touchpoint taxonomy

| Class | Behavior | Examples |
|---|---|---|
| Must-ask | Always stop, every mode | Sponsoring question, decision-maker, scope boundaries, out-of-scope process additions, cost actuals, checkpoint outcomes, gate dispositions, Build/Buy/Partner |
| Should-confirm | Guided: pause to approve. (Autonomous batching is Slice 2.) | Context map, opportunity log, scoring rationale, roadmap sequencing |
| Can-infer | Never ask | Run the engine, derive state, pick next phase, assemble deliverable HTML |

## Elastic processes & convergence

- An engagement is one portfolio holding 1..N processes; N=1 is the same spine with one
  process, nothing skipped.
- **Convergence gate:** before the first portfolio phase (Phase 6), confirm
  `processes/_index.md` lists every in-scope process with `Baseline = Ready`. A process
  intentionally held back goes in `.conductor.md` `deferred_processes` (deferring is a
  must-ask). Do not score a half-discovered portfolio.
- **Cross-process chain-detection:** at convergence (Phase 5 → 6), in the merged context
  where all processes' opportunities are visible, scan for a Chain Automation that spans
  process boundaries — a step that is no candidate alone but eliminates a verification
  checkpoint when chained. Per-process work cannot see this; you must.
- **Adding a process:** within stated scope → free (should-confirm), then re-converge.
  Outside scope → must-ask: expand scope or start a new engagement.

## Scope is the container

`scope.md` bounds the engagement. Adding work inside it is routine; adding work outside
it is a must-ask. A genuinely separate concern is a new engagement, not a bigger one.

## Decision log — `<engagement>/decision-log.md`

Record both parties' structural-class decisions (type classification, scores, roadmap
sequencing/wave, choosing between ≥2 viable options, selecting a non-default the rubric
didn't recommend). Never log by your own sense of importance; log by class. Append-only;
never edit a prior entry. When a human overrides your draft, record BOTH — never
overwrite. Entry template:

```
## <ISO datetime> — <decision class> — <OPP/PROC id or "portfolio">
- proposed_by: agent | human
- decided_by: agent-auto | human-ratified | human-overrode
- disposition: accepted | edited | overridden→<X> | invalidated-by-{staleness|checkpoint|gate}
- decision: <what was decided>
- rationale: <why>
- evidence: <file path + section/anchor, or model/*.json key>
```

## Staleness

When `changed_inputs` is non-empty: re-run `python -m engine.run <folder>/`, then
re-drive every portfolio phase downstream of the change. Any human ratification given
against the now-superseded numbers is recorded `invalidated-by-staleness` in the decision
log and re-surfaced per its touchpoint class — never silently kept. After a clean
re-drive, call `record_input_hashes` so outputs read clean again.

## Failure & rejection handling

- Phase subagent fails or `engine.run` errors → stop, surface the error (must-ask). Never
  advance on a failed step.
- Gate rejects → surface the failed dimension, route to its owning phase, re-drive forward.
- Checkpoint rejected → route to the checkpoint's route-back phase (registry), which
  triggers staleness forward.

## Sample mode

If the engagement folder contains `.sample-run.md`, drive with the bundled sample data
and do not prompt for live stakeholders (mirror the existing sample-run convention).
