# Slice 2 · Chunk A — Parallel per-process Phase 5 fan-out (reconciled design)

**Date:** 2026-06-24
**Status:** Design (approved in brainstorming; pending written-spec review)
**Supersedes:** `2026-06-21-slice2-parallel-fanout-design.md` (written one day before the #100
assembly layer landed; its proposed `state/opportunity_merge.py` is now redundant).
**Umbrella:** `2026-06-19-public-ai-first-distribution-design.md` §3.D · issue **#87** · epic **#85**.

> Chunk A of three. B = edit/interruption-splicing, C = granular autonomy + register-teaching
> + holding-the-line. Each ships its own spec → plan → PR, accumulating under CHANGELOG
> `[Unreleased]`; one `v2.19.0` release closes #87.

---

## 1. Why this is smaller than the original design

The 2026-06-21 design was authored **one day before** the portable assembly layer (#100, merged
as `193b009`) landed. Reconciling against today's code, most of Chunk A's mechanics already exist:

| Original Chunk A scope | Reality today |
|---|---|
| Concurrent per-process Phase 5 fan-out | Already in `skills/identifying-opportunities/SKILL.md` — parallel `opportunity-typer` batch, one per process |
| Deterministic process-order merge | Already in `state/assembly.py` `renumber_sequential` — the proposed `state/opportunity_merge.py` is redundant |
| Convergence + cross-process chain-detection | Already in `skills/conducting-engagement/SKILL.md` (Slice 1) |
| Phase 4-synthesis fan-out | Original design itself defers it (interviews are human-bound) |

What remains is **relocating fan-out ownership** to the conductor plus the AI-first UX and
failure posture — with **zero new `state/` code**. This honors the project's "no siloed code"
directive (the same principle that killed the original `feat/slice2-parallel-fanout` branch).

## 2. The architectural decision (the crux)

The conductor treats Phase 5 as a **single headless subagent**, but the Phase 5 skill dispatches
a **parallel batch of per-process sub-subagents** — and a subagent generally cannot spawn nested
subagents. So today's parallelism risks silently collapsing to sequential-inside-one-subagent.

**Decision (approved):** the **conductor owns the fan-out**. It dispatches the per-process
agents from main context (which *can* dispatch concurrently); the Phase 5 skill gains a
single-process-scoped mode and no longer self-dispatches when driven by the conductor.

## 3. Scope

**In:**
- Relocate per-process Phase 5 fan-out ownership to the conductor.
- Give `identifying-opportunities` an explicit **single-process-scoped** mode (write one
  process's staging, return a one-line summary, **do not assemble**).
- Conductor performs the merge via the **existing** `state/assembly.py` primitives.
- `≥2`-process trigger; N=1 stays the sequential spine.
- Cross-surface degradation to sequential.
- Per-process batch-failure handling.
- Jargon-free user-facing narration.

**Out (deferred follow-up, per the umbrella design):** Phase 4-synthesis fan-out. Its value is
context isolation, not speed (the interview is human-bound and unparallelizable), and it would
need a new per-process raw-notes artifact plus a Baseline-gate restructure — too much blast
radius to build speculatively. Tracked as a note, not built.

**Out:** any engine/math change; **any new `state/` helper**. The engine, staleness, hashing,
and convergence machinery already exist; `renumber_sequential` already does the deterministic
merge.

## 4. Architecture

### 4.1 Conductor (main context) owns dispatch
In `skills/conducting-engagement/SKILL.md`:

- **Trigger:** when the next step is Phase 5 (opportunity identification) **and** ≥2 in-scope
  processes have `Baseline = Ready`. (Convergence already requires the full set before Phase 6;
  fan-out runs after discovery is complete for all processes.) N<2 → run Phase 5 once,
  sequentially, exactly as today.
- **Fan-out dispatch:** dispatch one `ai-process-assessment:identifying-opportunities` subagent
  per process, each given the engagement folder, `engine_root`, and a single `PROC-NNN` scope,
  in one concurrent batch. SDD discipline: hand artifacts as files; each subagent returns only a
  one-line confirmation (process id, opportunity count, GRC flag counts), never opportunity
  content.
- **Merge (conductor-side, after the full set is staged):**
  `collect_staged('<name>/_staging/phase5')` →
  `renumber_sequential(staged, '<name>/opportunities', 'OPP')` →
  `index_from_headers(...)` → `cleanup('<name>/_staging/phase5')`, via the existing
  `PYTHONPATH="<engine_root>" python3 -c "from state.assembly import …"` form.
- **Then** run the existing cross-process chain-detection scan over the merged
  `opportunities/`, then proceed to convergence / Phase 6 as today.

### 4.2 Determinism
Each per-process subagent writes `<name>/_staging/phase5/proc-<id>.md` (disjoint files → zero
write-conflict under concurrency). `renumber_sequential` assigns global `OPP-NNN` in staged-file
sort order, which equals process order (`proc-001`, `proc-002`, … sort to `PROC-001`,
`PROC-002`, …). Therefore **concurrent and sequential fan-out produce byte-identical
`opportunities/`** — already covered by `renumber_sequential`'s #100 determinism/order-invariance
tests.

### 4.3 Phase 5 skill — single-process mode
In `skills/identifying-opportunities/SKILL.md`:

- Make single-process-scoped dispatch explicit: when invoked with one `PROC-NNN`, the phase reads
  only that process's `processes/PROC-NNN.md` (plus relevant `tech-inventory.md` sections),
  writes only that process's opportunities into `_staging/phase5/proc-<id>.md` with provisional
  `## TEMP-` ids, and **does not assemble**.
- The existing whole-portfolio behavior (self-dispatch batch + assemble) remains for **direct
  (non-conductor) invocation** and the N=1 path.

## 5. Trigger / degradation / failure

- **Trigger:** next step Phase 5 **and** ≥2 Ready baselines → concurrent fan-out. N=1 → single
  whole-portfolio invocation (unchanged spine).
- **Degradation:** on a surface without concurrent dispatch (e.g. Claude.ai), run the same
  per-process invocations **sequentially** into the same staging layout → same merge → identical
  result. Fan-out is an optimization; the sequential path is the invariant.
- **Failure:** one process's subagent fails → **re-dispatch only that process**; retain other
  processes' staged outputs; **do not merge until the full set is staged** (convergence already
  demands every in-scope process). This refines the existing "subagent fails → stop" rule into
  "fails → re-dispatch that process, others kept." Merge-helper error → stop, surface (must-ask),
  never advance on a failed merge.

