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

**The `ai-inference` conservatism rule.** AI inference (extraction/classification/drafting from
messy input) is probabilistic — it normally needs per-instance human verification. So
`ai-inference` is treated as an enabler that **also contributes an implicit verification blocker
unless `accuracy-bounded` is present**. Concretely, the engine computes `has_blocker` as: *any
blocker attribute is present, OR `ai-inference` is present without `accuracy-bounded`.* Result:
`ai-inference` alone → Yellow (human verifies); `ai-inference + accuracy-bounded` → Green
(end-to-end, measured). This bakes the Augmentation-vs-Automation conservatism into the rule rather
than leaving it to the tagger, and it keeps the clean two-axis shape (Green/Yellow/Red as above).

### 2. The controlled vocabulary (10 attributes)

| Attribute | Meaning | Class |
|---|---|---|
| `structured-data` | works on structured/digital data (fields, records, APIs) | enabler |
| `rule-based` | deterministic logic — if/then, thresholds, lookups | enabler |
| `templated` | templated/parameterized generation (standard emails, forms) | enabler |
| `ai-inference` | extraction / classification / drafting from messy input (ML/LLM lever) | enabler (probabilistic — see rule) |
| `accuracy-bounded` | a measurable accuracy threshold / acceptance criterion governs the AI output | enabler (qualifier — valid only with `ai-inference`) |
| `human-judgment` | discretion / interpretation / tradeoff a human must make each instance | blocker |
| `relationship` | interpersonal — negotiation, trust, client management | blocker |
| `external-dependency` | blocked on a party outside the firm (client/vendor acts) | blocker |
| `physical` | requires a real-world / offline act | blocker |
| `regulatory-signoff` | a regulation/policy mandates a human be accountable | blocker |

The vocabulary is **fixed**. An attribute outside the set is a defect (preserves determinism). A
genuine gap is a methodology-evolution decision (extend the vocabulary), never an ad-hoc
per-engagement addition. `state/capability.py` is the single source of truth; skill docs
reference it. `accuracy-bounded` without `ai-inference` is a defect (it qualifies nothing).

### 3. Two-pass authoring + artifact format

Phase 4 becomes two passes with separate actors:

- **Pass 1 — Map** (`process-mapper`, slimmed): writes only the step *actions* — clean
  current-state, owner-confirmable. No attributes, no colors, no capability rationale.
- **Pass 2 — Capability** (new `step-capability-tagger`): runs **after the orchestrator has
  assembled and final-numbered the Steps** (not against the mapper's provisional staging numbering —
  the orchestrator renumbers during assembly, so Pass 2 must see the settled list). Assigns
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
- The old free-text per-step rationale and the hand-written `Chain scan` section are removed. The
  engine computes the consecutive-Green **chains** (step ranges); the *value* of a chain
  (effort-per-checkpoint) is no longer authored in Phase 4 — Phase 5 derives it from the process
  FTE baseline allocated across the eliminated steps (see §4).

### 4. Computation + consumers

**`state/capability.py` (new, stdlib)** owns:
- the vocabulary (enabler/blocker classification + the `ai-inference`/`accuracy-bounded` rule),
- `compute_color(attributes) -> "Green"|"Yellow"|"Red"` (two-axis rule, incl. the implicit
  ai-verification blocker),
- a parser for the `Step capability` table — built on the existing `checkpoint_doc.md_table()`
  (no new bespoke table parser),
- consecutive-Green **chain** computation (returns runs of step indices — *ranges only*, no value),
- validation: unknown attribute, `accuracy-bounded` without `ai-inference`, empty attributes,
  missing evidence, and Steps↔capability-table mismatch → flagged.

Pure functions, fully unit-testable. Placed in `state/` (not `engine/`): the engine doctrine binds
**financial arithmetic** (numbers read back from `results.json`); capability is categorical
classification of prose process files, which is exactly what `state/` is for. It touches no
`model/*.json`. Reuses `checkpoint_doc.md_table()` rather than adding a fourth PROC-file parser.

**Consumers (read computed values; never author them):**
- **Phase 5** — `identifying-opportunities` skill + `opportunity-typer` agent read computed colors
  and computed chain ranges. The chain's **value** (effort eliminated per checkpoint) is derived
  here from the process FTE baseline allocated across the chain's eliminated steps, cited like any
  other value input — replacing the per-checkpoint effort that the old chain-scan prose carried.
- **Phase 6** — `scoring-opportunities` skill + `opportunity-scorer` agent also consume the chain
  scan today (Value Potential, Execution Horizon); they switch to the computed chains + the
  Phase-5-derived value. (This consumer was missed in the first draft.)
- **Renderer** — the owner process-validation doc already renders clean steps; it must keep the
  `Step capability` table out (assessor-only), consistent with the existing owner-vs-analysis split.

### 5. Validation / gate

The following are flagged at missing-baseline severity (the process does not advance to Phase 5
until resolved):
- an unknown attribute (outside the fixed vocabulary),
- `accuracy-bounded` present without `ai-inference`,
- a capability row with no evidence,
- a step (under **Steps**) with no capability row, or zero attributes,
- a **Steps ↔ Step-capability mismatch** — the validator asserts a strict 1:1: every step index has
  exactly one row, no gaps, no extra rows.

