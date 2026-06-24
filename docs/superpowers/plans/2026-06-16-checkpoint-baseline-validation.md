# Checkpoint 2 — Process & Baseline Validation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the methodology's first stakeholder validation checkpoint — a parameterized `building-checkpoint` skill that renders an interim client-facing HTML baseline-validation artifact after Phase 4, gated by a scoped (checkpoint-mode) deliverable-gate, with a recorded validate→revise→regenerate feedback loop.

**Architecture:** All deliverables are **methodology markdown** (a new skill, a new section-renderer agent, an outcome template, plus edits to the deliverable-gate, the keystone, and system-prompt.md). No HTML is rendered at build time — the skill renders HTML later when a consultant runs it on an engagement, mirroring the existing Phase 11 pattern. The new skill is registered via the **allowlist** (a cross-cutting non-phase skill, like `running-sample-engagement`), NOT the Phase Map — this keeps the linear chain and the 14-row phase map intact.

**Tech Stack:** Markdown skills/agents; Python 3.12 + pytest for the registration/guard tests (`tests/methodology_model.py` parses the keystone + skills + agents).

**Spec:** `docs/superpowers/specs/2026-06-16-checkpoint-baseline-validation-design.md`
**Issue:** grandaha/ai-process-assessment#49

---

## Critical constraints (verified against the test suite — do not violate)

- **Never write `baselines.md` or `process-map.md`** anywhere in `skills/` or `agents/`. `tests/test_guards.py::test_no_retired_monolithic_file_references` fails on those tokens. Use **`model/baselines.json`** and **`processes/PROC-NNN.md`** only. (`.json` is safe; the retired-monolith regex only matches `.md`.)
- **The new skill goes in the ALLOWLIST, not the Phase Map.** Adding a Phase-Map row would force it into the linear chain (`test_chain.py` requires every phase-skill be visited) and break `test_manifest.py` (phase count pinned to 14). Register it in `ALLOWLIST_NON_PHASE` instead.
- **Any keystone edit must be re-mirrored into `system-prompt.md`** — `test_guards.py::test_system_prompt_mirrors_keystone` asserts the keystone body (minus frontmatter) appears verbatim in `system-prompt.md`.
- **The deliverable-gate edit must stay backward-compatible and preserve its guards:** its `## Session Start` block must NOT mention `executive-summary.md` (`test_deliverable_gate_does_not_read_exec_summary`), and the file must keep `results.json` + "determinism" (`test_deliverable_gate_has_determinism_check`). The terminal (no-checkpoint-id) path must behave exactly as today.
- **No number is computed in prose** (methodology-wide rule). The renderer cites `model/baselines.json` / `processes/PROC-NNN.md` verbatim; absent metrics render as **PENDING**.
- Markdown/methodology change → the PR is **human-merged** (the auto-review loop routes markdown away from auto-merge).

## File structure

- **Create** `skills/building-checkpoint/SKILL.md` — the parameterized checkpoint orchestrator skill (registry-driven; only `baseline` wired).
- **Create** `agents/section-renderer-checkpoint-baseline.md` — data-driven renderer emitting `#baselines` + `#validate` blocks.
- **Create** `templates/checkpoint-outcome-template.md` — the feedback-loop record template.
- **Modify** `skills/deliverable-gate/SKILL.md` — add an additive "Checkpoint Mode" section.
- **Modify** `skills/using-methodology/SKILL.md` — add `checkpoints/` to the Engagement Folder Convention; add routing + when-to-invoke prose. No Phase-Map row.
- **Modify** `system-prompt.md` — re-mirror the keystone body.
- **Modify** `tests/test_skills.py` — allowlist the new skill; bump count 17 → 18.

---

## Task 1: Register the new skill in the tests (RED)

**Files:**
- Modify: `tests/test_skills.py`

- [ ] **Step 1: Add the skill to the allow-list and bump the count**

In `tests/test_skills.py`, update the allow-list block:

