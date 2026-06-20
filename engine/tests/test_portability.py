"""Proves the engine and state CLIs run by absolute path from any cwd.

Each test invokes the entrypoint as a script (not -m) from a foreign working
directory with a clean environment (no PYTHONPATH). This is the regression
guard for the shipped defect: `python3 /abs/engine/run.py <folder>` used to
raise ModuleNotFoundError because run.py never put the plugin root on sys.path.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"


def _seed_engagement(tmp_path: Path) -> Path:
    """Copy the lattice fixture model into a fresh engagement folder under tmp_path."""
    eng = tmp_path / "engagement"
    model = eng / "model"
    model.mkdir(parents=True)
    for f in FIXTURE.glob("*.json"):
        if f.name == "results.json":
            continue  # results is a derived output, not an input
        (model / f.name).write_text(f.read_text(), encoding="utf-8")
    return eng


def _clean_env() -> dict:
    """A minimal environment with no PYTHONPATH leaking the repo onto sys.path."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return env


def test_engine_run_by_absolute_path_from_foreign_cwd(tmp_path):
    eng = _seed_engagement(tmp_path)
    res = subprocess.run(
        [sys.executable, str(REPO / "engine" / "run.py"), str(eng)],
        cwd=str(tmp_path), env=_clean_env(),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    results = json.loads((eng / "model" / "results.json").read_text())
    assert results["wave1_aggregate"]["investment_point"] is not None


def test_state_by_absolute_path_from_foreign_cwd(tmp_path):
    eng = _seed_engagement(tmp_path)
    res = subprocess.run(
        [sys.executable, str(REPO / "state" / "state.py"), str(eng)],
        cwd=str(tmp_path), env=_clean_env(),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    snapshot = json.loads(res.stdout)
    assert snapshot["engagement"] == "engagement"
    assert "phases" in snapshot


def test_import_as_package_path_is_unchanged():
    """Imported as a package (pytest / -m), the guard must NOT fire."""
    import engine.run
    import state.state
    assert engine.run.__package__ == "engine"
    assert state.state.__package__ == "state"
