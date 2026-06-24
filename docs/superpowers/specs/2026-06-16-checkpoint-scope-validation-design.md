# Checkpoint 1 — Scope & Context Alignment — Design

**Date:** 2026-06-16
**Status:** Approved for planning
**Author:** Dave (with Claude)
**Issue:** grandaha/ai-process-assessment#49 (Checkpoint 1 of 3)
**Builds on:** the checkpoint pattern shipped in v2.10.0 (`docs/superpowers/specs/2026-06-16-checkpoint-baseline-validation-design.md`)

## Summary

Add **Checkpoint 1 — Scope & Context Alignment**, an interim client-facing HTML
artifact rendered after Phase 2, so the sponsor and decision-maker confirm that
the engagement's framing — the question being answered, who decides, scope
boundaries, success criteria, and the strategic context — is correct *before* the
engagement invests in tech inventory (Phase 3) and process discovery (Phase 4).

This is the cheapest place to catch misalignment: if the sponsoring question or
scope is wrong, every downstream phase is wrong. It is the second checkpoint built
on the established pattern (the `building-checkpoint` skill, the scoped
deliverable-gate Checkpoint Mode, the recorded feedback loop). Checkpoint 3
(Portfolio & Roadmap) remains a future cycle.

## Goals

- A consultant can produce a polished scope-and-context validation artifact from
  `scope.md` + `context.md`, with no new analysis.
- The sponsor/decision-maker can confirm or correct the framing; the outcome is
  recorded and routes corrections back to the owning phase.
- Internal consultant intelligence (the political landscape; the candid internal
  risk-tolerance read) is **never** exposed in the client-facing artifact.

## Non-Goals

- Not building Checkpoint 3.
- Not changing the `building-checkpoint` skill's architecture, the outcome
  template, or the enforcement model (recommended-and-recorded) — those are reused
  as-is. This cycle adds a registry row, a renderer, and small gate/keystone
  extensions.
- Not auto-merge-eligible: markdown/methodology work → human-merged.

## Decisions (locked in brainstorming)

1. **Insert after Phase 2** (once `context.md` exists), before Phase 3.
2. **Exclude the political landscape** from the artifact, and render risk only as
   neutral/regulatory framing — the political map and internal risk-tolerance read
   are internal-only.
3. Sources: `scope.md` + `context.md`. Audience: sponsor + decision-maker.
4. **Per-field route-back:** scope corrections → Phase 1 (`scoping-engagement`);
   context corrections → Phase 2 (`mapping-context`).

## Source schemas (verified)

- **scope.md:** Engagement folder, Sponsoring question, Decision-maker (name/role
  + what they'll do differently), In-scope domains, Out-of-scope boundaries,
  Success criteria, Constraints.
- **context.md:** Business model, Strategic priorities, Org structure, AI/automation
  maturity, Funding model, Risk posture, **Political landscape** (aligners,
  vetoers, skeptics — internal-only).

## Architecture

```
Phase 2 (context.md saved)
        │
        ▼
  building-checkpoint  (id = "scope")
   1. read scope.md → engagement folder; verify scope.md + context.md exist
   2. invoke deliverable-gate in Checkpoint Mode (checkpoint=scope)
   3. dispatch section-renderer-checkpoint-scope → _staging/checkpoint-scope/
   4. assemble checkpoints/checkpoint-scope.html from the checkpoint shell
   5. record checkpoints/CP-scope-outcome.md
        │
        ▼
  Sponsor + decision-maker review
        │
   ┌────┴───────────────┐
 Confirmed         Changes Requested
   │                    ├─ scope-field change   → Phase 1 (scoping-engagement)
   ▼                    └─ context-field change → Phase 2 (mapping-context)
 Phase 3 may proceed       → correct → regenerate the checkpoint
```

### Component 1 — Registry row (modify `skills/building-checkpoint/SKILL.md`)

Add a `scope` row to the Checkpoint Registry table (the skill is already
parameterized; this is additive):

| id | Insert after | Audience | Source files | Renderer | Output HTML | Outcome record | Route-back phase |
|---|---|---|---|---|---|---|---|
| `scope` | Phase 2 | Sponsor + decision-maker | `scope.md`, `context.md` | `section-renderer-checkpoint-scope` | `checkpoints/checkpoint-scope.html` | `checkpoints/CP-scope-outcome.md` | Phase 1 (`ai-process-assessment:scoping-engagement`) for scope fields; Phase 2 (`ai-process-assessment:mapping-context`) for context fields |

- **Session Start predecessor check** for `scope`: both `scope.md` and `context.md`
  must exist; halt naming whichever is missing.
- **Checkpoint shell sticky nav** for `scope`: three anchors — `#scope`,
  `#context`, `#validate`.
- **Recording the outcome / routing:** the route-back is per-field — a corrected
  *scope* field routes to Phase 1; a corrected *context* field routes to Phase 2.
  State both explicitly in the skill's "Recording the outcome" section. (The
  existing `baseline` single route-back is unchanged.)

