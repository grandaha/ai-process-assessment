# Engagement Conductor — Design

**Status:** Draft for review
**Date:** 2026-06-17
**Author:** Dave Raffaele (with Claude)
**Topic:** An autonomous orchestrator that drives a process-assessment engagement end-to-end.

---

## 1. Problem

The methodology was built bottoms-up. Every component is a *guardrail*: eleven gated
phases, a deterministic math engine, a rationalization table that argues down corner-cutting,
GRC and deliverable gates, a cockpit to watch it run. This produces excellent rigor — but a
guardrail assumes an expert operator standing inside it who already knows the methodology and
is being kept honest.

What is missing is a **driver**. Today the front door is "say *scope this engagement*," which
only works if you know that is the door, that there are eleven phases behind it, and that you
are the one who must walk through them. The system waits to be operated.

Two goals motivate this work:

- **AI-first.** The methodology should *drive* the engagement — take initiative, interview the
  human, advance phases, run the engine, and surface only the decisions that genuinely need a
  person. The walls stay; they move to the background where the human never has to know they
  are there.
- **Usable on their own, by either persona.** The same product must serve an outside
  **consultant** (domain-fluent, wants speed) and an untrained **internal operator** (no
  methodology training, needs teaching). One product serves both only if the *driver* adapts —
  not the user.

The insight that makes this cheap: **everything built bottoms-up is already the Conductor's
body.** The phase skills are its hands. The gate conditions (`prior file exists`) are already a
state machine. The gates and stakeholder checkpoints are already the list of "decisions that
need a human." `cockpit/state.py::read_state()` already derives engagement state from the
filesystem. We have every organ of an autonomous agent except the loop that makes them act on
their own. This design is that loop.

## 2. Goals / Non-goals

**Goals**

- A single skill, `conducting-engagement`, that becomes the natural-language front door and
  drives the eleven phases to a cleared deliverable.
- Adapts to consultant vs. operator (register) and to how hard it should drive (autonomy),
  without forking the spine.
- Treats **processes as elastic, first-class units** — start with one, start with many, add
  more later — converging to one portfolio.
- Preserves every existing guarantee: no phase-skipping, no prose arithmetic, single-write
  model ownership, gate clearances, evidence traceability.

**Non-goals (this spec)**

- No re-implementation of phase skills. The Conductor *supervises* them; it does not redo their
  work.
- No UI. The cockpit remains the read-only watcher (it may later surface the Conductor's current
  action, but not in Slice 1).
- No separate-deliverable-per-process / cross-engagement rollup ("Level 2", §6.6). Deferred —
  but not walled off.
- No mid-stream entry that skips phases. "Just build the business case" runs the full spine at
  N=1 (§6.2).

## 3. Core concept — a thin supervisor

The Conductor is a **thin, long-lived supervisor**. It holds only state and decisions in its own
context; all *content* work stays in the phase skills, which it dispatches to **subagents**.

The existing keystone `using-methodology` remains the **rulebook** (phase map, taxonomy,
rationalization table) — loaded passively into every session. The Conductor is the **agent that
acts on the rulebook**. It never contradicts the keystone, and because it derives "what's next"
from `read_state()`, hard-gate discipline (no skipping, file-must-exist-first) is enforced
*automatically and invisibly*. The human never hears "you cannot skip Phase 4"; the Conductor
simply never offers to.

**Why a separate skill and not folded into the keystone:** the keystone is always-loaded passive
reference; the Conductor is an *active loop you opt into*. Mixing the two would fire the loop even
when a user wants to invoke one phase by hand. Keep the rulebook passive, the driver separate.

## 4. Architecture

### 4.1 State sensor (reuse, plus one small addition)

The Conductor's "eyes" are `cockpit/state.py::read_state()`, which already returns: which phases
are `done` / `available` / `blocked`, which gates are triggered, which `model/*.json` inputs
exist. **State lives in files; the Conductor owns no parallel copy of content state.** This is
what makes resumption free — re-invoke next session, read the files, pick up.

`read_state()` is currently reachable only behind the cockpit server. **New code:** a one-shot
CLI, `python -m cockpit.state <engagement-folder>`, that prints the snapshot as JSON to stdout.
This is the only state machinery the Conductor needs and it is independently testable.

### 4.2 Subagent dispatch (mandatory, for context survival)

A full eleven-phase engagement is enormous and spans many sessions. If the Conductor runs each
phase *inline*, it exhausts its own context window mid-engagement and can no longer supervise. So
the architecture is: **the Conductor dispatches each phase to a fresh subagent**, passing the
phase skill plus the gathered inputs, and receives back a short confirmation. It then re-reads
state. The repo already uses subagent dispatch for renderers, so this is an established pattern.

This also unlocks **parallel per-process fan-out** (§6.3) almost for free.

### 4.3 The drive loop

```
0. resolve the active engagement folder: the one whose .conductor.md marks it incomplete.
      none -> treat as new (step 3); more than one incomplete -> ask which.
1. snapshot = read_state(engagement)            # cockpit.state CLI, JSON
2. reconcile snapshot with CLAUDE.md overrides  # §10 — authorized skips
3. no engagement yet?  -> INTAKE                 # §7 — set register + autonomy, run scoping
4. any stale outputs?  -> mark for re-drive      # §9 — staleness rule
5. pick next actionable unit of work:
      - per-process phase available for a process not yet done?   (§6.3)
      - else portfolio phase available and convergence gate open? (§6.4)
6. gather the phase's required human inputs not already on disk    # §4.4 — input contract
      -> interview at a depth set by register, asking only for the gaps   (§7-8)
7. dispatch the phase to a subagent with the gathered inputs; receive confirmation; re-read state  # §4.2, §4.4
8. did the step write a model/*.json input?  -> run `python -m engine.run <folder>/`
9. at a checkpoint insertion point (per the building-checkpoint registry)?
      -> offer to generate the checkpoint (should-confirm); its stakeholder outcome is must-ask
10. gate triggered (GRC non-green / pre-deliverable)?  -> run gate, surface result
11. record this step's structural-class decisions to the decision log    # §8.1
12. pause at the right human touchpoint (§8); else continue
13. loop until Phase 11 + Gate B clear
```

The Conductor stays thin and deterministic; every transition is derived from state, not
remembered.

### 4.4 Phase execution model — who talks to the human (resolution of step 6)

§4.2 says the Conductor dispatches phases to subagents, but most phase skills today *interview the
human interactively*, and a subagent in this harness returns a result rather than holding a live
conversation. That contradiction is resolved by executing phases in one of **two modes, by phase
character**:

- **Interview-heavy phases run inline** in the Conductor's own context — **Phase 1 (scoping),
  Phase 4 (discovery), Phase 8.5 (cost actuals)**. These *are* conversations; they keep their
  existing questioning. The Conductor enters the phase skill, conducts the interview, writes the
  output file, then **drops the transcript** and keeps only the state snapshot — state is
  file-derived, so it can forget aggressively (consistent with "owns only state and decisions").
- **Headless / transform phases dispatch to subagents** — **Phase 2, 3, 5, 6, 7, 9, 10, 11, the
  checkpoints, and the GRC / deliverable gates**. These transform files that already exist and need
  no live human turn. The Conductor hands the subagent an explicit **input set** and gets back a
  one-line confirmation. These are also the heaviest token consumers (large synthesis, rendered
  HTML), so putting them in subagents is exactly what protects the Conductor's context.

**Input contract.** A headless phase cannot ask the human, so it must be dispatched with everything
it needs. For each headless phase the plan records its **required inputs** (predecessor files plus
any human-supplied values gathered earlier). A missing required input is a *gap* the Conductor
fills **before** dispatch via a targeted inline question — a must-ask if it is a decision (e.g.,
Build/Buy/Partner), a should-confirm if it is draftable. This is the concrete meaning of
"interview, asking only for the gaps" in drive-loop step 6.

