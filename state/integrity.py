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

from state.phases import MODEL_INPUTS, PHASES


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

    # model/*.json: malformed inputs (surface) + absent results with inputs (auto).
    model = root / "model"
    any_input = False
    for stem in MODEL_INPUTS:
        mp = model / f"{stem}.json"
        if not mp.exists():
            continue
        any_input = True
        try:
            json.loads(mp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(Issue(
                "bad_json", f"model/{stem}.json", "surface",
                f"The {stem} figures you entered aren't readable — I need them again.",
            ))
    if any_input and not (model / "results.json").exists():
        issues.append(Issue(
            "results_missing", "model/results.json", "auto",
            "The calculated numbers are missing — I can recompute them.",
        ))

    issues.sort(key=lambda i: (i.target, i.kind))
    return issues
