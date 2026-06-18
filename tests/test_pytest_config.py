import configparser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def test_testpaths_includes_cockpit_tests():
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "pytest.ini")
    testpaths = cfg.get("pytest", "testpaths").split()
    assert "cockpit/tests" in testpaths, f"cockpit/tests missing from testpaths: {testpaths}"
