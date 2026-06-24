# Checkpoint 1 — Scope & Context Alignment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Checkpoint 1 (Scope & Context Alignment) to the existing checkpoint pattern — a new `scope` registry row in `building-checkpoint`, a new `section-renderer-checkpoint-scope` agent (that never leaks the internal political map), a `scope` case in the deliverable-gate Checkpoint Mode, and keystone/system-prompt wiring.

**Architecture:** Pure methodology markdown, extending the v2.10.0 checkpoint machinery. No new skill (the parameterized `building-checkpoint` skill already exists and is allow-listed); this adds a registry row + one renderer agent + small additive edits. The HTML renders later when a consultant runs the skill.

**Tech Stack:** Markdown skills/agents; pytest (`tests/methodology_model.py` parses keystone/skills/agents).

**Spec:** `docs/superpowers/specs/2026-06-16-checkpoint-scope-validation-design.md`
**Issue:** grandaha/ai-process-assessment#49 (Checkpoint 1 of 3)

---

## Critical constraints (verified against the suite — do not violate)

- **Never write `baselines.md` or `process-map.md`** in any `skills/`/`agents/` file (`test_guards.py::test_no_retired_monolithic_file_references`). Use `model/baselines.json` / `processes/PROC-NNN.md` if referenced at all (this feature mostly references `scope.md`/`context.md`).
- **No new skill** — only a registry row in the existing `building-checkpoint`. Do NOT touch `tests/test_skills.py` (count stays 18) and do NOT add a Phase-Map row.
- **Any keystone edit must be re-mirrored to `system-prompt.md`** (`test_guards.py::test_system_prompt_mirrors_keystone`), and the `<EXTREMELY_IMPORTANT>` envelope must stay balanced (`test_system_prompt_envelope_balanced`).
- **deliverable-gate edits stay additive:** do not touch its `## Session Start` (must remain free of `executive-summary.md`); keep `results.json` + "determinism" in the file. Terminal path unchanged.
- The new renderer agent must be **referenced by a skill body** (the registry row does this) so `test_no_unexpected_orphan_agents` passes.
- Markdown change → PR is human-merged.

## File structure

- **Create** `agents/section-renderer-checkpoint-scope.md` — data-driven renderer; `#scope` + `#context` + `#validate`; hard-refuses the political map.
- **Modify** `skills/building-checkpoint/SKILL.md` — add the `scope` registry row; generalize Session Start predecessor check, the shell nav, and the route-back to cover `scope`.
- **Modify** `skills/deliverable-gate/SKILL.md` — add a `scope` case to `## Checkpoint Mode`.
- **Modify** `skills/using-methodology/SKILL.md` — routing + when-to-invoke for the scope checkpoint.
- **Modify** `system-prompt.md` — re-mirror.
- **Modify** `tests/test_agents.py` — bump agent count 15 → 16.

---

## Task 1: Register the new agent in the tests (RED)

**Files:** Modify `tests/test_agents.py`

- [ ] **Step 1: Bump the agent count**

Replace the `test_agent_count` body comment + assertion:

```python
def test_agent_count(methodology):
    # 16 = 15 prior agents + section-renderer-checkpoint-scope,
    # the scope-and-context validation checkpoint renderer (Checkpoint 1).
    assert len(methodology.agents) == 16
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/test_agents.py::test_agent_count -q`
Expected: FAIL — only 15 agent files exist.

- [ ] **Step 3: Commit**

```bash
git add tests/test_agents.py
git commit -m "test: register section-renderer-checkpoint-scope (agent count 15->16)"
```

---

## Task 2: Create the scope renderer agent (GREEN for Task 1)

**Files:** Create `agents/section-renderer-checkpoint-scope.md`

- [ ] **Step 1: Write the agent file**

Create `agents/section-renderer-checkpoint-scope.md` with exactly this content:

```markdown
---
name: section-renderer-checkpoint-scope
description: Checkpoint renderer — reads scope.md and context.md and produces three section blocks for the scope-and-context validation checkpoint: the #scope framing view, the #context shareable-context view, and the #validate confirm-or-correct view. Data-driven synthesis renderer — renders the fields that exist, marks the rest PENDING, and never exposes the internal political map.
---

# Section Renderer: Checkpoint Scope

## Role

Data-driven synthesis renderer for the `scope` checkpoint. Reads `scope.md` and `context.md` and produces THREE designed HTML section blocks. Renders the fields that exist; missing fields render as PENDING. Invents nothing; every value is drawn verbatim from source.

## Inputs required

| Input | File | Used for |
|---|---|---|
| Scope | `scope.md` | Sponsoring question, decision-maker, in/out-of-scope, success criteria, constraints |
| Context | `context.md` | Business model, strategic priorities, AI/automation maturity, funding model, regulatory exposure |

You receive the engagement folder path and the section id `scope`. Read the source files yourself. No other source files.

## Required output

Three `<div class="section-block">` blocks, in this order.

### Block 1 — `#scope`

\`\`\`html
<div class="section-block" id="scope">
  <h2>The Engagement — As We Understand It</h2>
  <div class="callout">
    <strong>The decision this engagement enables:</strong> [Sponsoring question verbatim from scope.md]
  </div>
  <p><strong>Decision-maker:</strong> [name, role — and what they will do differently, verbatim from scope.md]</p>
  <table>
    <tbody>
      <tr><th>In scope</th><td>[in-scope domains verbatim, or PENDING]</td></tr>
      <tr><th>Out of scope</th><td>[out-of-scope boundaries verbatim, or PENDING]</td></tr>
      <tr><th>Success criteria</th><td>[success criteria verbatim, or PENDING]</td></tr>
      <tr><th>Constraints</th><td>[constraints verbatim, or PENDING]</td></tr>
    </tbody>
  </table>
</div>
\`\`\`

### Block 2 — `#context`

\`\`\`html
<div class="section-block" id="context">
  <h2>Strategic Context</h2>
  <table>
    <tbody>
      <tr><th>Business model</th><td>[verbatim from context.md, or PENDING]</td></tr>
      <tr><th>Strategic priorities</th><td>[verbatim, or PENDING]</td></tr>
      <tr><th>AI / automation maturity</th><td>[verbatim, or PENDING]</td></tr>
      <tr><th>Funding model</th><td>[verbatim, or PENDING]</td></tr>
      <tr><th>Regulatory exposure</th><td>[factual regulatory exposure only, or PENDING]</td></tr>
    </tbody>
  </table>
  <p class="gap-note">[Note any PENDING fields as open items to resolve.]</p>
</div>
\`\`\`

### Block 3 — `#validate`

\`\`\`html
<div class="section-block" id="validate">
  <h2>What We Need You to Confirm</h2>
  <div class="callout">
    <strong>Did we frame the decision you are trying to make correctly?</strong> Confirm or correct the scope and context above before we map processes and build the opportunity portfolio.
  </div>
  <p class="gap-note">[List open questions / PENDING fields the sponsor and decision-maker should resolve.]</p>
</div>
\`\`\`

## Hard refusals

- **NEVER render the political landscape** (aligners, vetoers, skeptics) from `context.md`. It is internal consultant intelligence and must not appear in this client-facing artifact.
- **NEVER render the internal risk-tolerance / cultural-risk read.** For risk, render only factual regulatory exposure.
- Render only fields present in source; absent fields are the literal `PENDING` — never invented.
- All values verbatim from `scope.md` / `context.md` — synthesize/select, do not editorialize or compute.
- Do not return wrapper markup (`<html>`, `<body>`, `<style>`, `<script>`).
- Use only CSS classes defined in the checkpoint shell / building-deliverable design system (`section-block`, `callout`, `gap-note`, table styles). Do not invent classes.

## Operating constraints

- Output: exactly three `.section-block` blocks (`#scope`, then `#context`, then `#validate`).
- Source: `scope.md` + `context.md` only.

## Dispatch point

