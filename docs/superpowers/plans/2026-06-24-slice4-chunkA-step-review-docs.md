# Slice 4 · Chunk A — Step Review Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the operator one readable, regenerable review document per fragmented step — consolidating its `_index.md` + per-item files, an inline-comment extractor, a change-history view of the decision log, and comment-preserving regeneration — surfaced read-only by the conductor at each step boundary.

**Architecture:** A new pure module `state/step_review.py` composes existing files (no new content, no engine). Items render by **filename-stem id** (`OPP-001.md` → `OPP-001`), uniform across all four fragmented phases, so no per-phase index parsing is needed. Chunk B will consume this module's `extract_comments` for the interactive comment lifecycle; Chunk A delivers the readable doc + read-only surfacing.

**Tech Stack:** Python standard library only + `state.*`. pytest (`.venv/bin/python -m pytest`).

## Global Constraints

- **Stdlib-only + `state.*`.** No third-party imports. (Spec §3.2.)
- **Pure.** No mutation of source files, no subprocess, no network. `render_review` returns a string; only the CLI writes. (Spec §3.2.)
- **No new content.** The review consolidates existing files verbatim; it computes nothing. (Spec §2.)
- **Items render by filename-stem id** (`OPP-001`), uniform across phases 4/5/6/8 — no per-phase index id parsing. (Plan refinement of Spec §3.2; sidesteps the usecase-briefs linked-id issue.)
- **`render_review` is comment-preserving:** unresolved inline comments in an existing target are re-injected at their anchor; an orphaned comment goes to an "Unanchored comments" section, never dropped. (Spec §3.2, §5.)
- **Change history is a *view* of the decision log** scoped to the step's item ids — never a second record. Tolerates a missing `comment:` field and a malformed heading (skip, don't crash). (Spec §3.3, §11.)
- **Comment convention:** a markdown blockquote led by `> 💬`, anchored by an explicit `@<ID>` or the nearest preceding heading's id. (Spec §4.1.)
- **CLI contract:** writes the target, prints its path, exit 0 for a valid dir; exit 2 + stderr `not a directory: <path>` otherwise — like `state/status.py`. (Spec §3.2.)
- **Conductor surfacing is read-only** in Chunk A (presents the review; the comment round-trip is Chunk B). (Spec §7, §9.)

---

## File Structure

- `state/step_review.py` — **create**: `Comment`, `extract_comments`, `review_path`, `render_review`, `render_change_history`, `_decision_history`, `main` (CLI).
- `state/tests/test_step_review.py` — **create**: extractor, renderer, change-history, preservation tests.
- `state/tests/test_step_review_cli.py` — **create**: CLI JSON-less output + exit codes.
- `skills/conducting-engagement/SKILL.md` — **modify**: add a read-only "Step reviews" surfacing section.
- `tests/test_conductor_skill.py` — **modify**: guard the new section.

---

### Task 1: `Comment` + `extract_comments`

**Files:**
- Create: `state/step_review.py`
- Test: `state/tests/test_step_review.py`

**Interfaces:**
- Produces:
  - `Comment(anchor: str | None, body: str, line: int)` — frozen dataclass.
  - `extract_comments(text: str) -> list[Comment]` — parses `> 💬` blockquote lines; anchor = explicit `@<ID>` in the body, else the nearest preceding heading's id, else `None`.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_step_review.py`:

```python
from state.step_review import Comment, extract_comments


def test_extract_explicit_anchor():
    text = "## OPP-001 — X\nbody\n\n> 💬 @OPP-003 this is augmentation\n"
    cs = extract_comments(text)
    assert cs == [Comment(anchor="OPP-003", body="@OPP-003 this is augmentation", line=4)]


def test_extract_positional_anchor():
    text = "## OPP-002 — Y\nbody\n\n> 💬 should be augmentation\n"
    cs = extract_comments(text)
    assert cs[0].anchor == "OPP-002"
    assert cs[0].body == "should be augmentation"


def test_extract_multiple_and_heading_switch():
    text = ("## OPP-001 — A\n> 💬 first\n"
            "## OPP-002 — B\n> 💬 second\n")
    cs = extract_comments(text)
    assert [(c.anchor, c.body) for c in cs] == [("OPP-001", "first"), ("OPP-002", "second")]


def test_extract_none_when_no_comments():
    assert extract_comments("## OPP-001 — A\njust content\n") == []


def test_extract_anchor_none_before_any_heading():
    cs = extract_comments("> 💬 orphan comment\n")
    assert cs[0].anchor is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.step_review'`.

