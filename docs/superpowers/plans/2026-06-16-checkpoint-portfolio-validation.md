# Checkpoint 3 — Portfolio & Roadmap Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Checkpoint 3 (`portfolio`) — an interim client-facing HTML artifact rendered after Phase 7 so the decision-maker/sponsor/IT-lead validate the prioritized portfolio and wave sequencing before Phase 8.

**Architecture:** Reuse the established checkpoint pattern (parameterized `building-checkpoint` skill + scoped `deliverable-gate` Checkpoint Mode + recorded outcome). This cycle adds one bespoke data-driven renderer agent, one registry row, one gate case, and keystone/system-prompt wiring. No engine code changes.

**Tech Stack:** Markdown skills/agents; Python test suite (pytest) for structural invariants (agent count, skill count, guards).

---

## Branch & baseline

- Working branch `feat/checkpoint-portfolio` is already created off `main` (which now includes CP1/`scope`, v2.11.0).
- Baseline verified: `python -m pytest -q` → **166 passed**; 16 agents; version 2.11.0.

## File Structure

- **Create** `agents/section-renderer-checkpoint-portfolio.md` — bespoke data-driven renderer; emits `#portfolio`, `#scoring`, `#roadmap`, `#validate` blocks.
- **Modify** `skills/building-checkpoint/SKILL.md` — frontmatter description; registry intro line; `portfolio` registry row; Session Start predecessor check; shell sticky-nav mapping; Recording-the-outcome route-back; Chain-to-next-skill.
- **Modify** `skills/deliverable-gate/SKILL.md` — add `portfolio` paragraph to `## Checkpoint Mode`.
- **Modify** `skills/using-methodology/SKILL.md` — Routing Logic bullet + When-to-Invoke row.
- **Modify** `system-prompt.md` — re-mirror the two keystone additions verbatim.
- **Modify** `tests/test_agents.py` — agent count 16 → 17.
- **Modify** `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `INSTALL.md` — version bump to 2.12.0 (via `make bump`).

Two dispatches: **A** = renderer + count test; **B** = skill/gate/keystone wiring. They are coupled only through the renderer *name*, which is fixed in this plan, so B can be written against the name without A's file existing.

---

## Task 1: Bump agent-count test to 17 (red), then create the renderer (green)

**Files:**
- Modify: `tests/test_agents.py` (the `test_agent_count` body + comment)
- Create: `agents/section-renderer-checkpoint-portfolio.md`

- [ ] **Step 1: Update the failing count test**

In `tests/test_agents.py`, replace the `test_agent_count` body:

```python
def test_agent_count(methodology):
    # 17 = 16 prior agents + section-renderer-checkpoint-portfolio,
    # the portfolio-and-roadmap validation checkpoint renderer (Checkpoint 3).
    assert len(methodology.agents) == 17
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_agents.py::test_agent_count -q`
Expected: FAIL — `assert 16 == 17` (the renderer file does not exist yet).

- [ ] **Step 3: Create the renderer agent file**

Create `agents/section-renderer-checkpoint-portfolio.md` with exactly this content:

```markdown
---
name: section-renderer-checkpoint-portfolio
description: Checkpoint renderer — reads scores/, opportunities/, and roadmap.md and produces four section blocks for the portfolio-and-roadmap validation checkpoint: the #portfolio ranked table, the #scoring per-OPP six-dimension detail, the #roadmap wave timeline + Wave 1 cards + investment, and the #validate confirm-or-correct view. Data-driven synthesis renderer — renders the OPPs/initiatives/waves that exist, marks the rest PENDING, hardcodes no counts or sample values, and renders the full analytical work product (full transparency — no content exclusions at this checkpoint).
---

# Section Renderer: Checkpoint Portfolio

## Role

