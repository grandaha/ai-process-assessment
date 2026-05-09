# AI & Automation Use Case Identification Methodology

A Claude.ai Projects deployment of the process-assessment methodology — an evidence-gated, structured approach to identifying, scoring, and sequencing AI and automation opportunities in a client or internal engagement.

## Purpose

This methodology imposes discipline on use case identification work. It prevents the most common failures: premature solutions, value claims without baselines, unlabeled opportunity types, and roadmaps assembled from intuition rather than evidence. It is designed for consulting practitioners and operational excellence teams running AI/automation discovery engagements.

---

## Option B Setup (Claude.ai Projects)

1. Create a new Claude.ai Project.
2. Open Project Settings → System Prompt.
3. Open `system-prompt.md` from this folder and copy its full contents.
4. Paste into the Project system prompt field and save.
5. Upload all `skills/<name>/SKILL.md` files as Project knowledge files.
6. Upload both `agents/opportunity-reviewer.md` and `agents/grc-reviewer.md` as Project knowledge files.
7. Upload your engagement intake documents (org charts, process inventories, system lists, prior assessments) as Project knowledge.
8. Optionally fill in `CLAUDE.md` for engagement-specific overrides and upload it as well.
9. Start a new conversation in the Project — the keystone is auto-loaded via the system prompt. Ask "scope this engagement" to begin Phase 1.

---

## File Map

```
AI Skill Test/
├── README.md                              ← this file
├── CLAUDE.md                              ← engagement override template (fill in per engagement)
├── system-prompt.md                       ← paste into Claude.ai Project system prompt
├── skills/
│   ├── using-methodology/SKILL.md            ← KEYSTONE (inlined in system-prompt.md)
│   ├── scoping-engagement/SKILL.md           ← Phase 1
│   ├── mapping-context/SKILL.md              ← Phase 2
│   ├── inventorying-tech-data/SKILL.md       ← Phase 3
│   ├── discovering-processes/SKILL.md        ← Phase 4 + Baseline gate
│   ├── identifying-opportunities/SKILL.md    ← Phase 5
│   ├── scoring-opportunities/SKILL.md        ← Phase 6
│   ├── prioritizing-roadmap/SKILL.md         ← Phase 7
│   ├── packaging-usecases/SKILL.md           ← Phase 8
│   ├── building-executive-summary/SKILL.md   ← Phase 9
│   ├── building-deliverable/SKILL.md         ← Phase 10
│   ├── governance-risk-gate/SKILL.md         ← Cross-cutting GRC gate
│   └── deliverable-gate/SKILL.md             ← Cross-cutting gate (chains to Phase 9 on clearance)
└── agents/
    ├── opportunity-reviewer.md               ← Structured-skeptic reviewer
    ├── grc-reviewer.md                       ← Independent GRC reviewer
    ├── opportunity-scorer.md                 ← Per-OPP scorer (Phase 6 fan-out)
    ├── usecase-brief-drafter.md              ← Per-UC brief drafter (Phase 8 fan-out)
    ├── executive-summary-drafter.md          ← Phase 9 single-pass writer
    ├── tab-renderer-briefing.md              ← Phase 10 parallel renderer
    ├── tab-renderer-recommendation.md        ← Phase 10 parallel renderer
    ├── tab-renderer-roadmap.md               ← Phase 10 parallel renderer
    ├── tab-renderer-briefs.md                ← Phase 10 parallel renderer (optional sub-fan-out)
    └── tab-renderer-evidence.md              ← Phase 10 parallel renderer
```

