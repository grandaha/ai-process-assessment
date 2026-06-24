import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "step_review.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_writes_review_and_prints_path(tmp_path):
    eng = tmp_path / "acme"
    (eng / "opportunities").mkdir(parents=True)
    (eng / "opportunities" / "_index.md").write_text("| OPP-ID |\n")
    (eng / "opportunities" / "OPP-001.md").write_text("## OPP-001 — X\n\nb\n")
    res = _run([str(eng), "5"])
    assert res.returncode == 0
    written = (eng / "reviews" / "05-opportunities.md")
    assert written.exists()
    assert "reviews/05-opportunities.md" in res.stdout
    assert "# Review — Opportunities" in written.read_text()


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "missing"), "5"])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