**Consequence for parallelism.** Because interview-heavy phases run inline against a single human,
they **cannot truly fan out** — the human is serial. The real concurrency win in §6.3 is the
*headless* per-process work (Phase 5 drafting), not the Phase 4 interviews. Slice 2's "parallel
fan-out" means parallel headless subagents, not parallel interviews.

This is the single highest-judgment call in the design; see §16.

## 5. Serving both users — two knobs

Set once at intake, stored in `<name>/.conductor.md` (§11). This file holds **only interaction
context** — never engagement content. Content stays file-derived; single-write-ownership is
untouched.

- **Register — *who am I talking to.***
  - *Consultant*: domain-fluent, terse, methodology vocabulary, infers aggressively, moves fast.
    Often *relaying* interviews run offline ("I spoke to the AP team, here are my notes").
  - *Operator*: no training assumed, teaches as it goes ("here's why baselines come before value"),
    plainer questions, offers examples. Usually *is* the stakeholder and answers directly.
- **Autonomy — *how hard do I drive.*** Modeled **per touchpoint-class** (§8), not as one global
  switch, so "draft opportunities for me, but I approve every score" is expressible. Slice 1
  exposes two presets over that granular model:
  - *Guided* (default): drives, but confirms each phase transition and every checkpoint/gate.
  - *Autonomous* (opt-in): drives through phases without per-step confirmation, stopping **only**
    at genuine human-decision points.

Register and autonomy are independent: consultant+guided and operator+autonomous are both valid.

**Why granular-but-presented-as-presets:** a global binary feels wrong fast and is a painful
migration to split later. Modeling autonomy per-class now, while only *exposing* two presets,
makes the future free. (Bake the model; expose the presets.)

## 6. The elastic portfolio model

### 6.1 One engagement = one portfolio

An engagement has one `scope.md` (one sponsoring question, one decision-maker) and holds **1..N
processes**. The output is one prioritized roadmap + business case + deliverable synthesized
*across* processes. This is already how Phases 6–11 think; the methodology's value *is* the
cross-process synthesis.

### 6.2 N=1 is not a special mode

"Assess this one process / one use case" is a portfolio of one: the *same spine* with a single
process, **nothing skipped**. It is lighter only because there is less content to work through —
there is **no separate "lite mode"** and no phase is dropped or collapsed. **Integrity line:** no
mid-stream entry. The moment someone jumps to the business case without a baseline, every number is
asserted instead of sourced and the whole point is gone.

### 6.3 Per-process vs portfolio-level phases

| Phase | Scope | Fan-out? |
|---|---|---|
| 1 Scoping, 2 Context, 3 Tech inventory | Engagement-level | No (one per engagement) |
| 4 Discovery, 5 Opportunity identification | **Per-process** | **Yes — parallel subagents** |
| 6 Scoring, 7 Roadmap, 9 Business case, 10 Exec summary, 11 Deliverable | **Portfolio-level** | No — must converge |
| 8 Packaging, 8.5 Cost actuals | Per-opportunity (already item-level) | Yes |

Per-process phases are dispatched **one subagent per process**. Each subagent sees only its
process. **Fan-out is the *model*, not the Slice 1 behavior:** Slice 1 runs per-process phases
**sequentially** (the split, convergence gate, and chain-detection all still apply); concurrent
execution is the Slice 2 headline (§13).

### 6.4 Convergence gate

