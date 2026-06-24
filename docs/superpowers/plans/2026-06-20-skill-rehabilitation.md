# Skill Rehabilitation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rehabilitate the operational skills to the portable reality shipped by the portability-core plan — bare `python3`, plugin root resolved durably from `<engine_root>`, every engine/state command invoked by absolute path, the false venv/`pyyaml` prerequisite removed, and a warm, jargon-free first turn.

**Architecture:** Markdown-only edits across five skills, gated by new guard tests. The Conductor (`conducting-engagement`) is the front door: it resolves `engine_root` from the session-start note (cold session) or the `state.state` snapshot (thereafter), reconciles it via `reconcile_engine_root`, and stamps it at Intake. The four standalone numeric skills each resolve `engine_root` from `.conductor.md` at their own Session Start and use the absolute-path command form. A blanket guard asserts no operational skill retains a `python -m engine.run` / `python -m state.state` typed-command form.

**Tech Stack:** Markdown skills; pytest guards in `tests/`.

## Global Constraints

- **Depends on the portability-core plan.** That plan (`2026-06-20-portability-core.md`) must be merged first — it ships the self-locating entrypoints (so `python3 <engine_root>/engine/run.py` actually runs), the front-door note (the cold-session source of `engine_root`), `read_state` surfacing `engine_root` in the snapshot, and `reconcile_engine_root()`. This plan references all four.
- **`<engine_root>` is the literal placeholder** used in skill prose for the absolute plugin root. The new command forms are exactly `python3 <engine_root>/engine/run.py <folder>/` and `python3 <engine_root>/state/state.py <folder>/`.
- **Do NOT edit `skills/using-methodology/SKILL.md` or `system-prompt.md`.** They stay verbatim-synced by a guard test. Their two `python -m engine.run` mentions are conceptual module references ("the deterministic engine (`python -m engine.run`)"), not operational run instructions — leave them. The blanket guard in this plan therefore excludes the keystone.
- **Runtime needs no venv.** The state helpers (`conductor_state`, `overrides`, `staleness`) and the engine are pure standard library; nothing under `engine/`/`state/` imports `pyyaml`. `pyyaml`/`pytest` are dev/test-only deps (the test suite parses skill frontmatter). The operator-facing prerequisite must reflect this — bare `python3`, no install step.
- **Inline `python -c` calls that import a `state.`/`engine.` module need `PYTHONPATH`.** The Conductor's Intake stamp and `record_input_hashes` call import `state.conductor_state` — from a foreign cwd they hit the same `ModuleNotFoundError`. Make them `PYTHONPATH="<engine_root>" python3 -c "…"`. (The scoring-opportunities `python3 -c` block is pure stdlib — `json, re, pathlib` — and needs no change.)
- **Human-merge only.** This plan is methodology-prose/markdown. Under the auto-review policy it is NOT auto-merge-eligible — it lands via a human-reviewed PR.
- **Full suite stays green.** Run with `.venv/bin/python -m pytest -q`. Baseline is the count after portability-core merges.

---

## File Structure

- `skills/conducting-engagement/SKILL.md` — prerequisites rewrite, `engine_root` resolution + reconcile in the drive loop, Intake stamps `engine_root` (portable `-c`), command swaps, greeting sharpen (Task 1).
- `skills/identifying-opportunities/SKILL.md` — command swap + Session-Start `engine_root` resolution (Task 2).
- `skills/building-business-case/SKILL.md` — command swap + Session-Start `engine_root` resolution (Task 2).
- `skills/scoring-opportunities/SKILL.md` — command swap (incl. the negative mentions) + Session-Start `engine_root` resolution (Task 2).
- `skills/building-checkpoint/SKILL.md` — command swap (incl. the negative mentions) + Session-Start `engine_root` resolution (Task 2).
- `tests/test_portable_skill_commands.py` — **new** — guard tests for both tasks (Task 1 adds the Conductor guards; Task 2 adds the blanket numeric-skill guard).

---

### Task 1: Rehabilitate the Conductor

Rewrite `conducting-engagement` to the portable reality: bare-`python3` prerequisites, `engine_root` resolution + reconcile in the drive loop, `engine_root` stamped at Intake (portable `-c`), absolute-path command forms, and a warm jargon-free greeting.

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Test: `tests/test_portable_skill_commands.py` (new)

