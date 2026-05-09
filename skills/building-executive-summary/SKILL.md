---
name: ai-process-assessment:building-executive-summary
description: Phase 9 — produces a standalone 1–2 page executive summary (executive-summary.md) sourced entirely from prior phase outputs. Designed to travel independently as a read-ahead for decision meetings. No new analysis.
---

# Phase 9: Building the Executive Summary

## Role in the system

The executive summary is the only artifact in the methodology designed to travel independently. It is sent as a read-ahead before a decision meeting, attached to a calendar invite, or shared without the full HTML deliverable open. It must stand alone: a reader who has never seen the engagement should be able to make a Go/No-Go decision from this document.

Phase 9 produces no new analysis. Every claim traces to a source file from Phases 1–8. If a claim cannot be sourced, it does not appear in the summary.

## Gate condition

`ai-process-assessment:deliverable-gate` cleared (all 8 phases complete, four-dimension integrity check passed, clearance recorded in `evidence-log.md`). This skill creates `executive-summary.md`.

## Required source files

The drafter receives all five. If any is missing, the skill halts and reports which file is absent.

| File | What it provides |
|---|---|
| `scope.md` | Decision-maker, sponsoring question, success criteria, in/out of scope |
| `roadmap.md` | Waves, sequencing, budget envelope |
| `scored-opportunities.md` | Portfolio scores, B/B/P classifications |
| `opportunities.md` | Value hypotheses, GRC flags |
| `baselines.md` | Key metrics grounding all value claims |

## Required content

The summary contains exactly these sections, in this order:

1. **Go / No-Go recommendation** — the verdict, with the named decision-maker (from `scope.md`)
2. **Pull-quote** — one sentence, ≤25 words, all figures traceable to source files
3. **Why This, Why Now** — 3–4 sentences, citing ≥2 named baseline metrics from `baselines.md`, sponsoring question from `scope.md`, cost of inaction
4. **Scoring & Wave Logic** — one paragraph explaining evaluation criteria from `scored-opportunities.md` and wave sequencing from `roadmap.md`
5. **Portfolio view** — single table covering every initiative: OPP-NNN, title, type, wave, composite score, named owner, month target
6. **Budget ask vs. envelope** — total ask vs. envelope from `roadmap.md`, with deltas
7. **Top 3–5 risks with mitigations** — each risk has a named owner (no "the team")
8. **First Proof Point** — names the specific OPP-ID of the highest-scored Wave 1 item; month target from `roadmap.md`; primary outcome from `opportunities.md`; one-sentence strategic rationale traced to `scope.md`
9. **Assumptions & Limitations** — two labeled sub-groups (Conditions and Open Items); each open item named and attributed; no vague placeholders
10. **Immediate next actions** — named owners, specific dates (no "Q3" — actual dates)

## Phase checklist

- [ ] Confirm `deliverable-gate` clearance is recorded in `evidence-log.md`
- [ ] Confirm all five source files exist
- [ ] Dispatch one `executive-summary-drafter` agent in a single tool call (passes: scope.md, roadmap.md, scored-opportunities.md, opportunities.md, baselines.md)
- [ ] Receive returned `executive-summary.md` content
- [ ] Verify every value claim cites a baseline; every owner is named (not a role); every date is concrete
- [ ] Confirm `Why This, Why Now` cites ≥2 named baseline metrics
- [ ] Confirm `Pull-quote` is ≤25 words and all figures are traceable to source files
- [ ] Confirm `Scoring & Wave Logic` names the wave framing used in `roadmap.md`
- [ ] Confirm `First Proof Point` names the specific highest-scored Wave 1 OPP-ID
- [ ] Confirm `Assumptions & Limitations` contains both a Conditions sub-group and an Open Items sub-group, with no vague placeholders
- [ ] Save to `docs/engagements/<engagement>/executive-summary.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:building-deliverable`

## Workflow

1. Confirm preconditions: deliverable-gate cleared; all five source files present.
2. Dispatch the `executive-summary-drafter` agent. Pass it the full content of all five source files. The agent is a single-pass writer — no fan-out, no parallelism. The document is short enough that assembly overhead would outweigh any benefit.
3. Receive the draft. Verify in main context: the Go/No-Go has a named decision-maker; the portfolio table covers every OPP from `scored-opportunities.md`; every risk has a named mitigation owner; every next action has a date. Confirm `Why This, Why Now` cites ≥2 named baseline metrics; confirm `Pull-quote` is ≤25 words and all figures are traceable to source files; confirm `Scoring & Wave Logic` names the wave framing used in `roadmap.md`; confirm `First Proof Point` names the specific highest-scored Wave 1 OPP-ID; confirm `Assumptions & Limitations` contains both a Conditions sub-group and an Open Items sub-group with no vague placeholders.
4. Save the file. The chain advances to `building-deliverable`.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The HTML deliverable already covers this — we don't need a separate summary." | The HTML opens in a browser. The executive summary travels in email, in calendar invites, on phones. They serve different consumption contexts. Skip it and you lose the read-ahead. |
| "We can re-derive numbers here for clarity." | New analysis in Phase 9 is rework with no review. Every figure must trace to `baselines.md` exactly as it appears in `scored-opportunities.md`. |
| "Owners can be the role — 'Head of Ops' is fine." | Roles change; people own decisions. Name the person. If unknown, that is a Phase 7 gap to fix in roadmap.md, not a Phase 9 problem to paper over. |
| "Dates can be quarters — 'Q3' is enough." | Q3 is a planning artifact, not a commitment. Use month-X targets from `roadmap.md`. |
| "Three risks is enough — we don't need five." | Three to five is the rule. Truncating to three when five matter hides risk; padding to five when three matter dilutes signal. Use the count the engagement evidence supports. |
| "We can fan out the summary across multiple agents for speed." | The summary is short. Assembly overhead from fan-out exceeds the time savings. Single-pass drafting is the discipline. |

## Handoff Protocol

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: Go/No-Go verdict, named decision-maker, wave portfolio (count of OPPs per wave), total budget ask, quick-win OPP-ID.

## Chain to next skill

→ `ai-process-assessment:building-deliverable` (Phase 10 — produces the HTML deliverable)