### Component 2 — `section-renderer-checkpoint-scope` agent (new)

**File:** `agents/section-renderer-checkpoint-scope.md`

Data-driven synthesis renderer. Reads `scope.md` + `context.md`. Emits three
section blocks:

- **`#scope`** — sponsoring question; decision-maker + what they'll do differently;
  in-scope domains; out-of-scope boundaries; success criteria; constraints.
  Verbatim from `scope.md`; absent fields render as **PENDING**.
- **`#context`** — **only the genuinely shareable framing fields: business model,
  strategic priorities, funding model.** Verbatim from `context.md`; PENDING for
  absent. (Refined during implementation review: `context.md`'s `Risk posture`
  bundles regulatory facts with a candid internal cultural-tolerance read, and
  `AI/automation maturity` carries candid internal sentiment — both are internal
  consultant assessments and are **excluded**, not extracted, to remove any
  leak path. Org structure and the political landscape are likewise excluded.)
- **`#validate`** — confirm-or-correct list + the framing question: *"Did we frame
  the decision you're trying to make correctly?"* plus any open questions.

**Hard refusals (renderer-specific, load-bearing):**
- **Never render the political landscape** (aligners/vetoers/skeptics) — it is
  internal-only and must not appear in the client-facing artifact.
- **Never render the internal risk-tolerance / cultural-risk read** — render risk
  only as neutral regulatory-exposure facts.
- No invented content; PENDING for absent fields; no wrapper markup; only
  shell-defined CSS classes.

### Component 3 — Gate Checkpoint Mode `scope` case (modify `skills/deliverable-gate/SKILL.md`)

Add a `scope` paragraph to the existing `## Checkpoint Mode` section. For
`checkpoint=scope` (after Phase 2), read only `scope.md` + `context.md`. Applicable
dimensions:

- **Completeness** — every in-scope domain named in `scope.md` is reflected; the
  scope is internally coherent (sponsoring question ↔ success criteria ↔ in/out
  scope align).
- **Evidence integrity** — any claim rendered traces to `scope.md`/`context.md`.

**Determinism integrity is N/A** at this checkpoint (no numeric figures exist yet)
— state this explicitly. Do not dispatch `opportunity-reviewer`. Record clearance
as a distinct checkpoint entry (`Checkpoint scope — cleared`). The terminal gate
path and the existing `baseline` case are unchanged.

### Component 4 — Keystone + system-prompt wiring

- **Routing Logic:** after Phase 2 saves `context.md`, before Phase 3 → recommended:
  invoke `building-checkpoint` (checkpoint `scope`) to validate framing with the
  sponsor + decision-maker. Recommended-and-recorded, not blocking. Per-field
  route-back on Changes Requested.
- **When-to-Invoke:** add a row mapping "validate the scope", "confirm the
  engagement framing", "scope alignment checkpoint" → `building-checkpoint`.
- **Engagement Folder Convention:** the `checkpoints/` entry already exists (from
  v2.10.0); no change needed beyond confirming it covers `checkpoint-scope.html` +
  `CP-scope-outcome.md` (it is generic `checkpoint-<id>.html` / `CP-<id>-outcome.md`).
- **Mirror to `system-prompt.md`** — re-mirror after the keystone edit; the
  envelope-balance guard (added in v2.10.0) plus the verbatim-mirror guard both
  apply.

## Testing

- **`tests/test_agents.py`** — new renderer agent → bump agent count 15 → 16;
  frontmatter `name`/`description` valid.
- **`tests/test_skills.py`** — unchanged (no new skill; registry row only). Skill
  count stays 18.
- **`tests/test_guards.py`** — must stay green: no retired tokens
  (`baselines.md`/`process-map.md`) introduced; deliverable-gate Session Start
  still free of `executive-summary.md` and still carries `results.json` +
  "determinism"; system-prompt mirror verbatim + envelope balanced.
- Full suite green (currently 165).

## Rollout

- Markdown change → human-merged PR. Version bump (minor, 2.11.0) + CHANGELOG; on
  merge, auto-tag → release publishes (end-to-end since #44).

## Risks / open points

- **Sensitive-content leakage** is the primary risk. The renderer's hard refusal
  against the political landscape + internal risk read is the structural guard; it
  must be unambiguous. (Consider a future guard test asserting the scope renderer
  forbids "political landscape" — noted, not required this cycle.)
- **Per-field route-back ambiguity** — the skill must make it clear that scope
  edits go to Phase 1 and context edits to Phase 2, so a mixed outcome routes both.
- Renderer generality: render whatever fields exist; PENDING the rest (same
  discipline as the baseline renderer).
