# Slice 3 · Chunk A — Messy/partial-state handling + resume hardening

**Part of:** Epic #85 → Slice 3 (#88), spec §3.E (`docs/superpowers/specs/2026-06-19-public-ai-first-distribution-design.md`).
**Date:** 2026-06-24.

## 1. Problem

The state layer judges a phase **done** purely by output-file existence
([`state/state.py`](../../../state/state.py) `_phase_status`: `(root / phase.output).exists()`).
**Existence ≠ completeness.** Real engagements accumulate mess the drive loop currently
sails straight past:

- A phase output is created but **empty or truncated** — an interrupted write leaves a
  zero-byte `scope.md`, or a fan-out crash leaves `opportunities/_index.md` present but
  half-written. The drive loop reads "done" and advances on garbage.
- An **index drifts from its item files** — a per-process Phase 5 fan-out wrote 2 of 5
  `OPP-NNN.md` bodies before crashing, or `_index.md` lists `OPP-007` whose body file was
  never written (or was hand-deleted). The index and the folder disagree.
- A `model/*.json` input is **malformed** (hand-edited to invalid JSON). The engine will
  fail opaquely later instead of being caught at resume.
- `model/results.json` is **absent while inputs exist** — the engine never ran, or the
  output was deleted. (The *changed-inputs* case — inputs edited after a clean run — is
  already owned by `state/staleness.py` and is **out of scope here**, to avoid redundant
  detection.)

These are exactly the "half-written files, manual edits, interrupted phases" the slice
calls out. Today none of them is detected; the Conductor trusts existence.

## 2. Goal

A **pure-Python integrity checker** that, given an engagement folder, returns a
deterministic, classified list of partial-state inconsistencies — each labelled
**auto-repairable** (deterministically re-derivable from sources) or **must-surface**
(needs human content). A Conductor section wires it into the drive loop so resume
**self-heals what is safely derivable and surfaces the rest** (the approved repair
stance), keeping every number's provenance intact (AC-3).

Non-goals: no new file formats; no LLM in the checker (it is a pure function of the
filesystem → testable, reproducible); no duplication of staleness (changed-inputs) or of
the `engine_root` reconcile (both already exist).

## 3. Design

### 3.1 New unit — `state/integrity.py`

Pure functions of the filesystem. No network, no subprocess, no mutation. Mirrors the
discipline of `state/state.py` and `state/staleness.py`.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Issue:
    kind: str      # machine id (see catalogue below)
    target: str    # repo-relative path or phase id the issue concerns
    repair: str    # "auto" | "surface"
    detail: str    # plain-language explanation, for Conductor narration

def check_integrity(root) -> list[Issue]:
    """Detect partial-state inconsistencies in an engagement folder.
    Pure; deterministic. Returns Issues sorted by (target, kind)."""
