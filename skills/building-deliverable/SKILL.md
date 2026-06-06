---
name: ai-process-assessment:building-deliverable
description: Phase 11 — assembles a single-scroll client-facing HTML deliverable (deliverable.html) by dispatching 5 section-renderer agents in parallel and interleaving their returned blocks into the correct page order. Synthesis renderers — not document converters. Each renderer distills its source to specified density.
updated: 2026-06-03T18:08
---

# Phase 11: Building the HTML Deliverable

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `executive-summary.md` and confirm it exists.

Gate condition: `executive-summary.md` must be present before proceeding.

## Role in the system

The HTML deliverable is the client-facing single-scroll artifact that synthesizes all engagement outputs into a single readable page. It is the final delivery package.

Phase 11 produces NO new content. Every section traces to a named source `.md` file from prior phases. If a section is wrong, the fix is in the source file — re-run the affected section-renderer agent against the corrected source. Do not edit the HTML directly to patch source-file errors.

Synthesis renderers receive specific sections to extract at specified density — not raw file dumps. They distill to the stated format. If an agent returns more than the specified output, reject it and re-dispatch with the constraint re-stated.

## Gate condition

`executive-summary.md` exists in the engagement folder. (Implicit: `deliverable-gate` clearance is required, since Phase 9 cannot complete without it.) This skill creates `deliverable.html`.

## Section structure

The deliverable contains exactly 9 sections in this scroll order:

| Section | Content summary | Source agent | Anchor ID |
|---|---|---|---|
| Verdict | GO/NO-GO verdict, pull-quote, 3 why-now bullets | section-renderer-executive (block 1) | `#verdict` |
| Problem | 3 oversized stat cards (time-to-fill, Day-1 incompletion, attrition cost) | section-renderer-problem | `#problem` |
| Portfolio | 12-row visual portfolio table with type badges, score bars, wave pills | section-renderer-portfolio | `#portfolio` |
| Use Cases | 7 compact Wave 1 initiative cards in a grid | section-renderer-roadmap (block 1) | `#usecases` |
| Roadmap | 3-band wave timeline graphic | section-renderer-roadmap (block 2) | `#roadmap` |
| Investment | 4 stat cards + ROM note | section-renderer-roadmap (block 3) | `#investment` |
| Top Risks | Compact 3-column risk table | section-renderer-executive (block 2) | `#risks` |
| Actions | Next actions table | section-renderer-executive (block 3) | `#actions` |
| Evidence | Phase completion chips + gate callouts | section-renderer-evidence | `#evidence` |

## Required CSS components

All CSS component systems below must be embedded in the static shell. Section-renderer agents must not invent new CSS classes. If a new class is genuinely needed, it must be added to the static shell and documented here first.

### Structural / layout components

| CSS class | Purpose | Used in |
|---|---|---|
| `.sticky-nav` | Sticky top navigation bar — links to all 9 section anchors | Page-level — top of body |
| `.sticky-nav a` | Nav link style — 11px bold uppercase, slate color | Sticky nav |
| `.section-block` | Padded scrollable content section with bottom border; `scroll-margin-top: 52px` for sticky nav offset | All 9 sections |
| `.section-block h2` | Section heading — 20px bold | All sections |
| `.doc-footer` | Document footer with border-top separator — confidentiality, preparer, date | Bottom of page |

### Stat card components

| CSS class | Purpose | Used in |
|---|---|---|
| `.stat-row` | CSS grid wrapper for stat cards (auto-fit columns, min 180px) | Problem section, Investment section |
| `.stat-card` / `.stat-value` / `.stat-label` / `.stat-sub` | KPI card with large bold number, uppercase label, sub-note | Problem section, Investment section |
| `.stat-context` | Supplementary context line below stat-sub — 11px slate gray | Problem section, Investment section |

### Verdict components

| CSS class | Purpose | Used in |
|---|---|---|
| `.verdict-block` / `.verdict-label` / `.verdict-text` | Bold GO/NO-GO verdict block — large colored label + rationale text | Verdict section |

### Score bar components

| CSS class | Purpose | Used in |
|---|---|---|
| `.score-bar-wrap` / `.score-bar-track` / `.score-bar-fill` / `.score-value` | Horizontal score bar with numeric value; fill width = score/5 × 100% | Portfolio table, Use Cases grid |

### Wave components