Portfolio-level phases are **blocked until every in-scope process has completed its per-process
phases**, or a process is explicitly **deferred to a later wave**. Deferral is **conductor
interaction-state**, recorded as a `deferred_processes` list in `.conductor.md` (§11) — *not* in
`processes/_index.md`, which is owned and written by Phase 4 and must stay unchanged. The
convergence check is therefore a skill-level rule: before the first portfolio phase, confirm
`processes/_index.md` lists every in-scope process with `Baseline = Ready`, treating any process in
`deferred_processes` as intentionally out of this wave (deferring one is a must-ask). This prevents
a half-discovered portfolio from being scored while still letting a wave close with known-deferred
processes.

### 6.5 Cross-process chain-detection pass (integrity-critical)

Parallel per-process fan-out **re-introduces the isolation the methodology forbids** — the
rationalization table is explicit that a step which is no AI candidate *alone* can belong to a
**chain** spanning process boundaries, and that is where the highest-value insight hides. Each
per-process subagent is blind to the others, so it cannot see a cross-process chain.

Therefore convergence (Phase 5 → 6) includes an **explicit cross-process chain-detection pass**,
run in the merged context where all processes' opportunities are visible at once. Without this,
parallel mode is faster *and dumber* — it ships exactly the failure the methodology exists to
prevent. Convergence is an opinionated step, not a concatenation of folders.

### 6.6 Incremental composition and the scope boundary

Adding a process to an in-flight engagement reuses the **staleness rule** (§9): the new process
makes the portfolio-level phases stale, so they re-converge. The governing rule:

> **`scope.md` is the container.** Adding a process *within* the stated scope is free (a
> should-confirm fan-in). Adding a process *outside* scope is a **must-ask**: "this is past your
> stated boundary — expand the scope, or start a new engagement?"

That single rule bridges small starts, growth, and the seam to the deferred "Level 2" (separate
deliverables per process, rolled up to an org view): a genuinely separate concern becomes a *new
engagement*, and composing multiple engagements is future work. The only guardrail Slice 1 owes
that future is: **conductor state is per-engagement, never global.**

## 7. Intake

