# Slice 2 · Chunk B — Edit & interruption splicing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user correct anything in plain language at any point; the conductor classifies the correction, routes it to an audited mechanism, re-runs the pipeline, and reports the deterministic delta.

**Architecture:** One new deterministic helper (`state/results_diff.py`) computes the before/after delta of `results.json`; everything else is conductor prose (a new `## Edit & interruption splicing` section) riding on already-built machinery (staleness re-drive, decision log, Chunk-A fan-out). Behavior is guarded by static string-presence tests over the skill prose (repo convention) plus unit tests for the helper.

**Tech Stack:** Python (stdlib only) for the helper + pytest; Markdown skill prose; static-guard tests.

## Global Constraints

- **Only one new code unit:** `state/results_diff.py`. No other `state/` or `engine/` code changes — `staleness.py`, `overrides.py`, `assembly.py`, `conductor_state.py`, and the engine are reused as-is.
- **No engine/math change.** `diff_results` does comparison only (no arithmetic); golden `results.json` untouched.
- **Off-limits (verbatim-sync):** do NOT edit `skills/using-methodology/SKILL.md` or any `system-prompt.md`.
- **Routing through owning artifacts only** — the conductor never free-edits arbitrary files; the three routes are model-input edit / owning-phase re-run / reopen human-only must-ask.
- **Decision-log enum (verbatim):** `decided_by: agent-auto | human-ratified | human-overrode`; `disposition: accepted | edited | overridden→<X> | invalidated-by-{…}`. AI-draft correction → `human-overrode` / `overridden→<X>`; fresh user fact → `human-ratified` / `edited`. Entries append-only.
- **Terminology:** "override" = the decision-log sense only; do NOT touch the CLAUDE.md-override machinery (`state/overrides.py`).
- **Autonomy:** act-then-show governs applying the *explicitly stated* correction; downstream re-opened ratifications follow the EXISTING touchpoint taxonomy + autonomy preset; autonomous batching stays Chunk C (do not add batching here).
- **Jargon-free narration:** the delta-narration block must contain none of: `OPP-`, `model/`, `_staging`, `renumber`, `Phase 1`…`Phase 11`.
- **Test command:** `.venv/bin/python -m pytest` (Python 3.13 venv; system 3.14 lacks pytest). **Baseline on this branch: 272 passed.** Final target: **282 passed** (272 + 6 helper tests + 4 conductor guards).
- **Branch:** `feat/slice2-chunkB-edit-splicing` (already created off `main` @ f3d7e9a).
- **Commits:** end every commit message with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## File Structure

- `state/results_diff.py` — **new**: `diff_results(before, after) -> list[Change]`, a deterministic recursive `results.json` delta. Single responsibility: structural comparison.
- `state/tests/test_results_diff.py` — **new**: unit tests for the helper.
- `skills/conducting-engagement/SKILL.md` — **modify**: add `## Edit & interruption splicing` section (intake + routes, confirm gate, both-parties logging, delta-narration block).
- `tests/test_conductor_skill.py` — **modify**: add `## Edit & interruption splicing` to `REQUIRED_HEADINGS`; add 4 guards (reusing the existing `_section` helper from Chunk A).
- `CHANGELOG.md` — **modify**: one entry under `## [Unreleased]`.

---

## Task 1: `state/results_diff.py` — deterministic delta helper

**Files:**
- Create: `state/results_diff.py`
- Test: `state/tests/test_results_diff.py`

**Interfaces:**
- Produces: `MISSING` (a module-level sentinel for an absent key); `Change` (frozen dataclass with fields `path: str`, `before`, `after`); `diff_results(before: dict, after: dict) -> list[Change]` — returns changes sorted by `path`. Dicts are recursed (dotted paths); every other value (scalars, lists) is compared as a leaf. Added key → `before is MISSING`; removed key → `after is MISSING`.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_results_diff.py`:

```python
"""Unit tests for the deterministic results delta (state/results_diff.py)."""
from state.results_diff import MISSING, Change, diff_results


def test_identical_inputs_yield_no_changes():
    a = {"value": {"OPP-001": {"low": 700000, "high": 1050000}}}
    assert diff_results(a, dict(a)) == []


def test_nested_numeric_change_detected():
    before = {"value": {"OPP-001": {"low": 700000}}}
    after = {"value": {"OPP-001": {"low": 800000}}}
    assert diff_results(before, after) == [
        Change(path="value.OPP-001.low", before=700000, after=800000)
    ]


def test_added_key_uses_missing_sentinel_for_before():
    before = {"costs": {}}
    after = {"costs": {"OPP-002": 5000}}
    assert diff_results(before, after) == [
        Change(path="costs.OPP-002", before=MISSING, after=5000)
    ]


