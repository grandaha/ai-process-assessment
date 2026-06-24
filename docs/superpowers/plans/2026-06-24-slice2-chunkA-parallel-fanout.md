# Slice 2 · Chunk A — Parallel per-process Phase 5 fan-out — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move per-process Phase 5 (opportunity identification) fan-out ownership to the conductor — concurrent when ≥2 processes are ready, degrading to sequential — reusing the existing `state/assembly.py` merge, with jargon-free narration and per-process failure handling.

**Architecture:** This is a **methodology-prose change**, not application code. The conductor (`skills/conducting-engagement/SKILL.md`) gains a "Parallel per-process fan-out" section that dispatches one single-process-scoped `identifying-opportunities` subagent per process from main context and then merges their staging via the *already-merged* `renumber_sequential`. The Phase 5 skill (`skills/identifying-opportunities/SKILL.md`) gains an explicit single-process mode (stage only, don't assemble). Behavior is guarded by **static string-presence tests** over the skill prose (the repo's established guard pattern — see `tests/test_guards.py`, `tests/test_conductor_skill.py`, `tests/test_onboarding.py`).

**Tech Stack:** Markdown skill prose; Python static-guard tests (pytest); `state/assembly.py` (reused, unchanged).

## Global Constraints

- **Zero new `state/` code.** Reuse `state/assembly.py` `renumber_sequential` / `index_from_headers` / `collect_staged` / `cleanup`. The originally-proposed `state/opportunity_merge.py` is **not** built (redundant post-#100).
- **No engine/math change.** Golden `results.json` is untouched; no arithmetic added anywhere.
- **Off-limits files (verbatim-sync guard):** do **not** edit `skills/using-methodology/SKILL.md` or any `system-prompt.md`.
- **Determinism invariant:** global `OPP-NNN` ids are assigned in `processes/_index.md` order (= staged-file sort order `proc-001`, `proc-002`, …); concurrent and sequential fan-out must yield byte-identical `opportunities/`.
- **Jargon-free narration:** the user-facing narration block must contain none of: `subagent`, `Phase 1`…`Phase 11`, `OPP-`, `_staging`, `renumber`.
- **CHANGELOG:** add one entry under `## [Unreleased]` in `CHANGELOG.md`; **no version bump** (accumulates toward `v2.19.0`).
- **Test command (everywhere below):** `.venv/bin/python -m pytest` (the venv uses Python 3.13; system 3.14 lacks working pip/pytest). Baseline before starting: **268 passed**.
- **Branch:** `feat/slice2-chunkA-parallel-fanout` (already created off `main`).
- **Commits:** end each commit message with the project trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## File Structure

- `skills/identifying-opportunities/SKILL.md` — **modify**: add a two-mode preamble to the `## Subagent Dispatch` section (single-process vs. whole-portfolio). Existing whole-portfolio dispatch + assembly stays.
- `skills/conducting-engagement/SKILL.md` — **modify**: add a new `## Parallel per-process fan-out (Phase 5)` section; update the execution-model "Headless phases" bullet to special-case Phase 5.
- `tests/test_guards.py` — **modify**: add the single-process-mode guard (near the existing `test_phase5_assembly_uses_portable_layer`).
- `tests/test_conductor_skill.py` — **modify**: add `## Parallel per-process fan-out` to `REQUIRED_HEADINGS`; add a local `_section` helper and three guards (fan-out core, degradation+failure, jargon-free narration).
- `CHANGELOG.md` — **modify**: one bullet under `## [Unreleased]`.

---

## Task 1: Phase 5 skill — explicit single-process-scoped mode

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md` (the `## Subagent Dispatch` section, currently starting at line 57)
- Test: `tests/test_guards.py` (append after `test_phase5_assembly_uses_portable_layer`, ~line 454)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: the staging contract the conductor relies on in Task 2 — a single-process invocation writes only `<engagement-folder>/_staging/phase5/proc-<process-id>.md` with `## TEMP-` ids, returns a one-line summary, and does **not** assemble.

- [ ] **Step 1: Write the failing test**

In `tests/test_guards.py`, after the `test_phase5_assembly_uses_portable_layer` function:

```python
def test_phase5_supports_single_process_scope(methodology):
    """Conductor-driven fan-out invokes Phase 5 one process at a time: stage only,
    no assemble. (Slice 2 Chunk A.)"""
    body = methodology.skills["ai-process-assessment:identifying-opportunities"].body
    assert "Single-process" in body
    assert "scoped to a single" in body
    assert "do not assemble" in body
    # The whole-portfolio assembly path must still exist for direct/N=1 invocation.
    assert "renumber_sequential" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase5_supports_single_process_scope -v`
Expected: FAIL (`assert "Single-process" in body` — the tokens aren't in the skill yet).

- [ ] **Step 3: Edit the skill prose**

In `skills/identifying-opportunities/SKILL.md`, insert this block immediately after the `## Subagent Dispatch` heading (line 57) and before the existing "Per-process opportunity identification is offloaded…" paragraph:

```markdown
**Invocation modes.** This skill runs in one of two modes:

- **Single-process (conductor-driven fan-out).** When the conductor invokes this skill
  scoped to a single `PROC-NNN`, act as the typer for that one process: read only its
  `processes/PROC-NNN.md` (and the relevant `tech-inventory.md` sections), write only that
  process's opportunities to `<engagement-folder>/_staging/phase5/proc-<process-id>.md` with
  provisional `## TEMP-` ids, return the one-line summary, and **do not assemble** — the
  conductor merges every process's staging into the canonical `opportunities/`.
- **Whole-portfolio (direct invocation or a single-process engagement).** Dispatch the
  per-process batch and assemble, exactly as described below.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase5_supports_single_process_scope -v`
Expected: PASS.

- [ ] **Step 5: Run the phase-5 guard neighbours to confirm no regression**

Run: `.venv/bin/python -m pytest tests/test_guards.py -q`
Expected: PASS (all guards, including `test_phase5_assembly_uses_portable_layer`).

- [ ] **Step 6: Commit**

```bash
git add skills/identifying-opportunities/SKILL.md tests/test_guards.py
git commit -m "feat(phase5): explicit single-process-scoped dispatch mode

Conductor-driven fan-out invokes opportunity identification one process at a
time (stage only, no assemble); whole-portfolio path retained for direct/N=1.
Part of #87 (Slice 2 Chunk A).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Conductor — own the per-process fan-out (trigger + dispatch + merge + chain-detection)

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (add new section; update execution-model bullet at line 155)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the single-process staging contract from Task 1.
- Produces: a `## Parallel per-process fan-out (Phase 5)` section and a `_section(text, header)` test helper that Tasks 3 and 4 reuse.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, add `"## Parallel per-process fan-out"` to the `REQUIRED_HEADINGS` list, then append this helper and test at the end of the file:

```python
def _section(text: str, header: str) -> str:
    start = text.find(header)
    assert start != -1, f"missing section: {header!r}"
    nxt = text.find("\n## ", start + len(header))
    return text[start: nxt if nxt != -1 else len(text)]


def test_conductor_owns_phase5_fanout():
    sec = _section(SKILL.read_text(), "## Parallel per-process fan-out")
    # Trigger: two or more processes with ready baselines.
    assert "≥2" in sec
    assert "Baseline = Ready" in sec
    # Conductor dispatches one subagent per process (not a single headless Phase 5).
    assert "one subagent per process" in sec
    # Merge reuses the portable assembly layer, in process order.
    assert "from state.assembly import" in sec
    assert "renumber_sequential" in sec
    # Cross-process chain-detection runs after the merge.
    assert "chain-detection" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — both `test_skill_has_all_load_bearing_sections` (new required heading missing) and `test_conductor_owns_phase5_fanout` (section absent).

- [ ] **Step 3: Add the new section to the conductor skill**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **after** the `## Execution model — who talks to the human (§4.4)` section and **before** `## Touchpoint taxonomy`:

```markdown
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
```

- [ ] **Step 4: Update the execution-model bullet to special-case Phase 5**

In `skills/conducting-engagement/SKILL.md` line 155, change the "Headless phases" bullet to point Phase 5 at the new section. Replace:

```markdown
- **Headless phases you dispatch to a subagent:** Phases 2, 3, 5, 6, 7, 9, 10, 11, the
```

with:

```markdown
- **Headless phases you dispatch to a subagent:** Phases 2, 3, 6, 7, 9, 10, 11, the
```

and append, as a new bullet immediately after that bullet's existing text (after "…re-read state."):

```markdown
- **Phase 5 (opportunity identification) is special:** with ≥2 ready processes you own a
  per-process fan-out rather than a single headless dispatch — see *Parallel per-process
  fan-out (Phase 5)*. With one process it runs once, whole-portfolio.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: PASS (all conductor guards, incl. the new heading and `test_conductor_owns_phase5_fanout`).

- [ ] **Step 6: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): own per-process Phase 5 fan-out + portable merge

Conductor dispatches one single-process opportunity-identification subagent per
process (>=2 ready), then merges via state.assembly renumber_sequential in
process order, then runs cross-process chain-detection. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Conductor — degradation + per-process failure handling

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (extend the fan-out section from Task 2)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Parallel per-process fan-out` section and `_section` helper from Task 2.
- Produces: degradation + failure rules within that section.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_fanout_degradation_and_failure():
    sec = _section(SKILL.read_text(), "## Parallel per-process fan-out")
    # Cross-surface degradation: same per-process work, run sequentially, identical result.
    assert "Degradation" in sec
    assert "sequentially" in sec
    # Per-process failure: re-dispatch only the failed process; merge waits for the full set.
    assert "re-dispatch only that process" in sec
    assert "do not merge until the full set is staged" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_fanout_degradation_and_failure -v`
Expected: FAIL (`assert "Degradation" in sec`).

- [ ] **Step 3: Extend the fan-out section**

In `skills/conducting-engagement/SKILL.md`, inside the `## Parallel per-process fan-out (Phase 5)` section, insert these two bullets **immediately before** the final `N<2 → run Phase 5 once…` line:

```markdown
- **Degradation:** on a surface without concurrent dispatch, run the same per-process
  invocations **sequentially** into the same staging layout — same merge, same ids, identical
  result. Fan-out is an optimization; the sequential path is the invariant.
- **Failure:** if one process's subagent fails, **re-dispatch only that process**; retain the
  others' staged outputs; **do not merge until the full set is staged** (convergence already
  demands every in-scope process). A merge error → stop, surface (must-ask), never advance on a
  failed merge.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_fanout_degradation_and_failure -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): fan-out degradation-to-sequential + per-process failure

On surfaces without concurrent dispatch, run per-process Phase 5 sequentially
(identical result). On a single subagent failure, re-dispatch only that process
and hold the merge until the full set is staged. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Conductor — jargon-free fan-out narration

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (add narration block to the fan-out section)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Parallel per-process fan-out` section from Task 2.
- Produces: a delimited `<!-- fanout-narration:start --> … <!-- fanout-narration:end -->` block guarded for jargon (mirrors the §3.B greeting guard in `tests/test_onboarding.py`).

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, append:

```python
def test_fanout_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- fanout-narration:start -->")
    end = text.find("<!-- fanout-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "fan-out narration must be wrapped in <!-- fanout-narration:start --> ... :end -->"
    narration = text[start:end]
    forbidden = ["subagent", "OPP-", "_staging", "renumber"] + [f"Phase {n}" for n in range(1, 12)]
    for token in forbidden:
        assert token not in narration, f"narration leaks methodology jargon: {token!r}"
    # It states the 'whole board at once' promise in plain language.
    assert "together" in narration.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_fanout_narration_is_jargon_free -v`
Expected: FAIL (markers not found).

- [ ] **Step 3: Add the narration block**

In `skills/conducting-engagement/SKILL.md`, at the **end** of the `## Parallel per-process fan-out (Phase 5)` section (after the `N<2 → …` line), add:

```markdown
When you begin the fan-out, narrate it in plain language — no step names, file names, or
internal ids:

<!-- fanout-narration:start -->
> I've mapped all your processes — now I'm finding opportunities across them together, so I
> can catch the wins that only show up when the whole picture is in view.
<!-- fanout-narration:end -->
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_fanout_narration_is_jargon_free -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): jargon-free fan-out narration block

Plain-language 'looking at the whole board at once' line, guarded free of
subagent/Phase/OPP/_staging tokens (mirrors the onboarding greeting guard).
Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: CHANGELOG + full-suite verification

**Files:**
- Modify: `CHANGELOG.md` (under `## [Unreleased]`, line 8)

**Interfaces:**
- Consumes: all prior tasks.
- Produces: the release note; final green suite.

- [ ] **Step 1: Add the CHANGELOG entry**

In `CHANGELOG.md`, under `## [Unreleased]` (line 8), add:

```markdown
### Added
- **Parallel per-process opportunity identification (Slice 2 Chunk A, #87).** On a
  multi-process engagement the conductor now finds opportunities across all processes
  concurrently — one per-process pass each, merged in process order into a single
  byte-identical result — including cross-process automation chains. Degrades to sequential
  where concurrent dispatch is unavailable; a single process's failure re-runs only that
  process. No engine/math change; reuses the portable assembly layer.
```

(If an `### Added` subsection already exists under `[Unreleased]`, add the bullet there instead of creating a second one.)

- [ ] **Step 2: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — **272 passed** (268 baseline + 4 new guards).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): Slice 2 Chunk A — parallel per-process fan-out (#87)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Push**

```bash
git push
```

The branch already has an open PR (#102). The auto-review gate will **HOLD** this (methodology-markdown + CHANGELOG touch, no wired Python helper) — expected; **merge by hand with a decision comment** once review is clean, mirroring #101.

---

## Self-Review

**1. Spec coverage** (against `2026-06-24-slice2-chunkA-parallel-fanout-reconciled.md`):
- §3 single-process mode → Task 1. §4.1 conductor dispatch + merge → Task 2. §4.2 determinism → reused `renumber_sequential` (asserted in Task 2 guard). §4.3 Phase 5 skill mode → Task 1. §5 trigger → Task 2; degradation + failure → Task 3. §6 narration → Task 4. §8 guards 1–4 → Tasks 2/1/3/4; guard 5 (determinism) → existing `renumber_sequential` tests (no new code). §9 files → all covered. §10 known limitation → no action (no regression). §11 merge note → Task 5 Step 4.
- **No-new-`state/`-code constraint:** honored — no task creates `state/opportunity_merge.py`.

**2. Placeholder scan:** none — every step shows the exact prose/test content and exact commands with expected output.

**3. Type/token consistency:** guard tokens match the prose verbatim — `"Single-process"`, `"scoped to a single"`, `"do not assemble"` (Task 1); `"≥2"`, `"Baseline = Ready"`, `"one subagent per process"`, `"from state.assembly import"`, `"renumber_sequential"`, `"chain-detection"` (Task 2); `"Degradation"`, `"sequentially"`, `"re-dispatch only that process"`, `"do not merge until the full set is staged"` (Task 3); narration markers + forbidden-token list (Task 4). The narration block contains no forbidden token (`together`, `processes`, `picture` only).
