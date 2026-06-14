"""Unit tests for the deterministic auto-merge gate logic.

The gate is the single most safety-critical piece: it decides whether an
LLM-reviewed PR auto-merges. Every ambiguity must fail closed (never merge).
"""
import sys
from pathlib import Path

# scripts/ is not on the path by default; add it (mirrors conftest's pattern).
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import auto_merge_gate as gate  # noqa: E402


class TestParseVerdict:
    def test_structured_output_automerge_is_yes(self):
        assert gate.parse_verdict('{"verdict": "AUTOMERGE"}', None) == "YES"

    def test_structured_output_hold_is_no(self):
        assert gate.parse_verdict('{"verdict": "HOLD"}', None) == "NO"

    def test_falls_back_to_token_in_review_text(self):
        assert gate.parse_verdict(None, "Looks good.\nAUTOMERGE: YES") == "YES"

    def test_token_no_in_review_text(self):
        assert gate.parse_verdict("", "Needs work.\nAUTOMERGE: NO") == "NO"

    def test_no_wins_over_yes_when_both_present(self):
        # Fail-safe: if the text is contradictory, treat as NO.
        assert gate.parse_verdict(None, "AUTOMERGE: YES ... actually AUTOMERGE: NO") == "NO"

    def test_missing_everything_is_unknown(self):
        assert gate.parse_verdict(None, None) == "UNKNOWN"

    def test_garbage_structured_output_falls_back_then_unknown(self):
        assert gate.parse_verdict("not json", "no token here") == "UNKNOWN"

    def test_unknown_is_not_yes(self):
        # The whole point: UNKNOWN must never be treated as approval.
        assert gate.parse_verdict(None, "") != "YES"
