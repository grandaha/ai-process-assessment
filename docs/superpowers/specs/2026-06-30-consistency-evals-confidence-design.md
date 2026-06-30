# Consistency Evals → Confidence Signal (tagger + scorer) — Design

**Issue:** #192 — Eval harness + consistency evals for the judgment agents (evals: phase 1)
**Branch:** `feat/192-consistency-evals` · **Worktree:** `.worktrees/192`
**Date:** 2026-06-30

## Goal

Stand up a reusable consistency-eval instrument for the methodology's LLM judgment
agents, and surface its result as a first-class **confidence** signal in the
client-facing checkpoints. This slice covers the two no-alignment agents:
`step-capability-tagger` (Phase 4) and `opportunity-scorer` (Phase 6).
`opportunity-typer` and `process-mapper` are deferred to a follow-up (they need a
cross-run alignment heuristic; tracked separately).

The methodology's recommendations rest on LLM judgment that is validated today only
by *provenance* (the agent cited a source) and an *optional* human checkpoint.
Nothing measures whether a judgment is even **consistent** run-to-run. This builds
that measurement and makes it visible.

## Constraint that shapes everything

This is a **Claude Code plugin** distributed as skills/agents markdown. It does **not**
make `claude -p` or Anthropic API calls. The only way to generate N runs of an agent
is the way the plugin already runs everything: **Claude Code dispatches the agent N
times as subagents**, driven by a skill. Therefore the work splits into a
pure-Python *metrics* layer (CI-testable) and a *skill* that drives the dispatch
(LLM work, not CI-testable).

## AI-native framing (governing rule)

Confidence is **intrinsic and automatic, but non-blocking**, and its plumbing is
invisible:

- **Automatic, not opt-in.** The Conductor self-checks consistency at Phase 4 and
  Phase 6 on the judgments that drive downstream decisions. The user never invokes
  an "eval" and never sees the word.
- **Non-blocking, not a hard gate.** It informs the existing baseline/portfolio
  checkpoints rather than halting the human. Every phase transition remains a human
  decision. (Orthogonal to #195, which hardens the *factual baseline* gate.)
- **Confidence is the UX; "eval" is internal.** The user sees a Confidence
  indicator on steps/opportunities in the checkpoint they already review, with shaky
  items highlighted for attention.

## Architecture — three layers

```
Phase 4: step-capability-tagger ×N ─┐
Phase 6: opportunity-scorer     ×N ─┤  (cross-cutting skill: evaluating-consistency)
                                    ▼
        _staging/evals/<phase>/<target>/run-1.md … run-N.md
                                    ▼
        state/evals.py  (pure metrics: parse → agreement/variance → flag)
                                    ▼
        evals/<target>.evals.json   +   evals/_index.md     (sidecar; NOT model/*.json)
                                    ▼
   ┌───────────────────────────────┴───────────────────────────────┐
   ▼ scorer (client-facing)                                         ▼ tagger (assessor-facing)
state/checkpoint_doc.py _build_portfolio reads sidecar       Conductor surfaces unstable steps
   → portfolio checkpoint .docx gains a per-opp Confidence      at Phase 4 + evals/_index.md;
     column; unstable opportunities flagged for the             assessor re-examines shaky steps
     decision-maker's adjudication                              before Phase 5. NO client docx
                                                                (computed color is internal).
```

**Why the split (code-grounded):** the scorer's outputs (dimension scores, composite,
B/B/P) are already shown to the decision-maker in the portfolio checkpoint, so a
Confidence column there fits. The tagger's output is the per-step **computed color**,
which the methodology *deliberately hides* from owner-facing docs (`process_review.py`
strips the rating; the baseline checkpoint is process-level with no step table). Color
is internal assessor analysis, so its confidence is surfaced to the assessor (Conductor
+ `evals/_index.md`), not injected into a client document. Both are "user-facing" — the
signal reaches a human decision point — but the right human differs per agent.

### Layer 1 — `state/evals.py` (pure metrics engine)

