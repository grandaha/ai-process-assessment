# Document Rendering Quality (#148) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the process-validation `.docx` renderer up to parity with the checkpoint-doc renderer (no data loss, no leaked markup, real lists) and add list-aware output shared across all doc types.

**Architecture:** Two renderer paths exist — `state/process_review.py` (per-process validation docs) and `state/checkpoint_doc.py` (every other checkpoint). `process_review` was never modernized. We add a `bullet_list` block to `state/docx.py`, add list-grouping to `checkpoint_doc`'s shared markdown→blocks helpers, then have `process_review` reuse those helpers via a plain (non-circular) import.

**Tech Stack:** Python stdlib only (`re`, `zipfile`, `xml.sax.saxutils`). Tests with pytest. Run tests with `python3.13` (python3.14 has broken pyexpat in this env).

## Global Constraints

- Stdlib only — no new dependencies. No `python-docx`.
- No fabrication: every rendered value is copied from the source `.md`; the internal-analysis sections (Conflicts / Chain scan / Challenge hypothesis) stay excluded from process-validation docs.
- `numbered_list` / `bullet_list` render as plain prefixed paragraphs — no `numbering.xml` part (matches the existing lazy pattern).
- `_clean_inline` strips only `**bold**` (leaves single `*`/`_` — they appear in identifiers).
- Keep existing `checkpoint_doc` behavior unchanged: tables, headings, bold-strip, `_require`, `_first_table`, adjacent-table split, internal exclusions (`_SCOPE_EXCLUDE`).
- Import direction: `process_review` imports from `checkpoint_doc` (top-level is safe — `checkpoint_doc` imports `process_review` only lazily inside `_build_process_validation`, so no import cycle in either load order). Do NOT create a new `md_blocks.py` module.
- Run tests with: `PYTHONPATH=. python3.13 -m pytest`.

---

### Task 1: List-aware shared renderer (`docx.bullet_list` + grouping in `checkpoint_doc`)

**Files:**
- Modify: `state/docx.py` (add `bullet_list` block type + factory)
- Modify: `state/checkpoint_doc.py` (add `_grouped_line_blocks`; rewire `blocks_from_markdown` and `prose_section`)
- Test: `tests/test_doc_rendering.py` (new)

**Interfaces:**
- Consumes: existing `docx._block`, `docx.build_docx`, `checkpoint_doc.md_table`, `_is_separator`, `_clean_inline`, `_md_line_block`.
- Produces:
  - `docx.bullet_list(items: list[str]) -> dict` — block `{"type": "bullet_list", "items": [...]}`
  - `checkpoint_doc._grouped_line_blocks(lines: list[str]) -> list[dict]` — table-free lines → grouped docx blocks (consecutive `-/*` → one `bullet_list`, consecutive `N.` → one `numbered_list`, else `_md_line_block`).
  - `blocks_from_markdown(text)` and `prose_section(title, md, heading)` keep the same signatures; output now contains real lists.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_doc_rendering.py`:

```python
# tests/test_doc_rendering.py — renderer-output tests (#148). Run with python3.13.
import zipfile

from state import docx
from state import checkpoint_doc as cd


def _types(blocks):
    return [b["type"] for b in blocks]


def test_bullet_list_factory():
    b = docx.bullet_list(["a", "b"])
    assert b == {"type": "bullet_list", "items": ["a", "b"]}


def test_bullet_list_renders_with_bullet_glyph(tmp_path):
    out = tmp_path / "d.docx"
    docx.build_docx([docx.bullet_list(["first", "second"])], str(out))
    with zipfile.ZipFile(out) as z:
        body = z.read("word/document.xml").decode("utf-8")
    assert "• first" in body
    assert "• second" in body


def test_blocks_from_markdown_groups_consecutive_bullets():
    blocks = cd.blocks_from_markdown("- one\n- two\n- three")
    assert _types(blocks) == ["bullet_list"]
    assert blocks[0]["items"] == ["one", "two", "three"]