```python
# Skills intentionally absent from the Phase Map:
#   using-methodology     — the keystone (carries the map itself)
#   running-sample-engagement — meta entry point for the bundled demo
#   generating-sample-intake  — demo-support: synthesizes sample intake files
#   building-checkpoint   — cross-cutting stakeholder validation checkpoint (interim)
ALLOWLIST_NON_PHASE = {
    "ai-process-assessment:using-methodology",
    "ai-process-assessment:running-sample-engagement",
    "ai-process-assessment:generating-sample-intake",
    "ai-process-assessment:building-checkpoint",
}
```

And bump the count assertion:

```python
def test_skill_count(methodology):
    # 14 phase skills + 4 allow-listed non-phase skills.
    assert len(methodology.skills) == 18
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/test_skills.py -q`
Expected: FAIL — `test_skill_count` asserts 18 but only 17 skill dirs exist; the allow-list now references a skill with no directory.

- [ ] **Step 3: Commit**

```bash
git add tests/test_skills.py
git commit -m "test: register building-checkpoint skill (allow-list + count 17->18)"
```

---

## Task 2: Create the `building-checkpoint` skill (GREEN for Task 1)

**Files:**
- Create: `skills/building-checkpoint/SKILL.md`

- [ ] **Step 1: Write the skill file**

Create `skills/building-checkpoint/SKILL.md` with exactly this content:

```markdown
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
4. Verify the registry row's predecessor output exists (for `baseline`: `processes/_index.md`). Halt with a clear message naming the missing file if not.

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

The checkpoint's predecessor output exists (for `baseline`: `processes/_index.md`). Before producing the HTML, this skill MUST invoke `ai-process-assessment:deliverable-gate` in **Checkpoint Mode** for this checkpoint id (see that skill's "Checkpoint Mode" section). Proceed only on checkpoint clearance recorded in `evidence-log.md`.

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

\`\`\`
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
\`\`\`

The smooth-scroll helper is identical to the Phase 11 shell:

\`\`\`js
function navScrollTo(anchorId) {
  var el = document.getElementById(anchorId);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
\`\`\`

## Recording the outcome

After the HTML is produced, the checkpoint is taken to the stakeholders named in the registry's audience (for `baseline`: process owners + sponsor). Record the result in `<name>/checkpoints/CP-<id>-outcome.md` using `templates/checkpoint-outcome-template.md`.

- **Confirmed** → downstream phases may rely on the validated output. The terminal deliverable-gate and final deliverable may cite the sign-off.
- **Changes Requested** → route to the registry's route-back phase (for `baseline`: Phase 4, `ai-process-assessment:discovering-processes`). Apply the corrections to `processes/PROC-NNN.md` / `model/baselines.json`, **re-run the engine** (`python -m engine.run <name>/`) if any number changed, regenerate the checkpoint, and append a new outcome record. Repeat until Confirmed.

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
```

- [ ] **Step 2: Run the skill-registration tests**

Run: `.venv/bin/pytest tests/test_skills.py tests/test_chain.py tests/test_manifest.py -q`
Expected: PASS. (`test_skill_count` now sees 18; `building-checkpoint` is a non-orphan via the allow-list; it has a resolvable `→ identifying-opportunities` chain target; phase map still 14 rows.)

- [ ] **Step 3: Run the guard tests (retired-file + mirror not yet touched)**

Run: `.venv/bin/pytest tests/test_guards.py -q`
Expected: PASS — confirm the new skill contains no `baselines.md` / `process-map.md` tokens. (It references `model/baselines.json` and `processes/PROC-NNN.md` only.)

- [ ] **Step 4: Commit**

```bash
git add skills/building-checkpoint/SKILL.md
git commit -m "feat(checkpoint): building-checkpoint skill (registry-driven; baseline wired)"
```

---

## Task 3: Create the baseline renderer agent

**Files:**
- Create: `agents/section-renderer-checkpoint-baseline.md`

- [ ] **Step 1: Write the agent file**

