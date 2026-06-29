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
    # engine INPUT shape: a LIST of per-process objects, each with a process_id (#149).
    (tmp_path / "model" / "baselines.json").write_text(
        '[{"process_id": "PROC-001", "volume": 140, "cycle_time_median": 3, '
        '"cycle_time_p90": 11, "error_rate": 0.22, "fte": 3.5, "source": "Priya"}]')
    cd.render_checkpoint(str(tmp_path), "baseline")
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-baseline.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Staffing" in xml and "140" in xml          # populated from baselines.json
    assert "3 / 11" in xml and "22%" in xml            # cycle median / P90 + error rate
    assert "PENDING" in xml                             # PROC-002 has no entry

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

def test_tech_data_doc_renders_sections(tmp_path):
    (tmp_path / "tech-inventory.md").write_text(
        "# Technology & Data Inventory\n"
        "## 1. System inventory\nPolaris PSA is the system of record.\n"
        "## 3. Data asset catalog\n| Asset | Sensitivity |\n|---|---|\n| Deliverables | High |\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "tech-data")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-tech-data.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Polaris PSA" in xml and "Deliverables" in xml and "High" in xml
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

def test_opportunities_doc_renders_per_opportunity_detail(tmp_path):
    d = tmp_path / "opportunities"; d.mkdir()
    (d / "_index.md").write_text(
        "| OPP-ID | Process | Type | Feasibility |\n|---|---|---|---|\n"
        "| OPP-001 | PROC-001 | Chain-Automation | Yellow |\n")
    (d / "OPP-001.md").write_text(
        "## OPP-001 — HubSpot-to-Kickoff Chain Automation (process: PROC-001)\n"
        "<!-- index: id=OPP-001 grc=Green -->\n\n"
        "**Type:** Chain Automation\n"
        "**Type source:** internal chain-scan derivation that must not render.\n"
        "**Hypothesis:** We believe a direct HubSpot-to-Teamwork integration will save setup time.\n"
        "**Value hypothesis:** ~3 hrs/project; 216-288 hrs/year recovered.\n"
        "**Chain formation:** step-by-step internal checkpoint analysis, excluded.\n"
        "**GRC flag:** Green — internal project data only.\n"
        "**Data / system dependencies:** HubSpot, Teamwork, Notion.\n"
        "**Structural response:** optimizing-around — challenge-hypothesis linkage, excluded.\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "opportunities")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-opportunities.docx") as z:
        xml = z.read("word/document.xml").decode()
    # name + client-facing fields present
    assert "HubSpot-to-Kickoff Chain Automation" in xml
    assert "direct HubSpot-to-Teamwork integration will save setup time" in xml   # Hypothesis
    assert "216-288 hrs/year recovered" in xml                                     # Value
    assert "internal project data only" in xml                                     # GRC flag
    assert "HubSpot, Teamwork, Notion" in xml                                      # dependencies
    # assessor-derivation fields excluded
    assert "chain-scan derivation" not in xml                                      # Type source
    assert "step-by-step internal checkpoint analysis" not in xml                  # Chain formation
    assert "challenge-hypothesis linkage" not in xml                              # Structural response
    assert "index: id=OPP-001" not in xml                                          # html comment

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

def test_missing_primary_source_raises(tmp_path):
    import pytest
    from state import checkpoint_doc as cd
    # no tech-inventory.md written → render must fail loudly, not emit a blank doc
    with pytest.raises(FileNotFoundError):
        cd.render_checkpoint(str(tmp_path), "tech-data")

def test_use_case_briefs_first_table_only_no_merge(tmp_path):
    # a UC file with TWO tables must render only the first; the second must not merge in
    d = tmp_path / "usecase-briefs"; d.mkdir()
    (d / "_index.md").write_text(
        "# Use-Case Briefs\n## UC mapping\n| UC | Title |\n|---|---|\n| UC-001 | Status Assistant |\n")
    (d / "UC-001.md").write_text(
        "# UC-001 — Status Assistant\n\n"
        "| Field | Value |\n|---|---|\n| Opportunity type | Chain Automation |\n\n"
        "## Risks\n| Risk | Mitigation |\n|---|---|\n| Data drift | Monitor monthly |\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "use-case-briefs")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-use-case-briefs.docx") as z:
        xml = z.read("word/document.xml").decode()
    assert "Chain Automation" in xml          # first table rendered
    assert "Data drift" not in xml            # second table NOT merged into the field table

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
