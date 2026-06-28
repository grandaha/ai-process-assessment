# state/tests/test_process_validation_gate.py
from pathlib import Path
from state.state import read_state

def _gate(root):
    return next(g for g in read_state(root)["gates"] if g["id"] == "process-validation")

def _scaffold(tmp_path, outcomes):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n"
        "| PROC-001 | A | Ready |\n| PROC-002 | B | Ready |\n")
    cp = tmp_path / "checkpoints" / "process-validation"; cp.mkdir(parents=True)
    for pid, val in outcomes.items():
        (cp / f"CP-{pid}-outcome.md").write_text(f"Outcome: {val}\n")

def test_required_when_an_outcome_is_pending(tmp_path):
    _scaffold(tmp_path, {"PROC-001": "Confirmed", "PROC-002": "Pending"})
    assert _gate(str(tmp_path))["status"] == "required"

def test_done_when_all_confirmed_or_waived(tmp_path):
    _scaffold(tmp_path, {"PROC-001": "Confirmed", "PROC-002": "Waived (owner OOO)"})
    assert _gate(str(tmp_path))["status"] == "done"

def test_not_required_when_no_ready_processes(tmp_path):
    (tmp_path / "processes").mkdir()
    (tmp_path / "processes" / "_index.md").write_text(
        "| PROC-ID | Process Name | Baseline |\n|---|---|---|\n")
    assert _gate(str(tmp_path))["status"] == "not-required"