def test_removed_key_uses_missing_sentinel_for_after():
    before = {"costs": {"OPP-002": 5000}}
    after = {"costs": {}}
    assert diff_results(before, after) == [
        Change(path="costs.OPP-002", before=5000, after=MISSING)
    ]


def test_list_value_compared_as_leaf():
    # roadmap order is a list — a reorder is one whole-list change, not per-element.
    before = {"roadmap": ["OPP-001", "OPP-002"]}
    after = {"roadmap": ["OPP-002", "OPP-001"]}
    assert diff_results(before, after) == [
        Change(path="roadmap", before=["OPP-001", "OPP-002"], after=["OPP-002", "OPP-001"])
    ]


def test_result_is_sorted_by_path_regardless_of_insertion_order():
    before = {"b": 1, "a": 1}
    after = {"b": 2, "a": 2}
    # Insertion order is b, a — but output must be sorted by path: a, then b.
    assert [c.path for c in diff_results(before, after)] == ["a", "b"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_results_diff.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.results_diff'`.

- [ ] **Step 3: Write the implementation**

Create `state/results_diff.py`:

```python
"""Deterministic structural delta over two ``results.json`` snapshots.

Pure comparison — no arithmetic (every number was already produced by the
engine). Dicts are recursed into dotted paths; every other value (scalars and
lists) is compared as a single leaf, so a reordered list is reported as one
whole-list change. Output is sorted by path, so the same inputs always yield
the same change list regardless of dict insertion order. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass


class _Missing:
    """Sentinel for a key absent on one side of the diff."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "MISSING"


MISSING = _Missing()


@dataclass(frozen=True)
class Change:
    path: str
    before: object
    after: object


def _walk(before, after, prefix, out):
    if isinstance(before, dict) and isinstance(after, dict):
        for key in set(before) | set(after):
            path = f"{prefix}.{key}" if prefix else str(key)
            _walk(before.get(key, MISSING), after.get(key, MISSING), path, out)
        return
    if before != after:
        out.append(Change(path=prefix, before=before, after=after))


def diff_results(before: dict, after: dict) -> list[Change]:
    """Return the changed leaves between two ``results.json`` structures,
    sorted by path. Added key → ``before is MISSING``; removed → ``after is
    MISSING``."""
    out: list[Change] = []
    _walk(before, after, "", out)
    return sorted(out, key=lambda c: c.path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest state/tests/test_results_diff.py -v`
Expected: PASS (6 passed).

Note on `MISSING` equality: a `_Missing` instance compares unequal to any real value via the default object identity, so `before != after` correctly fires for added/removed keys, and `MISSING != MISSING` is False (same singleton) so an absent-on-both branch never occurs (the key wouldn't be in the union).

- [ ] **Step 5: Commit**

```bash
git add state/results_diff.py state/tests/test_results_diff.py
git commit -m "feat(state): deterministic results.json delta helper

diff_results(before, after) -> sorted [Change]; recurses dicts to dotted
paths, compares lists/scalars as leaves, MISSING sentinel for added/removed.
No arithmetic. Backs the Chunk B edit delta report. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Conductor — `## Edit & interruption splicing` section (intake + routes + delta hookup)

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (add new section after the `## Staleness` section)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: `state.results_diff.diff_results` (Task 1); the existing `_section(text, header)` helper in `tests/test_conductor_skill.py` (added in Chunk A).
- Produces: the `## Edit & interruption splicing` section that Tasks 3 and 4 extend.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, add `"## Edit & interruption splicing"` to the `REQUIRED_HEADINGS` list, then append:

```python
def test_conductor_edit_splicing_intake_and_routes():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # Universal plain-language intake, handled at the drive-loop boundary.
    assert "plain language" in sec
    assert "drive-loop boundary" in sec
    # Three routes.
    assert "model/*.json" in sec          # numeric route
    assert "re-run the owning phase" in sec  # structural route
    assert "single-process mode" in sec      # structural re-type reuses Chunk A
    assert "re-open that must-ask" in sec     # human-only route
    # Delta report hookup to the Task 1 helper.
    assert "state.results_diff" in sec
    assert "diff_results" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — `test_skill_has_all_load_bearing_sections` (new heading missing) and `test_conductor_edit_splicing_intake_and_routes` (section absent).

- [ ] **Step 3: Add the section**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **after** the `## Staleness` section and **before** `## Failure & rejection handling`:

```markdown
## Edit & interruption splicing

The user can interrupt at any point to correct something in plain language — a number, a
classification, or a decision. Recognize the correction, fix the **owning artifact**, re-run the
audited pipeline, and report what changed. Never free-edit an arbitrary file: route every
correction through one of the three owning-artifact mechanisms below, so every number still traces
`results.json` → tested formula → sourced input.

**Intake.** Treat a plain-language correction ("no, our rate is $200", "that's augmentation, not
automation", "actually billing is out of scope") as an edit, not a new instruction. Handle it at
the next **drive-loop boundary**: apply, re-drive, then resume where you left off.

**Classify & route** the correction to exactly one owning artifact:

- **Numeric assumption** (rate, volume, value range) → edit the owning `model/*.json` field
  (located via `docs/data-contract.md`'s field/source map), then re-run the engine. The Staleness
  rule re-drives everything downstream.
- **Structural** (opportunity type, roadmap sequencing) → **re-run the owning phase**. For an
  opportunity re-type, re-drive only that process's Phase 5 (**single-process mode**, see *Parallel
  per-process fan-out*) and re-merge; the Staleness rule carries the change into scoring, roadmap,
  and business case.
- **Human-only decision** (scope boundary, Build/Buy/Partner) → **re-open that must-ask**
  touchpoint; do not silently apply it.

**Report what changed.** Snapshot `results.json` before applying the edit; after the re-drive,
compute the delta with `PYTHONPATH="<engine_root>" python3 -c "from state.results_diff import
diff_results; ..."` (comparing the before-snapshot to the new `results.json`) and narrate the
salient changes (see the delta narration below).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): edit & interruption splicing — intake + 3 routes

Universal plain-language correction intake at the drive-loop boundary;
classify to model-input edit / owning-phase re-run (structural re-type reuses
Chunk A single-process mode) / reopen human-only must-ask; delta via
state.results_diff. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Conductor — confirm gate (act-then-show + exceptions + autonomy reconciliation)

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (extend the edit section from Task 2)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Edit & interruption splicing` section and `_section` helper.
- Produces: the confirm-gate rules within that section.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_edit_confirm_gate():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # Act-then-show default.
    assert "act-then-show" in sec
    # The two confirm-first exceptions.
    assert "ambiguous" in sec
    assert "must-ask" in sec
    # Downstream re-surfacing defers to the existing contract; no new batching here.
    assert "touchpoint taxonomy" in sec
    assert "autonomy preset" in sec
    assert "Chunk C" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_edit_confirm_gate -v`
Expected: FAIL (`assert "act-then-show" in sec`).

- [ ] **Step 3: Extend the section**

In `skills/conducting-engagement/SKILL.md`, inside `## Edit & interruption splicing`, add this block immediately **after** the "Report what changed." paragraph:

```markdown
**Confirm gate (act-then-show).** A correction is cheap and reversible (a value edit plus an
append-only log entry), and the delta report is the confirmation after the fact — so the default is
**act-then-show**: apply the correction, then report what changed. Confirm *first* only when:

- the mapping is **ambiguous** — ask which field they mean ("the cost rate or the value-improvement
  rate?"), an interpretation question, not a permission question; or
- the correction re-opens a **human-only must-ask** — scope boundary, Build/Buy/Partner, cost
  actuals — which are always must-ask, every mode.

This governs only *applying the correction the user explicitly stated*. The downstream ratifications
the re-drive re-opens still follow the existing **touchpoint taxonomy** and **autonomy preset**
unchanged (guided pauses on should-confirm; batching of those is **Chunk C**, not here).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_edit_confirm_gate -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): edit confirm gate — act-then-show + autonomy reconciliation

Default act-then-show for explicitly-stated corrections; confirm-first only on
ambiguous mapping or human-only must-ask. Downstream re-surfacing defers to the
existing touchpoint taxonomy + autonomy preset; batching stays Chunk C. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Conductor — both-parties logging + jargon-free delta narration

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (extend the edit section)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Edit & interruption splicing` section and `_section` helper.
- Produces: the decision-log mappings and a delimited `<!-- edit-delta-narration:start --> … :end -->` block.

- [ ] **Step 1: Write the failing tests**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_edit_logs_both_parties():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # AI-draft correction mapping.
    assert "human-overrode" in sec
    assert "overridden→" in sec
    # Fresh user-fact mapping.
    assert "human-ratified" in sec
    assert "edited" in sec
    # Append-only, never overwrite the AI proposal.
    assert "append-only" in sec


def test_conductor_edit_delta_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- edit-delta-narration:start -->")
    end = text.find("<!-- edit-delta-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "delta narration must be wrapped in <!-- edit-delta-narration:start --> ... :end -->"
    narration = text[start:end]
    forbidden = ["OPP-", "model/", "_staging", "renumber"] + [f"Phase {n}" for n in range(1, 12)]
    for token in forbidden:
        assert token not in narration, f"delta narration leaks jargon: {token!r}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_edit_logs_both_parties tests/test_conductor_skill.py::test_conductor_edit_delta_narration_is_jargon_free -v`
Expected: FAIL (logging strings and narration markers absent).

- [ ] **Step 3: Add logging + narration block**

In `skills/conducting-engagement/SKILL.md`, at the **end** of the `## Edit & interruption splicing` section, add:

```markdown
**Log both parties.** Record every correction in the decision log, append-only — never overwrite
the original proposal (it is the override corpus the improvement flywheel mines):

- Correcting an AI draft (AI proposed X, human says Y): `proposed_by: agent`,
  `decided_by: human-overrode`, `disposition: overridden→Y`.
- A fresh user-supplied fact (no prior AI claim, or correcting a placeholder): `proposed_by: human`,
  `decided_by: human-ratified`, `disposition: edited`.

("Override" here is the decision-log sense — distinct from the CLAUDE.md methodology overrides in
the reconcile step; this is not that.)

**Narrate the delta** in plain language — no step names, file names, or internal ids:

<!-- edit-delta-narration:start -->
> Done — I updated that and re-ran the numbers. The business case moved from $1.4M to $1.1M, and
> the status-assembly opportunity shifted from this year to next. Want me to walk through why?
<!-- edit-delta-narration:end -->
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: PASS (all conductor guards green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): edit both-parties logging + jargon-free delta narration

Append-only decision-log mappings (human-overrode/overridden→X for AI-draft
corrections; human-ratified/edited for fresh facts) and a plain-language delta
narration block guarded free of OPP/model/Phase tokens. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: CHANGELOG + full-suite verification

**Files:**
- Modify: `CHANGELOG.md` (under `## [Unreleased]`)

**Interfaces:**
- Consumes: all prior tasks.

- [ ] **Step 1: Add the CHANGELOG entry**

In `CHANGELOG.md`, under `## [Unreleased]` (in the existing `### Added` subsection if one is present from Chunk A — add the bullet there rather than a second `### Added`):

```markdown
- **Edit & interruption splicing (Slice 2 Chunk B, #87).** The user can correct anything in plain
  language at any point — a number, a classification, or a decision. The conductor routes the
  correction to the right audited mechanism, re-runs the pipeline, and reports exactly what changed
  (backed by the new deterministic `state/results_diff.py`). Replaces the old spreadsheet "what-if",
  stricter because it re-runs the audited engine. No engine/math change.
```

- [ ] **Step 2: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — **282 passed** (272 baseline + 6 helper tests + 4 conductor guards).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): Slice 2 Chunk B — edit & interruption splicing (#87)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Push**

```bash
git push
```

This chunk carries a wired Python helper (`state/results_diff.py`) with tests, so it is expected to be **auto-merge-eligible** (unlike Chunk A's markdown-only HOLD) — but confirm the gate result before merging.

---

## Self-Review

**1. Spec coverage** (against `2026-06-24-slice2-chunkB-edit-splicing-design.md`):
- §4 intake + three routes → Task 2. §5 confirm gate + autonomy reconciliation → Task 3. §6 delta helper → Task 1; conductor hookup → Task 2; jargon-free narration → Task 4. §7 both-parties logging (exact enum) → Task 4. §8 splicing at drive-loop boundary → Task 2; Chunk-A renumber caveat → documented in spec §8 (no code path; structural route in Task 2 reuses single-process mode, which carries the caveat). §9 guards 1–5 → Tasks 2/3/4 (1,2,4,5) and Task 1 (3). §10 files → all covered.
- **"Out of scope" (sandbox preview):** correctly absent from all tasks.

**2. Placeholder scan:** none — every step has exact prose, test code, and commands with expected output.

**3. Type/token consistency:** guard tokens match the prose verbatim — Task 2: `plain language`, `drive-loop boundary`, `model/*.json`, `re-run the owning phase`, `single-process mode`, `re-open that must-ask`, `state.results_diff`, `diff_results`. Task 3: `act-then-show`, `ambiguous`, `must-ask`, `touchpoint taxonomy`, `autonomy preset`, `Chunk C`. Task 4: `human-overrode`, `overridden→`, `human-ratified`, `edited`, `append-only`, narration markers + forbidden list. Helper API (`MISSING`, `Change(path/before/after)`, `diff_results`) is consistent between Task 1's implementation and tests. The narration example contains none of the forbidden tokens (`$1.4M`, `business case`, `status-assembly opportunity` only).
