---
name: ai-process-assessment:using-methodology
description: Keystone — load at session start. Teaches model how to find and invoke all process-assessment skills, carries phase map, opportunity taxonomy, and master rationalization table.
---

# Using the Process Assessment Methodology

<EXTREMELY-IMPORTANT>
You are operating inside the AI & Automation Use Case Identification methodology. Every engagement runs through ten sequential phases plus two cross-cutting gates. You may not skip phases. You may not generate output for a phase until the prior phase's file exists in the engagement folder. CLAUDE.md overrides this skill — but only when CLAUDE.md says so explicitly.
</EXTREMELY-IMPORTANT>

## Phase Map

| Phase | Skill ID | Purpose | Gate condition | Output file |
|---|---|---|---|---|
| 1 | `scoping-engagement` | Front gate — sponsoring question, decision-maker, scope | New engagement prompt | `scope.md` |
| 2 | `mapping-context` | Org / strategic / political context | `scope.md` exists | `context.md` |
| 3 | `inventorying-tech-data` | Systems, APIs, data, enablers | `context.md` exists | `tech-inventory.md` |
| 4 | `discovering-processes` | Four-round interviews, baseline metrics | `tech-inventory.md` exists | `process-map.md`, `baselines.md` |
| 5 | `identifying-opportunities` | Typed opportunity log (OPP-NNN) | `process-map.md` and `baselines.md` exist | `opportunities.md` |
| 6 | `scoring-opportunities` | 7-dimension rubric + Build/Buy/Partner | `opportunities.md` saved; GRC cleared for any flagged | `scored-opportunities.md` |
| 7 | `prioritizing-roadmap` | Foundation/Scale/Optimize sequencing | `scored-opportunities.md` saved; reviewer cleared | `roadmap.md` |
| 8 | `packaging-usecases` | UC-NNN briefs (SCRA structure) | `roadmap.md` saved; reviewer cleared | `usecase-briefs.md` |
| 9 | `building-executive-summary` | Standalone 1–2 page executive summary | `deliverable-gate` cleared | `executive-summary.md` |
| 10 | `building-deliverable` | Self-contained client-ready HTML deliverable | `executive-summary.md` exists | `deliverable.html` |
| Gate A | `governance-risk-gate` | GRC review of flagged opportunities | Any non-Green GRC flag in `opportunities.md` | Logged in `evidence-log.md` |
| Gate B | `deliverable-gate` | Final integrity checklist | Before any external sharing | Clearance recorded in `evidence-log.md` |

## Opportunity Type Taxonomy

| Type | Definition |
|---|---|
| RPA | Deterministic, rules-based execution of structured tasks across digital systems. No judgment required. |
| AI Augmentation | AI assists a human in the loop — human retains decision authority. Examples: drafting, summarization, recommendation. |
| AI Automation | AI executes end-to-end without per-instance human review for bounded, well-specified tasks with measurable accuracy thresholds. |
| Agentic | Multi-step, tool-using AI that plans and acts toward a goal across systems with state and feedback. Higher autonomy, higher risk. |
| Data & Analytics | Decision support through measurement, modeling, or visualization. No process automation — informs human action. |

## Master Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "They just want a list of use cases — skip the discovery." | A list without baselines, types, and decision-maker context is a wishlist, not a portfolio. The methodology produces the list; skipping it produces noise. |
| "We already know what they need." | Prior knowledge is a hypothesis, not evidence. Run the phases — if you're right, they confirm fast. If you're wrong, you avoid shipping the wrong thing. |
| "There's no time for the full methodology." | Time pressure is the strongest argument for the methodology, not against it. Skipping phases shifts cost from discovery to rework. |
| "The client wants AI, not automation." | The client wants outcomes. Type is determined by the work, not the brand. A misclassified RPA opportunity sold as AI fails on cost and reliability. |
| "We've done this kind of engagement before." | The methodology travels; the answers don't. Reuse the structure, re-derive the content. |

## Routing Logic

- On any new engagement prompt → invoke `scoping-engagement`.
- After each phase's output file is saved → invoke the next skill in the chain.
- If any opportunity in `opportunities.md` has a non-Green GRC flag → invoke `governance-risk-gate` before scoring.
- Before any external sharing of any output → invoke `deliverable-gate`.
- After `deliverable-gate` clearance → invoke `building-executive-summary` (Phase 9).
- After `executive-summary.md` is saved → invoke `building-deliverable` (Phase 10).
- If CLAUDE.md declares an override for an engagement → honor it, and note the deviation for the deliverable gate's audit.

## When-to-Invoke Reference

| Trigger phrase / situation | Skill to invoke |
|---|---|
| "scope this engagement", "what are we trying to decide" | `scoping-engagement` |
| "what's the org context", "who else matters" | `mapping-context` |
| "what systems / data do they have" | `inventorying-tech-data` |
| "map the process", "interview operators" | `discovering-processes` |
| "what are the opportunities", "list use cases" | `identifying-opportunities` |
| "score these", "rank by value" | `scoring-opportunities` |
| "build the roadmap", "sequence into waves" | `prioritizing-roadmap` |
| "write the use case briefs", "package for delivery" | `packaging-usecases` |
| "this opportunity has compliance/risk concerns" | `governance-risk-gate` |
| "review before delivery", "final check" | `deliverable-gate` |
| "draft the executive summary", "build the read-ahead", "produce the exec brief" | `building-executive-summary` |
| "build the HTML deliverable", "render the client deck", "package the final HTML" | `building-deliverable` |

## Engagement Folder Convention

Every engagement gets its own folder under `docs/engagements/<engagement-name>/`. The following files are created in sequence:

- `scope.md` — Phase 1
- `context.md` — Phase 2
- `tech-inventory.md` — Phase 3
- `process-map.md` — Phase 4
- `baselines.md` — Phase 4 (load-bearing — see Baseline & Value Hypothesis gate)
- `opportunities.md` — Phase 5
- `scored-opportunities.md` — Phase 6
- `roadmap.md` — Phase 7
- `usecase-briefs.md` — Phase 8
- `evidence-log.md` — running log of subagent reviews and gate clearances
- `executive-summary.md` — Phase 9 (standalone 1–2 page exec brief; produced after deliverable-gate clearance)
- `deliverable.html` — Phase 10 (self-contained client-ready HTML deliverable)

A phase's skill MUST verify the predecessor file(s) exist before producing any output.

## Chain to next skill

→ `scoping-engagement` (on any new engagement prompt)
