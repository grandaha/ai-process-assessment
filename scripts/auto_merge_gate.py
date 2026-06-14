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


# --- top-level decision ---

RISK_LABELS = ("security",)


def decide(
    verdict: str,
    ci_passed: bool,
    changed_files: list[str],
    labels: list[str],
    round_count: int,
    max_rounds: int = 3,
) -> dict:
    """Return {'decision': 'merge'|'fix'|'human', 'reason': str}.

    'merge' = eligible to auto-merge (the workflow still honors report-only mode).
    'fix'   = dispatch the Python-only fixer, then push + re-review.
    'human' = leave the PR for a person; reason explains why.
    Fail-safe: any path that isn't clearly 'merge' or 'fix' returns 'human'.
    """
    paths = classify_paths(changed_files)
    has_risk_label = any(lbl in RISK_LABELS for lbl in labels)

    if verdict == "YES":
        if has_risk_label:
            return {"decision": "human", "reason": "carries a security/risk label"}
        if not ci_passed:
            return {"decision": "human", "reason": "CI is not green"}
        if paths["touches_protected"]:
            return {"decision": "human", "reason": "touches protected machinery (.github/ or gate module)"}
        if not paths["python_only"]:
            return {"decision": "human", "reason": "approved, but touches markdown — ready for you to merge"}
        return {"decision": "merge", "reason": "python-only, approved, CI green"}

    if verdict == "NO":
        if not paths["python_only"]:
            return {"decision": "human", "reason": "rejected and touches markdown — fixer cannot edit prose"}
        if round_count >= max_rounds:
            return {"decision": "human", "reason": f"max auto-fix rounds ({max_rounds}) reached"}
        return {"decision": "fix", "reason": "python-only rejection under the round cap"}

    return {"decision": "human", "reason": f"verdict {verdict} — failing closed"}


# --- CLI ---

def _parse_bool(s: str) -> bool:
    return s.strip().lower() in ("true", "1", "yes", "success")


def _split_lines(s: str) -> list[str]:
    return [line.strip() for line in s.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Auto-merge gate decision.")
    p.add_argument("--verdict", required=True)            # YES | NO | UNKNOWN
    p.add_argument("--ci-passed", required=True)          # true/false/success
    p.add_argument("--changed-files", default="")         # newline-separated
    p.add_argument("--labels", default="")                # newline-separated
    p.add_argument("--round", type=int, default=0)
    p.add_argument("--max-rounds", type=int, default=3)
    args = p.parse_args(argv)

    result = decide(
        verdict=args.verdict.strip().upper(),
        ci_passed=_parse_bool(args.ci_passed),
        changed_files=_split_lines(args.changed_files),
        labels=_split_lines(args.labels),
        round_count=args.round,
        max_rounds=args.max_rounds,
    )
    print(f"decision={result['decision']}")
    print(f"reason={result['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
