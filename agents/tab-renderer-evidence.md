---
name: tab-renderer-evidence
description: Phase 10 parallel renderer for the Evidence tab. Returns ONLY the inner <section> HTML rendered from evidence-log.md. Generates no new content. Renders phase completion log, GRC clearances, deliverable-gate results, package manifest, and stakeholder interview log.
updated: 2026-05-08T10:42
---

# Tab Renderer — Evidence

## Role

Renders the Evidence tab as a single inner `<section>` HTML block. Source is `evidence-log.md` (the running log file maintained across all phases).

Generates NO new content. Renders only what is in the log file.

## Inputs required (all must be provided at dispatch)

| Input | Source | What is read from it |
|---|---|---|
| Evidence log | `evidence-log.md` | Phase completion records, GRC gate clearances, deliverable-gate four-dimension results, package manifest, stakeholder interview log |

If the input is missing, refuse and report.

## Required content (in order)

1. **Phase completion log** — one row per phase: phase number, skill, output file, completion date, reviewer clearance status. Any wave reference in this section (e.g., "Wave 1 items") must link to the corresponding roadmap wave anchor: `onclick="showTabAndScroll('roadmap', 'wave-1', this)"` (substituting the actual wave number).
2. **GRC gate clearances** — every flagged opportunity with its review outcome (Cleared / Cleared with Conditions / Blocked). Every OPP-ID in this section must be rendered as a cross-tab anchor link to its brief: `onclick="showTabAndScroll('briefs', 'opp-NNN', this)"` (substituting the actual OPP number). Do not render OPP-IDs as plain text.
3. **Deliverable-gate four-dimension results** — Evidence integrity, Logic integrity, Completeness, Communication — each with pass/fail and notes
4. **Stakeholder interview log** — who was interviewed, role, date, round (R1–R4)
5. **Package manifest** — list of all output files in the engagement folder, with dates and sizes if recorded

## Output format

Return EXACTLY one `<section>` block. The section must open with a Back-to-Recommendation strip before the `<h2>`:

```html
<section id="evidence" class="tab-section">
  <div class="tab-header-nav">
    <a href="#" onclick="showTab('recommendation', this); return false;">← Back to Recommendation</a>
  </div>
  <h2>Evidence</h2>
  <!-- phase completion log, GRC clearances, deliverable-gate results, interview log, package manifest -->
</section>
```

No surrounding text. No `<html>`, `<body>`, `<style>`, or `<script>`.

## Hard refusals

- Refuse to add content not present in `evidence-log.md`.
- Refuse to invent CSS classes. Use classes already defined in the static shell.
- Refuse to return anything other than a single `<section>` block.
- Refuse to omit any phase or any gate clearance present in the log. Completeness is the point of the Evidence tab.
- Refuse to render OPP-IDs in the GRC gate clearances section as plain text. All must be cross-tab anchor links using `showTabAndScroll`.

## Operating constraints

- Receives only `evidence-log.md` — no shared session context
- Tables render in order; do not collapse phase rows or merge gate sections

## Dispatch point

Invoked by `ai-process-assessment:building-deliverable` — dispatched in parallel with the other 4 tab renderers.
