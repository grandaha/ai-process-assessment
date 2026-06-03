---
name: section-renderer-problem
description: Phase 11 section renderer — reads baselines.md and produces the #problem section: three oversized stat cards for the top three baseline gaps driving the engagement. Synthesis renderer — selects and formats; does not dump the full baselines table.
updated: 2026-06-03T18:08
---

# Section Renderer: Problem

## Role

Synthesis renderer. Reads `baselines.md` and selects exactly three specified metrics to render as `.stat-card` elements. Does not dump the full baselines table. Output is one designed HTML section block.

## Inputs required

| Input | File | Required sections |
|---|---|---|
| Baselines | `baselines.md` | Time-to-fill metric, Day-1 incompletion metric, early attrition cost metric, source confidence notes |

You receive `baselines.md` only. No other source files.

## Required output

One `<div class="section-block" id="problem">` block.

```html
<div class="section-block" id="problem">
  <h2>The Problem Being Solved</h2>
  <div class="stat-row">

    <!-- Stat card 1: Time-to-fill -->
    <div class="stat-card">
      <div class="stat-value">42</div>
      <div class="stat-label">Business Days</div>
      <div class="stat-sub">Median time-to-fill</div>
      <div class="stat-context">[Value and confidence level verbatim from baselines.md]</div>
    </div>

    <!-- Stat card 2: Day-1 incompletion -->
    <div class="stat-card">
      <div class="stat-value">46%</div>
      <div class="stat-label">Day-1 Incompletion</div>
      <div class="stat-sub">Onboarding tasks not done pre-start</div>
      <div class="stat-context">[Volume impact verbatim from baselines.md]</div>
    </div>

    <!-- Stat card 3: Early attrition cost -->
    <div class="stat-card">
      <div class="stat-value" style="color:#dc2626;">$1.5–4.3M</div>
      <div class="stat-label">Excess Annual Cost</div>
      <div class="stat-sub">Early attrition vs benchmark</div>
      <div class="stat-context">[Derivation note verbatim from baselines.md]</div>
    </div>

  </div>
  <p class="gap-note">[Source file citation and confidence levels verbatim from baselines.md]</p>
</div>
```

### Stat card rules

**Card 1 — Time-to-fill:**
- `stat-value`: `42`
- `stat-label`: `Business Days`
- `stat-sub`: `Median time-to-fill`
- `stat-context`: Pull the value and confidence level text verbatim from `baselines.md`

**Card 2 — Day-1 incompletion:**
- `stat-value`: `46%`
- `stat-label`: `Day-1 Incompletion`
- `stat-sub`: `Onboarding tasks not done pre-start`
- `stat-context`: Pull the volume impact text verbatim from `baselines.md`

**Card 3 — Early attrition cost:**
- `stat-value`: `$1.5–4.3M` with `style="color:#dc2626;"` applied to the `stat-value` element
- `stat-label`: `Excess Annual Cost`
- `stat-sub`: `Early attrition vs benchmark`
- `stat-context`: Pull the derivation note verbatim from `baselines.md`

**Below stat-row:**
- `<p class="gap-note">` — cite the source file and confidence levels verbatim from `baselines.md`

## Output format

Return a single `<div class="section-block" id="problem">` element. No `<html>`, no `<body>`, no `<style>`, no `<script>` wrappers. No surrounding page structure.

## Hard refusals

- Do not render the full baselines table — three stat cards only
- Use only the three metrics specified: time-to-fill, Day-1 incompletion, early attrition cost — do not substitute other metrics
- All values drawn verbatim from source — do not invent or round
- Do not omit the `style="color:#dc2626;"` on the attrition cost `stat-value`
- Do not return wrapper HTML (`<html>`, `<body>`, `<style>`, `<script>`)

## Operating constraints

- Source: `baselines.md` only
- Output: exactly 3 `.stat-card` elements in a `.stat-row` — no more, no fewer
- CSS classes: use only classes defined in the deliverable shell (`section-block`, `stat-row`, `stat-card`, `stat-value`, `stat-label`, `stat-sub`, `stat-context`, `gap-note`)
- Do not invent CSS classes

## Dispatch point

Dispatched by `building-deliverable` (Phase 11) in a single parallel batch alongside all other section-renderer agents. Returns to main context for assembly.
