# Deterministic Checkpoint Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all interim checkpoints deterministic Word (`.docx`) documents rendered from a declarative registry + thin shared layer, replacing the LLM-authored HTML path; fold #136's process-validation into the same layer.

**Architecture:** `state/checkpoint_doc.py` holds markdown helpers + section builders (on `state/docx.py`), a `CHECKPOINTS` registry of `Checkpoint` dataclasses (each with a small `build` fn composing the builders), and one `render_checkpoint(dir, id)` driver. `building-checkpoint` routes every id through `python3 -m state.checkpoint_doc`. The 3 section-renderer agents, the checkpoint HTML shell, and deliverable-gate Checkpoint Mode are deleted.

**Tech Stack:** Python 3.12 **standard library only** (`re`, `pathlib`, `dataclasses`); `state/docx.py`. pytest.

**Spec:** `docs/superpowers/specs/2026-06-28-deterministic-checkpoint-documents-design.md` (#131).

## Global Constraints

- **Stdlib only** — no new deps.
- **No fabrication** — every rendered value is copied verbatim from a source file.
- **scope checkpoint exclusions (CP1 guard):** never render risk posture, AI/automation maturity, or political landscape.
- **Phase 11 `deliverable.html` is untouched.** This is interim checkpoints only.
- **process-validation keeps its hard gate** (from #136); scope/baseline/portfolio stay recommended-and-recorded.
- **Ponytail:** the registry uses function-refs (each checkpoint a small `build` fn), not a string-descriptor interpreter. Reuse #136's `state/process_review.build_blocks` for process-validation; do not rewrite it. Tests assert valid-zip + content, not byte-golden.

## File structure
- `state/checkpoint_doc.py` (new) — helpers + builders + registry + driver + CLI.
- `state/process_review.py` (modify) — keep `build_blocks`; remove now-superseded `render_all`/`__main__`.
- `skills/building-checkpoint/SKILL.md` (modify) — route all ids through the deterministic command; drop HTML shell.
- `skills/deliverable-gate/SKILL.md` (modify) — remove Checkpoint Mode.
- `agents/section-renderer-checkpoint-{scope,baseline,portfolio}.md` (delete).
- `tests/` + `state/tests/` — new + updated guards.

---

### Task 1: `checkpoint_doc.py` — markdown helpers + section builders

**Files:** Create `state/checkpoint_doc.py`; Test `state/tests/test_checkpoint_doc_builders.py`

**Interfaces — Produces:**
- `md_field(md, label) -> str|None`, `md_section(md, heading) -> str|None`, `md_table(md, after_heading=None) -> (headers, rows)`
- `field_section(title, md, label) -> list[block]`, `prose_section(title, md, heading) -> list[block]`, `table_section(title, headers, rows) -> list[block]`, `note(text) -> list[block]`, `signoff_block(reviewer_label="Reviewer") -> list[block]`

- [ ] **Step 1: Write the failing test**

```python
# state/tests/test_checkpoint_doc_builders.py
from state import checkpoint_doc as cd

MD = """**Client:** Lattice Consulting Group
# Title
## Sponsoring question
Which initiative should we fund?

Second para.
## Out-of-scope boundaries
| Excluded | Rationale |
|---|---|
| Sales | Different org. |
"""

def test_md_field():
    assert cd.md_field(MD, "Client") == "Lattice Consulting Group"
    assert cd.md_field(MD, "Nope") is None

def test_md_section():
    sec = cd.md_section(MD, "Sponsoring question")
    assert "Which initiative" in sec and "Second para." in sec
    assert "Out-of-scope" not in sec   # stops at next ##

def test_md_table():
    headers, rows = cd.md_table(MD, after_heading="Out-of-scope boundaries")
    assert headers == ["Excluded", "Rationale"]
    assert rows == [["Sales", "Different org."]]   # separator row dropped

def test_field_section_and_signoff():
    assert cd.field_section("Client", MD, "Client")[0]["type"] == "heading"
    assert any("Confirmed" in b.get("text","") for b in cd.signoff_block())

def test_prose_section_paragraphs():
    blocks = cd.prose_section("Sponsoring question", MD, "Sponsoring question")
    texts = [b["text"] for b in blocks if b["type"] == "paragraph"]
    assert "Which initiative should we fund?" in texts and "Second para." in texts
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: state.checkpoint_doc`)
Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest state/tests/test_checkpoint_doc_builders.py -q`

- [ ] **Step 3: Implement**

```python
# state/checkpoint_doc.py — deterministic, declarative checkpoint documents (#131).
# Stdlib only. No fabrication: every value is copied from a source file.
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from state import docx

# ---- markdown helpers ----
def md_field(md, label):
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else None

def md_section(md, heading):
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None

def _is_separator(cells):
    return all(set(c) <= set("-: ") and c for c in cells)

def md_table(md, after_heading=None):
    text = md if after_heading is None else (md_section(md, after_heading) or "")
    parsed = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if _is_separator(cells):
            continue
        parsed.append(cells)
    return (parsed[0], parsed[1:]) if parsed else ([], [])

# ---- section builders (each returns a list of docx blocks) ----
def field_section(title, md, label):
    v = md_field(md, label)
    return [docx.heading(title, 2), docx.paragraph(v)] if v else []

def prose_section(title, md, heading):
    body = md_section(md, heading)
    if not body:
        return []
    out = [docx.heading(title, 2)]
    for line in body.splitlines():
        s = line.strip().lstrip("-* ").strip()
        if s and not s.startswith("|"):     # skip table rows; keep prose + bullets as paragraphs
            out.append(docx.paragraph(s))
    return out

def table_section(title, headers, rows):
    return [docx.heading(title, 2), docx.table(headers, rows)] if rows else []

def note(text):
    return [docx.paragraph(text)]

def signoff_block(reviewer_label="Reviewer"):
    return [docx.heading("Sign-off", 2),
            docx.paragraph(f"{reviewer_label}: ______________________"),
            docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
            docx.paragraph("Comments:")]
```

- [ ] **Step 4: Run → PASS.** **Step 5: Commit** `feat(checkpoint-doc): markdown helpers + section builders (#131)`

---

### Task 2: registry + driver + process-validation entry

**Files:** Modify `state/checkpoint_doc.py`, `state/process_review.py`; Test `state/tests/test_checkpoint_doc_driver.py`

**Interfaces:**
- Consumes: Task 1 builders; `state.process_review.build_blocks` (#136).
- Produces: `Checkpoint` dataclass; `CHECKPOINTS` dict; `render_checkpoint(engagement_dir, checkpoint_id) -> list[str]`; CLI `python3 -m state.checkpoint_doc <dir> <id>`; `_ready_processes(root) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# state/tests/test_checkpoint_doc_driver.py
import zipfile
from state import checkpoint_doc as cd

PROC = """## PROC-001 — Staffing
<!-- index: baseline=Ready -->
**Trigger:** A request enters the queue.
### Process Map
**Steps:**
1. Submit request. → Yellow — unstructured.
**Actors:** RMO analyst.
**Decision points:** Selection.
**Exceptions:** Double-booking.
**Upstream / downstream:** up; down.
### Baselines
| Field | Value | Source | Confidence |
|---|---|---|---|
| Volume | ~140/mo | Priya | Medium |
"""

def _scaffold(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | Staffing | Ready |\n| PROC-002 | Held | Pending |\n")
    (tmp_path / "processes" / "PROC-001.md").write_text(PROC)

def test_ready_processes(tmp_path):
    _scaffold(tmp_path)
    assert cd._ready_processes(tmp_path) == ["PROC-001"]

def test_render_process_validation_per_process(tmp_path):
    _scaffold(tmp_path)
    written = cd.render_checkpoint(str(tmp_path), "process-validation")
    cp = tmp_path / "checkpoints" / "process-validation"
    assert (cp / "PROC-001.docx").exists() and not (cp / "PROC-002.docx").exists()
    assert (cp / "CP-PROC-001-outcome.md").exists()
    with zipfile.ZipFile(cp / "PROC-001.docx") as z:
        assert "word/document.xml" in z.namelist()

def test_render_single_doc_checkpoint(tmp_path):
    # a single-doc checkpoint writes one .docx + one outcome stub
    (tmp_path / "scope.md").write_text("**Client:** Acme\n## Sponsoring question\nWhy?\n")
    (tmp_path / "context.md").write_text("# Context\n")
    written = cd.render_checkpoint(str(tmp_path), "scope")
    assert (tmp_path / "checkpoints" / "checkpoint-scope.docx").exists()
    assert (tmp_path / "checkpoints" / "CP-scope-outcome.md").exists()
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** (append to `state/checkpoint_doc.py`)

```python
@dataclass
class Checkpoint:
    id: str
    per_process: bool
    gate: bool
    output: str            # single-doc path, or "{pid}" template for per_process
    outcome: str           # outcome path, "{pid}" template for per_process
    build: Callable        # single: build(root)->blocks ; per_process: build(root, proc_md)->blocks

def _ready_processes(root):
    idx = Path(root) / "processes" / "_index.md"
    if not idx.exists():
        return []
    out = []
    for line in idx.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("PROC-") and cells[2].lower() == "ready":
            out.append(cells[0])
    return out

def _read(root, name):
    p = Path(root) / name
    return p.read_text(encoding="utf-8") if p.exists() else ""

# build functions for scope/baseline/portfolio land in Tasks 3-5.
def _build_process_validation(root, proc_md):
    from state.process_review import build_blocks
    return build_blocks(proc_md)

CHECKPOINTS = {
    "process-validation": Checkpoint(
        "process-validation", per_process=True, gate=True,
        output="checkpoints/process-validation/{pid}.docx",
        outcome="checkpoints/process-validation/CP-{pid}-outcome.md",
        build=_build_process_validation),
    # "scope"/"baseline"/"portfolio" added in Tasks 3-5.
}

def render_checkpoint(engagement_dir, checkpoint_id):
    cp = CHECKPOINTS[checkpoint_id]
    root = Path(engagement_dir)
    written = []
    if cp.per_process:
        for pid in _ready_processes(root):
            proc = root / "processes" / f"{pid}.md"
            if not proc.exists():
                continue
            out = root / cp.output.format(pid=pid)
            out.parent.mkdir(parents=True, exist_ok=True)
            docx.build_docx(cp.build(root, proc.read_text(encoding="utf-8")), str(out))
            written.append(str(out))
            oc = root / cp.outcome.format(pid=pid)
            if not oc.exists():
                oc.write_text(f"# {pid} — outcome\n\nOutcome: Pending\n", encoding="utf-8")
    else:
        out = root / cp.output
        out.parent.mkdir(parents=True, exist_ok=True)
        docx.build_docx(cp.build(root), str(out))
        written.append(str(out))
        oc = root / cp.outcome
        if not oc.exists():
            oc.write_text(f"# {checkpoint_id} — outcome\n\nOutcome: Pending\n", encoding="utf-8")
    return written

if __name__ == "__main__":
    print("\n".join(render_checkpoint(sys.argv[1], sys.argv[2])))
```

Then in `state/process_review.py`: **delete** `render_all` and the `if __name__ == "__main__"` block (superseded by the driver); **keep** `build_blocks` and its helpers. Update `state/tests/test_process_review.py`: remove the two `render_all` tests (the driver's per-process test now covers fan-out); keep the `build_blocks` tests.

> NOTE: Task 2's single-doc test references checkpoint id `scope`, whose `build` is added in Task 4. To keep Task 2 green on its own, add a temporary minimal `scope` entry now: `CHECKPOINTS["scope"] = Checkpoint("scope", False, False, "checkpoints/checkpoint-scope.docx", "checkpoints/CP-scope-outcome.md", lambda root: [docx.heading("Scope", 1)])`. Task 4 replaces the lambda with `_build_scope`.

- [ ] **Step 4: Run → PASS** (driver + process_review tests). **Step 5: Commit** `feat(checkpoint-doc): registry + driver + process-validation entry (#131)`

---

### Task 3: baseline entry

**Files:** Modify `state/checkpoint_doc.py`; Test add to `state/tests/test_checkpoint_doc_driver.py`

- [ ] **Step 1: Failing test**

```python
def test_baseline_doc_has_metrics_and_pending(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n| PROC-001 | Staffing | Ready |\n")
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "baselines.json").write_text(
        '{"PROC-001": {"volume": "~140/mo", "cycle_time": "3d/11d", "error_rate": "22%", "fte": "3.5"}}')
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "baseline")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-baseline.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Staffing" in xml and "~140/mo" in xml
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `checkpoint_doc.py`:

```python
import json

def _build_baseline(root):
    index = _read(root, "processes/_index.md")
    names = {r[0]: r[1] for r in md_table(index)[1] if r and r[0].startswith("PROC-")}
    try:
        data = json.loads(_read(root, "model/baselines.json") or "{}")
    except ValueError:
        data = {}
    rows = []
    for pid in _ready_processes(root):
        b = data.get(pid, {})
        def g(k): return b.get(k) or "PENDING"
        rows.append([pid, names.get(pid, ""), g("volume"), g("cycle_time"), g("error_rate"), g("fte")])
    blocks = [docx.heading("As-Is Baselines — For Your Confirmation", 1)]
    blocks += note("Please confirm these baseline figures for each process, or note corrections.")
    blocks += table_section("Baselines",
        ["Process", "Name", "Volume", "Cycle time", "Error/exception", "FTE"], rows)
    blocks += signoff_block("Sponsor / process owners")
    return blocks

CHECKPOINTS["baseline"] = Checkpoint(
    "baseline", per_process=False, gate=False,
    output="checkpoints/checkpoint-baseline.docx",
    outcome="checkpoints/CP-baseline-outcome.md", build=_build_baseline)
```

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): baseline entry (#131)`

---

### Task 4: scope entry (with CP1 exclusions)

**Files:** Modify `state/checkpoint_doc.py`; Test add to driver test

- [ ] **Step 1: Failing test**

```python
def test_scope_doc_includes_scope_excludes_internal_context(tmp_path):
    (tmp_path / "scope.md").write_text(
        "**Client:** Acme\n**Sponsor:** Dana\n"
        "## Sponsoring question\nWhich to fund?\n"
        "## In-scope domains\n1. Staffing\n2. Billing\n"
        "## Out-of-scope boundaries\n| Excluded | Rationale |\n|---|---|\n| Sales | other org |\n")
    (tmp_path / "context.md").write_text(
        "## Organization\nAcme does X.\n"
        "## Risk posture\nRisk-averse, burned by Project Swift.\n"
        "## AI / automation maturity\nLow.\n"
        "## Political landscape\nCFO distrusts the CDO.\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "scope")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-scope.docx") as z:
        xml = z.read("word/document.xml").decode().lower()
    assert "which to fund" in xml and "staffing" in xml and "sales" in xml   # scope content in
    for forbidden in ("risk posture", "project swift", "automation maturity", "political", "cfo distrusts"):
        assert forbidden not in xml      # internal context OUT
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — replace the temporary `scope` entry with:

```python
# Context sections that must never reach the client doc (CP1 guard).
_SCOPE_EXCLUDE = ("risk posture", "ai / automation maturity", "ai/automation maturity",
                  "automation maturity", "political landscape")

def _build_scope(root):
    scope = _read(root, "scope.md")
    context = _read(root, "context.md")
    blocks = [docx.heading("Engagement Scope — For Your Confirmation", 1)]
    for label in ("Client", "Sponsor", "Decision-maker"):
        blocks += field_section(label, scope, label)
    blocks += prose_section("Sponsoring question", scope, "Sponsoring question")
    blocks += prose_section("In scope", scope, "In-scope domains")
    h, r = md_table(scope, after_heading="Out-of-scope boundaries")
    blocks += table_section("Out of scope", h, r)
    # context.md: include only non-internal sections (exclude the CP1-guarded ones).
    for m in re.finditer(r"^##\s+(.+?)\s*$", context, re.MULTILINE):
        title = m.group(1).strip()
        if title.strip().lower() in _SCOPE_EXCLUDE:
            continue
        blocks += prose_section(title, context, title)
    blocks += note("Please confirm the scope above is correct, or note what should change.")
    blocks += signoff_block("Sponsor / decision-maker")
    return blocks

CHECKPOINTS["scope"] = Checkpoint(
    "scope", per_process=False, gate=False,
    output="checkpoints/checkpoint-scope.docx",
    outcome="checkpoints/CP-scope-outcome.md", build=_build_scope)
```

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): scope entry with CP1 exclusions (#131)`

---

### Task 5: portfolio entry

**Files:** Modify `state/checkpoint_doc.py`; Test add to driver test

- [ ] **Step 1: Failing test**

```python
def test_portfolio_doc_has_waves_and_scores(tmp_path):
    (tmp_path / "scores").mkdir(); (tmp_path / "opportunities").mkdir()
    (tmp_path / "scores" / "_index.md").write_text(
        "| OPP-ID | Composite | Horizon | B/B/P |\n|---|---|---|---|\n| OPP-003 | 4.17 | Short-run | Buy |\n")
    (tmp_path / "roadmap.md").write_text(
        "# Roadmap\n## Sequencing thesis\nClean data first.\n"
        "## Wave summary\n| Wave | Initiative | OPP | Composite |\n|---|---|---|---|\n"
        "| 1 — Foundation | Time Validation | OPP-003 | 4.17 |\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "portfolio")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-portfolio.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "OPP-003" in xml and "Foundation" in xml and "Clean data first." in xml
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — add to `checkpoint_doc.py`:

```python
def _build_portfolio(root):
    roadmap = _read(root, "roadmap.md")
    blocks = [docx.heading("Opportunity Portfolio & Roadmap — For Your Confirmation", 1)]
    blocks += prose_section("Sequencing", roadmap, "Sequencing thesis")
    wh, wr = md_table(roadmap, after_heading="Wave summary")
    blocks += table_section("Roadmap waves", wh, wr)
    sh, sr = md_table(_read(root, "scores/_index.md"))
    blocks += table_section("Scored opportunities", sh, sr)
    blocks += note("Please confirm the prioritization and sequencing, or note changes.")
    blocks += signoff_block("Decision-maker / sponsor")
    return blocks

CHECKPOINTS["portfolio"] = Checkpoint(
    "portfolio", per_process=False, gate=False,
    output="checkpoints/checkpoint-portfolio.docx",
    outcome="checkpoints/CP-portfolio-outcome.md", build=_build_portfolio)
```

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint-doc): portfolio entry (#131)`

---

### Task 6: rewire `building-checkpoint` to the deterministic command for all ids

**Files:** Modify `skills/building-checkpoint/SKILL.md`; Test `tests/test_checkpoint_deterministic.py`

- [ ] **Step 1: Failing test**

```python
# tests/test_checkpoint_deterministic.py
from pathlib import Path
SKILL = (Path(__file__).resolve().parents[1] / "skills" / "building-checkpoint" / "SKILL.md").read_text()

def test_all_checkpoints_route_through_deterministic_command():
    assert "python3 -m state.checkpoint_doc" in SKILL
    # the LLM section-renderer dispatch + HTML shell are gone
    assert "section-renderer-checkpoint" not in SKILL
    assert "Checkpoint shell" not in SKILL

def test_no_deliverable_gate_checkpoint_mode_for_checkpoints():
    assert "Checkpoint Mode" not in SKILL
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3:** Rewrite the skill's Orchestration so **every** id runs
  `PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>` (one deterministic path), then prompts for the outcome. Generalize Session Start (the wired-values list already includes all four ids from #136; extend the predecessor checks: scope→`scope.md`; baseline→`processes/_index.md`+`model/baselines.json`; portfolio→`roadmap.md`+`scores/_index.md`; process-validation→`processes/_index.md`). **Delete** the `## Gate condition` deliverable-gate invocation, the `## Orchestration` section-renderer steps (3–6), the `## Checkpoint shell` section, and the `## Deterministic checkpoint: process-validation` special-case (now the general path). Keep "Recording the outcome".

- [ ] **Step 4: PASS. Step 5: Commit** `feat(checkpoint): route all checkpoints through deterministic .docx renderer (#131)`

---

### Task 7: delete dead pieces + update branding guards

**Files:** Delete `agents/section-renderer-checkpoint-{scope,baseline,portfolio}.md`; Modify `skills/deliverable-gate/SKILL.md` (remove Checkpoint Mode section); Modify `tests/test_branding.py`

- [ ] **Step 1:** Update `tests/test_branding.py` — the deliverable-gate/branding guards that assert checkpoint **HTML** must change. Replace `test_checkpoint_skill_inlines_vendored_shell` with:

```python
def test_checkpoint_skill_is_deterministic_docx_not_html():
    text = CHECKPOINT_SKILL.read_text(encoding="utf-8")
    assert "python3 -m state.checkpoint_doc" in text
    assert "assets/osl/components.css" not in text   # no HTML shell in checkpoints anymore
```
(Leave the Phase-11 `building-deliverable` HTML branding tests untouched.)

- [ ] **Step 2: Run → FAIL** (old assertion / deleted-file references).
- [ ] **Step 3:** Delete the three `agents/section-renderer-checkpoint-*.md` files; remove the `## Checkpoint Mode` section from `skills/deliverable-gate/SKILL.md` and any cross-references to it. Grep to confirm nothing else references the deleted agents or Checkpoint Mode:
  `grep -rn "section-renderer-checkpoint\|Checkpoint Mode" skills/ agents/` → only allowed hits are none.
- [ ] **Step 4: Run full suite → PASS.** **Step 5: Commit** `refactor(checkpoint): remove HTML renderers + deliverable-gate Checkpoint Mode (#131)`

---

### Task 8: CHANGELOG

**Files:** Modify `CHANGELOG.md`

- [ ] **Step 1:** Under `## [Unreleased]`:

```markdown
### Changed
- **Interim checkpoints are now deterministic Word (`.docx`) documents** (#131). scope,
  baseline, portfolio, and process-validation all render from one declarative registry +
  shared layer (`state/checkpoint_doc.py` on `state/docx.py`) — identical every run,
  client-commentable. Replaces the per-checkpoint LLM HTML renderers (deleted, along with
  deliverable-gate Checkpoint Mode). The Phase 11 deliverable stays HTML. Adding a future
  per-phase checkpoint is now a registry entry (foundation for #99; delivers the interim half
  of #120).
```

- [ ] **Step 2:** Run full suite → PASS. **Step 3: Commit** `docs(changelog): deterministic checkpoint documents (#131)`

---

## Self-Review
- **Spec coverage:** shared layer (T1), registry+driver+process-validation fold-in (T2), the 3 entries (T3-5), building-checkpoint rewire (T6), deletions + branding guards (T7), CHANGELOG (T8). scope exclusions (T4 test). ✓
- **Placeholders:** none — every step has runnable code/commands. The Task 2 temporary `scope` lambda is explicitly replaced in Task 4 (noted).
- **Type consistency:** `render_checkpoint(dir, id) -> list[str]`, `Checkpoint(id, per_process, gate, output, outcome, build)`, builder return type `list[block]`, `build_blocks` reused unchanged. Consistent across tasks.
- **Ponytail:** function-ref registry (not a descriptor interpreter); reuse `build_blocks`; delete dead HTML path; valid-zip+content tests.
