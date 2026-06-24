# Conversational Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a stranger a warm, jargon-free first-run experience — on an ambiguous cold session the assistant greets them and offers to start a new assessment, continue an existing one, or run the sample — without any GUI, engine, or data change.

**Architecture:** Prose-only. Add a `## First contact` section to the front-door skill (`conducting-engagement`) that runs a decision tree (greet only on ambiguous cold first-contact; offer Continue/Start/Run-sample by what engagements exist), tweak the always-fires session-start hook's closing line in both `.sh`/`.ps1` to name those paths, and lock both with LLM-free guards. The hook stays dumb (no detection); branching lives in the skill.

**Tech Stack:** Markdown skill docs; bash + PowerShell hook scripts; pytest (stdlib) guards.

## Global Constraints

- **Prose only.** No engine/`state/`/data-contract changes; no new Python modules; no new skill.
- **Do NOT edit `skills/using-methodology/SKILL.md` or `system-prompt.md`** (verbatim-sync guard at `tests/test_guards.py`).
- **No version bump** — Foundation chunk; changes accumulate under CHANGELOG `[Unreleased]` (matches #90/#91). Do not edit `.claude-plugin/plugin.json` / `marketplace.json`.
- **No GUI** — the offer is conversational text, not a menu/widget/web UI.
- **Hook stays dumb:** always-fires, no engagement detection; the cold-vs-resume-vs-ambiguous branching is in the skill, not the hook.
- **`.sh` and `.ps1` hooks stay in sync** — same offer wording (modulo shell syntax).
- **Greeting is jargon-free:** the text between `<!-- greeting:start -->` and `<!-- greeting:end -->` must contain no phase names, GRC/convergence/deliverable-gate, or skill-ids. Phase names and skill-ids may appear only OUTSIDE that block (routing prose).
- **Run tests with the venv:** `.venv/bin/python -m pytest` (bare `python3` lacks `pyyaml` used by the `tests/` suite).
- Spec: `docs/superpowers/specs/2026-06-21-conversational-onboarding-design.md`.

---

## File Structure

- `skills/conducting-engagement/SKILL.md` (modify) — new `## First contact` section between "When this skill runs" and "Prerequisites".
- `hooks/session-start.sh` (modify) — closing-line tweak.
- `hooks/session-start.ps1` (modify) — identical closing-line tweak.
- `tests/test_onboarding.py` (new) — the two conductor guards.
- `tests/test_session_start_hook.py` (modify) — add the first-contact-offer assertion + a `.ps1` sync guard.
- `CHANGELOG.md` (modify) — `[Unreleased]` entry.

---

## Task 1: First-contact greeting + hook offer + guards

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Modify: `hooks/session-start.sh`, `hooks/session-start.ps1`
- Modify: `CHANGELOG.md`
- Create: `tests/test_onboarding.py`
- Modify: `tests/test_session_start_hook.py`

**Interfaces:**
- Consumes: nothing new. The decision tree reuses the drive loop's existing "step 0" engagement resolution (no code).
- Produces: a `## First contact` section with a greeting delimited by `<!-- greeting:start -->` / `<!-- greeting:end -->`; hook closing line naming the three paths.

- [ ] **Step 1: Write the failing conductor guards**

Create `tests/test_onboarding.py`:

```python
"""Conversational onboarding (Foundation #86 3.B) guards.

The front-door skill must offer the three first-contact paths, and its user-facing
greeting must stay free of methodology jargon (the "not the raw keystone dump" rule).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONDUCTOR = REPO / "skills" / "conducting-engagement" / "SKILL.md"

# Tokens that mean "the user is being shown the methodology", which the greeting must avoid.
GREETING_BLOCKLIST = (
    [f"Phase {n}" for n in range(1, 12)]
    + ["GRC", "convergence", "deliverable-gate", "ai-process-assessment:"]
)


def _body() -> str:
    return CONDUCTOR.read_text(encoding="utf-8")


def test_conductor_has_first_contact_offer():
    body = _body()
    assert "## First contact" in body, "conducting-engagement is missing the First contact section"
    for label in ("Start an assessment", "Continue", "Run the sample"):
        assert label in body, f"first-contact offer missing the path label: {label!r}"
    assert "ai-process-assessment:running-sample-engagement" in body, \
        "first-contact flow must route the sample to running-sample-engagement"


def test_greeting_is_jargon_free():
    body = _body()
    start = body.find("<!-- greeting:start -->")
    end = body.find("<!-- greeting:end -->")
    assert start != -1 and end != -1 and end > start, \
        "greeting must be wrapped in <!-- greeting:start --> ... <!-- greeting:end -->"
    greeting = body[start:end]
    for token in GREETING_BLOCKLIST:
        assert token not in greeting, f"greeting leaks methodology jargon: {token!r}"
```

- [ ] **Step 2: Run the conductor guards to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_onboarding.py -v`
Expected: FAIL — `## First contact` / greeting delimiters not present yet.

- [ ] **Step 3: Add the `## First contact` section to `conducting-engagement`**

In `skills/conducting-engagement/SKILL.md`, insert this section immediately AFTER the `## When this skill runs` section and BEFORE `## Prerequisites`. Keep all phase-name/skill-id mentions OUTSIDE the greeting delimiters.

````markdown
## First contact

On a **fresh session where the user has not given a clear assess-request and is not
clearly resuming** (they open with "hi", "what is this", or nothing specific), greet them
and offer the paths that fit what already exists — do NOT jump straight into Intake. On a
clear request ("assess my billing team"), skip the greeting and start. On a clear
"continue/resume", resolve and pick up — no greeting.

Resolve existing engagements first (folders with a `.conductor.md` whose work is
incomplete — the same resolution the drive loop's step 0 performs), then offer:

| Engagements found | Offer |
|---|---|
| None | **Start an assessment** · **Run the sample** |
| One | **Continue "&lt;name&gt;"** (lead) · **Start an assessment** · **Run the sample** |
| More than one | list them, then **Continue one (which?)** · **Start an assessment** · **Run the sample** |

Continue appears only when there is something to continue.

The greeting is warm and capability-framed — no step/phase names, no commands:

<!-- greeting:start -->
> Hi — I'm your AI assessment guide. I turn plain-language goals into **audited numbers**
> on where AI and automation can save your team time and money. You don't need to know any
> steps or commands — just talk to me.
>
> Want to:
> - **Start an assessment** — tell me the team, process, or goal you want to look at.
> - **See it work first** — I'll run a complete sample on a realistic (fictional)
>   company, end to end.

When resumable engagements exist, prepend a leading bullet (and, if more than one, offer a
short list to choose from):

> - **Continue "&lt;name&gt;"** — pick up where we left off.
<!-- greeting:end -->

Route the user's choice:

- **Start an assessment** → continue into **Intake** below (register inference, then Phase
  1). If their choice already names a target, go straight in without re-asking.
- **Run the sample** ("See it work first") → chain to
  `ai-process-assessment:running-sample-engagement`, which owns the bundled-vs-generated
  scenario chooser. Do not duplicate that logic here.
- **Continue "&lt;name&gt;"** → enter the drive loop at step 0 with that engagement
  resolved (list and let the user pick if more than one).
````

- [ ] **Step 4: Run the conductor guards to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_onboarding.py -v`
Expected: PASS (both). If `test_greeting_is_jargon_free` fails, a blocklisted token leaked inside the delimiters — move it into the routing prose below `<!-- greeting:end -->`.

- [ ] **Step 5: Tweak the hook closing line (both scripts, identical wording)**

The current closing line (in both files) is:

```
If you're resuming an assessment I'll pick up where we left off; if you're starting fresh,
just tell me what you'd like to assess — you don't need to know any commands or phase names.
```

Replace it in BOTH `hooks/session-start.sh` (inside the `cat <<EOF` heredoc) and
`hooks/session-start.ps1` (inside the `@" ... "@` here-string) with:

```
If you're resuming an assessment I'll pick up where we left off; if you're starting fresh
I'll greet you with your options — start a new one, continue an existing one, or run a
sample. You don't need to know any commands or phase names.
```

This preserves the existing `resuming` and `you don't need to know any commands or phase names`
phrases (so the current hook assertions still hold) and adds the three-path offer. Change
nothing else in the hooks.

- [ ] **Step 6: Add the hook assertions (offer + `.ps1` sync)**

In `tests/test_session_start_hook.py`, add these two tests (leave the existing tests
unchanged — they still pass):

```python
def test_note_offers_the_three_first_contact_paths():
    out = _run({}).stdout.lower()
    assert "continue an existing one" in out
    assert "run a sample" in out


def test_ps1_twin_carries_the_same_offer():
    # The .sh hook is exercised by subprocess above; the .ps1 twin can't run on the CI
    # linux runner, so guard its content statically to keep the two in sync.
    ps1 = (REPO / "hooks" / "session-start.ps1").read_text(encoding="utf-8").lower()
    assert "continue an existing one" in ps1
    assert "run a sample" in ps1
    assert "you don't need to know any commands or phase names" in ps1
```

- [ ] **Step 7: Run the hook tests**

Run: `.venv/bin/python -m pytest tests/test_session_start_hook.py -v`
Expected: PASS — the original five tests plus the two new ones.

- [ ] **Step 8: Add the CHANGELOG entry (no version bump)**

Under `## [Unreleased]` → `### Added` in `CHANGELOG.md`:

```markdown
- **Conversational onboarding.** On a fresh session the assistant now greets you and offers to start a new assessment, continue an existing one, or run the bundled sample — no commands or methodology vocabulary required. The session-start front door names the same three paths. (`conducting-engagement` first-contact flow.)
```

- [ ] **Step 9: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — all prior tests plus the new onboarding + hook tests. Confirm the
verbatim-sync guard (`using-methodology` ↔ `system-prompt.md`) and skill-count guards are
still green (this task touched neither the keystone nor the skill registry).

- [ ] **Step 10: Commit**

```bash
git add skills/conducting-engagement/SKILL.md hooks/session-start.sh hooks/session-start.ps1 \
        tests/test_onboarding.py tests/test_session_start_hook.py CHANGELOG.md
git commit -m "feat(onboarding): conversational first-contact greeting + hook offer"
```

---

## Self-Review notes (for the implementer/reviewer)

- **Spec coverage:** §2 decision tree → Step 3 table; §3 greeting + delimiter → Step 3 greeting block; §4 routing + hook line → Step 3 routing + Step 5; §5 tests → Steps 1/6; §6 single task + CHANGELOG → this task + Step 8; §7 no-GUI / no-engine-change → Global Constraints.
- **Jargon guard scoping:** the routing bullets intentionally contain `Phase 1` and `ai-process-assessment:running-sample-engagement` — these live BELOW `<!-- greeting:end -->`, so `test_greeting_is_jargon_free` (which slices only the greeting block) does not see them, while `test_conductor_has_first_contact_offer` (which greps the whole body) requires the skill-id. Both hold by construction.
- **Hook back-compat:** the existing `test_note_has_resume_agnostic_front_door_line` keeps passing because the new line still contains `resuming` and `you don't need to know any commands or phase names`.
- **Keystone untouched:** `conducting-engagement` is NOT under the verbatim-sync guard (only `using-methodology` ↔ `system-prompt.md` are); this edit is safe.
```
