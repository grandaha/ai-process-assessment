# Deterministic, Declarative Checkpoint Documents — Design

**Issue:** #131 · **Date:** 2026-06-28 · **Status:** approved (brainstorming)

## Problem

The three interim checkpoints (`scope`, `baseline`, `portfolio`) render as **LLM-authored HTML**:
`building-checkpoint` dispatches a `section-renderer-checkpoint-*` agent per checkpoint, which
reads source files and emits HTML section blocks assembled into an OSL-branded shell. Two costs:

1. **Not commentable.** Clients review these to confirm/correct; HTML can't take inline
   comments/track-changes the way stakeholder review needs (#131).
2. **Non-deterministic.** The structure/phrasing is model-authored each run — the opposite of
   the project's deterministic ethos (#120). The renderers "compute nothing" (figures verbatim
   from source) but still freestyle layout/ordering/emphasis per run.

Meanwhile #136 shipped a deterministic, per-process checkpoint (`process-validation`) on a
different (better) pattern: a Python transform → `state/docx.py` → `.docx`. We now have two
checkpoint patterns. And #99 wants *more* per-phase artifacts, which is expensive under the
per-checkpoint-agent model.

## Goal

Make every checkpoint a **deterministic, declarative document**: described as data in a
registry, rendered identically every run to **Word (`.docx`)** via a thin shared layer. Convert
the 3 existing checkpoints, fold `process-validation` into the same layer, and make adding a
future checkpoint a registry entry — no new agent, no HTML, no machinery.

