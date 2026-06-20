"""Guards that operational skills use the portable absolute-path command form.

The keystone (using-methodology) is intentionally excluded — its `python -m
engine.run` mentions are conceptual module references kept verbatim-synced with
system-prompt.md.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"


def _body(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_conductor_has_no_module_command_form():
    body = _body("conducting-engagement")
    assert "python -m engine.run" not in body
    assert "python -m state.state" not in body
    assert "python3 -m engine.run" not in body
    assert "python3 -m state.state" not in body


def test_conductor_uses_engine_root_command_form():
    body = _body("conducting-engagement")
    assert "python3 <engine_root>/engine/run.py" in body
    assert "python3 <engine_root>/state/state.py" in body


def test_conductor_prerequisites_have_no_venv_or_pyyaml():
    body = _body("conducting-engagement")
    assert "python3 -m venv" not in body
    assert "pip install -r requirements.txt" not in body
    assert "pyyaml" not in body.lower()


def test_conductor_resolves_and_reconciles_engine_root():
    body = _body("conducting-engagement")
    assert "engine_root" in body
    assert "reconcile_engine_root" in body
