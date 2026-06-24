# Slice 3 · Chunk C — Improvement-flywheel Auto-flagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the Conductor auto-write a structured RED entry when it catches itself reaching for a rationalization shortcut, via a small pure helper that enforces the non-destructive-prepend / Entry-Format invariant; GREEN/REFACTOR stay human-approved.

**Architecture:** A new pure module `state/improvement_log.py` (`Escape`, `render_entry`, `prepend_entry`) renders the canonical Entry Format and prepends it under `## Entries` (scaffolding an absent file; `ValueError` if an existing file lacks the header). A Conductor SKILL.md section wires detection → refuse → auto-RED-write → surface GREEN/REFACTOR. The canonical Entry-Format docs gain `pending` as a valid auto-RED value.

**Tech Stack:** Python standard library only + `state.*`. pytest (`.venv/bin/python -m pytest`).

## Global Constraints

- **Stdlib-only + `state.*`.** No third-party imports. (Spec §3.2.)
- **No clock in the module.** `Escape.date` is supplied by the caller — keeps it pure/testable. (Spec §3.2.)
- **Non-destructive prepend (existing entries immutable):** `prepend_entry` only inserts a new block (and scaffolds when absent); it never edits, reorders, or drops a prior entry. (Spec §3.2.)
- **`## Entries` contract:** absent file → scaffold; existing file with the header → insert after the **first** occurrence; existing file **without** the header → raise `ValueError`. (Spec §3.2.)
- **`reframe`** is the canonical reframe copied from a matched master-table row, or the literal `"pending"` when no row existed (never Conductor-invented). (Spec §3.2.)
- **`Keystone updated` / `Checklist/gate step updated` render as `pending`** for an auto-RED entry. (Spec §3.2.)
- **GREEN/REFACTOR stay human-approved** — the Conductor only auto-writes the RED capture and surfaces the proposal. (Spec §2, §3.3.)
- **Narration jargon-free**, conditional on a successful write. (Spec §3.3, Epic AC-1.)

---

## File Structure

- `state/improvement_log.py` — **create**: `Escape`, `render_entry`, `prepend_entry`.
- `state/tests/test_improvement_log.py` — **create**: render + prepend unit tests.
- `improvement-log.md` — **modify**: extend the Entry-Format template to allow `pending`.
- `skills/conducting-engagement/SKILL.md` — **modify**: add the flywheel section + narration.
- `tests/test_conductor_skill.py` — **modify**: guards for the new section.

---

### Task 1: `state/improvement_log.py` — render + non-destructive prepend

**Files:**
- Create: `state/improvement_log.py`
- Test: `state/tests/test_improvement_log.py`
- Modify: `improvement-log.md:25-26`

**Interfaces:**
- Produces:
  - `Escape(date, phase, skill, engagement, shortcut, would_produce, why_uncaught, reframe)` — frozen dataclass (all `str`).
  - `render_entry(escape) -> str` — one RED block in the canonical Entry Format.
  - `prepend_entry(log_path, escape) -> None` — scaffold-or-insert under `## Entries`; `ValueError` if an existing file lacks the header.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_improvement_log.py`:

```python
import pytest

from state.improvement_log import Escape, prepend_entry, render_entry

ESC = Escape(
    date="2026-06-24", phase="5", skill="identifying-opportunities",
    engagement="acme / round 1",
    shortcut="This step doesn't look like an AI candidate — let's skip it.",
    would_produce="A process dropped before its chain potential was evaluated.",
    why_uncaught="The step-by-step comparative-advantage row should have caught it.",
    reframe="Evaluate every step in the context of its neighbors, not in isolation.",
)


