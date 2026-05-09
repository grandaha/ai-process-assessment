---
name: ai-process-assessment:building-deliverable
description: Phase 10 — assembles a self-contained client-ready HTML deliverable (deliverable.html) by dispatching 5 tab-renderer agents in parallel and concatenating their output sections into a static shell. Generates no new content — renders existing .md files.
updated: 2026-05-08T10:44
---

# Phase 10: Building the HTML Deliverable

## Role in the system

The HTML deliverable is the client-facing single-page artifact that synthesizes all engagement outputs into a single readable file. It is the final delivery package.

Phase 10 produces NO new content. Every section traces to a named source `.md` file from prior phases. If a section is wrong, the fix is in the source file — re-run the relevant tab-renderer agent against the corrected source. Do not edit the HTML directly to patch source-file errors.

## Gate condition

`executive-summary.md` exists in the engagement folder. (Implicit: `deliverable-gate` clearance is required, since Phase 9 cannot complete without it.) This skill creates `deliverable.html`.

## Tab structure

The deliverable contains exactly 5 tabs, in this order:

| Tab | Content | Source files |
|---|---|---|
| Briefing | Engagement context, discovery narrative, tech & data landscape, opportunity overview | `scope.md`, `context.md`, `tech-inventory.md`, `process-map.md`, `baselines.md`, `opportunities.md`, `scored-opportunities.md` |
| Recommendation | Verdict, budget ask, portfolio table, quick-win callout, key risks, assumptions & limitations | `executive-summary.md` |
| Roadmap | Sequencing logic, wave cards (W1 fully specified / W2 directional / W3 intent), budget envelope, enabler dependency map | `roadmap.md` |
| Use Case Briefs | Portfolio at a Glance, Wave 1 SCRA briefs (full 11-field), Wave 2 summaries, Wave 3 placeholder | `usecase-briefs.md` |
| Evidence | Phase completion log, GRC gate clearance records, deliverable-gate four-dimension results, package manifest, stakeholder interview log | `evidence-log.md` |

## Required CSS components

All CSS component systems defined in the static shell must be used. Tab-renderer agents must not invent new CSS classes — if a new class is genuinely needed, it must be added to the static shell and documented here first.

### Structural / layout components

| CSS class | Purpose | Used in |
|---|---|---|
| `.briefing-pane` and children | Editorial narrative section with DM Serif Display, numbered sections, vision block, AI callouts | Briefing tab |
| `.phase-strip` / `.phase-chip` | Horizontal timeline showing 8 phases as chips | Briefing tab — "What we did" section |
| `.legend-wrapper` / `.legend-item` / `.swatch` / `.legend-pill` | Type taxonomy color-swatch legend | Briefing tab — opportunity overview |
| `.doc-footer` | Document footer with border-top separator | Bottom of page — confidentiality, preparer, date |
| `.tab-header-nav` | Back-to-Recommendation strip at the top of secondary tabs | Roadmap, Briefs, Evidence tabs |
| `.brief-nav` | Breadcrumb nav on Wave 1 brief cards | Use Case Briefs tab |
| `.brief-pagination` | Prev/Next navigation on Wave 1 brief cards | Use Case Briefs tab |

### Data visualization components (Recommendation tab)

| CSS class | Purpose | Used in |
|---|---|---|
| `.verdict-block` / `.verdict-label` / `.verdict-text` | Bold Go/No-Go verdict block — large colored label + rationale text | Recommendation tab — Section 1 (The Decision) |
| `.stat-row` | CSS grid wrapper for stat cards (auto-fit columns, min 180px) | Recommendation tab — Section 5 (The Investment) |
| `.stat-card` / `.stat-value` / `.stat-label` / `.stat-sub` | KPI card with large bold number, uppercase label, sub-note | Recommendation tab — Section 5 (The Investment) |
| `.score-bar-wrap` / `.score-bar-track` / `.score-bar-fill` / `.score-value` | Horizontal score bar with numeric value; fill width = score/5 × 100% | Recommendation tab — portfolio table Score column |
| `.wave-badge` + `.w1` / `.w2` / `.w3` / `.w12` | Color-coded wave pill badges (green/blue/gray/amber) | Recommendation tab — portfolio table Wave column |

### Callout variants

| CSS class | Purpose | Used in |
|---|---|---|
| `.callout` | Standard informational callout (blue left border) | Multiple tabs |
| `.callout-highlight` | Success callout (green left border) | Multiple tabs |
| `.callout-warning` | Warning callout (amber left border) | Multiple tabs |
| `.callout-note` | Muted callout (slate left border) | Multiple tabs |
| `.callout-success` | Success callout — distinct from `.callout-highlight`; use for First Proof Point | Recommendation tab — Section 6 |
| `.gap-note` | Gray italic text for data gaps | Multiple tabs |

## Interoperability conventions

All cross-tab and within-tab links in the deliverable follow these conventions:

### Anchor ID format
- Opportunity anchors: `id="opp-NNN"` (zero-padded 3 digits, e.g., `id="opp-008"`)
- Wave anchors: `id="wave-1"`, `id="wave-2"`, `id="wave-3"`
- Wave 3 briefs placeholder: `id="wave-3-placeholder"`
- Tab-level back-to-top: `id="section-top"` on the Recommendation tab

### JS helper function (add to static shell)
The static shell must include a `showTabAndScroll(tabId, anchorId, btn)` helper alongside the existing `showTab()`:

```js
function showTabAndScroll(tabId, anchorId, btn) {
  showTab(tabId, null);
  if (anchorId) {
    setTimeout(function() {
      var el = document.getElementById(anchorId);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  }
}
```

### Cross-tab link patterns
For links that switch tab AND scroll to anchor:
```
onclick="showTabAndScroll('briefs', 'opp-008', this); return false;"
```

For links that switch tab only:
```
onclick="showTab('recommendation', null); return false;"
```

For same-tab scroll links (within Briefs tab):
```
href="#opp-008"
```

### Visual distinction rule
Cross-tab links (tab-switching) must be visually distinct from same-tab scroll links.
Recommended: cross-tab links use a small icon (→) or styled differently in the shell CSS.
Tab-renderer agents MUST NOT invent new CSS classes — if a distinction class is needed, it must be added to the static shell and documented here first.

## Phase checklist

- [ ] Confirm `executive-summary.md` exists in the engagement folder
- [ ] Confirm all source files for all 5 tabs exist
- [ ] In a single tool-call batch, dispatch all 5 tab-renderer agents in parallel:
  - `tab-renderer-briefing` ← scope.md, context.md, tech-inventory.md, process-map.md, baselines.md, opportunities.md, scored-opportunities.md
  - `tab-renderer-recommendation` ← executive-summary.md
  - `tab-renderer-roadmap` ← roadmap.md
  - `tab-renderer-briefs` ← usecase-briefs.md
  - `tab-renderer-evidence` ← evidence-log.md
- [ ] Collect all 5 returned `<section>` blocks
- [ ] Verify each return is a single `<section>` block — no `<html>`, no `<body>`, no `<style>`, no `<script>`. If any agent returns wrapper markup, reject and re-dispatch.
- [ ] Assemble the final file in main context: static shell (CSS + JS + masthead + tab nav) + 5 tab sections + `.doc-footer`
- [ ] Confirm the static shell includes the `showTabAndScroll()` helper function
- [ ] Confirm anchor ID convention is consistent across all 5 sections (spot-check: verify `id="opp-001"` through the highest OPP-ID exist in the Briefs section; verify `id="wave-1"`, `id="wave-2"`, `id="wave-3"` exist in the Roadmap section)
- [ ] Write `docs/engagements/<engagement>/deliverable.html`
- [ ] Open the file and visually confirm: 5 tabs render, tab navigation works, no missing-class styling artifacts

## Assembly pattern

Main context performs assembly only — it generates no content.

```
CSS + JS + masthead + tab nav
  + [briefing section from tab-renderer-briefing]
  + [recommendation section from tab-renderer-recommendation]
  + [roadmap section from tab-renderer-roadmap]
  + [briefs section from tab-renderer-briefs]
  + [evidence section from tab-renderer-evidence]
  + .doc-footer
→ write deliverable.html
```

The static shell (CSS, JS, masthead, tab nav) lives in main context. Tab agents return only inner `<section>` content.

## Optional second fan-out — Briefs tab

The `tab-renderer-briefs` agent handles 10 items: 5 full Wave 1 SCRA briefs (heavy), 4 Wave 2 summaries, 1 Wave 3 placeholder. The briefs tab renderer MAY itself dispatch 5 brief-card sub-agents in parallel (one per Wave 1 UC) and assemble the tab internally before returning. This keeps Wave 1 brief detail out of both main context and the tab renderer's window.

This second fan-out is at the tab renderer's discretion, based on the size of `usecase-briefs.md`. The Phase 10 skill does not mandate it.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "Just write the HTML in main context — fan-out is overkill." | All 5 tabs in one context window blows the budget on a single engagement. The fan-out exists to keep main context clean for assembly. |
| "Generate any missing content here — the source file has a gap." | Phase 10 generates no content. A gap in the source is a Phase 1–9 problem. Fix the source, re-run the tab agent. |
| "Tab agents can return full HTML pages — easier to assemble." | Five full pages cannot be concatenated into one. Agents return inner `<section>` only. Wrapper markup from agents is rejected. |
| "Invent a CSS class if you need a new visual." | The shell defines the design system. Inventing classes breaks the package and bypasses design review. Use existing classes; if a new one is genuinely needed, that is a shell change, not a tab change. |
| "Skip the document footer — the masthead has the date." | The `.doc-footer` is part of the design system and carries confidentiality + preparer info. Omitting it ships an incomplete artifact. |
| "The briefs tab is too big — drop Wave 2 summaries." | Wave 2 summaries are commitments. The optional brief-card sub-fan-out exists exactly to handle the size — use it. |
| "The interoperability links can be added after assembly." | Cross-tab links depend on anchor IDs that must be set by the tab renderers. Assembly-time patching is fragile and error-prone. The renderers own the anchors; the skill owns the convention. |

## Chain to next skill

Terminal — Phase 10 completes the methodology output sequence. On successful write, `deliverable.html` may be shared externally alongside `executive-summary.md`. Any subsequent change to source `.md` files requires re-running the affected tab agent and reassembling the deliverable.

## Completion Confirmation

After writing `deliverable.html`, Janice must present the deliverable to the user:

1. **Name the file written** and its path
2. **Confirm all 5 tabs rendered** — name each tab
3. **Flag any visual artifacts** noted during the open/confirm step
4. **Invite the user to review** the deliverable and provide feedback

This is the end of the methodology chain. No further phase is invoked unless the user requests a re-run or revision.
