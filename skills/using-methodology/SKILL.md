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
| 1 | `ai-process-assessment:scoping-engagement` | Front gate — sponsoring question, decision-maker, scope | New engagement prompt | `scope.md` |
| 2 | `ai-process-assessment:mapping-context` | Org / strategic / political context | `scope.md` exists | `context.md` |
| 3 | `ai-process-assessment:inventorying-tech-data` | Systems, APIs, data, enablers | `context.md` exists | `tech-inventory.md` |
| 4 | `ai-process-assessment:discovering-processes` | Four-round interviews, baseline metrics | `tech-inventory.md` exists | `process-map.md`, `baselines.md` |
| 5 | `ai-process-assessment:identifying-opportunities` | Typed opportunity log (OPP-NNN) | `process-map.md` and `baselines.md` exist | `opportunities/` (folder: `_index.md` + `OPP-NNN.md` per opportunity) |
| 6 | `ai-process-assessment:scoring-opportunities` | 6-dimension rubric + Build/Buy/Partner | `opportunities/_index.md` exists; GRC cleared for any flagged | `scores/` (folder: `_index.md` + `OPP-NNN.md` per opportunity) |
| 7 | `ai-process-assessment:prioritizing-roadmap` | Foundation/Scale/Optimize sequencing | `scores/_index.md` saved; reviewer cleared | `roadmap.md` |
| 8 | `ai-process-assessment:packaging-usecases` | UC-NNN briefs (SCRA structure) | `roadmap.md` saved; reviewer cleared | `usecase-briefs/` (folder: `_index.md` + `UC-NNN.md` per opportunity) |
| 8.5 | `ai-process-assessment:collecting-cost-actuals` | Cost data collection from stakeholders — labor rates, implementation hours, vendor quotes, IT estimates | `usecase-briefs/_index.md` exists | `cost-actuals.md` |
| 9 | `ai-process-assessment:building-business-case` | Wave 1 ROM business case | `cost-actuals.md` exists | `business-case.md` |
| 10 | `ai-process-assessment:building-executive-summary` | Standalone 1–2 page executive summary | `ai-process-assessment:deliverable-gate` cleared | `executive-summary.md`; reviewer clearance in `evidence-log.md` |
| 11 | `ai-process-assessment:building-deliverable` | Self-contained client-ready HTML deliverable | `executive-summary.md` exists | `deliverable.html` |
| Gate A | `ai-process-assessment:governance-risk-gate` | GRC review of flagged opportunities | Any non-Green GRC flag in `opportunities/_index.md` | `grc/` folder (`_index.md` + `OPP-NNN.md` per flagged opportunity) |
| Gate B | `ai-process-assessment:deliverable-gate` | Final integrity checklist | Before any external sharing | Clearance recorded in `evidence-log.md` |

## Opportunity Type Taxonomy

| Type | Definition |
|---|---|
| RPA | Deterministic, rules-based execution of structured tasks across digital systems. No judgment required. |
| AI Augmentation | AI assists a human in the loop — human retains decision authority. Examples: drafting, summarization, recommendation. |
| AI Automation | AI executes end-to-end without per-instance human review for bounded, well-specified tasks with measurable accuracy thresholds. |
| Chain Automation | Two or more consecutive AI-executed steps forming an uninterrupted sequence. A human verifies only the final output; intermediate checkpoints are eliminated. Value source is checkpoint elimination, not individual step acceleration. |
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
| "This step doesn't look like an AI candidate — let's skip it." | Evaluate every step in the context of its neighbors, not in isolation. A step where humans have comparative advantage on its own may belong in a chain because appending it eliminates a human verification checkpoint. Step-by-step comparative advantage logic fails when chains are present. |

## Routing Logic

