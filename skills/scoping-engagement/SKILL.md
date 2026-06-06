---
name: ai-process-assessment:scoping-engagement
description: Phase 1 — front gate for all analytical work. Elicits sponsoring question, decision-maker, in/out-of-scope domains, success criteria, constraints. Saves scope.md.
---

# Phase 1: Scoping the Engagement

## Session Start

This skill runs as a standalone session. At session start:
1. Ask the user for the engagement name. This becomes the folder path `docs/engagements/<name>/`. Accept any lowercase, kebab-case, or alphanumeric string. Reject placeholder strings like `<name>`, `<fill in>`, or empty input — halt and re-ask.
2. Run `mkdir -p docs/engagements/<name>/` to create the engagement folder before writing any files.
3. No predecessor files required — this is Phase 1.

Gate condition: None. Proceed directly to scoping once the engagement folder is created.

## Role in the system

This is the front gate. No other phase may begin until scope.md exists. The purpose is to convert a vague request ("we want to identify AI use cases") into a decision the engagement is meant to enable. If you cannot name the decision-maker and what they will do differently, you do not yet have an engagement — you have a request for a list.

## Gate condition

New engagement prompt. No predecessor file required. This skill creates `scope.md`.

## Phase checklist

- [ ] Elicit the sponsoring question (the decision this engagement must enable)
- [ ] Identify the decision-maker by name and role; capture what they will do differently with the output
- [ ] List in-scope business units, process families, technology layers
- [ ] List out-of-scope items with rationale
- [ ] Define observable, measurable success criteria
- [ ] Capture constraints: budget, timeline, access, political sensitivities
- [ ] Apply the scope validity test: outcome must be a decision or action, not a list
- [ ] Save to `docs/engagements/<engagement>/scope.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:mapping-context`

## Key outputs (saved to scope.md)

| Field | Content |
|---|---|
| Engagement folder | Canonical path for all phase outputs — `docs/engagements/<resolved-name>/`. Written by Phase 1; all downstream phases read this field. |
| Sponsoring question | The single question this engagement must answer to enable a decision |
| Decision-maker | Name, role, and what they will do differently with the output |
| In-scope domains | Business units, process families, technology layers covered |
| Out-of-scope boundaries | What is explicitly excluded, with rationale |
| Success criteria | Observable, measurable conditions that signal the engagement succeeded |
| Constraints | Budget, timeline, access limits, political sensitivities |

## Workflow

1. Ask for the engagement name. Create `docs/engagements/<name>/` via `mkdir -p`.
2. Read user's engagement prompt.
3. If sponsoring question is not stated, ask for it explicitly. Do not infer.
4. Identify the decision-maker. If unnamed, ask. Capture their decision verb.
5. Walk in-scope and out-of-scope domains. Press for the boundary cases.
6. Translate "success" into something measurable. Reject "improved efficiency" — demand a metric or decision outcome.
7. Capture constraints — including the political ones the sponsor may not volunteer.
8. Apply the scope validity test. If the outcome is a list, return to step 2.
9. Write `scope.md` to `docs/engagements/<name>/scope.md`. The first field in the file is `**Engagement folder:** docs/engagements/<name>/`.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The sponsor said they want a list of use cases — that's the scope." | A list is an output, not a decision. Ask: what will they do with the list? That's the scope. |
| "The decision-maker is obvious — it's the person who hired us." | Often the buyer is not the decider. Ask explicitly who signs off on what comes next. |
| "Out-of-scope is whatever they didn't mention." | Implicit exclusions become disputes at delivery. Make exclusions explicit and rationale-backed. |
| "Success means they're happy with the deck." | Stakeholder satisfaction is not a success criterion. A success criterion is a measurable decision or action. |
| "Constraints will surface as we go." | Constraints discovered late kill credibility. Surface political sensitivities now or pay later. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `scope.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: decision-maker named, sponsoring question, in/out of scope domains, success criteria defined.

**Session boundary:** After the user approves `scope.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:mapping-context` to begin Phase 2. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:mapping-context` (after `scope.md` is saved)
