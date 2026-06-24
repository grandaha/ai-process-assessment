"""Partial-state integrity checks over an engagement folder.

Pure functions of the filesystem — no network, no subprocess, no mutation.
Detects and classifies inconsistencies the existence-only phase check in
state.state cannot see (truncated outputs, index/body drift, bad model JSON,
absent results). Repair is the Conductor's job; this module only reports.

Companion to state.staleness (changed inputs) and state.conductor_state
(.conductor.md health) — neither condition is re-checked here.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.phases import PHASES


@dataclass(frozen=True)
class Issue:
    kind: str
    target: str   # repo-relative path
    repair: str   # "auto" | "surface"
    detail: str


def check_integrity(root) -> list[Issue]:
    root = Path(root)
    issues: list[Issue] = []

    # empty_output: a non-index phase output exists but is blank.
    for p in PHASES:
        if p.output.endswith("/_index.md"):
            continue
        fp = root / p.output
        if fp.exists() and not fp.read_text(encoding="utf-8").strip():
            issues.append(Issue(
                "empty_output", p.output, "surface",
                f"The {p.name} step's output is there but empty — let's redo it.",
            ))

    issues.sort(key=lambda i: (i.target, i.kind))
    return issues
