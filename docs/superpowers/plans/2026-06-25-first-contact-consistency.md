# First-Contact Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Conductor's first contact behave the same way no matter how the user opens — always reflect intent back and confirm, then offer the paths — using this codebase's conversational-prose idiom, not an invented UI mechanism.

**Architecture:** First contact is plain conversational text governed by `skills/conducting-engagement/SKILL.md`. Consistency is enforced the way the rest of the product enforces it: a canonical user-facing line lives in a `<!-- …narration -->` block, and a guard asserts that block exists and stays jargon-free (mirroring `test_fanout_narration_is_jargon_free`). There is **no GUI/menu/button mechanism** — each surface (Claude Code, Cowork, Claude.ai) renders the conversation its own way (AC-4). The bug was a fuzzy classification branch ("clear request → skip the greeting and start") that sometimes skipped the offer entirely; removing it is the actual fix.

**Tech Stack:** Markdown skill files; Python `pytest` guards (stdlib only).

## Global Constraints

- **Conversational prose only — no widgets.** Do not introduce "buttons", "selectable options UI", or any platform-specific choice mechanism. Source: [conversational-onboarding-design.md](../specs/2026-06-21-conversational-onboarding-design.md) — *"prose only … No GUI/menu rendering — the offer is conversational text."*
- **Cross-surface (AC-4).** Behavior must hold in Claude Code, Cowork, and Claude.ai; nothing may depend on a surface-specific tool. Source: [public-ai-first-distribution-design.md](../specs/2026-06-19-public-ai-first-distribution-design.md).
- **Jargon-free user-facing text.** No phase names, file names, skill ids, or methodology vocabulary in any user-facing narration block. Enforced by guards.
- **Preserve existing contracts:** the `<!-- greeting:start -->…<!-- greeting:end -->` block, the three path labels (`Start an assessment`, `Continue`, `Run the sample`), and the two `or a `.sample-run.md`` resume occurrences must remain (guarded by `test_onboarding.py` and `test_guards.py::test_conductor_resume_detects_sample_marker`).
- **Honest language.** Describe the outcome as "consistent", not "deterministic" — the runtime is an LLM following prose; consistency is what guards can actually defend.
- **Process:** work continues on the existing issue #125 / branch `worktree-fix+125-first-contact-consistency` / PR #126. RED-first. Full `pytest -q` green before pushing.

---

### Task 1: Replace the foreign first-contact guards with idiomatic ones (RED)

The current branch added two guards in the wrong idiom/home: `test_first_contact_reflect_confirm_then_selectable` (asserts the foreign string `"selectable options"`) and `test_first_contact_legacy_skip_bypass_removed`, plus a `_first_contact_section` helper — all in `tests/test_guards.py`. Remove them and express the intent the codebase's way: a jargon-free `reflect-confirm` narration block (in `test_onboarding.py`, beside the greeting guard) and the legacy-bypass-removed check (also in `test_onboarding.py`, the first-contact home).

**Files:**
- Modify: `tests/test_guards.py` (delete the three additions from this branch)
- Modify: `tests/test_onboarding.py` (add two guards)

**Interfaces:**
- Consumes: `conducting-engagement/SKILL.md` body via the existing `methodology` fixture (test_guards) and `_body()` helper (test_onboarding).
- Produces: guards `test_first_contact_always_reflects_and_confirms`, `test_reflect_confirm_narration_is_jargon_free` in `test_onboarding.py`.

- [ ] **Step 1: Remove this branch's `test_guards.py` additions**

Delete exactly this block (added earlier on this branch) from `tests/test_guards.py`:

```python
# --- #first-contact-consistency guard (defends: non-deterministic first contact, #125) ---
# Same opener must produce the same shape every run: (1) always reflect intent back and
# confirm, then (2) present the next step as selectable options. A request "skips" nothing
# on phrasing alone — the only thing a named target changes is the confirmation sentence.
# The legacy "clear request -> skip the greeting and start" bypass is the source of the
# run-to-run variance and must be gone.

def _first_contact_section(body: str) -> str:
    i = body.find("## First contact")
    assert i != -1, "conducting-engagement has no '## First contact' section"
    j = body.find("\n## ", i + len("## First contact"))
    return body[i:] if j == -1 else body[i:j]


def test_first_contact_reflect_confirm_then_selectable(methodology):
    body = methodology.skills["ai-process-assessment:conducting-engagement"].body
    section = _first_contact_section(body)
    # Beat 1: always reflect the user's intent back and confirm before advancing.
    assert "Reflect their intent back and confirm" in section, (
        "first contact must always reflect intent back and confirm (beat 1)"
    )
    # Beat 2: the next step is presented as selectable options (deterministic buttons),
    # not freeform prose the user answers by typing.
    assert "selectable options" in section, (
        "first contact must present the next step as selectable options (beat 2)"
    )
    # A request only differs by whether it 'names a target' — never by skipping the beats.
    assert "names a target" in section, (
        "first contact must gate target-handling on whether the request names a target"
    )


def test_first_contact_legacy_skip_bypass_removed(methodology):
    body = methodology.skills["ai-process-assessment:conducting-engagement"].body
    assert "skip the greeting and start" not in body, (
        "the legacy 'skip the greeting and start' bypass causes non-deterministic first "
        "contact (#125) and must be removed"
    )
```

- [ ] **Step 2: Add idiomatic guards to `tests/test_onboarding.py`**

Append (the `_body()` helper and `REPO`/`CONDUCTOR` constants already exist in this file):

```python
def test_first_contact_always_reflects_and_confirms():
    """First contact must ALWAYS reflect the user's intent back and confirm before
    advancing — and the legacy 'clear request -> skip the greeting and start' bypass that
    let a target-less opener skip straight in (the #125 non-determinism) must be gone."""
    body = _body()
    assert "skip the greeting and start" not in body, \
        "legacy skip-the-greeting bypass must be removed (caused inconsistent first contact, #125)"
    assert "reflect their intent back and confirm" in body.lower(), \
        "first contact must instruct the Conductor to reflect intent back and confirm every time"


def test_reflect_confirm_narration_is_jargon_free():
    """The canonical reflect-and-confirm line is the user-facing text; like every other
    narration block it must be fenced and free of methodology jargon."""
    body = _body()
    start = body.find("<!-- reflect-confirm:start -->")
    end = body.find("<!-- reflect-confirm:end -->")
    assert start != -1 and end != -1 and end > start, \
        "reflect-confirm narration must be wrapped in <!-- reflect-confirm:start --> ... :end -->"
    narration = body[start:end]
    for token in GREETING_BLOCKLIST:
        assert token not in narration, f"reflect-confirm narration leaks jargon: {token!r}"
```

- [ ] **Step 3: Run the guards to verify they FAIL (RED)**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest tests/test_onboarding.py -q`
Expected: FAIL — `test_reflect_confirm_narration_is_jargon_free` fails (no `reflect-confirm` block yet) and `test_first_contact_always_reflects_and_confirms` fails on the lowercase-marker assertion (current text says "Reflect their intent back and confirm" — the `.lower()` check passes — but the `"skip the greeting and start"` assertion already passes since this branch removed it; if both pass, the RED comes only from the missing narration block, which is sufficient). Confirm at least the narration-block guard fails.

- [ ] **Step 4: Commit**

```bash
git add tests/test_guards.py tests/test_onboarding.py
git commit -m "test(conductor): idiomatic first-contact guards (reflect-confirm narration), drop widget guard (#125)"
```

---

### Task 2: Rewrite First contact in the conversational-prose idiom (GREEN)

Remove every "buttons / selectable-options UI / deterministic" phrase from the First contact section, keep the root-cause fix (always reflect-confirm + always offer the paths, no skip branch), add a `reflect-confirm` narration block, and restore the original `Offer` table header.

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (the `## First contact` section)

**Interfaces:**
- Consumes: nothing new.
- Produces: a `<!-- reflect-confirm:start -->…<!-- reflect-confirm:end -->` block; the literal text "reflect their intent back and confirm"; preserved `<!-- greeting -->` block, `Offer` table with the three path labels, and one `or a `.sample-run.md`` occurrence.

- [ ] **Step 1: Replace the First-contact body**

