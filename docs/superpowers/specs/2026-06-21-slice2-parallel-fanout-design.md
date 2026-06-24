# Slice 2 · Chunk A — Parallel per-process fan-out (design)

> Part of **#87** (Slice 2: Adaptive + Parallel + Editable), under epic **#85**. Umbrella: `docs/superpowers/specs/2026-06-19-public-ai-first-distribution-design.md` §3.D.
> Chunk A of three. B = edit/interruption-splicing, C = granular autonomy + register-teaching + holding-the-line. Each ships its own spec→plan→PR, accumulating under CHANGELOG `[Unreleased]`; one `v2.19.0` release closes #87.

## 1. What the user experiences (AI-first)

On a multi-process engagement, once the processes are mapped the AI says one thing —
*"I've mapped all six processes; now finding opportunities across them together"* — and
returns the **combined** opportunity landscape, fast, including any **cross-process
automation chain** that no single process revealed on its own. The user never hears
"subagent," "Phase 5," or "OPP-003." The parallelism is invisible trust-machinery; the
visible promise is *"I looked at the whole board at once."*

Single-process engagements (N=1) are unchanged: nothing to parallelize, identical
sequential spine.

## 2. Scope

**In:** concurrent per-process **Phase 5** (opportunity identification) fan-out, a
deterministic merge that assigns global `OPP-NNN` ids by process order, reuse of the
existing convergence + cross-process chain-detection gates, batch-failure handling, and
graceful degradation to sequential on surfaces without concurrent dispatch.

**Out (deferred follow-up):** Phase 4-synthesis fan-out. Its value is context isolation,
not speed (the interview is human-bound and unparallelizable), and it requires a new
per-process raw-notes artifact plus a restructure of the Baseline-gate phase — too much
blast radius to build speculatively. Revisit only if Phase 5 fan-out proves the pattern
and isolation quality demands it. Tracked as a note here, not built.

**Out:** any engine/math change. The engine, staleness, hashing, and convergence machinery
already exist from Slice 1. This chunk is conductor orchestration + a small deterministic
merge helper + guards.

## 3. The crux — deterministic merge by process order

Global `OPP-NNN` ids are portfolio-sequential. If N subagents each minted ids
independently they would all start at `OPP-001` and collide. Therefore **subagents do not
assign final ids.** Each writes its process's opportunities into a staging namespace; the
conductor performs a single deterministic merge:

- Iterate processes in **`processes/_index.md` order** (stable, not completion order).
- Assign global `OPP-NNN` sequentially across that ordered traversal.
- Write the canonical `opportunities/OPP-NNN.md` files + `opportunities/_index.md`.
- Run the existing cross-process chain-detection scan over the merged set.

Because id assignment is driven by process order, **concurrent and sequential fan-out
produce byte-identical `opportunities/`.** This preserves the determinism north star
("no randomness; re-running yields identical output") and is the headline guard.

### 3.1 Staging layout

Each per-process subagent writes to `opportunities/_staging/PROC-NNN/`:
provisional opportunity files for that process only (process-local numbering, e.g.
`OPP-PROC003-01`, which never escapes staging). Disjoint directories → zero write-conflict
under concurrency. The conductor reads all staging dirs, renumbers into global `OPP-NNN`,
writes the canonical files, and removes `_staging/`. Staging is an implementation detail,
never a methodology output.

### 3.2 The merge helper (tested `state/` unit)

The renumber+merge is a small **`state/`** helper, not conductor prose, because
"deterministic" deserves a test, not a promise. Proposed surface:

```
state/opportunity_merge.py
  merge_staged_opportunities(folder) -> list[str]   # returns assigned OPP ids, in order
```

It reads `processes/_index.md` for canonical order, walks
`opportunities/_staging/PROC-NNN/` in that order, assigns global `OPP-NNN`, and writes
`opportunities/OPP-NNN.md` + a fresh `opportunities/_index.md`. It builds a
provisional→final id map per process and applies it across that process's files, so an
intra-process **chain-formation** reference (one staged OPP citing another by its
provisional id) is rewritten to the final global id, not just the file's own id header.
(Cross-process chains don't exist yet at this point — the conductor's chain-detection runs
*after* merge.) It then clears staging. Pure stdlib (consistent with the
stdlib-only core). It assigns ids and moves files only — it makes **no value claim and no
arithmetic**, so it stays clear of the engine's exclusive ownership of numbers.

