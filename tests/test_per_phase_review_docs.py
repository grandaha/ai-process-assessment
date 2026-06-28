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