def test_blocks_from_markdown_groups_consecutive_numbers():
    blocks = cd.blocks_from_markdown("1. one\n2. two")
    assert _types(blocks) == ["numbered_list"]
    assert blocks[0]["items"] == ["one", "two"]


def test_blocks_from_markdown_strips_bold_in_list_items():
    blocks = cd.blocks_from_markdown("- a **bold** item")
    assert blocks[0]["items"] == ["a bold item"]


def test_blocks_from_markdown_preserves_interleaved_prose_and_table():
    md = "Intro line\n\n- b1\n- b2\n\n| H1 | H2 |\n|---|---|\n| x | y |"
    blocks = cd.blocks_from_markdown(md)
    t = _types(blocks)
    assert t == ["paragraph", "bullet_list", "table"]
    assert blocks[1]["items"] == ["b1", "b2"]
    assert blocks[2]["headers"] == ["H1", "H2"]


def test_blocks_from_markdown_switches_bullet_to_number_into_two_lists():
    blocks = cd.blocks_from_markdown("- a\n1. b")
    assert _types(blocks) == ["bullet_list", "numbered_list"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_doc_rendering.py -v`
Expected: FAIL — `AttributeError: module 'state.docx' has no attribute 'bullet_list'` and grouping assertions fail (current output is all paragraphs).

- [ ] **Step 3: Add `bullet_list` to `state/docx.py`**

In `_block`, add a branch next to `numbered_list`:

```python
    if t == "bullet_list":
        return ''.join(_p(f"• {item}") for item in b["items"])
```

Add the factory next to `numbered_list`:

```python
def bullet_list(items): return {"type": "bullet_list", "items": list(items)}
```

- [ ] **Step 4: Add `_grouped_line_blocks` and rewire `blocks_from_markdown` + `prose_section` in `state/checkpoint_doc.py`**

Add the helper (place it just above `blocks_from_markdown`):

```python
def _grouped_line_blocks(lines):
    """Table-free markdown lines -> docx blocks. Consecutive `-`/`*` lines collapse into one
    bullet_list; consecutive `N.` lines into one numbered_list; everything else via
    _md_line_block. Empty lines are skipped without breaking an adjacent list."""
    out, bullets, nums = [], [], []
    def flush():
        if bullets:
            out.append(docx.bullet_list(bullets)); bullets.clear()
        if nums:
            out.append(docx.numbered_list(nums)); nums.clear()
    for s in lines:
        if not s:
            continue
        mb = re.match(r"^[-*]\s+(.*)$", s)
        if mb:
            if nums: flush()
            bullets.append(_clean_inline(mb.group(1).strip()))
            continue
        mn = re.match(r"^\d+\.\s+(.*)$", s)
        if mn:
            if bullets: flush()
            nums.append(_clean_inline(mn.group(1).strip()))
            continue
        flush()
        b = _md_line_block(s)
        if b:
            out.append(b)
    flush()
    return out
```

Rewrite `blocks_from_markdown` to buffer non-table lines and run them through `_grouped_line_blocks`:

```python
def blocks_from_markdown(text):
    """Render a markdown body as docx blocks: contiguous pipe-table lines become a table;
    consecutive bullets/numbers become real lists; other non-empty lines become
    headings/paragraphs (markers stripped). Adjacent tables with no blank line between them
    render as separate tables."""
    out, tbl, lines = [], [], []
    def _cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]
    def _flush_tbl():
        if tbl:
            h, r = md_table("\n".join(tbl))
            if h:
                out.append(docx.table(h, r))
            tbl.clear()
    def _flush_lines():
        if lines:
            out.extend(_grouped_line_blocks(lines))
            lines.clear()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            _flush_lines()
            # a separator while one is already buffered = a new table started with no blank line:
            # the line just buffered is its header; flush the completed table first.
            if _is_separator(_cells(s)) and any(_is_separator(_cells(t)) for t in tbl):
                header = tbl.pop()
                _flush_tbl()
                tbl.append(header)
            tbl.append(s)
            continue
        _flush_tbl()
        lines.append(s)
    _flush_tbl()
    _flush_lines()
    return out
