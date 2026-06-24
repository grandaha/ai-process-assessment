# Slice 3 · Chunk B — `conductor-status` Surfacing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure-Python status projection (`state/status.py`) that composes the existing readers into one human-oriented view, with a CLI and a Conductor section that narrates it jargon-free.

**Architecture:** `status_view(root)` calls `state.state.read_state`, `state.conductor_state.read_conductor`, `state.staleness.changed_inputs`, and `state.integrity.check_integrity`, and assembles a presentation dict (progress, current step, blocked, attention, interaction, complete). It re-derives nothing — every status string and gate verdict comes from the composed functions. A thin `main` prints JSON; a Conductor SKILL.md section narrates on "where are we?".

**Tech Stack:** Python standard library only + `state.*`. pytest (`.venv/bin/python -m pytest`).

## Global Constraints

- **Stdlib-only + `state.*`.** No third-party imports.
- **Pure.** No mutation, no subprocess, no network. (Spec §3.1.)
- **Compose, never re-derive.** Phase status, gate logic, hashing, and integrity all come from the composed functions verbatim. (Spec §6.)
- **`current_step` matches only `"available"`** — `read_state` never emits `"overridden"`; CLAUDE.md overrides are out of scope. (Spec §3.2.)
- **`complete` = `current_step is None and grc_status != "required" and deliverable_status == "done"`.** (Spec §3.2.)
- **`partial_state` items carry `kind`, `target`, `repair`, `detail`.** (Spec §3.2.)
- **`gates_due`:** `"grc"` when grc status `== "required"`; `"deliverable"` when `current_step is None and deliverable_status != "done"`. (Spec §3.2.)
- **CLI contract:** JSON to stdout, exit `0` for a valid dir, exit `2` + stderr `not a directory: <path>` otherwise — identical to `state/state.py` / `state/integrity.py`. (Spec §3.3.)
- **Conductor narration is jargon-free** — no phase/file/skill names or ids in the narration block. (Epic AC-1.)

---

## File Structure

- `state/status.py` — **create**: `status_view(root) -> dict`, `main` (CLI).
- `state/tests/test_status.py` — **create**: projection unit tests.
- `state/tests/test_status_cli.py` — **create**: CLI JSON + exit codes.
- `skills/conducting-engagement/SKILL.md` — **modify**: add `## Status on demand` + narration block.
- `tests/test_conductor_skill.py` — **modify**: guards for the new section.

---

### Task 1: `status_view` projection

**Files:**
- Create: `state/status.py`
- Test: `state/tests/test_status.py`

**Interfaces:**
- Consumes: `state.state.read_state`, `state.conductor_state.read_conductor`, `state.staleness.changed_inputs`, `state.integrity.check_integrity`.
- Produces: `status_view(root) -> dict` with the shape in the spec §3.2.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_status.py`:

```python
from state.conductor_state import write_conductor
from state.staleness import hash_inputs
from state.status import status_view


def test_fresh_engagement_projection(engagement):
    root = engagement(**{"scope.md": "# Scope\ncontent\n"})
    v = status_view(root)
    assert v["engagement"] == root.name
    assert v["progress"]["done"] == 1 and v["progress"]["total"] == 12
    assert v["progress"]["percent"] == round(100 * 1 / 12)
    # Phase 1 done -> Phase 2 is the current step.
    assert v["current_step"]["id"] == "2"
    # interaction empty on a fresh engagement (no .conductor.md)
    assert v["interaction"]["register"] is None
    assert v["interaction"]["autonomy"] is None
    assert v["interaction"]["deferred_processes"] == []
    assert v["interaction"]["open_decisions"] == []
    # nothing needs attention
    assert v["attention"] == {"gates_due": [], "stale_inputs": [], "partial_state": []}
    assert v["complete"] is False


def test_blocked_phases_listed(engagement):
    root = engagement(**{"scope.md": "x"})
    v = status_view(root)
    blocked_ids = {b["id"] for b in v["blocked"]}
    assert "3" in blocked_ids  # Tech & Data waits on Context
    b3 = next(b for b in v["blocked"] if b["id"] == "3")
    assert b3["waiting_on"]  # carries a reason string


