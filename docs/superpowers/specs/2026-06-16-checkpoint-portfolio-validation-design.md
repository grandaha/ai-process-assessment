# Checkpoint 3 — Portfolio & Roadmap Review — Design

**Date:** 2026-06-16
**Status:** Approved for planning
**Author:** Dave (with Claude)
**Issue:** grandaha/ai-process-assessment#49 (Checkpoint 3 of 3 — this cycle closes the issue)
**Builds on:** the checkpoint pattern shipped in v2.10.0 (`baseline`) and v2.11.0 (`scope`)

## Summary

Add **Checkpoint 3 — Portfolio & Roadmap Review**, an interim client-facing HTML
artifact rendered after Phase 7, so the decision-maker, sponsor, and IT lead
green-light the **shape of Wave 1** — the prioritized portfolio, wave sequencing,
quick wins, dependencies, and the investment envelope — *before* the engagement
spends effort packaging use cases (Phase 8), collecting cost actuals (Phase 8.5),
and assembling the business case (Phase 9).

This is the "recommendations readout" in the classic consulting cadence (charter →
current-state readout → recommendations readout → final). It is the third and
final checkpoint built on the established pattern (the `building-checkpoint` skill,
the scoped deliverable-gate Checkpoint Mode, the recorded feedback loop). **This
cycle closes issue #49.**

## Goals

- A consultant can produce a polished portfolio-and-roadmap review artifact from
  `scores/`, `opportunities/`, and `roadmap.md`, with no new analysis.
- The decision-maker/sponsor/IT lead can confirm or correct the prioritization and
  sequencing; the outcome is recorded and routes corrections back to the owning
  phase (scoring → Phase 6, sequencing → Phase 7).
- The artifact renders the **full analytical work product** — the ranked portfolio
  *and* the per-OPP six-dimension scoring detail with rationale — because at this
  checkpoint the audience is making the prioritization decision and is entitled to
  the basis for it.

## Non-Goals

- Not reusing the Phase 11 `section-renderer-portfolio` / `section-renderer-roadmap`
  agents. Those are tuned to the sample engagement (hardcoded "exactly 7 Wave-1
  cards", a specific budget envelope, named OPPs/enablers) and would misrender any
  other engagement. CP3 gets a **bespoke data-driven renderer** consistent with the
  `scope`/`baseline` checkpoint renderers (render what exists, PENDING the rest).
- Not changing the `building-checkpoint` skill's architecture, the outcome template,
  or the enforcement model (recommended-and-recorded) — reused as-is. This cycle
  adds a registry row, a renderer, and small gate/keystone extensions.
- Not auto-merge-eligible: markdown/methodology work → human-merged.

## Decisions (locked in brainstorming)

1. **Insert after Phase 7** (once `roadmap.md` exists), before Phase 8.
2. **Bespoke data-driven renderer** (`section-renderer-checkpoint-portfolio`), not
   the Phase 11 renderers.
3. **Show everything, including dimensional detail.** No hard leak-exclusions —
   `scores/` and `roadmap.md` are analytical work products the client is deciding
   on, not candid internal assessments like `context.md`'s political read. (Contrast
   with the `scope` checkpoint, which excludes the political landscape and the
   internal risk/maturity reads.)
4. **Per-field route-back:** score/ranking corrections → Phase 6
   (`scoring-opportunities`); wave/sequencing corrections → Phase 7
   (`prioritizing-roadmap`). **Route-back re-runs the engine** (composites are
   computed), like `baseline` — unlike `scope`.
5. Audience: decision-maker + sponsor + IT lead.

## Source schemas (verified)

- **scores/_index.md:** `OPP-ID | Composite | Horizon | B/B/P` table — the ranking
  source.
