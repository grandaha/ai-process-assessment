"""Auto-RED capture for the improvement flywheel.

The Conductor calls prepend_entry() when it catches itself reaching for a
rationalization shortcut: it records a structured RED entry in the engagement's
improvement-log.md. GREEN (the rationalization-table row) and REFACTOR (gate
tightening) remain human-approved and are not done here.

Pure given (file contents, escape) — no clock (the date is passed in), no network.
The prepend is non-destructive: existing entries are never edited or reordered.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ENTRIES_HEADER = "## Entries"
_SCAFFOLD = (
    "# Improvement Log\n\n"
    "Prepend-only. New entries go at the top. Existing entries are never edited.\n\n"
    f"{ENTRIES_HEADER}\n"
)


@dataclass(frozen=True)
class Escape:
    date: str          # ISO date, supplied by the caller (no clock here)
    phase: str         # e.g. "5" or "n/a"
    skill: str         # skill dir name or "conductor"
    engagement: str    # engagement name/round, or "n/a"
    shortcut: str      # the rationalization the Conductor caught itself reaching for
    would_produce: str # the consequence it avoided
    why_uncaught: str  # which table row should have caught it (or "no row existed")
    reframe: str       # canonical reframe from the matched row, or "pending"


def render_entry(escape: Escape) -> str:
    """One RED entry in the canonical Entry Format (newest-first block)."""
    return (
        f"### [{escape.date}] Phase {escape.phase} — {escape.skill}\n\n"
        f"**Engagement/Round:** {escape.engagement}\n"
        f"**Shortcut taken:** {escape.shortcut}\n"
        f"**What it produced:** {escape.would_produce}\n"
        f"**Why the table didn't catch it:** {escape.why_uncaught}\n"
        f"**New row added to:** pending\n\n"
        f"| Rationalization / Shortcut | Correct Reframe |\n"
        f"|---|---|\n"
        f"| {escape.shortcut} | {escape.reframe} |\n\n"
        f"**Keystone updated:** pending\n"
        f"**Checklist/gate step updated:** pending\n"
    )


def prepend_entry(log_path, escape: Escape) -> None:
    """Prepend a RED entry under '## Entries'. Scaffold an absent file; insert after
    the first '## Entries' line of an existing one; raise ValueError if an existing
    file has no such header. Existing entries are never modified."""
    path = Path(log_path)
    block = render_entry(escape)
    if not path.exists():
        path.write_text(f"{_SCAFFOLD}\n{block}", encoding="utf-8")
        return
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip() == ENTRIES_HEADER:
            insert_at = i + 1
            break
    else:
        raise ValueError(f"{path}: no '{ENTRIES_HEADER}' header to prepend under")
    new_lines = lines[:insert_at] + [f"\n{block}"] + lines[insert_at:]
    path.write_text("".join(new_lines), encoding="utf-8")