Data-driven synthesis renderer for the `portfolio` checkpoint. Reads `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, and `roadmap.md`, and produces FOUR designed HTML section blocks. Renders the OPPs, initiatives, and waves that exist; missing fields render as PENDING. Invents nothing; every value is drawn verbatim from source. The only computation permitted is the score-bar width and the ranking order.

This checkpoint renders the **full analytical work product** — the ranked portfolio AND the per-OPP six-dimension scoring rationale. This is intentional: the audience (decision-maker, sponsor, IT lead) is making the prioritization decision and is entitled to the basis for it. Do NOT "tighten" this renderer by analogy to `section-renderer-checkpoint-scope`; there are no content exclusions at this checkpoint.

## Inputs required

| Input | File | Used for |
|---|---|---|
| Composite + sourcing | `scores/_index.md` | `OPP-ID \| Composite \| Horizon \| B/B/P` — ranking source |
| Six-dimension detail | `scores/OPP-NNN.md` | Per-dimension score + rationale + source per OPP |
| Type + structural | `opportunities/_index.md` | `Type` and `Structural` per OPP |
| Titles | `opportunities/OPP-NNN.md` | The `## OPP-NNN — [title]` header per OPP |
| Roadmap | `roadmap.md` | Wave 1 detail cards; Wave 1/2/3 tables; Enabler Projects; Budget Envelope Estimate; wave assignment per OPP |

You receive the engagement folder path and the section id `portfolio`. Read the source files yourself. No other source files.

## Required output

Four `<div class="section-block">` blocks, in this order: `#portfolio`, `#scoring`, `#roadmap`, `#validate`.

### Block 1 — `#portfolio`

One ranked table; **one row per OPP-ID present in `scores/_index.md`** (do not hardcode a row count), ranked by composite descending. Join the four normalized sources on OPP-ID.

```html
<div class="section-block" id="portfolio">
  <h2>The Prioritized Portfolio</h2>
  <p class="gap-note">[N] opportunities scored across 6 dimensions.</p>
  <table>
    <thead>
      <tr><th>Rank</th><th>OPP</th><th>Title</th><th>Type</th><th>Structural</th><th>Score</th><th>Wave</th><th>B/B/P</th></tr>
    </thead>
    <tbody>
      <!-- one <tr> per OPP-ID in scores/_index.md, ranked by composite descending -->
      <tr>
        <td>[rank]</td>
        <td>[OPP-NNN]</td>
        <td>[title, or PENDING]</td>
        <td><span class="uc-card-type type-[modifier]">[type label]</span></td>
        <td>[Structural: optimizing-around → <em>optimizing-around</em>; addressing-root → addressing-root; not-applicable → empty cell]</td>
        <td>
          <div class="score-bar-wrap">
            <div class="score-bar-track"><div class="score-bar-fill" style="width:[round(composite/5*100)]%"></div></div>
            <span class="score-value">[composite]</span>
          </div>
        </td>
        <td><span class="wave-badge w[N]">Wave [N]</span></td>
        <td>[Build / Buy / Partner, or PENDING]</td>
      </tr>
    </tbody>
  </table>
</div>
```

Type modifier classes: RPA→`type-rpa`, Augmentation→`type-aug`, AI→`type-ai`, Chain→`type-chain`, Data→`type-data`, Agentic→`type-agentic`. The label text matches the source value verbatim.

### Block 2 — `#scoring`

Per-OPP six-dimension detail, one compact group per OPP that has a `scores/OPP-NNN.md`. Render every scored OPP. PENDING any dimension a file omits.

```html
<div class="section-block" id="scoring">
  <h2>How Each Opportunity Scored</h2>
  <!-- one block per OPP, in portfolio rank order -->
  <h3>[OPP-NNN] — [title] · Composite [composite] · Horizon [Short-run/Long-run] · [B/B/P]</h3>
  <table>
    <thead><tr><th>Dimension</th><th>Score</th><th>Rationale</th></tr></thead>
    <tbody>
      <tr><th>Value Potential</th><td>[1–5, or PENDING]</td><td>[rationale verbatim, or PENDING]</td></tr>
      <tr><th>Technical Feasibility</th><td>[…]</td><td>[…]</td></tr>
      <tr><th>Data Readiness</th><td>[…]</td><td>[…]</td></tr>
      <tr><th>Org Change Readiness</th><td>[…]</td><td>[…]</td></tr>
      <tr><th>Strategic Alignment</th><td>[…]</td><td>[…]</td></tr>
      <tr><th>Time to Value</th><td>[…]</td><td>[…]</td></tr>
    </tbody>
  </table>
</div>
```

### Block 3 — `#roadmap`

A three-wave timeline (render the waves present in `roadmap.md`), Wave 1 initiative cards (render the Wave-1 initiatives that exist — do NOT hardcode 7), the enabler/dependency note, and the Budget Envelope Estimate as stat cards.

