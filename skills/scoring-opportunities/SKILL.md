---
name: ai-process-assessment:scoring-opportunities
description: Phase 6 — applies multi-dimensional scoring rubric (6 dimensions, 5-point scale, evidence-gated) plus build/buy/partner classification. Dispatches opportunity-reviewer subagent before save. Saves scores/OPP-NNN.md per opportunity + scores/_index.md.
---

# Phase 6: Scoring Opportunities

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `opportunities/_index.md` and confirm it exists.
3. Check `grc/_index.md` — confirm any flagged opportunities have status `Cleared` or `Cleared-with-Conditions` (no `Blocked` entries). Note: the status column uses the hyphenated extraction form. If `grc/_index.md` does not exist, no opportunities were GRC-flagged and scoring can proceed.

Gate condition: `opportunities/_index.md` present; any non-Green GRC flags resolved in `grc/_index.md` (no `Blocked` status).

## Role in the system

Scoring converts a typed opportunity log into a ranked portfolio. The rubric is multi-dimensional on purpose — a single composite score hides the trade-offs that determine sequencing. Every dimension must be sourced; intuition is not a source.

## Gate condition

`opportunities/_index.md` must exist. The GRC gate must be cleared for any opportunity with a non-Green GRC flag. This skill creates the `scores/` folder with per-OPP scored entries and `scores/_index.md`.

## Scoring Rubric

Score each opportunity across all six dimensions on a 1–5 scale. Cite the source for each score. Use the scale anchors below — do not interpret the scale without them.

| Dimension | What it measures | Required source |
|---|---|---|
| Value Potential | Magnitude of value if realized. For Chain Automation type: cite checkpoints eliminated × effort per checkpoint × volume. Do not aggregate step-level savings linearly — chain value is non-linear. | `processes/PROC-NNN.md` Baselines section |
| Technical Feasibility | Buildability given current systems and skills | `tech-inventory.md` |
| Data Readiness | Whether data needed exists, is accessible, and is fit for purpose | `tech-inventory.md` (data asset catalog) |
| Org Change Readiness | Whether the affected team can absorb the change | `context.md` |
| Strategic Alignment | Fit with stated strategic priorities | `context.md` |
| Time to Value | Speed from start to first measurable outcome | `tech-inventory.md` + `processes/PROC-NNN.md` |
| Execution Horizon | Whether value is achievable within existing job boundaries (Short-run) or requires redesigning how tasks are bundled across workers (Long-run). Short-run is faster and smaller. Long-run is larger but requires org design work as a dependency. **Long-run is NOT a long timeline or complex prerequisites — it specifically means the opportunity cannot deliver value until someone's job or role boundary is redesigned. A long GRC clearance track or missing integration is a dependency (Constraint 1), not a Long-run classification.** | `processes/PROC-NNN.md` chain scan + `context.md` |

### Scale Anchors (apply to all 6 dimensions)

**Value Potential**
- 1 — No supporting baseline; value is speculative or negligible
- 2 — Directional claim only; no named metric supports magnitude
- 3 — Moderate value; partially baselined; recovers meaningful cost or cycle time
- 4 — High value; strong baseline; recovers significant cost or time (>$100K/yr or >1 FTE or meaningful cycle-time compression across high volume)
- 5 — Very high value; strong baseline; major cost or strategic impact (>$500K/yr, or directly addresses the largest identified cost driver in the engagement)

**Enabler vs. mechanism:** An opportunity that surfaces information for human action (a dashboard, alert, or report) should be scored on its own contribution — the fraction of the downstream value it enables, discounted for the human decision step that remains. Do not assign the full downstream value to an enabler. A mechanism that directly executes the improvement scores higher than an enabler that makes the improvement possible.

**Technical Feasibility**
- 1 — Not feasible given current stack; requires capabilities that do not exist
- 2 — Major barriers; significant new capability required beyond the current stack
- 3 — Feasible but requires new integrations (8–12 week security review) or substantial new configuration
- 4 — Mostly in existing stack; Workday config changes only (6–10 week lead time); no new integration required
- 5 — Uses existing licensed features; minimal configuration; no new integration; quickest deployment path

