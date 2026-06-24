# Slice 3 · Chunk C — Improvement-flywheel auto-flagging

**Part of:** Epic #85 → Slice 3 (#88), spec §3.E. **Date:** 2026-06-24.
**Closes Slice 3** (after Chunks A #107, B #109).

## 1. Problem

The methodology already has a RED-GREEN-REFACTOR improvement loop
([`skills/using-methodology/SKILL.md`](../../../skills/using-methodology/SKILL.md) "Improvement
Log"): when someone notices a *rationalization escape* — a shortcut the methodology didn't
prevent (skip a step, compute a number inline, reuse prior answers) — they prepend a RED
entry to `improvement-log.md`, then add a rationalization-table row (GREEN) and tighten the
gate (REFACTOR). Today this fires only **when a human happens to notice**. The Conductor,
which is the one actually tempted by these shortcuts mid-drive, never self-reports.

The spec wants the Conductor to **auto-flag the escapes it encounters** into
`improvement-log.md` (the RED step), with a human still approving GREEN/REFACTOR.

## 2. Goal

When the Conductor catches itself reaching for one of the master-table rationalizations, it
**refuses the shortcut, auto-writes a structured RED entry, and surfaces it** — turning the
"holding the line" moment (Slice 2 Chunk C) into durable methodology signal. A small tested
helper enforces the append-only / Entry-Format invariant so the auto-write can never corrupt
the log. GREEN (table row) and REFACTOR (gate tightening) remain **human-approved**.

Non-goals: no auto-GREEN/REFACTOR (those edit skills/keystone — human only); no LLM in the
helper; no change to the master rationalization table itself.

## 3. Design

### 3.1 Where the RED entry is written — engagement-local

The auto-flag writes to **`<engagement>/improvement-log.md`** (the engagement folder), not
the plugin root. Rationale:
- **Portability (AC-2):** a stranger's plugin install lives in a read-only cache; the
  engagement folder is always writable and user-owned.
- **Capture without a repo:** the signal lands next to the run that produced it. In the
  maintainer's own dogfooding the engagement folder *is* in this repo, so escapes are
  captured in-tree automatically.
- The repo-root `improvement-log.md` remains the **curated methodology record**; engagement
  logs are the **raw auto-captured RED feed** a maintainer promotes upstream during
  GREEN/REFACTOR. `using-methodology`'s human RED step (repo-root) is unchanged; this adds
  the Conductor's automatic engagement-local capture.

**Discovery is a manual maintainer step (v1).** There is no automatic aggregation across
engagements — promotion upstream is a periodic maintainer action, not triggered by the
auto-flag. The primary v1 driver is dogfooding (the engagement folder is in this repo, so
entries are captured in-tree). The narration (below) names that a note was written so at
least the human in the session knows it exists. Cross-engagement aggregation is a possible
later enhancement, explicitly out of scope here.

### 3.2 New unit — `state/improvement_log.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Escape:
    date: str            # ISO date, supplied by caller (no clock in the module)
    phase: str           # e.g. "5" or "n/a"
    skill: str           # skill dir name or "conductor"
    engagement: str      # engagement name/round, or "n/a"
    shortcut: str        # the rationalization the Conductor caught itself reaching for
    would_produce: str   # the consequence it avoided
    why_uncaught: str    # which table row should have caught it (or "no row existed")
    reframe: str         # canonical reframe (reused from the matched master-table row),
                         # or "pending" when why_uncaught == "no row existed" — see below

def render_entry(escape: Escape) -> str:
    """Render one RED entry in the canonical Entry Format (newest-first block)."""

def prepend_entry(log_path, escape: Escape) -> None:
    """Prepend a RED entry under the '## Entries' header of log_path.

    Non-destructive prepend: inserts the new block immediately after '## Entries';
    existing entries are never edited or reordered. If log_path is absent, scaffold
    it (title + prepend-only note + '## Entries'). If log_path EXISTS but has no
    '## Entries' header, raise ValueError (never guess an insert point). If multiple
    '## Entries' lines exist, insert after the first. Pure given (file contents,
    escape) — no clock, no network."""
```

- **No clock in the module.** `Escape.date` is passed in (the Conductor supplies the
  session date) — keeps the unit pure and testable, matching the repo's no-`Date.now()`
  discipline.
- `render_entry` produces exactly the Entry Format already documented in
  `improvement-log.md` (heading `### [date] Phase N — skill`, the bold fields, the
  `| Rationalization | Correct Reframe |` row, and `Keystone updated: pending` /
  `Checklist/gate step updated: pending` — pending because GREEN/REFACTOR await the human).
- **`reframe` is reuse, not generation.** When the caught shortcut matches an existing
  master-table row, `reframe` is that row's canonical text (copied, not invented). When
  `why_uncaught == "no row existed"`, `reframe` is `"pending"` — the human authors the
  canonical reframe at GREEN. This keeps the auto-RED entry a pure capture and never
  auto-writes proto-GREEN methodology content.
- **Invariant — non-destructive prepend (existing entries immutable):** the helper only ever
  inserts a new block and rewrites the scaffold; it never mutates, reorders, or drops a prior
  entry. (Distinct from the human RED step's "append" wording in `using-methodology`.)
- **`## Entries` contract** (the main correctness risk): absent file → scaffold; existing
  file with the header → insert after the first occurrence; existing file **without** the
  header → `ValueError` (the Conductor surfaces it rather than mis-writing). Tested.
- `Keystone updated` / `Checklist/gate step updated` render as `pending` (not yes/no) for an
  auto-RED entry — the human resolves them at GREEN/REFACTOR. This is a deliberate, narrow
  extension of the Entry Format's `yes / no`; the canonical Entry-Format docs in
  `improvement-log.md` are updated to recognize `pending` (see §4).
- **Concurrency (known v1 limitation):** the helper is a read-modify-write with no file lock;
  two parallel Conductor instances could race (TOCTOU). Acceptable for v1 single-agent drive;
  noted, not solved here.

### 3.3 Conductor wiring — "Improvement flywheel — auto-flagging escapes"

A new section in `skills/conducting-engagement/SKILL.md`:

- **Detect (with a false-positive guard).** While driving, watch your own reasoning for the
  master-table rationalizations (the table in `using-methodology` — skip-a-step,
  compute-inline, reuse-prior-answers, optimize-around-not-root, etc.). Flag **only** when
  you would actually have taken the shortcut **and** the methodology does not explicitly
  permit the action in this context (mirroring the nuance in *holding the line*). A permitted
  reuse is not an escape. The trigger is the same catch-moment as *holding the line* (see
  *Adaptive autonomy & holding the line*).
- **Refuse + capture.** Do not take the shortcut. Auto-write a RED entry via
  `state.improvement_log.prepend_entry(<engagement>/improvement-log.md, Escape(...))`, where
  `<engagement>` is the **active engagement folder resolved at drive-loop step 0** (absolute
  path — the same folder the drive loop operates on; never a guessed or relative path). Fill
  `reframe` from the matched master-table row, or `"pending"` if no row existed. This is the
  only auto-step.
- **Write-failure path.** If `prepend_entry` raises (e.g. `ValueError` for a pre-existing
  log without `## Entries`, or a path error), **do not** narrate that it was logged — tell
  the human plainly that you caught the shortcut but couldn't write the note, and why. Never
  claim a durable record that does not exist.
- **Surface for GREEN/REFACTOR (human-approved), as two distinct asks.** After a successful
  write, tell the human you caught and logged the shortcut, and ask — distinguishing the two
  — whether to (GREEN) add the rationalization row to the relevant skill, and/or (REFACTOR)
  tighten the gate/checklist step. These edits touch skills/keystone and are **never**
  automatic.
- **Jargon-free narration**, fenced for the guard:

```
<!-- flywheel-narration:start -->
> Heads-up: I nearly took a shortcut there — reusing last time's answers instead of
> re-deriving them for your situation. I didn't, and I've noted it so the method gets a
> little sharper. Want me to fold that lesson into how I work, add a guardrail so it can't
> slip again — either, both, or neither and just keep going?
<!-- flywheel-narration:end -->
```

This composes with Slice 2 Chunk C: *holding the line* is the refusal; the flywheel is the
durable record of it. The must-ask floor and autonomy presets are unchanged.

## 4. Files

- **Create** `state/improvement_log.py` — `Escape`, `render_entry`, `prepend_entry`.
- **Create** `state/tests/test_improvement_log.py` — render format, scaffold-on-absent,
  non-destructive prepend (existing entries preserved), `ValueError` on missing-header,
  `reframe="pending"` rendering, determinism.
- **Modify** `improvement-log.md` — extend the Entry-Format docs to recognize `pending` as a
  valid auto-RED value for `Keystone updated` / `Checklist/gate step updated`.
- **Modify** `skills/conducting-engagement/SKILL.md` — add the flywheel section + narration.
- **Modify** `tests/test_conductor_skill.py` — guards for the new section.

## 5. Testing strategy

- **`state/tests/test_improvement_log.py`**:
  - `render_entry` contains the date/phase/skill heading, every bold field, the reframe row,
    and `pending` for keystone/checklist.
  - `render_entry` with `why_uncaught == "no row existed"` renders `reframe` as `pending`
    (no Conductor-invented canonical text).
  - `prepend_entry` on an absent file scaffolds the title + `## Entries` + the entry.
  - `prepend_entry` twice → newest entry appears first; the older entry is preserved verbatim
    (non-destructive prepend).
  - a pre-existing hand-written entry below `## Entries` (with `yes`/`no` keystone fields) is
    preserved verbatim — not corrupted — when a new one is prepended.
  - `prepend_entry` on an existing file with **no** `## Entries` header raises `ValueError`.
  - determinism: same `Escape` + same file → same result.
- **`tests/test_conductor_skill.py`**: guard the flywheel section — present, references
  `state.improvement_log` / `prepend_entry`, states GREEN/REFACTOR stay human-approved,
  narration block fenced + jargon-free (forbidden-token sweep, matching the sibling guards).
- Full suite stays green.

## 6. Reconciliation

- **Extends, does not replace, the existing loop.** `using-methodology`'s human RED step
  (repo-root log) is unchanged; this adds the Conductor's automatic engagement-local
  capture. GREEN/REFACTOR remain human-approved in both.
- **Composes with Slice 2 Chunk C** (*holding the line*): same catch-moment, now with a
  durable record. The must-ask floor is untouched.
- **Pure helper**, stdlib-only, no clock (date passed in) — matches `state/*` conventions
  and the repo's determinism rule.
- **No auto-edit of skills/keystone** — those are the GREEN/REFACTOR human steps; the
  Conductor only writes the RED capture and surfaces the proposal.
