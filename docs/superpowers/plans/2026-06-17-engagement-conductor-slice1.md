# Engagement Conductor — Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Minimum Viable Conductor — a `conducting-engagement` skill that drives the 11-phase methodology end-to-end (sequential processes, guided autonomy), backed by four small deterministic Python helpers it calls for state, staleness, override reconciliation, and its own private state.

**Architecture:** The Conductor is a thin orchestration *skill* (prose) that derives "what's next" from the filesystem via `cockpit.state.read_state()` and three new sibling helpers in the `cockpit/` package. Interview-heavy phases (1, 4, 8.5) run inline in the Conductor; headless transform phases run in subagents with an explicit input contract. All engagement *content* stays in the existing phase skills — unchanged. The Conductor's only private state is `<engagement>/.conductor.md`.

**Tech Stack:** Python 3 (stdlib + `pyyaml`, already a dependency), `pytest`, Markdown skill files. No new dependencies.

**Design spec:** `docs/superpowers/specs/2026-06-17-engagement-conductor-design.md`. Section references below (e.g., §4.4) point there.

## Global Constraints

- Python style matches the existing `cockpit/` package: `from __future__ import annotations` at the top of every module; type hints on all signatures; pure functions, no network, no mutation of engagement content. (Copy the conventions in `cockpit/state.py`.)
- New helper code lives in the `cockpit/` package; its tests live in `cockpit/tests/` and reuse the `engagement` fixture from `cockpit/tests/conftest.py`.
- No new third-party dependencies. `pyyaml` (already in `requirements.txt`) is the only parser allowed for frontmatter.
- Phase skills' content is **not modified**. The Conductor supervises them; it never edits their analytical logic.
- The new skill ID is exactly `ai-process-assessment:conducting-engagement`, and its directory is `skills/conducting-engagement/` (name must match directory — enforced by `tests/test_skills.py`).
- Commit after every task with a `feat(conductor):` or `test(conductor):` prefixed message ending with the repo's `Co-Authored-By:` trailer.
- Engagement folders are git-ignored; never commit an engagement folder created during testing.

---

## File Structure

**New files:**
- `cockpit/staleness.py` — content-hash staleness detection over `model/*.json` inputs.
- `cockpit/overrides.py` — parse the CLAUDE.md Methodology Overrides table; reconcile a snapshot against authorized skips.
- `cockpit/conductor_state.py` — read/write `<engagement>/.conductor.md` frontmatter.
- `cockpit/tests/test_state_cli.py`, `cockpit/tests/test_staleness.py`, `cockpit/tests/test_overrides.py`, `cockpit/tests/test_conductor_state.py` — unit tests.
- `skills/conducting-engagement/SKILL.md` — the Conductor orchestration skill (prose).
- `tests/test_conductor_skill.py` — structural guard that the skill contains its load-bearing sections.

**Modified files:**
- `pytest.ini` — add `cockpit/tests` to `testpaths` so cockpit + conductor tests run in CI.
- `cockpit/state.py` — add a `main()` + `__main__` block exposing `python -m cockpit.state <folder>` as a one-shot JSON printer.
- `tests/test_skills.py` — add the new skill to the non-phase allow-list; bump the skill count.

---

## Task 1: Run cockpit + conductor tests in CI

**Why first:** CI runs `pytest -q`, whose `testpaths` is `tests engine/tests` — it currently collects **zero** cockpit tests. Every helper below lives in `cockpit/tests/`, so without this fix none of the new tests gate CI.

**Files:**
- Modify: `pytest.ini`

- [ ] **Step 1: Confirm the gap**

Run: `python -m pytest -q --collect-only | grep -c "cockpit/tests"`
Expected: `0` (cockpit tests are not collected by the default run).

- [ ] **Step 2: Add `cockpit/tests` to testpaths**

Edit `pytest.ini` to read exactly:

```ini
[pytest]
testpaths = tests engine/tests cockpit/tests
python_files = test_*.py
python_functions = test_*
```