```

Rewrite `prose_section` to use the same grouping (it already skips table rows):

```python
def prose_section(title, md, heading):
    body = md_section(md, heading)
    if not body:
        return []
    lines = [line.strip() for line in body.splitlines() if not line.strip().startswith("|")]
    return [docx.heading(title, 2)] + _grouped_line_blocks(lines)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_doc_rendering.py -v`
Expected: PASS (7 tests).

- [ ] **Step 6: Run the full suite — no regressions**

Run: `PYTHONPATH=. python3.13 -m pytest -q`
Expected: PASS (all existing tests still green).

- [ ] **Step 7: Commit**

```bash
git add state/docx.py state/checkpoint_doc.py tests/test_doc_rendering.py
git commit -m "feat: list-aware docx rendering (bullet_list + grouped lists) (#148)"
```

---

### Task 2: Fix the process-validation renderer (`state/process_review.py`)

**Files:**
- Modify: `state/process_review.py`
- Test: `tests/test_doc_rendering.py` (extend)

**Interfaces:**
- Consumes: `checkpoint_doc.blocks_from_markdown`, `checkpoint_doc._clean_inline` (top-level import — safe, see Global Constraints), `docx.heading/paragraph/numbered_list/table`.
- Produces:
  - `process_review._field_body(md, label) -> str | None` — full multi-line body of a `**Label:**` field, up to the next `**Bold:**` field / `### heading` / end.
  - `_steps(md) -> list[str]` — clean step actions (no `— **Color** (…)`, no legacy ` → …`).
  - `build_blocks(proc_md) -> list[dict]` — same signature; multi-bullet fields now render as bullet lists, steps are clean.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_doc_rendering.py`:

```python
from state import process_review as pr

PROC = """## PROC-001 — Client Onboarding & Project Setup
<!-- index: baseline=Ready -->

**Trigger:** HubSpot deal marked "Closed Won"; Zapier creates a Teamwork project.

### Process Map

**Steps:**
1. PM receives Slack notification — **Green** (fully automated trigger; no human input)
2. PM re-keys client details into Teamwork — **Green** (structured data transfer)
3. PM waits for client materials — **Red** (external dependency on client)

**Actors:** Tyler Brooks / PM team; HubSpot; Zapier; Teamwork.

**Decision points:**
- Whether to proceed to kickoff with partial assets (judgment call)
- Whether scope gaps require a change order before work begins

**Exceptions:**
- Client never responds to asset requests (~5% of projects)
- Client-provided credentials do not work (~15% of projects)

**Upstream / downstream:**
- Upstream: HubSpot deal closure; no pre-sale asset checklist
- Downstream: PROC-003 launches as a parallel subprocess

**Conflicts:**
- **Conflict A:** internal assessor analysis that must never render.

**Chain scan:**
- Steps 1-2 form a Green chain — internal analysis, excluded.

**Challenge hypothesis:** Internal redesign analysis, excluded.

### Baselines

| Field | Value | Source | Confidence |
|---|---|---|---|
| Volume | 6-8 projects/month | Teamwork log | Medium |
| Cycle time | Median 18 days | Tyler's sheet | Medium-High |
"""


def test_field_body_captures_all_decision_points():
    body = pr._field_body(PROC, "Decision points")
    assert body.count("- ") == 2
    assert "partial assets" in body
    assert "change order" in body


def test_field_body_captures_all_exceptions():
    body = pr._field_body(PROC, "Exceptions")
    assert "never responds" in body
    assert "credentials do not work" in body


def test_field_body_single_line_trigger():
    body = pr._field_body(PROC, "Trigger")
    assert body.startswith("HubSpot deal")
    assert "Closed Won" in body


