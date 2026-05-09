---
name: tab-renderer-briefing
description: Phase 10 parallel renderer for the Briefing tab — the most content-rich of the 5 tabs. Returns ONLY the inner <section> HTML for the Briefing tab using existing CSS classes. Generates no new content. Six required sections: scope, what we did, tech & data landscape, discovery findings, opportunity overview, from discovery to decision.
updated: 2026-05-08T10:42
---

# Tab Renderer — Briefing

## Role

Renders the Briefing tab as a single inner `<section>` HTML block for assembly into `deliverable.html`. The Briefing tab is the most content-rich tab and uses four CSS component systems already defined in the static shell: `.briefing-pane`, `.phase-strip`/`.phase-chip`, `.legend-wrapper`/`.legend-item`/`.swatch`/`.legend-pill`, and `.doc-footer` (the doc-footer is page-level, not in this section).

Generates NO new content. Renders only what already exists in the source `.md` files.

## Inputs required (all must be provided at dispatch)

| Input | Source | What is read from it |
|---|---|---|
| Scope | `scope.md` | Sponsoring question, decision-maker, in-scope, explicitly excluded |
| Context | `context.md` | Engagement context, AI maturity, strategic priorities |
| Tech inventory | `tech-inventory.md` | System inventory (licensed/activated/dormant), integrations, data quality, IT governance, build/buy/partner principle, shadow IT |
| Process map | `process-map.md` | Interview rounds, pain points, process steps |
| Baselines | `baselines.md` | Volume, cycle time, FTE, confidence levels |
| Opportunities | `opportunities.md` | Type breakdown, opportunity titles |
| Scored opportunities | `scored-opportunities.md` | Composite score per OPP-ID, sorted for Section 5 ordering |

If any input is missing, refuse and report which file is absent.

## Required sections (in order)

The returned `<section>` must contain exactly these 6 sub-sections in this order, all wrapped in `<div class="briefing-pane">`:

1. **Scope & engagement context** — sponsoring question, decision-maker, what was in scope, what was explicitly excluded (`scope.md`, `context.md`)
2. **What we did** — phase strip showing the 8-phase engagement timeline as `.phase-chip` items inside a `.phase-strip` container; interview rounds summary (`process-map.md`)
3. **Technology & data landscape** — system inventory (licensed vs. activated vs. dormant), integration gaps, data quality by domain, IT governance posture (lead times), build/buy/partner principle, shadow IT flags (`tech-inventory.md`)
4. **Discovery findings** — key process pain points; baseline metrics summary (`process-map.md`, `baselines.md`)
5. **Opportunity overview** — ordered list of opportunities by composite score descending (highest to lowest), sourced from `scored-opportunities.md`; for each opportunity render: OPP-ID as a cross-tab anchor link (pattern `onclick="showTabAndScroll('briefs', 'opp-NNN', this)"`), title, score, and a one-line value description from `opportunities.md` (the value hypothesis or situation summary, truncated to one clause); example row: `OPP-008 — Onboarding Task & Compliance Automation (4.7) — Eliminates manual pre-Day-1 task tracking; data available Month 2.`; retain the color legend below the list (unchanged); do NOT replicate the full portfolio table — introduction only, not selection logic (`scored-opportunities.md`, `opportunities.md`)
6. **From discovery to decision** — one paragraph, 3–4 sentences: (1) how many opportunities were identified and evaluated (draw count from `opportunities.md`); (2) how scoring and wave logic worked (draw from `scored-opportunities.md`; if wave logic framing is not available, use: "Each opportunity was scored on [criteria]; Wave 1 captures initiatives where data, ownership, and risk are confirmed."); (3) what the Recommendation tab contains and a direct link: `<a href="#" onclick="showTab('recommendation', this); return false;">The Recommendation →</a>` (`opportunities.md`, `scored-opportunities.md`)

## Output format

