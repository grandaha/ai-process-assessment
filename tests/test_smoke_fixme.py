"""Throwaway test for auto-review fix-loop smoke test. Safe to delete."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _smoke_fixme as m  # noqa: E402


def test_add_returns_sum():
    assert m.add(2, 3) == 5
