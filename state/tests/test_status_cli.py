import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "status.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_prints_json_and_exits_zero(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("x")
    res = _run([str(eng)])
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["engagement"] == "acme"
    assert payload["current_step"]["id"] == "2"


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "missing")])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