## Components changed

| # | File | Change |
|---|---|---|
| 1 | `state/capability.py` (new) + tests | vocabulary, `compute_color`, table parser, chain computation, validation |
| 2 | `skills/discovering-processes/SKILL.md` | two-pass Phase 4; drop per-step colors + hand chain scan; document `Step capability` table + vocabulary; chains computed |
| 3 | `agents/process-mapper.md` | slim to steps-only (remove capability assignment) |
| 4 | `agents/step-capability-tagger.md` (new) | assign attributes + cite evidence per step |
| 5 | `skills/identifying-opportunities/SKILL.md`, `agents/opportunity-typer.md` | consume computed colors/chains; derive chain value from FTE baseline |
| 6 | `skills/scoring-opportunities/SKILL.md`, `agents/opportunity-scorer.md` | switch chain-scan inputs to computed chains + Phase-5-derived value |
| 7 | `skills/using-methodology/SKILL.md` | reference the attribute vocabulary (taxonomy unchanged) |
| 8 | `state/process_review.py` / `state/checkpoint_doc.py` | keep `Step capability` table out of the owner doc |
| 9 | tests + a fresh sample `PROC` in the new format | unit + integration + render coverage |

When editing #2 and #3, **inventory every color/chain mention** (the surface is larger than one
block): `discovering-processes` checklist + "what stays in main context" + rationalization table;
`process-mapper` behavior step + field schema + refusal rules + output template. A half-stripped
mapper that still says "mark Green/Yellow/Red" silently bypasses the new pass. Also check
`skills/generating-sample-intake` — its intake notes carry "AI capability and chain-scan notes"
in the old G/Y/R form; if a fresh sample run is to exercise the new flow, that intake format must
feed attributes/evidence, not colors.

## Testing

- **Unit (`state/capability.py`):** every enabler/blocker combination → expected color
  (Green/Yellow/Red); empty/unknown attributes → defect; table parser extracts (step, attributes,
  evidence); chain computation finds consecutive-Green runs; missing-evidence detection.
- **Integration:** a new-format `PROC-NNN.md` → correct per-step colors + chains; Phase 5 typing
  can read them.
- **Render:** owner process-validation doc shows clean step actions and does **not** contain the
  `Step capability` table.

## Worked example — PROC-001 (validates the vocabulary reproduces the old colors)

| Step | Action (abbrev) | Attributes | Computed | Old hand-assigned |
|---|---|---|---|---|
| 1 | receives Zapier/Slack notification | structured-data, rule-based | 🟢 | 🟢 |
| 2 | re-keys HubSpot fields into Teamwork | structured-data, rule-based | 🟢 | 🟢 |
| 3 | builds task list from Notion checklist | structured-data, rule-based, templated | 🟢 | 🟢 |
| 4 | sends templated kickoff email | templated, structured-data | 🟢 | 🟢 |
| 5 | waits for client to provide materials | external-dependency | 🔴 | 🔴 |
| 6 | sends follow-up reminders (N days elapsed) | rule-based, templated | 🟢 | 🟢 |
| 7 | judges whether assets sufficient to proceed | structured-data, human-judgment | 🟡 | 🟡 |
| 8 | sends kickoff meeting invite | rule-based, structured-data | 🟢 | 🟢 |
| 9 | updates milestones, assigns tasks | rule-based, structured-data | 🟢 | 🟢 |

Computed result: Green ×7, Red ×1, Yellow ×1 — **identical to the old hand-assigned colors**. No
step in PROC-001 relies on `ai-inference`, and none lands attribute-less, so the vocabulary covers
all nine cleanly. (The `ai-inference`/`accuracy-bounded` conservatism is exercised by other
processes with messy-input steps, and by unit tests.)

## Implementation order (for the plan)

1. `state/capability.py` engine + unit tests (no consumers yet) — vocabulary, color rule, table
   parse via `md_table`, chain ranges, validation.
2. Phase 4 authoring: format + `discovering-processes` two-pass + `process-mapper` slim +
   `step-capability-tagger` agent (inventory every color/chain mention).
3. Phase 5 + Phase 6 consumption: `identifying-opportunities`/`opportunity-typer` (incl.
   FTE-derived chain value) and `scoring-opportunities`/`opportunity-scorer`.
4. Renderer guard + fresh sample + integration/render tests.

## Risks / trade-offs

- **Residual attribution judgment.** Assigning attributes is still a judgment; the design
  constrains it (fixed vocabulary), separates it (distinct pass/actor), grounds it (evidence
  required), and removes outcome-picking (computed color). Judgment is minimized and auditable,
  not eliminated — which is the honest ceiling.
- **Lost per-step prose nuance.** The free-text "what makes it hard" collapses into attributes +
  evidence. Deliberate: facts over editorializable prose.
- **Vocabulary completeness.** A fixed 10-attribute set may not cover every step cleanly; gaps are
  resolved by evolving the vocabulary (a deliberate methodology change), not ad-hoc.
- **Residual judgment hot spots (named).** The two genuine boundaries where attribute selection can
  still carry bias are `ai-inference` vs `rule-based` and `human-judgment` vs `rule-based`. The
  `step-capability-tagger` agent must carry decision guidance + worked examples for exactly these,
  with the evidence-citation rule as the backstop.
