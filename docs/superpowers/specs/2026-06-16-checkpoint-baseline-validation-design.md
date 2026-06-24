# Checkpoint 2 — Process & Baseline Validation — Design

**Date:** 2026-06-16
**Status:** Approved for planning
**Author:** Dave (with Claude)
**Issue:** grandaha/ai-process-assessment#49

## Summary

Add the methodology's first **stakeholder validation checkpoint**: an interim,
client-facing HTML artifact produced after Phase 4 (process discovery) and before
Phase 5 (opportunity identification), so process owners and the sponsor can
confirm the as-is process maps and baseline metrics — and decide the challenge
hypotheses — *before* the engagement builds opportunities, scores, a roadmap, and
a business case on top of them.

This cycle builds **Checkpoint 2 (`baseline`) only**, as the reusable pattern.
It establishes a parameterized checkpoint skill, a data-driven baseline renderer,
a scoped (checkpoint-mode) deliverable-gate, and a recorded feedback-loop artifact.
Checkpoints 1 (Scope & Context) and 3 (Portfolio & Roadmap) are deliberately
deferred to follow-on cycles that reuse this pattern.

## Why this checkpoint, why now

Today the only externally-facing artifact is `deliverable.html` at Phase 11.
Phases 1–10 are internal markdown; the GRC and deliverable gates are internal QA.
So stakeholders never see polished output for sign-off until the end, by which
point scope, baselines, and prioritization are already baked in.

Baselines are the highest-leverage validation point: **every value figure in the
entire engagement is computed off `model/baselines.json`** (Phase 4 is its sole
writer; the engine resolves all `value.json` volumes from it). A wrong baseline
discovered at Phase 11 invalidates the business case. Validating baselines with
the people who own the work, immediately after Phase 4, is the cheapest place to
catch that error.

## Goals

- A consultant can produce a polished, client-ready HTML baseline-validation
  artifact from existing Phase 4 outputs, with no new analysis.
- Stakeholders can confirm/correct each process's baseline metrics and decide the
  challenge hypotheses; the outcome is recorded and auditable.
- Corrections route back to Phase 4, regenerate cleanly, and the engine re-runs if
  `baselines.json` changed.
- The pattern (skill + renderer + scoped gate + outcome artifact + keystone
  wiring) is reusable for Checkpoints 1 and 3 with new registry rows + renderers.

## Non-Goals

- **Not building Checkpoints 1 or 3** this cycle (registry is designed to extend).
- **Not refactoring Phase 11's shell** into a shared asset yet (YAGNI at one
  consumer; revisit when CP1/CP3 land — see Shell decision).
- **Not making the checkpoint a hard gate.** It is recommended-and-recorded:
  the keystone recommends it at the insertion point and its outcome is logged, but
  Phase 5 is not hard-blocked. CLAUDE.md may upgrade it to mandatory per engagement.
- Not auto-merge-eligible: this is markdown/methodology work; the auto-review loop
  will correctly route the PR to human merge.

## Decisions (locked in brainstorming)

1. Build **Checkpoint 2 only**, as the pattern.
2. **One parameterized `building-checkpoint` skill** driven by a checkpoint registry.
3. **Scoped mode of the existing `deliverable-gate`** (not a new gate).
4. **Recorded outcome artifact** (`checkpoints/CP-<id>-outcome.md`) + routing.
5. **Recommended-and-recorded** enforcement (not mandatory by default).

## Architecture

```
Phase 4 (processes/, model/baselines.json)
        │
        ▼
  building-checkpoint  (id = "baseline")
   1. read scope.md → engagement folder; verify processes/_index.md exists
   2. invoke deliverable-gate in CHECKPOINT MODE (scoped to existing files)
   3. dispatch section-renderer-checkpoint-baseline → _staging/
   4. assemble checkpoints/checkpoint-baseline.html from the checkpoint shell
   5. prompt to record checkpoints/CP-baseline-outcome.md
        │
        ▼
  Stakeholder review (process owners + sponsor)
        │
   ┌────┴─────────────┐
 Confirmed       Changes Requested
   │                   └─► route to Phase 4 → correct PROC-NNN / baselines.json
   ▼                        → re-run engine if baselines.json changed → regenerate
 Phase 5 may rely on the confirmed baselines
```

### Component 1 — `building-checkpoint` skill

**File:** `skills/building-checkpoint/SKILL.md` (new)

A single parameterized skill driven by an internal **Checkpoint Registry** table.
Only the `baseline` row is active this cycle; the table format anticipates CP1/CP3.

