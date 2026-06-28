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

def test_baseline_doc_has_metrics_and_pending(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | Staffing | Ready |\n"
        "| PROC-002 | Billing | Ready |\n")
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "baselines.json").write_text(
        '{"PROC-001": {"volume": "~140/mo", "cycle_time": "3d/11d", "error_rate": "22%", "fte": "3.5"}}')
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "baseline")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-baseline.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Staffing" in xml and "~140/mo" in xml
    assert "PENDING" in xml

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
