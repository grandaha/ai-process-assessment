"""Pure snapshot builder: an engagement folder -> a state dict.

No Claude, no network, no mutation. The state layer's correctness lives here, so it is
a pure function of the filesystem and the encoded phase map.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from state.phases import GATES, MODEL_INPUTS, PHASES


def _phase_status(root: Path) -> list[dict]:
    out = []
    for phase in PHASES:
        done = (root / phase.output).exists()
        if done:
            status, reason = "done", None
        elif phase.predecessor is None or (root / phase.predecessor).exists():
            status, reason = "available", None
        else:
            pred = next(p for p in PHASES if p.output == phase.predecessor)
            status = "blocked"
            reason = f"Waiting on {pred.name} ({phase.predecessor})"
        out.append({
            "id": phase.id,
            "name": phase.name,
            "skill": phase.skill,
            "output": phase.output,
            "status": status,
            "blocked_reason": reason,
        })
    return out


def _count_non_green_grc(index_path: Path) -> int:
    """Count opportunity rows whose GRC flag is Yellow or Red.

    Only the GRC column (index 5) gates: a Yellow/Red Feasibility or Data
    Readiness flag does NOT trigger Gate A. This matches the methodology — the
    GRC column is the governance/risk/compliance signal; the others are scoring
    inputs handled in Phase 6.
    """
    count = 0
    for line in index_path.read_text().splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != 7:
            continue
        grc = cells[5].lower()
        if cells[0].lower() in ("opp-id", "") or set(cells[5]) <= {"-"}:
            continue  # header or separator row
        if grc in ("yellow", "red"):
            count += 1
    return count


def _gate_status(root: Path) -> list[dict]:
    # Gate A — GRC
    opps_index = root / "opportunities" / "_index.md"
    grc_done = (root / "grc" / "_index.md").exists()
    if grc_done:
        grc = {"status": "done", "reason": "GRC review recorded in grc/_index.md"}
    elif opps_index.exists() and (n := _count_non_green_grc(opps_index)) > 0:
        noun = "opportunity" if n == 1 else "opportunities"
        grc = {"status": "required", "reason": f"{n} {noun} flagged Yellow/Red"}
    else:
        grc = {"status": "not-required", "reason": None}

    # Gate B — Deliverable
    deliverable_done = (root / "evidence-log.md").exists()
    deliverable = (
        {"status": "done", "reason": "Clearance recorded in evidence-log.md"}
        if deliverable_done
        else {"status": "not-run", "reason": None}
    )

    return [
        {"id": "grc", "name": GATES[0].name, "output": GATES[0].output, **grc},
        {"id": "deliverable", "name": GATES[1].name, "output": GATES[1].output, **deliverable},
    ]


def _model_section(root: Path) -> dict:
    results_path = root / "model" / "results.json"
    results = None
    if results_path.exists():
        try:
            results = json.loads(results_path.read_text())
        except (json.JSONDecodeError, OSError):
            results = None
    inputs_present = {
        key: (root / "model" / f"{stem}.json").exists()
        for stem, key in MODEL_INPUTS.items()
    }
    return {"results": results, "inputs_present": inputs_present}


def read_state(engagement_dir: Path | str) -> dict:
    root = Path(engagement_dir)
    phases = _phase_status(root)
    done = sum(1 for p in phases if p["status"] == "done")
    return {
        "engagement": root.name,
        "path": str(root),
        "progress": {"done": done, "total": len(PHASES)},
        "phases": phases,
        "gates": _gate_status(root),
        "model": _model_section(root),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="state.state")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    args = parser.parse_args(argv)
    if not args.engagement.is_dir():
        print(f"not a directory: {args.engagement}", file=sys.stderr)
        return 2
    print(json.dumps(read_state(args.engagement), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