Create `agents/section-renderer-checkpoint-baseline.md` with exactly this content:

```markdown
---
name: section-renderer-checkpoint-baseline
description: Checkpoint renderer — reads processes/PROC-NNN.md files and model/baselines.json and produces two section blocks for the baseline-validation checkpoint, the #baselines metrics view and the #validate confirm-or-correct view. Data-driven synthesis renderer — renders whatever metrics each process actually has, marks the rest PENDING, computes nothing.
---

# Section Renderer: Checkpoint Baseline

## Role

Data-driven synthesis renderer for the `baseline` checkpoint. Reads the relevant `processes/PROC-NNN.md` files and `model/baselines.json` and produces TWO designed HTML section blocks. Renders the metrics each process actually carries; missing metrics render as PENDING. Computes no numbers — every figure is drawn verbatim from source.

## Inputs required

| Input | File | Used for |
|---|---|---|
| Baselines (structured) | `model/baselines.json` | Per-process metric values (volume, cycle time, error rate, FTE effort) |
| Process detail | `processes/PROC-NNN.md` | Process names, source/confidence notes, challenge hypothesis per process |

You receive the engagement folder path and the section id `baseline`. Read the source files yourself. No other source files.

## Required output

Two `<div class="section-block">` blocks, in this order.

### Block 1 — `#baselines`

\`\`\`html
<div class="section-block" id="baselines">
  <h2>As-Is Baselines — For Your Confirmation</h2>
  <table>
    <thead>
      <tr><th>Process</th><th>Volume</th><th>Cycle time</th><th>Error rate</th><th>FTE effort</th><th>Source / confidence</th></tr>
    </thead>
    <tbody>
      <!-- one row per process present in model/baselines.json -->
      <!-- each metric: verbatim value from baselines.json, or the literal text PENDING if absent -->
    </tbody>
  </table>
  <p class="gap-note">[Source citation + confidence levels verbatim from processes/PROC-NNN.md. Note any PENDING metrics as open data gaps.]</p>
</div>
\`\`\`

### Block 2 — `#validate`

\`\`\`html
<div class="section-block" id="validate">
  <h2>What We Need You to Confirm</h2>
  <div class="callout">
    <strong>Confirm or correct each baseline above.</strong> These figures drive every value estimate in the rest of the assessment.
  </div>
  <!-- For each process: its challenge hypothesis (root-cause vs optimize-around) presented as a decision -->
  <!-- Use .callout-note per process; state the hypothesis and the question for the stakeholder -->
  <p class="gap-note">[List open questions / data gaps (PENDING metrics) the stakeholders should resolve.]</p>
</div>
\`\`\`

## Hard refusals

- Render only metrics present in `model/baselines.json`; absent metrics are the literal `PENDING` — never invented or rounded.
- All values verbatim from source — compute nothing.
- Do not reference `baselines.md` or `process-map.md` (retired). Sources are `model/baselines.json` and `processes/PROC-NNN.md`.
- Do not return wrapper markup (`<html>`, `<body>`, `<style>`, `<script>`).
- Use only CSS classes defined in the checkpoint shell / building-deliverable design system. Do not invent classes.

## Operating constraints

- Output: exactly two `.section-block` blocks (`#baselines`, then `#validate`).
- Source: `model/baselines.json` + the relevant `processes/PROC-NNN.md` files only.

## Dispatch point

Dispatched by `ai-process-assessment:building-checkpoint` for the `baseline` checkpoint. Writes its blocks to `<engagement>/_staging/checkpoint-baseline/` and returns a one-line confirmation per block. Returns to the main context for assembly.
```

- [ ] **Step 2: Run the agent tests**

Run: `.venv/bin/pytest tests/test_agents.py tests/test_guards.py -q`
Expected: PASS — agent frontmatter (`name`/`description`) valid; no retired-file tokens.

- [ ] **Step 3: Commit**

```bash
git add agents/section-renderer-checkpoint-baseline.md
git commit -m "feat(checkpoint): data-driven baseline section renderer"
```

---

## Task 4: Create the outcome template

**Files:**
- Create: `templates/checkpoint-outcome-template.md`

- [ ] **Step 1: Write the template**

Create `templates/checkpoint-outcome-template.md` with exactly this content:

```markdown
# Checkpoint Outcome — <checkpoint id>

