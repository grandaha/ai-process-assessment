# Slice 2 · Chunk C — Adaptive interaction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the conductor adapt to the human — plain-language per-class autonomy, should-confirm batching, register-driven teaching, and holding-the-line under pressure — within an unbreakable must-ask floor.

**Architecture:** Entirely conductor prose in `skills/conducting-engagement/SKILL.md` (one new `## Adaptive autonomy & holding the line` section, plus edits to Intake, the Execution model, and the Touchpoint taxonomy), guarded by static string-presence tests (repo convention). **Zero new Python** — the per-class `autonomy` map is a schema convention persisted via the existing `write_conductor`.

**Tech Stack:** Markdown skill prose; pytest static-guard tests.

## Global Constraints

- **Zero new code.** No `state/`/`engine/` changes. The `autonomy` map is written via the existing `write_conductor(root, data)`; `state.py` does not consume `autonomy`.
- **must-ask floor is verbatim** the existing must-ask taxonomy set: scope boundaries, out-of-scope process additions, cost actuals, checkpoint outcomes, gate dispositions, Build/Buy/Partner. Do not invent or remove must-ask items.
- **Autonomy never relaxes a must-ask** — a per-class setting can only tighten a should-confirm to `ask` or relax a should-confirm to `auto`.
- **Holding-the-line is firm-and-teaching, never refuse-and-quote** — never cite phase names/rules/methodology at the human; give the human reason + fastest honest path.
- **Register sets voice, autonomy sets cadence, the must-ask floor is the same for both.**
- **Off-limits (verbatim-sync):** do NOT edit `skills/using-methodology/SKILL.md` or any `system-prompt.md`. Golden `results.json` untouched.
- **CHANGELOG:** add one bullet under `## [Unreleased]`; **no version bump in this PR** (the post-merge `v2.19.0` release closes #87).
- **Test command:** `.venv/bin/python -m pytest` (Python 3.13 venv; system 3.14 lacks pytest). **Baseline on this branch: 282 passed.** Final target: **287 passed** (282 + 5 guards).
- **Branch:** `feat/slice2-chunkC-adaptive-interaction` (already created off `main` @ 29302a2).
- **Commits:** end every commit message with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

## File Structure

- `skills/conducting-engagement/SKILL.md` — **modify**: new `## Adaptive autonomy & holding the line` section (after `## Touchpoint taxonomy`, before `## Elastic processes & convergence`); update the Touchpoint-taxonomy should-confirm row; add a register-voice note to the Execution-model section; small Intake note that pace can be re-expressed any time.
- `tests/test_conductor_skill.py` — **modify**: add `## Adaptive autonomy & holding the line` to `REQUIRED_HEADINGS`; add 5 guards (reuse the existing `_section` helper from Chunk A).
- `CHANGELOG.md` — **modify**: one bullet under `## [Unreleased]`.

All five guards reuse the `_section(text, header)` helper already present in `tests/test_conductor_skill.py`. Do not redefine it.

---

## Task 1: Adaptive autonomy section (per-class interpretation + persistence)

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (new section after `## Touchpoint taxonomy`; small Intake note)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the existing `_section(text, header)` helper.
- Produces: the `## Adaptive autonomy & holding the line` section that Tasks 2 and 3 extend.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, add `"## Adaptive autonomy & holding the line"` to the `REQUIRED_HEADINGS` list, then append:

```python
def test_conductor_adaptive_autonomy():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    # Plain-language interface, any time.
    assert "plain language" in sec
    # Interpreted into per-class behavior and persisted (conductor-maintained).
    assert "per-class" in sec
    assert "per_class" in sec
    assert "write_conductor" in sec
    assert "never sees or edits" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — `test_skill_has_all_load_bearing_sections` (new heading missing) and `test_conductor_adaptive_autonomy` (section absent).

- [ ] **Step 3: Add the section**

In `skills/conducting-engagement/SKILL.md`, add this section immediately **after** the `## Touchpoint taxonomy` section (i.e. after its table) and **before** `## Elastic processes & convergence`:

```markdown
## Adaptive autonomy & holding the line

You adapt your interaction to the human within invariants that never move. The human never
configures anything — they express pace and trust in **plain language, at any point** ("stop asking
me about the small stuff", "slow down and walk me through these", "check anything cost-related with
me"), and you adapt.

**Adaptive autonomy.** Interpret each pace/trust statement into **per-class** behavior and persist
it in `.conductor.md` under `autonomy` (written via `write_conductor`; the human never sees or edits
it):

    autonomy: {
      should_confirm: "guided" | "batched" | "auto",
      per_class: { "<class or item>": "ask" | "auto" }
    }

`should_confirm` is the default cadence for should-confirm items; `per_class` records only what the
human has actually expressed (e.g. `"costs": "ask"`, `"scoring rationale": "auto"`); anything
unstated follows `should_confirm`. Re-interpret and re-persist whenever the human restates pace —
intake is just the first such moment, not the only one.
```

- [ ] **Step 4: Add the Intake note**

In `skills/conducting-engagement/SKILL.md`, in the Intake section's autonomy step (the one beginning "**Set autonomy preset**"), append this sentence to that step:

```markdown
   Pace and trust can be re-expressed at any point, not only here — see *Adaptive autonomy & holding the line*.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): adaptive per-class autonomy from plain language

Human expresses pace/trust in plain language any time; conductor interprets to
per-class behavior persisted in .conductor.md autonomy (via write_conductor),
never user-edited. Part of #87 (Slice 2 Chunk C).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: should-confirm batching + taxonomy update

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (extend the new section; edit the Touchpoint-taxonomy should-confirm row)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Adaptive autonomy & holding the line` section and `_section` helper.

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_should_confirm_batching():
    text = SKILL.read_text()
    sec = _section(text, "## Adaptive autonomy & holding the line")
    assert "reviewable digest" in sec
    assert "silently skipped" in sec
    # The taxonomy placeholder is replaced by the implemented behavior.
    assert "Autonomous batching is Slice 2" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_should_confirm_batching -v`
Expected: FAIL (`assert "reviewable digest" in sec`).

- [ ] **Step 3: Extend the section**

In `skills/conducting-engagement/SKILL.md`, inside `## Adaptive autonomy & holding the line`, add this block immediately **after** the `autonomy: { ... }` block and its following paragraph (i.e. after "intake is just the first such moment, not the only one."):

```markdown
**should-confirm batching.** When the human wants speed (`should_confirm` is `batched` or `auto`, or
a class is `auto`), do not pause on each should-confirm item. Accumulate them and surface one
**reviewable digest** at a natural boundary (before a gate, or at phase-group completion), each item
labeled so the human can correct any single one. Nothing is silently skipped — the digest is the
audit trail — and nothing pauses them mid-flow.
```

- [ ] **Step 4: Update the Touchpoint-taxonomy should-confirm row**

In `skills/conducting-engagement/SKILL.md`, in the `## Touchpoint taxonomy` table, replace the should-confirm row's Behavior cell. Change:

```markdown
| Should-confirm | Guided: pause to approve. (Autonomous batching is Slice 2.) | Context map, opportunity log, scoring rationale, roadmap sequencing; once `results.json` exists, generating any requested artifact via `ai-process-assessment:generate-artifact` (produced from the verified contract, never by hand) |
```

to:

```markdown
| Should-confirm | Guided: pause to approve. Batched/auto: accumulate into one reviewable digest at a natural boundary (each item correctable; nothing silently skipped) — see *Adaptive autonomy & holding the line*. | Context map, opportunity log, scoring rationale, roadmap sequencing; once `results.json` exists, generating any requested artifact via `ai-process-assessment:generate-artifact` (produced from the verified contract, never by hand) |
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_should_confirm_batching -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): should-confirm batching into a reviewable digest

When the human wants speed, accumulate should-confirm items into one labeled,
correctable digest at a natural boundary (nothing silently skipped); replaces
the taxonomy's 'Autonomous batching is Slice 2' placeholder. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: must-ask invariant + holding-the-line

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (extend the new section)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `## Adaptive autonomy & holding the line` section and `_section` helper.

- [ ] **Step 1: Write the failing tests**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_must_ask_invariant():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    assert "must-ask never collapses" in sec
    assert "any pressure" in sec
    assert "never** relax a must-ask" in sec or "never relax a must-ask" in sec


def test_conductor_holding_the_line():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    assert "firm and teaching" in sec
    assert "never refuse-and-quote" in sec
    assert "shortest honest path" in sec
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_must_ask_invariant tests/test_conductor_skill.py::test_conductor_holding_the_line -v`
Expected: FAIL (the invariant/holding-the-line prose is absent).

- [ ] **Step 3: Extend the section**

In `skills/conducting-engagement/SKILL.md`, at the **end** of the `## Adaptive autonomy & holding the line` section (after the should-confirm batching block), add:

```markdown
**The line that never moves.** must-ask never collapses — in any mode, under any pressure, whatever
autonomy the human has set: scope boundaries, out-of-scope process additions, cost actuals,
checkpoint outcomes, gate dispositions, Build/Buy/Partner. A per-class setting can tighten a
should-confirm item to `ask` or relax a should-confirm item to `auto`; it can **never** relax a
must-ask. "Just do everything, don't ask me" speeds up should-confirm and can-infer and never
touches the floor.

**Holding the line.** When the human pushes to skip a must-ask ("just give me the number, skip
this"), honor the **spirit** — move faster everywhere else, batch the rest — while holding the
**floor**. Give the human reason the gate exists and the fastest honest path through it ("this one
number is what makes the $1.3M defensible — 30 seconds and it's yours"). Be **firm and teaching,
never refuse-and-quote**: do not cite phase names, rules, or the methodology at the human. Holding
the line is the shortest honest path, never a wall.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: PASS (all conductor guards green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): must-ask floor invariant + holding-the-line posture

must-ask never collapses under any pressure; autonomy can never relax it. Under
pressure to skip, hold the floor firm-and-teaching (human reason + fastest
honest path), never refuse-and-quote. Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Register-driven teaching in the execution model

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (add a register-voice note to the Execution-model section)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: nothing from other tasks (independent prose addition).

- [ ] **Step 1: Write the failing test**

In `tests/test_conductor_skill.py`, append:

```python
def test_conductor_register_drives_teaching():
    text = SKILL.read_text()
    assert "Register voice" in text
    assert "teach as you go" in text
    assert "terse and domain-fluent" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_register_drives_teaching -v`
Expected: FAIL (`assert "Register voice" in text`).

- [ ] **Step 3: Add the register-voice note**

In `skills/conducting-engagement/SKILL.md`, at the **end** of the `## Execution model — who talks to the human (§4.4)` section (after its last bullet, the "Input contract" bullet), add:

```markdown
- **Register voice (teaching).** The `register` stamped at intake drives *how* you explain
  throughout the drive loop, not just at intake. **operator** (own team, no methodology training) →
  teach as you go: plain-language "here's why this matters / what this means", explain before you
  ask. **consultant** (domain-fluent, relaying interviews) → terse and domain-fluent: assume the
  vocabulary, no hand-holding. Register sets the voice; autonomy sets the cadence; the must-ask
  floor is the same for both.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_conductor_register_drives_teaching -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): register drives the teaching voice downstream

operator -> teach-as-you-go plain language; consultant -> terse domain-fluent.
Register sets voice, autonomy sets cadence, must-ask floor same for both.
Part of #87.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: CHANGELOG + full-suite verification

**Files:**
- Modify: `CHANGELOG.md` (under `## [Unreleased]`)

**Interfaces:**
- Consumes: all prior tasks.

- [ ] **Step 1: Add the CHANGELOG entry**

In `CHANGELOG.md`, under `## [Unreleased]` (in the existing `### Added` subsection if one is present from Chunks A/B — add the bullet there rather than a second `### Added`):

```markdown
- **Adaptive interaction (Slice 2 Chunk C, #87).** The conductor adapts to the human: pace and trust
  expressed in plain language at any point become per-class autonomy; should-confirm items batch into
  one reviewable digest when speed is wanted; the register (operator vs consultant) drives the
  teaching voice; and the must-ask floor never collapses — under pressure the conductor holds the
  line firm-and-teaching (human reason + fastest honest path), never refuse-and-quote. The engine of
  AC-1. No new code.
```

- [ ] **Step 2: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — **287 passed** (282 baseline + 5 new guards).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): Slice 2 Chunk C — adaptive interaction (#87)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Push**

```bash
git push
```

Markdown-only change → the auto-review gate will likely **HOLD** it (as for Chunk A) → hand-merge with a decision comment. After merge, cut `v2.19.0` (separate step) to close #87.

---

## Self-Review

**1. Spec coverage** (against `2026-06-24-slice2-chunkC-adaptive-interaction-design.md`):
- §3.1 adaptive autonomy + persistence → Task 1; should-confirm batching → Task 2. §3.2 must-ask invariant → Task 3. §3.3 holding-the-line → Task 3. §3.4 register-driven teaching → Task 4. §4 files → all covered (Intake note Task 1; new section Tasks 1–3; taxonomy Task 2; execution model Task 4; CHANGELOG Task 5). §6 guards 1–5 → Tasks 1/2/3(×2)/4. §7 release → noted in Task 5 (post-merge, not in PR).
- **Zero-new-code constraint:** honored — no task creates or edits any `state/`/`engine/` file.

**2. Placeholder scan:** none — every step has exact prose, test code, and commands with expected output.

**3. Type/token consistency:** guard tokens match the prose verbatim — Task 1: `plain language`, `per-class`, `per_class`, `write_conductor`, `never sees or edits`. Task 2: `reviewable digest`, `silently skipped`, and `"Autonomous batching is Slice 2" not in text` (defended by the Step-4 taxonomy edit). Task 3: `must-ask never collapses`, `any pressure`, `never** relax a must-ask` (the prose uses `**never** relax a must-ask`; the test accepts either bolded or plain), `firm and teaching`, `never refuse-and-quote`, `shortest honest path`. Task 4: `Register voice`, `teach as you go`, `terse and domain-fluent`. All five guards reuse `_section`/`SKILL.read_text()`; none redefines `_section`.
