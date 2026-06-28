---
name: ai-process-assessment:building-checkpoint
description: Cross-cutting checkpoint — renders an interim, client-facing stakeholder-validation artifact at a defined point in the methodology (all 8 ids wired: `scope`, `baseline`, `portfolio`, `process-validation`, `tech-data`, `opportunities`, `use-case-briefs`, `business-case`). Every checkpoint routes through the deterministic `.docx` renderer — no LLM-authored content, no HTML path. Synthesis renderers, not document converters — no new content; every figure traces to a prior-phase source.
---

# [CROSS-CUTTING] Building a Stakeholder Validation Checkpoint

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All `<name>` paths below use this value.
2. Check for `.sample-run.md` in the engagement folder — if present, this is a sample run; proceed with sample data, do not prompt for live stakeholders.
3. Resolve the checkpoint id (wired values: `baseline`, `scope`, `portfolio`, `process-validation`, `tech-data`, `opportunities`, `use-case-briefs`, `business-case`). Look up its row in the Checkpoint Registry below.
4. Verify the registry row's predecessor outputs exist. For `scope`: `scope.md`. For `baseline`: both `processes/_index.md` and `model/baselines.json`. For `portfolio`: both `roadmap.md` and `scores/_index.md`. For `process-validation`: `processes/_index.md`. For `tech-data`: `tech-inventory.md`. For `opportunities`: `opportunities/_index.md`. For `use-case-briefs`: `usecase-briefs/_index.md`. For `business-case`: `business-case.md`. Halt with a clear message naming whichever file is missing if not.

**Session Start — resolve `engine_root`:** read `engine_root` (the absolute plugin root)
from this engagement's `.conductor.md` (`read_conductor`). Every engine command below is
`PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>`.

## Role in the system

The methodology's only externally-facing artifact used to be the Phase 11 `deliverable.html`. A checkpoint is an **interim** client-facing artifact that lets stakeholders validate a foundational output before the engagement builds on top of it. Checkpoint 2 (`baseline`) validates the Phase 4 process maps and baseline metrics — the figures every downstream value calculation depends on.

This skill produces **NO new content**. Every figure traces to a named prior-phase source (`processes/PROC-NNN.md`, `model/baselines.json`). If a section is wrong, the fix is in the source file — correct it and re-run the renderer. Do not hand-edit the output to patch a source error.

It is **recommended-and-recorded**, not a hard gate: the keystone recommends invoking it at the insertion point, and its outcome is logged, but the next phase is not hard-blocked. A CLAUDE.md override may make a checkpoint mandatory for an engagement.

## Checkpoint Registry

All eight checkpoint ids are active — the checkpoint pattern is complete.