On a natural-language opener ("help me find AI opportunities in my ops team", "assess this
client"):

1. Establish **register** (consultant vs operator) — **infer from the opener and confirm in one
   line** ("Sounds like you're assessing your own team — I'll keep it plain and explain as we go;
   say the word if you'd rather I move fast and skip the teaching."). Never a cold multiple-choice
   quiz; the inference is usually obvious from how they phrased the request.
2. Establish **autonomy** preset (default guided).
3. Run `scoping-engagement` (creates the engagement folder, `scope.md`, gitignore protection).
4. Stamp `.conductor.md` with register, autonomy, and **`methodology_version`** (§8.2).
5. Enter the drive loop.

The Conductor's trigger phrases must be broad natural language so a naive user falls into it
without knowing magic words.

## 8. Touchpoint taxonomy — "drives but doesn't run away"

Every possible pause is classified. This is the load-bearing table.

| Class | Conductor behavior | Examples |
|---|---|---|
| **Must-ask** (human owns the decision) | Always stop, every mode | Sponsoring question, decision-maker, scope boundaries, out-of-scope additions, cost actuals, checkpoint outcomes, gate dispositions, Build/Buy/Partner |
| **Should-confirm** (Conductor drafts, human ratifies) | Guided: pause to approve. Autonomous: draft + record to decision log + batch for review at next checkpoint | Context map, opportunity log, scoring rationale, roadmap sequencing |
| **Can-infer** (mechanical) | Never asks | Run the engine, derive state, pick next phase, assemble deliverable HTML |

Sponsoring question and cost actuals *cannot* be inferred — so they are always asked, in every
mode. This dovetails with the deterministic-math rule: a value claim never rests on an inferred
number.

### 8.1 Decision log — the trust layer *and* the learning substrate

The methodology makes *numbers* auditable. The moment the Conductor drives, judgment calls a human
used to make (process prioritization, opportunity drafting, type classification, score rationale,
sequencing) need the same auditability — "the AI decided" is a liability in front of a client or
CFO. So the Conductor records consequential decisions to `<name>/decision-log.md`. This is the
deterministic-math discipline applied to *judgment* instead of arithmetic.

**Record both parties, not just the agent.** A one-sided log can *audit* but cannot *teach*. To
govern, we must attribute who decided what; to improve, we need the **delta** between agent and
expert judgment — and a delta requires both sides on the record. The most valuable entry in the
system is "agent proposed RPA → human overrode to Chain Automation → because the appended step
eliminates a verification checkpoint": a labeled correction produced as a free byproduct of the
work. Log only the agent and that label is gone forever.

**What to log — by structural class, never by the agent's own sense of importance** (that would be
auditing the auditor). Always log, full rationale: opportunity **type classifications**, **scores**,
**roadmap sequencing / wave** assignments, any decision where the actor **chose between ≥2 viable
options**, or **selected a non-default where the methodology specifies one** (e.g., Build when the
rubric recommends Buy). These are all objectively detectable from the work product — no "is this
important?" judgment is involved. Pure mechanical drafting (summaries, formatting) gets no entry —
it is reconstructable from the output file it produced.

**Fields that make an entry learnable, not just auditable:**

- **Provenance** — `proposed_by` (agent | human) and `decided_by` (agent-auto | human-ratified |
  human-overrode).
- **Disposition** *(the label)* — `accepted` | `edited` | `overridden→X` |
  `invalidated-by-{staleness | checkpoint | gate}`. An override is a negative example; a later
  invalidation of something both approved is a stronger one.
- **Outcome linkage** — did the decision survive to the deliverable, or get reversed downstream?

**Implementation trap:** when a human overrides an agent draft, **do not overwrite it** — record
*both* the proposal and the correction. The naive build silently deletes the highest-value data in
the system.

Entries are **append-only**, never edited after the fact, and each links to its evidence source — a
file path with section/anchor, or a `model/*.json` key — the same discipline as the existing
`evidence-log` (number provenance) and `improvement-log` (methodology escapes); the decision log is
their third sibling (judgment provenance).

**Slice boundary.** *Recording* both parties with provenance + disposition lands in **Slice 1** —
because if engagement #1 logs only the agent side, that early data is un-learnable forever and the
human's decisions and overrides cannot be reconstructed after the fact. *Mining* the corpus for
patterns is later (§15) — it needs volume across engagements. Capture right now; learn later.

### 8.2 Methodology version stamp

The plugin ships versioned and keeps moving; a real engagement spans weeks and plugin updates. The
Conductor writes `methodology_version` into `.conductor.md` at intake, so mid-flight drift (e.g.,
the Phase 6 rubric changing) is detectable. One line now; impossible to reconstruct later.

## 9. Staleness rule

`read_state()` knows file *existence*, not file *validity*. Real engagements flow backward: a
stakeholder at the Phase 7 portfolio checkpoint says "your baseline was wrong." After the fix,
`scores/`, `roadmap.md`, `business-case.md` all still *exist* — so naive state says "done" and the
Conductor would drive a deliverable built on corrected-but-not-recomputed numbers.

**Signal — content hash, not mtime.** The Conductor records the SHA-256 of every `model/*.json`
input in `.conductor.md` at the moment the engine last ran (§11). An input is **changed** when its
current hash differs from the recorded one. This is chosen for *accuracy*: mtime is simpler but
unreliable in this repo's iCloud-synced folder, where checkout and sync rewrite timestamps (the
same noise that has corrupted git refs before) — a content hash only fires on a *real* content
change, never on a touch, checkout, or re-sync.

**Rule:** when an upstream `model/*.json` input is changed, everything downstream of it (per the
single-write-ownership dependency order) is **stale** and must be re-driven forward — re-run the
engine, then re-converge the affected portfolio phases. This reuses the single-write-ownership
table (which already encodes the dependency order) and powers both backward-correction *and*
incremental process addition (§6.6) — they are the same mechanism. After a successful re-drive,
the Conductor updates the recorded hashes so the outputs read clean again.

