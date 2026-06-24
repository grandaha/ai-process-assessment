# Portability Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the engine and state CLIs runnable by absolute path from any working directory on bare `python3`, make the session-start hook path-agnostic and a conversational front door, and plumb `engine_root` through the state layer so the model can reconstruct every command from one durable token.

**Architecture:** Three independent components. (1) A `__package__` guard at the top of `engine/run.py` and `state/state.py` puts the plugin root on `sys.path` only when the module is invoked as a script by path — byte-identical behavior under `-m`/pytest. (2) The session-start hook (`.sh` + `.ps1`) drops the hardcoded author-path gate, always fires unless silenced, resolves interpreter + `CLAUDE_PLUGIN_ROOT` on the real machine, and injects a compact front-door note. (3) `engine_root` round-trips through `.conductor.md`, surfaces in the `state.state` snapshot, and self-heals via a reconcile helper.

**Tech Stack:** Python 3 standard library only (no third-party imports in `engine/` or `state/` runtime modules); bash + PowerShell for hooks; pytest for tests.

## Global Constraints

- **Runtime is pure stdlib.** Do NOT add any third-party import (`yaml`, `openpyxl`, `formulas`, etc.) to any module under `engine/` or `state/`. The stdlib-core guard `engine/tests/test_stdlib_core.py` (which blocks `{"yaml", "openpyxl", "formulas"}` at import) must stay green.
- **Golden numbers are frozen.** `model/results.json` for the lattice fixture must stay byte-identical. `engine/tests/test_lattice_golden.py` pins this. The `sys.path` guard must not change any compute output.
- **The guard fires only as-a-script.** The `if __package__ in (None, "")` block must put the plugin root on `sys.path` ONLY when run as `python3 /abs/.../engine/run.py …`. Under `python3 -m engine.run` or pytest (`__package__ == "engine"` / `"state"`) it must NOT fire — behavior byte-identical to today.
- **Plugin root = `Path(__file__).resolve().parent.parent`.** For `engine/run.py` that is `engine/`'s parent (the root); for `state/state.py` that is `state/`'s parent (the root). Both correct.
- **Do NOT edit `skills/using-methodology/SKILL.md` or `system-prompt.md`.** They are kept verbatim-synced by a guard test (`tests/test_guards.py`); their `python -m engine.run` mentions are conceptual module references, out of scope for this plan.
- **No test currently pins the hook's body.** This plan adds the first hook tests. The hook no longer injects the keystone skill body; the methodology reaches the model through the normal skill mechanism (Claude Code) and `system-prompt.md` (claude.ai).
- **Full suite stays green.** Baseline is **203 passing**. Every task ends with the full suite green.
- **Run tests with the repo venv:** `.venv/bin/python -m pytest …` (the suite's frontmatter parsing imports `pyyaml`, a dev/test-only dep; the runtime does not need it).
- **Auto-merge eligibility:** this plan is Python/shell only. Keep it free of methodology-prose/markdown-skill edits so it stays auto-merge-eligible under the auto-review policy.

---

## File Structure

- `engine/run.py` — add the self-locating guard above the package imports (Component 1).
- `state/state.py` — add the same guard; also surface `engine_root` in the snapshot (Components 1 + 3).
- `engine/tests/test_portability.py` — **new** — subprocess tests proving both CLIs run from a foreign cwd by absolute path, plus an import-path-unchanged assertion (Component 1).
- `hooks/session-start.sh` — rewrite: drop gate, always-fire, resolve root+interpreter, inject front-door note (Component 2).
- `hooks/session-start.ps1` — rewrite to identical logic in PowerShell (Component 2).
- `tests/test_session_start_hook.py` — **new** — runs `session-start.sh` and asserts note content, silence opt-out, no dead author path/skill name (Component 2).
- `state/conductor_state.py` — add `reconcile_engine_root()` helper (Component 3).
- `state/tests/test_conductor_state.py` — add `engine_root` round-trip + reconcile unit tests (Component 3).
- `state/tests/test_state.py` — add a test that `read_state` surfaces `engine_root` from `.conductor.md` (Component 3).

---

### Task 1: Self-locating entrypoints

Add the `__package__` guard to both `engine/run.py` and `state/state.py`, and prove with subprocess tests that each runs from a foreign cwd invoked by absolute path with a clean env — the test that would have caught the shipped defect.

**Files:**
- Modify: `engine/run.py` (insert guard between the stdlib imports and the `from engine.compute import …` line, currently `engine/run.py:9-15`)
- Modify: `state/state.py` (insert guard between the stdlib imports and the `from state.phases import …` line, currently `state/state.py:11-13`)
- Test: `engine/tests/test_portability.py` (new)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing other tasks consume directly. The guard is internal; `main(argv)` signatures and module import behavior are unchanged.

- [ ] **Step 1: Write the failing test**

Create `engine/tests/test_portability.py`:

```python
"""Proves the engine and state CLIs run by absolute path from any cwd.

Each test invokes the entrypoint as a script (not -m) from a foreign working
directory with a clean environment (no PYTHONPATH). This is the regression
guard for the shipped defect: `python3 /abs/engine/run.py <folder>` used to
raise ModuleNotFoundError because run.py never put the plugin root on sys.path.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"


def _seed_engagement(tmp_path: Path) -> Path:
    """Copy the lattice fixture model into a fresh engagement folder under tmp_path."""
    eng = tmp_path / "engagement"
    model = eng / "model"
    model.mkdir(parents=True)
    for f in FIXTURE.glob("*.json"):
        if f.name == "results.json":
            continue  # results is a derived output, not an input
        (model / f.name).write_text(f.read_text(), encoding="utf-8")
    return eng


def _clean_env() -> dict:
    """A minimal environment with no PYTHONPATH leaking the repo onto sys.path."""
    import os
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return env


def test_engine_run_by_absolute_path_from_foreign_cwd(tmp_path):
    eng = _seed_engagement(tmp_path)
    res = subprocess.run(
        [sys.executable, str(REPO / "engine" / "run.py"), str(eng)],
        cwd=str(tmp_path), env=_clean_env(),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    results = json.loads((eng / "model" / "results.json").read_text())
    assert results["wave1_aggregate"]["investment_point"] is not None


def test_state_by_absolute_path_from_foreign_cwd(tmp_path):
    eng = _seed_engagement(tmp_path)
    res = subprocess.run(
        [sys.executable, str(REPO / "state" / "state.py"), str(eng)],
        cwd=str(tmp_path), env=_clean_env(),
        capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    snapshot = json.loads(res.stdout)
    assert snapshot["engagement"] == "engagement"
    assert "phases" in snapshot


def test_import_as_package_path_is_unchanged():
    """Imported as a package (pytest / -m), the guard must NOT fire."""
    import engine.run
    import state.state
    assert engine.run.__package__ == "engine"
    assert state.state.__package__ == "state"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_portability.py -v`
Expected: the two subprocess tests FAIL — `res.returncode` is non-zero and `res.stderr` contains `ModuleNotFoundError: No module named 'engine'` (and `'state'`). The `test_import_as_package_path_is_unchanged` test PASSES already.

- [ ] **Step 3: Add the guard to `engine/run.py`**

In `engine/run.py`, the current top is:

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.compute import (
    AACE_CLASS5_LABEL, cost_structure, initiative_rom, payback,
    score_composite, value_range, wave1_aggregate, wave1_point,
)
```

Insert the guard between the stdlib imports and the `from engine.compute import …` block so it runs before the package import:

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.compute import (
    AACE_CLASS5_LABEL, cost_structure, initiative_rom, payback,
    score_composite, value_range, wave1_aggregate, wave1_point,
)
```

- [ ] **Step 4: Add the guard to `state/state.py`**

In `state/state.py`, the current top is:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from state.phases import GATES, MODEL_INPUTS, PHASES
```

Insert the guard before the `from state.phases import …` block:

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.phases import GATES, MODEL_INPUTS, PHASES
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_portability.py -v`
Expected: all four tests PASS.

- [ ] **Step 6: Run the golden + stdlib-core guards**

Run: `.venv/bin/python -m pytest engine/tests/test_lattice_golden.py engine/tests/test_stdlib_core.py -v`
Expected: PASS — the guard changed neither compute output nor the stdlib-only property.

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (203 prior + 4 new = 207).

- [ ] **Step 8: Commit**

```bash
git add engine/run.py state/state.py engine/tests/test_portability.py
git commit -m "feat(portability): self-locating engine/state entrypoints"
```

---

### Task 2: Path-agnostic session-start hook

Rewrite `session-start.sh` and `session-start.ps1` to drop the hardcoded author-path gate, always fire (unless `AI_ASSESSMENT_SILENT=1`), resolve interpreter + plugin root on the real machine, and inject a compact front-door note. Add the first hook tests.

**Files:**
- Modify (rewrite): `hooks/session-start.sh`
- Modify (rewrite): `hooks/session-start.ps1`
- Test: `tests/test_session_start_hook.py` (new)

No change to `hooks/hooks.json` or `hooks/hooks-cursor.json` — both already invoke `session-start.sh` by `${CLAUDE_PLUGIN_ROOT}` path; their wiring is unaffected.

**Interfaces:**
- Consumes: nothing from earlier tasks. (The note's engine/state command forms use `python3 <root>/engine/run.py` — the same absolute-path form Task 1 made runnable.)
- Produces: the front-door note text (a fixed template). Component 4's skill rehab assumes the model receives `engine_root` from this note on the cold first session.

- [ ] **Step 1: Write the failing test**

Create `tests/test_session_start_hook.py`:

```python
"""The session-start hook is the path-agnostic conversational front door.

It must fire on any install location, inject the resolved plugin root and the
engine/state command forms, carry a resume-agnostic greeting line, honor the
silence opt-out, and contain no hardcoded author path or dead skill name.
"""
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "session-start.sh"


def _run(env_extra: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = "/tmp/some/install/location"
    env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK)], env=env, capture_output=True, text=True,
    )


def test_note_contains_resolved_root_and_engine_command():
    out = _run({}).stdout
    assert "/tmp/some/install/location" in out
    assert "/tmp/some/install/location/engine/run.py" in out
    assert "/tmp/some/install/location/state/state.py" in out


def test_note_has_resume_agnostic_front_door_line():
    out = _run({}).stdout
    assert "resuming" in out.lower()
    assert "you don't need to know any commands or phase names" in out.lower()


def test_silence_opt_out_produces_no_output():
    res = _run({"AI_ASSESSMENT_SILENT": "1"})
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def test_no_dead_author_path_or_skill_name():
    out = _run({}).stdout
    assert "/Users/daveraffaele" not in out
    assert "ai-usecase-methodology" not in out
    assert "ai-cockpit" not in out


def test_note_is_wrapped_for_standing_context():
    out = _run({}).stdout
    assert "<EXTREMELY_IMPORTANT>" in out
    assert "</EXTREMELY_IMPORTANT>" in out
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_session_start_hook.py -v`
Expected: FAIL — the current hook `exit 0`s because `CLAUDE_PROJECT_DIR` is not the author path, so stdout is empty.

- [ ] **Step 3: Rewrite `hooks/session-start.sh`**

Replace the entire file with:

```bash
#!/usr/bin/env bash
# Path-agnostic conversational front door. Fires on every install (opt-in by
# installing the plugin) unless AI_ASSESSMENT_SILENT=1. Injects the one durable
# token every engine/state command needs — the absolute plugin root — plus the
# command forms and a warm, jargon-free greeting. The hook stays dumb: it does
# not detect whether an engagement exists; conducting-engagement resolves that.

if [ "${AI_ASSESSMENT_SILENT:-}" = "1" ]; then
  exit 0
fi

ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$ROOT" ]; then
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

cat <<EOF
<EXTREMELY_IMPORTANT>
This session has the ai-process-assessment plugin installed. It turns plain-language
goals into audited AI/automation opportunity numbers via an 11-phase methodology.

Plugin root: ${ROOT}
Interpreter: ${PY}
Engine command form: ${PY} ${ROOT}/engine/run.py <engagement-folder>/
State command form:  ${PY} ${ROOT}/state/state.py <engagement-folder>/

If you're resuming an assessment I'll pick up where we left off; if you're starting
fresh, just tell me what you'd like to assess — you don't need to know any commands
or phase names.
</EXTREMELY_IMPORTANT>
EOF
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_session_start_hook.py -v`
Expected: all five tests PASS.

- [ ] **Step 5: Rewrite `hooks/session-start.ps1` to identical logic**

Replace the entire file with:

```powershell
# Path-agnostic conversational front door (PowerShell twin of session-start.sh).
# Fires on every install unless AI_ASSESSMENT_SILENT=1. Injects the absolute
# plugin root, the engine/state command forms, and a warm, jargon-free greeting.

if ($env:AI_ASSESSMENT_SILENT -eq "1") { exit 0 }

$root = $env:CLAUDE_PLUGIN_ROOT
if ([string]::IsNullOrEmpty($root)) { exit 0 }

if (Get-Command python3 -ErrorAction SilentlyContinue) { $py = "python3" } else { $py = "python" }

@"
<EXTREMELY_IMPORTANT>
This session has the ai-process-assessment plugin installed. It turns plain-language
goals into audited AI/automation opportunity numbers via an 11-phase methodology.

Plugin root: $root
Interpreter: $py
Engine command form: $py $root/engine/run.py <engagement-folder>/
State command form:  $py $root/state/state.py <engagement-folder>/

If you're resuming an assessment I'll pick up where we left off; if you're starting
fresh, just tell me what you'd like to assess — you don't need to know any commands
or phase names.
</EXTREMELY_IMPORTANT>
"@
```

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (207 prior + 5 new = 212).

- [ ] **Step 7: Commit**

```bash
git add hooks/session-start.sh hooks/session-start.ps1 tests/test_session_start_hook.py
git commit -m "feat(portability): path-agnostic session-start front door"
```

---

### Task 3: `engine_root` state plumbing

Make `engine_root` round-trip through `.conductor.md`, surface in the `state.state` snapshot, and self-heal via a reconcile helper. This is the durable channel the Conductor reads every session after the cold first one.

**Files:**
- Modify: `state/conductor_state.py` (add `reconcile_engine_root()`)
- Modify: `state/state.py` (surface `engine_root` in `read_state`'s snapshot)
- Test: `state/tests/test_conductor_state.py` (add round-trip + reconcile tests)
- Test: `state/tests/test_state.py` (add a snapshot-surfaces-engine_root test)

**Interfaces:**
- Consumes: `read_conductor` / `write_conductor` from `state/conductor_state.py` (existing — they already round-trip arbitrary string keys, so `engine_root` stores as a plain key).
- Produces:
  - `reconcile_engine_root(root: Path, live_root: str) -> str` — reads the stamped `engine_root` from `.conductor.md`; if it differs from `live_root` (or is absent), re-stamps it to `live_root`; returns the authoritative value (always `live_root`).
  - `read_state(...)` snapshot gains a top-level key `"engine_root"` whose value is the stamped `engine_root` (or `None` if `.conductor.md` has none).

- [ ] **Step 1: Write the failing reconcile + round-trip tests**

Add to `state/tests/test_conductor_state.py`:

```python
from state.conductor_state import (
    read_conductor, write_conductor, reconcile_engine_root,
)


def test_engine_root_round_trips(tmp_path):
    write_conductor(tmp_path, {"engine_root": "/old/install"})
    assert read_conductor(tmp_path)["engine_root"] == "/old/install"


def test_reconcile_restamps_when_live_root_differs(tmp_path):
    write_conductor(tmp_path, {"register": "operator", "engine_root": "/old/install"})
    result = reconcile_engine_root(tmp_path, "/new/install")
    assert result == "/new/install"
    data = read_conductor(tmp_path)
    assert data["engine_root"] == "/new/install"
    assert data["register"] == "operator"  # other keys preserved


def test_reconcile_stamps_when_absent(tmp_path):
    write_conductor(tmp_path, {"register": "operator"})
    result = reconcile_engine_root(tmp_path, "/new/install")
    assert result == "/new/install"
    assert read_conductor(tmp_path)["engine_root"] == "/new/install"


def test_reconcile_no_write_when_matching(tmp_path):
    write_conductor(tmp_path, {"engine_root": "/same/install"})
    before = (tmp_path / ".conductor.md").read_text()
    result = reconcile_engine_root(tmp_path, "/same/install")
    after = (tmp_path / ".conductor.md").read_text()
    assert result == "/same/install"
    assert before == after  # idempotent: no rewrite when already correct
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_conductor_state.py -v`
Expected: `test_engine_root_round_trips` PASSES (write/read already handle arbitrary keys); the three `reconcile_*` tests FAIL with `ImportError: cannot import name 'reconcile_engine_root'`.

- [ ] **Step 3: Add `reconcile_engine_root` to `state/conductor_state.py`**

Append to `state/conductor_state.py`:

```python
def reconcile_engine_root(root: Path, live_root: str) -> str:
    """Self-heal the stamped plugin root against the live hook-injected one.

    The live value wins: if the stamped engine_root is absent or differs (plugin
    upgraded to a new version-stamped cache path, or the engagement was copied to
    another machine), re-stamp to live_root. No rewrite when already correct.
    Returns the authoritative root (always live_root).
    """
    data = read_conductor(root)
    if data.get("engine_root") != live_root:
        data["engine_root"] = live_root
        write_conductor(root, data)
    return live_root
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest state/tests/test_conductor_state.py -v`
Expected: all PASS.

- [ ] **Step 5: Write the failing snapshot test**

Add to `state/tests/test_state.py`:

```python
from state.conductor_state import write_conductor
from state.state import read_state


def test_snapshot_surfaces_engine_root(tmp_path):
    write_conductor(tmp_path, {"engine_root": "/install/path"})
    snap = read_state(tmp_path)
    assert snap["engine_root"] == "/install/path"


def test_snapshot_engine_root_is_none_when_unstamped(tmp_path):
    snap = read_state(tmp_path)
    assert snap["engine_root"] is None
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_state.py -k engine_root -v`
Expected: FAIL — `KeyError: 'engine_root'` (the snapshot has no such key yet).

- [ ] **Step 7: Surface `engine_root` in `read_state`**

In `state/state.py`, add the import near the top package-import block (after the guard, alongside `from state.phases import …`):

```python
from state.conductor_state import read_conductor
from state.phases import GATES, MODEL_INPUTS, PHASES
```

Then in `read_state`, add `engine_root` to the returned dict:

```python
def read_state(engagement_dir: Path | str) -> dict:
    root = Path(engagement_dir)
    phases = _phase_status(root)
    done = sum(1 for p in phases if p["status"] == "done")
    return {
        "engagement": root.name,
        "path": str(root),
        "engine_root": read_conductor(root).get("engine_root"),
        "progress": {"done": done, "total": len(PHASES)},
        "phases": phases,
        "gates": _gate_status(root),
        "model": _model_section(root),
    }
```

Note: `read_conductor` is pure filesystem logic (reads `.conductor.md`), so `read_state` stays a pure function of the filesystem. No import cycle: `conductor_state` imports `state.staleness` → `state.phases`; it does not import `state.state`.

- [ ] **Step 8: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest state/tests/test_state.py -k engine_root -v`
Expected: both PASS.

- [ ] **Step 9: Run the stdlib-core guard and full suite**

Run: `.venv/bin/python -m pytest engine/tests/test_stdlib_core.py -q && .venv/bin/python -m pytest -q`
Expected: stdlib-core green (the new import path stays stdlib-only); full suite all pass (212 prior + 6 new = 218).

- [ ] **Step 10: Commit**

```bash
git add state/conductor_state.py state/state.py state/tests/test_conductor_state.py state/tests/test_state.py
git commit -m "feat(portability): plumb engine_root through state layer"
```

---

## Notes for the executor

- **Branch name:** `feat/portability-core`.
- **Test counts** in "Expected" lines are guides, not asserts — if the real baseline drifted, the relevant signal is that the *new* tests go RED then GREEN and nothing previously green turns RED.
- After all three tasks: the final whole-branch review (opus) should confirm the six Global Constraints — stdlib-only, golden byte-identical, guard fires only as-a-script, keystone/system-prompt untouched, hook body has no dead author path, full suite green.
- This plan is the auto-merge-eligible half of the spec `docs/superpowers/specs/2026-06-20-stranger-starts-by-talking-design.md`. The markdown skill rehab (Component 4) is the separate human-merge plan `2026-06-20-skill-rehabilitation.md`, which depends on Component 3's `engine_root`-in-snapshot and the front-door note shipped here.
