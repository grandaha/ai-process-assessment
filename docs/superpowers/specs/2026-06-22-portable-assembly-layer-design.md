# Portable staging + assembly layer (design)

> Tracks **#100**, under epic **#85**. Surfaced during Slice 2 (#87) parallel-fan-out work, which it supersedes and underpins.
> Supersedes the abandoned `feat/slice2-parallel-fanout` branch (its merge-helper logic + tests carry forward into `state/assembly.py`).

## 1. Problem

The methodology's fan-out-and-assemble pattern is a **universal convention**: a phase dispatches one subagent per unit (round / process / opportunity / section / initiative), each writes its output to `<engagement>/_staging/<phase>/<unit>.md`, the orchestrator assembles the canonical artifact from the staging files, then removes the staging tree. Eight phases use it. **A source audit (2026-06-22) found the assembler is split into two surfaces:**

| Phase | Skill | Unit | Staging | Assembler today | Surface |
|---|---|---|---|---|---|
| 4 Discovery | `discovering-processes` | per round | `_staging/phase4/round-N.md` | Bash `for` loop builds `processes/_index.md` | **shell** (index-from-files) |
| 5 Opportunities | `identifying-opportunities` | per process | `_staging/phase5/proc-*.md` | **awk** renumber `TEMP-`→`OPP-NNN`, split, index | **shell** (renumber + index-from-headers) |
| 6 Scoring | `scoring-opportunities` | per OPP | `_staging/phase6/OPP-NNN.md` | `mv` + Python (composites→`scores.json`) + shell index | **shell** (promote + index); engine Python stays |
| Gate A GRC | `governance-risk-gate` | per flagged OPP | `_staging/grc/OPP-NNN.md` | `mv` + shell index | **shell** (promote + index) |
| 8 Packaging | `packaging-usecases` | per OPP | `usecase-briefs/UC-NNN.md` (direct) | model authors `_index.md` in main context | **main-context** (no shell) |
| 9 Business case | `building-business-case` | per initiative | `_staging/phase9/<id>.md` | model concatenates blocks + label-verify + assumptions | **main-context** (no shell) |
| 11 Deliverable | `building-deliverable` | per section | `_staging/phase11/<section-id>.html` | model interleaves blocks by `id=` anchor + generates shell/`<style>` | **main-context** (no shell) |
| Checkpoints | `building-checkpoint` | per section | `_staging/checkpoint-<id>/<section-id>.html` | model assembles + generates shell/`<style>` | **main-context** (no shell) |

**Only the first four phases assemble in inline shell** (`awk`, `mv`, `for f in`, `grep -o`). Shell does not run in Claude.ai's Python-only code tool, so **those four assemblers are non-portable** — a systemic barrier to the cross-surface goal (§3.A / AC-2), not a Phase-5 quirk. The other four assemble **in main context**: the model itself reads the staged blocks and writes the artifact. They are not *broken* on any surface (the model runs everywhere), but they are **non-deterministic and untested**, and two of them are genuinely generative — Phase 11/checkpoints *interleave* blocks by HTML anchor and generate the page shell/`<style>`; Phase 8/9 mix a deterministic file step with model-authored content (the `_index.md` "one-line description" column, label verification, Key-Assumptions compilation). A plain `concat` does not capture them.

**Scope decision (2026-06-22, Dave):** build `state/assembly.py` as the full shared toolkit — including `concat_ordered`, built and unit-tested so it is ready — but **migrate only the four shell phases now** (4, 5, 6, Gate A). That delivers the actual portability win, behavior-preserving, with one shared module and no silo. The four main-context phases are a **scoped follow-up** (§6): converting them is a *determinism + tested-path* change, not a portability fix, and Phase 11/checkpoints need a richer interleave primitive than concat — decide their target shape before forcing a primitive onto generative assembly.

## 2. Solution

A single stdlib-only `state/assembly.py` — a **toolkit of small composable primitives** that each phase composes via a one-line `python3 -c "from state.assembly import …"` call, replacing its inline shell. One convention, one tested module, every phase.

**Home: `state/`, not `engine/`.** The engine owns *math* (formulas, golden numbers). This layer does *file orchestration* and computes no numbers. The boundary stays crisp — **engine = numbers, `state/assembly` = files.** Phase 6's composite math and `model/scores.json` remain entirely in the engine; the assembler only moves the scored files and rebuilds the index from their headers.

