---
name: ai-process-assessment:governance-risk-gate
description: Cross-cutting gate — evaluates GRC-flagged opportunities across regulatory exposure, model risk, auditability, failure consequence. Returns Cleared / Cleared with Conditions / Blocked. Cannot be bypassed without CLAUDE.md override.
---

# [CROSS-CUTTING] Governance, Risk & Compliance Gate

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `opportunities/_index.md` — confirm it exists and identify all non-Green GRC flagged entries from the GRC column.

Gate condition: At least one non-Green GRC flag must be present to invoke this gate.

## Role in the system

Fires after `opportunities/_index.md` is saved for every opportunity with a non-Green GRC flag. Independent of strategic priority and scoring outcome. Returns one of three statuses; routing depends on the status.

This gate cannot be bypassed without an explicit CLAUDE.md override naming the engagement and the rationale.

## Gate condition

`opportunities/_index.md` exists and contains at least one opportunity with a Yellow or Red GRC flag.

This skill creates the `grc/` folder with per-OPP GRC review files and `grc/_index.md`.

## GRC Evaluation Dimensions

| Dimension | Question to answer |
|---|---|
| Regulatory exposure | Does this opportunity touch regulated data, decisions, or processes? Which regimes apply? |
| Model risk | What is the consequence of a model error? How is the model validated, monitored, and updated? |
| Auditability | Can a third party reconstruct the decision path for any individual transaction? |
| Failure consequence | What happens when this fails — to customers, to the business, to regulators? |

## GRC Clearance — three exit statuses

| Status | Meaning | Routing |
|---|---|---|
| Cleared | No material concerns; opportunity proceeds unchanged | → `ai-process-assessment:scoring-opportunities` |
| Cleared with Conditions | Proceed only with named conditions (e.g., human-in-loop, audit logging, scope limit) | → `ai-process-assessment:scoring-opportunities` with conditions attached to OPP entry |
| Blocked | Material concerns cannot be mitigated within engagement scope | → `ai-process-assessment:identifying-opportunities` to re-classify or remove |

## Phase checklist

> Dispatch all flagged OPPs to `grc-reviewer` in a single parallel batch. Sequential dispatch is a context-bloat anti-pattern — wait for all clearance statuses before proceeding to update `opportunities/OPP-NNN.md` files.

- [ ] Dispatch one `grc-reviewer` agent per flagged opportunity in a SINGLE parallel tool-call batch. Do not dispatch sequentially. Each agent receives: engagement folder path, OPP-ID, and staging file path `<engagement-folder>/_staging/grc/OPP-NNN.md`. The agent reads `opportunities/OPP-NNN.md` directly — do not pass file content. Never pass the full engagement context.
- [ ] Collect one-line summaries from agents (status + inline conditions list). Full reviews are in staging files — do NOT request them back.
- [ ] Record the clearance status for each OPP from the one-line summaries (Cleared / Cleared with Conditions / Blocked)
- [ ] Assemble GRC reviews to canonical folder via Bash:
  ```bash
  mkdir -p <name>/grc
  mv <name>/_staging/grc/OPP-*.md <name>/grc/
  ```
  Then generate the index from extraction headers:
  ```bash
  echo "| OPP-ID | Status | Conditions |" > <name>/grc/_index.md
  echo "|--------|--------|------------|" >> <name>/grc/_index.md
  for f in <name>/grc/OPP-*.md; do
    header=$(grep "^<!-- index:" "$f" | head -1)
    id=$(echo "$header" | grep -o 'id=[^ >]*' | cut -d= -f2)
    gstatus=$(echo "$header" | grep -o 'status=[^ >]*' | cut -d= -f2)  # not 'status': read-only in zsh
    cond=$(echo "$header" | grep -o 'conditions=[^ >]*' | cut -d= -f2)
    echo "| $id | $gstatus | $cond |" >> <name>/grc/_index.md
  done
  ```
  Verify: `ls <name>/grc/OPP-*.md | wc -l`
- [ ] For Cleared with Conditions, update the GRC flag line in `opportunities/OPP-NNN.md` using the inline conditions from the one-line summary — no staging file read required. Format: `**GRC flag:** Yellow — [original basis] | Cleared with Conditions: (1) <condition>, (2) <condition>`
- [ ] For Blocked, route the opportunity back to Phase 5 for re-classification or removal; do not carry a Blocked OPP into scoring
- [ ] For Cleared, no update to `opportunities/OPP-NNN.md` is required

**Output rule:** Do NOT reproduce OPP entry content in this response. Summarize GRC outcomes as a table: OPP-ID | Status | Condition count. Do not echo full OPP content.
- [ ] Cleanup: `rm -rf <name>/_staging/grc`

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The legal team will catch this later." | Later is delivery. Catching GRC issues at delivery means rework, not refinement. |
| "Yellow flags don't really need a full review." | Yellow exists to force the question, not to permit a shortcut. The review is the answer to "is Yellow actually OK?". |
| "We can attach conditions informally — they don't need to be in the OPP entry." | Conditions that don't travel with the opportunity get lost between scoring and delivery. They belong in the entry. |
| "Blocked opportunities can stay in the log for awareness." | Blocked items in the log get scored anyway. Either re-classify (find a different intervention for the same process) or remove. |
| "Sequential GRC reviews are fine — there are usually only 1–2 flagged items." | Even one GRC review conducted in main context adds a long agentic result to the window. Parallel dispatch + staging files keeps main context to one-liner summaries regardless of the number of flagged items. |

## Chain to next skill

→ `ai-process-assessment:scoring-opportunities` (Cleared / Cleared with Conditions)
→ `ai-process-assessment:identifying-opportunities` (Blocked — re-classify or remove)

**Session boundary:** After GRC review is complete and `grc/_index.md` is generated, this gate session is complete. Instruct the user to start a fresh Claude Code session and invoke the appropriate next skill: `ai-process-assessment:scoring-opportunities` (Cleared / Cleared with Conditions) or `ai-process-assessment:identifying-opportunities` (Blocked). Do not continue methodology work in this session.
