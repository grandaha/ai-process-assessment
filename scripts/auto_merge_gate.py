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


# --- path classification ---

ALLOWED_PREFIXES = ("engine/", "tests/", "scripts/")
MARKDOWN_SUFFIXES = (".md",)
# Never auto-merge changes to the loop's own machinery, even though they live
# under allowed prefixes. claude-code-action also cannot edit .github/ files,
# but we guard it deterministically regardless.
PROTECTED_PREFIXES = (".github/",)
PROTECTED_FILES = ("scripts/auto_merge_gate.py",)


def classify_paths(changed_files: list[str]) -> dict:
    """Classify a PR's changed-file set for merge eligibility.

    python_only is True iff there is at least one changed file and ALL changed
    files are under an allowed prefix, none are markdown, and none are protected.
    """
    touches_markdown = any(
        f.endswith(MARKDOWN_SUFFIXES) for f in changed_files
    )
    touches_protected = any(
        f in PROTECTED_FILES or f.startswith(PROTECTED_PREFIXES)
        for f in changed_files
    )
    all_allowed = bool(changed_files) and all(
        f.startswith(ALLOWED_PREFIXES) for f in changed_files
    )
    python_only = all_allowed and not touches_markdown and not touches_protected
    return {
        "python_only": python_only,
        "touches_markdown": touches_markdown,
        "touches_protected": touches_protected,
    }