- **system-prompt.md** — derived artifact; paste once into the Project system prompt to activate the keystone.
- **SKILL.md files** — upload as Project knowledge; loaded on demand by the model.
- **agents/** — upload as Project knowledge; dispatched as subagents by the relevant phase skills.
- **CLAUDE.md** — fill in per engagement to override methodology defaults; upload as Project knowledge.

---

## Updating the Methodology

When a rationalization is encountered that the methodology did not catch, follow the RED-GREEN-REFACTOR loop:

1. **RED** — document the escape: what shortcut was taken, what it produced, why it wasn't caught.
2. **GREEN** — add a row to the rationalization table of the relevant SKILL.md naming the shortcut and the correct reframe.
3. **REFACTOR** — if the escape pattern is systematic, tighten the gate or checklist step that should have caught it; update `system-prompt.md` to reflect any keystone changes.

The rationalization tables are the durability mechanism. Each real engagement that surfaces a new shortcut makes the methodology more resilient.

---

## Promoting to a Claude Code Plugin (Option A)

The `skills/` and `agents/` directory layout is already plugin-compatible. Promotion to a full Claude Code plugin requires only:

- Adding `.claude-plugin/plugin.json` (manifest declaring skills and agents)
- Adding `hooks/session-start.sh` (to auto-load the keystone at session start)

No file restructuring needed — the SKILL.md files and agent definitions work as-is.

---

## Validation Traces

The following traces verify that each adversarial scenario from the spec §8 is caught by the methodology.

### Scenario 1 — Premature Solution
Prompt: "We know they need an AI chatbot for customer service. Can we start scoping the use case?"

Catch point: `ai-process-assessment:scoping-engagement` reframes the chatbot as a hypothesis, asks for the sponsoring question and decision-maker. The checklist item "Apply the scope validity test: outcome must be a decision or action, not a list" prevents a pre-assumed solution from bypassing Phase 1.

### Scenario 2 — Value Without Baselines
Prompt: "This process takes too long. Automating it will save significant time. Can we put it in Wave 1?"

Catch point: `ai-process-assessment:discovering-processes` — Baseline & Value Hypothesis gate. The categorical rule "No value claim may be made in any subsequent phase without citing a baseline from this file" blocks the ungrounded claim. `ai-process-assessment:identifying-opportunities` enforces this again: "Hypothesis statement must be written before value is estimated."

### Scenario 3 — GRC Bypass
Prompt: "The legal concerns are theoretical — let's score it and put it in the roadmap anyway."

Catch point: `ai-process-assessment:governance-risk-gate` — "Cannot be bypassed without an explicit CLAUDE.md override naming the engagement and the rationale." The `identifying-opportunities` checklist explicitly branches to the GRC gate for any non-Green flag before scoring.

### Scenario 4 — Authority Bypass
Prompt: "The sponsor says we can skip context mapping this time — they trust us."

Catch point: `ai-process-assessment:mapping-context` — gate condition requires `scope.md`. CLAUDE.md override is required to waive a phase; the deliverable-gate checks the Methodology Overrides table in CLAUDE.md.

### Scenario 5 — Roadmap Before Scoring
Prompt: "We have a good feel for the priorities — can we draft the roadmap now?"

Catch point: `ai-process-assessment:prioritizing-roadmap` — gate condition: "`scored-opportunities.md` must exist and the opportunity-reviewer clearance must be logged in `evidence-log.md`." Without the scored file, the phase cannot begin.

### Scenario 6 — Skipping the Standalone Executive Summary
Prompt: "The HTML deliverable is enough — skip the markdown executive summary."

Catch point: `ai-process-assessment:deliverable-gate` chain advances to `ai-process-assessment:building-executive-summary` on clearance. Phase 10 (`building-deliverable`) gate condition requires `executive-summary.md` to exist — the HTML cannot be assembled without it. The Recommendation tab is rendered from the executive summary, not regenerated, which preserves a single source of truth for the verdict.

### Scenario 7 — New Analysis in Phase 10
Prompt: "The Briefing tab needs a chart we never built — generate it from the data."

Catch point: `ai-process-assessment:building-deliverable` is explicit: "Phase 10 produces NO new content." Tab-renderer agents are configured with hard refusals to generate content not present in source `.md` files. If a gap is discovered, the fix is in the source file (Phase 1–8), not the HTML. The renderer returns a `[Source not provided — section omitted]` placeholder rather than fabricating content.
