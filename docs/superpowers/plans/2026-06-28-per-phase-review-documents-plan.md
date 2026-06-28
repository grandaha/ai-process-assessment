# Per-Phase Review Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four offered, per-phase review documents (P3 tech-data, P5 opportunities, P8 use-case-briefs, P9 business-case) as deterministic Word docs on the #131 registry, and have the Conductor offer each at its phase boundary.

**Architecture:** Reuse #131 (`state/checkpoint_doc.py` registry/driver + `state/docx.py`). Add one prose+tables section builder (`full_section`), four registry entries with small `build` fns, and Conductor + building-checkpoint wiring. No new module.

**Tech Stack:** Python 3.12 **stdlib only** (`re`, `pathlib`); `state.docx`/`state.checkpoint_doc`. pytest.

**Spec:** `docs/superpowers/specs/2026-06-28-per-phase-review-documents-design.md` (#99).

## Global Constraints

- **Stdlib only**; **no fabrication** (every value copied from the phase source file).
- All four entries: `per_process=False`, `gate=False`, sign-off block included (recommended-and-recorded, NOT hard gates).
- Existing checkpoints unchanged; process-validation hard gate unchanged; Phase 11 deliverable + generate-artifact untouched.
- Ids: `tech-data`, `opportunities`, `use-case-briefs`, `business-case`. use-case-briefs = ONE combined doc.
- **Ponytail:** reuse existing builders; add only `full_section` (prose+tables) since tech-data/business-case sections carry tables that `prose_section` drops. Tests assert valid-zip + content, not byte-golden.

---

### Task 1: `full_section` builder (prose + tables) + fix prose_section bold-strip

**Files:** Modify `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_builders.py`

**Interfaces — Produces:** `full_section(title, md, heading) -> list[block]` (heading + the section's prose paragraphs AND any pipe-tables, in order); helper `blocks_from_markdown(text) -> list[block]`.

- [ ] **Step 1: Write the failing test**

```python
# add to state/tests/test_checkpoint_doc_builders.py
def test_full_section_renders_prose_and_tables():
    md = """## 3. Data asset catalog
Polaris holds operational truth.

| Asset | Sensitivity |
|---|---|
| Deliverables | High |

Shadow spreadsheets exist.
## 4. Next
other
"""
    blocks = cd.full_section("Data assets", md, "3. Data asset catalog")
    assert blocks[0] == {"type": "heading", "text": "Data assets", "level": 2}
    types = [b["type"] for b in blocks]
    assert "table" in types and "paragraph" in types          # both rendered
    tbl = next(b for b in blocks if b["type"] == "table")
    assert tbl["headers"] == ["Asset", "Sensitivity"] and tbl["rows"] == [["Deliverables", "High"]]
    paras = [b["text"] for b in blocks if b["type"] == "paragraph"]
    assert "Polaris holds operational truth." in paras and "Shadow spreadsheets exist." in paras
    assert "4. Next" not in repr(blocks)                       # stops at next section

def test_prose_section_keeps_bold_leader():
    md = "## S\n**Important:** do it.\n## T\n"
    blocks = cd.prose_section("S", md, "S")
    assert any(b["text"] == "**Important:** do it." for b in blocks)   # bold not stripped
```

- [ ] **Step 2: Run → FAIL.**
Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_checkpoint_doc_builders.py -k "full_section or bold_leader" -q`

- [ ] **Step 3: Implement** — add to `state/checkpoint_doc.py`:

```python
def blocks_from_markdown(text):
    """Render a markdown body as docx blocks: contiguous pipe-table lines become a table,
    other non-empty lines become paragraphs (leading bullet/number markers stripped)."""
    out, tbl = [], []
    def _flush():
        if tbl:
            h, r = md_table("\n".join(tbl))
            if h:
                out.append(docx.table(h, r))
            tbl.clear()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            tbl.append(s)
            continue
        _flush()
        s = re.sub(r"^[-*]\s+", "", s).strip()      # strip a bullet marker only, not **bold**
        if s:
            out.append(docx.paragraph(s))
    _flush()
    return out

def full_section(title, md, heading):
    body = md_section(md, heading)
    return [docx.heading(title, 2)] + blocks_from_markdown(body) if body else []
```

Also fix `prose_section`'s over-strip (the logged #131 minor): change its line
`s = line.strip().lstrip("-* ").strip()` to `s = re.sub(r"^[-*]\s+", "", line.strip()).strip()`.

- [ ] **Step 4: Run → PASS.** **Step 5: Commit** `feat(checkpoint-doc): full_section (prose+tables) builder + fix prose bold-strip (#99)`

---

### Task 2: `tech-data` entry (P3)

**Files:** Modify `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_driver.py`

- [ ] **Step 1: Write the failing test**

```python
def test_tech_data_doc_renders_sections_excludes_contract_notes(tmp_path):
    (tmp_path / "tech-inventory.md").write_text(
        "# Technology & Data Inventory\n"
        "## 1. System inventory\nPolaris PSA is the system of record.\n"
        "## 3. Data asset catalog\n| Asset | Sensitivity |\n|---|---|\n| Deliverables | High |\n"
        "## Phase-3 input-contract notes\nINTERNAL: do not show the client.\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "tech-data")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-tech-data.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Polaris PSA" in xml and "Deliverables" in xml and "High" in xml
    assert "INTERNAL: do not show" not in xml and "input-contract" not in xml.lower()
    assert "Confirmed" in xml                                  # sign-off present
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `state/checkpoint_doc.py`:

```python
_TECH_EXCLUDE = ("phase-3 input-contract notes",)

def _build_tech_data(root):
    md = _read(root, "tech-inventory.md")
    blocks = [docx.heading("Technology & Data Inventory — For Your Confirmation", 1)]
    blocks += note("Please confirm your systems and data-sensitivity classifications are "
                   "captured correctly — these drive the downstream governance review.")
    for m in re.finditer(r"^##\s+(.+?)\s*$", md, re.MULTILINE):
        title = m.group(1).strip()
        if any(x in title.lower() for x in _TECH_EXCLUDE):
            continue
        blocks += full_section(title, md, title)
    blocks += signoff_block("IT lead / sponsor")
    return blocks

CHECKPOINTS["tech-data"] = Checkpoint(
    "tech-data", per_process=False, gate=False,
    output="checkpoints/checkpoint-tech-data.docx",
    outcome="checkpoints/CP-tech-data-outcome.md", build=_build_tech_data)
```

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): tech-data review entry (#99)`

---

### Task 3: `opportunities` entry (P5)

**Files:** Modify `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_driver.py`

- [ ] **Step 1: Write the failing test**

```python
def test_opportunities_doc_renders_landscape(tmp_path):
    (tmp_path / "opportunities").mkdir()
    (tmp_path / "opportunities" / "_index.md").write_text(
        "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
        "|--------|---------|------|-------------|----------------|-----|------------|\n"
        "| OPP-001 | PROC-003 | ChainAutomation | Yellow | Green | Green | addressing-root |\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "opportunities")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-opportunities.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "OPP-001" in xml and "ChainAutomation" in xml and "Confirmed" in xml
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `state/checkpoint_doc.py`:

```python
def _build_opportunities(root):
    h, r = md_table(_read(root, "opportunities/_index.md"))
    blocks = [docx.heading("Opportunity Landscape — For Your Review", 1)]
    blocks += note("Here are the opportunities we identified. Tell us if any are missing or "
                   "mischaracterized before we score and prioritize them.")
    blocks += table_section("Opportunities", h, r)
    blocks += signoff_block("Sponsor / decision-maker")
    return blocks

CHECKPOINTS["opportunities"] = Checkpoint(
    "opportunities", per_process=False, gate=False,
    output="checkpoints/checkpoint-opportunities.docx",
    outcome="checkpoints/CP-opportunities-outcome.md", build=_build_opportunities)
```

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): opportunities review entry (#99)`

---

### Task 4: `use-case-briefs` entry (P8, one combined doc)

**Files:** Modify `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_driver.py`

- [ ] **Step 1: Write the failing test**

```python
def test_use_case_briefs_doc_has_index_and_per_brief(tmp_path):
    d = tmp_path / "usecase-briefs"; d.mkdir()
    (d / "_index.md").write_text(
        "# Use-Case Briefs\n## UC ↔ OPP mapping\n"
        "| UC-NNN | Title | Wave |\n|---|---|---|\n| UC-001 | Status Assistant | 1 |\n")
    (d / "UC-001.md").write_text(
        "# UC-001 — Status Assistant\n\n| Field | Value |\n|---|---|\n"
        "| Opportunity type | Chain Automation |\n## Situation\nThe PM assembles reports.\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "use-case-briefs")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-use-case-briefs.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "UC-001" in xml and "Status Assistant" in xml          # index + brief title
    assert "Chain Automation" in xml                              # per-brief field table
    assert "Confirmed" in xml
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `state/checkpoint_doc.py`:

```python
def _build_use_case_briefs(root):
    idx = _read(root, "usecase-briefs/_index.md")
    blocks = [docx.heading("Use-Case Briefs — For Your Review", 1)]
    blocks += note("These are the packaged use cases. Confirm each reflects how the work really "
                   "happens, or note corrections.")
    h, r = md_table(idx)                                  # the UC↔OPP mapping table
    blocks += table_section("Brief index", h, r)
    for uc in sorted((Path(root) / "usecase-briefs").glob("UC-*.md")):
        text = uc.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
        title = m.group(1).strip() if m else uc.stem
        th, tr = md_table(text)                           # first table = the Field/Value summary
        blocks += [docx.heading(title, 2)]
        blocks += table_section("", th, tr) if tr else []
    blocks += signoff_block("Sponsor / process owners")
    return blocks

CHECKPOINTS["use-case-briefs"] = Checkpoint(
    "use-case-briefs", per_process=False, gate=False,
    output="checkpoints/checkpoint-use-case-briefs.docx",
    outcome="checkpoints/CP-use-case-briefs-outcome.md", build=_build_use_case_briefs)
```

Note: `table_section("", th, tr)` emits an empty heading then the table; if that reads oddly,
the implementer may pass the title through instead — but keep the Field/Value table rendered.

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): use-case-briefs review entry (#99)`

---

### Task 5: `business-case` entry (P9)

**Files:** Modify `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_driver.py`

- [ ] **Step 1: Write the failing test**

```python
def test_business_case_doc_renders_sections_and_cost_table(tmp_path):
    (tmp_path / "business-case.md").write_text(
        "# Wave 1 ROM Business Case\n"
        "## The decision this supports\nFund the quick win first.\n"
        "## 2. Per-initiative cost structure\n"
        "| Cost category | Estimate |\n|---|---|\n| Implementation labor | $111,000 |\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "business-case")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-business-case.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Fund the quick win first." in xml and "$111,000" in xml   # prose + cost table
    assert "Confirmed" in xml
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `state/checkpoint_doc.py`:

```python
def _build_business_case(root):
    md = _read(root, "business-case.md")
    blocks = [docx.heading("Business Case — For Your Review", 1)]
    blocks += note("Confirm the cost and value figures and the funding recommendation, or tell "
                   "us what to revisit.")
    for m in re.finditer(r"^##\s+(.+?)\s*$", md, re.MULTILINE):
        title = m.group(1).strip()
        blocks += full_section(title, md, title)
    blocks += signoff_block("Decision-maker / sponsor")
    return blocks

CHECKPOINTS["business-case"] = Checkpoint(
    "business-case", per_process=False, gate=False,
    output="checkpoints/checkpoint-business-case.docx",
    outcome="checkpoints/CP-business-case-outcome.md", build=_build_business_case)
```

- [ ] **Step 4: PASS (then full suite). Step 5: Commit** `feat(checkpoint-doc): business-case review entry (#99)`

---

### Task 6: register the 4 ids + Conductor offers them at phase boundaries

**Files:** Modify `skills/building-checkpoint/SKILL.md`, `skills/conducting-engagement/SKILL.md`; Test `tests/test_per_phase_review_docs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_per_phase_review_docs.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
CP = (REPO / "skills" / "building-checkpoint" / "SKILL.md").read_text()
COND = (REPO / "skills" / "conducting-engagement" / "SKILL.md").read_text()
IDS = ["tech-data", "opportunities", "use-case-briefs", "business-case"]

def test_building_checkpoint_wires_new_ids():
    for i in IDS:
        assert i in CP, f"building-checkpoint missing wired id {i}"

def test_conductor_offers_new_docs_at_phase_boundaries():
    for i in IDS:
        assert i in COND, f"conductor missing offer for {i}"
    # offered, not gated: these must not be described as blocking/hard gates
    assert "offer" in COND.lower()
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement**
  - `building-checkpoint/SKILL.md` Session Start: add `tech-data`, `opportunities`, `use-case-briefs`, `business-case` to the wired-values list, and predecessor checks: `tech-data`→`tech-inventory.md`; `opportunities`→`opportunities/_index.md`; `use-case-briefs`→`usecase-briefs/_index.md`; `business-case`→`business-case.md`. (Routing already general.)
  - `conducting-engagement/SKILL.md`: extend the checkpoint-insertion list (the should-confirm "offer to generate it" step) so the Conductor **offers** the review doc at the end of Phase 3 (`tech-data`), Phase 5 (`opportunities`), Phase 8 (`use-case-briefs`), and Phase 9 (`business-case`). State they are **offered, opt-in, recommended-and-recorded — not hard gates** (only process-validation gates). Add a jargon-free narration line, e.g.:
    > Want a short write-up of what we just captured that you can share or confirm? Totally optional.

- [ ] **Step 4: Run → PASS, then full suite.** **Step 5: Commit** `feat(conductor): offer per-phase review docs at P3/P5/P8/P9 (#99)`

---

### Task 7: CHANGELOG

**Files:** Modify `CHANGELOG.md`

- [ ] **Step 1:** Under `## [Unreleased]`:

```markdown
### Added
- **Per-phase review documents** (#99). The Conductor now offers an optional, client-facing
  Word review doc at four more phase boundaries — tech & data (P3, IT confirms the systems +
  data-sensitivity that drive governance), opportunity landscape (P5), use-case briefs (P8),
  and business case (P9). Each renders deterministically from the phase's source files (on the
  #131 registry) with a sign-off block; offered/opt-in, not gates. Foundation #99 now lets a new
  per-phase artifact be added as a registry entry.
```

- [ ] **Step 2:** Run full suite → PASS. **Step 3: Commit** `docs(changelog): per-phase review documents (#99)`

---

## Self-Review
- **Spec coverage:** full_section builder (T1), the 4 entries (T2-5), building-checkpoint wiring + Conductor offer (T6), CHANGELOG (T7). tech-data exclusion (T2 test); business-case tables (T5 test); use-case-briefs combined doc (T4). ✓
- **Placeholders:** none — runnable code/commands throughout.
- **Type consistency:** `full_section(title, md, heading)`, `blocks_from_markdown(text)`, `Checkpoint(id, per_process, gate, output, outcome, build)`, `build(root)->blocks` — consistent with #131. Reused builders: `md_table`, `table_section`, `note`, `signoff_block`, `_read`.
- **Ponytail:** one new builder only; entries are small build fns; fixed the #131 prose bold-strip minor while in the file; valid-zip+content tests.
