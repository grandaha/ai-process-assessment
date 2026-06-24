# Slice 4 — Step Reviews (operator-facing per-step review & revise)

**Initiative spec.** New work, sequenced **before D2 (#89)**: a good per-step review
experience is part of what makes the product worth launching.
**Date:** 2026-06-24. **Builds on:** Slice 2 (edit-splicing, holding-the-line),
Slice 3 (status projection, staleness, decision log).

## 1. Problem

As the operator (the consultant or person driving the model) moves through the assessment,
each step produces working output — but it is either a single working file nobody is
prompted to review, or, for the folder-based steps, **fragmented** across an `_index.md`
plus a pile of per-item files (`processes/PROC-NNN.md`, `opportunities/OPP-NNN.md`,
`scores/OPP-NNN.md`, `usecase-briefs/UC-NNN.md`). Nobody can "review the opportunities" by
reading a split folder. Today only two output tiers are framed for review: the **3 client
checkpoints** (stakeholder validation) and the **final deliverable** (client hand-off).
There is no **operator tier** — a readable working document for *each* step that the person
driving reviews, marks up, and revises before the next step builds on it.

## 2. Goal

A third, operator-facing output tier — **step reviews**:

- Each step has a **readable review document** the operator can open. For the fragmented
  steps it is a consolidated render; for steps that already have a clean single document it
  is that document.
- The operator marks up the document **inline**, anchoring each comment to the item it is
  about.
- The conductor **works through the comments with the operator**, routing agreed changes
  through the existing audited edit engine — and **pushes back when a comment conflicts**
  with the evidence, the methodology, the cascade, or a prior decision, rather than
  complying blindly.
- Revisions re-derive downstream via staleness, keeping the chain coherent.

Non-goals: no client-facing rendering here (that is the checkpoints/deliverable); no
annotation UI / JS / server (deliberately rejected — see §7); no new numbers (reviews
render existing content, never compute).

## 3. The review document

### 3.1 Form

A **markdown** file the operator opens in their editor (this plugin lives in the IDE).

- **Fragmented steps (Phases 4, 5, 6, 8)** → a consolidated render at
  `<engagement>/reviews/<NN>-<phase>.md`, produced by a parameterized pure-Python renderer.
  The render is a **target, not a source of truth**: it consolidates the `_index.md` summary
  table and each per-item file into one readable document, each item a section carrying its
  **stable anchor** (the item id, e.g. `OPP-3`). No new content — pure consolidation of
  existing files (mirrors the checkpoint renderers' "no new figures" discipline).
- **Single-document steps (Phases 1, 2, 3, 7, 8.5, 9, 10)** → the existing document
  (`scope.md`, `context.md`, `tech-inventory.md`, `roadmap.md`, `cost-actuals.md`,
  `business-case.md`, `executive-summary.md`) **is** the review surface. No duplicate render.
  Anchors are the document's own headings.

The operator never sees a fragmented folder as the review surface; they see one readable
document either way. (Phase 11, `deliverable.html`, has no operator review — it *is* the
client hand-off tier, reviewed via the deliverable-gate, not the operator tier.)

### 3.2 New unit — `state/step_review.py`

Pure functions of the filesystem, stdlib + `state.*` only (matches `state/status.py`,
`state/integrity.py`).

```python
def render_review(root, phase_id) -> str:
    """Consolidate a fragmented phase's _index.md + per-item files into one readable
    review document (each item a section with its id anchor). Pure; deterministic.
    Raises ValueError for a non-fragmented phase_id (those use their source doc)."""

def review_path(phase_id) -> str:
    """Relative path of the review render target for a fragmented phase,
    e.g. '5' -> 'reviews/05-opportunities.md'. (Single-doc phases return their
    source path.)"""
```

A thin CLI (`python3 <engine_root>/state/step_review.py <folder> <phase_id>`) writes the
render target and prints its path — same invocation/exit-code contract as the other
`state/*` tools. **Regeneration is unconditional** from source when invoked (the
`generate-artifact` discipline: never trust a stale cache) — but see §5 for the
comment-aware lifecycle that prevents regeneration from clobbering pending comments.

## 4. Inline comments

### 4.1 Convention

Right under the item they are reacting to, the operator drops a visible, easy-to-type,
anchored marker — a markdown blockquote led by a comment sigil:

```
### OPP-3 — Automated invoice reconciliation
…item content…

> 💬 @OPP-3 this is augmentation, not automation — a human still signs off
```

- The anchor is the explicit `@<id>` token; if omitted, it falls back to the **nearest
  preceding item heading**. Either resolves to exactly one owning item.
- Extraction is a **pure function** — `extract_comments(text) -> list[Comment]` where
  `Comment(anchor, body, line)` — fully inside the LLM-free test stack. (This is markdown
  text parsing, not the rejected JS annotation surface.)
- The sigil (`> 💬`) is chosen to be visible in both raw and rendered markdown and trivially
  greppable. The exact sigil is finalized in the chunk plan; a plain-text fallback
  (`> [comment] …`) is supported by the same extractor.

`extract_comments` lives in `state/step_review.py` and is reused for both the rendered
review targets and the single-document review surfaces.

### 4.2 The operator never hand-edits source content

Comments express *intent*; the conductor applies the change through the owning artifact via
edit-splicing (Slice 2 Chunk B). The operator does not edit `model/*.json` or per-item
fields directly — that would bypass the audited pipeline. They comment; the conductor routes.

## 5. The comment-aware lifecycle

The lifecycle is explicit so inline comments are never silently destroyed:

1. **Generate.** Step completes → conductor renders the review document fresh from source
   (fragmented phases) or points the operator at the source doc (single-doc phases).
2. **Annotate.** Operator adds inline `> 💬` comments at anchors, saves.
3. **Intake.** Operator says "I've commented" (or the conductor re-reads on request) →
   conductor runs `extract_comments` over the document.
4. **Work through (with pushback — §6).** For each comment: classify via edit-splicing,
   check for conflict; apply the agreed changes to the owning artifact; re-run the audited
   pipeline; staleness re-derives downstream.
5. **Regenerate.** Conductor regenerates the review document fresh — changes reflected,
   **resolved** comments cleared.

Invariants:
- The conductor **never regenerates a document that still carries unresolved comments**
  silently. Regeneration happens at step 1 (initial) and step 5 (after a processing pass).
- Regeneration is **comment-preserving**: any comment not yet resolved is carried forward to
  its anchor in the fresh render (safety net for a mid-review re-render).
- For **single-document** review surfaces there is no regeneration (the doc is source); the
  conductor applies the edit and **strips the resolved comment lines** in the same edit, so
  the source never accumulates stale comments.

## 6. Conflict pushback

Comments are not applied blindly. As the conductor works through each one (step 4), it
checks the requested change against what it already knows and, on a conflict, **surfaces it
and reasons it through with the operator** — firm-and-teaching (the human reason + the
fastest honest path), the *holding-the-line* posture from Slice 2 Chunk C. It does **not**
refuse (the operator is the decision-maker) and it does **not** silently comply against the
evidence or the method; the operator decides and the override is logged.

Conflict classes:

| Class | Example | Response |
|---|---|---|
| **Evidence / grounding** | "change this figure to $500k" where the figure is *computed* from a sourced input | Cannot overwrite a computed result (breaks traceability/AC-3); offer to change the underlying assumption instead. |
| **Methodology / rationalization** | "skip GRC on this one" while it is flagged Red | A rationalization escape → *holding the line* + auto-log to the improvement flywheel (Slice 3 C). |
| **Cascade / consistency** | "make OPP-3 wave 1" when its dependency is in wave 2 | Surface the inconsistency before applying. |
| **Prior decision** | a comment reversing a decision already in the decision log | "You decided X earlier — override it?" (logged as an override). |
| **Intra-batch** | two comments in the same pass that contradict each other | Surface both; ask which governs. |

Detectable-deterministically conflicts (evidence/computed-vs-input, cascade, prior-decision,
intra-batch) are flagged by composing existing machinery (the deliverable-gate's
markdown↔results discipline, `state.staleness`, the decision log, the data contract). The
methodology/rationalization class reuses *holding the line* + the master rationalization
table + the flywheel auto-flag. **No new conflict engine** — this is a composition layer in
the conductor over capabilities Slices 2 and 3 already provide.

## 7. Boundary surfacing — AI-native, lightweight

Step reviews slot into the drive loop's **existing guided pauses** (no new gate). When a
step completes, the conductor narrates what came out and what moved, and offers the review:
*"Here's what I found — want to look or change anything before we build on it?"* The operator
can wave it through ("looks good, continue"), open/read the review document, or comment. The
**register** (operator vs consultant, Slice 2 C) drives how much the conductor explains.
This is the operator tier; it is **not** a recorded sign-off — the 3 client checkpoints
remain the recorded stakeholder validations.

## 8. The deferred annotation surface (route-2 seam)

A browser highlight-and-comment UI was considered and **rejected for now**: it needs a
surface outside the LLM-free test stack, re-opens the bespoke-UI door closed with the
dashboard removal (#73/#75), forks the experience by surface right before the public launch,
and its real payoff (composing the comment text) is something the AI should absorb anyway.
The design keeps the seam open: everything reduces to `(anchor, comment)` pairs fed to
edit-splicing, so if dense-document friction is ever *measured*, an HTML view can emit the
same anchored block with zero back-end rework. Trigger: a real engagement shows the inline
markdown convention measurably slows the operator on dense documents.

## 9. Decomposition

Two chunks, same brainstorm → spec → plan → subagent-TDD → review flow used for Slices 2–3:

- **Chunk A — Step review documents.** `state/step_review.py` (`render_review`,
  `review_path`, CLI); the parameterized consolidation of the 4 fragmented phases; conductor
  "step review at the boundary" surfacing. Deliverable: the operator can open one readable
  review document for any step.
- **Chunk B — Inline comments + conflict pushback.** `extract_comments`; the comment-aware
  lifecycle (§5); conductor wiring to work through comments, route via edit-splicing, and
  push back on conflicts (§6). Deliverable: the operator marks up a review and the conductor
  revises with them, coherently.

## 10. Files (across both chunks)

- **Create** `state/step_review.py` — `render_review`, `review_path`, `extract_comments`,
  `Comment`, CLI.
- **Create** `state/tests/test_step_review.py` — renderer consolidation, anchors, determinism,
  CLI; comment extraction (explicit + positional anchor, multiple, none); comment-preserving
  regeneration.
- **Modify** `skills/conducting-engagement/SKILL.md` — add "Step reviews" (boundary
  surfacing + lifecycle) and the conflict-pushback handling; reference from the drive loop.
- **Modify** `tests/test_conductor_skill.py` — guards for the new sections (present,
  references `state/step_review.py`, lifecycle protects comments, conflict-pushback classes,
  jargon-free narration sweep).

## 11. Testing strategy

- **`state/tests/test_step_review.py`** (pure units): `render_review` consolidates a folder
  phase's index + items into one doc with each item's id anchor present; raises for a
  single-doc phase; deterministic (same inputs → same bytes). `extract_comments` returns the
  right `(anchor, body)` for explicit `@id`, positional fallback, multiple comments, and
  none; ignores non-comment blockquotes. Comment-preserving regeneration: a render that
  carries an unresolved comment re-emits it at its anchor. CLI: writes the target, prints the
  path, exit 0; non-dir → exit 2.
- **`tests/test_conductor_skill.py`** (static guards): the step-review and conflict-pushback
  sections present; references the renderer; states the no-silent-clobber + comment-preserving
  invariants; enumerates the conflict classes; narration jargon-free (forbidden-token sweep).
- Full suite stays green.

## 12. Reconciliation

- **Composition, not new engines.** The renderer/extractor are the only new code; the
  revision path is edit-splicing (Slice 2 B), the cascade is staleness (Slice 3), conflict
  pushback is holding-the-line + gates + decision log + flywheel.
- **Distinct from checkpoints and the deliverable.** Step reviews are the *operator* tier
  (internal, lightweight); the 3 checkpoints stay the *client* validation tier; the final
  deliverable stays the client hand-off. No overlap.
- **No stale-cache risk.** Review render targets are regenerated from source; the
  comment-aware lifecycle is the only thing that defers regeneration, and it preserves
  comments when it does.
- **Pure/stdlib/testable**, matching the `state/*` conventions — the rejected JS surface is
  explicitly out (§8).
