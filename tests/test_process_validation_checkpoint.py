# tests/test_process_validation_checkpoint.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
SKILL = (REPO / "skills" / "building-checkpoint" / "SKILL.md").read_text(encoding="utf-8")

def test_registry_has_process_validation_row():
    assert "process-validation" in SKILL
    assert "checkpoints/process-validation/PROC-NNN.docx" in SKILL

def test_process_validation_is_deterministic_path():
    # It must run the renderer module, NOT the LLM section-renderer / HTML-shell path.
    assert "state.process_review" in SKILL
    assert "section-renderer-checkpoint-process-validation" not in SKILL