def test_render_entry_has_format_fields():
    out = render_entry(ESC)
    assert "### [2026-06-24] Phase 5 — identifying-opportunities" in out
    assert "**Engagement/Round:** acme / round 1" in out
    assert "**Shortcut taken:** This step doesn't look like an AI candidate" in out
    assert "**What it produced:** A process dropped" in out
    assert "**Why the table didn't catch it:**" in out
    # the proposed reframe row
    assert "| Rationalization / Shortcut | Correct Reframe |" in out
    assert "Evaluate every step in the context of its neighbors" in out
    # GREEN/REFACTOR fields are pending for an auto-RED entry
    assert "**Keystone updated:** pending" in out
    assert "**Checklist/gate step updated:** pending" in out


def test_render_entry_reframe_pending_when_no_row():
    esc = Escape(date="2026-06-24", phase="n/a", skill="conductor",
                 engagement="n/a", shortcut="some novel shortcut",
                 would_produce="x", why_uncaught="no row existed", reframe="pending")
    out = render_entry(esc)
    assert "| some novel shortcut | pending |" in out


def test_prepend_scaffolds_absent_file(tmp_path):
    log = tmp_path / "improvement-log.md"
    prepend_entry(log, ESC)
    text = log.read_text()
    assert text.startswith("# Improvement Log")
    assert "## Entries" in text
    assert "### [2026-06-24] Phase 5 — identifying-opportunities" in text


def test_prepend_newest_first_and_preserves_prior(tmp_path):
    log = tmp_path / "improvement-log.md"
    first = Escape(date="2026-06-01", phase="4", skill="discovering-processes",
                   engagement="e1", shortcut="FIRST-SHORTCUT", would_produce="x",
                   why_uncaught="y", reframe="z")
    prepend_entry(log, first)
    prepend_entry(log, ESC)  # newer
    text = log.read_text()
    # newest appears before the older one
    assert text.index("identifying-opportunities") < text.index("discovering-processes")
    # the older entry is preserved verbatim
    assert "FIRST-SHORTCUT" in text


def test_prepend_preserves_existing_yes_no_entry(tmp_path):
    log = tmp_path / "improvement-log.md"
    log.write_text(
        "# Improvement Log\n\n## Entries\n\n"
        "### [2026-05-01] Phase 4 — discovering-processes\n\n"
        "**Keystone updated:** no\n**Checklist/gate step updated:** no\n"
    )
    prepend_entry(log, ESC)
    text = log.read_text()
    # existing yes/no entry untouched
    assert "**Keystone updated:** no" in text
    # new entry present and ahead of it
    assert text.index("identifying-opportunities") < text.index("discovering-processes")


def test_prepend_raises_without_entries_header(tmp_path):
    log = tmp_path / "improvement-log.md"
    log.write_text("# Some other log\n\nfreeform notes, no Entries header\n")
    with pytest.raises(ValueError):
        prepend_entry(log, ESC)


def test_prepend_is_deterministic(tmp_path):
    log1 = tmp_path / "a.md"
    log2 = tmp_path / "b.md"
    prepend_entry(log1, ESC)
    prepend_entry(log2, ESC)
    assert log1.read_text() == log2.read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_improvement_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.improvement_log'`.

- [ ] **Step 3: Create the module**

Create `state/improvement_log.py`:

```python
"""Auto-RED capture for the improvement flywheel.

The Conductor calls prepend_entry() when it catches itself reaching for a
rationalization shortcut: it records a structured RED entry in the engagement's
improvement-log.md. GREEN (the rationalization-table row) and REFACTOR (gate
tightening) remain human-approved and are not done here.

Pure given (file contents, escape) — no clock (the date is passed in), no network.
The prepend is non-destructive: existing entries are never edited or reordered.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ENTRIES_HEADER = "## Entries"
_SCAFFOLD = (
    "# Improvement Log\n\n"
    "Prepend-only. New entries go at the top. Existing entries are never edited.\n\n"
    f"{ENTRIES_HEADER}\n"
)


@dataclass(frozen=True)
class Escape:
    date: str          # ISO date, supplied by the caller (no clock here)
    phase: str         # e.g. "5" or "n/a"
    skill: str         # skill dir name or "conductor"
    engagement: str    # engagement name/round, or "n/a"
    shortcut: str      # the rationalization the Conductor caught itself reaching for
    would_produce: str # the consequence it avoided
    why_uncaught: str  # which table row should have caught it (or "no row existed")
    reframe: str       # canonical reframe from the matched row, or "pending"


def render_entry(escape: Escape) -> str:
    """One RED entry in the canonical Entry Format (newest-first block)."""
    return (
        f"### [{escape.date}] Phase {escape.phase} — {escape.skill}\n\n"
        f"**Engagement/Round:** {escape.engagement}\n"
        f"**Shortcut taken:** {escape.shortcut}\n"
        f"**What it produced:** {escape.would_produce}\n"
        f"**Why the table didn't catch it:** {escape.why_uncaught}\n"
        f"**New row added to:** pending\n\n"
        f"| Rationalization / Shortcut | Correct Reframe |\n"
        f"|---|---|\n"
        f"| {escape.shortcut} | {escape.reframe} |\n\n"
        f"**Keystone updated:** pending\n"
        f"**Checklist/gate step updated:** pending\n"
    )


def prepend_entry(log_path, escape: Escape) -> None:
    """Prepend a RED entry under '## Entries'. Scaffold an absent file; insert after
    the first '## Entries' line of an existing one; raise ValueError if an existing
    file has no such header. Existing entries are never modified."""
    path = Path(log_path)
    block = render_entry(escape)
    if not path.exists():
        path.write_text(f"{_SCAFFOLD}\n{block}", encoding="utf-8")
        return
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == ENTRIES_HEADER:
            insert_at = i + 1
            break
    else:
        raise ValueError(f"{path}: no '{ENTRIES_HEADER}' header to prepend under")
    new_lines = lines[:insert_at] + [f"\n{block}"] + lines[insert_at:]
    path.write_text("".join(new_lines), encoding="utf-8")
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_improvement_log.py -v`
Expected: PASS (all seven).

- [ ] **Step 5: Extend the Entry-Format docs for `pending`**

In `improvement-log.md`, update the two **template** lines (lines 25-26, inside the Entry
Format section — NOT the example entry at lines 47-48):

Change:
```
**Keystone updated:** yes / no
**Checklist/gate step updated:** yes / no — <which gate or checklist step, if yes>
```
to:
```
**Keystone updated:** yes / no / pending
**Checklist/gate step updated:** yes / no / pending — <which gate or checklist step, if yes; "pending" for an auto-flagged RED entry awaiting GREEN/REFACTOR>
```

- [ ] **Step 6: Run the full suite + commit**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

```bash
git add state/improvement_log.py state/tests/test_improvement_log.py improvement-log.md
git commit -m "feat(state): improvement-log auto-RED helper (slice3 chunkC)"
```

---

### Task 2: Conductor wiring — "Improvement flywheel" section + guards

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: `state.improvement_log.prepend_entry`; the active engagement folder resolved at drive-loop step 0.
- Produces: a `## Improvement flywheel — auto-flagging escapes` section with a fenced `<!-- flywheel-narration:start -->`/`:end` block. Guarded by `tests/test_conductor_skill.py`.

- [ ] **Step 1: Write the failing guard tests**

In `tests/test_conductor_skill.py`, append `"## Improvement flywheel — auto-flagging escapes"` to the `REQUIRED_HEADINGS` list, and add:

```python
def test_conductor_flywheel_section():
    sec = _section(SKILL.read_text(), "## Improvement flywheel — auto-flagging escapes")
    # Auto-RED capture via the helper.
    assert "state.improvement_log" in sec or "prepend_entry" in sec
    # Only RED is automatic; GREEN/REFACTOR stay human-approved.
    assert "GREEN" in sec and "REFACTOR" in sec
    assert "human" in sec.lower()
    # Narration conditional on a successful write (failure path stated).
    assert "could" in sec.lower() or "fail" in sec.lower() or "couldn't" in sec.lower()
    # Fenced narration block.
    assert "<!-- flywheel-narration:start -->" in sec
    assert "<!-- flywheel-narration:end -->" in sec


def test_conductor_flywheel_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- flywheel-narration:start -->")
    end = text.find("<!-- flywheel-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "flywheel narration must be wrapped in <!-- flywheel-narration:start --> ... :end -->"
    narration = text[start:end]
    forbidden = (["OPP-", "PROC-", "improvement-log", "prepend_entry", "RED", "GREEN",
                  "REFACTOR", "rationalization", "Escape("]
                 + [f"Phase {n}" for n in range(1, 12)])
    for token in forbidden:
        assert token not in narration, f"flywheel narration leaks jargon: {token!r}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — section heading missing.

- [ ] **Step 3: Add the section**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **after** the existing `## Adaptive autonomy & holding the line` section (the flywheel is the durable record of the holding-the-line moment). Locate that heading and insert the new section before whatever `## ` heading follows it:

````markdown
## Improvement flywheel — auto-flagging escapes

When *holding the line* (above) catches you reaching for a methodology shortcut, don't just
refuse it — record it, so the method itself gets sharper over time.

1. **Detect (with a false-positive guard).** Watch your own reasoning for the master-table
   rationalizations in `using-methodology` (skip-a-step, compute-a-number-inline,
   reuse-prior-answers, optimize-around-not-root, …). Flag **only** when you would actually
   have taken the shortcut **and** the methodology does not explicitly permit the action
   here. A permitted reuse is not an escape.
2. **Refuse + auto-capture (RED).** Do not take the shortcut. Write a RED entry to the active
   engagement's `improvement-log.md` (the engagement folder resolved at drive-loop step 0,
   by absolute path):
   `PYTHONPATH="<engine_root>" python3 -c "from state.improvement_log import Escape, prepend_entry; prepend_entry('<engagement>/improvement-log.md', Escape(date='<today>', phase='<n>', skill='<skill>', engagement='<name>', shortcut='<caught shortcut>', would_produce='<avoided consequence>', why_uncaught='<which row, or \"no row existed\">', reframe='<canonical reframe from the matched row, or \"pending\">'))"`.
   Supply `<today>` yourself (the module keeps no clock). Use the canonical reframe from the
   matched master-table row, or `pending` when no row existed. This RED capture is the only
   automatic step.
3. **On write failure, don't claim success.** If the call raises (e.g. a pre-existing log
   without an `## Entries` header, or a path error), tell the human plainly that you caught
   the shortcut but couldn't write the note, and why — never narrate a record that doesn't
   exist.
4. **Surface GREEN/REFACTOR (human-approved), as two distinct asks.** After a successful
   write, tell the human you caught and logged it, and ask — distinguishing the two —
   whether to **GREEN** (add the rationalization row to the relevant skill) and/or
   **REFACTOR** (tighten the gate/checklist step). These edit skills/keystone and are
   **never** automatic.

This composes with *holding the line*: that section is the refusal; this is the durable
record. The must-ask floor and autonomy presets are unchanged.

Narrate jargon-free — no step, file, or method-internal names:

<!-- flywheel-narration:start -->
> Heads-up: I nearly took a shortcut there — reusing last time's answers instead of
> re-deriving them for your situation. I didn't, and I've noted it so the method gets a
> little sharper. Want me to fold that lesson into how I work, add a guardrail so it can't
> slip again — either, both, or neither and just keep going?
<!-- flywheel-narration:end -->
````

- [ ] **Step 4: Run the guard tests + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS (new guards green; whole suite green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): improvement flywheel auto-flagging (slice3 chunkC)"
```

---

## Final verification

- [ ] Whole suite: `.venv/bin/python -m pytest -q` — all green.
- [ ] Smoke: `PYTHONPATH=. python3 -c "from state.improvement_log import Escape, prepend_entry; import tempfile, pathlib; d=pathlib.Path(tempfile.mkdtemp())/'improvement-log.md'; prepend_entry(d, Escape('2026-06-24','5','s','e','shortcut','x','y','z')); print(d.read_text())"` prints a well-formed scaffolded log with the entry.