```html
<div class="section-block" id="roadmap">
  <h2>Three-Wave Roadmap</h2>
  <div class="wave-timeline">
    <!-- one .wave-band per wave present in roadmap.md -->
    <div class="wave-band w[N]">
      <div class="wave-band-label">Wave [N] · [label]</div>
      <div class="wave-band-horizon">[horizon from roadmap.md]</div>
      <div class="wave-pills">
        <!-- one pill per initiative/item in that wave's table, short name -->
        <span class="wave-pill">[short name]</span>
      </div>
      <div class="wave-band-note">[note verbatim from roadmap.md, or omit if none]</div>
    </div>
  </div>

  <h3>Wave 1 Initiatives</h3>
  <div class="uc-grid">
    <!-- one .uc-card per Wave 1 initiative present in roadmap.md -->
    <div class="uc-card">
      <div class="uc-card-header">
        <div>
          <span class="uc-card-type type-[modifier]">[Type]</span>
          <!-- only when roadmap.md marks this initiative a quick win: -->
          <span class="uc-quickwin">⚡ Quick Win</span>
        </div>
        <div class="score-bar-wrap">
          <div class="score-bar-track"><div class="score-bar-fill" style="width:[round(score/5*100)]%"></div></div>
          <span class="score-value">[score]</span>
        </div>
      </div>
      <div class="uc-card-body">
        <div class="uc-card-title">[initiative title]</div>
        <p class="uc-problem">[first sentence of Problem, ≤25 words, or PENDING]</p>
        <div class="uc-outcome">→ [first success metric with baseline, ≤20 words, or PENDING]</div>
        <div class="uc-meta">
          <span>[owner(s), or PENDING]</span>
          <span>[month target, or PENDING]</span>
          <span class="wave-badge w1">Wave 1</span>
          <span>[B/B/P, or PENDING]</span>
        </div>
      </div>
    </div>
  </div>

  <div class="callout-note">[enabler-projects / dependency note verbatim from roadmap.md, or omit if none]</div>

  <h3>The Investment</h3>
  <div class="stat-row">
    <!-- one .stat-card per figure in the Budget Envelope Estimate table -->
    <div class="stat-card">
      <div class="stat-value">[figure verbatim, or PENDING]</div>
      <div class="stat-label">[label verbatim]</div>
      <div class="stat-sub">[sub detail verbatim, or omit]</div>
    </div>
  </div>
  <p class="gap-note">ROM estimate. [Any envelope caveat verbatim from roadmap.md.]</p>
</div>
```

### Block 4 — `#validate`

```html
<div class="section-block" id="validate">
  <h2>What We Need You to Confirm</h2>
  <div class="callout">
    <strong>Did we prioritize and sequence Wave 1 correctly?</strong> Confirm or correct the portfolio ranking, the scoring, and the wave sequencing above before we package the Wave 1 use cases and build the business case.
  </div>
  <p class="gap-note">[List open questions / PENDING fields the decision-maker, sponsor, and IT lead should resolve.]</p>
</div>
```

## Hard refusals

- No invented content. Absent fields render as the literal `PENDING` — never a fabricated score, wave, owner, or dollar figure.
- **Never hardcode counts or sample values** — no fixed "7 Wave-1 cards", no specific budget envelope, no named OPPs/enablers baked into the output. Render exactly the OPPs/initiatives/waves the sources contain. (This is the failure mode of the Phase 11 renderers; this agent must not repeat it.)
- All values verbatim/selected from source. The only computation permitted is the score-bar width (`round(score/5*100)%`) and ranking order.
- **No content-sensitivity exclusions at this checkpoint** — render the full work product including six-dimension rationale. Do not omit scoring detail.
- Do not return wrapper markup (`<html>`, `<body>`, `<style>`, `<script>`).
- Use only CSS classes defined in the checkpoint shell / building-deliverable design system: `section-block`, `callout`, `gap-note`, table styles, `uc-grid`, `uc-card`, `uc-card-header`, `uc-card-title`, `uc-card-body`, `uc-card-type`, `type-rpa`/`type-aug`/`type-ai`/`type-chain`/`type-data`/`type-agentic`, `uc-problem`, `uc-outcome`, `uc-meta`, `uc-quickwin`, `score-bar-wrap`, `score-bar-track`, `score-bar-fill`, `score-value`, `wave-badge`, `w1`/`w2`/`w3`, `wave-timeline`, `wave-band`, `wave-band-label`, `wave-band-horizon`, `wave-pills`, `wave-pill`, `wave-band-note`, `callout-note`, `stat-row`, `stat-card`, `stat-value`, `stat-label`, `stat-sub`. Do not invent classes. `<em>` is a permitted inline element (not a class).