A peer of `state/capability.py` and `state/integrity.py`: pure functions, no network,
no subprocess, no mutation beyond the explicit write entry point. Reuses
`capability.parse_step_capability` and `capability.compute_color` so the eval's notion
of "color" is identical to the engine's.

**Tagger consistency** — input: N tagger output texts (each a full
`**Step capability:**` table) for one process.
- Parse each run → per-step attribute set + computed color.
- Per step: attribute-set agreement (mean pairwise Jaccard across runs) and
  **computed-color unanimity** (all N runs agree on Green/Yellow/Red).
- A step is **unstable** ⇔ computed color is not unanimous across the N runs.
  (Color drives chains, which add/remove whole opportunities — the highest-stakes
  instability. Jaccard is reported as a secondary signal, not a flag trigger.)
- Result: `{process_id, n_runs, steps: [{step, color_unanimous, colors, jaccard_mean, unstable}], unstable_step_count}`.

**Scorer consistency** — input: N scorer output texts (each a dimensional-score table
+ B/B/P) for one opportunity.
- Parse each run → 6 dimension integers, composite (recomputed via
  `engine.compute.score_composite` for parity), B/B/P classification.
- Per dimension: spread (max−min) and population stdev. Composite spread.
  B/B/P modal agreement (fraction of runs at the modal classification).
- An opportunity is **unstable** ⇔ composite spread > 0.5 **or** any dimension
  spread ≥ 2 **or** B/B/P not unanimous.
- Result: `{opp_id, n_runs, dimensions: {<dim>: {spread, stdev, values}}, composite_spread, bbp_modal_agreement, unstable}`.

**Defaults:** `N = 5` (configurable). Thresholds as above, defined as module
constants so they are testable and overridable.

**Write entry point + CLI:** `python -m state.evals <engagement> <phase> <target>`
reads `_staging/evals/<phase>/<target>/run-*.md`, writes
`evals/<target>.evals.json`, and (re)builds `evals/_index.md` (one row per target:
id, n_runs, unstable count, overall stable|unstable). Mirrors the existing
`state.checkpoint_doc` CLI shape.

### Layer 2 — `evaluating-consistency` skill (the runner)

A **cross-cutting** skill (same role as `building-checkpoint`: Conductor-invoked, not
its own phase). Given a phase + target, it:
1. Re-dispatches the target agent **N times** on the *same* inputs the phase already
   passed it (tagger: same PROC file + evidence; scorer: same OPP + PROC + tech-inventory + context),
   in a single parallel tool-call batch per target, each writing to
   `_staging/evals/<phase>/<target>/run-K.md`.
2. Runs `python -m state.evals <engagement> <phase> <target>`.
3. Returns a one-line summary (target, n_runs, unstable count). Does **not** echo run
   content into the main context.

The skill is the only non-CI-testable piece; it is covered by the existing
structural skill/agent tests (frontmatter, referenced-agent resolution, etc.).

### Layer 3 — rendering + Conductor wiring

- **Scorer renderer (client-facing):** extend `_build_portfolio` in
  `state/checkpoint_doc.py` to read `evals/OPP-NNN.evals.json` and add a **Confidence**
  column to the "Scored opportunities" table — per opportunity: "Stable" or
  "⚠ Needs review — composite 3.5–4.2; Build×3 / Partner×2". Honors the
  deliverable-readability rule. When a sidecar is absent (evals not run for an
  opportunity), the cell reads "—"; the column is omitted entirely if no opportunity
  has a sidecar. No PENDING, no error.
- **Tagger surfacing (assessor-facing, no client docx):** computed color is internal
  (owner docs strip it), so tagger confidence is **not** rendered into any client
  checkpoint. It lives in `evals/_index.md` and is surfaced by the Conductor at Phase 4
  (below), so the assessor re-examines shaky steps before opportunities are built.
