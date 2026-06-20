"""Proves the compute/state core runs with no third-party deps available.

Each test runs a subprocess that installs a meta_path blocker for
yaml/openpyxl/formulas, then exercises the core. This is the AC-2/AC-4 guard:
the numbers must run in any bare-Python code sandbox.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"

_BLOCKER = '''
import sys
_BLOCKED = {"yaml", "openpyxl", "formulas"}
class _Block:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in _BLOCKED:
            raise ImportError("blocked for stdlib-core test: " + name)
        return None
sys.meta_path.insert(0, _Block())
'''


def _run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", _BLOCKER + script],
        cwd=REPO, capture_output=True, text=True,
    )


def _seed_model(tmp_path: Path) -> Path:
    model = tmp_path / "model"
    model.mkdir()
    for f in FIXTURE.glob("*.json"):
        (model / f.name).write_text(f.read_text())
    return model


def test_engine_run_core_path_needs_no_third_party_deps(tmp_path):
    model = _seed_model(tmp_path)
    script = f'''
from engine.run import main
rc = main([{str(tmp_path)!r}])
assert rc == 0, rc
import json
r = json.load(open({str(model / "results.json")!r}, encoding="utf-8"))
assert r["wave1_aggregate"]["investment_point"] is not None
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout


def test_conductor_state_needs_no_yaml(tmp_path):
    script = f'''
from pathlib import Path
from state.conductor_state import write_conductor, read_conductor
root = Path({str(tmp_path)!r})
write_conductor(root, {{"register": "operator", "autonomy": {{"should_confirm": True}}}})
got = read_conductor(root)
assert got["register"] == "operator"
assert got["autonomy"]["should_confirm"] is True
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout
