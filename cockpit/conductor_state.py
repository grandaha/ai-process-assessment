"""Read/write the Conductor's private state file, <engagement>/.conductor.md.

Interaction context only — never engagement content. Content state is always
derived from the engagement files via cockpit.state.read_state(); this file holds
register, autonomy, version stamp, deferred processes, and the model-input hashes
that power staleness detection (cockpit.staleness).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from cockpit.staleness import hash_inputs

CONDUCTOR_FILE = ".conductor.md"


def read_conductor(root: Path) -> dict:
    path = Path(root) / CONDUCTOR_FILE
    if not path.exists():
        return {}
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def write_conductor(root: Path, data: dict) -> None:
    body = yaml.safe_dump(data, sort_keys=False).strip()
    (Path(root) / CONDUCTOR_FILE).write_text(f"---\n{body}\n---\n")


def record_input_hashes(root: Path) -> dict:
    data = read_conductor(root)
    data["model_input_hashes"] = hash_inputs(root)
    write_conductor(root, data)
    return data
