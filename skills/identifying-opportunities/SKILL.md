---
name: ai-process-assessment:identifying-opportunities
description: Phase 5 — applies opportunity type taxonomy to every mapped process. Produces typed opportunity log (OPP-NNN) with hypothesis, value range, feasibility/data/GRC flags. Saves per-OPP files to opportunities/ folder.
---

# Phase 5: Identifying Opportunities

## Session Start

This skill runs as a standalone session. At session start:
1. Confirm the engagement folder path with the user if not already provided.
2. Read `process-map.md`, `baselines.md`, and `tech-inventory.md` — confirm each exists.

Gate condition: Both `process-map.md` and `baselines.md` must be present before proceeding.

## Role in the system

This phase converts mapped processes into a typed opportunity log. Type — RPA / AI Augmentation / Chain Automation / AI Automation / Agentic / Data & Analytics — is assigned BEFORE scoring because the rubric weights vary by type. A misclassified opportunity gets the wrong scoring lens and the wrong sourcing recommendation.

## Gate condition

`process-map.md` and `baselines.md` must both exist. This skill creates the `opportunities/` folder with per-OPP files and `opportunities/_index.md`.

## OPP-NNN Entry Structure

Every opportunity is logged with a stable identifier `OPP-NNN` and the following seven fields:

| Field | Content |
|---|---|
| Process reference | ID from `process-map.md` |
| Opportunity type | RPA / AI Augmentation / Chain Automation / AI Automation / Agentic / Data & Analytics |
| Hypothesis | One-sentence statement: "We believe that [intervention] will [effect] because [mechanism]." |
| Value hypothesis | Estimated value range, citing specific baseline(s) from `baselines.md` |
| Chain formation | If two or more consecutive AI-capable steps from the process-map.md chain scan are involved: describe the chain (step range, checkpoints eliminated, current human effort at each eliminated checkpoint). If this is a single-step opportunity, write "Single step — no chain." |
| Feasibility flag | Green / Yellow / Red — based on `tech-inventory.md` |
| Data readiness flag | Green / Yellow / Red — based on data asset catalog |
| GRC flag | Green / Yellow / Red — regulatory, model risk, auditability, failure consequence |

**Categorical rule: Hypothesis statement must be written before value is estimated. This prevents reverse-engineering the hypothesis from a desired outcome.**

## Subagent Dispatch

Per-process opportunity identification is offloaded to subagents. Each mapped process is independent for typing purposes, so they parallelize cleanly.

- **When:** After `process-map.md` and `baselines.md` are confirmed present, dispatch one `opportunity-typer` subagent per mapped process in a single parallel tool-call batch.
- **Pass to each subagent:** engagement folder path, process ID, and staging file path: `<engagement-folder>/_staging/phase5/proc-<process-id>.md`. The agent reads its own `process-map.md` entry, `baselines.md` rows, and `tech-inventory.md` sections. Do not pass file content to the subagent.
- **Return:** One-line summary only: process ID, opportunity count, GRC flag counts (Green/Yellow/Red). Full OPP content is written to the staging file by the agent — it does NOT flow back to main context.
- **Assembly:** After all agents complete, assemble with Bash:
  ```bash
  mkdir -p docs/engagements/<name>/opportunities
  awk '/^## TEMP/{n++; f=sprintf("docs/engagements/<name>/opportunities/OPP-%03d.md",n); printf "## OPP-%03d",n > f; sub(/^## TEMP-[^ ]+/,""); print > f; next} f{print > f}' docs/engagements/<name>/_staging/phase5/proc-*.md
  ```
  Then generate the index by reading the per-file headers:
  ```bash
  echo "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC |" > docs/engagements/<name>/opportunities/_index.md
  echo "|--------|---------|------|-------------|----------------|-----|" >> docs/engagements/<name>/opportunities/_index.md
  for f in docs/engagements/<name>/opportunities/OPP-*.md; do
    id=$(grep "^## OPP" "$f" | head -1 | awk '{print $2}')
    proc=$(grep "^\*\*Process:" "$f" | head -1 | sed 's/\*\*Process:\*\* //')
    type=$(grep "^\*\*Type:" "$f" | head -1 | sed 's/\*\*Type:\*\* //' | cut -d' ' -f1)
    feas=$(grep "^\*\*Feasibility flag:" "$f" | head -1 | sed 's/\*\*Feasibility flag:\*\* //')
    data=$(grep "^\*\*Data readiness flag:" "$f" | head -1 | sed 's/\*\*Data readiness flag:\*\* //')
    grc=$(grep "^\*\*GRC flag:" "$f" | head -1 | sed 's/\*\*GRC flag:\*\* //' | cut -d' ' -f1)
    echo "| $id | $proc | $type | $feas | $data | $grc |" >> docs/engagements/<name>/opportunities/_index.md
  done
  ```
  Verify with: `ls docs/engagements/<name>/opportunities/OPP-*.md | wc -l`
  Cleanup: `rm -rf docs/engagements/<name>/_staging/phase5`
- **What stays in main context:** The one-line summaries from each agent (process ID, counts, GRC flags), the OPP headings from the grep verification, the GRC-flag branch decision, and cross-process consistency review of headings only.

## Phase checklist

- [ ] Confirm `process-map.md` and `baselines.md` exist
- [ ] For each mapped process, walk the opportunity type taxonomy and assign the correct type
- [ ] Write the hypothesis statement BEFORE estimating value
- [ ] Source value range against named baseline(s) from `baselines.md`
- [ ] Set feasibility flag against `tech-inventory.md`
- [ ] Set data readiness flag against data asset catalog
- [ ] Set GRC flag based on regulatory exposure, model risk, auditability, failure consequence
- [ ] Assign stable OPP-NNN identifier
- [ ] Save each opportunity to `docs/engagements/<engagement>/opportunities/OPP-NNN.md`; generate `opportunities/_index.md` master index
- [ ] If any opportunity has a non-Green GRC flag → branch to `ai-process-assessment:governance-risk-gate`
- [ ] Otherwise → Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:scoring-opportunities`

## Workflow

1. Load `process-map.md` and `baselines.md`. If either is missing, return to Phase 4.
2. For each process, review the chain scan from `process-map.md`. Identify chain formation opportunities first — runs of consecutive Green steps that could eliminate one or more human verification checkpoints. These are Chain Automation type candidates. Then walk the six-row taxonomy for remaining steps. Pick the type that fits the work, not the brand the client wants on the slide.
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
| "We evaluated each step on its own merits and assigned the best type." | Per-step evaluation misses chain opportunities. A step that looks unattractive in isolation may be the right assignment for AI because it sits between two AI-capable steps — eliminating an extra human checkpoint can outweigh per-step comparative disadvantage. Always review chain scan results before typing individual steps. |

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