**Interfaces:**
- Consumes (from portability-core): the front-door note's `Plugin root:` line; the `state.state` snapshot's `engine_root` field; `reconcile_engine_root(root, live_root)`; `record_input_hashes(root)`.
- Produces: the `engine_root` stamp in `.conductor.md` that the four numeric skills (Task 2) read at their own Session Start.

- [ ] **Step 1: Write the failing guard test**

Create `tests/test_portable_skill_commands.py`:

```python
"""Guards that operational skills use the portable absolute-path command form.

The keystone (using-methodology) is intentionally excluded — its `python -m
engine.run` mentions are conceptual module references kept verbatim-synced with
system-prompt.md.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"


def _body(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_conductor_has_no_module_command_form():
    body = _body("conducting-engagement")
    assert "python -m engine.run" not in body
    assert "python -m state.state" not in body
    assert "python3 -m engine.run" not in body
    assert "python3 -m state.state" not in body


def test_conductor_uses_engine_root_command_form():
    body = _body("conducting-engagement")
    assert "python3 <engine_root>/engine/run.py" in body
    assert "python3 <engine_root>/state/state.py" in body


def test_conductor_prerequisites_have_no_venv_or_pyyaml():
    body = _body("conducting-engagement")
    assert "python3 -m venv" not in body
    assert "pip install -r requirements.txt" not in body
    assert "pyyaml" not in body.lower()


def test_conductor_resolves_and_reconciles_engine_root():
    body = _body("conducting-engagement")
    assert "engine_root" in body
    assert "reconcile_engine_root" in body
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_portable_skill_commands.py -v`
Expected: all four FAIL — the current skill carries `python -m engine.run`, `python3 -m venv`, `pyyaml`, and no `<engine_root>`/`reconcile_engine_root` text.

- [ ] **Step 3: Replace the Prerequisites section**

In `skills/conducting-engagement/SKILL.md`, replace the entire `## Prerequisites (first run on a host)` section (currently lines 22–34, from the heading through the line ending `…you can use it directly.`) with:

```markdown
## Prerequisites

The state helpers and the engine are pure Python **standard library** — no venv, no
`pip install`, no third-party deps. Any `python3` runs them. You need exactly one
durable value: the **plugin root** — the absolute path to this installed plugin.

- **Cold first session:** the session-start hook injects it as a `Plugin root: <path>`
  line, with the engine/state command forms. Use that path.
- **Every session after:** it is stamped in the engagement's `.conductor.md` as
  `engine_root` and surfaced in the `state.state` snapshot's `engine_root` field.

Throughout this skill, `<engine_root>` denotes that path. Every engine/state command is
invoked by absolute path: `python3 <engine_root>/engine/run.py <folder>/` and
`python3 <engine_root>/state/state.py <folder>/`.

(Contributors running the test suite additionally need `pyyaml`/`pytest` from
`requirements.txt`; that is a development dependency, not a prerequisite for running an
assessment.)
```

- [ ] **Step 4: Sharpen the Intake greeting (step 1)**

In Intake step 1, the example greeting already infers register in one line. Confirm it names no phase, file, or command, and leave its substance intact. Replace the example sentence only if it leaks jargon — the current text is:

> Example: "Sounds like you're assessing your own team — I'll keep it plain and explain as we go; tell me if you'd rather I move fast."

Keep it (it is warm, zero-jargon, names nothing). No edit required unless a reviewer flags leaked vocabulary.

- [ ] **Step 5: Stamp `engine_root` at Intake (step 4), portably**

Replace Intake step 4 (currently lines 48–51) with:

```markdown
4. **Stamp `.conductor.md`** with `register`, `autonomy.should_confirm`,
   `methodology_version` (read from `.claude-plugin/plugin.json`), `engine_root`
   (the absolute plugin root from the session-start note), and empty
   `open_decisions` / `deferred_processes`. Use:
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import write_conductor; ..."`.
```

- [ ] **Step 6: Resolve + reconcile `engine_root` in the drive loop**

In `## The drive loop`, insert a new step 0 (renumber existing 0→0 stays "Resolve the active engagement" — keep it) by adding a dedicated resolution step immediately after the existing step 0 ("Resolve the active engagement") and before step 1 ("Read state"). Insert:

```markdown
0a. **Resolve `engine_root`:** take the live plugin root from the session-start note
   (injected fresh every session start). This is the value all commands below use.
```

Then change step 1 ("Read state") from:

> 1. **Read state:** `python -m state.state <folder>` → JSON snapshot.

to:

```markdown
1. **Read state:** `python3 <engine_root>/state/state.py <folder>` → JSON snapshot.
   Then **reconcile:** compare the snapshot's `engine_root` to the live root from the
   session-start note; if they differ (plugin upgraded to a new cache path, or the
   engagement was copied to another machine), re-stamp via
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import reconcile_engine_root; reconcile_engine_root('<folder>', '<engine_root>')"`.
   The live value always wins.
```

- [ ] **Step 7: Swap the remaining engine commands**

In drive-loop step 6 (currently line 79), change:

> 6. **After a step that wrote a `model/*.json` input,** run `python -m engine.run <folder>/`
>    then `state.conductor_state.record_input_hashes(folder)`.

to:

```markdown
6. **After a step that wrote a `model/*.json` input,** run
   `python3 <engine_root>/engine/run.py <folder>/` then
   `PYTHONPATH="<engine_root>" python3 -c "from state.conductor_state import record_input_hashes; record_input_hashes('<folder>')"`.
```

In the `## Staleness` section (currently line 151), change:

> When `changed_inputs` is non-empty: re-run `python -m engine.run <folder>/`, then …

to:

```markdown
When `changed_inputs` is non-empty: re-run `python3 <engine_root>/engine/run.py <folder>/`, then …
```

Leave the bare module-name references untouched — line 73's "`state.state` reports the GRC gate" and line 159's "`engine.run` errors" name the module conceptually and carry no `python -m` typed form. The guard targets only the typed command form, so these are fine.

- [ ] **Step 8: Run the guard test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_portable_skill_commands.py -v`
Expected: the four `test_conductor_*` tests PASS.

- [ ] **Step 9: Run the methodology/skill guard suite and full suite**

Run: `.venv/bin/python -m pytest tests/test_guards.py tests/test_skills.py tests/test_conductor_skill.py -q && .venv/bin/python -m pytest -q`
Expected: all PASS — the verbatim-sync guard stays green (keystone untouched), and no skill-structure guard regresses.

- [ ] **Step 10: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_portable_skill_commands.py
git commit -m "feat(skills): rehabilitate Conductor for portable engine_root"
```

---

### Task 2: Portable command form across the numeric skills

Swap every typed `python -m engine.run` / `python -m state.state` form to the absolute-path `python3 <engine_root>/…` form across the four standalone numeric skills, and give each a Session-Start line that resolves `engine_root` from `.conductor.md`. Add a blanket guard covering all five operational skills.

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md`
- Modify: `skills/building-business-case/SKILL.md`
- Modify: `skills/scoring-opportunities/SKILL.md`
- Modify: `skills/building-checkpoint/SKILL.md`
- Test: `tests/test_portable_skill_commands.py` (add the blanket guard)

**Interfaces:**
- Consumes: the `engine_root` stamp written by the Conductor at Intake (Task 1); `read_conductor` for the Session-Start resolution wording.
- Produces: nothing downstream — these are leaf operational skills.

- [ ] **Step 1: Add the failing blanket guard**

Append to `tests/test_portable_skill_commands.py`:

```python
NUMERIC_SKILLS = [
    "identifying-opportunities",
    "building-business-case",
    "scoring-opportunities",
    "building-checkpoint",
]


def test_numeric_skills_have_no_module_command_form():
    offenders = []
    for name in NUMERIC_SKILLS:
        body = _body(name)
        for bad in ("python -m engine.run", "python -m state.state",
                    "python3 -m engine.run", "python3 -m state.state"):
            if bad in body:
                offenders.append(f"{name}: {bad}")
    assert not offenders, offenders


def test_numeric_skills_resolve_engine_root_at_session_start():
    for name in NUMERIC_SKILLS:
        body = _body(name)
        assert "engine_root" in body, name


def test_skills_invoking_engine_use_absolute_path_form():
    # Skills that actually run the engine must use the absolute-path form.
    for name in ("identifying-opportunities", "building-business-case",
                 "building-checkpoint"):
        body = _body(name)
        assert "python3 <engine_root>/engine/run.py" in body, name
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_portable_skill_commands.py -k numeric -v`
Expected: FAIL — all four skills still carry `python -m engine.run` and none mentions `engine_root`.

- [ ] **Step 3: Edit `identifying-opportunities`**

Add a Session-Start resolution line at the top of the skill's operational body (after its frontmatter/intro, before the first command), e.g.:

```markdown
**Session Start — resolve `engine_root`:** read `engine_root` (the absolute plugin root)
from this engagement's `.conductor.md` (`read_conductor`). Every engine command below is
`python3 <engine_root>/engine/run.py …`.
```

Then in the line currently at `skills/identifying-opportunities/SKILL.md:44`, change:

> Then run `python -m engine.run <engagement-folder>/` and cite the resulting `results.json` …

to:

> Then run `python3 <engine_root>/engine/run.py <engagement-folder>/` and cite the resulting `results.json` …

- [ ] **Step 4: Edit `building-business-case`**

Add the same Session-Start resolution line near the top of the skill body. Then swap all three occurrences:

- Line 27: `python -m engine.run <engagement-folder>/` → `python3 <engine_root>/engine/run.py <engagement-folder>/`
- Line 128: `python -m engine.run <engagement-folder>/` → `python3 <engine_root>/engine/run.py <engagement-folder>/`
- Line 143: `python -m engine.run <engagement-folder>/` → `python3 <engine_root>/engine/run.py <engagement-folder>/`

- [ ] **Step 5: Edit `scoring-opportunities`**

Add the same Session-Start resolution line near the top. Then swap the negative mention at line 99:

> Note: `python -m engine.run` is **not** called in Phase 6. The full engine run (which produces `model/results.json`) happens in Phase 9 …

to:

> Note: `python3 <engine_root>/engine/run.py` is **not** called in Phase 6. The full engine run (which produces `model/results.json`) happens in Phase 9 …

Leave the `python3 -c "…"` block (Step 2, ~line 134) unchanged — it imports only `json, re, pathlib` (stdlib) and runs from any cwd.

- [ ] **Step 6: Edit `building-checkpoint`**

Add the same Session-Start resolution line near the top. Then swap both occurrences:

- Line 90: `re-run `python -m engine.run <name>/`` → `re-run `python3 <engine_root>/engine/run.py <name>/``
- Line 92: `the engine is **not** run at this checkpoint — `python -m engine.run` is a Phase 9 step` → `the engine is **not** run at this checkpoint — `python3 <engine_root>/engine/run.py` is a Phase 9 step`

- [ ] **Step 7: Run the blanket guard to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_portable_skill_commands.py -v`
Expected: all guards PASS (Task 1's conductor guards + Task 2's numeric guards).

- [ ] **Step 8: Run the skill-structure guards and full suite**

Run: `.venv/bin/python -m pytest tests/test_guards.py tests/test_skills.py -q && .venv/bin/python -m pytest -q`
Expected: all PASS. Confirm specifically that `test_system_prompt_embeds_methodology` (verbatim sync) stays green — the keystone and `system-prompt.md` were not touched.

- [ ] **Step 9: Commit**

```bash
git add skills/identifying-opportunities/SKILL.md skills/building-business-case/SKILL.md skills/scoring-opportunities/SKILL.md skills/building-checkpoint/SKILL.md tests/test_portable_skill_commands.py
git commit -m "feat(skills): portable engine command form across numeric skills"
```

---

## Notes for the executor

- **Branch name:** `feat/skill-rehabilitation`. Depends on `feat/portability-core` being merged to `main` first.
- **Human-merge:** open a PR and stop. Do NOT auto-merge — this is methodology prose.
- **Markdown editing is fiddly:** read each skill before editing; the line numbers above are from the pre-edit state and will drift as you edit. Anchor edits on the exact old-string snippets quoted, not on line numbers.
- **Keystone is off-limits:** if any step tempts you to touch `skills/using-methodology/SKILL.md` or `system-prompt.md`, stop — that is a Global Constraint violation and breaks the verbatim-sync guard.
- After both tasks: the final whole-branch review confirms the four Global-Constraint pillars — no venv/`pyyaml` in operator prereqs, no typed `python -m` form in any operational skill, keystone/system-prompt untouched (sync guard green), full suite green.