**Data Readiness**
- 1 — Critical gaps; data does not exist, is inaccessible, or is fundamentally unfit for purpose
- 2 — Poor quality or major gaps in key datasets; significant remediation required before deployment
- 3 — Moderate quality; data exists with known gaps; usable with documented limitations
- 4 — Good quality; minor gaps that do not block deployment
- 5 — Good quality, real-time, complete; no relevant gaps for this use case

**Org Change Readiness**
- 1 — Active resistance; change will fail without a major multi-year intervention
- 2 — Meaningful resistance; targeted change management program required; key skeptical stakeholders with real veto risk
- 3 — Mixed; some champions, some skeptics; standard change management needed; no active blockers
- 4 — Favorable; key stakeholders aligned; limited adoption friction expected
- 5 — High readiness; champion-driven; team actively wants the change

**Strategic Alignment**
- 1 — No alignment with any stated strategic priority
- 2 — Tangential or indirect alignment to one priority
- 3 — Directly supports one stated strategic priority
- 4 — Directly supports two stated strategic priorities
- 5 — Core to three or more stated priorities, including CEO- or Board-level initiatives

**Time to Value**
- 1 — 12+ months to first measurable outcome; major prerequisites on the critical path
- 2 — 9–12 months; significant dependencies or prerequisites
- 3 — 6–9 months including IT lead time and any prerequisite work
- 4 — 3–6 months; uses existing stack with known lead times
- 5 — Under 3 months or measurable within one quarter; minimal dependencies

**Categorical rule: Each dimension score must cite a source (`processes/PROC-NNN.md`, `tech-inventory.md`, or `context.md`). No dimension may be scored from intuition.**

**Execution Horizon is a required field on every scored opportunity entry: Short-run / Long-run with one-sentence rationale. This field is consumed by Phase 7 sequencing.**

## Composite score (computed post-assembly)

The composite is **not** computed by the scorer agent. After all agents complete and files are assembled, the orchestrator runs a Python script that:
1. Extracts dimension integers from the markdown tables in each `scores/OPP-NNN.md`
2. Computes `round(sum(dimensions) / 6, 2)` — identical to `engine.compute.score_composite`
3. Stamps the composite back into the file (replacing `PENDING`) in both the index comment and the body line
4. Writes `model/scores.json` for consumption by the full engine run in Phase 9

The `_index.md` is always generated last — after stamping — so it never contains `PENDING` or agent-estimated values.

Note: `python -m engine.run` is **not** called in Phase 6. The full engine run (which produces `model/results.json` and `financial-model.xlsx`) happens in Phase 9 once value, cost, and initiative inputs are available.

## Build/Buy/Partner Classification

Required for every scored opportunity. Inputs:

- **Build capacity** — internal skills, available bandwidth
- **Vendor maturity** — does a credible product exist for this use case
- **Strategic differentiation** — does owning this capability differentiate the business
- **TCO horizon** — total cost of ownership over 3-year window for each path

Output one of: **Build / Buy / Partner / Hybrid**, with rationale citing the four inputs.

**Classification guidance:**
- **Buy** — org procures a vendor product and deploys/configures it internally or with minimal vendor professional services
- **Partner** — vendor product exists, but significant configuration or implementation requires a systems integrator as the delivery mechanism; use when the org lacks capacity to implement even a commercial solution (e.g., small IT team, large platform configuration scope)
- **Hybrid** — two paths share meaningful weight; name both components

Calibration: uniform Buy across all opportunities in an engagement with a small IT team is a signal to reconsider. If an SI would realistically be the delivery vehicle, that is Partner.

## Subagent Dispatch

This phase already runs two subagents. This section names the pattern so it reads consistently with the other phases — the operational detail lives in the Phase checklist and Workflow below, which are authoritative.

