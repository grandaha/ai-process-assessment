---
name: ai-process-assessment:building-checkpoint
description: Cross-cutting checkpoint — renders an interim, client-facing HTML stakeholder-validation artifact at a defined point in the methodology (Checkpoints 1 `scope`, 2 `baseline`, and 3 `portfolio` are wired). Parameterized by checkpoint id via the Checkpoint Registry. Synthesis renderers, not document converters — no new content; every figure traces to a prior-phase source.
---

# [CROSS-CUTTING] Building a Stakeholder Validation Checkpoint

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All `<name>` paths below use this value.
2. Check for `.sample-run.md` in the engagement folder — if present, this is a sample run; proceed with sample data, do not prompt for live stakeholders.
3. Resolve the checkpoint id (wired values: `baseline`, `scope`, `portfolio`). Look up its row in the Checkpoint Registry below.
4. Verify the registry row's predecessor outputs exist. For `baseline`: both `processes/_index.md` and `model/baselines.json`. For `scope`: both `scope.md` and `context.md`. For `portfolio`: both `roadmap.md` and `scores/_index.md`. Halt with a clear message naming whichever file is missing if not.

**Session Start — resolve `engine_root`:** read `engine_root` (the absolute plugin root)
from this engagement's `.conductor.md` (`read_conductor`). Every engine command below is
`python3 <engine_root>/engine/run.py …`.

## Role in the system

The methodology's only externally-facing artifact used to be the Phase 11 `deliverable.html`. A checkpoint is an **interim** client-facing artifact that lets stakeholders validate a foundational output before the engagement builds on top of it. Checkpoint 2 (`baseline`) validates the Phase 4 process maps and baseline metrics — the figures every downstream value calculation depends on.

This skill produces **NO new content**. Every figure traces to a named prior-phase source (`processes/PROC-NNN.md`, `model/baselines.json`). If a section is wrong, the fix is in the source file — correct it and re-run the renderer. Do not hand-edit the HTML to patch a source error.

It is **recommended-and-recorded**, not a hard gate: the keystone recommends invoking it at the insertion point, and its outcome is logged, but the next phase is not hard-blocked. A CLAUDE.md override may make a checkpoint mandatory for an engagement.

## Checkpoint Registry

The `baseline` (Checkpoint 2), `scope` (Checkpoint 1), and `portfolio` (Checkpoint 3) rows are all active — the checkpoint pattern is complete.