- [ ] **Step 3: Create the module with the extractor**

Create `state/step_review.py`:

```python
"""Operator-facing step review documents.

Consolidates a fragmented phase's _index.md + per-item files into one readable
review document, appends a change-history view of the decision log scoped to the
step's items, and preserves unresolved inline comments across regeneration.
Pure functions of the filesystem; stdlib + state.* only. Only the CLI writes.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.phases import PHASES

_ID_RE = re.compile(r"[A-Z]+-\d+$")        # full-match an id token
_ID_SEARCH = re.compile(r"[A-Z]+-\d+")     # find an id inside a heading
_COMMENT_RE = re.compile(r"^>\s*💬\s*(.*\S)\s*$")
_AT_RE = re.compile(r"@([A-Z]+-\d+)")


@dataclass(frozen=True)
class Comment:
    anchor: str | None   # item id the comment is about, or None if unresolvable
    body: str            # the comment text (may include the @id token)
    line: int            # 1-based line number in the source text


def extract_comments(text: str) -> list[Comment]:
    out: list[Comment] = []
    heading_id: str | None = None
    for i, line in enumerate(text.splitlines(), start=1):
        m = _COMMENT_RE.match(line)
        if m:
            body = m.group(1).strip()
            at = _AT_RE.search(body)
            out.append(Comment(at.group(1) if at else heading_id, body, i))
            continue
        if line.lstrip().startswith("#"):
            s = _ID_SEARCH.search(line)
            if s:
                heading_id = s.group(0)
    return out
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: PASS (all five).

- [ ] **Step 5: Commit**

```bash
git add state/step_review.py state/tests/test_step_review.py
git commit -m "feat(state): step-review inline comment extractor (slice4 chunkA)"
```

---

### Task 2: `review_path` + `render_review` (summary + items)

**Files:**
- Modify: `state/step_review.py`
- Test: `state/tests/test_step_review.py`

**Interfaces:**
- Consumes: `state.phases.PHASES`.
- Produces:
  - `review_path(phase_id: str) -> str` — `reviews/NN-<slug>.md` for a fragmented phase; the source output path for a single-doc phase; `ValueError` for an unknown id.
  - `render_review(root, phase_id: str) -> str` — for a fragmented phase, a readable doc: title + the `_index.md` summary + each item body (sorted by id), separated by `---`. `ValueError` for a non-fragmented phase. (Change history + comment preservation added in Tasks 3–4.)

- [ ] **Step 1: Write the failing tests**

Append to `state/tests/test_step_review.py`:

```python
from state.step_review import render_review, review_path
import pytest


def test_review_path_fragmented_and_single():
    assert review_path("5") == "reviews/05-opportunities.md"
    assert review_path("4") == "reviews/04-processes.md"
    assert review_path("7") == "roadmap.md"            # single-doc -> source
    with pytest.raises(ValueError):
        review_path("99")


def test_render_review_consolidates_index_and_items(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID | Type |\n| --- | --- |\n| OPP-001 | Aug |\n",
        "opportunities/OPP-001.md": "## OPP-001 — Invoice\n\nFirst body.\n",
        "opportunities/OPP-002.md": "## OPP-002 — Status\n\nSecond body.\n",
    })
    out = render_review(root, "5")
    assert "# Review — Opportunities (opportunities/)" in out
    assert "## Summary" in out and "| OPP-ID | Type |" in out
    # both item bodies present, in id order
    assert out.index("OPP-001 — Invoice") < out.index("OPP-002 — Status")
    assert "First body." in out and "Second body." in out


def test_render_review_rejects_single_doc_phase(engagement):
    root = engagement(**{"roadmap.md": "x"})
    with pytest.raises(ValueError):
        render_review(root, "7")


