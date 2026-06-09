---
name: ai-process-assessment:inventorying-tech-data
description: Phase 3 — catalogs systems, APIs, datasets, foundational enablers, IT governance, build/buy/partner posture, shadow IT. Saves tech-inventory.md.
---

# Phase 3: Inventorying Technology and Data

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `context.md` and confirm it exists.
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently, extract the `intake_root` field from its YAML frontmatter, and note the Phase Intake Map. At the live-interview step in the Workflow below, read `<intake_root>/systems-and-data.md` instead of interviewing a live IT stakeholder.

Gate condition: `context.md` must be present before proceeding.

## Role in the system

Feasibility scoring and sourcing recommendations are downstream of what actually exists. This phase produces an honest snapshot of systems, integrations, data, and enabler gaps. Without this, every later feasibility claim is speculation.

## Gate condition

`context.md` must exist. This skill creates `tech-inventory.md`.

## Phase checklist

- [ ] Catalog systems of record and systems of engagement within scope
- [ ] Map APIs and integrations available between those systems
- [ ] Catalog data assets: location, ownership, quality, refresh cadence
- [ ] Identify foundational enabler gaps (identity, observability, MLOps, etc.)
- [ ] Document IT governance posture: change control, security review, deployment gates
- [ ] Capture build/buy/partner posture for AI/automation
- [ ] Surface shadow IT — what teams are using outside official sanction
- [ ] Save to `docs/engagements/<engagement>/tech-inventory.md`
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:discovering-processes`

## Key outputs (saved to tech-inventory.md)

| Field | Content |
|---|---|
| System inventory | Systems of record / engagement within scope; ownership; lifecycle stage |
| API / integration map | Available integrations, their reliability, and known gaps |
| Data asset catalog | Datasets — location, owner, quality, refresh cadence, sensitivity |
| Foundational enabler gaps | Missing prerequisites: identity, logging, MLOps, monitoring, governance tooling |
| IT governance posture | Change control, security review, deployment process; speed and rigor |
| Build/Buy/Partner posture | Org's stated and observed preferences; precedents that shape future choices |
| Shadow IT | Unsanctioned tools / data flows in active use within scope |

## Workflow

1. Confirm `context.md` exists. If not, return to Phase 2.
2. Pull system inventory from CMDB or equivalent; verify against operator interviews.
3. Map only the integrations relevant to in-scope processes.
4. For data assets, capture quality honestly — "we have customer data" is not the same as "the customer table is reconciled nightly with 99.5% completeness."
5. Identify enabler gaps that would block any AI/automation: no identity = no agent; no observability = no production AI.
6. Surface shadow IT — operators will mention tools nobody else acknowledges.
7. Save `tech-inventory.md` and chain forward.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "We can use the official systems list." | Official lists miss shadow IT, undocumented integrations, and informal data flows where the actual work happens. |
| "Data quality is good enough." | "Good enough" without metrics is a guess. Capture refresh cadence, completeness, and ownership. |
| "Foundational enablers can be built into Wave 1." | Building enablers concurrent with Wave 1 use cases is how programs collapse. Surface gaps now so they can sequence as enablers. |
| "Build/Buy/Partner is a per-opportunity question." | Org-level posture (capex stance, prior burns, partner relationships) shapes every per-opportunity decision. Capture once. |
| "Shadow IT isn't the scope." | Shadow IT is where the real process lives. Ignoring it produces a roadmap that automates the official process while the actual one stays manual. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `tech-inventory.md` in this response. State the file path only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: systems cataloged (count), integration gaps, data quality flags, IT governance posture, any shadow IT surfaced.

**Session boundary:** After the user approves `tech-inventory.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:discovering-processes` to begin Phase 4. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:discovering-processes` (after `tech-inventory.md` is saved)