| id | Insert after | Source files | Renderer(s) | Output | Route-back phase |
|---|---|---|---|---|---|
| `baseline` | Phase 4 | `processes/PROC-NNN.md`, `model/baselines.json`, `scope.md` (header only) | `section-renderer-checkpoint-baseline` | `checkpoints/checkpoint-baseline.html` | Phase 4 (`discovering-processes`) |

**Session start / orchestration:**
1. Read `scope.md`; extract `Engagement folder:`. Halt if absent (return to Phase 1).
2. Resolve the checkpoint id (default/only: `baseline`). Look up its registry row.
3. Verify the predecessor output exists (`processes/_index.md`); halt with a clear
   message if not.
4. Invoke `deliverable-gate` in **checkpoint mode** for this id (Section: gate).
   Proceed only on checkpoint clearance.
5. Dispatch the registry's renderer(s) to `<engagement>/_staging/checkpoint-<id>/`.
6. Assemble `<engagement>/checkpoints/checkpoint-<id>.html` from the checkpoint
   shell (Section: shell), interleaving the returned section blocks in order.
7. Open/confirm the file (sticky nav targets, anchors present, no missing-class
   artifacts), then prompt the user to record the outcome (Component 4).

**Disciplines inherited from `building-deliverable`:** produces NO new content —
every figure traces to a source `.md`/`.json`; renderers receive specific
sections at specified density (not file dumps) and return inner section blocks
only (no `<html>/<body>/<style>/<script>`); fixes go to the source, then re-run
the renderer. Rationalization table + session-boundary + "do not echo HTML"
completion rule mirror the Phase 11 skill.

### Component 2 — `section-renderer-checkpoint-baseline` agent

**File:** `agents/section-renderer-checkpoint-baseline.md` (new)

**Data-driven** (unlike the sample-hardcoded Phase 11 renderers). Reads the
relevant `processes/PROC-NNN.md` files + `model/baselines.json`. Emits **two**
section blocks:

- `#baselines` — one row per process: the metrics that process actually has
  (volume, cycle time, error rate, FTE effort — whatever is present), each with
  its source/confidence note. Absent metrics render as **PENDING**, never invented.
  Figures are drawn verbatim from `baselines.json`/`PROC-NNN.md` — the renderer
  computes nothing.
- `#validate` — the explicit *"confirm or correct"* list and the per-process
  **challenge hypothesis** (root-cause vs. optimize-around) presented for a
  stakeholder decision, plus any open questions/data gaps.

Hard refusals mirror the existing renderers: no invented/rounded numbers, no
wrapper markup, only shell-defined CSS classes.

### Component 3 — Scoped deliverable-gate (checkpoint mode)

**File:** `skills/deliverable-gate/SKILL.md` (modified, backward-compatible)

Today the gate's Session Start hard-requires *all* phase files, so it cannot run
mid-flow. Add a **checkpoint mode**:

- Invocation carries a checkpoint id (or the set of files-present). In checkpoint
  mode, the gate reads only the files that exist at that point and runs the
  integrity dimensions over them; **later-phase files are legitimately absent, not
  failures.**
- For `baseline`, the applicable dimensions are: **Evidence integrity** (every
  rendered figure traces to a `PROC-NNN.md`/`baselines.json` source),
  **Determinism integrity** (every rendered number equals its `baselines.json`
  source; PENDING stays PENDING), and **Completeness** (every in-scope domain from
  `scope.md` that Phase 4 should have covered is present or its gap acknowledged).
  Logic/Business-Case/Communication dimensions that require later phases are
  **skipped as not-yet-applicable** and noted as such.
- The `opportunity-reviewer` dispatch (which assumes opportunities exist) is
  **not run** at the baseline checkpoint; checkpoint clearance is a lighter,
  scoped pass.
- Clearance is recorded in `evidence-log.md` as a distinct checkpoint entry
  (e.g., `Checkpoint baseline — cleared`), separate from terminal Gate B.
- **The full terminal gate (invoked with no checkpoint id) behaves exactly as
  today.** This is the regression line the plan must protect.

### Component 4 — Feedback-loop artifact

**File (per engagement, generated):** `checkpoints/CP-baseline-outcome.md`
**Template (new):** `templates/checkpoint-outcome-template.md`

Fields: checkpoint id; date; attendees / sign-off names (process owners, sponsor);
status (**Confirmed** | **Changes Requested**); itemized changes (what · which
PROC-NNN / metric · who raised); routing note (→ Phase 4 to correct, re-run engine
if `baselines.json` changed, regenerate the checkpoint).

