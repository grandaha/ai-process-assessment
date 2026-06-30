# Attribute-Based Deterministic AI-Capability Tagging — Design

**Issue:** #186
**Status:** Approved design (pending spec review) → implementation plan

## Problem

In Phase 4, each process step is tagged Green / Yellow / Red for AI capability, and the
rationale is written inline with the step. Because the verdict is authored *while* the step is
described — by the same actor in the same pass — the judgment anchors the description: a step the
mapper senses is automatable gets described as cleaner/more structured than it is, and vice
versa. The factual record bends toward the verdict. This is the same hazard the methodology
already guards against in Phase 5 with *hypothesis-before-value*.

Two corroborating signals that the colors are a separate lens from the current-state record: the
chain scan is already a separate post-assembly pass, and the owner-facing process-validation doc
already *strips* the colors out (they're assessor analysis, not owner-confirmable current state).

## Goal

Replace human color-picking with **factual step attributes → deterministic, engine-computed
color**, authored in a **separate, evidence-cited pass** so the description and the verdict can
never co-bias. Make capability tagging consistent, auditable, and reproducible.

Non-goals: changing the opportunity *type* taxonomy (RPA / AI Augmentation / …); changing the
financial engine; back-compatibility with the old prose-color format (clean forward switch).

## Design

### 1. The rule model (two-axis enabler/blocker)

Every attribute in the controlled vocabulary is pre-classified as an **enabler** (there is an
automatable component) or a **blocker** (there is a human-only requirement). The color is
computed:

- **Green** = has an enabler **and** no blocker
- **Yellow** = has an enabler **and** a blocker (AI does part; a human owns part)
- **Red** = has a blocker **and** no enabler (nothing for AI to do)
- A step with neither an enabler nor a blocker (no/only-unknown attributes) is a **defect**, not a
  silently-assigned color.

`human-judgment` is the Green↔Yellow discriminator for AI work: AI executing end-to-end (no
per-instance human decision) is Green; AI assisting where a human decides each instance is Yellow.
This maps onto the methodology's AI Automation vs AI Augmentation split.

### 2. The controlled vocabulary (9 attributes)

| Attribute | Meaning | Class |
|---|---|---|
| `structured-data` | works on structured/digital data (fields, records, APIs) | enabler |
| `rule-based` | deterministic logic — if/then, thresholds, lookups | enabler |
| `templated` | templated/parameterized generation (standard emails, forms) | enabler |
| `ai-inference` | extraction / classification / drafting from messy input (ML/LLM lever) | enabler |
| `human-judgment` | discretion / interpretation / tradeoff a human must make each instance | blocker |
| `relationship` | interpersonal — negotiation, trust, client management | blocker |
| `external-dependency` | blocked on a party outside the firm (client/vendor acts) | blocker |
| `physical` | requires a real-world / offline act | blocker |
| `regulatory-signoff` | a regulation/policy mandates a human be accountable | blocker |

The vocabulary is **fixed**. An attribute outside the set is a defect (preserves determinism). A
genuine gap is a methodology-evolution decision (extend the vocabulary), never an ad-hoc
per-engagement addition. `state/capability.py` is the single source of truth; skill docs
reference it.

### 3. Two-pass authoring + artifact format

Phase 4 becomes two passes with separate actors:

- **Pass 1 — Map** (`process-mapper`, slimmed): writes only the step *actions* — clean
  current-state, owner-confirmable. No attributes, no colors, no capability rationale.
- **Pass 2 — Capability** (new `step-capability-tagger`): runs after the steps are fixed; assigns
  attributes per step from the vocabulary, **each citing evidence**; never edits step text.

Both live in separate sections of `processes/PROC-NNN.md`:

```
**Steps:**
1. PM re-keys client details into Teamwork
2. PM waits for the client to provide materials
3. PM reviews assets and decides whether to proceed

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | HubSpot + Teamwork both API-available (tech-inventory) |
| 2 | external-dependency | operator: "we just wait on the client" |
| 3 | structured-data, human-judgment | operator: "I decide if there's enough to start" |
```

- No color token appears in the source; the engine derives it (1→Green, 2→Red, 3→Yellow).
- Evidence is **required** per row — an attribute with no basis is a defect (same rule as "every
  baseline traces to a source"). This makes attribution falsifiable, not intuitive.
- Pass 2 is a per-process subagent dispatched in parallel after Pass 1 (same fan-out as the mapper).
- The old free-text per-step rationale and the hand-written `Chain scan` section are removed.

### 4. Computation + consumers

**`state/capability.py` (new, stdlib)** owns:
- the vocabulary (enabler/blocker classification),
- `compute_color(attributes) -> "Green"|"Yellow"|"Red"` (two-axis rule),
- a parser for the `Step capability` table from a `PROC-NNN.md`,
- consecutive-Green **chain** computation (returns runs of step indices),
- validation: unknown attribute, empty attributes, missing evidence → flagged.

Pure functions, fully unit-testable. Placed in `state/` (not `engine/`) because it parses the
prose process files, which the `state/` layer already does (checkpoint rendering); the financial
`engine/` remains untouched.

**Consumers (read computed values; never author them):**
- **Phase 5** — `identifying-opportunities` skill + `opportunity-typer` agent read computed colors
  and computed chains instead of prose colors and the hand-written chain-scan section. The *value
  judgment* about which chains matter stays human (Phase 5).
- **Renderer** — the owner process-validation doc already renders clean steps; it must keep the
  `Step capability` table out (assessor-only), consistent with the existing owner-vs-analysis split.

### 5. Validation / gate

A `Step capability` table with an unknown attribute, a row with no evidence, or a step (under
Steps) with no capability row / zero attributes is flagged at missing-baseline severity (the
process does not advance to Phase 5 until resolved).

## Components changed

| # | File | Change |
|---|---|---|
| 1 | `state/capability.py` (new) + tests | vocabulary, `compute_color`, table parser, chain computation, validation |
| 2 | `skills/discovering-processes/SKILL.md` | two-pass Phase 4; drop per-step colors + hand chain scan; document `Step capability` table + vocabulary; chains computed |
| 3 | `agents/process-mapper.md` | slim to steps-only (remove capability assignment) |
| 4 | `agents/step-capability-tagger.md` (new) | assign attributes + cite evidence per step |
| 5 | `skills/identifying-opportunities/SKILL.md`, `agents/opportunity-typer.md` | consume computed colors/chains |
| 6 | `skills/using-methodology/SKILL.md` | reference the attribute vocabulary (taxonomy unchanged) |
| 7 | `state/process_review.py` / `state/checkpoint_doc.py` | keep `Step capability` table out of the owner doc |
| 8 | tests + a fresh sample `PROC` in the new format | unit + integration + render coverage |

## Testing

- **Unit (`state/capability.py`):** every enabler/blocker combination → expected color
  (Green/Yellow/Red); empty/unknown attributes → defect; table parser extracts (step, attributes,
  evidence); chain computation finds consecutive-Green runs; missing-evidence detection.
- **Integration:** a new-format `PROC-NNN.md` → correct per-step colors + chains; Phase 5 typing
  can read them.
- **Render:** owner process-validation doc shows clean step actions and does **not** contain the
  `Step capability` table.

## Implementation order (for the plan)

1. `state/capability.py` engine + unit tests (no consumers yet).
2. Phase 4 authoring: format + `discovering-processes` two-pass + `process-mapper` slim +
   `step-capability-tagger` agent.
3. Phase 5 consumption: `identifying-opportunities` + `opportunity-typer` read computed values.
4. Renderer guard + fresh sample + integration/render tests.

## Risks / trade-offs

- **Residual attribution judgment.** Assigning attributes is still a judgment; the design
  constrains it (fixed vocabulary), separates it (distinct pass/actor), grounds it (evidence
  required), and removes outcome-picking (computed color). Judgment is minimized and auditable,
  not eliminated — which is the honest ceiling.
- **Lost per-step prose nuance.** The free-text "what makes it hard" collapses into attributes +
  evidence. Deliberate: facts over editorializable prose.
- **Vocabulary completeness.** A fixed 9-attribute set may not cover every step cleanly; gaps are
  resolved by evolving the vocabulary (a deliberate methodology change), not ad-hoc.
