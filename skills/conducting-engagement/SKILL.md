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

## First contact

On a **fresh session where the user has not given a clear assess-request and is not
clearly resuming** (they open with "hi", "what is this", or nothing specific), greet them
and offer the paths that fit what already exists — do NOT jump straight into Intake. On a
clear request ("assess my billing team"), skip the greeting and start. On a clear
"continue/resume", resolve and pick up — no greeting.

Resolve existing engagements first (folders with a `.conductor.md` whose work is
incomplete — the same resolution the drive loop's step 0 performs), then offer:

| Engagements found | Offer |
|---|---|
| None | **Start an assessment** · **Run the sample** |
| One | **Continue "&lt;name&gt;"** (lead) · **Start an assessment** · **Run the sample** |
| More than one | list them, then **Continue one (which?)** · **Start an assessment** · **Run the sample** |

Continue appears only when there is something to continue.

The greeting is warm and capability-framed — no step/phase names, no commands:

<!-- greeting:start -->
> Hi — I'm your AI assessment guide. I turn plain-language goals into **audited numbers**
> on where AI and automation can save your team time and money. You don't need to know any
> steps or commands — just talk to me.
>
> Want to:
> - **Start an assessment** — tell me the team, process, or goal you want to look at.
> - **See it work first** — I'll run a complete sample on a realistic (fictional)
>   company, end to end.

When resumable engagements exist, prepend a leading bullet (and, if more than one, offer a
short list to choose from):

> - **Continue "&lt;name&gt;"** — pick up where we left off.
<!-- greeting:end -->

Route the user's choice:

- **Start an assessment** → continue into **Intake** below (register inference, then Phase
  1). If their choice already names a target, go straight in without re-asking.
- **Run the sample** ("See it work first") → chain to
  `ai-process-assessment:running-sample-engagement`, which owns the bundled-vs-generated
  scenario chooser. Do not duplicate that logic here.
- **Continue "&lt;name&gt;"** → enter the drive loop at step 0 with that engagement
  resolved (list and let the user pick if more than one).

## Prerequisites

The state helpers and the engine are pure Python **standard library** — no venv, no
`pip install`, no third-party deps. Any `python3` runs them. You need exactly one
durable value: the **plugin root** — the absolute path to this installed plugin.

- **Cold first session:** the session-start hook injects it as a `Plugin root: <path>`
  line, with the engine/state command forms. Use that path.
- **Every session after:** it is stamped in the engagement's `.conductor.md` as
  `engine_root` and surfaced in the `state.state` snapshot's `engine_root` field.

Throughout this skill, `<engine_root>` denotes that path. Every engine/state command is
invoked by absolute path: `python3 <engine_root>/engine/run.py <folder>/` and
`python3 <engine_root>/state/state.py <folder>/`.

(Contributors running the test suite additionally need the packages in
`requirements.txt`; those are development dependencies, not prerequisites for running an
assessment.)

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
   `methodology_version` (read from `.claude-plugin/plugin.json`), `engine_root`
   (the absolute plugin root from the session-start note), and empty
   `open_decisions` / `deferred_processes`. Use:
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import write_conductor; ..."`.

## The drive loop

Repeat until Phase 11 is done and Gate B is cleared:

0. **Resolve the active engagement:** the folder containing a `.conductor.md` whose work
   is incomplete. None → run Intake. More than one incomplete → ask which.
0a. **Resolve `engine_root`:** take the live plugin root from the session-start note
   (injected fresh every session start). This is the value all commands below use.
1. **Read state:** `python3 <engine_root>/state/state.py <folder>` → JSON snapshot.
   Then **reconcile:** compare the snapshot's `engine_root` to the live root from the
   session-start note; if they differ (plugin upgraded to a new cache path, or the
   engagement was copied to another machine), re-stamp via
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import reconcile_engine_root; reconcile_engine_root('<folder>', '<engine_root>')"`.
   The live value always wins.
2. **Reconcile overrides:** apply `state.overrides.parse_overrides(CLAUDE.md)` +
   `reconcile(...)` so authorized skips don't block. An override row only fires if its
   Override cell contains the phase's output filename (e.g. `context.md`) or skill dir
   name (e.g. `mapping-context`); a row that names the phase only in prose is silently
   ignored. If a Methodology Overrides row clearly intends a phase but carries no such
   token, surface it and ask the human to add it (must-ask) — never proceed as if the
   phase were unskipped.
3. **Check staleness:** load `model_input_hashes` from `.conductor.md`; if
   `state.staleness.changed_inputs(folder, recorded)` is non-empty, a model input
   changed — re-run the engine and re-drive the affected portfolio phases forward
   (see "Staleness" below) before doing anything else.
4. **Pick the next step:** the first phase whose status is `available`/`overridden`.
   Respect the convergence gate (below) before any portfolio phase. **Per-phase status
   does not encode gate clearance** — `state.state` reports the GRC gate separately in the
   snapshot's `gates` array, so Phase 6 (Scoring) reads `available` even with unresolved
   non-Green GRC flags. Before entering Phase 6 or any portfolio phase, check `gates`: if
   `grc.status == "required"`, run Gate A first (step 8). Reading only `phases` here would
   skip Gate A.
5. **Gather gaps, then execute** per the execution model below.
6. **After a step that wrote a `model/*.json` input,** run
   `python3 <engine_root>/engine/run.py <folder>/` then
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import record_input_hashes; record_input_hashes('<folder>')"`.
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
- **Headless phases you dispatch to a subagent:** Phases 2, 3, 6, 7, 9, 10, 11, the
  checkpoints, and the GRC/deliverable gates. A subagent cannot ask the human, so before
  dispatch you must have every input it needs on disk. Hand the subagent the engagement
  folder path and the phase skill to run; receive a one-line confirmation; re-read state.
- **Input contract:** before dispatching a headless phase, confirm its predecessor files
  exist and gather any human-supplied value it needs via a targeted inline question — a
  **must-ask** if it's a decision (e.g., Build/Buy/Partner), a **should-confirm** if it's
  draftable.
- **Phase 5 (opportunity identification) is special:** with ≥2 ready processes you own a
  per-process fan-out rather than a single headless dispatch — see *Parallel per-process
  fan-out (Phase 5)*. With one process it runs once, whole-portfolio.

## Parallel per-process fan-out (Phase 5)

When the next step is Phase 5 (opportunity identification) and **≥2** in-scope processes
have `Baseline = Ready`, **you own the fan-out** — do not dispatch Phase 5 as a single
headless subagent. (Convergence already requires the full discovered set before Phase 6,
so every in-scope process is ready before this runs.)

- **Dispatch:** dispatch **one subagent per process**, each running
  `ai-process-assessment:identifying-opportunities` scoped to a single `PROC-NNN`, in one
  concurrent batch. Give each the engagement folder, `engine_root`, and its one `PROC-NNN`.
  Each writes only `<name>/_staging/phase5/proc-<process-id>.md` and returns a one-line
  summary (process id, opportunity count, GRC flag counts) — never opportunity content.
- **Merge (you, after the full set is staged):** assemble with the portable layer, identical
  to the Phase 5 skill's whole-portfolio assembly:

  ```bash
  PYTHONPATH="<engine_root>" python3 -c "
  from state.assembly import collect_staged, renumber_sequential, index_from_headers, cleanup
  staged = collect_staged('<name>/_staging/phase5')
  ids = renumber_sequential(staged, '<name>/opportunities', 'OPP')
  index_from_headers(
      ['<name>/opportunities/%s.md' % i for i in ids],
      '<name>/opportunities/_index.md',
      [('OPP-ID', 'id'), ('Process', 'process'), ('Type', 'type'),
       ('Feasibility', 'feasibility'), ('Data Readiness', 'data'),
       ('GRC', 'grc'), ('Structural', 'struct')],
  )
  cleanup('<name>/_staging/phase5')
  "
  ```

  `renumber_sequential` assigns global `OPP-NNN` in staged-file (process) order, so concurrent
  and sequential fan-out yield **byte-identical** `opportunities/`.
- **Then** run the cross-process **chain-detection** scan over the merged `opportunities/`
  (see *Elastic processes & convergence*), then proceed to convergence / Phase 6.

N<2 → run Phase 5 once, whole-portfolio, exactly as before (the sequential spine).

## Touchpoint taxonomy

| Class | Behavior | Examples |
|---|---|---|
| Must-ask | Always stop, every mode | Sponsoring question, decision-maker, scope boundaries, out-of-scope process additions, cost actuals, checkpoint outcomes, gate dispositions, Build/Buy/Partner |
| Should-confirm | Guided: pause to approve. (Autonomous batching is Slice 2.) | Context map, opportunity log, scoring rationale, roadmap sequencing; once `results.json` exists, generating any requested artifact via `ai-process-assessment:generate-artifact` (produced from the verified contract, never by hand) |
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

When `changed_inputs` is non-empty: re-run `python3 <engine_root>/engine/run.py <folder>/`, then
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
