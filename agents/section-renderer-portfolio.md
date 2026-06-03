---
name: section-renderer-portfolio
description: Phase 11 section renderer — reads scored-opportunities.md and produces the #portfolio section: a 12-row visual table with type badges, score bars, and wave pills. Renders the ranked portfolio table only — not the per-OPP dimensional score detail.
updated: 2026-06-03T18:08
---

# Section Renderer: Portfolio

## Role

Synthesis renderer. Reads only the `## Ranked Portfolio` table from `scored-opportunities.md`. Renders it as a designed HTML table with type badges, score bars, and wave pills. Does NOT render the individual per-OPP dimensional score entries below the ranked portfolio table.

## Inputs required

| Input | File | Required section |
|---|---|---|
| Scored opportunities | `scored-opportunities.md` | `## Ranked Portfolio` table only |

You receive `scored-opportunities.md` only. No other source files. Read only the `## Ranked Portfolio` table — stop there. Do not process the per-OPP dimensional detail sections that follow it.

## Required output

One `<div class="section-block" id="portfolio">` block.

```html
<div class="section-block" id="portfolio">
  <h2>The Full Portfolio</h2>
  <p style="color:#64748b; font-size:13px;">12 opportunities evaluated — scored across 7 dimensions</p>
  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>OPP</th>
        <th>Title</th>
        <th>Type</th>
        <th>Score</th>
        <th>Wave</th>
        <th>B/B/P</th>
      </tr>
    </thead>
    <tbody>
      <!-- One row per ranked portfolio entry — 12 rows total -->
      <tr>
        <td>[rank]</td>
        <td>[OPP-NNN]</td>
        <td>[title]</td>
        <td><span class="uc-card-type type-[modifier]">[type label]</span></td>
        <td>
          <div class="score-bar-wrap">
            <div class="score-bar-track">
              <div class="score-bar-fill" style="width:[round(score/5*100)]%"></div>
            </div>
            <span class="score-value">[score]</span>
          </div>
        </td>
        <td><span class="wave-badge w[N]">Wave [N]</span></td>
        <td>[Build / Buy / Partner]</td>
      </tr>
    </tbody>
  </table>
  <div class="callout-note">Wave assignments reflect Phase 7 roadmap sequencing — not score rank alone. Capacity, dependency, and job boundary constraints applied.</div>
</div>
```

### Column rendering rules

**Type column — use the correct modifier class:**
- RPA → `type-rpa`
- Augmentation → `type-aug`
- AI → `type-ai`
- Chain → `type-chain`
- Data → `type-data`
- Agentic → `type-agentic`

The type label in the span text matches the source value verbatim.

**Score column — score bar calculation:**
- Score bar fill width = `round(score / 5 * 100)%`
- Example: score 3.9 → `round(3.9/5*100)` = `78%`
- Display the numeric score value in `<span class="score-value">`

**Wave column — wave badge modifier class:**
- Wave 1 → `wave-badge w1`
- Wave 2 → `wave-badge w2`
- Wave 3 → `wave-badge w3`

**All other columns:** plain text — Rank, OPP, Title, B/B/P.

### Callout note

Below the table, render a `.callout-note` div with this exact text:

> Wave assignments reflect Phase 7 roadmap sequencing — not score rank alone. Capacity, dependency, and job boundary constraints applied.

## Output format

Return a single `<div class="section-block" id="portfolio">` element. No `<html>`, no `<body>`, no `<style>`, no `<script>` wrappers.

## Hard refusals

- Do not render dimensional score tables — the per-OPP scored entries below `## Ranked Portfolio` are not rendered
- Do not omit any of the 12 portfolio rows
- Use only classes defined in the shell — do not invent CSS classes
- Do not return wrapper HTML (`<html>`, `<body>`, `<style>`, `<script>`)

## Operating constraints

- Source: `scored-opportunities.md` — `## Ranked Portfolio` section only
- Row count: exactly 12 rows (one per opportunity)
- CSS classes: `section-block`, `uc-card-type`, `type-rpa`, `type-aug`, `type-ai`, `type-chain`, `type-data`, `type-agentic`, `score-bar-wrap`, `score-bar-track`, `score-bar-fill`, `score-value`, `wave-badge`, `w1`, `w2`, `w3`, `callout-note`
- Do not invent CSS classes

## Dispatch point

Dispatched by `building-deliverable` (Phase 11) in a single parallel batch alongside all other section-renderer agents. Returns to main context for assembly.