**Re-drive re-opens decisions.** Re-driving a stale downstream phase invalidates the human
ratifications that were given against the now-superseded numbers: each such decision is recorded
`invalidated-by-staleness` in the decision log (§8.1) and re-surfaced per its touchpoint class. The
Conductor never silently keeps a ratification that was given against numbers that have since
changed.

## 10. Failure, rejection, and override handling

- **Phase subagent fails / `engine.run` errors:** stop, surface to human with the error
  (must-ask). Do not advance on a failed step.
- **Gate rejects** (GRC red, deliverable-gate fails): surface the failed dimension and route to
  its owning phase; re-drive forward after the fix.
- **Checkpoint rejected** (e.g., "baseline wrong"): route back to the checkpoint's route-back
  phase (per the Checkpoint Registry), which triggers the staleness rule forward.
- **CLAUDE.md overrides:** `read_state()` is pure file logic and does not know an authorized skip
  exists. The Conductor reconciles *file truth* (state) with *authorized deviations* (the CLAUDE.md
  Methodology Overrides table): an overridden phase is treated as satisfied rather than
  forever-blocking. Without this, the Conductor fights the user's own config.

## 11. Conductor private state — `<name>/.conductor.md`

Parallels the existing `.sample-run.md` marker. Frontmatter only; **interaction context, never
content.**

```yaml
---
register: operator            # consultant | operator
autonomy:                     # per touchpoint-class; presets set all at once
  should_confirm: guided      # guided | autonomous
methodology_version: 2.13.1
last_action: "dispatched discovery for PROC-003"
open_decisions: []            # must-asks awaiting the human
deferred_processes: []        # processes intentionally out of the current wave (§6.4)
model_input_hashes:           # SHA-256 of each model/*.json at last engine run (§9 staleness)
  baselines.json: "e3b0c442…"
  value.json: "a1d0c6e8…"
---
```

Content state is *always* derived from the engagement files via `read_state()`; `.conductor.md`
never duplicates it.

## 12. Relationship to existing components

- **`using-methodology`** — unchanged rulebook; the Conductor honors it.
- **Phase skills** — content logic unchanged. Execution per §4.4: interview-heavy phases (1, 4,
  8.5) run inline; headless phases run in subagents and may need a small non-interactive execution
  path (the plan identifies which, and whether each already runs cleanly without live prompts).
- **`engine.run`** — unchanged; invoked after any model input changes.
- **Gates / checkpoints** — unchanged; they *are* the human touchpoints.
- **`cockpit`** — gains a `python -m cockpit.state` one-shot JSON CLI; server unchanged.
- **`running-sample-engagement`** — becomes the Conductor's end-to-end integration test (drive the
  Lattice demo in sample mode, no live human, assert all outputs + `results.json`).

## 13. Slicing

**Slice 1 — Minimum Viable Conductor (drives the happy path, sequentially).**
- `conducting-engagement` skill; natural-language front door; intake (register + autonomy preset +
  version stamp).
- `python -m cockpit.state` JSON CLI.
- Drive loop over phases 1→11, sequential processes, engine runs, convergence gate.
- Touchpoint taxonomy enforced; **must-ask** complete; **should-confirm** in guided mode.
- **Decision log** — both-parties capture with provenance + disposition (§8.1), not a stripped-down
  version; **staleness rule**; **failure/gate/checkpoint** handling; **CLAUDE.md override**
  reconciliation; **scope-boundary** rule on process add.
- Per-process vs portfolio phase split and **cross-process chain-detection pass** baked into the
  model (even though processes run sequentially here).
- **Phase execution split (§4.4)** — inline interview phases vs headless subagent phases, with the
  per-headless-phase input contract; confirm each headless phase runs without live prompts.
- Resumes from file-state across sessions.