Replace the entire span from `Every first contact follows the **same two beats` … through the end of the `Route the user's selection:` list with:

```markdown
Every first contact follows the **same shape, no matter how the user opens** — a bare "hi",
"lets do an ai assessment", and "assess my billing team" all get the identical flow. That is
the AI-native promise: plain conversation, the same way every time, with the methodology
invisible. **No opener bypasses this** — there is no "clear enough to skip straight in" path,
because that is exactly what made the experience vary from one run to the next.

**First, reflect their intent back and confirm — in one line, before anything else.** Mirror
what they said and ask for a yes. Whether the request **names a target** (a team, process, or
goal) only changes what you reflect, never whether you reflect: if they named one, name it
back; if they did not, reflect the general intent. Canonical line for a target-less opener:

<!-- reflect-confirm:start -->
> Happy to help with that — I'm hearing you'd like to find where AI and automation could save
> your team time and money. Have I got that right?
<!-- reflect-confirm:end -->

When they name a target, fold it into the same sentence ("…assess how your sales team works and
where AI and automation could help — have I got that right?"). Infer **register** (consultant vs
operator) from how they phrased it and let it set your voice from here on; never run a cold
multiple-choice quiz. A "continue/resume" opener is reflected the same way ("Looks like you'd
like to pick up where we left off — yes?").

**Then, on their yes, offer the paths that fit what already exists** — in plain conversational
language. You write the words; each surface renders the conversation its own way (do not assume
or require buttons or a menu widget).

Resolve existing engagements first (folders with a `.conductor.md` whose work is incomplete,
**or a `.sample-run.md`** marker from a generated/bundled sample whose work is incomplete — a
freshly generated sample has only `.sample-run.md` until Phase 1 stamps `.conductor.md`, so a
resolution that keys on `.conductor.md` alone would miss it and report "nothing to resume" —
the same resolution the drive loop's step 0 performs), then offer:

| Engagements found | Offer |
|---|---|
| None | **Start an assessment** · **Run the sample** |
| One | **Continue "&lt;name&gt;"** (lead) · **Start an assessment** · **Run the sample** |
| More than one | list them, then **Continue one (which?)** · **Start an assessment** · **Run the sample** |

Continue appears only when there is something to continue. The offer is warm and
capability-framed — no step/phase names, no commands:

<!-- greeting:start -->
> I turn plain-language goals into **audited numbers** on where AI and automation can save
> your team time and money. You don't need to know any steps or commands — just pick one:
>
> - **Start an assessment** — the team, process, or goal you want to look at.
> - **See it work first** — I'll run a complete sample on a realistic (fictional) company,
>   end to end.

When resumable engagements exist, prepend a leading option (and, if more than one, list them
to choose from):

> - **Continue "&lt;name&gt;"** — pick up where we left off.
<!-- greeting:end -->

Route the user's choice:

- **Start an assessment** → continue into **Intake** below (register already inferred above,
  then Phase 1). If the reflect-and-confirm already captured a target, carry it in — do not re-ask.
- **Run the sample** ("See it work first") → chain to
  `ai-process-assessment:running-sample-engagement`, which owns the bundled-vs-generated
  scenario chooser. Do not duplicate that logic here.
- **Continue "&lt;name&gt;"** → enter the drive loop at step 0 with that engagement resolved
  (list and let the user pick if more than one).
```

- [ ] **Step 2: Verify no widget/overclaim language remains in the section**

Run: `grep -niE "selectable options|deterministic|platform's .*UI" skills/conducting-engagement/SKILL.md`
Expected: no matches inside `## First contact`. (Note: the word "buttons" intentionally remains in ONE place — the negation "do not assume or require buttons or a menu widget" — so it is deliberately excluded from this gate; do not grep for `button`. A "deterministic" reference elsewhere in engine/state prose, if any, is unrelated — confirm any hit is outside `## First contact`.)