- **Scorer dispatch (`opportunity-scorer`):** One subagent per opportunity, dispatched in a single parallel tool-call batch. Each receives: engagement folder path, OPP-ID, the path to `processes/PROC-NNN.md` for that opportunity's process, and staging file path: `<engagement-folder>/_staging/phase6/OPP-NNN.md`. The agent reads its own OPP entry from `opportunities/OPP-NNN.md`, its process file from `processes/PROC-NNN.md` (which contains both process context and baseline metrics), and the relevant sections of `tech-inventory.md` and `context.md`. Do not pass file content to the subagent. No cross-OPP context is shared. Each scorer writes its full entry to the staging file and returns only a one-line summary (composite score and B/B/P classification).
- **Reviewer dispatch (`opportunity-reviewer`):** One subagent over the fully assembled `scores/` folder draft, for independent cross-OPP calibration and consistency review. Pass to the reviewer: engagement folder path. The reviewer reads the `scores/` folder itself. Do not pass document content. Return: The reviewer appends findings to `<engagement-folder>/evidence-log.md` directly. Returns one-line summary to main context: "N Critical, N Important, N Minor findings." The orchestrator does NOT receive full review content.
- **Assembly:** After all scorer agents complete, run the following sequence in order:

  **Step 1 — Move staged files:**
  ```bash
  mkdir -p <name>/scores
  mv <name>/_staging/phase6/OPP-*.md <name>/scores/
  ```

  **Step 2 — Compute composites, stamp files, write `model/scores.json`:**
  ```bash
  python3 -c "
  import json, re
  from pathlib import Path
  eng = Path('<name>')
  eng.joinpath('model').mkdir(exist_ok=True)
  entries = []
  for f in sorted(eng.joinpath('scores').glob('OPP-*.md')):
      text = f.read_text()
      dims = [int(m) for m in re.findall(r'\| [^\|]+ \| (\d)/5 \|', text)]
      if len(dims) != 6:
          print(f'WARNING: {f.name} has {len(dims)} dimension rows, expected 6 — skipped')
          continue
      composite = round(sum(dims) / 6, 2)
      text = re.sub(r'composite=PENDING', f'composite={composite}', text, count=1)
      text = text.replace('**Composite:** PENDING (engine-computed)', f'**Composite:** {composite} / 5')
      f.write_text(text)
      entries.append({'opp_id': f.stem, 'dimensions': dims})
      print(f'Stamped {f.stem}: {composite}')
  eng.joinpath('model/scores.json').write_text(json.dumps(entries, indent=2))
  print(f'Wrote {len(entries)} entries to model/scores.json')
  "
  ```

  **Step 3 — Generate `_index.md` from stamped files:**
  ```bash
  echo "| OPP-ID | Composite | Horizon | B/B/P |" > <name>/scores/_index.md
  echo "|--------|-----------|---------|-------|" >> <name>/scores/_index.md
  for f in <name>/scores/OPP-*.md; do
    header=$(grep "^<!-- index:" "$f" | head -1)
    id=$(echo "$header" | grep -o 'id=[^ >]*' | cut -d= -f2)
    comp=$(echo "$header" | grep -o 'composite=[^ >]*' | cut -d= -f2)
    horiz=$(echo "$header" | grep -o 'horizon=[^ >]*' | cut -d= -f2)
    bbp=$(echo "$header" | grep -o 'bbp=[^ >]*' | cut -d= -f2)
    echo "| $id | $comp | $horiz | $bbp |" >> <name>/scores/_index.md
  done
  ```

  Verify with: `ls <name>/scores/OPP-*.md | wc -l`
  Confirm no PENDING values remain: `grep -l PENDING <name>/scores/OPP-*.md` (expect no output)

  Cleanup (non-fatal — sandbox may restrict deletion of empty directories):
  ```bash
  rm -rf <name>/_staging/phase6 || echo "Cleanup skipped (sandbox restriction) — directory is empty"
  ```
- **What stays in main context:** One-line summaries from each scorer agent (OPP-NNN, composite score, B/B/P), resolution of reviewer Critical findings, and the save + evidence-log clearance. Do not re-derive scores or B/B/P inline.

See the Phase checklist and Workflow sections for the authoritative step sequence and ordering.

