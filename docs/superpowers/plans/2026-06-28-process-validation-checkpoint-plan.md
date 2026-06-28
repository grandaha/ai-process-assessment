# Process-Validation Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-process, owner-facing **current-state process-validation checkpoint** after Phase 4 that emits one editable Word `.docx` per in-scope process and hard-gates Phase 5 on per-process sign-off.

**Architecture:** A stdlib `.docx` generator (`state/docx.py`) + a pure PROC→blocks transform & batch renderer (`state/process_review.py`); `building-checkpoint` gets a deterministic `process-validation` branch that runs the renderer (no LLM, no HTML shell, no Gate B); a new gate in `state.py`/`phases.py` that the Conductor checks before Phase 5.

**Tech Stack:** Python 3.12 **standard library only** (`zipfile`, `re`, `xml.sax.saxutils`). pytest.

**Spec:** `docs/superpowers/specs/2026-06-26-process-validation-checkpoint-design.md` (#136).

## Global Constraints

- **Stdlib only** — no third-party deps (the engine/state core runs in any sandbox). Verified by `tests/test_branding.py`-style import discipline; `requirements.txt` unchanged.
- **No fabrication** — every rendered field traces verbatim to `processes/PROC-NNN.md`. The renderer is a transform, not an author.
- **Exclude internal analysis** from the owner doc: per-step color notes (`→ Yellow/Red — …`), **Conflicts**, **Chain scan**, **Challenge hypothesis**.
- **Ponytail deviations from spec** (smaller, deliberate):
  - Block types limited to `heading`/`paragraph`/`numbered_list`/`table` (spec also listed bullet_list/signoff — sign-off renders as heading+paragraphs; no bullet_list needed).
  - Baselines read from the **PROC file's own `### Baselines` table**, not `model/baselines.json` (single source; it's a read-only context block, not a computed figure).
  - Tests assert **valid-zip + content**, not byte-identical golden (`zipfile` stamps mtime; byte-stability isn't worth a custom ZipInfo). Spec's "byte-stable" → "content-stable".

---

### Task 1: `state/docx.py` — minimal stdlib .docx generator

**Files:**
- Create: `state/docx.py`
- Test: `state/tests/test_docx.py`

**Interfaces:**
- Produces: `build_docx(blocks: list[dict], out_path: str) -> str`; builders `heading(text, level=1)`, `paragraph(text)`, `numbered_list(items)`, `table(headers, rows)` returning block dicts.
- Block dict shapes: `{"type":"heading","text":str,"level":int}`, `{"type":"paragraph","text":str}`, `{"type":"numbered_list","items":[str]}`, `{"type":"table","headers":[str],"rows":[[str]]}`.

- [ ] **Step 1: Write the failing test**

```python
# state/tests/test_docx.py
import zipfile
from xml.etree import ElementTree as ET
from state import docx

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def _document_xml(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        assert {"[Content_Types].xml", "_rels/.rels",
                "word/document.xml", "word/styles.xml"} <= names
        return z.read("word/document.xml").decode("utf-8")

def test_build_docx_valid_and_has_content(tmp_path):
    out = tmp_path / "x.docx"
    blocks = [
        docx.heading("Title", 1),
        docx.paragraph("Hello <world> & co"),   # must be XML-escaped
        docx.numbered_list(["first", "second"]),
        docx.table(["A", "B"], [["1", "2"]]),
    ]
    docx.build_docx(blocks, str(out))
    xml = _document_xml(str(out))
    ET.fromstring(xml)                       # parses = well-formed
    assert "Hello &lt;world&gt; &amp; co" in xml
    assert "1. first" in xml and "2. second" in xml
    assert xml.count(f"{W}tbl") >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_docx.py -q`
Expected: FAIL (`ModuleNotFoundError: state.docx`).

- [ ] **Step 3: Write minimal implementation**

```python
# state/docx.py — minimal stdlib .docx (WordprocessingML) generator. No third-party deps.
# ponytail: only the block types the process review needs; add more when a caller needs them.
# ponytail: numbered_list renders as "N. text" paragraphs — avoids the fiddly numbering.xml part.
import zipfile
from xml.sax.saxutils import escape

_CT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

_DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

_STYLES = ('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DM Sans" w:hAnsi="DM Sans"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'''
 + ''.join(
     f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
     f'<w:pPr><w:outlineLvl w:val="{n-1}"/></w:pPr>'
     f'<w:rPr><w:b/><w:color w:val="1B75BC"/><w:sz w:val="{sz}"/></w:rPr></w:style>'
     for n, sz in ((1, 36), (2, 28), (3, 24)))
 + '</w:styles>')

_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

def _p(text, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

def _tbl(headers, rows):
    def _row(cells, bold=False):
        b = '<w:rPr><w:b/></w:rPr>' if bold else ''
        tcs = ''.join(
            f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>'
            f'<w:p><w:r>{b}<w:t xml:space="preserve">{escape(str(c))}</w:t></w:r></w:p></w:tc>'
            for c in cells)
        return f'<w:tr>{tcs}</w:tr>'
    borders = '<w:tblBorders>' + ''.join(
        f'<w:{s} w:val="single" w:sz="4" w:color="CCCCCC"/>'
        for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + '</w:tblBorders>'
    return (f'<w:tbl><w:tblPr>{borders}</w:tblPr>'
            + _row(headers, bold=True) + ''.join(_row(r) for r in rows) + '</w:tbl>')

def _block(b):
    t = b["type"]
    if t == "heading":
        return _p(b["text"], style=f'Heading{b.get("level", 1)}')
    if t == "paragraph":
        return _p(b["text"])
    if t == "numbered_list":
        return ''.join(_p(f"{i}. {item}") for i, item in enumerate(b["items"], 1))
    if t == "table":
        return _tbl(b["headers"], b["rows"])
    raise ValueError(f"unknown block type: {t}")

def build_docx(blocks, out_path):
    body = ''.join(_block(b) for b in blocks)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document {_NS}><w:body>{body}'
                '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr></w:body></w:document>')
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/document.xml", document)
    return out_path

def heading(text, level=1): return {"type": "heading", "text": text, "level": level}
def paragraph(text): return {"type": "paragraph", "text": text}
def numbered_list(items): return {"type": "numbered_list", "items": list(items)}
def table(headers, rows): return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_docx.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add state/docx.py state/tests/test_docx.py
git commit -m "feat(docx): minimal stdlib .docx generator (#136)"
```

---

### Task 2: `state/process_review.py` — PROC→blocks transform + batch renderer

**Files:**
- Create: `state/process_review.py`
- Test: `state/tests/test_process_review.py`

**Interfaces:**
- Consumes: `state.docx` (Task 1).
- Produces:
  - `build_blocks(proc_md: str) -> list[dict]` — pure transform of one PROC file's text.
  - `render_all(engagement_dir: str) -> list[str]` — reads `processes/_index.md`, for each `Ready` process reads `processes/PROC-NNN.md`, writes `checkpoints/process-validation/PROC-NNN.docx` and (if absent) `checkpoints/process-validation/CP-PROC-NNN-outcome.md` with `Outcome: Pending`; returns the list of PROC ids rendered.
  - `__main__`: `python3 -m state.process_review <engagement_dir>` calls `render_all`.

- [ ] **Step 1: Write the failing test**

```python
# state/tests/test_process_review.py
from state import process_review as pr

PROC = """## PROC-001 — Staffing & Resource Assignment
<!-- index: baseline=Ready -->

**Trigger:** A project is won and a staffing request enters the queue.

### Process Map

**Steps:**
1. EM submits a staffing request. → Yellow — intake is unstructured.
2. Analyst checks the Grid for availability. → Red — shadow Excel.

**Actors:** RMO analyst, engagement manager.
**Decision points:** Candidate selection (judgment-heavy).
**Exceptions:** Double-bookings.
**Upstream / downstream:** Upstream won deals; downstream delivery.
**Conflicts:** Conflict B — rework rate.
**Chain scan:** Low chain potential.
**Challenge hypothesis:** Actor model is sound; the real constraint is data freshness.

### Baselines

| Field | Value | Source | Confidence |
|---|---|---|---|
| Volume | ~140/mo | Priya | Medium |
| FTE effort | 3.5 | RMO estimate | Medium |
"""

def test_build_blocks_includes_owner_fields_strips_color_notes():
    blocks = pr.build_blocks(PROC)
    text = "\n".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "PROC-001" in text and "Staffing & Resource Assignment" in text
    assert "A project is won" in text                      # trigger
    assert "EM submits a staffing request." in text        # step text kept
    assert "Yellow" not in text and "intake is unstructured" not in text  # color note stripped
    assert "RMO analyst" in text                           # actors
    assert "Candidate selection" in text                   # decision points
    assert "Double-bookings" in text                       # exceptions

def test_build_blocks_excludes_internal_analysis():
    text = repr(pr.build_blocks(PROC))
    assert "Challenge hypothesis" not in text and "data freshness" not in text
    assert "Chain scan" not in text and "Conflict B" not in text

def test_build_blocks_baselines_table_present():
    blocks = pr.build_blocks(PROC)
    tbls = [b for b in blocks if b["type"] == "table"]
    flat = repr(tbls)
    assert "Volume" in flat and "~140/mo" in flat and "FTE effort" in flat

def test_build_blocks_has_signoff():
    text = repr(pr.build_blocks(PROC))
    assert "Sign-off" in text and "Confirmed" in text and "Changes requested" in text

def test_render_all_writes_docx_and_outcome_per_ready_process(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | Staffing | Ready |\n| PROC-002 | Held | Pending |\n")
    (tmp_path / "processes" / "PROC-001.md").write_text(PROC)
    ids = pr.render_all(str(tmp_path))
    assert ids == ["PROC-001"]                              # only Ready ones
    cp = tmp_path / "checkpoints" / "process-validation"
    assert (cp / "PROC-001.docx").exists()
    assert (cp / "CP-PROC-001-outcome.md").exists()
    assert "Outcome: Pending" in (cp / "CP-PROC-001-outcome.md").read_text()

def test_render_all_does_not_clobber_existing_outcome(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n| PROC-001 | Staffing | Ready |\n")
    (tmp_path / "processes" / "PROC-001.md").write_text(PROC)
    cp = tmp_path / "checkpoints" / "process-validation"; cp.mkdir(parents=True)
    (cp / "CP-PROC-001-outcome.md").write_text("Outcome: Confirmed\n")
    pr.render_all(str(tmp_path))
    assert "Confirmed" in (cp / "CP-PROC-001-outcome.md").read_text()  # preserved
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_process_review.py -q`
Expected: FAIL (`ModuleNotFoundError: state.process_review`).

- [ ] **Step 3: Write minimal implementation**

```python
# state/process_review.py — render per-process current-state owner-review .docx (#136).
# Pure transform + batch renderer. Stdlib only. No fabrication: every field is copied
# from the PROC file; internal analysis (color notes, conflicts, chain scan, challenge
# hypothesis) is deliberately excluded — see #136 spec.
import re
import sys
from pathlib import Path

from state import docx

# Owner-facing single-line fields, in render order. (Conflicts/Chain scan/Challenge
# hypothesis are intentionally absent.)
_FIELDS = [("Trigger", "Trigger"),
           ("Actors", "Actors"),
           ("Decision points", "Decision points"),
           ("Exceptions", "Exceptions"),
           ("Upstream / downstream", "Upstream / downstream")]

def _field(md, label):
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else None

def _title(md):
    m = re.search(r"^##\s*(PROC-\d+)\s*[—-]\s*(.+)$", md, re.MULTILINE)
    return (m.group(1), m.group(2).strip()) if m else ("PROC-???", "Process")

def _steps(md):
    # numbered lines under "**Steps:**" up to the next blank line / bold label;
    # strip the internal "→ …" color note from each.
    block = re.search(r"\*\*Steps:\*\*\s*\n(.*?)(?:\n\s*\n|\n\*\*)", md, re.DOTALL)
    if not block:
        return []
    out = []
    for line in block.group(1).splitlines():
        m = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if m:
            out.append(m.group(1).split(" → ")[0].strip())   # drop color note
    return out

def _baselines(md):
    # rows of the "### Baselines" table → [(Field, Value)] (drop Source/Confidence cols).
    sec = md.split("### Baselines", 1)
    if len(sec) < 2:
        return []
    rows = []
    for line in sec[1].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[0] != "Field" and not cells[0].startswith("---"):
            rows.append([cells[0], cells[1]])
    return rows

def build_blocks(proc_md):
    pid, name = _title(proc_md)
    blocks = [docx.heading(f"{pid} — {name}", 1),
              docx.paragraph("Please review the current-state capture of this process below "
                             "and confirm it is accurate, or note what should change.")]
    trigger = _field(proc_md, "Trigger")
    if trigger:
        blocks += [docx.heading("Trigger", 2), docx.paragraph(trigger)]
    steps = _steps(proc_md)
    if steps:
        blocks += [docx.heading("Steps", 2), docx.numbered_list(steps)]
    for label, _ in _FIELDS[1:]:                              # Actors..Upstream/downstream
        val = _field(proc_md, label)
        if val:
            blocks += [docx.heading(label, 2), docx.paragraph(val)]
    bl = _baselines(proc_md)
    if bl:
        blocks += [docx.heading("Baseline figures (for context)", 2),
                   docx.table(["Field", "Value"], bl)]
    blocks += [docx.heading("Sign-off", 2),
               docx.paragraph("Process owner: ______________________"),
               docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
               docx.paragraph("Comments:")]
    return blocks

def _ready_processes(index_md):
    out = []
    for line in index_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("PROC-") and cells[2].lower() == "ready":
            out.append(cells[0])
    return out

def render_all(engagement_dir):
    root = Path(engagement_dir)
    index = root / "processes" / "_index.md"
    ids = _ready_processes(index.read_text(encoding="utf-8")) if index.exists() else []
    out_dir = root / "checkpoints" / "process-validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    for pid in ids:
        proc = root / "processes" / f"{pid}.md"
        if not proc.exists():
            continue
        docx.build_docx(build_blocks(proc.read_text(encoding="utf-8")),
                        str(out_dir / f"{pid}.docx"))
        outcome = out_dir / f"CP-{pid}-outcome.md"
        if not outcome.exists():
            outcome.write_text(f"# {pid} — process validation outcome\n\nOutcome: Pending\n"
                               "<!-- set to: Confirmed | Changes requested | Waived (reason) -->\n",
                               encoding="utf-8")
    return ids

if __name__ == "__main__":
    print("\n".join(render_all(sys.argv[1])))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_process_review.py -q`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add state/process_review.py state/tests/test_process_review.py
git commit -m "feat(process-review): per-process owner-review .docx renderer (#136)"
```

---

### Task 3: Wire `process-validation` into `building-checkpoint`

**Files:**
- Modify: `skills/building-checkpoint/SKILL.md`
- Test: `tests/test_process_validation_checkpoint.py`

**Interfaces:**
- Consumes: `state.process_review.render_all` via CLI (Task 2).
- Produces: registry row + a deterministic orchestration branch the Conductor invokes.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_process_validation_checkpoint.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
SKILL = (REPO / "skills" / "building-checkpoint" / "SKILL.md").read_text(encoding="utf-8")

def test_registry_has_process_validation_row():
    assert "process-validation" in SKILL
    assert "checkpoints/process-validation/PROC-NNN.docx" in SKILL

def test_process_validation_is_deterministic_path():
    # It must run the renderer module, NOT the LLM section-renderer / HTML-shell path.
    assert "state.process_review" in SKILL
    assert "section-renderer-checkpoint-process-validation" not in SKILL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest tests/test_process_validation_checkpoint.py -q`
Expected: FAIL (strings absent).

- [ ] **Step 3: Add the registry row + deterministic branch**

In `skills/building-checkpoint/SKILL.md`, add this row to the Checkpoint Registry table (after the `baseline` row):

```
| `process-validation` | Phase 4 (before `baseline`) | Process owner (one per process) | `processes/_index.md`, `processes/PROC-NNN.md` | *(deterministic — `state.process_review`, no LLM renderer)* | `checkpoints/process-validation/PROC-NNN.docx` (one per process) | `checkpoints/process-validation/CP-PROC-NNN-outcome.md` (one per process) | Phase 4 (`ai-process-assessment:discovering-processes`) for the affected process |
```

Add this section after `## Orchestration`:

```markdown
## Deterministic checkpoint: `process-validation`

`process-validation` is a **per-process, owner-facing Word checkpoint** and does NOT use the
section-renderer / HTML-shell / Gate-B path above. It is a faithful transform of the process
maps (no model-authored content, so nothing to gate for fabrication). For this id only:

1. Run: `PYTHONPATH="<engine_root>" python3 -m state.process_review <name>`
   — writes one `checkpoints/process-validation/PROC-NNN.docx` and one
   `CP-PROC-NNN-outcome.md` (Outcome: Pending) per in-scope (`Ready`) process.
2. Tell the user a per-process Word review was generated for each process owner to confirm or
   mark up, and that **each owner's sign-off must be recorded** in its `CP-PROC-NNN-outcome.md`
   (`Confirmed` | `Changes requested` | `Waived (reason)`) before Phase 5.
3. On any `Changes requested`, route that process back to Phase 4, re-run, and regenerate
   (re-run the command — it preserves existing outcome files).
```

- [ ] **Step 4: Run test to verify it passes**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest tests/test_process_validation_checkpoint.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/building-checkpoint/SKILL.md tests/test_process_validation_checkpoint.py
git commit -m "feat(checkpoint): wire deterministic process-validation checkpoint (#136)"
```

---

### Task 4: Hard gate — block Phase 5 until per-process sign-off

**Files:**
- Modify: `state/phases.py` (add the gate to `GATES`)
- Modify: `state/state.py` (`_gate_status` reports it)
- Modify: `skills/conducting-engagement/SKILL.md` (drive loop checks it before Phase 5)
- Test: `state/tests/test_process_validation_gate.py`, and add one guard to `tests/test_guards.py`

**Interfaces:**
- Consumes: `processes/_index.md`, `checkpoints/process-validation/CP-PROC-NNN-outcome.md`.
- Produces: a `{"id":"process-validation", ...}` entry in `read_state(...)["gates"]` with status `required` | `done` | `not-required`.

- [ ] **Step 1: Write the failing test**

```python
# state/tests/test_process_validation_gate.py
from pathlib import Path
from state.state import read_state

def _gate(root):
    return next(g for g in read_state(root)["gates"] if g["id"] == "process-validation")

def _scaffold(tmp_path, outcomes):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | A | Ready |\n| PROC-002 | B | Ready |\n")
    cp = tmp_path / "checkpoints" / "process-validation"; cp.mkdir(parents=True)
    for pid, val in outcomes.items():
        (cp / f"CP-{pid}-outcome.md").write_text(f"Outcome: {val}\n")

def test_required_when_an_outcome_is_pending(tmp_path):
    _scaffold(tmp_path, {"PROC-001": "Confirmed", "PROC-002": "Pending"})
    assert _gate(str(tmp_path))["status"] == "required"

def test_done_when_all_confirmed_or_waived(tmp_path):
    _scaffold(tmp_path, {"PROC-001": "Confirmed", "PROC-002": "Waived (owner OOO)"})
    assert _gate(str(tmp_path))["status"] == "done"

def test_not_required_when_no_ready_processes(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n")
    assert _gate(str(tmp_path))["status"] == "not-required"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_process_validation_gate.py -q`
Expected: FAIL (no `process-validation` gate in `gates`).

- [ ] **Step 3: Implement the gate**

In `state/phases.py`, append to the `GATES` list:

```python
    Gate("process-validation", "Process Validation (owner sign-off)", "checkpoints/process-validation/"),
```

In `state/state.py`, inside `_gate_status`, before the final `return`, add:

```python
    # Process-validation gate — per-process owner sign-off before Phase 5.
    pv_index = root / "processes" / "_index.md"
    pv_ready = []
    if pv_index.exists():
        for line in pv_index.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0].startswith("PROC-") and cells[2].lower() == "ready":
                pv_ready.append(cells[0])
    if not pv_ready:
        pv = {"status": "not-required", "reason": None}
    else:
        pending = []
        for pid in pv_ready:
            f = root / "checkpoints" / "process-validation" / f"CP-{pid}-outcome.md"
            txt = f.read_text(encoding="utf-8").lower() if f.exists() else ""
            if not ("outcome: confirmed" in txt or "outcome: waived" in txt):
                pending.append(pid)
        pv = ({"status": "done", "reason": "all process owners signed off"} if not pending
              else {"status": "required",
                    "reason": f"{len(pending)} process(es) awaiting owner sign-off"})
```

And add to the returned list (after the `grc` entry):

```python
        {"id": "process-validation", "name": GATES[2].name, "output": GATES[2].output, **pv},
```

(`GATES[2]` is the new entry; `deliverable` is now `GATES[1]` still — keep its dict using `GATES[1]`.)

In `skills/conducting-engagement/SKILL.md`, drive-loop step 4 (next-step selection), add before entering Phase 5:

```markdown
**Before Phase 5 (opportunity identification):** check the `process-validation` gate in the
`state.state` snapshot's `gates` array. If `status == "required"`, you may not start Phase 5 —
run `ai-process-assessment:building-checkpoint` (checkpoint `process-validation`) and get each
process owner's sign-off recorded (`Confirmed` or `Waived (reason)`; a `Waived` is a must-ask
operator decision) in `checkpoints/process-validation/CP-PROC-NNN-outcome.md`. A
`Changes requested` routes that process back to Phase 4. This mirrors how the GRC gate blocks
Phase 6.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_process_validation_gate.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Add a drive-loop guard + run full suite**