def test_render_review_deterministic(engagement):
    root = engagement(**{
        "scores/_index.md": "| OPP-ID |\n",
        "scores/OPP-001.md": "## OPP-001 — S\n\nb\n",
    })
    assert render_review(root, "6") == render_review(root, "6")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: FAIL — `ImportError` for `render_review` / `review_path`.

- [ ] **Step 3: Add the constants, `review_path`, and `render_review`**

In `state/step_review.py`, add after the regexes:

```python
# Fragmented phases: phase_id -> (folder, review-file slug, display name).
_FRAGMENTED = {
    "4": ("processes", "04-processes", "Process Discovery"),
    "5": ("opportunities", "05-opportunities", "Opportunities"),
    "6": ("scores", "06-scores", "Scoring"),
    "8": ("usecase-briefs", "08-usecase-briefs", "Use-Case Briefs"),
}
```

Then add (after `extract_comments`):

```python
def review_path(phase_id: str) -> str:
    if phase_id in _FRAGMENTED:
        return f"reviews/{_FRAGMENTED[phase_id][1]}.md"
    for p in PHASES:
        if p.id == phase_id:
            return p.output
    raise ValueError(f"unknown phase_id: {phase_id}")


def _item_bodies(folder: Path) -> list[Path]:
    return sorted(
        (p for p in folder.glob("*.md")
         if p.name != "_index.md" and _ID_RE.fullmatch(p.stem)),
        key=lambda p: p.stem,
    )


def render_review(root, phase_id: str) -> str:
    if phase_id not in _FRAGMENTED:
        raise ValueError(f"phase {phase_id} is not fragmented; use its source doc")
    root = Path(root)
    folder_name, _slug, display = _FRAGMENTED[phase_id]
    folder = root / folder_name

    parts = [
        f"# Review — {display} ({folder_name}/)", "",
        "> Working review document — read it and tell me what to change.", "",
    ]
    index = folder / "_index.md"
    if index.exists():
        parts += ["## Summary", "", index.read_text(encoding="utf-8").rstrip(), ""]
    for p in _item_bodies(folder):
        parts += ["---", "", p.read_text(encoding="utf-8").rstrip(), ""]
    return "\n".join(parts).rstrip() + "\n"
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: PASS (Task 1 + Task 2 tests).

- [ ] **Step 5: Commit**

```bash
git add state/step_review.py state/tests/test_step_review.py
git commit -m "feat(state): step-review render (summary + items) (slice4 chunkA)"
```

---

### Task 3: Change-history view of the decision log

**Files:**
- Modify: `state/step_review.py`
- Test: `state/tests/test_step_review.py`

**Interfaces:**
- Produces:
  - `_decision_history(root, ids: set[str]) -> list[dict]` — decision-log entries whose heading id is in `ids`, in file order, each `{"when","id","comment","change"}`. Missing `comment:` → `"—"`; `change` falls back from `disposition` to `decision`. Malformed heading (fewer than 3 ` — ` fields) is skipped.
  - `render_change_history(root, ids: set[str]) -> str` — a `## Change history` markdown section: a table when entries exist, else `No changes yet.` Cell values have `|` escaped.
  - `render_review` now ends with the change-history section, scoped to the step's item ids.

- [ ] **Step 1: Write the failing tests**

Append to `state/tests/test_step_review.py`:

```python
from state.step_review import render_change_history

_LOG = (
    "# Decision Log\n\n"
    "## 2026-06-24T10:00 — type classification — OPP-001\n"
    "- proposed_by: agent\n- decided_by: human-overrode\n"
    "- disposition: overridden→Augmentation\n- decision: retype to Augmentation\n"
    "- comment: this is augmentation, not automation\n\n"
    "## 2026-06-24T11:00 — sequencing — PROC-009\n"   # different step, must be excluded
    "- disposition: edited\n- comment: unrelated\n\n"
)


def test_change_history_scopes_to_ids(engagement):
    root = engagement(**{"decision-log.md": _LOG})
    out = render_change_history(root, {"OPP-001"})
    assert "## Change history" in out
    assert "this is augmentation, not automation" in out
    assert "overridden→Augmentation" in out
    assert "PROC-009" not in out and "unrelated" not in out


def test_change_history_empty(engagement):
    root = engagement(**{"opportunities/_index.md": "x"})
    assert "No changes yet." in render_change_history(root, {"OPP-001"})


def test_change_history_missing_comment_field(engagement):
    log = ("## 2026-06-24T10:00 — sequencing — OPP-002\n"
           "- disposition: edited\n- decision: moved to wave 2\n")
    root = engagement(**{"decision-log.md": log})
    out = render_change_history(root, {"OPP-002"})
    assert "moved to wave 2" in out  # change falls back to decision
    assert "| — |" in out            # comment renders as em-dash placeholder


def test_change_history_skips_malformed_heading(engagement):
    log = "## not a real entry heading\n- disposition: edited\n"
    root = engagement(**{"decision-log.md": log})
    # no crash; nothing scoped in
    assert "No changes yet." in render_change_history(root, {"OPP-001"})


def test_render_review_includes_change_history(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID |\n",
        "opportunities/OPP-001.md": "## OPP-001 — X\n\nb\n",
        "decision-log.md": _LOG,
    })
    out = render_review(root, "5")
    assert "## Change history" in out
    assert "this is augmentation, not automation" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: FAIL — `ImportError` for `render_change_history`; `render_review` lacks the section.

- [ ] **Step 3: Add the history functions and wire them in**

In `state/step_review.py`, add:

```python
def _esc(cell: str) -> str:
    return cell.replace("|", r"\|")


def _decision_history(root, ids: set[str]) -> list[dict]:
    path = Path(root) / "decision-log.md"
    if not path.exists():
        return []
    out: list[dict] = []
    cur: dict | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = None
            fields = [s.strip() for s in line[3:].split(" — ")]
            if len(fields) >= 3 and fields[-1] in ids:
                cur = {"when": fields[0], "id": fields[-1], "comment": "—", "change": "—"}
                out.append(cur)
        elif cur is not None and line.startswith("- "):
            key, _, val = line[2:].partition(":")
            key, val = key.strip(), val.strip()
            if key == "comment":
                cur["comment"] = val or "—"
            elif key == "disposition":
                cur["change"] = val or "—"
            elif key == "decision" and cur["change"] == "—":
                cur["change"] = val or "—"
    return out


def render_change_history(root, ids: set[str]) -> str:
    entries = _decision_history(root, ids)
    lines = ["## Change history", ""]
    if not entries:
        lines.append("No changes yet.")
        return "\n".join(lines)
    lines += ["| When | Item | Original comment | What changed |", "|---|---|---|---|"]
    for e in entries:
        lines.append(f"| {_esc(e['when'])} | {_esc(e['id'])} | "
                     f"{_esc(e['comment'])} | {_esc(e['change'])} |")
    return "\n".join(lines)
```

Then change the end of `render_review` — replace the final `return` with:

```python
    ids = {p.stem for p in _item_bodies(folder)}
    parts += [render_change_history(root, ids), ""]
    return "\n".join(parts).rstrip() + "\n"
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: PASS (Tasks 1–3).

- [ ] **Step 5: Commit**

```bash
git add state/step_review.py state/tests/test_step_review.py
git commit -m "feat(state): step-review change-history view of decision log (slice4 chunkA)"
```

---

### Task 4: Comment-preserving regeneration

**Files:**
- Modify: `state/step_review.py`
- Test: `state/tests/test_step_review.py`

**Interfaces:**
- Produces: `render_review` now re-injects unresolved comments found in an existing target — each at its anchor item (right after that item body), an orphaned/`None`-anchor comment under an `## Unanchored comments` section before the change history. Consumes `review_path`, `extract_comments`.

- [ ] **Step 1: Write the failing tests**

Append to `state/tests/test_step_review.py`:

```python
def test_render_preserves_anchored_comment(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID |\n",
        "opportunities/OPP-001.md": "## OPP-001 — X\n\nb\n",
    })
    # write an existing review target carrying a comment
    target = root / "reviews" / "05-opportunities.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_review(root, "5").replace(
        "b\n", "b\n\n> 💬 @OPP-001 please revise\n"))
    out = render_review(root, "5")
    assert "> 💬 @OPP-001 please revise" in out
    # the comment sits within the OPP-001 section, before Change history
    assert out.index("please revise") < out.index("## Change history")


def test_render_preserves_orphan_comment_in_unanchored(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID |\n",
        "opportunities/OPP-001.md": "## OPP-001 — X\n\nb\n",
    })
    target = root / "reviews" / "05-opportunities.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    # comment anchored to an item that no longer exists
    target.write_text("# Review\n\n> 💬 @OPP-999 stale anchor\n")
    out = render_review(root, "5")
    assert "## Unanchored comments" in out
    assert "stale anchor" in out


def test_render_no_target_no_comments(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID |\n",
        "opportunities/OPP-001.md": "## OPP-001 — X\n\nb\n",
    })
    out = render_review(root, "5")
    assert "Unanchored comments" not in out
    assert "> 💬" not in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: FAIL — comments are not preserved (the three new tests fail).

- [ ] **Step 3: Add comment preservation to `render_review`**

Replace the body of `render_review` **from the line after `folder = root / folder_name` to the end of the function** (i.e. everything that builds and returns the document — this supersedes the Task 2/3 body, re-including the change-history call) with:

```python
    # comments to preserve from an existing target
    target = root / review_path(phase_id)
    preserved = extract_comments(target.read_text(encoding="utf-8")) if target.exists() else []
    bodies = _item_bodies(folder)
    ids = {p.stem for p in bodies}
    by_anchor: dict[str, list[Comment]] = {}
    unanchored: list[Comment] = []
    for c in preserved:
        (by_anchor.setdefault(c.anchor, []) if c.anchor in ids else unanchored).append(c)

    parts = [
        f"# Review — {display} ({folder_name}/)", "",
        "> Working review document — read it and tell me what to change.", "",
    ]
    index = folder / "_index.md"
    if index.exists():
        parts += ["## Summary", "", index.read_text(encoding="utf-8").rstrip(), ""]
    for p in bodies:
        parts += ["---", "", p.read_text(encoding="utf-8").rstrip(), ""]
        for c in by_anchor.get(p.stem, []):
            parts += [f"> 💬 {c.body}", ""]
    if unanchored:
        parts += ["## Unanchored comments", ""]
        for c in unanchored:
            parts += [f"> 💬 {c.body}", ""]
    parts += [render_change_history(root, ids), ""]
    return "\n".join(parts).rstrip() + "\n"
```

Note: `by_anchor.setdefault(c.anchor, [])` returns the list to append to; the conditional appends the comment to either that list or `unanchored`. A `None` anchor is never in `ids`, so it lands in `unanchored`.

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_step_review.py -v`
Expected: PASS (Tasks 1–4).

- [ ] **Step 5: Commit**

```bash
git add state/step_review.py state/tests/test_step_review.py
git commit -m "feat(state): step-review comment-preserving regeneration (slice4 chunkA)"
```

---

### Task 5: CLI entry point

**Files:**
- Modify: `state/step_review.py`
- Test: `state/tests/test_step_review_cli.py`

**Interfaces:**
- Produces: `main(argv=None) -> int` — `python3 state/step_review.py <folder> <phase_id>` writes `render_review` to `<folder>/<review_path(phase_id)>` (creating `reviews/` if needed) and prints the written path; exit 0. Non-dir folder → stderr `not a directory: <path>`, exit 2.

- [ ] **Step 1: Write the failing test**

Create `state/tests/test_step_review_cli.py`:

```python
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "step_review.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_writes_review_and_prints_path(tmp_path):
    eng = tmp_path / "acme"
    (eng / "opportunities").mkdir(parents=True)
    (eng / "opportunities" / "_index.md").write_text("| OPP-ID |\n")
    (eng / "opportunities" / "OPP-001.md").write_text("## OPP-001 — X\n\nb\n")
    res = _run([str(eng), "5"])
    assert res.returncode == 0
    written = (eng / "reviews" / "05-opportunities.md")
    assert written.exists()
    assert "reviews/05-opportunities.md" in res.stdout
    assert "# Review — Opportunities" in written.read_text()


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "missing"), "5"])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_step_review_cli.py -v`
Expected: FAIL — no `main`/`__main__` (subprocess writes nothing, exit 0 with empty stdout).

