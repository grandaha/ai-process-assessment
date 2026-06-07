import sys
from pathlib import Path

import pytest

# Make methodology_model importable regardless of pytest rootdir.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from methodology_model import build_methodology  # noqa: E402


@pytest.fixture(scope="session")
def methodology():
    return build_methodology()
