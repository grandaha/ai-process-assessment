"""A presentation projection of an engagement's standing.

Pure composition of the existing readers — state.state (content), state.conductor_state
(interaction), state.staleness (changed inputs), state.integrity (partial state) — into
one human-oriented view the Conductor narrates on demand. Re-derives nothing: every
phase status and gate verdict comes from the composed functions.

Not the removed SSE cockpit dashboard (#73/#75): a single pure projection + CLI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.conductor_state import read_conductor
from state.integrity import check_integrity
from state.staleness import changed_inputs
from state.state import read_state


def status_view(root) -> dict:
    root = Path(root)
    snap = read_state(root)
    # read_state already read .conductor.md once (for engine_root); we read it again
    # for the full interaction dict. Both are pure and the file is tiny.
    conductor = read_conductor(root)

    phases = snap["phases"]
    current = next((p for p in phases if p["status"] == "available"), None)
    current_step = {"id": current["id"], "name": current["name"]} if current else None
    blocked = [
        {"id": p["id"], "name": p["name"], "waiting_on": p["blocked_reason"]}
        for p in phases if p["status"] == "blocked"
    ]

    gate_status = {g["id"]: g["status"] for g in snap["gates"]}
    grc_status = gate_status.get("grc")
    deliverable_status = gate_status.get("deliverable")

    gates_due = []
    if grc_status == "required":
        gates_due.append("grc")
    if current_step is None and deliverable_status != "done":
        gates_due.append("deliverable")

    # Staleness needs a recorded baseline. With no recorded hashes (a fresh
    # engagement, or a legacy/unparseable .conductor.md that read_conductor maps
    # to {}), nothing is known-stale — flagging every input as "stale" would be a
    # false alarm on this read-only surface. The conductor records hashes after
    # each model phase, so real staleness is still caught in a driven engagement.
    recorded = conductor.get("model_input_hashes") or {}
    stale = changed_inputs(root, recorded) if recorded else []
    partial = [
        {"kind": i.kind, "target": i.target, "repair": i.repair, "detail": i.detail}
        for i in check_integrity(root)
    ]

    done = snap["progress"]["done"]
    total = snap["progress"]["total"]

    return {
        "engagement": snap["engagement"],
        "progress": {"done": done, "total": total,
                     "percent": int(round(100 * done / total))},
        "current_step": current_step,
        "blocked": blocked,
        "attention": {
            "gates_due": gates_due,
            "stale_inputs": stale,
            "partial_state": partial,
        },
        "interaction": {
            "register": conductor.get("register"),
            "autonomy": (conductor.get("autonomy") or {}).get("should_confirm"),
            "deferred_processes": conductor.get("deferred_processes", []),
            "open_decisions": conductor.get("open_decisions", []),
        },
        "complete": (current_step is None and grc_status != "required"
                     and deliverable_status == "done"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="state.status")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    args = parser.parse_args(argv)
    if not args.engagement.is_dir():
        print(f"not a directory: {args.engagement}", file=sys.stderr)
        return 2
    print(json.dumps(status_view(args.engagement), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
