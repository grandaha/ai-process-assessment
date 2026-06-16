---
name: ai-process-assessment:deliverable-gate
description: Cross-cutting terminal gate — runs four-dimension integrity checklist (evidence, logic, completeness, communication) before any external sharing. Cannot be bypassed.
---

# [CROSS-CUTTING] Deliverable Gate

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read all phase output files for integrity check:
   `scope.md`, `context.md`, `tech-inventory.md`, `processes/_index.md`,
   `opportunities/_index.md`, `scores/_index.md`, `roadmap.md`,
   `usecase-briefs/_index.md`, `cost-actuals.md`, `business-case.md`

Gate condition: All phase output files must exist before the integrity check can proceed.

## Role in the system

Fires before ANY external sharing of outputs, regardless of phase. The terminal gate. Cannot be bypassed without explicit CLAUDE.md override.

## Gate condition

Any output (interim or final) is about to be shared with anyone outside the engagement team.

## Five Integrity Dimensions

- **Evidence integrity** — every value claim in the deliverable traces to a citation in `processes/PROC-NNN.md` baseline sections. No figure floats free.
- **Logic integrity** — the chain process → opportunity → score → roadmap → brief has no gaps. A reader can walk from any brief back to the baseline that grounds it.
- **Completeness** — every in-scope domain from `scope.md` is addressed. Gaps are acknowledged, not hidden.
- **Communication readiness** — the portfolio view (waves, value, sequencing) is present and coherent in `roadmap.md` and `scores/_index.md`, so the executive summary (Phase 10) can lead with it rather than with methodology narrative. Gate B runs *before* Phase 10, so `executive-summary.md` does not yet exist and is not inspected here — this dimension confirms the raw material to lead with the portfolio view is in place.
- **Determinism integrity** — every numeric figure in every markdown deliverable equals its source in `model/results.json`. No number is computed in prose. A figure that does not match `results.json` (or that has no `results.json` source) blocks the gate. PENDING values must appear as PENDING, never as an invented number.

## Checkpoint Mode (interim validation)

When invoked by `ai-process-assessment:building-checkpoint` with a `checkpoint=<id>`, the gate runs in **Checkpoint Mode**: it inspects only the files that exist at that point in the methodology and treats not-yet-produced phase files as **legitimately absent, not failures**. The terminal gate (invoked with no checkpoint id) is unaffected and still requires all phase files per Session Start.

For `checkpoint=baseline` (after Phase 4), read only: `scope.md`, `processes/_index.md`, the relevant `processes/PROC-NNN.md` files, and `model/baselines.json`. If `model/baselines.json` is missing, the checkpoint does **NOT** clear — route back to Phase 4 for remediation; a missing baseline must not silently pass. Run only the applicable dimensions:

- **Evidence integrity** — every figure to be rendered traces to a `processes/PROC-NNN.md` / `model/baselines.json` source. No figure floats free.
- **Determinism integrity** — every numeric figure equals its `model/baselines.json` source; PENDING renders as PENDING, never an invented number.
- **Completeness** — every in-scope process domain from `scope.md` that Phase 4 should have covered is present in `processes/`, or its gap is acknowledged.

Dimensions that require later phases (Logic chain through scores/roadmap/briefs, Business Case, Communication readiness) are **not applicable** at this checkpoint and are skipped — note them as "deferred to later checkpoints / terminal gate." Do **not** dispatch the `opportunity-reviewer` subagent in Checkpoint Mode (opportunities do not exist yet); checkpoint clearance is a lighter, scoped pass.

Record clearance as a distinct checkpoint entry in `evidence-log.md`, e.g. `Checkpoint baseline — cleared (Evidence, Determinism, Completeness)`. On non-clearance, route to the dimension's owning phase (for `baseline`: Phase 4) for remediation before the checkpoint renders.

For `checkpoint=scope` (after Phase 2), read only: `scope.md` and `context.md`. Run only the applicable dimensions:

- **Completeness** — every in-scope domain named in `scope.md` is present and legible in the rendered scope view, and the scope is internally coherent (sponsoring question ↔ success criteria ↔ in/out-of-scope align).
- **Evidence integrity** — every claim to be rendered traces to a `scope.md` / `context.md` source.

**Determinism integrity is not applicable** at the `scope` checkpoint — no numeric figures exist yet; state this rather than checking it. Record clearance as `Checkpoint scope — cleared (Completeness, Evidence)`. On non-clearance, route a scope-field gap (sponsoring question, decision-maker, in/out-of-scope, success criteria, constraints) to Phase 1 and a context-field gap (business model, strategic priorities, funding model) to Phase 2 before the checkpoint renders.

## Phase checklist

- [ ] Run Evidence integrity check — sample value claims, walk each to its baseline
- [ ] Run Logic integrity check — pick a Wave 1 brief, trace process → opportunity → score → roadmap → brief
- [ ] Run Completeness check — cross-reference scoped domains against deliverable coverage
- [ ] Run Business Case integrity check — confirm `business-case.md` ROM label is present; every figure has a stated assumption; Buy/Partner initiatives flag missing vendor quotes; one-time and recurring costs are separated
- [ ] Run Communication readiness check — confirm the portfolio view (waves, value, sequencing) is present and lead-able from `roadmap.md` + `scores/_index.md` (the executive summary does not exist yet — it is written in Phase 10, after this gate clears)
- [ ] Run Determinism integrity check — for each numeric figure in `business-case.md`, `executive-summary.md` (if present), and `roadmap.md`, confirm it equals the corresponding `model/results.json` value; block on any mismatch or unsourced number
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
| "The model's arithmetic looks right — no need to check results.json." | LLM prose arithmetic is non-deterministic and compounds. The engine is the only source of truth; the gate verifies equality, it does not re-trust the model. |

## Chain to next skill

**Output rule:** Do NOT reproduce the contents of any phase file in this response. State clearance status, critical finding count, and file paths only.

→ `ai-process-assessment:building-executive-summary` (on clearance — Phase 10 produces the standalone executive summary).

On non-clearance, route to the skill responsible for the failed dimension. Phase 10 may not begin until clearance is recorded in `evidence-log.md`.

**Session boundary:** After clearance is recorded in `evidence-log.md`, this gate session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:building-executive-summary` to begin Phase 10. Do not continue methodology work in this session.