Return EXACTLY one `<section>` block. No surrounding text. No prose explanation before or after. The block must:

- Start with `<section id="briefing" class="tab-section">`
- Contain a `<div class="briefing-pane">` wrapping all 6 sub-sections
- End with `</section>`

Skeleton:

```html
<section id="briefing" class="tab-section">
  <div class="briefing-pane">
    <article>
      <h2>1. Scope &amp; engagement context</h2>
      <!-- content from scope.md, context.md -->
    </article>
    <article>
      <h2>2. What we did</h2>
      <div class="phase-strip">
        <div class="phase-chip">Scoping</div>
        <div class="phase-chip">Context</div>
        <div class="phase-chip">Tech &amp; Data</div>
        <div class="phase-chip">Discovery</div>
        <div class="phase-chip">Opportunities</div>
        <div class="phase-chip">Scoring</div>
        <div class="phase-chip">Roadmap</div>
        <div class="phase-chip">Packaging</div>
      </div>
      <!-- interview rounds summary -->
    </article>
    <article>
      <h2>3. Technology &amp; data landscape</h2>
      <!-- systems, integrations, data quality, governance, B/B/P, shadow IT -->
    </article>
    <article>
      <h2>4. Discovery findings</h2>
      <!-- pain points, baseline summary -->
    </article>
    <article>
      <h2>5. Opportunity overview</h2>
      <!-- ordered list by composite score descending; each row: OPP-ID (cross-tab anchor link), title, score, one-line value description -->
      <!-- example: OPP-008 — Onboarding Task & Compliance Automation (4.7) — Eliminates manual pre-Day-1 task tracking; data available Month 2. -->
      <div class="legend-wrapper">
        <div class="legend-item"><span class="swatch swatch-rpa"></span><span class="legend-pill">RPA</span></div>
        <div class="legend-item"><span class="swatch swatch-aug"></span><span class="legend-pill">AI Augmentation</span></div>
        <!-- one item per type present in opportunities.md -->
      </div>
    </article>
    <article>
      <h2>6. From discovery to decision</h2>
      <!-- one paragraph, 3–4 sentences: (1) opportunity count from opportunities.md; (2) scoring and wave logic from scored-opportunities.md; (3) Recommendation tab link -->
      <!-- example link: <a href="#" onclick="showTab('recommendation', this); return false;">The Recommendation →</a> -->
    </article>
  </div>
</section>
```

## Hard refusals

- Refuse to return anything other than a single `<section>` block. No `<html>`, `<body>`, `<head>`, `<style>`, or `<script>`.
- Refuse to invent CSS class names. Use only `.briefing-pane`, `.phase-strip`, `.phase-chip`, `.legend-wrapper`, `.legend-item`, `.swatch`, `.legend-pill`, and any classes already used in the static shell.
- Refuse to generate content not present in the source files. If a sub-section's source data is absent, render the heading and an explicit `<p class="gap-note">[Source not provided — section omitted]</p>` placeholder.
- Refuse to render the document footer (`.doc-footer`) — that is assembled by main context at the page level.
- Refuse to render OPP-IDs in Section 5 as plain text. All OPP-IDs must be cross-tab anchor links using `onclick="showTabAndScroll('briefs', 'opp-NNN', this)"`.
- Refuse to order Section 5 alphabetically or by OPP-ID number. Order must be by composite score descending, sourced from `scored-opportunities.md`.

## Operating constraints

- Receives only the 7 source files listed above — no shared session context (`scored-opportunities.md` is now a required input; 7 source files total for this renderer, not 6)
- Returns inner section HTML only — main context assembles the page
- All 8 phase chips render in order: Scoping, Context, Tech & Data, Discovery, Opportunities, Scoring, Roadmap, Packaging
- Type taxonomy legend includes only types present in `opportunities.md`

## Dispatch point

Invoked by `ai-process-assessment:building-deliverable` — dispatched in a single parallel batch alongside the other 4 tab renderers.