- **Conductor wiring (`conducting-engagement`):** after Phase 4 tagging completes and
  before offering the `baseline` checkpoint, the Conductor auto-invokes
  `evaluating-consistency` for each in-scope process (tagger) and, if any step is
  unstable, surfaces those steps to the assessor (names PROC + step + the colors seen)
  as a non-blocking note. After Phase 6 scoring completes and before offering the
  `portfolio` checkpoint, it auto-invokes it for each scored opportunity (scorer) so the
  Confidence column is populated. Recorded (it ran / didn't), non-blocking.

## Storage decision

Eval results live in a **sidecar** `evals/` family, deliberately **outside** the
`model/*.json` engine input contract. `engine.run` and `state.integrity` are
untouched — confidence is not an input to `results.json` arithmetic; it is metadata
about *how trustworthy* a judgment is. This keeps the deterministic math contract and
the integrity gate clean.

## Data formats

`evals/PROC-NNN.evals.json`:
```json
{
  "target": "PROC-001", "phase": "phase4", "agent": "step-capability-tagger",
  "n_runs": 5, "unstable_step_count": 1,
  "steps": [
    {"step": 1, "colors": ["Green","Green","Green","Green","Green"],
     "color_unanimous": true, "jaccard_mean": 1.0, "unstable": false},
    {"step": 2, "colors": ["Green","Yellow","Green","Yellow","Green"],
     "color_unanimous": false, "jaccard_mean": 0.6, "unstable": true}
  ]
}
```

`evals/OPP-NNN.evals.json`:
```json
{
  "target": "OPP-001", "phase": "phase6", "agent": "opportunity-scorer",
  "n_runs": 5, "unstable": true,
  "dimensions": {
    "Value Potential": {"values": [4,4,4,5,4], "spread": 1, "stdev": 0.4},
    "Technical Feasibility": {"values": [3,3,2,4,3], "spread": 2, "stdev": 0.63}
  },
  "composite_spread": 0.33,
  "bbp": {"values": ["Build","Build","Partner","Build","Build"], "modal": "Build", "modal_agreement": 0.8}
}
```

`evals/_index.md`: one row per target — `| Target | Agent | Runs | Unstable | Status |`.

## Testing

All deterministic layers are unit-tested against **recorded** N-run fixtures under
`tests/fixtures/evals/`:
- `tagger-stable/` (5 runs, all colors agree) and `tagger-unstable/` (5 runs, one
  step's color flips) → assert per-step metrics + `unstable` flags + index.
- `scorer-stable/` and `scorer-unstable/` (composite/dim/bbp variation) → assert
  per-dimension spread/stdev, composite spread, bbp agreement, `unstable` flag.
- Renderer test: feed a sidecar → assert the Confidence column/section appears in the
  rendered checkpoint and that an absent sidecar omits it cleanly.
- Structural tests already cover the new skill/agent references.

The dispatch skill itself is LLM work and is not CI-tested. Internal-QA reuse comes
free: run `evaluating-consistency` once on the sample engagement and commit the
result as a regression fixture.

## Out of scope (this slice)

- `opportunity-typer` and `process-mapper` consistency (need cross-run alignment).
- Gold-standard **accuracy** evals (#193).
- Propagating confidence into the Phase 11 `deliverable.html` / executive summary
  (checkpoints are the user-facing surface for this slice).
- Hard-gating on instability (#195 is the gate-hardening lever).

## File map

| File | Responsibility |
|---|---|
| `state/evals.py` | Pure metrics engine + CLI: parse runs → metrics → sidecar + index |
| `skills/evaluating-consistency/SKILL.md` | Cross-cutting runner: N× dispatch → run engine → summarize |
| `state/checkpoint_doc.py` | Extend `_build_portfolio` to read scorer sidecar, add Confidence column |
| `skills/conducting-engagement/SKILL.md` | Auto-invoke evaluating-consistency at P4 (surface unstable steps to assessor) and P6 (populate portfolio Confidence) |
| `tests/test_evals.py` | Metrics + thresholds + index against recorded fixtures |
| `tests/fixtures/evals/...` | Recorded stable/unstable run sets for tagger + scorer |
| `tests/test_doc_rendering.py` | Confidence rendering assertions (extend existing) |
| `CHANGELOG.md` | `[Unreleased]` entry |
```