- **Checkpoint:** <id> (e.g., baseline — Process & Baseline Validation)
- **Date:** <YYYY-MM-DD>
- **Attendees / sign-off:** <names + roles — e.g., process owner(s), sponsor>
- **Status:** Confirmed | Changes Requested

## Changes requested

| What | Which PROC-NNN / metric | Raised by |
|---|---|---|
| <e.g., cycle time is 9 days, not 12> | PROC-003 · cycle time | <name> |

(Leave the table empty and write "None — confirmed as presented" if Status is Confirmed.)

## Routing

- On **Changes Requested**: route to <route-back phase — e.g., Phase 4 discovering-processes>; correct the source file(s); re-run `python -m engine.run <engagement>/` if any number changed; regenerate the checkpoint; append a new outcome record.
- On **Confirmed**: downstream phases may rely on the validated output; the terminal deliverable-gate and final deliverable may cite this sign-off.
```

- [ ] **Step 2: Verify the suite is unaffected**

Run: `.venv/bin/pytest -q`
Expected: PASS (templates are not parsed by the test model; this just confirms nothing regressed).

- [ ] **Step 3: Commit**

```bash
git add templates/checkpoint-outcome-template.md
git commit -m "feat(checkpoint): stakeholder outcome record template"
```

---

## Task 5: Add Checkpoint Mode to the deliverable-gate

**Files:**
- Modify: `skills/deliverable-gate/SKILL.md`

The change is **additive**. Do not alter the existing `## Session Start`, `## Gate condition`, `## Five Integrity Dimensions`, or `## Phase checklist` content (the terminal path must be unchanged), and do not add `executive-summary.md` to the Session Start block.

- [ ] **Step 1: Insert a Checkpoint Mode section**

Insert this new section immediately AFTER the `## Five Integrity Dimensions` section and BEFORE `## Phase checklist`:

```markdown
## Checkpoint Mode (interim validation)

When invoked by `ai-process-assessment:building-checkpoint` with a `checkpoint=<id>`, the gate runs in **Checkpoint Mode**: it inspects only the files that exist at that point in the methodology and treats not-yet-produced phase files as **legitimately absent, not failures**. The terminal gate (invoked with no checkpoint id) is unaffected and still requires all phase files per Session Start.

For `checkpoint=baseline` (after Phase 4), read only: `scope.md`, `processes/_index.md`, the relevant `processes/PROC-NNN.md` files, and `model/baselines.json`. Run only the applicable dimensions:

- **Evidence integrity** — every figure to be rendered traces to a `processes/PROC-NNN.md` / `model/baselines.json` source. No figure floats free.
- **Determinism integrity** — every numeric figure equals its `model/results.json` / `model/baselines.json` source; PENDING renders as PENDING, never an invented number.
- **Completeness** — every in-scope process domain from `scope.md` that Phase 4 should have covered is present in `processes/`, or its gap is acknowledged.

Dimensions that require later phases (Logic chain through scores/roadmap/briefs, Business Case, Communication readiness) are **not applicable** at this checkpoint and are skipped — note them as "deferred to later checkpoints / terminal gate." Do **not** dispatch the `opportunity-reviewer` subagent in Checkpoint Mode (opportunities do not exist yet); checkpoint clearance is a lighter, scoped pass.

Record clearance as a distinct checkpoint entry in `evidence-log.md`, e.g. `Checkpoint baseline — cleared (Evidence, Determinism, Completeness)`. On non-clearance, route to the dimension's owning phase (for `baseline`: Phase 4) for remediation before the checkpoint renders.
```

- [ ] **Step 2: Run the gate guards (must stay green)**