def test_interaction_surfaced_from_conductor(engagement):
    root = engagement(**{"scope.md": "x"})
    write_conductor(root, {
        "register": "operator",
        "autonomy": {"should_confirm": "batched"},
        "deferred_processes": ["PROC-009"],
        "open_decisions": ["scope-boundary"],
    })
    v = status_view(root)
    assert v["interaction"]["register"] == "operator"
    assert v["interaction"]["autonomy"] == "batched"
    assert v["interaction"]["deferred_processes"] == ["PROC-009"]
    assert v["interaction"]["open_decisions"] == ["scope-boundary"]


def test_complete_requires_all_phases_grc_and_gate_b(engagement):
    # Every phase output present (folder indexes carry a bare header, no data rows
    # -> no drift, GRC not-required), plus Gate B clearance.
    files = {
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n", "opportunities/_index.md": "| OPP-ID |\n",
        "scores/_index.md": "| OPP-ID |\n", "roadmap.md": "x",
        "usecase-briefs/_index.md": "| UC-NNN |\n", "cost-actuals.md": "x",
        "business-case.md": "x", "executive-summary.md": "x", "deliverable.html": "x",
        "evidence-log.md": "x",
    }
    root = engagement(**files)
    v = status_view(root)
    assert v["current_step"] is None
    assert v["progress"]["percent"] == 100
    assert v["attention"]["gates_due"] == []
    assert v["attention"]["partial_state"] == []
    assert v["complete"] is True


def test_done_except_gate_b_is_not_complete(engagement):
    files = {
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n", "opportunities/_index.md": "| OPP-ID |\n",
        "scores/_index.md": "| OPP-ID |\n", "roadmap.md": "x",
        "usecase-briefs/_index.md": "| UC-NNN |\n", "cost-actuals.md": "x",
        "business-case.md": "x", "executive-summary.md": "x", "deliverable.html": "x",
    }  # no evidence-log.md
    root = engagement(**files)
    v = status_view(root)
    assert v["current_step"] is None
    assert "deliverable" in v["attention"]["gates_due"]
    assert v["complete"] is False


def test_determinism(engagement):
    root = engagement(**{"scope.md": "x"})
    assert status_view(root) == status_view(root)


def test_attention_stale_inputs(engagement):
    # Record a hash for baselines, then change the file -> staleness fires.
    root = engagement(**{"model/baselines.json": '[{"process_id": "PROC-001"}]'})
    recorded = hash_inputs(root)              # current hash of baselines.json
    write_conductor(root, {"model_input_hashes": recorded})
    (root / "model" / "baselines.json").write_text('[{"process_id": "PROC-002"}]')
    v = status_view(root)
    assert "baselines" in v["attention"]["stale_inputs"]


def test_attention_partial_state_carries_detail(engagement):
    root = engagement(**{"scope.md": "   "})  # whitespace-only -> empty_output
    v = status_view(root)
    ps = v["attention"]["partial_state"]
    assert any(i["kind"] == "empty_output" and i["target"] == "scope.md"
               and i["repair"] == "surface" and i["detail"] for i in ps)