## Phase checklist

- [ ] Confirm `opportunities/_index.md` exists and GRC gate cleared for flagged items
- [ ] Dispatch one `opportunity-scorer` agent per opportunity in a single parallel tool-call batch (pass: OPP-ID, OPP entry path `opportunities/OPP-NNN.md`, process file path `processes/PROC-NNN.md` for the opportunity's process, staging file path; the agent reads all source files itself)
- [ ] Collect one-line summaries from scorer agents (OPP-NNN, composite, B/B/P). Full scored entries are in staging files.
- [ ] Assemble via Bash: move staged files → compute composites + stamp + write `model/scores.json` → generate `scores/_index.md` (see Assembly sequence in Subagent Dispatch)
- [ ] Verify count: `ls <name>/scores/OPP-*.md | wc -l`; confirm no PENDING: `grep -l PENDING <name>/scores/OPP-*.md` (expect no output)
- [ ] Dispatch the `opportunity-reviewer` subagent for independent review
- [ ] Resolve any Critical findings before save
- [ ] Save each scored entry to `<name>/scores/OPP-NNN.md`; generate `scores/_index.md` master index
- [ ] Log reviewer clearance in `evidence-log.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:prioritizing-roadmap`

## Workflow

1. Confirm `opportunities/_index.md` exists and GRC clearance is recorded for all flagged opportunities.
2. Dispatch `opportunity-scorer` agents in parallel — one per opportunity. Pass each agent its OPP-ID, the paths to `opportunities/OPP-NNN.md` and `processes/PROC-NNN.md` (for the process the opportunity belongs to), and its staging file path (`_staging/phase6/OPP-NNN.md`). The agent reads all source files itself. Do NOT share cross-OPP context between agents. Collect one-line summaries only — do NOT request the full scored entry back.
3. After all agents complete, run the Assembly sequence (see Assembly in Subagent Dispatch): move staged files → compute composites + stamp files + write `model/scores.json` (single Python script) → generate `scores/_index.md`. Verify count and confirm no PENDING values remain. Cleanup `_staging/phase6` (non-fatal). B/B/P is in the individual score files and the index — do not re-derive in main context.
4. Dispatch the `opportunity-reviewer` subagent. Pass: engagement folder path only. The reviewer reads `scores/_index.md` and individual `scores/OPP-NNN.md` files itself. Do not pass document content.
5. Resolve all Critical findings. Important findings should be addressed; Minor findings are noted.
6. Save and chain forward.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Composite score is enough — we can drop the dimensions." | Composite hides trade-offs. A high-value, low-readiness opportunity scores the same as a medium-everything opportunity. The dimensions ARE the decision input. |
| "We can score from intuition for the small ones." | The rule is categorical for a reason. Once intuition is permitted for "small" items, the boundary moves. |
| "We'll figure out Build/Buy/Partner later." | B/B/P is an input to sequencing and brief writing. Deferring it pushes the same decision into less-prepared phases. |
| "The reviewer subagent slows us down." | The reviewer is the durability mechanism for this phase. Skipping it is how scored portfolios pass through to delivery with sourcing gaps. |
| "Scoring in main context lets me calibrate scores across OPPs — parallel agents can't do that." | Cross-OPP calibration happens during the consistency review of the assembled file, not during drafting. The `opportunity-reviewer` subagent is the calibration gate. Scoring inline re-introduces context bloat. |
| "The value estimate is the sum of each step's individual time savings." | For Chain Automation opportunities, value comes primarily from eliminating human verification checkpoints, not from accelerating individual steps. Linear step-count aggregation is the wrong model. Cite checkpoints eliminated and effort per checkpoint from the chain scan. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `scores/OPP-NNN.md` in this response. State the file path(s) only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: top 3 scored opportunities with scores, score distribution, any critical reviewer findings and how resolved.

**Session boundary:** After the user approves `scores/_index.md` is saved and the reviewer is cleared, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:prioritizing-roadmap` to begin Phase 7. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:prioritizing-roadmap` (after `scores/_index.md` is saved and reviewer cleared)
