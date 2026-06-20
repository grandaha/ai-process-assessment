"""Read/write the Conductor's private state file, <engagement>/.conductor.md.

Interaction context only — never engagement content. Content state is always
derived from the engagement files via state.state.read_state(); this file holds
register, autonomy, version stamp, deferred processes, and the model-input hashes
that power staleness detection (state.staleness).

The frontmatter body is JSON (stdlib only) fenced by '---' lines, so the core
runs without third-party deps in any code sandbox.
"""
from __future__ import annotations

import json
from pathlib import Path

from state.staleness import hash_inputs

CONDUCTOR_FILE = ".conductor.md"


def read_conductor(root: Path) -> dict:
    path = Path(root) / CONDUCTOR_FILE
    if not path.exists():
        return {}
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}
    rest = text[len("---\n"):]
    end = rest.rfind("\n---")
    if end == -1:
        return {}
    body = rest[:end].strip()
    if not body:
        return {}
    try:
        loaded = json.loads(body)
    except json.JSONDecodeError:
        return {}  # legacy/corrupt frontmatter — treat as empty; caller re-stamps
    return loaded if isinstance(loaded, dict) else {}


def write_conductor(root: Path, data: dict) -> None:
    body = json.dumps(data, indent=2)
    (Path(root) / CONDUCTOR_FILE).write_text(f"---\n{body}\n---\n")


def record_input_hashes(root: Path) -> dict:
    data = read_conductor(root)
    data["model_input_hashes"] = hash_inputs(root)
    write_conductor(root, data)
    return data