**Routing rule (in the skill):** on *Changes Requested*, route to the registry's
route-back phase (Phase 4), apply corrections to `PROC-NNN.md`/`baselines.json`,
re-run `python -m engine.run <engagement>/` if any number changed, regenerate the
checkpoint, and append a new outcome record. On *Confirmed*, downstream phases may
rely on the baselines; the terminal gate and final deliverable may cite the
sign-off.

### Component 5 — Checkpoint HTML shell

For this single checkpoint, the skill assembles from a **small self-contained
shell** that reuses Phase 11's **exact CSS class names and design tokens**
(`.section-block`, `.sticky-nav`, `.stat-*`, `.callout*`, `.doc-footer`, etc.) so
the checkpoint looks consistent with the final deliverable. The shell's sticky
nav has two links (`#baselines`, `#validate`) plus the masthead/footer.

**Deferred:** extracting Phase 11's shell into a shared `templates/` asset. That
extraction earns its keep at 3 consumers (CP1/CP3); doing it now would mean
refactoring Phase 11 for a single new consumer. Flagged as a follow-up.

### Component 6 — Keystone + system-prompt wiring

**Files:** `skills/using-methodology/SKILL.md` and `system-prompt.md` (mirror).

- **Registration (revised during planning):** register the skill via the
  test **allow-list** (`ALLOWLIST_NON_PHASE`), NOT a Phase-Map row. A Phase-Map
  row would force the skill into the linear chain (`test_chain.py` requires every
  phase-skill be visited) and break the 14-row manifest (`test_manifest.py`).
  The checkpoint is cross-cutting (like `running-sample-engagement`); it is wired
  via the keystone's Routing Logic prose, not the parsed Phase Map.
- **Engagement Folder Convention:** add `checkpoints/` (folder:
  `checkpoint-<id>.html` + `CP-<id>-outcome.md`).
- **Routing Logic + When-to-Invoke:** add lines — after Phase 4 / `processes/_index.md`
  saved, recommend `building-checkpoint` (baseline) for stakeholder validation
  before Phase 5; trigger phrases like "validate the baselines", "review the
  process maps with the client".
- **Mirror to `system-prompt.md`** — a guard test enforces keystone↔system-prompt
  sync; both change together.

## Testing

The repo's test model (`tests/methodology_model.py`) parses the keystone Phase
Map, skills, and agents. New/affected tests:

- **`test_skills.py`** — `building-checkpoint` is a new skill, registered in
  `ALLOWLIST_NON_PHASE`. Bump `test_skill_count` (17 → 18) and confirm
  `test_no_orphan_skills` passes. It must have well-formed frontmatter, a `name`
  matching its directory, and a `## Chain to next skill` section (parser reads the
  `→` target). The Phase Map stays 14 rows (`test_manifest.py` unchanged).
- **`test_agents.py`** — `section-renderer-checkpoint-baseline` must have valid
  frontmatter `name`/`description`.
- **`test_chain.py` / `test_outputs.py` / `test_manifest.py` / `test_guards.py`**
  — run the suite; satisfy whatever each asserts (chain target resolves; the
  `checkpoints/` convention token is consistent; any skill/agent manifest that
  enumerates entries includes the new ones). The plan resolves these by running
  `pytest` and fixing what fails, TDD-style.
- **Backward-compat:** add/keep a test (or manual check in the plan) that the
  terminal deliverable-gate path is unchanged when no checkpoint id is supplied.
- **Manifests:** if `.claude-plugin/plugin.json` / `marketplace.json` enumerate
  skills, register the new skill there (suite will catch omissions).
- Full suite must stay green (currently 164).

## Rollout

- Markdown/methodology change → PR is **human-merged** (auto-review loop routes it
  away from auto-merge; correct).
- Version bump (minor, e.g. 2.10.0) + CHANGELOG per the repo release convention;
  on merge, auto-tag + release publish (now end-to-end after #44).
- Optionally exercise the new checkpoint against the bundled sample engagement to
  confirm it renders from real Phase 4 outputs.

## Risks / open points

- **Renderer generality.** The baseline renderer must handle engagements whose
  processes carry different metric sets; it renders what exists and marks the rest
  PENDING. (This also exposes that the Phase 11 renderers are sample-specific —
  noted, not fixed here.)
- **Gate-mode complexity.** Adding checkpoint mode must not weaken the terminal
  gate. Keep the change additive and guard the terminal path.
- **Scope creep to CP1/CP3.** Explicitly out of scope; the registry makes them
  cheap later.
