# tests/test_per_phase_review_docs.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
CP = (REPO / "skills" / "building-checkpoint" / "SKILL.md").read_text()
COND = (REPO / "skills" / "conducting-engagement" / "SKILL.md").read_text()
IDS = ["tech-data", "opportunities", "use-case-briefs", "business-case"]
DOCX_PATHS = [f"checkpoints/checkpoint-{i}.docx" for i in IDS]

def test_building_checkpoint_wires_new_ids():
    # each id must appear alongside its output .docx path in the registry table
    for i, path in zip(IDS, DOCX_PATHS):
        assert i in CP, f"building-checkpoint missing wired id {i}"
        assert path in CP, f"building-checkpoint registry missing output path {path}"

def test_building_checkpoint_registry_no_gate_semantics():
    # the registry must record opt-in / no-gate for each of the 4 new ids
    # "opt-in, no gate" appears in each of the 4 new registry rows
    assert CP.count("opt-in, no gate") >= 4, \
        "building-checkpoint registry must have 'opt-in, no gate' in all 4 new rows"

def test_conductor_offers_new_docs_at_phase_boundaries():
    for i in IDS:
        assert i in COND, f"conductor missing offer for {i}"
    # offered, not gated: conductor must describe these as opt-in, NOT hard gates
    assert "NOT hard gates" in COND, "conductor must describe per-phase review docs as NOT hard gates"
    assert "Totally optional" in COND, "conductor must narrate the offer as optional"
