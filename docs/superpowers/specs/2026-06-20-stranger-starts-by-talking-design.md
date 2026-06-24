# "A Stranger Starts by Talking" — Portability + Conversational Front Door

**Date:** 2026-06-20
**Status:** Approved (brainstorm complete)
**Milestone:** Foundation (#86), under epic #85 — second chunk after the stdlib-only engine core (#90, merged)

## Why

After the stdlib-only core (#90), the engine *can* run on bare `python3`. But it
still **can't run for an installed user**, and an installed user has no way to
*start* by talking. Two concrete defects, both reproduced:

1. **The engine is un-runnable from any real install.** From a working directory
   that isn't the plugin root:
   - `python3 -m engine.run` → `ModuleNotFoundError: No module named 'engine'`
   - `python3 /abs/path/engine/run.py` → same error (`run.py` does
     `from engine.compute import …` but never puts the plugin root on
     `sys.path`)
   - `PYTHONPATH=<plugin-root> python3 -m engine.run` → works

   Every numeric skill instructs `python -m engine.run <folder>/`, which only
   works because the author's cwd happens to be the plugin root. On a real
   install the plugin lives in `~/.claude/plugins/cache/.../` while the
   engagement folder is in some other project — so this fails on the first
   engine run of the first assessment.

2. **The session-start hook is hard-broken for anyone but the author.**
   `hooks/session-start.sh` gates on the literal path
   `/Users/daveraffaele/Desktop/ai-cockpit` and injects a renamed-away skill
   (`using-methodology` under `ai-usecase-methodology`). For any other user it
   `exit 0`s — no methodology, no onboarding.

This chunk fixes both and turns session-start into a conversational front door,
so a non-expert installs the plugin, describes what they want to assess in plain
language, and gets real, audited numbers — on any machine, on bare `python3`.

This directly serves the two launch-blocking criteria from the north star:
(a) a non-expert completes a full assessment using only natural language, zero
methodology vocabulary leaked; (b) a clean-machine install runs a sample and
produces real numbers.

## Goals

- The engine and state CLIs run from **any** working directory, invoked by
  absolute path, on **bare `python3`** — no venv, no `PYTHONPATH`, no `cd`.
- Session start is **path-agnostic** and works on every install location, and
  becomes the conversational doorbell that routes a user into the Conductor.
- The Conductor (`conducting-engagement`) is rehabilitated to the new reality:
  no venv prerequisite, bare `python3`, plugin root resolved durably.
- A non-expert's first run is a warm, zero-jargon conversation, not a README.

## Non-Goals (scope boundaries)

- **No `bin/` shell wrapper.** Rejected during brainstorm: a wrapper needs a
  Windows twin kept in sync and is useless on Claude.ai (no shell). The
  self-locating Python module is OS-agnostic and degrades to the Claude.ai
  Python sandbox.
- **No Claude.ai packaging work** beyond the portability that falls out for
  free. Claude Code + Cowork remain the first-class surfaces.
- **No Slice 2/3 features** (parallel fan-out, granular autonomy, editing,
  flywheel). This is Foundation portability + onboarding only.

## Design

### Component 1 — Self-locating entrypoints

`engine/run.py` and `state/state.py` both import their sibling package at module
top (`from engine.compute import …`, `from state.phases import …`), which
executes *before* `main()`. So a `sys.path` fix inside `main()` is too late; it
must run at the very top of the module, before those imports, and only when the
module is invoked as a script by path (not when imported as a package by tests
or `-m`):

```python
import sys
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.compute import (...)   # unchanged
```

- Run as `python3 /abs/.../engine/run.py <folder>` → `__name__ == "__main__"`,
  `__package__ == ""` → the guard fires, plugin root goes on `sys.path`, the
  package imports resolve.
- Imported as `engine.run` (pytest, `python3 -m engine.run`) → `__package__ ==
  "engine"` → guard skips, behavior byte-identical to today.

`Path(__file__).resolve().parent.parent` is the plugin root: `run.py`'s parent
is `engine/`, whose parent is the root; `state.py`'s parent is `state/`, whose
parent is the root. Both are correct.

**Regression guard (the test that pins the actual bug):** from a foreign cwd
(`tmp_path`), run `python3 <repo>/engine/run.py <seeded-engagement>` and
`python3 <repo>/state/state.py <seeded-engagement>` as
subprocesses with `cwd=tmp_path` and a clean env (no `PYTHONPATH`); assert exit
0 and that `results.json` / a valid JSON snapshot is produced. This is the test
that would have caught the shipped defect.

### Component 2 — Path-agnostic session-start hook

Rewrite `hooks/session-start.sh`, `hooks/session-start.ps1`, and the Cursor
variant `hooks/hooks-cursor.json` reference so they:

1. **Delete the hardcoded gate.** No `CLAUDE_PROJECT_DIR` path check; no
   `ai-usecase-methodology` / `using-methodology` names.
2. **Always fire** (install = opt-in), unless `AI_ASSESSMENT_SILENT=1` is set
   (then `exit 0` silently).
3. **Resolve interpreter and root on the real machine:** pick `python3` if
   present, else `python`; read plugin root from `CLAUDE_PLUGIN_ROOT` (the var
   the hook is already invoked with in `hooks.json`).
4. **Inject a compact front-door note** containing:
   - the resolved plugin root (absolute) and interpreter — the one durable
     token every engine/state command needs;
   - the exact engine and state command forms, e.g.
     `python3 <root>/engine/run.py <folder>/` and
     `python3 <root>/state/state.py <folder>/`;
   - one resume-agnostic line: "If you're resuming an assessment I'll pick up
     where we left off; if you're starting fresh, just tell me what you'd like
     to assess — you don't need to know any commands or phase names."

**The hook stays dumb (Refinement A).** It does **not** detect whether an
engagement exists — `conducting-engagement`'s drive loop already resolves "the
folder containing a `.conductor.md` whose work is incomplete." Duplicating that
in fragile shell is rejected. The hook's only conditional is `AI_ASSESSMENT_SILENT`.

The injected note is wrapped so the model treats it as standing context (the
existing hook already wraps injected skill text in `<EXTREMELY_IMPORTANT>`; keep
that convention for the front-door note).

**Cross-platform:** `.sh` (bash) and `.ps1` (PowerShell) carry identical logic;
both are minimal (resolve two values, print a fixed template). No third script.

### Component 3 — Root delivery: inject + stamp + reconcile

The plugin root is the single token every engine/state command needs, and
`CLAUDE_PLUGIN_ROOT` only exists at hook time. Because this harness does not
persist shell state between commands, the model must reconstruct the full
command each time from one durable value. Delivery has two complementary
mechanisms covering different windows:

- **Hook injection** covers the cold first session — at that moment no
  engagement folder exists yet, so there is nothing to read from disk.
- **`.conductor.md`** covers every session after. At Intake,
  `conducting-engagement` stamps `engine_root` (absolute) into `.conductor.md`
  (already stdlib-JSON after #90, already written there alongside `register` /
  `autonomy` / `methodology_version`). The drive loop reads it from the
  `state.state` snapshot.

**Reconciliation (self-healing).** Early in the drive loop each session, compare
the live hook-injected root against the stamped `engine_root`. The live value
wins; if they differ (plugin upgraded to a new version-stamped cache path, or
the engagement was copied to another machine), re-stamp. Because the hook fires
fresh at every session start — before compaction can drop the value — the
re-stamp always runs against a correct root. `engine_root` lives only in the
gitignored engagement folder, so storing an absolute machine path there never
leaks across machines via git.

`state.state` must surface `engine_root` in its JSON snapshot so the drive loop
reads it through the existing channel rather than re-parsing `.conductor.md`.

### Component 4 — Rehabilitate the skills

**`conducting-engagement`:**
- **Prerequisites:** replace the venv/`pyyaml` prerequisite block with the new
  reality — the core runs on bare `python3`; the plugin root comes from the
  session-start note (cold session) or `.conductor.md` (`engine_root`,
  thereafter); no venv is required for an assessment.
- **Intake step 4:** stamp `engine_root` into `.conductor.md` alongside the
  existing keys.
- **Drive loop step 0/1:** resolve `engine_root` from the `state.state`
  snapshot; reconcile against the live hook value (hook wins, re-stamp on
  mismatch) before any engine/state call.
- **Command swap:** every `python -m engine.run …` / `python -m state.state …`
  becomes `python3 <engine_root>/engine/run.py …` / `python3
  <engine_root>/state/state.py …`.
- **Cold-start greeting:** sharpen to a warm, zero-jargon opening that infers
  register in one line and never names a phase, file, or command.

**Standalone numeric skills** (`identifying-opportunities`,
`building-business-case`, `scoring-opportunities`, `building-checkpoint`): each
runs as its own session, so each resolves `engine_root` from `.conductor.md` at
its Session Start, then uses the `python3 <engine_root>/engine/run.py …` form.
Apply the same command swap everywhere these skills hardcode `python -m
engine.run`.

## Testing

- **Self-location (Component 1):** subprocess tests invoking `engine/run.py` and
  `state/state.py` by absolute path from a foreign cwd with a clean env; assert
  exit 0 and correct output. Plus a test asserting the import-as-package path
  (`-m` / pytest) is unchanged (the `__package__` guard does not fire).
- **Hook (Component 2):** run `session-start.sh` with `CLAUDE_PLUGIN_ROOT` set
  and assert: (a) the injected note contains the resolved root and the engine
  command form; (b) no hardcoded author path or dead skill name appears in the
  output; (c) `AI_ASSESSMENT_SILENT=1` produces empty output and exit 0;
  (d) the note carries the resume-agnostic front-door line.
- **Root delivery (Component 3):** `engine_root` round-trips through
  `write_conductor` / `read_conductor`; `state.state` surfaces it in the
  snapshot; a reconcile unit asserts "live value differs → re-stamped".
- **Golden invariant:** `model/results.json` for the lattice fixture stays
  byte-identical (the `sys.path` guard must not change compute output).
- **Full suite** green (currently 211 passing).

## Risks / Open Edges

- **Compaction still possible before the first stamp.** In the cold first
  session, if compaction hits between session start and Intake-step-4, the root
  could be lost before it's stamped. Mitigation: Intake stamps `engine_root`
  early (it already runs Phase 1 / creates the folder near the top of Intake),
  minimizing the window. Acceptable residual risk.
- **`python` resolving to Python 2** on ancient machines. Mitigation: prefer
  `python3`; the `python` fallback is last-resort and the engine targets py3
  syntax, which fails loudly rather than silently miscomputing.

## Decomposition for plans

One spec, likely two plans:

1. **Portability core:** Component 1 (self-locating entrypoints + tests),
   Component 2 (path-agnostic hook + tests), Component 3 state-layer pieces
   (`engine_root` in `.conductor.md` + `state.state` snapshot + reconcile unit).
   All Python/shell, independently testable, auto-merge-eligible.
2. **Skill rehabilitation:** Component 4 (Conductor + numeric-skill rewrites,
   greeting). Markdown-heavy → human-merge under the auto-review policy.