- On any new engagement prompt → invoke `ai-process-assessment:scoping-engagement`.
- After each phase's output file is saved → invoke the next skill in the chain.
- For phases that carry a `## Subagent Dispatch` section (discovering-processes, identifying-opportunities, scoring-opportunities, prioritizing-roadmap) → offload the per-item or independent-review work to the named subagents per that section; keep gate decisions and cross-item judgments in the main context.
- If any opportunity in `opportunities/_index.md` has a non-Green GRC flag → invoke `ai-process-assessment:governance-risk-gate` before scoring.
- Before any external sharing of any output → invoke `ai-process-assessment:deliverable-gate`.
- After `usecase-briefs/_index.md` is saved and reviewer cleared → invoke `ai-process-assessment:collecting-cost-actuals` (Phase 8.5) before Phase 9.
- After `ai-process-assessment:deliverable-gate` clearance → invoke `ai-process-assessment:building-executive-summary` (Phase 10).
- After `executive-summary.md` is saved → invoke `ai-process-assessment:building-deliverable` (Phase 11).
- If CLAUDE.md declares an override for an engagement → honor it, and note the deviation for the deliverable gate's audit.

## When-to-Invoke Reference

| Trigger phrase / situation | Skill to invoke |
|---|---|
| "scope this engagement", "what are we trying to decide" | `ai-process-assessment:scoping-engagement` |
| "what's the org context", "who else matters" | `ai-process-assessment:mapping-context` |
| "what systems / data do they have" | `ai-process-assessment:inventorying-tech-data` |
| "map the process", "interview operators" | `ai-process-assessment:discovering-processes` |
| "what are the opportunities", "list use cases" | `ai-process-assessment:identifying-opportunities` |
| "score these", "rank by value" | `ai-process-assessment:scoring-opportunities` |
| "build the roadmap", "sequence into waves" | `ai-process-assessment:prioritizing-roadmap` |
| "write the use case briefs", "package for delivery" | `ai-process-assessment:packaging-usecases` |
| "this opportunity has compliance/risk concerns" | `ai-process-assessment:governance-risk-gate` |
| "review before delivery", "final check" | `ai-process-assessment:deliverable-gate` |
| "draft the executive summary", "build the read-ahead", "produce the exec brief" | `ai-process-assessment:building-executive-summary` |
| "build the HTML deliverable", "render the client deck", "package the final HTML" | `ai-process-assessment:building-deliverable` |
| "collect cost data", "get vendor quotes", "what do we need to price this", "gather the estimates" | `ai-process-assessment:collecting-cost-actuals` |
| "build the business case", "what does Wave 1 cost", "estimate the investment" | `ai-process-assessment:building-business-case` |

## Engagement Folder Convention

Every engagement gets its own folder under `docs/engagements/<engagement-name>/`. The following files are created in sequence:

- `scope.md` — Phase 1
- `context.md` — Phase 2
- `tech-inventory.md` — Phase 3
- `process-map.md` — Phase 4
- `baselines.md` — Phase 4 (load-bearing — see Baseline & Value Hypothesis gate)
- `opportunities/` — Phase 5 (folder: `_index.md` + `OPP-NNN.md` per opportunity)
- `grc/` — GRC Gate (folder: `_index.md` + `OPP-NNN.md` per flagged opportunity; only present when Gate A ran)
- `scores/` — Phase 6 (folder: `_index.md` + `OPP-NNN.md` per opportunity)
- `roadmap.md` — Phase 7
- `usecase-briefs/` — Phase 8 (folder: `_index.md` master index + `UC-NNN.md` per opportunity, one file per UC across all three waves)
- `cost-actuals.md` — Phase 8.5 (labor rates, implementation hours, vendor quotes, IT integration estimates — required before Phase 9)
- `business-case.md` — Phase 9
- `evidence-log.md` — running log of subagent reviews and gate clearances
- `executive-summary.md` — Phase 10 (standalone 1–2 page exec brief; produced after deliverable-gate clearance)
- `deliverable.html` — Phase 11 (self-contained client-ready HTML deliverable)

A phase's skill MUST verify the predecessor file(s) exist before producing any output.

## Chain to next skill

→ `ai-process-assessment:scoping-engagement` (on any new engagement prompt)