| id | Insert after | Audience | Source files | Output | Outcome record | Route-back phase |
|---|---|---|---|---|---|---|
| `scope` | Phase 2 | Sponsor + decision-maker | `scope.md`, `context.md` | `checkpoints/checkpoint-scope.docx` | `checkpoints/CP-scope-outcome.md` | Phase 1 (`ai-process-assessment:scoping-engagement`) for scope-field changes; Phase 2 (`ai-process-assessment:mapping-context`) for context-field changes |
| `baseline` | Phase 4 | Process owners + sponsor | `processes/PROC-NNN.md`, `model/baselines.json`, `scope.md` (header only) | `checkpoints/checkpoint-baseline.docx` | `checkpoints/CP-baseline-outcome.md` | Phase 4 (`ai-process-assessment:discovering-processes`) |
| `portfolio` | Phase 7 | Decision-maker + sponsor + IT lead | `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, `roadmap.md`, `scope.md` (header only) | `checkpoints/checkpoint-portfolio.docx` | `checkpoints/CP-portfolio-outcome.md` | Phase 6 (`ai-process-assessment:scoring-opportunities`) for score/ranking changes; Phase 7 (`ai-process-assessment:prioritizing-roadmap`) for wave/sequencing changes |
| `process-validation` | Phase 4 (before `baseline`) | Process owner (one per process) | `processes/_index.md`, `processes/PROC-NNN.md` | `checkpoints/process-validation/PROC-NNN.docx` (one per process) | `checkpoints/process-validation/CP-PROC-NNN-outcome.md` (one per process) | Phase 4 (`ai-process-assessment:discovering-processes`) for the affected process |
| `tech-data` | Phase 3 | IT lead + sponsor | `tech-inventory.md` | `checkpoints/checkpoint-tech-data.docx` | `checkpoints/CP-tech-data-outcome.md` | n/a — advisory review doc, opt-in, no gate |
| `opportunities` | Phase 5 | Sponsor + decision-maker | `opportunities/_index.md` | `checkpoints/checkpoint-opportunities.docx` | `checkpoints/CP-opportunities-outcome.md` | n/a — advisory review doc, opt-in, no gate |
| `use-case-briefs` | Phase 8 | Sponsor + process owners | `usecase-briefs/_index.md`, `usecase-briefs/UC-NNN.md` | `checkpoints/checkpoint-use-case-briefs.docx` | `checkpoints/CP-use-case-briefs-outcome.md` | n/a — advisory review doc, opt-in, no gate |
| `business-case` | Phase 9 | Decision-maker + sponsor | `business-case.md` | `checkpoints/checkpoint-business-case.docx` | `checkpoints/CP-business-case-outcome.md` | n/a — advisory review doc, opt-in, no gate |

## Orchestration

Every checkpoint id follows the same deterministic path — no LLM renderer, no HTML assembly.

1. Resolve the registry row for the checkpoint id and confirm predecessor files exist (Session Start step 4).
2. Run: `PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>`
   — writes the output file(s) listed in the registry row for this id.
3. Prompt the user to record the stakeholder outcome (see "Recording the outcome").

For `process-validation` specifically: the command writes one `checkpoints/process-validation/PROC-NNN.docx` and one `CP-PROC-NNN-outcome.md` (Outcome: Pending) per in-scope (`Ready`) process. Tell the user a per-process Word review was generated for each process owner to confirm or mark up, and that **each owner's sign-off must be recorded** in its `CP-PROC-NNN-outcome.md` (`Confirmed` | `Changes requested` | `Waived (reason)`) before Phase 5. On any `Changes requested`, route that process back to Phase 4, re-run, and regenerate (re-run the command — it preserves existing outcome files).

## Recording the outcome

After the output is produced, the checkpoint is taken to the stakeholders named in the registry's audience (for `baseline`: process owners + sponsor). Record the result in `<name>/checkpoints/CP-<id>-outcome.md` (for baseline: `checkpoints/CP-baseline-outcome.md`) by copying `templates/checkpoint-outcome-template.md` and filling it in — do not name the output after the template.

- **Confirmed** → downstream phases may rely on the validated output. The terminal deliverable-gate and final deliverable may cite the sign-off.
- **Changes Requested** → route to the registry's route-back phase (for `baseline`: Phase 4, `ai-process-assessment:discovering-processes`). Correct the source file(s) (`processes/PROC-NNN.md` / `model/baselines.json`) — **editing the source file is what refreshes the checkpoint, not the engine run**. Then regenerate the checkpoint by re-running the command from Orchestration. Finally, re-run `PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>` so downstream phases pick up the change. Append a new outcome record. Repeat until Confirmed.
- **Changes Requested (`scope` checkpoint) — route per field:** a corrected **scope** field (sponsoring question, decision-maker, in/out-of-scope, success criteria, constraints) routes to Phase 1 (`ai-process-assessment:scoping-engagement`); a corrected **context** field (business model, strategic priorities, funding model) routes to Phase 2 (`ai-process-assessment:mapping-context`). A mixed outcome routes to both. Correct the source file(s) — editing the source is what refreshes the checkpoint — then regenerate `checkpoints/checkpoint-scope.docx` by re-running the command and append a new outcome record. Repeat until Confirmed. (No engine run is involved at this checkpoint — there are no figures.)
- **Changes Requested (`portfolio` checkpoint) — route per field:** a corrected **score/ranking** field (composite score, dimension score, Build/Buy/Partner, type) routes to Phase 6 (`ai-process-assessment:scoring-opportunities`); a corrected **wave/sequencing** field (wave assignment, sequencing constraint, enabler, investment envelope) routes to Phase 7 (`ai-process-assessment:prioritizing-roadmap`). A mixed outcome routes to both. Correct the owning phase's source(s) and re-run that phase's assembly so the affected inputs re-stamp: a score/ranking change means re-running Phase 6 (`ai-process-assessment:scoring-opportunities`), whose assembly recomputes and re-stamps the composites into `scores/OPP-NNN.md`, `model/scores.json`, and `scores/_index.md`; a wave/sequencing change means re-running Phase 7 (`ai-process-assessment:prioritizing-roadmap`), which rewrites `roadmap.md` and `model/initiatives.json`. The engine is **not** run at this checkpoint — `PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>` is the only command. Then regenerate `checkpoints/checkpoint-portfolio.docx` and append a new outcome record. Repeat until Confirmed.

## Phase checklist

- [ ] Read `scope.md`; resolve engagement folder; check `.sample-run.md`
- [ ] Resolve checkpoint id and registry row; verify predecessor output exists
- [ ] Run: `PYTHONPATH="<engine_root>" python3 -m state.checkpoint_doc <name> <id>`
- [ ] Record outcome file; route Changes Requested back to the route-back phase

## Rationalization Table

| Rationalization / Shortcut | Correct reframe |
|---|---|
| "It's interim — skip the renderer." | Every checkpoint runs the same deterministic command. No content is authored by the LLM — figures trace to source files. |
| "Generate the missing metric here — the source has a gap." | The checkpoint generates no content. A gap in `processes/PROC-NNN.md` / `model/baselines.json` renders as PENDING; fix the source and re-run the renderer. |
| "Hand-edit the output to fix a number." | Numbers come from source files. Edit the source and re-run `python3 -m state.checkpoint_doc`. |
| "Stakeholders confirmed verbally — no need to record it." | The outcome record is the audit trail the terminal gate and final deliverable cite. Record Confirmed/Changes Requested with names and items. |

## Chain to next skill

- `baseline`: on Confirmed → `ai-process-assessment:identifying-opportunities` (Phase 5); on Changes Requested → `ai-process-assessment:discovering-processes` (Phase 4).
- `scope`: on Confirmed → `ai-process-assessment:inventorying-tech-data` (Phase 3); on Changes Requested → `ai-process-assessment:scoping-engagement` (Phase 1, scope fields) / `ai-process-assessment:mapping-context` (Phase 2, context fields).
- `portfolio`: on Confirmed → `ai-process-assessment:packaging-usecases` (Phase 8); on Changes Requested → `ai-process-assessment:scoring-opportunities` (Phase 6, score fields) / `ai-process-assessment:prioritizing-roadmap` (Phase 7, sequencing fields).
- `process-validation`: per-process sign-off is recorded in `checkpoints/process-validation/CP-PROC-NNN-outcome.md`; on all processes Confirmed → return to `ai-process-assessment:conducting-engagement` (Conductor continues to Phase 5); on any Changes Requested → route that process back to `ai-process-assessment:discovering-processes` (Phase 4), re-run, regenerate, then re-record.
- `tech-data` / `opportunities` / `use-case-briefs` / `business-case`: advisory review docs offered at Phases 3 / 5 / 8 / 9 (opt-in). Record the outcome in `CP-<id>-outcome.md` if the client signs off. No route-back, nothing blocks — declining is fine.

**Output rule:** Do NOT reproduce or echo the document content in this response. State the file path only.

**Return to the Conductor:** Producing the checkpoint and recording its outcome completes this skill's work. The checkpoint **outcome** is a must-ask touchpoint — the Conductor stops for the stakeholder's decision. Once it is recorded, control returns to `ai-process-assessment:conducting-engagement`, which routes onward itself: on Changes Requested it re-drives the route-back phase above; on Confirmed it continues to the next phase. It isolates that phase by dispatching a subagent — it does **not** ask the user to restart a session.