- [ ] **Step 3: Append the CLI**

Append to `state/step_review.py`:

```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="state.step_review")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    parser.add_argument("phase_id", help="fragmented phase id (4, 5, 6, 8)")
    args = parser.parse_args(argv)
    if not args.engagement.is_dir():
        print(f"not a directory: {args.engagement}", file=sys.stderr)
        return 2
    rel = review_path(args.phase_id)
    out_path = args.engagement / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_review(args.engagement, args.phase_id), encoding="utf-8")
    print(str(rel))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_step_review_cli.py -v`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add state/step_review.py state/tests/test_step_review_cli.py
git commit -m "feat(state): step-review CLI (write + print path) (slice4 chunkA)"
```

---

### Task 6: Conductor — read-only "Step reviews" surfacing + guard

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `state/step_review.py` CLI.
- Produces: a `## Step reviews` section (read-only surfacing for Chunk A) with a fenced jargon-free narration block. Guarded by `tests/test_conductor_skill.py`.

- [ ] **Step 1: Write the failing guard tests**

In `tests/test_conductor_skill.py`, append `"## Step reviews"` to `REQUIRED_HEADINGS`, and add:

```python
def test_conductor_step_reviews_section():
    sec = _section(SKILL.read_text(), "## Step reviews")
    # Renders the review by absolute path.
    assert "state/step_review.py" in sec
    # Read-only in this chunk (the comment round-trip comes later).
    assert "read-only" in sec.lower()
    # Fragmented vs single-doc distinction is stated.
    assert "fragmented" in sec.lower()
    # Jargon-free narration block, fenced.
    assert "<!-- step-review-narration:start -->" in sec
    assert "<!-- step-review-narration:end -->" in sec


def test_conductor_step_review_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- step-review-narration:start -->")
    end = text.find("<!-- step-review-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "step-review narration must be wrapped in its fences"
    narration = text[start:end]
    forbidden = (["OPP-", "PROC-", "UC-", "step_review", "_index.md", "reviews/",
                  "render_review"] + [f"Phase {n}" for n in range(1, 12)])
    for token in forbidden:
        assert token not in narration, f"step-review narration leaks jargon: {token!r}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — section heading missing.

- [ ] **Step 3: Add the section**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **before** `## Status on demand` (the two read-time operator surfaces sit together):

````markdown
## Step reviews

At each step boundary, offer the operator a readable review of what the step produced before
the next step builds on it — the operator tier (distinct from the client checkpoints and the
final deliverable). In this revision the review is **read-only**: you present it; corrections
still flow through *Edit & interruption splicing* (the inline-comment round-trip lands in a
later revision).

- For a **fragmented** step (process discovery, opportunities, scoring, use-case briefs —
  split across an index + per-item files), render the consolidated review by absolute path:
  `python3 <engine_root>/state/step_review.py <folder> <phase_id>` — it writes one readable
  document and prints its path. Offer to open it.
- For a step that already has one clean document, that document is the review — just point to
  it.

Surfacing a review is **read-only**: it never advances the drive loop or mutates anything.
The register sets how much you explain (operator vs consultant voice).

Narrate jargon-free — no file names, ids, or step numbers:

<!-- step-review-narration:start -->
> Here's what this step produced, pulled together so it's easy to read in one place. Take a
> look whenever you like — and just tell me if anything should change before I build on it.
<!-- step-review-narration:end -->
````

- [ ] **Step 4: Run the guard tests + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS (new guards green; whole suite green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): step reviews read-only surfacing (slice4 chunkA)"
```

---

## Final verification

- [ ] Whole suite: `.venv/bin/python -m pytest -q` — all green.
- [ ] Smoke: `python3 state/step_review.py sample-pso-delivery/ 5` writes `reviews/05-opportunities.md` consolidating the sample's opportunities; open it and confirm it reads as one document with a Change-history section (`No changes yet.` on the untouched sample).
