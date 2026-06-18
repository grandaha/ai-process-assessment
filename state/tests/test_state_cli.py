import json
import subprocess
import sys


def test_module_is_runnable(engagement):
    root = engagement("scope.md")
    proc = subprocess.run(
        [sys.executable, "-m", "state.state", str(root)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert set(data) >= {"engagement", "progress", "phases", "gates", "model"}


def test_missing_folder_exits_nonzero(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "state.state", str(tmp_path / "nope")],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