def test_attention_grc_gate_due(engagement):
    # An opportunities index with a Yellow GRC flag makes Gate A required. A valid
    # matching body keeps Chunk A integrity quiet so the assertion targets gates_due.
    idx = ("| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
           "| --- | --- | --- | --- | --- | --- | --- |\n"
           "| OPP-001 | PROC-001 | AIAugmentation | Green | Green | Yellow | addressing-root |\n")
    root = engagement(**{
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n",
        "opportunities/_index.md": idx,
        "opportunities/OPP-001.md": ("## OPP-001 — X\n<!-- index: id=OPP-001 process=PROC-001 "
                                     "type=AIAugmentation feasibility=Green data=Green grc=Yellow "
                                     "struct=addressing-root -->\n\nbody\n"),
    })
    v = status_view(root)
    assert "grc" in v["attention"]["gates_due"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_status.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.status'`.

- [ ] **Step 3: Create the module**

Create `state/status.py`:

```python
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

    stale = changed_inputs(root, conductor.get("model_input_hashes", {}))
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
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_status.py -v`
Expected: PASS (all six).

- [ ] **Step 5: Commit**

```bash
git add state/status.py state/tests/test_status.py
git commit -m "feat(state): status_view projection (slice3 chunkB)"
```

---

### Task 2: CLI entry point

**Files:**
- Modify: `state/status.py`
- Test: `state/tests/test_status_cli.py`

**Interfaces:**
- Consumes: `status_view`.
- Produces: `main(argv=None) -> int` — prints `json.dumps(status_view(...), indent=2)`; returns 0 for a valid directory, prints `not a directory: <path>` to stderr and returns 2 otherwise.

- [ ] **Step 1: Write the failing test**

Create `state/tests/test_status_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "status.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_prints_json_and_exits_zero(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("x")
    res = _run([str(eng)])
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["engagement"] == "acme"
    assert payload["current_step"]["id"] == "2"


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "missing")])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_status_cli.py -v`
Expected: FAIL — no `main`/`__main__`, so the subprocess prints nothing (assertions fail).

- [ ] **Step 3: Append the CLI**

Append to `state/status.py`:

```python
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
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_status_cli.py -v`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add state/status.py state/tests/test_status_cli.py
git commit -m "feat(state): status CLI (JSON out, exit codes) (slice3 chunkB)"
```

---

### Task 3: Conductor wiring — "Status on demand" section + guards

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `state/status.py` CLI (`python3 <engine_root>/state/status.py <folder>`).
- Produces: a `## Status on demand` section with a fenced `<!-- status-narration:start -->`/`:end` block. Guarded by `tests/test_conductor_skill.py`.

- [ ] **Step 1: Write the failing guard tests**

In `tests/test_conductor_skill.py`, append `"## Status on demand"` to the `REQUIRED_HEADINGS` list, and add:

```python
def test_conductor_status_on_demand_section():
    sec = _section(SKILL.read_text(), "## Status on demand")
    # Reads the status projection by absolute path.
    assert "state/status.py" in sec
    # Read-only: surfacing status never advances the drive loop.
    assert "read-only" in sec.lower() or "does not advance" in sec.lower()
    # Jargon-free narration block is present and fenced.
    assert "<!-- status-narration:start -->" in sec
    assert "<!-- status-narration:end -->" in sec
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — section heading missing.

- [ ] **Step 3: Add the section**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **before** the `## Resuming into a messy state` section (so the two read-time helpers sit together):

````markdown
## Status on demand

When the user asks where things stand — "where are we?", "what's left?", "what do you need
from me?", "status?" — read `python3 <engine_root>/state/status.py <folder>` and narrate it
in plain language. This is **read-only**: surfacing status never advances the drive loop or
mutates anything.

The projection gives you: how far along (`progress`), the current step, what's `blocked`,
an `attention` bucket (`gates_due`, `stale_inputs`, `partial_state`), the `interaction` mode,
and a `complete` flag. Translate it — never read the raw field names, phase numbers, file
names, or ids aloud:

- **Progress** → a friendly fraction or "about two-thirds of the way."
- **Current step** → describe what it *does* next, not its name ("I'll put rough numbers to
  the opportunities"), not "Phase 6 / scoring-opportunities."
- **Attention** → only if non-empty: a decision they still owe (`open_decisions`), numbers
  being re-run (`stale_inputs`), something to redo together (`partial_state` — use each
  item's `detail`), or a gate to clear (`gates_due`). If a deliverable gate is owed because
  the work is done, frame it as "all that's left is the final sign-off," not "Gate B not-run."
- **Mode** → mention only if it helps ("I'm moving autonomously — say the word to slow down").
- **Complete** → if true, say the engagement is wrapped and offer the deliverable.

<!-- status-narration:start -->
> We're about two-thirds of the way through. Right now I'm lining up which opportunities to
> take forward; next I'll put rough numbers to them. Nothing's waiting on you at the moment —
> I'll flag it the second something needs your call.
<!-- status-narration:end -->
````

- [ ] **Step 4: Run the guard tests + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS (new guards green; whole suite green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): status on demand — jargon-free narration (slice3 chunkB)"
```

---

## Final verification

- [ ] Whole suite: `.venv/bin/python -m pytest -q` — all green.
- [ ] `python3 state/status.py sample-pso-delivery/` prints a sensible projection (complete sample → high progress, `partial_state: []`) — a real-data smoke check.