def test_steps_are_clean_actions():
    steps = pr._steps(PROC)
    assert len(steps) == 3
    joined = " ".join(steps)
    for marker in ("Green", "Yellow", "Red", "**", "—", "(", "automated trigger"):
        assert marker not in joined, f"leaked {marker!r} into steps"
    assert steps[0] == "PM receives Slack notification"


def test_build_blocks_renders_both_decision_points_as_bullets():
    blocks = pr.build_blocks(PROC)
    # find the bullet_list that follows the "Decision points" heading
    idx = next(i for i, b in enumerate(blocks)
               if b["type"] == "heading" and b["text"] == "Decision points")
    lst = blocks[idx + 1]
    assert lst["type"] == "bullet_list"
    assert len(lst["items"]) == 2


def test_build_blocks_excludes_internal_sections():
    blocks = pr.build_blocks(PROC)
    text = " ".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "Conflict A" not in text
    assert "Chain scan" not in text
    assert "Challenge hypothesis" not in text
    assert "redesign analysis" not in text


def test_build_blocks_keeps_baselines_and_signoff():
    blocks = pr.build_blocks(PROC)
    headings = [b["text"] for b in blocks if b["type"] == "heading"]
    assert "Baseline figures (for context)" in headings
    assert "Sign-off" in headings
    assert any(b["type"] == "table" for b in blocks)


def test_build_blocks_no_leaked_markers_anywhere():
    blocks = pr.build_blocks(PROC)
    for b in blocks:
        for s in [b.get("text", "")] + b.get("items", []):
            assert "**" not in s
            assert " → " not in s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_doc_rendering.py -k "field_body or steps or build_blocks" -v`
Expected: FAIL — `_field_body` does not exist; `_steps` leaks `**Green**`/rationale (splits on ` → `, not the em-dash); decision points render as a single paragraph.

- [ ] **Step 3: Rewrite `state/process_review.py`**

Replace the module body below the imports. New imports at top:

```python
import re