This is the AI-native end state for checkpoints: the AI drives *when/whether* and narrates it
conversationally; the **artifact is deterministic and consistent** (the rule enforced in
#125/#128, the determinism of #120/#136).

## Non-goals

- **Phase 11 `deliverable.html` is untouched** — it stays HTML. This is interim checkpoints only.
- **Not deciding the deliverable taxonomy (#99).** This builds the *mechanism*; deciding *which*
  additional per-phase artifacts to add is a fast follow that adds registry entries.
- No new analytical content — fields are copied verbatim from source (the no-fabrication invariant).
- Not full HTML visual parity in Word — minimal OSL styling (heading color + DM Sans), as in #136.

## Architecture

### 1. `state/docx.py` (exists, #136) — reused unchanged
Block-model → `.docx`. Blocks: `heading`, `paragraph`, `numbered_list`, `table`.

### 2. `state/checkpoint_doc.py` (new) — the thin shared layer
- **Section builders** on top of `docx` blocks (each returns a list of blocks):
  - `field_section(title, md, label)` — heading + paragraph from a `**label:**` field.
  - `steps_section(title, md)` — heading + numbered list from a `**Steps:**` block (strips `→` color notes).
  - `table_from_index(title, index_md, columns)` — heading + table from a `_index.md` markdown table (selected columns).
  - `table_from_baselines(title, baselines_json, fields)` — heading + per-process metrics table.
  - `signoff_block(...)` — owner/outcome/comments scaffold.
  - `note(text)` — a confirm-or-correct instruction paragraph.
- **Registry** — pure data, one entry per checkpoint:
  ```python
  CHECKPOINTS = {
    "scope": Checkpoint(
        id="scope", per_process=False, gate=False,
        sources=["scope.md", "context.md"],
        output="checkpoints/checkpoint-scope.docx",
        outcome="checkpoints/CP-scope-outcome.md",
        sections=[ ... section descriptors ... ],
        exclusions=[...]),   # see Per-checkpoint content
    "baseline": ..., "portfolio": ..., "process-validation": ...,
  }
  ```
  A section descriptor names a builder + its source + args (declarative). `per_process=True`
  fans out one doc per `Ready` process (process-validation); else a single doc.
- **Driver** `render_checkpoint(engagement_dir, checkpoint_id) -> list[str]`: looks up the
  entry, reads sources, runs each section descriptor → assembled block list →
  `docx.build_docx`; writes the output doc(s) + outcome stub(s) (no clobber of existing
  outcomes). Returns the paths written.
- **CLI** `python3 -m state.checkpoint_doc <engagement_dir> <checkpoint_id>`.

### 3. Registry entries (4)
- **`process-validation`** — per-process. **Reuse #136's working code, don't rewrite it:**
  `state/process_review.py::build_blocks` stays as this checkpoint's per-process extractor; the
  `checkpoint_doc` driver owns the generic per-process fan-out + outcome stubs and calls
  `build_blocks` for the blocks. (So `render_all` in `process_review.py` is superseded by the
  generic driver, but `build_blocks` is kept and called.)
- **`scope`**, **`baseline`**, **`portfolio`** — see content below.

### 4. `building-checkpoint` — route everything through the deterministic command
All checkpoint ids run `PYTHONPATH=<engine_root> python3 -m state.checkpoint_doc <name> <id>`.
The Session Start id-list, predecessor checks, and the deterministic-routing branch (from #136)
generalize to all ids. The LLM section-renderer dispatch, the HTML shell, and the
deliverable-gate Checkpoint Mode step are removed for checkpoints.

### 5. Removed (deduped)
- `agents/section-renderer-checkpoint-{scope,baseline,portfolio}.md`
- The checkpoint HTML shell block in `building-checkpoint`.
- `deliverable-gate` **Checkpoint Mode** (no LLM authoring left to gate; the final Gate B for
  Phase 11 is untouched). Remove its section + any references.

## Per-checkpoint content (verbatim from source)

- **scope** ← `scope.md` + `context.md`. Sections: engagement header, scope summary, in/out
  of scope, stakeholders, plus a confirm-or-correct note + sign-off. **Exclusions (CP1 guard,
  carried over verbatim):** never render risk posture, AI/automation maturity, or political
  landscape.
- **baseline** ← `processes/PROC-NNN.md` + `model/baselines.json`. Single doc: per-process
  metrics table (volume, cycle time, error/exception rate, FTE — verbatim, `PENDING` where
  absent), confirm-or-correct note, sign-off. (Distinct from process-validation: this is the
  cross-process *summary*; process-validation is the per-process *step-by-step detail*.)
- **portfolio** ← `scores/_index.md` + `opportunities/_index.md` + `roadmap.md`. Single doc:
  scored-opportunity table, roadmap waves, confirm-or-correct note, sign-off.
- **process-validation** ← per-process detail (unchanged from #136): trigger/steps[stripped]/
  actors/decision points/exceptions/upstream-downstream + baseline figures + sign-off.

## Data flow

```
Conductor (decides when, narrates) → building-checkpoint <id>
  → python3 -m state.checkpoint_doc <name> <id>
      → registry[id]: read sources → section builders → blocks → docx.build_docx
      → write checkpoint-<id>.docx (or per-process PROC-NNN.docx) + outcome stub(s)
  → owner/stakeholder reviews .docx, records outcome in CP-*-outcome.md
```

## Gates / behavior

- **process-validation** keeps its **hard gate** before Phase 5 (#136), unchanged.
- **scope/baseline/portfolio** stay **recommended-and-recorded** (existing behavior), now Word.

## Relationship to other issues

- **Delivers #120's interim-document half** — the 3 checkpoints become deterministic/canonical
  (registry = the structure contract). #120's Phase-11-deliverable half stays open.
- **Enables #99** — adding a per-phase artifact becomes a registry entry; the registry carries
  an (optional) insertion-phase field so #99 can declare new artifacts without new machinery.
- **Folds in #136** — `process-validation` joins the shared layer; one pattern for all checkpoints.

## Testing

- `checkpoint_doc` section builders: each returns the expected blocks from a fixture (field
  extraction, color-note stripping, table-from-index/baselines).
- Each registry entry renders a valid `.docx` (valid zip + parses) with expected content; the
  **scope** doc excludes risk posture / AI maturity / political landscape (guard); baseline
  shows `PENDING` for missing metrics; per-process fan-out for process-validation.
- `building-checkpoint` routes all 4 ids through the deterministic command; the removed agents
  and HTML/Checkpoint-Mode references are gone (guards).
- Update `tests/test_branding.py`: drop/replace assertions that expect checkpoint **HTML**
  (`assets/osl/...` inlined into checkpoint HTML, `class="brand-logo"` in checkpoints). Phase 11
  deliverable branding assertions stay.
- Gate tests (process-validation) unchanged.

## Ponytail notes (keep it thin)

- The shared layer is **helpers + a data registry + one driver** — not a generic "rendering
  framework." Section descriptors are dumb data; extractors are tiny functions. We generalize
  across **4 real** checkpoints, not an imagined one.
- Word styling is minimal (heading color + DM Sans). No numbering.xml (steps render `"N. text"`),
  inherited from `docx.py`.
- Tests assert valid-zip + content, not byte-golden.

## Open questions

None blocking. Confirmed in brainstorming: full unification (all 4 on the shared layer);
baseline stays a single summary doc distinct from process-validation; delete the 3 agents +
HTML shell + deliverable-gate Checkpoint Mode outright.