## Operating constraints

- Output: exactly four `.section-block` blocks (`#portfolio`, then `#scoring`, then `#roadmap`, then `#validate`).
- Sources: `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, `roadmap.md` only.

## Dispatch point

Dispatched by `ai-process-assessment:building-checkpoint` for the `portfolio` checkpoint. Writes its blocks to `<engagement>/_staging/checkpoint-portfolio/` and returns a one-line confirmation per block. Returns to the main context for assembly.
```

- [ ] **Step 4: Run the agent suite to verify green**

Run: `python -m pytest tests/test_agents.py -q`
Expected: PASS (count is 17; name matches filename; frontmatter present).

- [ ] **Step 5: Commit**

```bash
git add agents/section-renderer-checkpoint-portfolio.md tests/test_agents.py
git commit -m "feat(checkpoint): add section-renderer-checkpoint-portfolio (Checkpoint 3 renderer)"
```

---

## Task 2: Wire the `portfolio` registry row + per-checkpoint mappings in `building-checkpoint`

**Files:**
- Modify: `skills/building-checkpoint/SKILL.md`

- [ ] **Step 1: Update the frontmatter description**

Change the parenthetical in the `description:` field from
`(Checkpoints 1 \`scope\` and 2 \`baseline\` are wired)` to
`(Checkpoints 1 \`scope\`, 2 \`baseline\`, and 3 \`portfolio\` are wired)`.

- [ ] **Step 2: Update the Registry intro line**

Replace:
> The `baseline` (Checkpoint 2) and `scope` (Checkpoint 1) rows are active. The table format anticipates Checkpoint 3 (future cycle).

with:
> The `baseline` (Checkpoint 2), `scope` (Checkpoint 1), and `portfolio` (Checkpoint 3) rows are all active — the checkpoint pattern is complete.

- [ ] **Step 3: Add the `portfolio` registry row**

Append this row to the Checkpoint Registry table (after the `scope` row):

```
| `portfolio` | Phase 7 | Decision-maker + sponsor + IT lead | `scores/_index.md`, `scores/OPP-NNN.md`, `opportunities/_index.md`, `opportunities/OPP-NNN.md`, `roadmap.md`, `scope.md` (header only) | `section-renderer-checkpoint-portfolio` | `checkpoints/checkpoint-portfolio.html` | `checkpoints/CP-portfolio-outcome.md` | Phase 6 (`ai-process-assessment:scoring-opportunities`) for score/ranking changes; Phase 7 (`ai-process-assessment:prioritizing-roadmap`) for wave/sequencing changes |
```

- [ ] **Step 4: Extend the Session Start predecessor check (step 4)**

In `## Session Start` item 4, add the `portfolio` predecessor clause so it reads (append to the existing sentence listing `baseline`/`scope`):

> For `portfolio`: both `roadmap.md` and `scores/_index.md`. Halt with a clear message naming whichever file is missing if not.

- [ ] **Step 5: Extend the checkpoint-shell sticky-nav mapping**

In `## Checkpoint shell`, after the `scope` bullet, add:

```
- `portfolio` → nav `Portfolio` (`#portfolio`), `Scoring` (`#scoring`), `Roadmap` (`#roadmap`), `Validate` (`#validate`); masthead label "Portfolio & Roadmap Review — Interim"; blocks `#portfolio`, `#scoring`, `#roadmap`, `#validate` from `section-renderer-checkpoint-portfolio`.
```

- [ ] **Step 6: Add the `portfolio` route-back to "Recording the outcome"**

After the `scope`-checkpoint route-per-field bullet, add:

```
- **Changes Requested (`portfolio` checkpoint) — route per field:** a corrected **score/ranking** field (composite score, dimension score, Build/Buy/Partner, type) routes to Phase 6 (`ai-process-assessment:scoring-opportunities`); a corrected **wave/sequencing** field (wave assignment, sequencing constraint, enabler, investment envelope) routes to Phase 7 (`ai-process-assessment:prioritizing-roadmap`). A mixed outcome routes to both. Correct the source file(s) — editing the source is what refreshes the checkpoint — then re-run `python -m engine.run <name>/` so the composite scores recompute, regenerate `checkpoints/checkpoint-portfolio.html`, and append a new outcome record. Repeat until Confirmed.
```

- [ ] **Step 7: Add the `portfolio` line to "Chain to next skill"**

After the `scope` bullet, add:

```
- `portfolio`: on Confirmed → `ai-process-assessment:packaging-usecases` (Phase 8); on Changes Requested → `ai-process-assessment:scoring-opportunities` (Phase 6, score fields) / `ai-process-assessment:prioritizing-roadmap` (Phase 7, sequencing fields).
```

- [ ] **Step 8: Run the skills suite + referenced-agents resolve**

Run: `python -m pytest tests/test_skills.py tests/test_agents.py::test_referenced_agents_resolve -q`
Expected: PASS (skill count stays 18; the newly-referenced `section-renderer-checkpoint-portfolio` resolves to the file created in Task 1).

- [ ] **Step 9: Commit**

```bash
git add skills/building-checkpoint/SKILL.md
git commit -m "feat(checkpoint): wire portfolio registry row + per-checkpoint mappings"
```

---

## Task 3: Add the `portfolio` case to deliverable-gate Checkpoint Mode

**Files:**
- Modify: `skills/deliverable-gate/SKILL.md`

- [ ] **Step 1: Add the `portfolio` paragraph**

In `## Checkpoint Mode`, after the `scope` paragraph (which ends with the Phase 1/Phase 2 routing sentence) and before `## Phase checklist`, add:

```
For `checkpoint=portfolio` (after Phase 7), read only: `scope.md` (header), `scores/_index.md`, the `scores/OPP-NNN.md` files, `opportunities/_index.md`, the `opportunities/OPP-NNN.md` files, `roadmap.md`, and the computed inputs `model/scores.json`, `model/initiatives.json`, and `model/results.json`. If `scores/_index.md` or `roadmap.md` is missing, the checkpoint does **NOT** clear — route back (scores → Phase 6, roadmap → Phase 7); a missing portfolio must not silently pass. Run only the applicable dimensions:

- **Completeness** — every OPP-ID in `scores/_index.md` is reflected in the portfolio and has a `scores/OPP-NNN.md`; every wave in `roadmap.md` is present; the portfolio is internally coherent (ranking ↔ wave assignment ↔ Build/Buy/Partner align).
- **Evidence integrity** — every figure to be rendered traces to a `scores/` / `opportunities/` / `roadmap.md` source.
- **Determinism integrity** — every composite equals its `model/scores.json` / `model/results.json` source; ROM/investment figures trace to `model/initiatives.json`; PENDING renders as PENDING, never an invented number.

Dimensions that require later phases (Business Case, Communication readiness) are not applicable at this checkpoint — note them as deferred. Do **not** dispatch the `opportunity-reviewer` subagent in Checkpoint Mode; checkpoint clearance is a lighter, scoped pass. Record clearance as `Checkpoint portfolio — cleared (Completeness, Evidence, Determinism)` in `evidence-log.md`. On non-clearance, route a score/ranking gap to Phase 6 (`scoring-opportunities`) and a wave/sequencing gap to Phase 7 (`prioritizing-roadmap`) for remediation before the checkpoint renders.
```

- [ ] **Step 2: Run the guards suite**

Run: `python -m pytest tests/test_guards.py -q`
Expected: PASS (Session Start still carries `results.json` + "determinism"; no retired tokens introduced).

- [ ] **Step 3: Commit**

```bash
git add skills/deliverable-gate/SKILL.md
git commit -m "feat(checkpoint): add portfolio case to deliverable-gate Checkpoint Mode"
```

---

## Task 4: Keystone routing + system-prompt mirror

**Files:**
- Modify: `skills/using-methodology/SKILL.md`
- Modify: `system-prompt.md`

- [ ] **Step 1: Add the Routing Logic bullet**

In `skills/using-methodology/SKILL.md`, immediately after the existing `baseline` Routing Logic bullet (the one beginning "After Phase 4 saves `processes/_index.md`…"), add:

```
- After Phase 7 saves `roadmap.md`, before Phase 8 → **recommended:** invoke `ai-process-assessment:building-checkpoint` (checkpoint `portfolio`) to validate the prioritized portfolio and wave sequencing — ranking, scoring, quick wins, dependencies, and the investment envelope — with the decision-maker + sponsor + IT lead. Recommended-and-recorded, not a hard gate — Phase 8 is not blocked on it unless CLAUDE.md makes it mandatory. On a "Changes Requested" outcome, route score corrections to Phase 6 and sequencing corrections to Phase 7, re-run the engine, and regenerate before Phase 8.
```

