# Current-State Process Validation Checkpoint — Design

**Issue:** #136 · **Date:** 2026-06-26 · **Status:** approved (brainstorming)

## Problem

The methodology produces detailed current-state process maps in Phase 4 — stored in
`processes/PROC-NNN.md` with Trigger, numbered Steps, Actors, Decision points, Exceptions,
and Upstream/downstream. **None of that step-by-step detail is ever client-facing.** The only
post-Phase-4 client artifact is Checkpoint 2 (`baseline`), a one-line-per-process summary of
names + baseline numbers (`section-renderer-checkpoint-baseline` emits "one row per process").

In a real engagement, the **process owners** must review the step-by-step capture of *their*
process and sign off that it is accurate before the engagement builds value hypotheses on top
of it. That review does not exist today. This is the foundational client sign-off that
everything downstream depends on.

## Goal

Add an interim, **process-owner-facing** checkpoint after Phase 4 that renders each in-scope
process's full step-by-step current-state map as an editable **Word (.docx)** document for
that owner to confirm and finalize, and **hard-gate** Phase 5 on per-process sign-off.

## Non-goals

- Not changing Checkpoint 2 (`baseline`) — it stays the sponsor-facing numbers summary.
- Not converting the existing 3 checkpoints to Word — that is #131, which reuses the generator
  this design builds.
- No new analytical content — the renderer copies from `PROC-NNN.md` verbatim (the
  no-fabrication invariant all checkpoints share).
- Not full brand parity in Word — minimal OSL styling (heading color + DM Sans) is enough;
  the artifact's job is to be reviewed/commented, not to be pixel-matched to the HTML brand.

## Architecture

Four components, each independently testable:

### 1. `state/docx.py` — stdlib-only `.docx` generator

A pure-stdlib module that builds a valid `.docx` (Office Open XML / WordprocessingML) from a
small structured document model, using `zipfile` + string-templated XML. No third-party deps,
so it runs in any sandbox (preserves the stdlib-only core invariant).

**Document model (input):** an ordered list of block elements:
- `heading(level, text)` — 1–3, mapped to Word heading styles.
- `paragraph(text)` — body text.
- `numbered_list(items)` / `bullet_list(items)`.
- `table(headers, rows)`.
- `signoff(fields)` — a labeled block (renders as a small table / labeled paragraphs).

**Output (.docx zip parts):**
- `[Content_Types].xml`
- `_rels/.rels`
- `word/_rels/document.xml.rels`
- `word/styles.xml` — minimal: Normal (DM Sans), Heading1–3 (DM Sans, OSL blue `#1B75BC`),
  list/table basics.
- `word/document.xml` — the body built from the document model.

**API (consumed by later tasks):**
```python
# state/docx.py
def build_docx(blocks: list[dict], out_path: str) -> str:
    """Write a .docx at out_path from an ordered list of block dicts; return out_path.
    Each block: {"type": "heading"|"paragraph"|"numbered_list"|"bullet_list"|"table"|"signoff", ...}.
    XML text is escaped; the produced file is a valid zip with the required OOXML parts."""
```
Helper builders (`heading()`, `paragraph()`, …) return the block dicts, so callers compose a
list and call `build_docx`.

**Determinism:** no timestamps in the parts that vary run-to-run (OOXML core props omitted or
fixed), so the same input yields a byte-stable zip — testable and golden-able.

### 2. `state/process_review.py` — PROC → document-model transform

A pure function that reads a `PROC-NNN.md` (and the process's baseline row from
`model/baselines.json`) and returns the ordered block list for that process's owner review.
Pure data transform, no I/O beyond reading the named source files; no fabrication — every
block traces to a parsed field of the source.

**Owner-facing content (included):** process id + name (heading), Trigger, Steps (numbered,
**stripped of the internal Red/Yellow color notes** — owner sees the clean step text), Actors,
Decision points, Exceptions, Upstream/downstream, a read-only **Baseline figures** table
(Volume, Cycle time, Error/exception rate, FTE effort) as context, and a **Sign-off block**
(Process owner, Outcome: Confirmed / Changes requested, Comments).

