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

from state.assembly import _header_fields
from state.phases import GATES, MODEL_INPUTS, PHASES


_ID_RE = re.compile(r"[A-Z]+-\d+$")


@dataclass(frozen=True)
class Issue:
    kind: str
    target: str   # repo-relative path
    repair: str   # "auto" | "surface"
    detail: str


def _folder_targets() -> list[tuple[str, bool]]:
    """(folder_name, header_based) for every folder-bearing phase/gate."""
    out = []
    for entry in (*PHASES, *GATES):
        if entry.output.endswith("/_index.md"):
            out.append((entry.output[: -len("/_index.md")], entry.header_based))
    return out


def _index_ids(index_path: Path) -> set[str]:
    """Ids in an _index.md table: first cells matching <PREFIX>-<N>.

    Generalizes state.state's header/separator skip across all folders (which
    carry different headers, and usecase-briefs a title line) by taking only
    id-shaped cells — headers, separators, and prose never match.
    """
    ids: set[str] = set()
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells and _ID_RE.fullmatch(cells[0]):
            ids.add(cells[0])
    return ids


def _body_ids(folder: Path) -> set[str]:
    return {
        p.stem for p in folder.glob("*.md")
        if p.name != "_index.md" and _ID_RE.fullmatch(p.stem)
    }


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

    # index/body drift, per folder-bearing phase/gate.
    for folder_name, header_based in _folder_targets():
        folder = root / folder_name
        index_path = folder / "_index.md"
        rel_index = f"{folder_name}/_index.md"
        body_ids = _body_ids(folder)
        index_nonempty = (
            index_path.exists() and bool(index_path.read_text(encoding="utf-8").strip())
        )
        index_ids = _index_ids(index_path) if index_nonempty else set()

        # truncated index with nothing to rebuild from -> surface.
        if index_path.exists() and not index_nonempty and not body_ids:
            issues.append(Issue(
                "empty_output", rel_index, "surface",
                f"The {folder_name.replace('-', ' ')} list is there but empty.",
            ))

        # indexed ids with no body file -> surface (all folders).
        missing = sorted(index_ids - body_ids)
        if missing:
            issues.append(Issue(
                "index_missing_item", rel_index, "surface",
                "Some items are listed but their details are missing: "
                + ", ".join(missing),
            ))

        if header_based:
            malformed = sorted(
                bid for bid in body_ids
                if not _header_fields((folder / f"{bid}.md").read_text(encoding="utf-8"))
            )
            for bid in malformed:
                issues.append(Issue(
                    "malformed_item", f"{folder_name}/{bid}.md", "surface",
                    "One item is incomplete and needs redoing.",
                ))
            orphan = sorted(body_ids - index_ids)
            if orphan and not malformed:
                issues.append(Issue(
                    "index_orphan_items", rel_index, "auto",
                    "Some finished items aren't in the list yet — I can re-add them.",
                ))

    issues.sort(key=lambda i: (i.target, i.kind))
    return issues