Run: `.venv/bin/pytest tests/test_guards.py -q`
Expected: PASS. Specifically `test_deliverable_gate_does_not_read_exec_summary` (Session Start untouched, no `executive-summary.md` there) and `test_deliverable_gate_has_determinism_check` (`results.json` + "determinism" still present).

- [ ] **Step 3: Full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add skills/deliverable-gate/SKILL.md
git commit -m "feat(checkpoint): add backward-compatible Checkpoint Mode to deliverable-gate"
```

---

## Task 6: Wire the checkpoint into the keystone

**Files:**
- Modify: `skills/using-methodology/SKILL.md`

Do NOT add a Phase-Map row (keeps the chain + 14-row manifest intact). Make three additive edits.

- [ ] **Step 1: Add `checkpoints/` to the Engagement Folder Convention list**

In the `## Engagement Folder Convention` bulleted list, add this bullet immediately after the `usecase-briefs/` line (order is cosmetic; placement near the mid-flow artifacts reads best):

```markdown
- `checkpoints/` — stakeholder validation checkpoints (folder: `checkpoint-<id>.html` + `CP-<id>-outcome.md`; recommended, recorded — see Routing Logic). Present only when a checkpoint was run.
```

- [ ] **Step 2: Add routing logic for the checkpoint**

In the `## Routing Logic` bullet list, add this bullet immediately after the `processes`/Phase 4 related routing (after the line about subagents, before the GRC line is fine):

```markdown
- After Phase 4 saves `processes/_index.md`, before Phase 5 → **recommended:** invoke `ai-process-assessment:building-checkpoint` (checkpoint `baseline`) to validate the process maps and baseline metrics with process owners + the sponsor. It is recommended-and-recorded, not a hard gate — Phase 5 is not blocked on it unless CLAUDE.md makes it mandatory. On a "Changes Requested" outcome, route back to Phase 4, correct, re-run the engine, and regenerate before Phase 5.
```

- [ ] **Step 3: Add a When-to-Invoke row**

In the `## When-to-Invoke Reference` table, add this row:

```markdown
| "validate the baselines", "review the process maps with the client", "stakeholder checkpoint" | `ai-process-assessment:building-checkpoint` |
```

- [ ] **Step 4: Run keystone-related tests (mirror will fail until Task 7)**

Run: `.venv/bin/pytest tests/test_manifest.py tests/test_skills.py tests/test_outputs.py -q`
Expected: PASS (phase map still 14; `checkpoints/` added to convention is an extra entry — `test_outputs` only requires phase outputs ⊆ convention, so extras are fine).

Run: `.venv/bin/pytest tests/test_guards.py::test_system_prompt_mirrors_keystone -q`
Expected: **FAIL** — the keystone changed but `system-prompt.md` has not been re-mirrored yet. Task 7 fixes this.

- [ ] **Step 5: Commit**

```bash
git add skills/using-methodology/SKILL.md
git commit -m "feat(checkpoint): wire checkpoint into keystone (convention + routing prose)"
```

---

## Task 7: Re-mirror system-prompt.md

**Files:**
- Modify: `system-prompt.md`

`test_system_prompt_mirrors_keystone` requires the keystone body (everything after the YAML frontmatter) to appear verbatim as a substring of `system-prompt.md`.

- [ ] **Step 1: Inspect how system-prompt.md embeds the keystone**

Run: `head -40 system-prompt.md`
Identify where the mirrored keystone body begins (there may be a short preamble before it). The mirrored region is the keystone's content starting at `# Using the Process Assessment Methodology`.

- [ ] **Step 2: Replace the mirrored region with the current keystone body**

Regenerate the mirror: take `skills/using-methodology/SKILL.md`, drop its YAML frontmatter (everything through the second `---`), and replace the corresponding region in `system-prompt.md` with that exact body. Preserve any non-keystone preamble that legitimately precedes the mirror. The simplest reliable approach:

```bash
python3 - <<'PY'
from pathlib import Path
ks = Path("skills/using-methodology/SKILL.md").read_text()
body = ks.split("---", 2)[-1].strip()   # keystone body, frontmatter dropped
sp = Path("system-prompt.md").read_text()
anchor = "# Using the Process Assessment Methodology"
pre = sp[: sp.find(anchor)]             # keep any preamble before the mirror
Path("system-prompt.md").write_text(pre + body + "\n")
print("system-prompt.md re-mirrored")
PY
```

- [ ] **Step 3: Verify the mirror guard and stale-token guard pass**

Run: `.venv/bin/pytest tests/test_guards.py::test_system_prompt_mirrors_keystone -q`
Expected: PASS.

Confirm no stale tokens were introduced (the guard also forbids `scored-opportunities.md`, `7-dimension`, `ten sequential phases`):
Run: `.venv/bin/pytest tests/test_guards.py -q`
Expected: PASS.

- [ ] **Step 4: Full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS — all green (was 164; now 164 with the bumped count assertion still one test).

- [ ] **Step 5: Commit**

```bash
git add system-prompt.md
git commit -m "chore: re-mirror system-prompt.md after keystone checkpoint wiring"
```

---

## Task 8: Cross-file consistency check

**Files:** none modified — verification only.

- [ ] **Step 1: Confirm the registry/skill/agent/template names all agree**

Grep for the wired identifiers and confirm each appears where expected:

Run:
```bash
grep -rn "building-checkpoint" skills/ system-prompt.md tests/
grep -rn "section-renderer-checkpoint-baseline" skills/building-checkpoint/SKILL.md agents/
grep -rn "checkpoint-baseline.html\|CP-baseline-outcome.md\|checkpoints/" skills/building-checkpoint/SKILL.md skills/using-methodology/SKILL.md
```
Expected: the skill id is allow-listed (tests), wired (keystone + system-prompt), and self-consistent; the renderer name in the skill matches the agent's frontmatter `name`; the output/outcome filenames match between the skill registry and the keystone convention.

- [ ] **Step 2: Confirm no retired tokens slipped in**

Run: `.venv/bin/pytest tests/test_guards.py::test_no_retired_monolithic_file_references -q`
Expected: PASS.

- [ ] **Step 3: Full suite once more**

Run: `.venv/bin/pytest -q`
Expected: PASS.

---

## Finishing the branch (per repo convention)

- [ ] Bump the version: `make bump VERSION=2.10.0`
- [ ] Add a `## [2.10.0] — 2026-06-16` entry to `CHANGELOG.md` describing the baseline validation checkpoint (new `building-checkpoint` skill, baseline renderer, deliverable-gate Checkpoint Mode, outcome template, keystone wiring). Commit: `git add -A && git commit -m "chore: bump to 2.10.0"`.
- [ ] Open the PR to `main` (it will be human-merged — markdown change). Reference issue #49 and note Checkpoints 1 & 3 are deferred follow-ups.
- [ ] On merge, `auto-tag` → `release` publishes v2.10.0 (end-to-end after #44).

---

## Self-review notes

- **Spec coverage:** Component 1 → Task 2; Component 2 → Task 3; Component 3 → Task 5; Component 4 → Task 4 (+ recording flow in Task 2's skill); Component 5 (shell) → documented in Task 2's skill; Component 6 → Tasks 6 + 7; Testing section → Tasks 1, 3, 8 + suite runs; Rollout → Finishing.
- **Registration approach revised from the spec:** the spec floated "add as a Phase-Map row"; planning against `test_chain.py`/`test_manifest.py` showed that breaks the linear-chain and 14-row invariants, so the skill is registered via the **allow-list** instead (cleaner; wired via routing prose). This is the only deviation and it is strictly safer.
- **Guard traps covered:** retired-file tokens (avoid `baselines.md`/`process-map.md`), system-prompt mirror (Task 7), gate Session-Start/determinism guards (Task 5 additive-only).
- **No placeholders:** every created file's full content is inline; every edit shows exact insert text and anchor.