```

`check_integrity` **detects and classifies only — it never repairs.** Repair is performed
by the Conductor using primitives that already exist (`state/assembly.py` for indexes,
`engine/run.py` for results). This keeps the checker pure and avoids it importing or
shelling the engine.

### 3.2 Issue catalogue

Driven by `state/phases.py` (`PHASES`, `MODEL_INPUTS`) and the folder convention
(per-item phases: `processes/` `PROC-`, `opportunities/` `OPP-`, `scores/` `OPP-`,
`usecase-briefs/` `UC-`; gate folder `grc/` `OPP-`).

**Header-based vs field-based vs hand-assembled folders.** Phases 5/6 and the `grc/` gate
assemble their `_index.md` from each body's extraction header (`<!-- index: id=... -->`)
via `assembly.index_from_headers`, and their index tables carry **bare** ids (`OPP-001`);
their bodies are **header-based** and the index is rebuildable. Two folders are *not*:
- Phase 4 (`processes/`): `discovering-processes` builds its index from content-derived
  fields via `assembly.index_from_fields` (bodies carry `<!-- index: baseline=Ready -->`,
  *not* an `id=` header) — **field-based**.
- Phase 8 (`usecase-briefs/`): `packaging-usecases` **hand-assembles** its `_index.md` in
  main context — a rich 12-column table whose id cells are **markdown links**
  (`[UC-001](UC-001.md)`), which `index_from_headers` cannot reproduce. Treat it like
  `processes/`: header-based checks do not apply.

The header-dependent checks below (`malformed_item`, and the header-based auto-repair of
`index_orphan_items`) therefore apply **only to header-based folders**; running them on
`processes/` or `usecase-briefs/` would false-positive on valid files and, on repair,
overwrite a legitimate index with an empty-id or stripped-down table. To encode this
without hardcoding folder names in `integrity.py`, add a `header_based: bool` field to the
`Phase` dataclass (`True` for 5/6 and the grc gate; `False` for Phase 4, Phase 8, and all
non-folder phases); the checker reads it. Header-agnostic checks (`empty_output`,
`index_missing_item`, `bad_json`, `results_missing`) apply to all folders unchanged.

| kind | Trigger | repair | Repair path (Conductor) |
|---|---|---|---|
| `empty_output` | A `PHASES` output file exists but is empty / whitespace-only | `surface` | Re-drive that phase (its content is gone). |
| `index_orphan_items` | *(header-based folders only)* Body files exist but are absent from `_index.md` — **including the case where `_index.md` itself is absent** (bodies present, no index) — withheld for the folder if any body produced a `malformed_item` | `auto` | Rebuild index via `assembly.index_from_headers` from the body files. |
| `index_missing_item` | `_index.md` references an item id with no matching body file | `surface` | Re-drive that phase (the body content is gone). |
| `malformed_item` | *(header-based folders only)* A body file (`PREFIX-*.md`) is present but lacks a valid extraction header (`assembly._header_fields` → `{}`), whether or not it is indexed | `surface` | Re-drive that item (its header/content is incomplete). |
| `bad_json` | A present `model/<stem>.json` (stem ∈ `MODEL_INPUTS`) fails `json.loads` | `surface` | Ask the human for the correct value; re-record. |
| `results_missing` | ≥1 `model/*.json` input exists but `model/results.json` is absent | `auto` | Run `engine/run.py`, then `record_input_hashes`. |

**Deliberately not flagged** (already owned elsewhere, or out of scope by decision):
- changed model inputs after a clean run → `state/staleness.py`.
- corrupt/absent `.conductor.md` → `read_conductor` returns `{}` + drive-loop re-stamp /
  `reconcile_engine_root`.
- **orphan `_staging/` files** (a fan-out crash between the last subagent write and the
  merge) → *known gap, out of scope for this chunk.* Staging is transient infrastructure
  owned by the fan-out merge, not durable engagement state. Flagged here so the next
  developer knows it is a conscious exclusion, not an oversight; a later chunk may add a
  `stale_staging` (auto: run the merge from present staged files, then verify).
- **`processes/` (Phase 4) and `usecase-briefs/` (Phase 8) index drift** → *orphan
  auto-repair deferred.* Both are `header_based=False`, so they get the header-agnostic
  checks (`empty_output`, `index_missing_item`, `bad_json`) but **not** `malformed_item` or
  header-based `index_orphan_items`. `processes/` would need `index_from_fields` with a
  Phase-4-specific `extract` (parsing `## PROC-NNN — Name`); `usecase-briefs/` is
  hand-assembled with a rich linked-id table that no assembly primitive reproduces. A later
  chunk can add bespoke repair paths. Until then, a drift in either surfaces only via the
  phase reading "not done" in `state.state` and is re-driven — pre-existing behavior, not a
  regression.

Detection details:
- *empty/whitespace*: `path.read_text().strip() == ""`.
- *index drift*: glob the folder for `PREFIX-*.md` body files (excluding `_index.md`) into
  a set. If `_index.md` exists, parse its id column into a set — **reuse the exact
  header/separator-skip heuristic of `state.state._count_non_green_grc`** (skip a `|`-row
  whose first cell lower-cases to the column header or is empty/`-`-only) so the two
  parsers never disagree. If `_index.md` is absent, the indexed set is empty.
  - indexed-ids with no body file → `index_missing_item` (surface). *(All folders.)*
  - **header-based folders only** (`phase.header_based`):
    - any body file (orphan or indexed) with `_header_fields(text) == {}` →
      `malformed_item` (surface).
    - body-ids not in the indexed set → `index_orphan_items` (auto), **withheld** for the
      folder if any body produced a `malformed_item` above (we never auto-rebuild an
      empty-id row).
  - **field-based folders** (`processes/`): only `index_missing_item` applies here; orphan
    and header checks are skipped (see "Deliberately not flagged").
  - More than one of these can fire for one folder.
- *bad_json*: attempt `json.loads(path.read_text())`; `JSONDecodeError` → `bad_json`.
- *results_missing*: ≥1 `MODEL_INPUTS` stem file present **and** `model/results.json`
  absent. **Partial inputs are safe to auto-repair:** the engine is designed to run after
  every model-writing phase and renders absent inputs as `PENDING`
  (`engine/model.py` `load_inputs` — "Missing files load as empty"), so re-running against
  whatever inputs exist reproduces exactly the incremental state the drive loop would have
  produced. No all-inputs-present guard is needed or wanted (that would suppress the
  legitimate after-Phase-4-only case).

`check_integrity` does not catch or wrap I/O exceptions — an unexpected `OSError`
mid-scan propagates, matching `state.state`'s behavior (a broken filesystem is not a
partial-state issue to classify).

Ordering: results sorted by `(target, kind)` so output is stable across runs and
filesystems (no mtime, matching the staleness rationale).

### 3.3 CLI entry

`python3 <engine_root>/state/integrity.py <folder>` prints the Issue list as JSON
(same invocation shape as `state/state.py`), so the Conductor reads it by absolute path
with no third-party deps. Exit `0` always when the folder is valid (issues are data, not
errors); exit `2` if the path is not a directory (mirrors `state.state.main`).

### 3.4 Conductor wiring — drive-loop step 1

A new subsection of `skills/conducting-engagement/SKILL.md`, **"Resuming into a messy
state,"** invoked as part of drive-loop step 1 (read state), **before** staleness (step 3)
and step-selection (step 4):

1. Run `state/integrity.py <folder>`.
2. **Auto-repair** every `repair: "auto"` issue silently, using the existing primitive
   (`index_from_headers` for `index_orphan_items`; `engine/run.py` + `record_input_hashes`
   for `results_missing`). These are deterministic re-derivations from sources — no human
   input, fully reproducible, so no confirmation needed.
3. **Surface** every `repair: "surface"` issue as a single batched **must-ask** in plain
   language (no file/phase names leaked): name what looks incomplete and that you need to
   re-do that part with them. Do not advance past a `surface` issue.
4. Re-run integrity after auto-repairs and assert **only `surface` issues remain** — this
   catches both an auto issue that failed to clear and any new issue an auto-repair
   introduced (e.g. a rebuilt index that still leaves `results_missing` because inputs are
   partial — itself auto, so it repairs on the second pass). If any `auto` issue persists
   after a second pass, surface it rather than looping.

Narration block (jargon-free), fenced for the guard like the existing narration blocks:

```
<!-- resume-recovery-narration:start -->
> Picking up where we left off. A couple of things look half-finished from last time —
> I've tidied up what I could re-build automatically. One part (the team's process notes)
> didn't get saved completely; let's redo that quickly together before we go on.
<!-- resume-recovery-narration:end -->
```

## 4. Files

- **Modify** `state/phases.py` — add a `header_based: bool` field to **both** `Phase` and
  `Gate` (the grc folder is a `Gate`). `True` for phases 5/6/8 and the grc gate; `False`
  for Phase 4 and all non-folder phases (the flag is only consulted for folder-bearing
  entries, so its value is irrelevant for `scope.md`-style phases — default it `False`).
  Update existing constructions; run the suite to confirm `state.state` (which reads these
  by attribute) is unaffected.
- **Create** `state/integrity.py` — `Issue`, `check_integrity`, `main` (CLI).
- **Create** `state/tests/test_integrity.py` — unit tests for every `kind` and the
  classification, plus the CLI exit codes and deterministic ordering.
- **Modify** `skills/conducting-engagement/SKILL.md` — add the "Resuming into a messy
  state" subsection + narration block; reference it from drive-loop step 1.
- **Modify** `tests/test_conductor_skill.py` — static string-presence guards for the new
  section (section present, references integrity, distinguishes auto vs surface, narration
  block fenced, wired before staleness/step-4).

## 5. Testing strategy

- **`state/tests/test_integrity.py`** (the trust core): build tiny engagement folders in
  `tmp_path`, assert the exact `Issue` set per scenario — clean folder → `[]`; empty
  `scope.md` → one `empty_output`; orphan `OPP-003.md` (valid header) not in index →
  `index_orphan_items` (auto); **`_index.md` absent but `OPP-001..003.md` present (valid
  headers) → `index_orphan_items` (auto)**; index lists `OPP-009` with no file →
  `index_missing_item` (surface); **a body file with no extraction header → `malformed_item`
  (surface), and the orphan issue for that folder is withheld**; malformed
  `model/value.json` → `bad_json`; **only `baselines.json` present + no `results.json` →
  `results_missing` (auto), i.e. partial inputs still fire**; a folder with several issues
  → sorted, complete set. Plus: CLI prints JSON & exit 0; non-dir → exit 2; deferral — a
  *changed* (not absent) input produces **no** integrity issue (staleness owns it); a
  clean fully-complete engagement with `results.json` → `[]`. **Field-based folder: a
  `processes/PROC-002.md` with no `id=` header (valid Phase 4 state) produces no
  `malformed_item` and no `index_orphan_items`** (header checks skipped for
  `header_based=False`); but a `processes/` index referencing a `PROC` with no body file
  still yields `index_missing_item`.
- **`tests/test_conductor_skill.py`**: static guards over the new SKILL.md section using
  the existing `_section`/`methodology` fixture convention.
- Full suite (`.venv/bin/python -m pytest`) stays green.

## 6. Reconciliation (checked against existing machinery)

- **No redundancy with `staleness.py`**: integrity flags only *absent* results, never
  *changed* inputs — that boundary is explicit in the catalogue.
- **No redundancy with `conductor_state` reconcile**: `.conductor.md` health is already
  self-healed; integrity does not touch it.
- **Reuses `assembly.index_from_headers`** for index repair rather than re-deriving — same
  primitive the fan-out merge uses, so a rebuilt index is byte-identical to a freshly
  assembled one.
- **Matches existing CLI/purity conventions** of `state/state.py` and `state/staleness.py`
  (pure function + thin `main`, JSON out, absolute-path invocation).
