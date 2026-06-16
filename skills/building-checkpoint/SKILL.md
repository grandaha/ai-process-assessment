---
name: ai-process-assessment:building-checkpoint
description: Cross-cutting checkpoint — renders an interim, client-facing HTML stakeholder-validation artifact at a defined point in the methodology (Checkpoint 2 baseline is the only one wired). Parameterized by checkpoint id via the Checkpoint Registry. Synthesis renderers, not document converters — no new content; every figure traces to a prior-phase source.
---

# [CROSS-CUTTING] Building a Stakeholder Validation Checkpoint

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All `<name>` paths below use this value.
2. Check for `.sample-run.md` in the engagement folder — if present, this is a sample run; proceed with sample data, do not prompt for live stakeholders.
3. Resolve the checkpoint id (default and only wired value: `baseline`). Look up its row in the Checkpoint Registry below.
4. Verify the registry row's predecessor outputs exist (for `baseline`: both `processes/_index.md` and `model/baselines.json`). Halt with a clear message naming whichever file is missing if not.

## Role in the system

The methodology's only externally-facing artifact used to be the Phase 11 `deliverable.html`. A checkpoint is an **interim** client-facing artifact that lets stakeholders validate a foundational output before the engagement builds on top of it. Checkpoint 2 (`baseline`) validates the Phase 4 process maps and baseline metrics — the figures every downstream value calculation depends on.

This skill produces **NO new content**. Every figure traces to a named prior-phase source (`processes/PROC-NNN.md`, `model/baselines.json`). If a section is wrong, the fix is in the source file — correct it and re-run the renderer. Do not hand-edit the HTML to patch a source error.

It is **recommended-and-recorded**, not a hard gate: the keystone recommends invoking it at the insertion point, and its outcome is logged, but the next phase is not hard-blocked. A CLAUDE.md override may make a checkpoint mandatory for an engagement.

## Checkpoint Registry

Only the `baseline` row is active. The table format anticipates Checkpoints 1 and 3 (future cycles).

| id | Insert after | Source files | Renderer(s) | Output HTML | Outcome record | Route-back phase |
|---|---|---|---|---|---|---|
| `baseline` | Phase 4 | `processes/PROC-NNN.md`, `model/baselines.json`, `scope.md` (header only) | `section-renderer-checkpoint-baseline` | `checkpoints/checkpoint-baseline.html` | `checkpoints/CP-baseline-outcome.md` | Phase 4 (`ai-process-assessment:discovering-processes`) |

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

## Checkpoint shell

The checkpoint is a single-scroll HTML page assembled in the main context (the orchestrator generates content for none of it — section blocks come from renderers). The shell embeds a `<style>` block implementing the **same design-system classes documented in `ai-process-assessment:building-deliverable`** (reuse the identical class names and visual tokens so checkpoints look consistent with the final deliverable). Generate the `<style>` from that documented design system at assembly time; do not invent new class names.

Shell structure:

```
<head> [<style> design-system CSS] [smooth-scroll JS helper] </head>
<body>
  <nav class="sticky-nav">
    <a href="#baselines" onclick="navScrollTo('baselines'); return false;">Baselines</a>
    <a href="#validate"  onclick="navScrollTo('validate'); return false;">Validate</a>
  </nav>
  [masthead block — engagement name from scope.md, "Baseline Validation — Interim", date]

  #baselines   ← section-renderer-checkpoint-baseline block 1
  #validate    ← section-renderer-checkpoint-baseline block 2

  <div class="doc-footer"> [confidentiality, preparer, "INTERIM — for stakeholder validation", date] </div>
</body>
```

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
- **Changes Requested** → route to the registry's route-back phase (for `baseline`: Phase 4, `ai-process-assessment:discovering-processes`). Correct the source file(s) (`processes/PROC-NNN.md` / `model/baselines.json`) — **editing the source file is what refreshes the checkpoint, not the engine run**. Then regenerate the checkpoint from the corrected source(s). Finally, re-run `python -m engine.run <name>/` so downstream phases pick up the change. Append a new outcome record. Repeat until Confirmed.

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

→ `ai-process-assessment:identifying-opportunities` (on a Confirmed `baseline` checkpoint, Phase 5 proceeds. On Changes Requested, route back to `ai-process-assessment:discovering-processes` first.)

**Output rule:** Do NOT reproduce or echo the HTML content in this response. State the file path only.

**Session boundary:** Producing the checkpoint and recording its outcome completes this session. Instruct the user to start a fresh session for the route-back phase (on Changes Requested) or for Phase 5 (on Confirmed).