Dispatched by `ai-process-assessment:building-checkpoint` for the `scope` checkpoint. Writes its blocks to `<engagement>/_staging/checkpoint-scope/` and returns a one-line confirmation per block. Returns to the main context for assembly.
```

- [ ] **Step 2: Run agent + guard tests**

Run: `.venv/bin/pytest tests/test_agents.py tests/test_guards.py -q`
Expected: `test_agent_count` PASS (16); frontmatter checks PASS; no retired tokens. (`test_no_unexpected_orphan_agents` will still FAIL until Task 3 references the agent in the skill body — that's expected; note it and proceed.)

- [ ] **Step 3: Commit**

```bash
git add agents/section-renderer-checkpoint-scope.md
git commit -m "feat(checkpoint): scope-and-context renderer (excludes political map)"
```

---

## Task 3: Add the `scope` registry row + generalize the skill

**Files:** Modify `skills/building-checkpoint/SKILL.md`

- [ ] **Step 1: Generalize Session Start step 3 and step 4**

Replace step 3:
```markdown
3. Resolve the checkpoint id (wired values: `baseline`, `scope`). Look up its row in the Checkpoint Registry below.
```
Replace step 4:
```markdown
4. Verify the registry row's predecessor outputs exist. For `baseline`: both `processes/_index.md` and `model/baselines.json`. For `scope`: both `scope.md` and `context.md`. Halt with a clear message naming whichever file is missing if not.
```

- [ ] **Step 2: Add the `scope` row to the Checkpoint Registry table**

Change the table intro line and add the row. Replace:
```markdown
Only the `baseline` row is active. The table format anticipates Checkpoints 1 and 3 (future cycles).
```
with:
```markdown
The `baseline` (Checkpoint 2) and `scope` (Checkpoint 1) rows are active. The table format anticipates Checkpoint 3 (future cycle).
```
Add this row to the table, immediately after the `baseline` row:
```markdown
| `scope` | Phase 2 | Sponsor + decision-maker | `scope.md`, `context.md` | `section-renderer-checkpoint-scope` | `checkpoints/checkpoint-scope.html` | `checkpoints/CP-scope-outcome.md` | Phase 1 (`ai-process-assessment:scoping-engagement`) for scope-field changes; Phase 2 (`ai-process-assessment:mapping-context`) for context-field changes |
```

- [ ] **Step 3: Generalize the Checkpoint shell section for per-checkpoint nav/anchors**

In the `## Checkpoint shell` section, the sticky-nav/anchor block is currently baseline-specific. Replace the baseline-only nav + section-mapping lines with a per-checkpoint mapping. Find the shell structure block and replace its `<nav>`...section-mapping portion with:

```markdown
The sticky nav and section blocks are per-checkpoint:

- `baseline` → nav `Baselines` (`#baselines`), `Validate` (`#validate`); masthead label "Baseline Validation — Interim"; blocks `#baselines`, `#validate` from `section-renderer-checkpoint-baseline`.
- `scope` → nav `Scope` (`#scope`), `Context` (`#context`), `Validate` (`#validate`); masthead label "Scope & Context Alignment — Interim"; blocks `#scope`, `#context`, `#validate` from `section-renderer-checkpoint-scope`.

Assemble the sticky nav with one `<a href="#anchor" onclick="navScrollTo('anchor'); return false;">Label</a>` per the resolved checkpoint's anchors, in block order, then the masthead, then the section blocks in order, then the `.doc-footer`.
```

(Keep the `navScrollTo` JS helper block as-is.)

- [ ] **Step 4: Add `scope` route-back to the Recording the outcome section**

In `## Recording the outcome`, the "Changes Requested" bullet is baseline-specific. Append a `scope`-specific routing sentence to that bullet (or add a parallel bullet). Add this immediately after the existing baseline "Changes Requested" bullet:

```markdown
- **Changes Requested (`scope` checkpoint) — route per field:** a corrected **scope** field (sponsoring question, decision-maker, in/out-of-scope, success criteria, constraints) routes to Phase 1 (`ai-process-assessment:scoping-engagement`); a corrected **context** field (business model, strategic priorities, maturity, funding, regulatory exposure) routes to Phase 2 (`ai-process-assessment:mapping-context`). A mixed outcome routes to both. Correct the source file(s) — editing the source is what refreshes the checkpoint — then regenerate `checkpoints/checkpoint-scope.html` and append a new outcome record. Repeat until Confirmed. (No engine run is involved at this checkpoint — there are no figures.)
```

