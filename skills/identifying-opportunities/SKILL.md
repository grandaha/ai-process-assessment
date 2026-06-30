---
name: ai-process-assessment:identifying-opportunities
description: Phase 5 — applies opportunity type taxonomy to every mapped process. Produces typed opportunity log (OPP-NNN) with hypothesis, value range, feasibility/data/GRC flags. Saves per-OPP files to opportunities/ folder.
---

# Phase 5: Identifying Opportunities

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `processes/_index.md` and `tech-inventory.md` — confirm each exists. Confirm no `Unavailable` entries in `processes/_index.md` before proceeding (each process without baselines must have been remediated or explicitly scoped out).

**Session Start — resolve `engine_root`:** read `engine_root` (the absolute plugin root)
from this engagement's `.conductor.md` (`read_conductor`). Every engine command below is
`python3 <engine_root>/engine/run.py …`.

Gate condition: `processes/_index.md` must be present before proceeding.

## Role in the system

This phase converts mapped processes into a typed opportunity log. Type — RPA / AI Augmentation / Chain Automation / AI Automation / Agentic / Data & Analytics — is assigned BEFORE scoring because the rubric weights vary by type. A misclassified opportunity gets the wrong scoring lens and the wrong sourcing recommendation.

## Gate condition

`processes/_index.md` must exist (all per-process files written by Phase 4). This skill creates the `opportunities/` folder with per-OPP files and `opportunities/_index.md`.

## OPP-NNN Entry Structure

Every opportunity is logged with a stable identifier `OPP-NNN` and the following fields:

| Field | Content |
|---|---|
| Process reference | ID from `processes/_index.md` |
| Opportunity type | RPA / AI Augmentation / Chain Automation / AI Automation / Agentic / Data & Analytics |
| Hypothesis | One-sentence statement: "We believe that [intervention] will [effect] because [mechanism]." |
| Value hypothesis | Estimated value range, citing specific baseline(s) from `processes/PROC-NNN.md` |
| Chain formation | If two or more consecutive AI-capable steps are involved: describe the chain (step range, checkpoints eliminated). Current human effort at each eliminated checkpoint is **derived from the process FTE baseline** (`model/baselines.json` `fte`) allocated across the chain's eliminated steps — cite `model/baselines.json` as the source. If this is a single-step opportunity, write "Single step — no chain." |
| Feasibility flag | Green / Yellow / Red — based on `tech-inventory.md` |
| Data readiness flag | Green / Yellow / Red — based on data asset catalog |
| GRC flag | Green / Yellow / Red — regulatory, model risk, auditability, failure consequence |
| Structural response | `addressing-root` / `optimizing-around` / `not-applicable` — set against the process's challenge hypothesis from `processes/PROC-NNN.md`. Annotates only; never blocks. |

**Categorical rule: Hypothesis statement must be written before value is estimated. This prevents reverse-engineering the hypothesis from a desired outcome.**

## Value range (engine-computed)

The value hypothesis is written *before* the number (hypothesis-before-value discipline is unchanged). The numeric range itself is **not** multiplied in prose. Record `{"opp_id": "...", "improvement_low": x, "improvement_high": y, "process_id": "PROC-NN", "volume_fraction": f, "rate": r}` to the engagement's `model/value.json`. Do **not** restate a `volume`: the engine resolves it as `baselines.<process_id>.volume × volume_fraction`, so volume is never hand-copied. Set `volume_fraction` to `1.0` when the opportunity addresses the whole process; use a smaller fraction (with a one-line rationale in `opportunities/OPP-NNN.md`) when it addresses only a slice. `process_id` must name a process that exists in `model/baselines.json`, and `rate` must trace to a sourced figure. Then run `python3 <engine_root>/engine/run.py <engagement-folder>/` and cite the resulting `results.json` `value.<OPP-ID>` range in `opportunities/OPP-NNN.md`.

