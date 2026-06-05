---
name: ai-process-assessment:deliverable-gate
description: Cross-cutting terminal gate — runs four-dimension integrity checklist (evidence, logic, completeness, communication) before any external sharing. Cannot be bypassed.
---

# [CROSS-CUTTING] Deliverable Gate

## Session Start

This skill runs as a standalone session. At session start:
1. Confirm the engagement folder path with the user if not already provided.
2. Read all phase output files for integrity check:
   `scope.md`, `context.md`, `tech-inventory.md`, `process-map.md`, `baselines.md`,
   `opportunities/_index.md`, `scores/_index.md`, `roadmap.md`,
   `usecase-briefs/_index.md`, `cost-actuals.md`, `business-case.md`

Gate condition: All phase output files must exist before the integrity check can proceed.

## Role in the system

Fires before ANY external sharing of outputs, regardless of phase. The terminal gate. Cannot be bypassed without explicit CLAUDE.md override.

## Gate condition

Any output (interim or final) is about to be shared with anyone outside the engagement team.

## Four Integrity Dimensions

- **Evidence integrity** — every value claim in the deliverable traces to a citation in `baselines.md`. No figure floats free.
- **Logic integrity** — the chain process → opportunity → score → roadmap → brief has no gaps. A reader can walk from any brief back to the baseline that grounds it.
- **Completeness** — every in-scope domain from `scope.md` is addressed. Gaps are acknowledged, not hidden.
- **Communication** — the executive summary leads with the portfolio view (waves, value, sequencing), not with methodology narrative.

## Phase checklist

- [ ] Run Evidence integrity check — sample value claims, walk each to its baseline
- [ ] Run Logic integrity check — pick a Wave 1 brief, trace process → opportunity → score → roadmap → brief
- [ ] Run Completeness check — cross-reference scoped domains against deliverable coverage
- [ ] Run Business Case integrity check — confirm `business-case.md` ROM label is present; every figure has a stated assumption; Buy/Partner initiatives flag missing vendor quotes; one-time and recurring costs are separated
- [ ] Run Communication check — does the executive summary lead with portfolio view?
- [ ] Dispatch `opportunity-reviewer` subagent for independent integrity review
  Return: The reviewer appends findings to `<engagement-folder>/evidence-log.md` directly. Returns one-line summary: "N Critical, N Important, N Minor findings." The orchestrator does NOT receive full review content. Resolve all Critical findings before recording clearance.
- [ ] Resolve all Critical findings before clearance
- [ ] Mark cleared for delivery in `evidence-log.md` OR route back to the relevant skill for remediation

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "It's just an interim share — the gate is overkill." | "Interim" outputs become the basis for decisions. The gate fires before any external sharing, not just final delivery. |
| "Spot-checking evidence is enough." | Spot-checks miss the systematic gaps. The gate samples deliberately, including the highest-stakes claims. |
| "Acknowledged gaps look bad — better to omit them." | Hidden gaps surface in delivery and cost credibility. Acknowledged gaps demonstrate rigor. |
| "Lead with methodology — they paid for the rigor." | Executives buy the portfolio view. Methodology earns credibility in appendices, not in the lead. |

## Chain to next skill

**Output rule:** Do NOT reproduce the contents of any phase file in this response. State clearance status, critical finding count, and file paths only.

→ `ai-process-assessment:building-executive-summary` (on clearance — Phase 10 produces the standalone executive summary).

On non-clearance, route to the skill responsible for the failed dimension. Phase 10 may not begin until clearance is recorded in `evidence-log.md`.

**Session boundary:** After clearance is recorded in `evidence-log.md`, this gate session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:building-executive-summary` to begin Phase 10. Do not continue methodology work in this session.