This makes Chunk A a Python PR (auto-merge-eligible per the auto-review loop) rather than
pure markdown.

## 4. Orchestration (conductor changes)

In `skills/conducting-engagement/SKILL.md`:

- **Trigger:** when the next step is Phase 5 (opportunity identification) **and** ≥2
  in-scope processes have `Baseline = Ready` (convergence already requires the full set
  before Phase 6; fan-out runs after discovery is complete for all processes). N<2 → run
  Phase 5 once, sequentially, exactly as today.
- **Fan-out dispatch:** one subagent per process, each given the engagement folder,
  `engine_root`, and a single `PROC-NNN` scope. Each runs
  `ai-process-assessment:identifying-opportunities` scoped to that one process, writing
  into `opportunities/_staging/PROC-NNN/`. Hand artifacts as files (SDD discipline) — the
  subagent returns only a one-line confirmation, not opportunity content.
- **Merge:** call `merge_staged_opportunities(folder)`, then run cross-process
  chain-detection over the merged `opportunities/`, then proceed to convergence/Phase 6 as
  today.
- **Degradation:** on a surface without concurrent dispatch (e.g. Claude.ai), run the
  per-process subagents sequentially into the same staging layout. Same merge, same ids,
  identical result. Fan-out is an optimization; the sequential path is the invariant.

In `skills/identifying-opportunities/SKILL.md`:

- Make **single-process-scoped dispatch** explicit: when invoked with one `PROC-NNN`, the
  phase reads only that process, writes only that process's opportunities, into the staging
  path, with process-local provisional ids. The existing whole-portfolio behavior remains
  for the N=1 / sequential path.

## 5. Failure handling

- One subagent fails → re-dispatch **only that process**; other processes' staged outputs
  are retained; **do not merge until the full set is staged** (convergence already demands
  every in-scope process). This refines the existing "subagent fails → stop" rule into
  "fails → re-dispatch that process, others kept."
- Merge helper error → stop, surface (must-ask), never advance on a failed merge.

## 6. Decisions & determinism interplay

- The deterministic merge means re-running fan-out (concurrent or sequential) over the same
  staged inputs is reproducible — no decision-log churn from id reshuffling.
- Opportunity-type classification remains a structural-class decision logged per the
  existing decision-log rules; fan-out does not change what gets logged, only how many
  subagents produce drafts in parallel.

## 7. Testable acceptance (guards)

1. **Determinism / order-invariance:** given staged per-process opportunities, the merge
   assigns `OPP-NNN` by `processes/_index.md` order; a test that stages the same inputs in
   shuffled directory-iteration order still yields byte-identical `opportunities/`.
2. **Trigger condition:** conductor prose dispatches concurrent per-process Phase 5 only
   when ≥2 processes have Ready baselines; N=1 stays the sequential spine.
3. **Disjoint staging:** per-process subagents write only their own `_staging/PROC-NNN/`;
   no path overlap (collision-free by construction).
4. **Batch failure:** one failed process → re-dispatch that process only; no merge until
   the full set is staged.
5. **Jargon-free user prose:** the user-facing fan-out narration carries no "subagent",
   "Phase 5", or `OPP-NNN` tokens (reuse the §3.B jargon-guard pattern).

## 8. Files touched

- `state/opportunity_merge.py` (new) + `tests/` for the merge helper (guards 1, 3).
- `skills/conducting-engagement/SKILL.md` (fan-out trigger, dispatch, merge, degradation,
  failure — guards 2, 4, 5).
- `skills/identifying-opportunities/SKILL.md` (explicit single-process-scoped dispatch +
  staging path).
- `tests/` guards for the conductor prose (2, 4, 5).
- `CHANGELOG.md` under `[Unreleased]`; **no version bump** (accumulates toward v2.19.0).

`skills/using-methodology/SKILL.md` / `system-prompt.md` are **not** touched (verbatim-sync
guard, off-limits). Golden `results.json` is untouched (no arithmetic in this chunk).