**Unit convention — `rate` carries the period (the engine does not annualize).** The engine computes `value = improvement × (baselines.volume × volume_fraction) × rate` and the Wave-1 roll-up is reported as *annual* value — but `baselines.volume` is the **raw measured volume at whatever cadence the baseline was sourced** (e.g. "720 reports/month"), and there is **no annualization step in the engine**. So `rate` must carry both the period and the per-unit dollar basis needed to make the product land in annual dollars. Pick the basis that matches the value lever and **state its derivation in one line in `opportunities/OPP-NNN.md`** (the derivation is documented in prose; the multiplication still happens only in the engine):

- *FTE-effort lever* (most operational processes): set `rate = (FTE × fully-loaded annual $/FTE) ÷ baseline.volume`, so `improvement` is the fraction of that effort eliminated. Worked example: PROC with 5.5 FTE, $130K loaded, baseline.volume 720/mo → `rate = 5.5 × 130000 ÷ 720 ≈ 993.06`; `improvement 0.50–0.65` yields an annual value of `0.50–0.65 × 720 × 993.06`.
- *Per-transaction lever*: set `rate = annual $ released per unit of the baseline volume` directly.

If `baseline.volume` is monthly and you forget the period, the result is ~12× too small — a silent unit bug the deliverable-gate will not catch (the arithmetic is internally consistent, just wrong-scaled). Always sanity-check the resulting `results.json` `value.<OPP-ID>` range against the process's FTE × loaded-cost ceiling.

## Subagent Dispatch

**Invocation modes.** This skill runs in one of two modes:

- **Single-process (conductor-driven fan-out).** When the conductor invokes this skill
  scoped to a single `PROC-NNN`, act as the typer for that one process: read only its
  `processes/PROC-NNN.md` (and the relevant `tech-inventory.md` sections), write only that
  process's opportunities to `<engagement-folder>/_staging/phase5/proc-<process-id>.md` with
  provisional `## TEMP-` ids, return the one-line summary, and **do not assemble** — the
  conductor merges every process's staging into the canonical `opportunities/`.
- **Whole-portfolio (direct invocation or a single-process engagement).** Dispatch the
  per-process batch and assemble, exactly as described below.

Per-process opportunity identification is offloaded to subagents. Each mapped process is independent for typing purposes, so they parallelize cleanly.

- **When:** After `processes/_index.md` is confirmed present, dispatch one `opportunity-typer` subagent per mapped process in a single parallel tool-call batch.
- **Pass to each subagent:** engagement folder path, process ID (PROC-NNN), the absolute path to `processes/PROC-NNN.md` for that process, and staging file path: `<engagement-folder>/_staging/phase5/proc-<process-id>.md`. The agent reads its own `processes/PROC-NNN.md` (which contains both process map data and baseline metrics) and the relevant `tech-inventory.md` sections. Do not pass file content to the subagent.
- **Return:** One-line summary only: process ID, opportunity count, GRC flag counts (Green/Yellow/Red). Full OPP content is written to the staging file by the agent — it does NOT flow back to main context.

**Assembly (portable):** After all agents complete, assemble with one call into the tested `state.assembly` layer. `<engine_root>` is the absolute plugin root resolved at Session Start.

```bash
PYTHONPATH="<engine_root>" python3 -c "
from state.assembly import collect_staged, renumber_sequential, index_from_headers, cleanup
staged = collect_staged('<name>/_staging/phase5')
ids = renumber_sequential(staged, '<name>/opportunities', 'OPP')
index_from_headers(
    ['<name>/opportunities/%s.md' % i for i in ids],
    '<name>/opportunities/_index.md',
    [('OPP-ID', 'id'), ('Process', 'process'), ('Type', 'type'),
     ('Feasibility', 'feasibility'), ('Data Readiness', 'data'),
     ('GRC', 'grc'), ('Structural', 'struct')],
)
cleanup('<name>/_staging/phase5')
"
```

`renumber_sequential` splits each staged `proc-*.md` at its `## TEMP-<token>` headings, assigns global `OPP-NNN` ids in staged-file order (which equals process order — `proc-001`, `proc-002`, … sort to `PROC-001`, `PROC-002`, …), and remaps each opportunity's provisional token to its final id throughout its block. `index_from_headers` rebuilds `opportunities/_index.md` from the `<!-- index: -->` headers — reading each attribute key (`id=`, `process=`, `type=`, `feasibility=`, `data=`, `grc=`, `struct=`) in order and emitting a markdown table row. The resulting index has columns: `| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |`. Output is byte-identical regardless of subagent completion order.
- **What stays in main context:** The one-line summaries from each agent (process ID, counts, GRC flags), the OPP headings from the grep verification, the GRC-flag branch decision, and cross-process consistency review of headings only.