**Excluded (internal analysis):** per-step color annotations, Challenge hypothesis, Chain
scan, Conflicts reconciliation prose. These are our judgments, not what the owner validates.

### 3. `process-validation` checkpoint — wired into `building-checkpoint`

Add a `process-validation` row to the Checkpoint Registry and a renderer path. Unlike the
existing checkpoints (one HTML artifact via an LLM section-renderer agent), this checkpoint is
**deterministic and per-process**: `building-checkpoint`, for checkpoint id
`process-validation`, iterates every in-scope process and calls
`state/process_review.py` + `state/docx.py` to write
`checkpoints/process-validation/PROC-NNN.docx` — one per process. No LLM section-renderer
needed (the content is a faithful transform, not synthesis), which also removes a fabrication
surface.

**Registry row:**
| field | value |
|---|---|
| id | `process-validation` |
| Insert after | Phase 4 |
| Audience | Process owner (one per process) |
| Source files | `processes/PROC-NNN.md` (each), `model/baselines.json` |
| Output | `checkpoints/process-validation/PROC-NNN.docx` (one per process) |
| Outcome record | `checkpoints/process-validation/CP-PROC-NNN-outcome.md` (one per process) |
| Route-back | Phase 4 (`discovering-processes`) for the affected process |

Sequences **before** CP2 `baseline` after Phase 4 (confirm the steps, then the numbers).

### 4. Hard gate in the Conductor drive loop

`conducting-engagement` gains a convergence gate: **before entering Phase 5**, every in-scope
process in `processes/_index.md` must have a `CP-PROC-NNN-outcome.md` recording **Confirmed**
(or an explicit **Waived** with a reason — operator decision, recorded, must-ask). A process
marked **Changes requested** routes back to Phase 4 for that process, re-runs the engine, and
regenerates only that process's `.docx`. The gate is reported via `state.py` (a new
`gates` entry, mirroring how the GRC gate is surfaced) so the Conductor blocks deterministically.

The keystone (`using-methodology`) and the Conductor narrate this jargon-free ("let's get each
team lead to confirm we captured their process correctly before we build on it").

## Data flow

```
Phase 4 → processes/PROC-NNN.md + model/baselines.json
   → building-checkpoint(process-validation)
       → for each PROC: process_review.py (PROC + baseline → blocks) → docx.py → PROC-NNN.docx
   → owner reviews .docx, returns outcome → CP-PROC-NNN-outcome.md (Confirmed/Changes/Waived)
   → drive-loop gate: all Confirmed/Waived? → Phase 5 ; any Changes → Phase 4 (that PROC) → re-run → regenerate
```

## Testing

- `state/docx.py`: produced file is a valid zip containing the required OOXML parts; opens as a
  WordprocessingML document (parse `word/document.xml`); text is XML-escaped; byte-stable for
  fixed input (golden); headings/lists/tables/signoff render to the expected `<w:p>`/`<w:tbl>`.
- `state/process_review.py`: maps a fixture `PROC-NNN.md` to the expected block list; includes
  owner-facing fields; **excludes** challenge hypothesis / chain scan / color notes; baseline
  table populated from `model/baselines.json`; no content absent from the source.
- Checkpoint wiring (`tests/`): registry has `process-validation`; building-checkpoint emits one
  `.docx` + one outcome stub per in-scope process under `checkpoints/process-validation/`.
- Gate (`tests/test_guards.py` + state tests): `state.py` reports the process-validation gate;
  Phase 5 is blocked while any in-scope process lacks Confirmed/Waived; Changes-requested routes
  back to Phase 4.
- Anti-regression guard: the owner `.docx` content must not contain the excluded internal-analysis
  markers (challenge hypothesis / chain scan).

## Open questions

None blocking. (Confirmed in brainstorming: exclude internal analysis; include baseline figures
as read-only context; id `process-validation`.)
