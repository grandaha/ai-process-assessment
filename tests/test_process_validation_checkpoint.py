# tests/test_process_validation_checkpoint.py
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
SKILL = (REPO / "skills" / "building-checkpoint" / "SKILL.md").read_text(encoding="utf-8")

def test_registry_has_process_validation_row():
    assert "process-validation" in SKILL
    assert "checkpoints/process-validation/PROC-NNN.docx" in SKILL

def test_process_validation_is_deterministic_path():
    # #131: all ids including process-validation route through state.checkpoint_doc.
    assert "python3 -m state.checkpoint_doc" in SKILL
    assert "section-renderer-checkpoint-process-validation" not in SKILL

def test_session_start_wired_values_includes_process_validation():
    # Session Start step 3 must list process-validation in the wired values.
    # Find the line mentioning wired values and confirm process-validation is there.
    wired_line = next(
        (line for line in SKILL.splitlines() if "wired values" in line or "wired-values" in line),
        None,
    )
    assert wired_line is not None, "No 'wired values' line found in Session Start"
    assert "process-validation" in wired_line, (
        f"'process-validation' missing from wired-values line: {wired_line!r}"
    )

def test_session_start_predecessor_check_for_process_validation():
    # Session Start step 4 must describe the processes/_index.md check for process-validation.
    # Both the id and the file must appear in proximity (same paragraph / step 4 block).
    predecessor_block = next(
        (line for line in SKILL.splitlines() if "process-validation" in line and "processes/_index.md" in line),
        None,
    )
    assert predecessor_block is not None, (
        "No line combines 'process-validation' and 'processes/_index.md' "
        "(Session Start step 4 predecessor check missing)"
    )

def test_orchestration_covers_all_ids_including_process_validation():
    # #131: Gate condition is deleted; unified Orchestration must cover all ids.
    # Gate condition and separate special-case sections must be gone.
    assert "## Gate condition" not in SKILL
    assert "## Deterministic checkpoint" not in SKILL
    # Orchestration section must exist and mention the deterministic command.
    lines = SKILL.splitlines()
    orch_idx = next((i for i, l in enumerate(lines) if "## Orchestration" in l), None)
    assert orch_idx is not None, "'## Orchestration' section not found"
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > orch_idx and l.startswith("## ")),
        len(lines),
    )
    orch_block = "\n".join(lines[orch_idx:next_section_idx])
    assert "python3 -m state.checkpoint_doc" in orch_block, (
        "Orchestration must reference the deterministic command"
    )

def test_phase_checklist_covers_process_validation():
    # #131: all ids use the same path; the checklist must cover process-validation
    # (via the unified deterministic command step, not an exemption note).
    lines = SKILL.splitlines()
    checklist_idx = next((i for i, l in enumerate(lines) if "## Phase checklist" in l), None)
    assert checklist_idx is not None, "'## Phase checklist' section not found"
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > checklist_idx and l.startswith("## ")),
        len(lines),
    )
    checklist_block = "\n".join(lines[checklist_idx:next_section_idx])
    assert "checkpoint_doc" in checklist_block, (
        "Phase checklist must include the deterministic checkpoint_doc command step"
    )

def test_chain_to_next_skill_has_process_validation():
    # Chain-to-next-skill section must include a process-validation entry.
    lines = SKILL.splitlines()
    chain_idx = next((i for i, l in enumerate(lines) if "## Chain to next skill" in l), None)
    assert chain_idx is not None, "'## Chain to next skill' section not found"
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > chain_idx and l.startswith("## ")),
        len(lines),
    )
    chain_block = "\n".join(lines[chain_idx:next_section_idx])
    assert "process-validation" in chain_block, (
        "'process-validation' entry missing from 'Chain to next skill' section"
    )
