---
name: ai-process-assessment:evaluating-consistency
description: Cross-cutting confidence self-check — re-runs a judgment agent N times on identical inputs and measures run-to-run agreement, producing an evals/ confidence sidecar. Covers step-capability-tagger (Phase 4, per-step computed color) and opportunity-scorer (Phase 6, per-dimension / composite / B-B-P). Automatic and non-blocking; the user sees "confidence", never "eval".
---

# [CROSS-CUTTING] Confidence Self-Check (Consistency Evals)

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs. Do not ask the user for the path. Halt if scope.md is absent or the field is missing.
2. Resolve the **phase** and **target(s)**: `phase4` for `step-capability-tagger` (target = a PROC-id), `phase6` for `opportunity-scorer` (target = an OPP-id). The Conductor passes these; if invoked directly, infer from what exists (`processes/PROC-NNN.md` → phase4; `scores/OPP-NNN.md` → phase6).
3. Resolve `N` (default 5; a CLAUDE.md override may change it).

**Session Start — resolve `engine_root`:** read `engine_root` (the absolute plugin root) from this engagement's `.conductor.md` (`read_conductor`). The engine command below is `PYTHONPATH="<engine_root>" python3 -m state.evals <name> <phase> <target>`.

## Role in the system

The judgment agents are non-deterministic. This skill measures whether an agent gives the *same* answer when run repeatedly on the *same* inputs, and records the result as a **confidence** signal. It authors no analysis content — it only re-runs an existing agent and runs a deterministic metric. It is **automatic and non-blocking**: the Conductor invokes it; it never halts a phase. The result informs the checkpoint the human already reviews.

## Procedure — phase4 (step-capability-tagger), per process

1. Build N scratch copies of the process file with any existing capability table removed, so each run appends a fresh table:
   ```bash
   PYTHONPATH="<engine_root>" python3 -c "
   import re, sys
   from pathlib import Path
   eng, pid, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
   src = Path(eng)/'processes'/f'{pid}.md'
   base = re.split(r'\n\*\*Step capability:\*\*', src.read_text(encoding='utf-8'))[0].rstrip() + '\n'
   d = Path(eng)/'_staging'/'evals'/'phase4'/pid
   d.mkdir(parents=True, exist_ok=True)
   for k in range(1, n+1):
       (d/f'run-{k}.md').write_text(base, encoding='utf-8')
   print(f'wrote {n} run stubs to {d}')
   " <name> <PROC-id> <N>
   ```
2. **Dispatch the `step-capability-tagger` subagent N times in a single parallel tool-call batch.** Each subagent gets: the engagement folder, the process id, the path to its own `_staging/evals/phase4/<PROC-id>/run-K.md` (use this AS the PROC file it appends to — not the real `processes/PROC-NNN.md`), and the same evidence sources the Phase 4 tagging used. Each appends its `**Step capability:**` table to its own run file.
3. Run: `PYTHONPATH="<engine_root>" python3 -m state.evals <name> phase4 <PROC-id>`
4. Read `evals/<PROC-id>.evals.json`. Return a one-line summary: `<PROC-id>: <unstable_step_count> of <#steps> steps unstable across <N> runs`. Do NOT echo run content.

## Procedure — phase6 (opportunity-scorer), per opportunity

1. **Dispatch the `opportunity-scorer` subagent N times in a single parallel tool-call batch.** Each subagent gets identical inputs — the OPP-id, `opportunities/OPP-NNN.md`, `processes/PROC-NNN.md` for its process, and the relevant `tech-inventory.md` / `context.md` sections — and a distinct staging path `_staging/evals/phase6/<OPP-id>/run-K.md` to write to.
2. Run: `PYTHONPATH="<engine_root>" python3 -m state.evals <name> phase6 <OPP-id>`
3. Read `evals/<OPP-id>.evals.json`. Return a one-line summary: `<OPP-id>: <Stable|Unstable> across <N> runs`. Do NOT echo run content.

## AI-native rules

- The user never invokes this skill and never sees the words "eval", "consistency", or "variance". The Conductor runs it automatically; the human sees only **confidence** (a portfolio Confidence column, or a Conductor note about steps that need a second look).
- Computed color is internal. Tagger confidence is surfaced to the assessor only — never written into a client-facing document.
- Non-blocking: nothing here gates a phase. Unstable items are surfaced for attention, not used to halt.

## Output rule

Do NOT reproduce run content or the sidecar JSON in the response. State the summary line and the sidecar path only. Cleanup of `_staging/evals/<phase>/<target>` is optional and non-fatal.

## Return to the Conductor

Producing the sidecar completes this skill's work. Control returns to `ai-process-assessment:conducting-engagement`, which surfaces unstable tagger steps to the assessor (phase4) or relies on the portfolio checkpoint's Confidence column (phase6).
