from pathlib import Path
SKILL = (Path(__file__).resolve().parents[1] / "skills" / "building-checkpoint" / "SKILL.md").read_text()

def test_all_checkpoints_route_through_deterministic_command():
    assert "python3 -m state.checkpoint_doc" in SKILL
    # the LLM section-renderer dispatch + HTML shell are gone
    assert "section-renderer-checkpoint" not in SKILL
    assert "Checkpoint shell" not in SKILL

def test_no_deliverable_gate_checkpoint_mode_for_checkpoints():
    assert "Checkpoint Mode" not in SKILL
