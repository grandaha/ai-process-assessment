---
name: ai-process-assessment:mapping-context
description: Phase 2 — establishes organizational and strategic context. Maps business model, priorities, org structure, AI maturity, funding model, risk posture, political landscape. Saves context.md.
---

# Phase 2: Mapping Organizational Context

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Confirm `scope.md` exists (already read in step 1).
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently. At the live-interview step in the Workflow below, read the intake file listed for Phase 2 in the marker's Phase Intake Map (`<intake_root>/org-context.md`) instead of interviewing a live sponsor or operator.

Gate condition: `scope.md` must be present before proceeding.

## Role in the system

Opportunities don't exist in a vacuum. Two organizations with identical processes can have opposite right answers depending on funding model, risk posture, and political reality. This phase captures the surrounding conditions so later scoring and sequencing reflect the organization that actually exists, not a generic one.

## Gate condition

`scope.md` must exist in the engagement folder. This skill creates `context.md`.

## Phase checklist

- [ ] Capture the business model — how the organization makes money and where margin pressure sits
- [ ] List strategic priorities for the current and next planning cycle
- [ ] Map org structure relevant to scope: who owns what, where the seams are
- [ ] Assess AI/automation maturity: prior wins, prior failures, current capabilities
- [ ] Document the funding model: capex/opex split, who pays for transformation
- [ ] Capture risk posture: regulated, conservative, tolerant; recent incidents
- [ ] Capture political landscape: who must be aligned, who can veto, who is skeptical
- [ ] Save to `docs/engagements/<engagement>/context.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:inventorying-tech-data`

## Key outputs (saved to context.md)

| Field | Content |
|---|---|
| Business model | How the org makes money; where margin pressure lives |
| Strategic priorities | Stated priorities for current and next planning cycle |
| Org structure | Functions, ownership boundaries, key seams within scope |
| AI/automation maturity | Prior initiatives — wins, failures, lessons; current capabilities |
| Funding model | Capex/opex split; who funds transformation; who owns ROI |
| Risk posture | Regulatory exposure; cultural risk tolerance; recent incidents |
| Political landscape | Aligners, vetoers, skeptics; coalitions and rivalries within scope |

## Workflow

1. Confirm `scope.md` exists. If not, return to Phase 1.
2. Walk each context dimension with the sponsor and at least one operator.
3. Triangulate maturity: don't take "we're early days" or "we're advanced" at face value — ask for specific prior initiatives and outcomes.
4. Surface political landscape directly. If the sponsor declines to discuss it, note that as a risk.
5. Save `context.md` and chain forward.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Context is fluff — get to the opportunities." | Without context, scoring becomes generic. Strategic alignment, change readiness, and risk dimensions all depend on it. |
| "They told me they're 'mature' on AI." | Self-assessed maturity is unreliable. Ask for specific prior initiatives and outcomes. |
| "Politics isn't my job to map." | Politics determines which opportunities survive. Skipping this step is delegating sequencing failure to luck. |
| "Funding model can be figured out at the end." | Funding model determines which sourcing recommendations are viable. Capture it now. |
| "Risk posture is the same as their industry's." | Industry sets the floor. Internal posture — driven by recent incidents and leadership — sets the actual threshold. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `context.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: strategic priorities, AI maturity assessment, risk posture, funding model.

**Session boundary:** After the user approves `context.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:inventorying-tech-data` to begin Phase 3. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:inventorying-tech-data` (after `context.md` is saved)