- **scores/OPP-NNN.md:** per-OPP six-dimension detail — Value Potential, Technical
  Feasibility, Data Readiness, Org Change Readiness, Strategic Alignment, Time to
  Value — each a 1–5 score with rationale and a source citation; plus the Execution
  Horizon (Short-run / Long-run) classification and Build/Buy/Partner. Composite =
  `round(sum(6 dimensions)/6, 2)`.
- **opportunities/_index.md:** `OPP-ID | Process | Type | Structural` — Type and the
  `Structural` (`addressing-root` / `optimizing-around` / `not-applicable`) value
  per OPP.
- **opportunities/OPP-NNN.md:** the `## OPP-NNN — [title]` header line, per OPP.
- **roadmap.md:** Wave 1 initiative detail cards; Wave 1 Summary Table; Wave 2/3
  tables; Enabler Projects table; Budget Envelope Estimate table; sequencing
  constraints.
- **scope.md:** header only (engagement name for the masthead).

## Architecture

```
Phase 7 (roadmap.md saved)
        │
        ▼
  building-checkpoint  (id = "portfolio")
   1. read scope.md → engagement folder; verify roadmap.md + scores/_index.md exist
   2. invoke deliverable-gate in Checkpoint Mode (checkpoint=portfolio)
   3. dispatch section-renderer-checkpoint-portfolio → _staging/checkpoint-portfolio/
   4. assemble checkpoints/checkpoint-portfolio.html from the checkpoint shell
   5. record checkpoints/CP-portfolio-outcome.md
        │
        ▼
  Decision-maker + sponsor + IT lead review
        │
   ┌────┴───────────────────┐
 Confirmed             Changes Requested
   │                        ├─ score/ranking change → Phase 6 (scoring-opportunities)
   ▼                        └─ wave/sequencing change → Phase 7 (prioritizing-roadmap)
 Phase 8 may proceed           → correct source → re-run engine → regenerate
```

### Component 1 — Registry row (modify `skills/building-checkpoint/SKILL.md`)

Add a `portfolio` row to the Checkpoint Registry (the skill is already
parameterized; this is additive):

| id | Insert after | Audience | Source files | Renderer | Output HTML | Outcome record | Route-back phase |
|---|---|---|---|---|---|---|---|
| `portfolio` | Phase 7 | Decision-maker + sponsor + IT lead | `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, `roadmap.md`, `scope.md` (header only) | `section-renderer-checkpoint-portfolio` | `checkpoints/checkpoint-portfolio.html` | `checkpoints/CP-portfolio-outcome.md` | Phase 6 (`ai-process-assessment:scoring-opportunities`) for score/ranking fields; Phase 7 (`ai-process-assessment:prioritizing-roadmap`) for wave/sequencing fields |

Additional per-checkpoint edits in the skill:

- **Frontmatter description:** update "(Checkpoints 1 `scope` and 2 `baseline` are
  wired)" → "(Checkpoints 1 `scope`, 2 `baseline`, and 3 `portfolio` are wired)".
- **Registry intro line:** update "The `baseline` (Checkpoint 2) and `scope`
  (Checkpoint 1) rows are active. The table format anticipates Checkpoint 3 (future
  cycle)." → all three rows are active; the pattern is complete.
- **Session Start predecessor check** for `portfolio`: both `roadmap.md` and
  `scores/_index.md` must exist; halt naming whichever is missing.
- **Checkpoint shell sticky nav** for `portfolio`: four anchors — `#portfolio`,
  `#scoring`, `#roadmap`, `#validate`; masthead label "Portfolio & Roadmap Review
  — Interim".
- **Recording the outcome / routing:** per-field — a corrected score/ranking field
  routes to Phase 6; a corrected wave/sequencing field routes to Phase 7; a mixed
  outcome routes to both. **Correct the source file(s) → re-run
  `python -m engine.run <name>/` → regenerate the checkpoint** (the composite scores
  are engine-computed, so the engine run is required, exactly like `baseline`).