### 2.1 Primitives

All take/return `pathlib.Path` / `str`, pure stdlib (`pathlib`, `re`, `shutil`), matching existing `state/` modules (`from __future__ import annotations`, module docstring, pure functions). Signatures are the design intent; exact final names are fixed in the plan.

- `collect_staged(staging_dir) -> list[Path]` — staged files in **deterministic** (sorted) order. Returns `[]` if the dir is absent.
- `renumber_sequential(files, dest_dir, prefix, *, order=None) -> list[str]` — split staged files that contain multiple `## TEMP-<token>` entries into one canonical `<dest>/<PREFIX>-NNN.md` per entry, assigning `<PREFIX>-NNN` (3-digit) in `order` (a list of unit ids; default = `files` order), and **remap every provisional `TEMP-` id in the body to its final id** (own heading + intra-unit references). Returns the assigned ids. *(Phase 5: `prefix="OPP"`, `order`=processes/_index.md order.)*
- `index_from_headers(files, dest_index, columns) -> int` — rebuild a markdown `_index.md` table at `dest_index` by extracting each file's `<!-- index: key=val … -->` header, emitting `columns` (ordered list of `(Header, key)`). Returns row count. *(Phases 5, 6, 8.)*
- `index_from_fields(files, dest_index, columns, extract) -> int` — same, but pulls fields via a small per-phase mapping when there is no extraction header *(Phase 4: read each `PROC-NNN.md`'s id/name/baseline).* Kept distinct from `index_from_headers` so Phase 4's source-of-truth (the assembled PROC files) is explicit.
- `promote(staging_dir, dest_dir, *, pattern="*.md") -> list[Path]` — move per-unit staged files to the canonical dir, returning the moved paths. *(Gate A → `grc/`, Phase 6 → `scores/`, Phase 8 → `usecase-briefs/`.)*
- `concat_ordered(files, dest_file, order, *, sep="\n") -> Path` — concatenate staged files in an explicit `order` (list of unit ids → matched to filenames) into one document at `dest_file`. Format-agnostic (md or html). *(Phases 9, 11, checkpoints.)*
- `cleanup(staging_dir) -> None` — remove the staging tree (stdlib `shutil.rmtree(..., ignore_errors=True)`), which also fixes the existing "Cleanup skipped (sandbox restriction)" shell fragility gracefully.

### 2.2 Per-phase composition

- **Phase 4:** orchestrator synthesis (cross-round judgment — stays in main context, NOT delegated) writes `processes/PROC-NNN.md`; then `index_from_fields(PROC files) → processes/_index.md`; `cleanup`. *(Only the index `for` loop is replaced; synthesis is untouched.)*
- **Phase 5:** `collect_staged` → `renumber_sequential(prefix="OPP", order=processes order)` → `index_from_headers → opportunities/_index.md` → `cleanup`. *(Replaces the awk block; `opportunity-typer` and the `## TEMP-`/`<!-- index: -->` format are unchanged.)*
- **Phase 6:** `promote(_staging/phase6 → scores/)`; engine computes composites + `model/scores.json` (**unchanged**); `index_from_headers → scores/_index.md`; `cleanup`.
- **Gate A:** `promote(_staging/grc → grc/)`; `cleanup`.
- **Phase 8:** `promote(_staging/phase8 → usecase-briefs/)`; `index_from_headers → usecase-briefs/_index.md`; consistency pass (judgment, stays); `cleanup`.
- **Phase 9:** `concat_ordered(_staging/phase9, business-case.md, order=Wave-1 initiative order)`; `cleanup`.
- **Phase 11:** `concat_ordered(_staging/phase11, deliverable.html, order=page order)`; `cleanup`.
- **Checkpoints:** `concat_ordered(_staging/checkpoint-<id>, <out>.html, order=registry section order)`; `cleanup`.

### 2.3 Determinism

Defined once, applied layer-wide: id assignment and index/concat ordering follow a **canonical order** (an explicit `order` argument, or sorted filenames), never subagent completion order. Output is therefore reproducible regardless of dispatch timing — the property the abandoned Chunk A helper proved, now generalized. No primitive uses `iterdir`/`glob` for ordering without sorting.

## 3. Migration approach

One phase per task (each independently testable and reviewable). **This plan migrates the four shell phases only** (per the §1 scope decision):

1. **Build `state/assembly.py` + full unit tests** for every primitive — including `concat_ordered` (built and tested now so the follow-up has it ready), even though no phase wires it in this plan. The determinism/order-invariance test is the headline. No phase wired yet.
2. **Migrate Phase 5** (the awk — gnarliest, and the original Chunk A target): swap the assembler for layer calls; guard that no `awk` remains and the layer is called.
3. **Migrate Phase 6**, **Gate A**, **Phase 4** — each its own task: replace the shell assembler with the layer call(s), add a per-phase guard asserting no shell assembler remains (`awk`/`for f in`/`grep -o` absent from the assembly section) and the layer is invoked. Phase 6 keeps its inline composite-math Python (engine territory) untouched — only the `mv` and the shell index loop are replaced.

The four main-context phases (8, 9, 11, checkpoints) are **not** touched in this plan; they remain a follow-up (§6).

Each migration must keep the canonical output byte-compatible in structure (same files, same `_index.md` columns, same ids) — these are behavior-preserving refactors, not redesigns. The one accepted cosmetic difference: the `_index.md` separator row (the `|---|---|` dashes) may differ in dash count; markdown renders identically and no test or golden pins it. Column header labels and all data cells are preserved verbatim. Where a phase's golden/sample output exists, it must not change.

## 4. Constraints

- **Stdlib only.** No import outside the standard library (the layer must run in any Python code sandbox).
- **No arithmetic / no value claims.** The layer orchestrates files only. All numbers stay in the engine; `model/*.json` and `results.json` are untouched by this work.
- **Behavior-preserving.** Canonical artifacts (`processes/`, `opportunities/`, `scores/`, `grc/`, `usecase-briefs/`, `business-case.md`, `deliverable.html`, every `_index.md`) keep the same structure, ids, and columns. The `<!-- index: -->` extraction-header format and the `## TEMP-` provisional-id format are kept as-is (tested by existing guards, e.g. `tests/test_guards.py` typer tokens).
- **Off-limits:** `skills/using-methodology/SKILL.md` and `system-prompt.md` (verbatim-sync guard). The engine and golden `results.json`.
- **Agents unchanged.** `opportunity-typer`, `opportunity-scorer`, the renderers, etc. already write the staging files; only the *assembler* (orchestrator side) changes.
- **CHANGELOG** under `[Unreleased]`, no per-task version bump; one release closes #100.

## 5. Testable acceptance

1. **Primitive unit tests** in `state/tests/test_assembly.py` — each primitive, including edge cases (missing staging dir, empty dir, staged file without header, multiple entries per file, intra-unit reference remap).
2. **Determinism guard** — `renumber_sequential` / `index_from_headers` / `concat_ordered` produce byte-identical output under shuffled staged-file creation order.
3. **Per-phase migration guards** — for each migrated phase, a guard that the assembly section invokes `state.assembly` and contains no shell assembler tokens (`awk`, `for f in`, `grep -o`, `ls ` … `wc -l`).
4. **Full suite green** at every task (baseline before this work: 256 on `main`; the Slice-2 branch's 264 are abandoned with that branch).
5. **No engine drift** — `model/*.json`, `results.json`, and the golden-number suite are unchanged.

## 6. Out of scope

- **The four main-context phases (8 Packaging, 9 Business case, 11 Deliverable, Checkpoints) — deferred follow-up.** They assemble in main context, not shell, so they are already cross-surface; converting them buys determinism + a tested path, not portability. Phase 11/checkpoints need an anchor-ordered *interleave* primitive (richer than `concat_ordered`) plus a decision on how much of the model-generated shell/`<style>` should become deterministic; Phase 8/9 need their deterministic file step separated from model-authored content. Scope and design these once the four shell phases prove the layer. `concat_ordered` is built and tested in this plan so the follow-up starts with it in hand.
- The Slice 2 (#87) conductor parallel-fan-out **UX** (the AI-first "working through all your processes together" framing, ≥2-process trigger, batch-failure posture). That resumes on top of this layer once it lands.
- Phase 4-synthesis fan-out (still deferred, per the original Slice 2 scoping).
- Any change to subagent dispatch itself, agent specs, or the `<!-- index: -->` / `## TEMP-` formats.
- Any new artifact or deliverable (tracked separately as #99).
