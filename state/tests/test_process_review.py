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