- **Chain to next skill** for `portfolio`: on Confirmed →
  `ai-process-assessment:packaging-usecases` (Phase 8); on Changes Requested →
  `ai-process-assessment:scoring-opportunities` (Phase 6, score fields) /
  `ai-process-assessment:prioritizing-roadmap` (Phase 7, sequencing fields).

### Component 2 — `section-renderer-checkpoint-portfolio` agent (new)

**File:** `agents/section-renderer-checkpoint-portfolio.md`

Data-driven synthesis renderer. Reads `scores/_index.md`, `scores/OPP-NNN.md`,
`opportunities/_index.md`, `opportunities/OPP-NNN.md`, and `roadmap.md`. Emits four
section blocks:

- **`#portfolio`** — ranked table, **one row per OPP-ID present in
  `scores/_index.md`** (not a fixed count), ranked by composite descending: Rank,
  OPP, Title, Type (with the `type-*` badge class), Structural, Composite (score
  bar), Wave, B/B/P. Joins the four normalized sources on OPP-ID. Missing fields
  render as PENDING.
- **`#scoring`** — per-OPP six-dimension detail with rationale, one compact block
  per OPP (Value Potential, Technical Feasibility, Data Readiness, Org Change
  Readiness, Strategic Alignment, Time to Value — each score + its rationale/source
  verbatim from `scores/OPP-NNN.md`), plus the Horizon and B/B/P. This is the
  transparency the audience needs to validate the ranking. Render every OPP that has
  a `scores/OPP-NNN.md`; PENDING any dimension a file omits.
- **`#roadmap`** — three-wave timeline (render the waves that exist in `roadmap.md`),
  Wave 1 initiative cards (render the Wave-1 initiatives that exist — **not** a fixed
  7), the enabler-projects / dependency note, and the Budget Envelope Estimate as
  investment stat cards. Quick-win badges rendered only when `roadmap.md` marks an
  initiative as a quick win. ROM label preserved.
- **`#validate`** — confirm-or-correct list + the framing question: *"Did we
  prioritize and sequence Wave 1 correctly?"* plus any open questions / PENDING
  fields.

**Renderer discipline (load-bearing):**
- No invented content; PENDING for absent fields; never fabricate a score, wave, or
  dollar figure.
- All values verbatim/selected from source; the only computation permitted is the
  score-bar width (`round(score/5*100)%`) and ranking order, mirroring the Phase 11
  portfolio renderer.
- Data-driven counts — render exactly the OPPs/initiatives/waves that exist. **Never
  hardcode "7 Wave-1 cards", a specific envelope, or named OPPs/enablers** (the bug
  in the Phase 11 renderers that motivated a bespoke agent).
- No wrapper markup (`<html>`, `<body>`, `<style>`, `<script>`); only
  shell-defined / building-deliverable design-system CSS classes (`section-block`,
  `callout`, `gap-note`, table styles, `uc-card*`, `score-bar*`, `wave-badge`,
  `w1`/`w2`/`w3`, `uc-card-type`, `type-*`, `stat-*`, `wave-timeline`, `wave-band*`,
  `wave-pill*`, `callout-note`, `uc-quickwin`).

**No hard refusals on content sensitivity** — unlike the `scope` renderer, this
checkpoint renders the full work product. (State this explicitly so a future editor
does not "tighten" it by analogy to `scope`.)

### Component 3 — Gate Checkpoint Mode `portfolio` case (modify `skills/deliverable-gate/SKILL.md`)

Add a `portfolio` paragraph to the existing `## Checkpoint Mode` section. For
`checkpoint=portfolio` (after Phase 7), read only: `scope.md` (header),
`scores/_index.md`, the `scores/OPP-NNN.md` files, `opportunities/_index.md`, the
`opportunities/OPP-NNN.md` files, `roadmap.md`, and the computed inputs
`model/scores.json`, `model/initiatives.json`, and `model/results.json`. Applicable
dimensions:

- **Completeness** — every OPP-ID in `scores/_index.md` is reflected in the
  portfolio and has a `scores/OPP-NNN.md`; every wave in `roadmap.md` is present; the
  portfolio is internally coherent (ranking ↔ wave assignment ↔ B/B/P align).
- **Evidence integrity** — every figure rendered traces to a
  `scores/`/`opportunities/`/`roadmap.md` source.
- **Determinism integrity** — every composite equals its `model/scores.json` /
  `model/results.json` source; ROM/investment figures trace to
  `model/initiatives.json`; PENDING renders as PENDING, never an invented number.
  **Applicable here** (figures exist) — contrast with the `scope` checkpoint where
  it is N/A.

If `scores/_index.md` or `roadmap.md` is missing, the checkpoint does **NOT** clear
— route back (scores → Phase 6, roadmap → Phase 7); a missing portfolio must not
silently pass. Do **not** dispatch the `opportunity-reviewer` subagent (checkpoint
clearance is a lighter, scoped pass). Dimensions that require later phases (Business
Case, Communication readiness) are not applicable — note them as deferred. Record
clearance as `Checkpoint portfolio — cleared (Completeness, Evidence, Determinism)`
in `evidence-log.md`. On non-clearance, route a score/ranking gap to Phase 6 and a
wave/sequencing gap to Phase 7 before the checkpoint renders. The terminal gate path
and the existing `baseline`/`scope` cases are unchanged.

### Component 4 — Keystone + system-prompt wiring

- **Routing Logic:** after Phase 7 saves `roadmap.md`, before Phase 8 → recommended:
  invoke `building-checkpoint` (checkpoint `portfolio`) to validate the prioritized
  portfolio and wave sequencing with the decision-maker + sponsor + IT lead.
  Recommended-and-recorded, not blocking. On "Changes Requested", route score
  corrections to Phase 6 and sequencing corrections to Phase 7, re-run the engine,
  and regenerate before Phase 8.
- **When-to-Invoke:** add a row mapping "validate the portfolio", "review the
  roadmap with the client", "portfolio sequencing checkpoint" → `building-checkpoint`.
- **Engagement Folder Convention:** the generic `checkpoints/` entry already covers
  `checkpoint-<id>.html` / `CP-<id>-outcome.md`; no change needed.
- **Mirror to `system-prompt.md`** — re-mirror after the keystone edit; the
  envelope-balance guard and the verbatim-mirror guard both apply.

## Testing

- **`tests/test_agents.py`** — new renderer agent → bump agent count 16 → 17;
  frontmatter `name`/`description` valid; `name` matches filename.
- **`tests/test_skills.py`** — unchanged (no new skill; registry row only). Skill
  count stays 18.
- **`tests/test_guards.py`** — must stay green: no retired tokens
  (`baselines.md`/`process-map.md`) introduced; deliverable-gate Session Start still
  free of `executive-summary.md` and still carries `results.json` + "determinism";
  system-prompt mirror verbatim + envelope balanced. **No new leak guard** — the
  "show everything" decision means there is no content-exclusion invariant to lock
  for this checkpoint.
- Full suite green (currently 166 on main).

## Rollout

- Markdown change → human-merged PR. Version bump (minor, 2.12.0) + CHANGELOG; on
  merge, auto-tag → release publishes. **Closes #49** (all three checkpoints live).

## Risks / open points

- **Renderer over-tightening:** a future editor might "harden" this renderer by
  analogy to the `scope` renderer and start excluding scoring detail. The renderer
  spec must state explicitly that full-transparency is intentional for this
  checkpoint.
- **Per-field route-back ambiguity:** the skill must make clear that score edits go
  to Phase 6 and sequencing edits to Phase 7, and that both require an engine re-run
  before regeneration.
- **Renderer generality:** render whatever OPPs/initiatives/waves exist; PENDING the
  rest; never hardcode counts or sample values (the explicit failure mode of the
  Phase 11 renderers).