from state import docx
from state.checkpoint_doc import blocks_from_markdown, _clean_inline
```

Replace `_FIELDS` / `_field` with `_field_body`:

```python
def _field_body(md, label):
    # Full body of a **Label:** field: inline text on the label line plus any following
    # lines, up to the next **Bold:** field, ### heading, or end of file.
    m = re.search(
        rf"^\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=^\*\*[^\n]+?:\*\*|^###\s|\Z)",
        md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None
```

Keep `_title` unchanged. Rewrite `_steps` to strip the em-dash color note:

```python
def _steps(md):
    # numbered lines under "**Steps:**" up to the next blank line / bold label;
    # strip the internal "— **Color** (rationale)" note and any legacy " → …" from each.
    block = re.search(r"\*\*Steps:\*\*\s*\n(.*?)(?:\n\s*\n|\n\*\*)", md, re.DOTALL)
    if not block:
        return []
    out = []
    for line in block.group(1).splitlines():
        m = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if m:
            action = re.sub(r"\s*—\s*\*\*(?:Green|Yellow|Red)\*\*.*$", "", m.group(1))
            action = action.split(" → ")[0]
            out.append(_clean_inline(action).strip())
    return out
```

Keep `_baselines` unchanged. Rewrite `build_blocks` to route field bodies through `blocks_from_markdown`:

```python
def build_blocks(proc_md):
    pid, name = _title(proc_md)
    blocks = [docx.heading(f"{pid} — {name}", 1),
              docx.paragraph("Please review the current-state capture of this process below "
                             "and confirm it is accurate, or note what should change.")]
    trigger = _field_body(proc_md, "Trigger")
    if trigger:
        blocks += [docx.heading("Trigger", 2)] + blocks_from_markdown(trigger)
    steps = _steps(proc_md)
    if steps:
        blocks += [docx.heading("Steps", 2), docx.numbered_list(steps)]
    for label in ("Actors", "Decision points", "Exceptions", "Upstream / downstream"):
        body = _field_body(proc_md, label)
        if body:
            blocks += [docx.heading(label, 2)] + blocks_from_markdown(body)
    bl = _baselines(proc_md)
    if bl:
        blocks += [docx.heading("Baseline figures (for context)", 2),
                   docx.table(["Field", "Value"], bl)]
    blocks += [docx.heading("Sign-off", 2),
               docx.paragraph("Process owner: ______________________"),
               docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
               docx.paragraph("Comments:")]
    return blocks
```

Update the module docstring's mention of the "→ …" color note to describe the em-dash color note actually stripped.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_doc_rendering.py -v`
Expected: PASS (all Task 1 + Task 2 tests).

- [ ] **Step 5: Run the full suite — no regressions**

Run: `PYTHONPATH=. python3.13 -m pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add state/process_review.py tests/test_doc_rendering.py
git commit -m "fix: process-validation renderer — full field capture + clean steps (#148)"
```

---

### Task 3: Verify against the real sample + CHANGELOG + version bump

**Files:**
- Modify: `CHANGELOG.md` (add entry under `[Unreleased]`)
- Verify only (no edit): the real sample engagement at
  `/Users/daveraffaele/Documents/Claude/Projects/assessment-test/sample-web-ecomm-agency/`

- [ ] **Step 1: Re-render the real sample PROC-001 and inspect**

```bash
PYTHONPATH=. python3.13 -m state.checkpoint_doc \
  /Users/daveraffaele/Documents/Claude/Projects/assessment-test/sample-web-ecomm-agency \
  process-validation
```

Then extract `word/document.xml` from the regenerated
`checkpoints/process-validation/PROC-001.docx` and confirm by inspection:
- Both decision points present; both exceptions present (no data loss).
- No literal `**`, `→`, or leading `- ` markers.
- Steps read as clean actions (no Green/Yellow/Red, no rationale).
- Decision points / Exceptions / Upstream-downstream render as `•` bullet lists.
- Baselines table and Sign-off intact; Conflicts / Chain scan / Challenge hypothesis absent.

(Verification step only — the sample lives outside the repo, so it is not a committed test. The committed coverage is `tests/test_doc_rendering.py`.)

- [ ] **Step 2: Add CHANGELOG entry**

Under `## [Unreleased]` add:

```markdown
### Fixed
- **Process-validation document quality (#148):** the per-process validation `.docx` renderer now captures full multi-item fields (Decision points / Exceptions no longer drop all but the first item), strips leaked step ratings (`— **Green/Yellow/Red** (…)`), and renders clean actions — closing the parity gap with the v2.25.1 checkpoint renderer.

### Added
- **List-aware document rendering (#148):** `docx.bullet_list` plus consecutive-list grouping in the shared markdown→blocks renderer — bulleted source renders as a real `•` list and numbered source as a numbered list across all checkpoint/review documents.
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: changelog for doc rendering quality (#148)"
```

---

## Self-Review

- **Spec coverage:** Part 1 (multi-bullet capture → Task 2 `_field_body`; step-rating strip → Task 2 `_steps`; marker-strip/run-on → Task 2 routes bodies through `blocks_from_markdown`). Part 2 (`bullet_list` → Task 1 docx; grouping → Task 1 `_grouped_line_blocks` + rewire; sharing without circular import → top-level import, justified in Global Constraints; no `md_blocks.py` per lazy-alternative). Acceptance criteria → tests in Tasks 1-2 + manual sample verify in Task 3.
- **Placeholder scan:** none — every code step has complete code.
- **Type consistency:** `_field_body` (new name, not `_field`) used consistently in Task 2 build_blocks; `bullet_list` factory + block type string `"bullet_list"` match between docx.py and `_grouped_line_blocks`; `_grouped_line_blocks` returns docx block dicts consumed by `blocks_from_markdown`/`prose_section`.
- **Regression guard:** Task 1 Step 6 and Task 2 Step 5 run the full suite; `prose_section` keeps returning its heading when body is present; adjacent-table split logic preserved verbatim.
