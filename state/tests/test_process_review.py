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

def test_build_blocks_includes_owner_fields_and_rating_subbullets():
    blocks = pr.build_blocks(PROC)
    text = "\n".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "PROC-001" in text and "Staffing & Resource Assignment" in text
    assert "A project is won" in text                      # trigger
    assert "EM submits a staffing request." in text        # step action kept (clean)
    assert "intake is unstructured" in text                # rating note kept (as sub-bullet)
    assert "RMO analyst" in text                           # actors
    assert "Candidate selection" in text                   # decision points
    assert "Double-bookings" in text                       # exceptions
    # the action paragraph itself must NOT carry the rating note
    step1 = next(b["text"] for b in blocks
                 if b["type"] == "paragraph" and b["text"].startswith("1."))
    assert "Yellow" not in step1 and "→" not in step1

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

