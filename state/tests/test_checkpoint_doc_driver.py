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