**Slice 2 — Adaptive + parallel.**
- **Parallel per-process fan-out** (headline).
- Full granular autonomy (per-class), autonomous-mode should-confirm batching at checkpoints.
- Register-driven verbosity/teaching depth.
- **Holding-the-line posture** toward an impatient non-expert operator (firm-but-teaching, not
  refuse-and-quote-the-table).
- Mid-engagement interruption / "stop, that's wrong" splicing.

**Slice 3 — Polish + flywheel hook.**
- Graceful messy/partial-state handling; multi-session resume hardening.
- Cockpit surfaces the Conductor's current action.
- **Improvement-flywheel hook:** the Conductor flags rationalization escapes it encounters into
  `improvement-log.md` (auto-detection; human still approves the GREEN/REFACTOR).

## 14. Testing

- **State CLI** — unit tests over fixture engagement folders (done/available/blocked/stale).
- **Staleness logic** — unit tests over content-hash/dependency-order fixtures (changed-input
  hash → correct downstream outputs flagged stale).
- **CLAUDE.md override reconciliation** — unit tests (overridden phase treated as satisfied).
- **End-to-end** — drive `running-sample-engagement` (Lattice demo) via the Conductor in sample
  mode; assert all phase outputs + `results.json` + a cleared Gate B.
- The Conductor skill itself is a prompt; its *supporting code* is what carries unit tests, and the
  sample engagement is its integration test — aligned with the existing test culture.

## 15. Future directions (named, not built here)

- **Improvement flywheel (the real mechanism).** The both-parties decision log (§8.1) is the
  substrate. The loop: `decision log → mine for systematic human-overrides-agent patterns →
  tighten the skill / gate / rationalization-table that should have produced the right call → the
  next engagement's agent reads improved instructions and decides better`. This is honestly bounded:
  it improves the *methodology* (skills, gates, tables — encoded in prompts), not model weights. It
  upgrades the existing `improvement-log` RED-GREEN-REFACTOR loop from "fires when a human happens
  to notice an escape" to "continuous and evidence-weighted" — a repeated override across N
  engagements is a methodology gap *with a sample size*, not a hunch. Pattern-mining needs volume,
  so it ties to multi-engagement below; the *capture* it depends on is in Slice 1.
- **Holding-the-line posture** — the methodology's challenge function under AI agency, against a
  non-expert with organizational impatience (Slice 2).
- **Level 2: multi-engagement rollup** — separate deliverables per process/department composed to
  an org view. Two purposes, not one: client-facing rollup, *and* the corpus the improvement
  flywheel mines (a human-vs-agent pattern only emerges across many engagements). Seam preserved by
  keeping conductor state per-engagement.

## 16. Resolved decisions

- **Register at intake → infer-and-confirm** (not a cold quiz). The opener almost always reveals
  the persona; the Conductor confirms in one line and moves on (§7).
- **Staleness signal → content hash (SHA-256), not mtime.** Chosen for accuracy in the
  iCloud-synced environment where mtimes are unreliable (§9, §11).
- **Phase execution → inline interviews, headless transforms (§4.4).** Resolves "who talks to the
  human." *This is the call most worth a second look before planning* — it determines which phase
  skills need a headless execution path and bounds where parallelism can actually pay off.

- **Decision log → trust layer *and* learning substrate.** Log **both parties'** structural-class
  decisions (type, score, sequencing, chose-between-options, departed-from-default) with
  **provenance + disposition + outcome linkage** — never overwriting an agent draft a human
  corrected. Granularity is set by decision *class*, not the agent's sense of importance. This is
  what makes the improvement flywheel (§15) possible; capture lands in Slice 1, mining is later
  (§8.1).

## 17. Open questions

- **Pattern-detection threshold** — how many repeated human-overrides-agent of the same kind
  constitute a methodology gap worth a RED-GREEN-REFACTOR entry? Needs real corpus volume to tune;
  not a Slice 1 blocker.
