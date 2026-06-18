"""Reconcile a state snapshot with authorized deviations in CLAUDE.md.

read_state() is pure file logic; it cannot know a phase was deliberately skipped.
The CLAUDE.md "Methodology Overrides" table records those decisions. This module
turns real override rows into satisfied phases so downstream phases unblock.
"""
from __future__ import annotations

from state.phases import PHASES

_PLACEHOLDERS = ("<", "e.g.,", "fill in")


def _tokens() -> dict[str, str]:
    """Map every recognizable phase token -> that phase's output path."""
    tokens: dict[str, str] = {}
    for p in PHASES:
        tokens[p.output] = p.output
        tokens[p.skill] = p.output
        tokens[p.skill.split(":")[-1]] = p.output  # bare dir name
    return tokens


def parse_overrides(claude_md_text: str) -> set[str]:
    tokens = _tokens()
    authorized: set[str] = set()
    for line in claude_md_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != 3:
            continue
        override, reason, authorizer = cells
        if override.lower() == "override" or set(override) <= {"-"}:
            continue  # header or separator row
        joined = " ".join(cells).lower()
        if any(ph in joined for ph in _PLACEHOLDERS):
            continue  # untouched template row
        if not reason or not authorizer:
            continue  # incomplete row — not a real authorization
        for token, output in tokens.items():
            if token and token in override:
                authorized.add(output)
    return authorized


def reconcile(snapshot: dict, authorized: set[str]) -> dict:
    by_output = {p.output: p for p in PHASES}
    for ph in snapshot["phases"]:
        if ph["output"] in authorized and ph["status"] != "done":
            ph["status"] = "overridden"
            ph["blocked_reason"] = None
    satisfied = {
        ph["output"] for ph in snapshot["phases"]
        if ph["status"] in ("done", "overridden")
    }
    for ph in snapshot["phases"]:
        if ph["status"] == "blocked":
            phase = by_output[ph["output"]]
            if phase.predecessor is None or phase.predecessor in satisfied:
                ph["status"] = "available"
                ph["blocked_reason"] = None
    return snapshot
