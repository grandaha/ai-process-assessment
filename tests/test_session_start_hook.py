"""The session-start hook is the path-agnostic conversational front door.

It must fire on any install location, inject the resolved plugin root and the
engine/state command forms, carry a resume-agnostic greeting line, honor the
silence opt-out, and contain no hardcoded author path or dead skill name.
"""
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "session-start.sh"


def _run(env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = "/tmp/some/install/location"
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK)], env=env, capture_output=True, text=True,
    )


def test_note_contains_resolved_root_and_engine_command():
    out = _run({}).stdout
    assert "/tmp/some/install/location" in out
    assert "/tmp/some/install/location/engine/run.py" in out
    assert "/tmp/some/install/location/state/state.py" in out


def test_note_has_resume_agnostic_front_door_line():
    out = _run({}).stdout
    assert "resuming" in out.lower()
    assert "you don't need to know any commands or phase names" in out.lower()


def test_silence_opt_out_produces_no_output():
    res = _run({"AI_ASSESSMENT_SILENT": "1"})
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def test_no_dead_author_path_or_skill_name():
    out = _run({}).stdout
    assert "/Users/daveraffaele" not in out
    assert "ai-usecase-methodology" not in out
    assert "ai-cockpit" not in out


def test_note_is_wrapped_for_standing_context():
    out = _run({}).stdout
    assert "<EXTREMELY_IMPORTANT>" in out
    assert "</EXTREMELY_IMPORTANT>" in out


def test_note_offers_the_three_first_contact_paths():
    out = _run({}).stdout.lower()
    assert "continue an existing one" in out
    assert "run a sample" in out


def test_ps1_twin_carries_the_same_offer():
    # The .sh hook is exercised by subprocess above; the .ps1 twin can't run on the CI
    # linux runner, so guard its content statically to keep the two in sync.
    ps1 = (REPO / "hooks" / "session-start.ps1").read_text(encoding="utf-8").lower()
    assert "continue an existing one" in ps1
    assert "run a sample" in ps1
    assert "you don't need to know any commands or phase names" in ps1