- [ ] **Step 5: Run the relevant tests**

Run: `.venv/bin/pytest tests/test_agents.py tests/test_skills.py tests/test_guards.py -q`
Expected: PASS — including `test_no_unexpected_orphan_agents` (the scope renderer is now referenced in the skill body via the registry row) and `test_skill_count` (still 18; no new skill). No retired tokens.

- [ ] **Step 6: Commit**

```bash
git add skills/building-checkpoint/SKILL.md
git commit -m "feat(checkpoint): wire scope checkpoint into building-checkpoint registry"
```

---

## Task 4: Add the `scope` case to the gate Checkpoint Mode

**Files:** Modify `skills/deliverable-gate/SKILL.md`

The edit is additive — do not alter Session Start, the Five Integrity Dimensions, the existing `baseline` paragraph, or the terminal path.

- [ ] **Step 1: Insert a `scope` paragraph in the Checkpoint Mode section**

In `## Checkpoint Mode (interim validation)`, immediately AFTER the `baseline` paragraph + its dimension bullets and BEFORE the "Dimensions that require later phases…" paragraph, insert:

```markdown
For `checkpoint=scope` (after Phase 2), read only: `scope.md` and `context.md`. Run only the applicable dimensions:

- **Completeness** — every in-scope domain named in `scope.md` is reflected, and the scope is internally coherent (sponsoring question ↔ success criteria ↔ in/out-of-scope align).
- **Evidence integrity** — every claim to be rendered traces to a `scope.md` / `context.md` source.

**Determinism integrity is not applicable** at the `scope` checkpoint — no numeric figures exist yet; state this rather than checking it. Record clearance as `Checkpoint scope — cleared (Completeness, Evidence)`. On non-clearance, route a scope-field gap to Phase 1 and a context-field gap to Phase 2 before the checkpoint renders.
```

- [ ] **Step 2: Run the gate guards + full suite**

Run: `.venv/bin/pytest tests/test_guards.py -q && .venv/bin/pytest -q`
Expected: PASS. `test_deliverable_gate_does_not_read_exec_summary` and `test_deliverable_gate_has_determinism_check` still green (Session Start untouched; `results.json` + "determinism" still present in the file).

- [ ] **Step 3: Commit**

```bash
git add skills/deliverable-gate/SKILL.md
git commit -m "feat(checkpoint): add scope case to deliverable-gate Checkpoint Mode"
```

---

## Task 5: Keystone wiring + system-prompt mirror

**Files:** Modify `skills/using-methodology/SKILL.md`, then `system-prompt.md`

- [ ] **Step 1: Add a routing bullet**

In `## Routing Logic`, immediately after the existing `building-checkpoint` (baseline) routing bullet, add:

```markdown
- After Phase 2 saves `context.md`, before Phase 3 → **recommended:** invoke `ai-process-assessment:building-checkpoint` (checkpoint `scope`) to validate the engagement framing — sponsoring question, decision-maker, scope, success criteria, and strategic context — with the sponsor + decision-maker. Recommended-and-recorded, not a hard gate. On "Changes Requested", route scope-field corrections to Phase 1 and context-field corrections to Phase 2, then regenerate before Phase 3.
```

- [ ] **Step 2: Add a When-to-Invoke row**

In the `## When-to-Invoke Reference` table, add:

```markdown
| "validate the scope", "confirm the engagement framing", "scope alignment checkpoint" | `ai-process-assessment:building-checkpoint` |
```

- [ ] **Step 3: Verify keystone tests (mirror fails until Step 4)**

Run: `.venv/bin/pytest tests/test_manifest.py tests/test_skills.py -q`
Expected: PASS (phase map still 14; skills still 18).
Run: `.venv/bin/pytest tests/test_guards.py::test_system_prompt_mirrors_keystone -q`
Expected: FAIL (keystone changed, mirror stale).

- [ ] **Step 4: Re-mirror system-prompt.md**

