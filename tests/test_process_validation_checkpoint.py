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

def test_gate_and_orchestration_have_routing_skip_for_process_validation():
    # There must be an explicit routing note (containing both "process-validation" and "skip")
    # that appears before or within the Gate/Orchestration sections so an executor is sent
    # to the deterministic section instead of the HTML path.
    lines = SKILL.splitlines()
    # Find Gate condition section
    gate_idx = next((i for i, l in enumerate(lines) if "## Gate condition" in l), None)
    assert gate_idx is not None, "'## Gate condition' section not found"
    # The skip/routing note must appear at or before the Gate section (could be just before it
    # or as the first content of Gate condition).  Search from just before Gate through
    # Orchestration end (defined as start of next ## heading after Orchestration).
    orch_idx = next((i for i, l in enumerate(lines) if "## Orchestration" in l), None)
    assert orch_idx is not None, "'## Orchestration' section not found"
    # Find end of Orchestration section
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > orch_idx and l.startswith("## ")),
        len(lines),
    )
    routing_zone = "\n".join(lines[max(0, gate_idx - 5):next_section_idx])
    assert "process-validation" in routing_zone and "skip" in routing_zone.lower(), (
        "No routing/skip note for 'process-validation' found near Gate condition or Orchestration"
    )

def test_phase_checklist_exempts_process_validation():
    # The Phase checklist must note that process-validation is exempt from the
    # gate / section-renderer / HTML-assembly steps.
    lines = SKILL.splitlines()
    checklist_idx = next((i for i, l in enumerate(lines) if "## Phase checklist" in l), None)
    assert checklist_idx is not None, "'## Phase checklist' section not found"
    next_section_idx = next(
        (i for i, l in enumerate(lines) if i > checklist_idx and l.startswith("## ")),
        len(lines),
    )
    checklist_block = "\n".join(lines[checklist_idx:next_section_idx])
    assert "process-validation" in checklist_block, (
        "'process-validation' exemption missing from Phase checklist"
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