Add to `tests/test_guards.py`:

```python
def test_conductor_gates_phase5_on_process_validation(methodology):
    body = methodology.skills["ai-process-assessment:conducting-engagement"].body
    assert "process-validation` gate" in body or "`process-validation`" in body, \
        "Conductor must check the process-validation gate before Phase 5 (#136)"
    assert "Before Phase 5" in body, "Conductor must block Phase 5 on owner sign-off (#136)"
```

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest -q`
Expected: PASS (full suite).

- [ ] **Step 6: Commit**

```bash
git add state/phases.py state/state.py skills/conducting-engagement/SKILL.md state/tests/test_process_validation_gate.py tests/test_guards.py
git commit -m "feat(gate): block Phase 5 until per-process owner sign-off (#136)"
```

---

### Task 5: CHANGELOG

**Files:** Modify `CHANGELOG.md`

- [ ] **Step 1: Add under `## [Unreleased]`**

```markdown
### Added
- **Current-state process-validation checkpoint** (#136). A new per-process, owner-facing
  checkpoint after Phase 4 emits one editable Word (`.docx`) per in-scope process — the
  step-by-step current-state map for that owner to confirm — and **hard-gates Phase 5** until
  every process has a recorded sign-off. Includes a stdlib-only `.docx` generator
  (`state/docx.py`) reusable by #131.
```

- [ ] **Step 2: Run full suite, commit**

```bash
~/Developer/ai-process-assessment/.venv/bin/python -m pytest -q
git add CHANGELOG.md
git commit -m "docs(changelog): process-validation checkpoint (#136)"
```

---

## Self-Review

- **Spec coverage:** docx generator (T1), PROC→blocks transform + per-process render + outcome stubs (T2), checkpoint wiring deterministic/per-process (T3), hard gate before Phase 5 + route-back (T4), CHANGELOG (T5). ✓ Excluded-analysis requirement covered by T2 tests + the transform. The spec's "anti-regression guard that the .docx excludes internal markers" is satisfied by `test_build_blocks_excludes_internal_analysis` (blocks-level, which is what the docx is built from).
- **Placeholder scan:** none — every code step is complete.
- **Type consistency:** `build_docx(blocks, out_path)`, `build_blocks(md)`, `render_all(dir)`, block dict shapes, and the gate dict id `process-validation` are consistent across tasks. `GATES` indices: grc=0, deliverable=1, process-validation=2 (state.py references updated accordingly).
- **Ponytail deviations** from spec are listed in Global Constraints (block-type trim, baselines from PROC file, content-stable not byte-stable, skip Gate-B for this deterministic checkpoint). All reduce code without losing a requirement.
