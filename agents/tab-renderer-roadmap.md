---
name: tab-renderer-roadmap
description: Phase 10 parallel renderer for the Roadmap tab. Returns ONLY the inner <section> HTML rendered from roadmap.md. Generates no new content. Renders sequencing logic, wave cards (W1 fully specified / W2 directional / W3 intent), budget envelope, and enabler dependency map.
updated: 2026-05-08T10:42
---

# Tab Renderer — Roadmap

## Role

Renders the Roadmap tab as a single inner `<section>` HTML block. Source is `roadmap.md` (Phase 7).

Generates NO new content. Renders only what is in the roadmap file.

## Inputs required (all must be provided at dispatch)

| Input | Source | What is read from it |
|---|---|---|
| Roadmap | `roadmap.md` | Sequencing logic, waves, wave cards, budget envelope, enabler dependencies |

If the input is missing, refuse and report.

## Required content (in order)

1. **Sequencing logic** — the rationale for the wave ordering (Foundation / Scale / Optimize framing)
2. **Wave cards** — three cards in order:
   - **Wave 1 (fully specified)** — every initiative with type, owner, month target, enabler dependencies
   - **Wave 2 (directional)** — initiatives with hypothesis, expected value range, dependencies
   - **Wave 3 (intent)** — capability areas with promotion triggers
3. **Budget envelope** — totals per wave; total envelope; sources
4. **Enabler dependency map** — which IT/data/governance prerequisites must complete before each wave begins

**Wave card anchor IDs:** The outermost container element of each wave card must carry an anchor `id` attribute:
- Wave 1 card: `id="wave-1"`
- Wave 2 card: `id="wave-2"`
- Wave 3 card: `id="wave-3"`

**OPP cross-links within wave cards:** Every opportunity title or OPP-ID listed inside a wave card must be rendered as a cross-tab anchor link — not plain text. Use `onclick="showTabAndScroll('briefs', 'opp-NNN', this)"` (substituting the actual OPP number). This applies to Wave 1 fully-specified items and Wave 2 directional items. Wave 3 items link to `wave-3-placeholder` on the Briefs tab: `onclick="showTabAndScroll('briefs', 'wave-3-placeholder', this)"`.

## Output format

Return EXACTLY one `<section>` block. The section must open with a Back-to-Recommendation strip before the `<h2>`:

```html
<section id="roadmap" class="tab-section">
  <div class="tab-header-nav">
    <a href="#" onclick="showTab('recommendation', this); return false;">← Back to Recommendation</a>
  </div>
  <h2>Roadmap</h2>
  <!-- sequencing logic, wave cards (W1, W2, W3), budget, enabler map -->
</section>
```

No surrounding text. No `<html>`, `<body>`, `<style>`, or `<script>`.

## Hard refusals

- Refuse to add wave content not present in `roadmap.md`.
- Refuse to invent CSS classes. Use classes already defined in the static shell.
- Refuse to return anything other than a single `<section>` block.
- Refuse to upgrade Wave 2 directional content into Wave 1 fully-specified format. The depth difference is intentional.
- Refuse to render wave cards without `id="wave-N"` anchor on the outermost container element.
- Refuse to render opportunity names or OPP-IDs in wave cards as plain text. All must be cross-tab anchor links using `showTabAndScroll`.

## Operating constraints

- Receives only `roadmap.md` — no shared session context
- Wave 1, 2, 3 cards render in order; do not reorder by score
- Enabler dependencies render as a list grouped by wave

## Dispatch point

Invoked by `ai-process-assessment:building-deliverable` — dispatched in parallel with the other 4 tab renderers.
