"""Operator-facing step review documents.

Consolidates a fragmented phase's _index.md + per-item files into one readable
review document, appends a change-history view of the decision log scoped to the
step's items, and preserves unresolved inline comments across regeneration.
Pure functions of the filesystem; stdlib + state.* only. Only the CLI writes.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.phases import PHASES

_ID_RE = re.compile(r"[A-Z]+-\d+$")        # full-match an id token
_ID_SEARCH = re.compile(r"[A-Z]+-\d+")     # find an id inside a heading
_COMMENT_RE = re.compile(r"^>\s*💬\s*(.*\S)\s*$")
_AT_RE = re.compile(r"@([A-Z]+-\d+)")

# Fragmented phases: phase_id -> (folder, review-file slug, display name).
_FRAGMENTED = {
    "4": ("processes", "04-processes", "Process Discovery"),
    "5": ("opportunities", "05-opportunities", "Opportunities"),
    "6": ("scores", "06-scores", "Scoring"),
    "8": ("usecase-briefs", "08-usecase-briefs", "Use-Case Briefs"),
}


@dataclass(frozen=True)
class Comment:
    anchor: str | None   # item id the comment is about, or None if unresolvable
    body: str            # the comment text (may include the @id token)
    line: int            # 1-based line number in the source text


def extract_comments(text: str) -> list[Comment]:
    out: list[Comment] = []
    heading_id: str | None = None
    for i, line in enumerate(text.splitlines(), start=1):
        m = _COMMENT_RE.match(line)
        if m:
            body = m.group(1).strip()
            at = _AT_RE.search(body)
            out.append(Comment(at.group(1) if at else heading_id, body, i))
            continue
        if line.lstrip().startswith("#"):
            s = _ID_SEARCH.search(line)
            if s:
                heading_id = s.group(0)
    return out


def review_path(phase_id: str) -> str:
    if phase_id in _FRAGMENTED:
        return f"reviews/{_FRAGMENTED[phase_id][1]}.md"
    for p in PHASES:
        if p.id == phase_id:
            return p.output
    raise ValueError(f"unknown phase_id: {phase_id}")


def _item_bodies(folder: Path) -> list[Path]:
    return sorted(
        (p for p in folder.glob("*.md")
         if p.name != "_index.md" and _ID_RE.fullmatch(p.stem)),
        key=lambda p: p.stem,
    )


def _esc(cell: str) -> str:
    return cell.replace("|", r"\|")


def _decision_history(root, ids: set[str]) -> list[dict]:
    path = Path(root) / "decision-log.md"
    if not path.exists():
        return []
    out: list[dict] = []
    cur: dict | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = None
            fields = [s.strip() for s in line[3:].split(" — ")]
            if len(fields) >= 3 and fields[-1] in ids:
                cur = {"when": fields[0], "id": fields[-1], "comment": "—", "change": "—"}
                out.append(cur)
        elif cur is not None and line.startswith("- "):
            key, _, val = line[2:].partition(":")
            key, val = key.strip(), val.strip()
            if key == "comment":
                cur["comment"] = val or "—"
            elif key == "disposition":
                cur["change"] = val or "—"
            elif key == "decision" and cur["change"] == "—":
                cur["change"] = val or "—"
    return out


def render_change_history(root, ids: set[str]) -> str:
    entries = _decision_history(root, ids)
    lines = ["## Change history", ""]
    if not entries:
        lines.append("No changes yet.")
        return "\n".join(lines)
    lines += ["| When | Item | Original comment | What changed |", "|---|---|---|---|"]
    for e in entries:
        lines.append(f"| {_esc(e['when'])} | {_esc(e['id'])} | "
                     f"{_esc(e['comment'])} | {_esc(e['change'])} |")
    return "\n".join(lines)


def render_review(root, phase_id: str) -> str:
    if phase_id not in _FRAGMENTED:
        raise ValueError(f"phase {phase_id} is not fragmented; use its source doc")
    root = Path(root)
    folder_name, _slug, display = _FRAGMENTED[phase_id]
    folder = root / folder_name

    # comments to preserve from an existing target
    target = root / review_path(phase_id)
    preserved = extract_comments(target.read_text(encoding="utf-8")) if target.exists() else []
    bodies = _item_bodies(folder)
    ids = {p.stem for p in bodies}
    by_anchor: dict[str, list[Comment]] = {}
    unanchored: list[Comment] = []
    for c in preserved:
        (by_anchor.setdefault(c.anchor, []) if c.anchor in ids else unanchored).append(c)

    parts = [
        f"# Review — {display} ({folder_name}/)", "",
        "> Working review document — read it and tell me what to change.", "",
    ]
    index = folder / "_index.md"
    if index.exists():
        parts += ["## Summary", "", index.read_text(encoding="utf-8").rstrip(), ""]
    for p in bodies:
        parts += ["---", "", p.read_text(encoding="utf-8").rstrip(), ""]
        for c in by_anchor.get(p.stem, []):
            parts += [f"> 💬 {c.body}", ""]
    if unanchored:
        parts += ["## Unanchored comments", ""]
        for c in unanchored:
            parts += [f"> 💬 {c.body}", ""]
    parts += [render_change_history(root, ids), ""]
    return "\n".join(parts).rstrip() + "\n"