## Phase checklist

- [ ] Confirm `processes/_index.md` exists and all entries have `Baseline: Ready`
- [ ] For each mapped process, walk the opportunity type taxonomy and assign the correct type
- [ ] Write the hypothesis statement BEFORE estimating value
- [ ] Source value range against named baseline(s) from `processes/PROC-NNN.md`
- [ ] Set feasibility flag against `tech-inventory.md`
- [ ] Set data readiness flag against data asset catalog
- [ ] Set GRC flag based on regulatory exposure, model risk, auditability, failure consequence
- [ ] Set Structural response (addressing-root / optimizing-around / not-applicable) against the process's challenge hypothesis
- [ ] Assign stable OPP-NNN identifier
- [ ] Save each opportunity to `<name>/opportunities/OPP-NNN.md`; generate `opportunities/_index.md` master index
- [ ] If any opportunity has a non-Green GRC flag → branch to `ai-process-assessment:governance-risk-gate`
- [ ] Otherwise → Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:scoring-opportunities`

## Workflow

1. Load `processes/_index.md`. If missing, return to Phase 4. For each PROC-NNN entry, confirm `processes/PROC-NNN.md` exists.
2. For each process, read the **computed** per-step colors and consecutive-Green chains from `state/capability.py` (`step_colors`, `compute_chains`) — these are derived, not authored. Identify chain formation opportunities first — runs of consecutive Green steps that could eliminate one or more human verification checkpoints. These are Chain Automation type candidates. Then walk the six-row taxonomy for remaining steps. Pick the type that fits the work, not the brand the client wants on the slide.
3. Write the hypothesis. The format is forcing: it requires naming the intervention, the effect, and the mechanism.
4. Estimate value. Cite the baseline by name. If no baseline supports the claim, the process is not opportunity-eligible — return to Phase 4 for baseline capture.
5. Set the three flags. Be honest about Yellow and Red — they're inputs to scoring and gating, not failures.
6. If any opportunity carries a non-Green GRC flag, branch to the GRC gate before scoring.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Type doesn't matter — the scoring will sort it out." | Type determines which scoring rubric applies and which sourcing path is viable. Misclassification at this step is uncorrectable downstream. |
| "The client wants AI — call it AI Augmentation." | Type is determined by the work, not the brand. Mislabeling RPA as AI sets up cost overruns and reliability failures. |
| "We can estimate value first and write the hypothesis to match." | This is the most common failure mode. Hypothesis-before-value is a hard rule because reversing it produces motivated reasoning. |
| "GRC flags can be set later — let's not slow things down." | Yellow/Red flags route to a separate gate. Setting them late means flagged opportunities sit in scoring with bad inputs. |
| "Feasibility is fine — they have AWS." | Feasibility is per-opportunity. Cloud presence is not the same as identity, observability, MLOps, or the specific integration you need. |
| "We evaluated each step on its own merits and assigned the best type." | Per-step evaluation misses chain opportunities. A step that looks unattractive in isolation may be the right assignment for AI because it sits between two AI-capable steps — eliminating an extra human checkpoint can outweigh per-step comparative disadvantage. Always read the computed chains from `state/capability.py` (`compute_chains`) before typing individual steps. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `opportunities/OPP-NNN.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: opportunities identified (count), GRC flag summary (Green/Yellow/Red counts), next routing decision.

**Session boundary:** After the user approves `opportunities/_index.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke either `ai-process-assessment:governance-risk-gate` (if any non-Green GRC flags exist) or `ai-process-assessment:scoring-opportunities` (if all Green). Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:governance-risk-gate` (if any opportunity has a non-Green GRC flag)
→ `ai-process-assessment:scoring-opportunities` (otherwise, or after GRC clearance)