- [ ] **Step 3: Verify cockpit tests now collect and pass**

Run: `python -m pytest -q`
Expected: the existing cockpit suite (≈30 tests) now runs alongside the rest; all green.

- [ ] **Step 4: Commit**

```bash
git add pytest.ini
git commit -m "test(cockpit): include cockpit/tests in default pytest run

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: One-shot state CLI — `python -m cockpit.state`

The Conductor's "eyes." `read_state()` already exists and is fully tested; this task only adds a command-line entry that prints its JSON snapshot to stdout, so the skill can shell out to it (§4.1).

**Files:**
- Modify: `cockpit/state.py` (append a `main()` and `__main__` guard; do not touch `read_state`)
- Test: `cockpit/tests/test_state_cli.py`

**Interfaces:**
- Consumes: `cockpit.state.read_state(engagement_dir) -> dict` (existing).
- Produces: `cockpit.state.main(argv: list[str] | None = None) -> int` — parses `argv` for one positional engagement folder, prints `json.dumps(read_state(folder), indent=2)` to stdout, returns `0`; prints an error to stderr and returns `2` if the folder is not a directory. Module is runnable as `python -m cockpit.state <folder>`.

- [ ] **Step 1: Write the failing test**

```python
# cockpit/tests/test_state_cli.py
import json
import subprocess
import sys

from cockpit.state import main


def test_main_prints_valid_json_snapshot(engagement, capsys):
    root = engagement("scope.md")
    rc = main([str(root)])
    out = capsys.readouterr().out
    snap = json.loads(out)
    assert rc == 0
    assert snap["engagement"] == "acme-engagement"
    by_id = {p["id"]: p for p in snap["phases"]}
    assert by_id["1"]["status"] == "done"
    assert by_id["2"]["status"] == "available"


def test_main_rejects_non_directory(tmp_path, capsys):
    rc = main([str(tmp_path / "does-not-exist")])
    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