## 6. UX (AI-first)

On a multi-process engagement, once processes are mapped the AI says one thing —
*"I've mapped all six processes; now finding opportunities across them together"* — and returns
the **combined** opportunity landscape, including any cross-process automation chain that no
single process revealed alone. The user never hears "subagent," "Phase 5," or "OPP-003."
Parallelism is invisible trust-machinery; the visible promise is *"I looked at the whole board at
once."* Reuse the §3.B jargon-guard pattern. Single-process (N=1) engagements are unchanged.

## 7. Decisions & determinism interplay

- The deterministic merge means re-running fan-out (concurrent or sequential) over the same staged
  inputs is reproducible — no decision-log churn from id reshuffling.
- Opportunity-type classification remains a structural-class decision logged per the existing
  decision-log rules; fan-out changes only how many subagents produce drafts in parallel, not what
  gets logged.

## 8. Testable acceptance (guards)

1. **Trigger condition:** conductor prose dispatches concurrent per-process Phase 5 only when ≥2
   processes have Ready baselines; N=1 stays the sequential spine.
2. **Single-process scope:** an `identifying-opportunities` invocation scoped to one `PROC-NNN`
   writes only its own `_staging/phase5/proc-<id>.md` and does not assemble.
3. **Batch failure:** one failed process → re-dispatch that process only; no merge until the full
   set is staged.
4. **Jargon-free narration:** the user-facing fan-out narration carries no "subagent", "Phase 5",
   or `OPP-NNN` tokens (reuse the §3.B jargon-guard pattern).
5. **Determinism / order-invariance:** covered by the existing `renumber_sequential` tests; no new
   merge code, so no new determinism test is required (a regression test referencing the
   per-process staging convention may be added if cheap).

## 9. Files touched

- `skills/conducting-engagement/SKILL.md` — fan-out trigger, conductor-side dispatch, merge,
  degradation, failure, narration (guards 1, 3, 4).
- `skills/identifying-opportunities/SKILL.md` — explicit single-process-scoped mode +
  no-assemble-when-scoped (guard 2).
- `tests/` — conductor-prose + skill-prose guards (1–4).
- `CHANGELOG.md` under `[Unreleased]`; **no version bump** (accumulates toward `v2.19.0`).

**Not touched:** `skills/using-methodology/SKILL.md` / `system-prompt.md` (verbatim-sync guard,
off-limits); golden `results.json` (no arithmetic in this chunk); `state/assembly.py` (reused
as-is — no new helper).

## 10. Known limitation (no regression)

`renumber_sequential` rewrites a block's own provisional `TEMP-` id throughout that block, but does
**not** remap a cross-block reference within the same process (one staged OPP citing another by its
provisional id). This matches today's behavior — it is not introduced by Chunk A. Cross-process
chains are detected by the conductor **after** merge, so they reference final global ids.

## 11. Merge note

This chunk is mostly methodology markdown (conductor + skill prose) plus test guards. The
auto-review/auto-merge gate will **HOLD** it as a markdown-touching change (as it did for #101) →
**merge by hand with a decision comment**. Expected, not a defect.
