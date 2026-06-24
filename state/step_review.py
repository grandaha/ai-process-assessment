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