def test_module_is_runnable(engagement):
    root = engagement("scope.md", "context.md")
    proc = subprocess.run(
        [sys.executable, "-m", "cockpit.state", str(root)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["progress"]["done"] == 2
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest cockpit/tests/test_state_cli.py -v`
Expected: FAIL — `ImportError: cannot import name 'main'` (and the subprocess test fails: no `__main__` entry).

- [ ] **Step 3: Implement `main()` and the `__main__` guard**

Append to `cockpit/state.py` (after `read_state`):

```python
def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="cockpit.state")
    parser.add_argument("engagement", help="path to the engagement folder")
    args = parser.parse_args(argv)
    folder = Path(args.engagement)
    if not folder.is_dir():
        print(f"not a directory: {folder}", file=sys.stderr)
        return 2
    print(json.dumps(read_state(folder), indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

Add `import sys` to the existing imports at the top of the file (keep `import json` and `from pathlib import Path`, which are already present).

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest cockpit/tests/test_state_cli.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add cockpit/state.py cockpit/tests/test_state_cli.py
git commit -m "feat(conductor): add python -m cockpit.state one-shot JSON CLI

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Content-hash staleness detection

When a `model/*.json` input changes, everything downstream is stale (§9). The signal is a SHA-256 content hash, chosen over mtime because the repo lives in an iCloud-synced folder where timestamps are unreliable. This module computes hashes and compares against the hashes recorded at the last engine run.

**Files:**
- Create: `cockpit/staleness.py`
- Test: `cockpit/tests/test_staleness.py`

**Interfaces:**
- Consumes: `cockpit.phases.MODEL_INPUTS: dict[str, str]` (existing; keys are model input stems: `baselines`, `value`, `scores`, `initiatives`, `costs`).
- Produces:
  - `hash_inputs(root: Path) -> dict[str, str]` — for each `model/<stem>.json` that exists, the SHA-256 hex of its bytes, keyed by stem. Missing files are omitted.
  - `changed_inputs(root: Path, recorded: dict[str, str]) -> list[str]` — stems whose current hash differs from `recorded`, plus stems present now but absent from `recorded`, sorted. A stem in `recorded` but missing on disk is also "changed" (it was deleted).

- [ ] **Step 1: Write the failing test**

```python
# cockpit/tests/test_staleness.py
from cockpit.staleness import hash_inputs, changed_inputs


def test_hash_inputs_only_includes_present_files(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    hashes = hash_inputs(root)
    assert set(hashes) == {"baselines"}
    assert len(hashes["baselines"]) == 64  # sha256 hex


def test_no_change_when_content_identical(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    assert changed_inputs(root, recorded) == []


def test_detects_changed_content(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    (root / "model" / "baselines.json").write_text('{"a": 2}')
    assert changed_inputs(root, recorded) == ["baselines"]


def test_new_input_counts_as_changed(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    (root / "model" / "value.json").write_text('{"v": 1}')
    assert changed_inputs(root, recorded) == ["value"]


def test_deleted_input_counts_as_changed(engagement):
    root = engagement(**{"model/scores.json": "[]"})
    recorded = hash_inputs(root)
    (root / "model" / "scores.json").unlink()
    assert changed_inputs(root, recorded) == ["scores"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest cockpit/tests/test_staleness.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cockpit.staleness'`.

- [ ] **Step 3: Implement the module**

```python
# cockpit/staleness.py
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest cockpit/tests/test_staleness.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add cockpit/staleness.py cockpit/tests/test_staleness.py
git commit -m "feat(conductor): content-hash staleness detection for model inputs

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: CLAUDE.md override reconciliation

`read_state()` is pure file logic and doesn't know an *authorized* phase skip exists. The CLAUDE.md Methodology Overrides table records deliberate deviations; this module parses real (non-placeholder) override rows and marks the named phases as satisfied so downstream phases unblock (§10).

**Files:**
- Create: `cockpit/overrides.py`
- Test: `cockpit/tests/test_overrides.py`

**Interfaces:**
- Consumes: `cockpit.phases.PHASES` (existing list of `Phase(id, name, skill, output, predecessor)`).
- Produces:
  - `parse_overrides(claude_md_text: str) -> set[str]` — the set of phase `output` paths authorized to skip. A row qualifies only if it is a real 3-column table row whose Override cell names a known phase (by output filename, full skill id, or bare skill dir name) **and** whose Reason and Authorized-by cells are both non-empty and contain no template placeholder (`<`, `e.g.,`, `fill in`).
  - `reconcile(snapshot: dict, authorized: set[str]) -> dict` — mutates and returns `snapshot`: each phase whose `output` is in `authorized` and is not already `done` becomes `status="overridden"`, `blocked_reason=None`; then any phase still `blocked` whose predecessor is now satisfied (`done` or `overridden`, or `None`) becomes `available`.

- [ ] **Step 1: Write the failing test**

```python
# cockpit/tests/test_overrides.py
from cockpit.overrides import parse_overrides, reconcile
from cockpit.state import read_state


REAL = (
    "| Override | Reason | Authorized by |\n"
    "|---|---|---|\n"
    "| Skip context mapping (context.md) | reuse from prior engagement | Dana Lee |\n"
)
PLACEHOLDER = (
    "| Override | Reason | Authorized by |\n"
    "|---|---|---|\n"
    "| <e.g., Skip context mapping> | <e.g., same client> | <name> |\n"
)


def test_parses_real_override_to_output_path():
    assert parse_overrides(REAL) == {"context.md"}


def test_ignores_placeholder_template_row():
    assert parse_overrides(PLACEHOLDER) == set()


def test_ignores_row_missing_reason_or_authorizer():
    text = (
        "| Override | Reason | Authorized by |\n"
        "|---|---|---|\n"
        "| Skip context.md |  |  |\n"
    )
    assert parse_overrides(text) == set()


def test_matches_by_bare_skill_name():
    text = (
        "| Override | Reason | Authorized by |\n"
        "|---|---|---|\n"
        "| Skip mapping-context | stable | Dana |\n"
    )
    assert parse_overrides(text) == {"context.md"}


def test_reconcile_unblocks_phase_after_overridden_predecessor(engagement):
    root = engagement("scope.md")  # phase 1 done, 2 available, 3 blocked
    snap = reconcile(read_state(root), {"context.md"})
    by_id = {p["id"]: p for p in snap["phases"]}
    assert by_id["2"]["status"] == "overridden"
    assert by_id["3"]["status"] == "available"
    assert by_id["3"]["blocked_reason"] is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest cockpit/tests/test_overrides.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cockpit.overrides'`.

- [ ] **Step 3: Implement the module**

```python
# cockpit/overrides.py
"""Reconcile a state snapshot with authorized deviations in CLAUDE.md.

read_state() is pure file logic; it cannot know a phase was deliberately skipped.
The CLAUDE.md "Methodology Overrides" table records those decisions. This module
turns real override rows into satisfied phases so downstream phases unblock.
"""
from __future__ import annotations

from cockpit.phases import PHASES

_PLACEHOLDERS = ("<", "e.g.,", "fill in")


def _tokens() -> dict[str, str]:
    """Map every recognizable phase token -> that phase's output path."""
    tokens: dict[str, str] = {}
    for p in PHASES:
        tokens[p.output] = p.output
        tokens[p.skill] = p.output
        tokens[p.skill.split(":")[-1]] = p.output  # bare dir name
    return tokens


def parse_overrides(claude_md_text: str) -> set[str]:
    tokens = _tokens()
    authorized: set[str] = set()
    for line in claude_md_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != 3:
            continue
        override, reason, authorizer = cells
        if override.lower() == "override" or set(override) <= {"-"}:
            continue  # header or separator row
        joined = " ".join(cells).lower()
        if any(ph in joined for ph in _PLACEHOLDERS):
            continue  # untouched template row
        if not reason or not authorizer:
            continue  # incomplete row — not a real authorization
        for token, output in tokens.items():
            if token and token in override:
                authorized.add(output)
    return authorized


def reconcile(snapshot: dict, authorized: set[str]) -> dict:
    by_output = {p.output: p for p in PHASES}
    for ph in snapshot["phases"]:
        if ph["output"] in authorized and ph["status"] != "done":
            ph["status"] = "overridden"
            ph["blocked_reason"] = None
    satisfied = {
        ph["output"] for ph in snapshot["phases"]
        if ph["status"] in ("done", "overridden")
    }
    for ph in snapshot["phases"]:
        if ph["status"] == "blocked":
            phase = by_output[ph["output"]]
            if phase.predecessor is None or phase.predecessor in satisfied:
                ph["status"] = "available"
                ph["blocked_reason"] = None
    return snapshot
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest cockpit/tests/test_overrides.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add cockpit/overrides.py cockpit/tests/test_overrides.py
git commit -m "feat(conductor): reconcile state snapshot with CLAUDE.md overrides

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Conductor private state — read/write `.conductor.md`

The Conductor's only private state (§11): register, autonomy preset, methodology version, last action, open decisions, deferred processes, and the model-input hashes that power staleness (§9). Stored as YAML frontmatter in `<engagement>/.conductor.md`. This module is the typed reader/writer so the skill and the staleness helper agree on the format.

**Files:**
- Create: `cockpit/conductor_state.py`
- Test: `cockpit/tests/test_conductor_state.py`

**Interfaces:**
- Consumes: `pyyaml` (`import yaml`); `cockpit.staleness.hash_inputs`.
- Produces:
  - `CONDUCTOR_FILE = ".conductor.md"` (module constant).
  - `read_conductor(root: Path) -> dict` — parse the YAML frontmatter block (between the first two `---` lines) of `<root>/.conductor.md`; return `{}` if the file is absent. Missing keys are not defaulted here (caller decides).
  - `write_conductor(root: Path, data: dict) -> None` — write `data` as a frontmatter-only `.conductor.md` (a leading `---`, the YAML, a closing `---`, trailing newline). Overwrites.
  - `record_input_hashes(root: Path) -> dict` — convenience: set `data["model_input_hashes"] = hash_inputs(root)` on the current conductor dict, persist, and return the updated dict. Used right after an engine run.

- [ ] **Step 1: Write the failing test**

```python
# cockpit/tests/test_conductor_state.py
from cockpit.conductor_state import (
    read_conductor, write_conductor, record_input_hashes, CONDUCTOR_FILE,
)


def test_read_absent_returns_empty(engagement):
    assert read_conductor(engagement()) == {}


def test_write_then_read_roundtrips(engagement):
    root = engagement()
    data = {
        "register": "operator",
        "autonomy": {"should_confirm": "guided"},
        "methodology_version": "2.13.1",
        "deferred_processes": [],
    }
    write_conductor(root, data)
    assert (root / CONDUCTOR_FILE).exists()
    assert read_conductor(root) == data


def test_record_input_hashes_persists_current_model(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    write_conductor(root, {"register": "consultant"})
    updated = record_input_hashes(root)
    assert "baselines" in updated["model_input_hashes"]
    assert read_conductor(root)["model_input_hashes"] == updated["model_input_hashes"]
    assert read_conductor(root)["register"] == "consultant"  # preserved
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest cockpit/tests/test_conductor_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cockpit.conductor_state'`.

- [ ] **Step 3: Implement the module**

```python
# cockpit/conductor_state.py
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest cockpit/tests/test_conductor_state.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add cockpit/conductor_state.py cockpit/tests/test_conductor_state.py
git commit -m "feat(conductor): read/write .conductor.md private state

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: The `conducting-engagement` skill

The orchestration prose. This is the Conductor itself — it reads state via the helpers from Tasks 2–5 and drives the loop. It is not unit-testable as logic; its automated guard (Task 7) asserts the load-bearing sections exist, and the end-to-end check (Task 8) drives the sample engagement. Write every section; the content below is the required substance, not a summary to expand later.

**Files:**
- Create: `skills/conducting-engagement/SKILL.md`

**Interfaces:**
- Consumes (as shell commands the skill instructs the model to run): `python -m cockpit.state <folder>`; the helper functions are invoked via short inline Python (`python -c "from cockpit.conductor_state import ..."`) or described as procedures. The engine: `python -m engine.run <folder>/`.
- Produces: a registered skill `ai-process-assessment:conducting-engagement` (consumed by Task 7's allow-list and count).

- [ ] **Step 1: Write the SKILL.md**

Create `skills/conducting-engagement/SKILL.md` with this frontmatter (exact) and the sections below.

````markdown
---
name: ai-process-assessment:conducting-engagement
description: Front door and autonomous driver — on a natural-language request ("help me find AI opportunities", "assess this client/team"), drives the full 11-phase methodology end-to-end: derives state from the engagement folder, interviews only for gaps, dispatches phases, runs the engine, and stops only at genuine human-decision points. Honors using-methodology as the rulebook.
---

# Conducting an Engagement

<EXTREMELY-IMPORTANT>
You are the driver. The human should never need to know the phase names, the file
layout, or which skill to invoke. You derive what's next from the engagement folder
and take the next action yourself, pausing only at the touchpoints in the table below.
You honor `ai-process-assessment:using-methodology` as the rulebook — you never skip a
phase or compute a number in prose. CLAUDE.md overrides this skill only where it says so.
</EXTREMELY-IMPORTANT>

## When this skill runs

On any natural-language opener that means "assess / find AI opportunities / evaluate
automation" for a team, client, process, or use case. You become the front door — no
magic phrase required.

## Intake (first contact only)

1. **Infer register, confirm in one line.** From how they phrased the request, infer
   **consultant** (domain-fluent, relaying interviews they ran) or **operator** (their
   own team, no methodology training). Confirm in a single sentence and move on — never
   a cold multiple-choice quiz. Example: "Sounds like you're assessing your own team —
   I'll keep it plain and explain as we go; tell me if you'd rather I move fast."
2. **Set autonomy preset** (default **guided**): guided = confirm each phase transition
   and every checkpoint/gate; autonomous = drive without per-step confirmation, stopping
   only at must-ask points. (Slice 1 runs should-confirm in guided mode.)
3. **Run Phase 1** inline (`ai-process-assessment:scoping-engagement`) — this creates the
   engagement folder, `scope.md`, and the gitignore entry.
4. **Stamp `.conductor.md`** with `register`, `autonomy.should_confirm`,
   `methodology_version` (read from `.claude-plugin/plugin.json`), and empty
   `open_decisions` / `deferred_processes`. Use:
   `python -c "from cockpit.conductor_state import write_conductor; ..."`.

## The drive loop

Repeat until Phase 11 is done and Gate B is cleared:

0. **Resolve the active engagement:** the folder containing a `.conductor.md` whose work
   is incomplete. None → run Intake. More than one incomplete → ask which.
1. **Read state:** `python -m cockpit.state <folder>` → JSON snapshot.
2. **Reconcile overrides:** apply `cockpit.overrides.parse_overrides(CLAUDE.md)` +
   `reconcile(...)` so authorized skips don't block.
3. **Check staleness:** load `model_input_hashes` from `.conductor.md`; if
   `cockpit.staleness.changed_inputs(folder, recorded)` is non-empty, a model input
   changed — re-run the engine and re-drive the affected portfolio phases forward
   (see "Staleness" below) before doing anything else.
4. **Pick the next step:** the first phase whose status is `available`/`overridden`.
   Respect the convergence gate (below) before any portfolio phase.
5. **Gather gaps, then execute** per the execution model below.
6. **After a step that wrote a `model/*.json` input,** run `python -m engine.run <folder>/`
   then `cockpit.conductor_state.record_input_hashes(folder)`.
7. **At a checkpoint insertion point** (per the `building-checkpoint` registry: after
   Phase 2 `scope`, Phase 4 `baseline`, Phase 7 `portfolio`): offer to generate it
   (should-confirm); its stakeholder **outcome** is must-ask.
8. **If a gate triggers** (GRC non-green in `opportunities/_index.md`, or before any
   external share): run the gate; surface the result.
9. **Record this step's structural-class decisions** to the decision log (below).
10. **Pause** at the right touchpoint (table below); otherwise continue.

## Execution model — who talks to the human (§4.4)

- **Interview-heavy phases run inline in your own context:** Phase 1 (scoping), Phase 4
  (discovery), Phase 8.5 (cost actuals). Conduct their questioning yourself, write the
  output file, then drop the transcript and keep only the state snapshot.
- **Headless phases you dispatch to a subagent:** Phases 2, 3, 5, 6, 7, 9, 10, 11, the
  checkpoints, and the GRC/deliverable gates. A subagent cannot ask the human, so before
  dispatch you must have every input it needs on disk. Hand the subagent the engagement
  folder path and the phase skill to run; receive a one-line confirmation; re-read state.
- **Input contract:** before dispatching a headless phase, confirm its predecessor files
  exist and gather any human-supplied value it needs via a targeted inline question — a
  **must-ask** if it's a decision (e.g., Build/Buy/Partner), a **should-confirm** if it's
  draftable.

## Touchpoint taxonomy

| Class | Behavior | Examples |
|---|---|---|
| Must-ask | Always stop, every mode | Sponsoring question, decision-maker, scope boundaries, out-of-scope process additions, cost actuals, checkpoint outcomes, gate dispositions, Build/Buy/Partner |
| Should-confirm | Guided: pause to approve. (Autonomous batching is Slice 2.) | Context map, opportunity log, scoring rationale, roadmap sequencing |
| Can-infer | Never ask | Run the engine, derive state, pick next phase, assemble deliverable HTML |

## Elastic processes & convergence

- An engagement is one portfolio holding 1..N processes; N=1 is the same spine with one
  process, nothing skipped.
- **Convergence gate:** before the first portfolio phase (Phase 6), confirm
  `processes/_index.md` lists every in-scope process with `Baseline = Ready`. A process
  intentionally held back goes in `.conductor.md` `deferred_processes` (deferring is a
  must-ask). Do not score a half-discovered portfolio.
- **Cross-process chain-detection:** at convergence (Phase 5 → 6), in the merged context
  where all processes' opportunities are visible, scan for a Chain Automation that spans
  process boundaries — a step that is no candidate alone but eliminates a verification
  checkpoint when chained. Per-process work cannot see this; you must.
- **Adding a process:** within stated scope → free (should-confirm), then re-converge.
  Outside scope → must-ask: expand scope or start a new engagement.

## Scope is the container

`scope.md` bounds the engagement. Adding work inside it is routine; adding work outside
it is a must-ask. A genuinely separate concern is a new engagement, not a bigger one.

## Decision log — `<engagement>/decision-log.md`

Record both parties' structural-class decisions (type classification, scores, roadmap
sequencing/wave, choosing between ≥2 viable options, selecting a non-default the rubric
didn't recommend). Never log by your own sense of importance; log by class. Append-only;
never edit a prior entry. When a human overrides your draft, record BOTH — never
overwrite. Entry template:

```
## <ISO datetime> — <decision class> — <OPP/PROC id or "portfolio">
- proposed_by: agent | human
- decided_by: agent-auto | human-ratified | human-overrode
- disposition: accepted | edited | overridden→<X> | invalidated-by-{staleness|checkpoint|gate}
- decision: <what was decided>
- rationale: <why>
- evidence: <file path + section/anchor, or model/*.json key>
```

## Staleness

When `changed_inputs` is non-empty: re-run `python -m engine.run <folder>/`, then
re-drive every portfolio phase downstream of the change. Any human ratification given
against the now-superseded numbers is recorded `invalidated-by-staleness` in the decision
log and re-surfaced per its touchpoint class — never silently kept. After a clean
re-drive, call `record_input_hashes` so outputs read clean again.

## Failure & rejection handling

- Phase subagent fails or `engine.run` errors → stop, surface the error (must-ask). Never
  advance on a failed step.
- Gate rejects → surface the failed dimension, route to its owning phase, re-drive forward.
- Checkpoint rejected → route to the checkpoint's route-back phase (registry), which
  triggers staleness forward.

## Sample mode

If the engagement folder contains `.sample-run.md`, drive with the bundled sample data
and do not prompt for live stakeholders (mirror the existing sample-run convention).
````

- [ ] **Step 2: Sanity-check the frontmatter parses**

Run: `python -c "import pathlib,yaml; t=pathlib.Path('skills/conducting-engagement/SKILL.md').read_text(); print(yaml.safe_load(t.split('---')[1])['name'])"`
Expected: prints `ai-process-assessment:conducting-engagement`.

- [ ] **Step 3: Commit**

```bash
git add skills/conducting-engagement/SKILL.md
git commit -m "feat(conductor): add conducting-engagement orchestration skill

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Register the skill in the guard tests

The skill is intentionally **not** in the Phase Map (it's a cross-cutting driver), so the existing `tests/test_skills.py` will flag it as an orphan and its count assertion will fail until updated. Also add a structural guard that the skill carries its load-bearing sections.

**Files:**
- Modify: `tests/test_skills.py` (allow-list + count)
- Create: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `methodology` session fixture (`tests/conftest.py`), which exposes `methodology.skills` keyed by skill ID.

- [ ] **Step 1: Run the existing skill tests to see them fail**

Run: `python -m pytest tests/test_skills.py -v`
Expected: FAIL — `test_no_orphan_skills` reports `ai-process-assessment:conducting-engagement` as an orphan, and `test_skill_count` expects 18 but finds 19.

- [ ] **Step 2: Add the skill to the allow-list and bump the count**

In `tests/test_skills.py`, add the skill to `ALLOWLIST_NON_PHASE`:

```python
ALLOWLIST_NON_PHASE = {
    "ai-process-assessment:using-methodology",
    "ai-process-assessment:running-sample-engagement",
    "ai-process-assessment:generating-sample-intake",
    "ai-process-assessment:building-checkpoint",
    "ai-process-assessment:conducting-engagement",
}
```

And update `test_skill_count`:

```python
def test_skill_count(methodology):
    # 14 phase skills + 5 allow-listed non-phase skills (incl. the conductor).
    assert len(methodology.skills) == 19
```

- [ ] **Step 3: Write the structural guard for the skill**

```python
# tests/test_conductor_skill.py
"""The conducting-engagement skill must carry its load-bearing sections."""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "conducting-engagement" / "SKILL.md"

REQUIRED_HEADINGS = [
    "## Intake",
    "## The drive loop",
    "## Execution model",
    "## Touchpoint taxonomy",
    "## Elastic processes & convergence",
    "## Decision log",
    "## Staleness",
    "## Failure & rejection handling",
]


def test_skill_exists():
    assert SKILL.exists()


def test_skill_has_all_load_bearing_sections():
    text = SKILL.read_text()
    missing = [h for h in REQUIRED_HEADINGS if h not in text]
    assert not missing, f"conducting-engagement SKILL.md missing sections: {missing}"


def test_skill_names_both_parties_in_decision_log():
    text = SKILL.read_text()
    assert "proposed_by" in text and "decided_by" in text and "disposition" in text
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_skills.py tests/test_conductor_skill.py -v`
Expected: PASS (all skill guards green, including the new structural guard).

- [ ] **Step 5: Commit**

```bash
git add tests/test_skills.py tests/test_conductor_skill.py
git commit -m "test(conductor): register conducting-engagement in skill guards

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: End-to-end validation on the sample engagement

The Conductor's integration test is driving the bundled sample to a cleared deliverable (§14). This is an **agent-run validation, not a pytest** — it exercises the skill prose. Run it, observe, and record the result.

**Files:**
- None created. This task produces an evidence note, committed to the plan's companion log if desired.

- [ ] **Step 1: Full unit suite is green**

Run: `python -m pytest -q`
Expected: all tests pass, including the new `cockpit/tests/*` (now collected via Task 1) and `tests/test_conductor_skill.py`.

- [ ] **Step 2: Drive the sample via the Conductor**

In a fresh session, invoke the `conducting-engagement` skill and ask it to run the sample engagement (the existing `running-sample-engagement` provides the sample intake; the Conductor should detect `.sample-run.md` and drive in sample mode). Let it drive end-to-end.

- [ ] **Step 3: Assert the engagement completed correctly**

Verify in the sample engagement folder:
- All phase outputs exist: `scope.md` … `deliverable.html` (the 12 phase outputs).
- `model/results.json` exists and the deliverable's figures equal their `results.json` values (the deliverable-gate's own check).
- `evidence-log.md` records Gate B clearance.
- `.conductor.md` exists with `model_input_hashes` populated.
- `decision-log.md` exists and contains at least one entry with `proposed_by`/`decided_by`/`disposition`.

Expected: every item present. If any phase stalled because the Conductor couldn't determine the next step or a headless phase tried to prompt the human, capture the transcript — that's a §4.4 input-contract gap to fix before Slice 1 is "done."

- [ ] **Step 4: Record the outcome**

Note pass/fail and any gaps in the session's `.remember` log (or the engagement's `evidence-log.md`). This closes Slice 1.

---

## Finishing the branch

After Task 8 passes, follow the repo's finish-branch protocol (do **not** fold into a task above): bump the version in the three manifests (`make bump VERSION=2.14.0`), add a `## [2.14.0]` CHANGELOG entry describing the Conductor (Slice 1), and open a PR. Slice 2 (parallel fan-out, autonomous batching, holding-the-line posture) and Slice 3 (flywheel hook) are separate plans.
