import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "integrity.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_prints_json_and_exits_zero(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("   ")  # one empty_output
    res = _run([str(eng)])
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload == [{
        "kind": "empty_output", "target": "scope.md",
        "repair": "surface", "detail": payload[0]["detail"],
    }]


def test_cli_clean_folder_prints_empty_list(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("real content")
    res = _run([str(eng)])
    assert res.returncode == 0
    assert json.loads(res.stdout) == []


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "does-not-exist")])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