| id | Insert after | Audience | Source files | Renderer(s) | Output HTML | Outcome record | Route-back phase |
|---|---|---|---|---|---|---|---|
| `baseline` | Phase 4 | Process owners + sponsor | `processes/PROC-NNN.md`, `model/baselines.json`, `scope.md` (header only) | `section-renderer-checkpoint-baseline` | `checkpoints/checkpoint-baseline.html` | `checkpoints/CP-baseline-outcome.md` | Phase 4 (`ai-process-assessment:discovering-processes`) |
| `process-validation` | Phase 4 (before `baseline`) | Process owner (one per process) | `processes/_index.md`, `processes/PROC-NNN.md` | *(deterministic — `state.process_review`, no LLM renderer)* | `checkpoints/process-validation/PROC-NNN.docx` (one per process) | `checkpoints/process-validation/CP-PROC-NNN-outcome.md` (one per process) | Phase 4 (`ai-process-assessment:discovering-processes`) for the affected process |
| `scope` | Phase 2 | Sponsor + decision-maker | `scope.md`, `context.md` | `section-renderer-checkpoint-scope` | `checkpoints/checkpoint-scope.html` | `checkpoints/CP-scope-outcome.md` | Phase 1 (`ai-process-assessment:scoping-engagement`) for scope-field changes; Phase 2 (`ai-process-assessment:mapping-context`) for context-field changes |
| `portfolio` | Phase 7 | Decision-maker + sponsor + IT lead | `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, `roadmap.md`, `scope.md` (header only) | `section-renderer-checkpoint-portfolio` | `checkpoints/checkpoint-portfolio.html` | `checkpoints/CP-portfolio-outcome.md` | Phase 6 (`ai-process-assessment:scoring-opportunities`) for score/ranking changes; Phase 7 (`ai-process-assessment:prioritizing-roadmap`) for wave/sequencing changes |

## Gate condition

The checkpoint's predecessor outputs exist (for `baseline`: `processes/_index.md` and `model/baselines.json`). Before producing the HTML, this skill MUST invoke `ai-process-assessment:deliverable-gate` in **Checkpoint Mode** for this checkpoint id (see that skill's "Checkpoint Mode" section). Proceed only on checkpoint clearance recorded in `evidence-log.md`.

## Orchestration

1. Resolve the registry row for the checkpoint id.
2. Invoke `ai-process-assessment:deliverable-gate` in Checkpoint Mode (`checkpoint=<id>`). On non-clearance, route to the failed dimension's owning phase; do not render.
3. Dispatch the registry's renderer agent(s), passing the engagement folder path and the checkpoint id only — not file contents. Each renderer reads the source files it needs and writes its section block(s) to `<name>/_staging/checkpoint-<id>/<section-id>.html`, returning a one-line confirmation. The orchestrator does NOT receive HTML content from renderers.
4. Verify each return carries no wrapper markup (`<html>`, `<body>`, `<style>`, `<script>`). Reject and re-dispatch any that do.
5. Assemble `<name>/checkpoints/checkpoint-<id>.html` from the checkpoint shell (below), interleaving the staged section blocks in the order the shell's sticky nav lists them.
6. Open the file and confirm: scroll works, sticky-nav links target the right anchors, all anchors present, no missing-class artifacts.
7. Prompt the user to record the stakeholder outcome (see "Recording the outcome").

## Deterministic checkpoint: `process-validation`

`process-validation` is a **per-process, owner-facing Word checkpoint** and does NOT use the
section-renderer / HTML-shell / Gate-B path above. It is a faithful transform of the process
maps (no model-authored content, so nothing to gate for fabrication). For this id only:

1. Run: `PYTHONPATH="<engine_root>" python3 -m state.process_review <name>`
   — writes one `checkpoints/process-validation/PROC-NNN.docx` and one
   `CP-PROC-NNN-outcome.md` (Outcome: Pending) per in-scope (`Ready`) process.
2. Tell the user a per-process Word review was generated for each process owner to confirm or
   mark up, and that **each owner's sign-off must be recorded** in its `CP-PROC-NNN-outcome.md`
   (`Confirmed` | `Changes requested` | `Waived (reason)`) before Phase 5.
3. On any `Changes requested`, route that process back to Phase 4, re-run, and regenerate
   (re-run the command — it preserves existing outcome files).

## Checkpoint shell

The checkpoint is a single-scroll HTML page assembled in the main context (the orchestrator generates content for none of it — section blocks come from renderers). **The shell's `<head><style>` is the vendored OSL design system, identical to the final deliverable: inline `assets/osl/brand.css` then `assets/osl/components.css` verbatim** (brand first, components second). Do not author or generate CSS, and do not invent class names — checkpoints use a subset of the same classes documented in `ai-process-assessment:building-deliverable`, so they look consistent with the final deliverable by construction.

Shell structure:

```
<head> [<style> assets/osl/brand.css + assets/osl/components.css, inlined verbatim] [smooth-scroll JS helper] </head>
<body>
  <nav class="sticky-nav">
    [per-checkpoint anchors — see mapping below]
  </nav>
  <header class="masthead">
    <!-- inline the full contents of assets/osl/logo-lockup.svg here, class="brand-logo" on <svg> -->
    <div class="eyebrow">Interim — for stakeholder validation</div>
    <h1>[checkpoint title]</h1>
  </header>

  [section blocks in anchor order — from the resolved checkpoint's renderer]

  <div class="doc-footer"> [confidentiality, preparer, "INTERIM — for stakeholder validation", date] </div>
</body>
```

The sticky nav and section blocks are per-checkpoint:

- `baseline` → nav `Baselines` (`#baselines`), `Validate` (`#validate`); masthead label "Baseline Validation — Interim"; blocks `#baselines`, `#validate` from `section-renderer-checkpoint-baseline`.
- `scope` → nav `Scope` (`#scope`), `Context` (`#context`), `Validate` (`#validate`); masthead label "Scope & Context Alignment — Interim"; blocks `#scope`, `#context`, `#validate` from `section-renderer-checkpoint-scope`.
- `portfolio` → nav `Portfolio` (`#portfolio`), `Scoring` (`#scoring`), `Roadmap` (`#roadmap`), `Validate` (`#validate`); masthead label "Portfolio & Roadmap Review — Interim"; blocks `#portfolio`, `#scoring`, `#roadmap`, `#validate` from `section-renderer-checkpoint-portfolio`.

Assemble the sticky nav with one `<a href="#anchor" onclick="navScrollTo('anchor'); return false;">Label</a>` per the resolved checkpoint's anchors, in block order, then the masthead, then the section blocks in order, then the `.doc-footer`.

The smooth-scroll helper is identical to the Phase 11 shell:

```js
function navScrollTo(anchorId) {
  var el = document.getElementById(anchorId);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

## Recording the outcome

After the HTML is produced, the checkpoint is taken to the stakeholders named in the registry's audience (for `baseline`: process owners + sponsor). Record the result in `<name>/checkpoints/CP-<id>-outcome.md` (for baseline: `checkpoints/CP-baseline-outcome.md`) by copying `templates/checkpoint-outcome-template.md` and filling it in — do not name the output after the template.

- **Confirmed** → downstream phases may rely on the validated output. The terminal deliverable-gate and final deliverable may cite the sign-off.
- **Changes Requested** → route to the registry's route-back phase (for `baseline`: Phase 4, `ai-process-assessment:discovering-processes`). Correct the source file(s) (`processes/PROC-NNN.md` / `model/baselines.json`) — **editing the source file is what refreshes the checkpoint, not the engine run**. Then regenerate the checkpoint from the corrected source(s). Finally, re-run `python3 <engine_root>/engine/run.py <name>/` so downstream phases pick up the change. Append a new outcome record. Repeat until Confirmed.
- **Changes Requested (`scope` checkpoint) — route per field:** a corrected **scope** field (sponsoring question, decision-maker, in/out-of-scope, success criteria, constraints) routes to Phase 1 (`ai-process-assessment:scoping-engagement`); a corrected **context** field (business model, strategic priorities, funding model) routes to Phase 2 (`ai-process-assessment:mapping-context`). A mixed outcome routes to both. Correct the source file(s) — editing the source is what refreshes the checkpoint — then regenerate `checkpoints/checkpoint-scope.html` and append a new outcome record. Repeat until Confirmed. (No engine run is involved at this checkpoint — there are no figures.)
- **Changes Requested (`portfolio` checkpoint) — route per field:** a corrected **score/ranking** field (composite score, dimension score, Build/Buy/Partner, type) routes to Phase 6 (`ai-process-assessment:scoring-opportunities`); a corrected **wave/sequencing** field (wave assignment, sequencing constraint, enabler, investment envelope) routes to Phase 7 (`ai-process-assessment:prioritizing-roadmap`). A mixed outcome routes to both. Correct the owning phase's source(s) and re-run that phase's assembly so the affected inputs re-stamp: a score/ranking change means re-running Phase 6 (`ai-process-assessment:scoring-opportunities`), whose assembly recomputes and re-stamps the composites into `scores/OPP-NNN.md`, `model/scores.json`, and `scores/_index.md`; a wave/sequencing change means re-running Phase 7 (`ai-process-assessment:prioritizing-roadmap`), which rewrites `roadmap.md` and `model/initiatives.json`. The engine is **not** run at this checkpoint — `python3 <engine_root>/engine/run.py` is a Phase 9 step. Then regenerate `checkpoints/checkpoint-portfolio.html` and append a new outcome record. Repeat until Confirmed.

## Phase checklist

- [ ] Read `scope.md`; resolve engagement folder; check `.sample-run.md`
- [ ] Resolve checkpoint id and registry row; verify predecessor output exists
- [ ] Invoke `deliverable-gate` in Checkpoint Mode; proceed only on clearance
- [ ] Dispatch the registry renderer(s) to `_staging/checkpoint-<id>/`
- [ ] Verify no wrapper markup in returns; assemble `checkpoints/checkpoint-<id>.html`
- [ ] Open and confirm scroll/nav/anchors/classes
- [ ] Record `checkpoints/CP-<id>-outcome.md`; route Changes Requested back to the route-back phase

## Rationalization Table

| Rationalization / Shortcut | Correct reframe |
|---|---|
| "It's interim — skip the gate." | The deliverable-gate fires before ANY external sharing. Checkpoint Mode runs the applicable dimensions over the files that exist — interim is exactly when validation prevents expensive rework. |
| "Generate the missing metric here — the source has a gap." | The checkpoint generates no content. A gap in `processes/PROC-NNN.md` / `model/baselines.json` renders as PENDING; fix the source and re-run the renderer. |
| "Hand-edit the HTML to fix a number." | Numbers come from source files. Edit the source, re-run the renderer, reassemble. |
| "Stakeholders confirmed verbally — no need to record it." | The outcome record is the audit trail the terminal gate and final deliverable cite. Record Confirmed/Changes Requested with names and items. |

## Chain to next skill

- `baseline`: on Confirmed → `ai-process-assessment:identifying-opportunities` (Phase 5); on Changes Requested → `ai-process-assessment:discovering-processes` (Phase 4).
- `scope`: on Confirmed → `ai-process-assessment:inventorying-tech-data` (Phase 3); on Changes Requested → `ai-process-assessment:scoping-engagement` (Phase 1, scope fields) / `ai-process-assessment:mapping-context` (Phase 2, context fields).
- `portfolio`: on Confirmed → `ai-process-assessment:packaging-usecases` (Phase 8); on Changes Requested → `ai-process-assessment:scoring-opportunities` (Phase 6, score fields) / `ai-process-assessment:prioritizing-roadmap` (Phase 7, sequencing fields).

**Output rule:** Do NOT reproduce or echo the HTML content in this response. State the file path only.

**Return to the Conductor:** Producing the checkpoint and recording its outcome completes this skill's work. The checkpoint **outcome** is a must-ask touchpoint — the Conductor stops for the stakeholder's decision. Once it is recorded, control returns to `ai-process-assessment:conducting-engagement`, which routes onward itself: on Changes Requested it re-drives the route-back phase above; on Confirmed it continues to the next phase. It isolates that phase by dispatching a subagent — it does **not** ask the user to restart a session.
