# Improvement Log

Prepend-only. New entries go at the top. Existing entries are never edited.

Each entry records one rationalization escape: a shortcut the methodology did not prevent, which triggered the RED step of the RED-GREEN-REFACTOR loop. The entry is written before the rationalization table row is added, so the escape and the fix are permanently linked.

## Entry Format

Add entries under `## Entries` below, newest first.

---

### [YYYY-MM-DD] Phase N — skill-name

**Engagement/Round:** <engagement name and round, or "n/a">
**Shortcut taken:** <what the agent or practitioner did instead>
**What it produced:** <observable outputs, artifacts, or negative consequences of the shortcut>
**Why the table didn't catch it:** <which rationalization row(s) should have prevented this, and why they didn't — or note that no row existed>
**New row added to:** <list all SKILL.md files modified, with repo-relative paths>

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| <shortcut text verbatim> | <correct reframe text verbatim> |

**Keystone updated:** yes / no / pending
**Checklist/gate step updated:** yes / no / pending — <which gate or checklist step, if yes; "pending" for an auto-flagged RED entry awaiting GREEN/REFACTOR>

---

## Entries

<!-- The entry below is illustrative. The rationalization row it references was not
     added to discovering-processes/SKILL.md — it exists only to demonstrate the format. -->

### 2026-06-08 — Phase 4 — discovering-processes (example entry)

**Engagement/Round:** Lattice Consulting sample / Round 2 (operator)
**Shortcut taken:** After mapping a high-volume process the agent immediately proposed "automate the slow steps" without first asking the three structural challenge questions. The sponsor round had been skipped.
**What it produced:** Three automation opportunities typed and logged before baselines existed; downstream scores had no grounded cycle-time input and produced fabricated figures.
**Why the table didn't catch it:** The master rationalization table carried the "Map it, find the slow steps, automate them" row, but the agent interpreted the row as applying only when all four rounds were explicitly skipped. Partial skip (Round 1 only) was not caught.
**New row added to:** `skills/discovering-processes/SKILL.md`

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Round 1 (sponsor) isn't needed if I have operator notes." | The structural challenge questions are asked of the sponsor, not the operator — the operator will defend the current structure. A partial skip of Round 1 is the same defect as a full skip: no challenge hypothesis, process does not advance to Phase 5. |

**Keystone updated:** no — the existing "Map it, find the slow steps, automate them" row remains; the new row belongs in the discovering-processes skill where the four-round sequence is defined.
**Checklist/gate step updated:** no