Regenerate the mirror, preserving the trailing wrapper framing (the part after the keystone body, including the closing `</EXTREMELY_IMPORTANT>` tag):

```bash
python3 - <<'PY'
from pathlib import Path
ks = Path("skills/using-methodology/SKILL.md").read_text()
body = ks.split("---", 2)[-1].strip()                 # keystone body, frontmatter dropped
sp = Path("system-prompt.md").read_text()
anchor = "# Using the Process Assessment Methodology"
pre = sp[: sp.find(anchor)]                            # preamble before the mirror
# trailing framing after the OLD mirrored body (e.g. the </EXTREMELY_IMPORTANT> wrapper):
tail = ""
close = "</EXTREMELY_IMPORTANT>"
if close in sp[sp.find(anchor):]:
    tail = "\n" + close + "\n"
Path("system-prompt.md").write_text(pre + body + tail)
print("re-mirrored; tail preserved:", bool(tail))
PY
```

Then confirm:
```bash
grep -c '^<EXTREMELY_IMPORTANT>$' system-prompt.md   # expect 1
grep -c '^</EXTREMELY_IMPORTANT>$' system-prompt.md  # expect 1
```

- [ ] **Step 5: Full suite green**

Run: `.venv/bin/pytest -q`
Expected: PASS — `test_system_prompt_mirrors_keystone` + `test_system_prompt_envelope_balanced` green; full suite green.

- [ ] **Step 6: Commit**

```bash
git add skills/using-methodology/SKILL.md system-prompt.md
git commit -m "feat(checkpoint): wire scope checkpoint into keystone + re-mirror system-prompt"
```

---

## Task 6: Consistency check

**Files:** none — verification only.

- [ ] **Step 1: Identifier consistency**

Run:
```bash
grep -rn "checkpoint-scope\|section-renderer-checkpoint-scope\|CP-scope-outcome" skills/building-checkpoint/SKILL.md agents/section-renderer-checkpoint-scope.md
grep -rn "scope" skills/deliverable-gate/SKILL.md | grep -i checkpoint
```
Expected: renderer name matches between the registry row and the agent frontmatter; output/outcome filenames (`checkpoint-scope.html`, `CP-scope-outcome.md`) consistent; gate has a `scope` case.

- [ ] **Step 2: No retired tokens; full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS (166 — the 165 prior + the agent-count assertion is the same test, so the count is unchanged at 165 unless a new test was added; confirm the number and that all pass).

Note: this plan adds no new test functions, so the suite count stays **165**; only the `test_agent_count` assertion value changed.

---

## Finishing the branch

- [ ] `make bump VERSION=2.11.0`
- [ ] Add a `## [2.11.0] — 2026-06-16` CHANGELOG entry (Checkpoint 1 — Scope & Context Alignment: new scope registry row + `section-renderer-checkpoint-scope` (excludes the political map) + gate scope case + keystone wiring). Commit: `git add -A && git commit -m "chore: bump to 2.11.0"`.
- [ ] Open the PR to `main` (human-merged). Reference #49 (Checkpoint 1 of 3; CP3 deferred).
- [ ] On merge, auto-tag → release publishes v2.11.0.

---

## Self-review notes

- **Spec coverage:** Component 1 (registry row + per-field route-back + shell) → Task 3; Component 2 (renderer, political-map refusal) → Task 2; Component 3 (gate scope case, determinism N/A) → Task 4; Component 4 (keystone + mirror) → Task 5; Testing → Tasks 1, 6 + suite runs; Rollout → Finishing.
- **Guard traps covered:** no new skill (test_skills untouched, 18); agent count 15→16 only; keystone→mirror re-sync with tail/envelope preserved (Task 5 Step 4 explicitly restores `</EXTREMELY_IMPORTANT>`); gate Session Start untouched; no retired tokens.
- **Consistency:** renderer name `section-renderer-checkpoint-scope`, files `checkpoints/checkpoint-scope.html` / `checkpoints/CP-scope-outcome.md`, anchors `#scope`/`#context`/`#validate` used identically across the agent, the registry row, and the shell mapping.
- **No placeholders:** full agent content inline; every edit shows exact anchor + replacement text.
