import importlib.util

import pytest

from methodology_model import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "extract_changelog",
    REPO_ROOT / ".github" / "scripts" / "extract_changelog.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
extract = _mod.extract


SAMPLE = """# Changelog

## [Unreleased]

## [2.7.0] — 2026-06-09

### Changed
- Data architecture convergence.

## [2.6.0] — 2026-06-09

### Added
- Old stuff.
"""


def test_extracts_named_section_body_only():
    out = extract(SAMPLE, "2.7.0")
    assert "### Changed" in out
    assert "Data architecture convergence." in out
    # Stops at the next section header — does not bleed into 2.6.0.
    assert "Old stuff" not in out
    assert "## [2.6.0]" not in out


def test_section_header_line_is_not_included():
    out = extract(SAMPLE, "2.7.0")
    assert "## [2.7.0]" not in out


def test_missing_version_raises_keyerror():
    with pytest.raises(KeyError):
        extract(SAMPLE, "9.9.9")


def test_extracts_last_section_with_no_following_header():
    # The final section has no next "## [" to break on — the loop must run to
    # end-of-file and capture its body without bleeding past it.
    out = extract(SAMPLE, "2.6.0")
    assert "### Added" in out
    assert "Old stuff." in out
    assert "## [2.6.0]" not in out  # header line excluded
    assert "Data architecture convergence." not in out  # no earlier section