| CSS class | Purpose | Used in |
|---|---|---|
| `.wave-badge` + `.w1` / `.w2` / `.w3` | Color-coded wave pill badges (green/blue/gray) | Portfolio table, Use Cases grid |
| `.wave-timeline` | 3-band container for wave roadmap — flexbox, rounded, overflow hidden | Roadmap section |
| `.wave-band` | Individual wave band — flex 1, padded | Roadmap section |
| `.wave-band.w1` / `.wave-band.w2` / `.wave-band.w3` | Wave band background and border colors | Roadmap section |
| `.wave-band-label` | Small uppercase band label (e.g., "Wave 1 · Foundation") | Roadmap section |
| `.wave-band-horizon` | Large bold horizon text (e.g., "Months 0–6") — color varies by wave | Roadmap section |
| `.wave-pills` | Flex wrapping container for wave pills | Roadmap section |
| `.wave-pill` | Individual initiative pill — rounded, muted background | Roadmap section |
| `.wave-band-note` | Small muted note below pills | Roadmap section |

### Use case card components

| CSS class | Purpose | Used in |
|---|---|---|
| `.uc-grid` | CSS grid for use case cards — auto-fit, min 360px columns | Use Cases section |
| `.uc-card` | Individual use case card — bordered, rounded, flex column | Use Cases section |
| `.uc-card-header` | Card header — flex row, type badge + score bar | Use Cases section |
| `.uc-card-title` | Card title — 14px bold | Use Cases section |
| `.uc-card-body` | Card body — padded flex column | Use Cases section |
| `.uc-card-type` | Type badge — 11px pill with modifier class | Portfolio table, Use Cases cards |
| `.uc-problem` | Problem statement text — 13px, line-height 1.5 | Use Cases cards |
| `.uc-outcome` | Outcome statement — 12px bold green on green-tint background | Use Cases cards |
| `.uc-meta` | Meta row — flex wrap, 11px slate | Use Cases cards |
| `.uc-quickwin` | Quick-win badge — yellow tint, 10px bold | Use Cases cards |

### Type badge modifier classes

| CSS class | Type | Colors |
|---|---|---|
| `.type-rpa` | RPA | slate background, slate text |
| `.type-aug` | Augmentation | purple-tint background, purple text |
| `.type-ai` | AI | blue-tint background, blue text |
| `.type-chain` | Chain | teal-tint background, teal text |
| `.type-data` | Data | amber-tint background, amber text |
| `.type-agentic` | Agentic | orange-tint background, orange text |

### Phase completion log components (evidence section)

| CSS class | Purpose | Used in |
|---|---|---|
| `.phase-log` | Vertical stack of phase chip rows | Evidence section |
| `.phase-chip-row` | One row — dot + label/meta stacked | Evidence section |
| `.phase-dot` | Filled green dot (complete) | Evidence section |
| `.phase-dot.pending` | Empty gray dot (pending) | Evidence section |
| `.phase-chip-label` | Phase name — 13px bold | Evidence section |
| `.phase-chip-meta` | Output filename + status — 11px slate | Evidence section |

### Owner chip

| CSS class | Purpose | Used in |
|---|---|---|
| `.owner-chip` | Inline owner name pill — 11px, slate background, rounded | Risks table, Actions table |

### Callout variants

| CSS class | Purpose | Used in |
|---|---|---|
| `.callout` | Standard informational callout (blue left border) | Multiple sections |
| `.callout-highlight` | Success callout (green left border) | Evidence section — Gate B |
| `.callout-warning` | Warning callout (amber left border) | Evidence section — GRC gates |
| `.callout-note` | Muted callout (slate left border) | Portfolio section, Roadmap section |
| `.callout-success` | Success callout — distinct from `.callout-highlight` | Use where appropriate |
| `.gap-note` | Gray italic text for data gaps and ROM notes | Problem section, Investment section |

## JS helper

The static shell includes a single smooth-scroll helper. No tab-switching logic. `showTab()` and `showTabAndScroll()` are removed.

```js
function navScrollTo(anchorId) {
  var el = document.getElementById(anchorId);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

Sticky nav usage pattern:

```html
<a href="#verdict" onclick="navScrollTo('verdict'); return false;">Verdict</a>
```

## Sticky nav HTML

The static shell includes a sticky nav immediately after `<body>`:

```html
<nav class="sticky-nav">
  <a href="#verdict" onclick="navScrollTo('verdict'); return false;">Verdict</a>
  <a href="#problem" onclick="navScrollTo('problem'); return false;">Problem</a>
  <a href="#portfolio" onclick="navScrollTo('portfolio'); return false;">Portfolio</a>
  <a href="#usecases" onclick="navScrollTo('usecases'); return false;">Use Cases</a>
  <a href="#roadmap" onclick="navScrollTo('roadmap'); return false;">Roadmap</a>
  <a href="#investment" onclick="navScrollTo('investment'); return false;">Investment</a>
  <a href="#risks" onclick="navScrollTo('risks'); return false;">Risks</a>
  <a href="#actions" onclick="navScrollTo('actions'); return false;">Actions</a>
  <a href="#evidence" onclick="navScrollTo('evidence'); return false;">Evidence</a>