- [ ] **Step 2: Add the When-to-Invoke row**

In the When-to-Invoke table, after the `scope` checkpoint row, add:

```
| "validate the portfolio", "review the roadmap with the client", "portfolio sequencing checkpoint" | `ai-process-assessment:building-checkpoint` |
```

- [ ] **Step 3: Mirror both additions into `system-prompt.md`**

`system-prompt.md` is a verbatim mirror of the keystone's shared sections. Add the identical Routing Logic bullet (Step 1) and the identical When-to-Invoke row (Step 2) at the corresponding positions in `system-prompt.md`. Do not paraphrase — the mirror guard compares text.

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS — all green. Confirm the system-prompt verbatim-mirror guard and the envelope-balance guard both pass.

- [ ] **Step 5: Commit**

```bash
git add skills/using-methodology/SKILL.md system-prompt.md
git commit -m "feat(checkpoint): keystone routing + system-prompt mirror for portfolio checkpoint"
```

---

## Task 5: Version bump + CHANGELOG + PR

**Files:**
- Modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `INSTALL.md` (via `make bump`)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump version to 2.12.0**

Run: `make bump VERSION=2.12.0`
Expected: the three version files updated to 2.12.0.

- [ ] **Step 2: Add the CHANGELOG entry**

Add a `## [2.12.0] - 2026-06-16` section at the top of the entries in `CHANGELOG.md`:

```markdown
## [2.12.0] - 2026-06-16

### Added
- **Checkpoint 3 — Portfolio & Roadmap Review** (`portfolio`): an interim client-facing HTML artifact rendered after Phase 7 so the decision-maker, sponsor, and IT lead validate the prioritized portfolio, wave sequencing, quick wins, dependencies, and investment envelope before Phase 8. Completes the three-checkpoint pattern and closes #49.
  - New bespoke data-driven renderer `section-renderer-checkpoint-portfolio` (emits `#portfolio`, `#scoring`, `#roadmap`, `#validate`). Renders the full analytical work product including per-OPP six-dimension scoring rationale; renders only the OPPs/initiatives/waves that exist (no hardcoded counts or sample values).
  - `building-checkpoint` registry row, Session Start predecessor check (`roadmap.md` + `scores/_index.md`), shell sticky-nav, per-field route-back (score → Phase 6, sequencing → Phase 7; engine re-run required), and chain-to-next-skill.
  - `deliverable-gate` Checkpoint Mode `portfolio` case (Completeness, Evidence, Determinism — determinism applicable; `opportunity-reviewer` not dispatched).
  - Keystone Routing Logic + When-to-Invoke wiring, mirrored to `system-prompt.md`.
```

- [ ] **Step 3: Run the full suite once more**

Run: `python -m pytest -q`
Expected: PASS — all green.

- [ ] **Step 4: Commit and push**

```bash
git add -A
git commit -m "chore: bump to 2.12.0 — Checkpoint 3 portfolio (closes #49)"
git push -u origin feat/checkpoint-portfolio
```

- [ ] **Step 5: Open the PR**

```bash
gh pr create --base main --head feat/checkpoint-portfolio \
  --title "feat: Checkpoint 3 — Portfolio & Roadmap Review (v2.12.0)" \
  --body "Adds Checkpoint 3 (\`portfolio\`), the final stakeholder-validation checkpoint, rendered after Phase 7. Closes #49 (all three checkpoints live). Markdown/methodology — human-merge."
```

---

## Self-Review (completed)

- **Spec coverage:** registry row (T2), renderer (T1), gate case (T3), keystone+mirror (T4), tests (T1 count; T2/T3/T4 suite runs), rollout/CHANGELOG/bump (T5) — all spec sections covered. Frontmatter + registry-intro updates covered (T2 steps 1–2).
- **Placeholder scan:** the `[…]` tokens inside the renderer's `#scoring` table are intentional HTML render-placeholders shown to the renderer agent (it fills them from source), not plan TODOs; every plan step carries full content.
- **Type/name consistency:** the renderer name `section-renderer-checkpoint-portfolio` is identical across the agent file (T1), the registry row + shell mapping (T2), and is the token `test_referenced_agents_resolve` checks (T2 step 8). Anchors `#portfolio`/`#scoring`/`#roadmap`/`#validate` are identical across the renderer blocks (T1) and the shell nav mapping (T2 step 5). Route-back phases (6/7) are consistent across registry row, Recording-the-outcome, gate case, and keystone.
