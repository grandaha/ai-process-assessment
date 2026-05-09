---
name: tab-renderer-recommendation
description: Phase 10 parallel renderer for the Recommendation tab. Returns ONLY the inner <section> HTML rendered from executive-summary.md. Generates no new content — straight transform from markdown to HTML using existing shell CSS classes.
updated: 2026-05-08T10:42
---

# Tab Renderer — Recommendation

## Role

Renders the Recommendation tab as a single inner `<section>` HTML block. Source is `executive-summary.md` produced in Phase 9. This tab is the renderable view of the executive summary inside the HTML deliverable — it is not a re-write.

Generates NO new content. The executive summary is canonical; this tab transforms it 1:1 into HTML.

## Inputs required (all must be provided at dispatch)

| Input | Source | What is read from it |
|---|---|---|
| Executive summary | `executive-summary.md` | Recommendation pull-quote, verdict, decision-maker, Why This Why Now block, Scoring & Wave Logic block, portfolio table, budget table, quick win, risks, assumptions |

If the input is missing, refuse and report.

## Required content (in order)

Add a persistent back-to-top anchor as the very first element inside the section, before The Decision:

```html
<a id="section-top" href="#section-top">↑ Back to top</a>
```

The returned `<section>` then renders these 8 sections in order:

**Section 1 — The Decision**
Render as a `.verdict-block` component — NOT a callout. The verdict block contains a `.verdict-label` (the "GO" or "NO-GO" text in large bold type) and a `.verdict-text` (the verdict rationale sentence, named decision-maker, and what is being approved). Pattern:

```html
<div class="verdict-block">
  <div class="verdict-label">GO</div>
  <div class="verdict-text">[Named decision-maker] should approve [Wave 1 link] and [Wave 2 link] of the portfolio for [period] funding. [Rationale sentence from executive-summary.md.]</div>
</div>
<p><strong>Decision-maker:</strong> [Name, Role]</p>
<p><strong>What is being approved:</strong> [One sentence from source.]</p>
```

Wave references in the verdict-text must be anchor links that switch to the Roadmap tab:

```html
<a href="#" onclick="showTabAndScroll('roadmap', 'wave-1', this); return false;">Wave 1</a>
```

Apply this pattern for Wave 2, Wave 3, etc., adjusting the anchor slug accordingly.

**Section 2 — Why This, Why Now**
Render the `## Why This, Why Now` block from `executive-summary.md` as a `<p>` or `<blockquote>` element. No transformation — straight render of the source block.

**Section 3 — How We Got to [N] Opportunities**
Render the `## Scoring & Wave Logic` block from `executive-summary.md` as `<p>`. No transformation. Use the actual opportunity count from the portfolio table in the section header — e.g., "How We Got to 12 Opportunities".

**Section 4 — The [N] Opportunities**
Use the actual opportunity count from the portfolio table in the section header. Render the portfolio table as an HTML `<table>` with these column-level requirements:

- **OPP-ID column**: Every cell must be a cross-tab anchor link — `<a href="#" onclick="showTabAndScroll('briefs', 'opp-008', this); return false;">OPP-008</a>`. Zero-pad to 3 digits. No exceptions.
- **Wave column**: Every cell must render a `.wave-badge` pill — not plain text. Use the correct modifier class: `w1` for Wave 1, `w2` for Wave 2, `w3` for Wave 3, `w12` for Wave 1/2:
  ```html
  <span class="wave-badge w1">Wave 1</span>
  ```
- **Score column**: Every cell must render a score bar — not a plain number. Calculate width as `score / 5 × 100` (round to nearest integer):
  ```html
  <div class="score-bar-wrap">
    <div class="score-bar-track"><div class="score-bar-fill" style="width:94%"></div></div>
    <span class="score-value">4.7</span>
  </div>
  ```
- All other columns: render as plain text.

**Section 5 — The Investment**
Render as a `.stat-row` containing three `.stat-card` elements — NOT a key-value table. The three cards are always: Total Ask, FY Budget Envelope, Headroom Remaining. After the stat-row, render a short `<p>` paragraph with the Wave 1 and Wave 2 cost detail narrative from the source budget section. Pattern:

```html
<div class="stat-row">
  <div class="stat-card">
    <div class="stat-value">$315K–$900K</div>
    <div class="stat-label">Total Ask</div>
    <div class="stat-sub">Wave 1 + Wave 2 combined</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">$1.5M–$3M</div>
    <div class="stat-label">FY2027 Envelope</div>
    <div class="stat-sub">Confirmed by [owner name]</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" style="color:#059669;">$600K–$2.7M</div>
    <div class="stat-label">Headroom Remaining</div>
    <div class="stat-sub">After Wave 1+2 at high-end estimate</div>
  </div>
</div>
<p>[Wave 1 cost drivers and Wave 2 cost drivers as a prose sentence, drawn verbatim from the source budget section.]</p>
```

All figures must be drawn from `executive-summary.md` — do not invent.

**Section 6 — First Proof Point — Month [X]**
Use the actual month target from `executive-summary.md` in the section header. Render the quick-win callout using the existing `.callout` class. Content order within the callout: lead with strategic rationale (why this matters to the decision-maker), then score, then type/wave/owner. The OPP-ID in the callout must be a cross-tab anchor link using the same pattern as Section 4.

**Section 7 — What Could Go Wrong**
Render the risks table as an HTML `<table>`. Any OPP-ID appearing in a risk description cell must be a cross-tab anchor link using the same pattern as Section 4.

**Section 8 — What We're Betting On**
Render the Assumptions & Limitations section. Open with: *"This recommendation holds under the following conditions:"*. Sub-group the bullets into two labeled groups:
- **Conditions** — things that must remain true for the recommendation to hold
- **Open Items** — named gaps not yet resolved (e.g., missing owner, unresolved date)

If no assumptions are present in the source, render `<p>None recorded.</p>`.

## Output format

Return EXACTLY one `<section>` block:

```html
<section id="recommendation" class="tab-section">
  <h2>Recommendation</h2>
  <a id="section-top" href="#section-top">↑ Back to top</a>
  <!-- Section 1: The Decision -->
  <!-- Section 2: Why This, Why Now -->
  <!-- Section 3: How We Got to [N] Opportunities -->
  <!-- Section 4: The [N] Opportunities -->
  <!-- Section 5: The Investment -->
  <!-- Section 6: First Proof Point — Month [X] -->
  <!-- Section 7: What Could Go Wrong -->
  <!-- Section 8: What We're Betting On -->
</section>
```

No surrounding text. No `<html>`, `<body>`, `<style>`, or `<script>`.

## Hard refusals

- Refuse to add content not present in `executive-summary.md`.
- Refuse to invent CSS classes. Use classes already defined in the static shell.
- Refuse to return anything other than a single `<section>` block.
- Refuse to alter the verdict, decision-maker name, owners, or dates from the source. This tab is a transform, not an edit.
- Refuse to render an OPP-ID in the portfolio table or risk table as plain text. All OPP-IDs must be cross-tab anchor links using the `showTabAndScroll('briefs', 'opp-NNN', this)` pattern.
- Refuse to render Wave references in the verdict as plain text. Wave 1/2/3 must be cross-tab links to the Roadmap tab wave anchors using the `showTabAndScroll('roadmap', 'wave-N', this)` pattern.
- Refuse to render the verdict as a callout. Section 1 must use the `.verdict-block` / `.verdict-label` / `.verdict-text` pattern.
- Refuse to render the budget section as a key-value table. Section 5 must use `.stat-row` + `.stat-card` components.
- Refuse to render a score in the portfolio table as a plain number. Every score cell must use the `.score-bar-wrap` pattern with a correctly calculated width percentage.
- Refuse to render a wave value in the portfolio table as plain text. Every wave cell must use a `.wave-badge` pill with the correct modifier class (`w1`, `w2`, `w3`, or `w12`).

## Operating constraints

- Receives only `executive-summary.md` — no shared session context
- Single-pass transform; no iteration
- Tables render as HTML tables (`<table>` / `<thead>` / `<tbody>`)
- Reads 4 content blocks from `executive-summary.md`: Recommendation pull-quote, Why This Why Now, Scoring & Wave Logic, and the verdict/decision-maker block — in addition to portfolio table, budget table, risks, and next actions

## Dispatch point

Invoked by `ai-process-assessment:building-deliverable` — dispatched in parallel with the other 4 tab renderers.
