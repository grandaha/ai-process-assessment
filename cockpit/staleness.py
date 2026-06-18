"""Content-hash staleness detection over an engagement's model/*.json inputs.

Pure functions of the filesystem. A content hash (not mtime) is the staleness
signal: the repo lives in an iCloud-synced folder where checkout/sync rewrite
timestamps, but a hash only changes when bytes actually change.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from cockpit.phases import MODEL_INPUTS


def hash_inputs(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for stem in MODEL_INPUTS:
        path = Path(root) / "model" / f"{stem}.json"
        if path.exists():
            out[stem] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def changed_inputs(root: Path, recorded: dict[str, str]) -> list[str]:
    current = hash_inputs(root)
    stems = set(current) | set(recorded)
    return sorted(s for s in stems if current.get(s) != recorded.get(s))
