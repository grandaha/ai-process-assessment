---
name: ai-process-assessment:governance-risk-gate
description: Cross-cutting gate — evaluates GRC-flagged opportunities across regulatory exposure, model risk, auditability, failure consequence. Returns Cleared / Cleared with Conditions / Blocked. Cannot be bypassed without CLAUDE.md override.
---

# [CROSS-CUTTING] Governance, Risk & Compliance Gate

## Role in the system

Fires after `opportunities.md` is saved for every opportunity with a non-Green GRC flag. Independent of strategic priority and scoring outcome. Returns one of three statuses; routing depends on the status.

This gate cannot be bypassed without an explicit CLAUDE.md override naming the engagement and the rationale.

## Gate condition

`opportunities.md` exists and contains at least one opportunity with a Yellow or Red GRC flag.

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

> Dispatch all flagged OPPs to `grc-reviewer` in a single parallel batch. Sequential dispatch is a context-bloat anti-pattern — wait for all clearance statuses before proceeding to update opportunities.md.

- [ ] Dispatch one `grc-reviewer` agent per flagged opportunity in a SINGLE parallel tool-call batch. Do not dispatch sequentially. Each agent receives only its own OPP entry, relevant process context, and its staging file path: `<engagement-folder>/_staging/grc/OPP-NNN.md` — never the full engagement context.
- [ ] Collect one-line summaries from agents (status + inline conditions list). Full reviews are in staging files — do NOT request them back.
- [ ] Assign one of: Cleared / Cleared with Conditions / Blocked (from the one-line summaries)
- [ ] Assemble full reviews into `evidence-log.md` via Bash: `cat docs/engagements/<name>/_staging/grc/*.md >> docs/engagements/<name>/evidence-log.md`
- [ ] For Cleared with Conditions, use the inline conditions from the one-line summaries to update the OPP entry in `opportunities.md` — no staging file read required
- [ ] For Blocked, route the opportunity back to Phase 5 for re-classification or removal
- [ ] Update `opportunities.md` with clearance status per OPP
- [ ] Cleanup: `rm -rf docs/engagements/<name>/_staging/grc`

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