- [ ] **Step 3: Run the onboarding guards to verify they PASS (GREEN)**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest tests/test_onboarding.py -q`
Expected: PASS (reflect-confirm block present + jargon-free; greeting + path labels intact; bypass gone).

- [ ] **Step 4: Run the full suite**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest -q`
Expected: PASS, all tests (including `test_conductor_resume_detects_sample_marker`, which needs two `or a `.sample-run.md`` occurrences — one here, one in drive-loop step 0).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md
git commit -m "fix(conductor): first contact is consistent via reflect-confirm + conversational offer (#125)"
```

---

### Task 3: Correct the CHANGELOG wording and finalize the PR

**Files:**
- Modify: `CHANGELOG.md` (the `[Unreleased]` entry added on this branch)

**Interfaces:** none.

- [ ] **Step 1a: Restore the dropped `## [2.22.1]` header (pre-existing regression)**

The `[Unreleased]` section currently has TWO `### Fixed` blocks and no `## [2.22.1]` header — an earlier hand-edit dropped it, so the #122 sample entry sits under `[Unreleased]` and `test_changelog_has_section_for_current_version` fails (plugin.json is 2.22.1 with no matching CHANGELOG section). Restore the header by prefixing the SECOND `### Fixed` block (the sample one, identified by its unique #122 bullet) with the version header. Edit:

old:
```markdown
### Fixed
- **Sample run is now Conductor-driven end to end** (#122). Resolves two defects hit when
```
new:
```markdown
## [2.22.1] - 2026-06-25

### Fixed
- **Sample run is now Conductor-driven end to end** (#122). Resolves two defects hit when
```

This leaves `[Unreleased]` holding only the first-contact (#125) entry and `[2.22.1]` holding the #122 entry — restoring the structure released in PR #124.

- [ ] **Step 1b: Replace "deterministic" with honest "consistent" framing**

In `CHANGELOG.md` under `[Unreleased] → ### Fixed` (the first-contact #125 bullet), replace the existing bullet with:

```markdown
- **First contact is now consistent across runs and openers** (#125). The same opener used to
  behave differently from one run to the next, because a fuzzy "clear request → skip the
  greeting and start" branch sometimes skipped the path offer entirely. First contact now
  follows the same conversational shape every time, regardless of phrasing: always reflect the
  user's intent back and confirm in one line — a named target only fills in what gets reflected
  — then offer the paths. The canonical reflect-and-confirm line lives in a jargon-free
  narration block (same convention as the greeting), with guards in `tests/test_onboarding.py`.
  Stays conversational prose only — no UI/widget mechanism — so it holds across Claude Code,
  Cowork, and Claude.ai.
```

- [ ] **Step 2: Run the full suite one final time**

Run: `~/Developer/ai-process-assessment/.venv/bin/python -m pytest -q`
Expected: PASS (full suite).

- [ ] **Step 3: Commit and push to the existing PR branch**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): honest 'consistent' framing for first-contact fix (#125)"
git push origin worktree-fix+125-first-contact-consistency
```

- [ ] **Step 4: Update the PR body** to drop the "deterministic"/buttons framing and describe the conversational-prose + narration-block approach, then leave PR #126 for review (do not merge without explicit approval).

---

## Self-Review

**Spec coverage:**
- "Same behavior regardless of opener" → Task 2 removes the skip branch; always reflect-confirm + offer. ✓
- "Reflect intent back and confirm" (user's explicit request) → Task 2 reflect-confirm block + prose. ✓
- "AI-native idiom, no widgets" → Global Constraints + Task 2 Step 2 grep gate. ✓
- "Consistency enforced the codebase way" → Task 1 narration-block + jargon guards mirroring `test_fanout_narration_is_jargon_free`. ✓
- "Preserve existing contracts" → greeting block, three labels, `.sample-run.md` ×2 retained and re-verified in Task 2 Steps 3–4. ✓
- "Honest language" → Task 3 changelog. ✓

**Placeholder scan:** none — all steps carry exact text, commands, and expected output.

**Type/string consistency:** guard strings match the skill text exactly — `reflect-confirm:start`/`:end` (block), `"reflect their intent back and confirm"` (lowercased marker), `"skip the greeting and start"` (absence). `GREETING_BLOCKLIST` reused from `test_onboarding.py`. Table header restored to `Offer`; labels `Start an assessment` / `Continue` / `Run the sample` preserved for `test_onboarding.py::test_conductor_has_first_contact_offer`.