</nav>
```

## Phase checklist

- [ ] Confirm `executive-summary.md` exists in the engagement folder
- [ ] Confirm all 5 source files exist: `executive-summary.md`, `baselines.md`, `scores/_index.md`, `roadmap.md`, `evidence-log.md`
- [ ] In a single tool-call batch, dispatch all 5 section-renderer agents in parallel:
  - `section-renderer-executive` ← engagement folder path, section ID: `executive`
  - `section-renderer-problem` ← engagement folder path, section ID: `problem`
  - `section-renderer-portfolio` ← engagement folder path, section ID: `portfolio`
  - `section-renderer-roadmap` ← engagement folder path, section ID: `roadmap`
  - `section-renderer-evidence` ← engagement folder path, section ID: `evidence`
  - Pass to each renderer: engagement folder path and its section ID. Each renderer reads the source files it needs for its section. Do not pass document content to renderers.
- [ ] Each renderer writes its section to `<engagement-folder>/_staging/phase11/<section-id>.html`. Returns one-line confirmation: "section <id> written." Orchestrator collects confirmations, then assembles `deliverable.html` from staging files. The orchestrator does NOT receive HTML block content from renderers.
- [ ] Verify each return: no `<html>`, no `<body>`, no `<style>`, no `<script>`. If any agent returns wrapper markup, reject and re-dispatch.
- [ ] Assemble in main context in the specified page order (see assembly pattern below)
- [ ] Write `docs/engagements/<engagement>/deliverable.html`
- [ ] Open the file and confirm: scroll works, sticky nav links target correct sections, all 9 anchors present, no missing-class artifacts

## Assembly pattern

Main context performs assembly only — it generates no content. Section-renderer agents return HTML blocks; main context interleaves them in page order.

```
Static shell:
  <head> CSS + JS </head>
  <body>
    <nav class="sticky-nav"> [9 nav links] </nav>
    [masthead block]

Page sections in this order:
    #verdict        ← section-renderer-executive block 1
    #problem        ← section-renderer-problem block 1
    #portfolio      ← section-renderer-portfolio block 1
    #usecases       ← section-renderer-roadmap block 1
    #roadmap        ← section-renderer-roadmap block 2
    #investment     ← section-renderer-roadmap block 3
    #risks          ← section-renderer-executive block 2
    #actions        ← section-renderer-executive block 3
    #evidence       ← section-renderer-evidence block 1

    .doc-footer

  </body>
→ write deliverable.html
```

Because `section-renderer-executive` returns three blocks and `section-renderer-roadmap` returns three blocks, main context extracts each block by its `id="..."` anchor and places it in the specified page order. Blocks from a single renderer are not necessarily adjacent in the page.

## Rationalization table

| Rationalization / Shortcut | Correct reframe |
|---|---|
| "Just render the full source file — synthesis is overkill." | Verbatim renders produce thousands of words per section that no executive reads in a deliverable. Synthesis renderers produce designed artifacts at specified density. |
| "Generate any missing content here — the source file has a gap." | Phase 11 generates no content. A gap in the source is a Phase 1–9 problem. Fix the source, re-run the affected renderer. |
| "Place the three executive blocks adjacent to each other." | The page order is intentional. #verdict opens the page; #risks and #actions close it after the portfolio and roadmap. Assembly interleaving is the design. |
| "Section renderers can return full HTML pages — easier to collect." | Full pages cannot be interleaved. Agents return inner `<div class="section-block">` only. Wrapper markup from agents is rejected. |
| "Invent a CSS class if you need a new visual." | The shell defines the design system. Inventing classes breaks the package. Use existing classes; if a new one is genuinely needed, that is a shell change — add it here and document it before using it. |

## Chain to next skill

Terminal — Phase 11 completes the methodology output sequence. On successful write, `deliverable.html` may be shared externally alongside `executive-summary.md`. Any subsequent change to source `.md` files requires re-running the affected section-renderer agent and reassembling the deliverable.

## Completion confirmation

**Output rule:** Do NOT reproduce or echo the HTML content of `deliverable.html` in this response. State the file path only.

After writing `deliverable.html`, present the deliverable to the user:

1. Name the file written and its path
2. Confirm all 9 sections rendered — name each section
3. Flag any visual artifacts noted during the open/confirm step
4. Invite the user to review the deliverable and provide feedback

This is the end of the methodology chain. No further phase is invoked unless the user requests a re-run or revision.

**Session boundary:** This is the end of the methodology chain. This session is complete. No further phase invocation is needed unless the user requests a re-run or revision.
