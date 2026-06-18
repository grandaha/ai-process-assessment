import configparser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def test_testpaths_includes_state_tests():
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "pytest.ini")
    testpaths = cfg.get("pytest", "testpaths").split()
    assert "state/tests" in testpaths, f"state/tests missing from testpaths: {testpaths}"
