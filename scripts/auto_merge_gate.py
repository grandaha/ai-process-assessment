"""Deterministic decision logic for the PR auto-review-fix-merge loop.

Pure functions + a thin CLI. No network calls. The workflow gathers facts
(verdict, changed files, CI status, labels, round) and asks this module for a
single decision. Every ambiguity fails closed: when in doubt, do NOT merge.
"""
from __future__ import annotations

import json


def parse_verdict(structured_output: str | None, review_text: str | None) -> str:
    """Return 'YES', 'NO', or 'UNKNOWN'.

    Primary channel: structured_output JSON with a 'verdict' of AUTOMERGE/HOLD.
    Fallback: an 'AUTOMERGE: YES'/'AUTOMERGE: NO' token in the review prose.
    Fails closed — anything ambiguous or missing returns 'UNKNOWN'.
    """
    if structured_output:
        try:
            data = json.loads(structured_output)
            verdict = str(data.get("verdict", "")).upper()
            if verdict == "AUTOMERGE":
                return "YES"
            if verdict == "HOLD":
                return "NO"
        except (ValueError, AttributeError):
            pass  # fall through to token parsing

    if review_text:
        body = review_text.upper()
        if "AUTOMERGE: NO" in body:   # checked first — NO wins, fail-safe
            return "NO"
        if "AUTOMERGE: YES" in body:
            return "YES"

    return "UNKNOWN"
