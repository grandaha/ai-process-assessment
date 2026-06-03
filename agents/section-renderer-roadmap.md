---
name: section-renderer-roadmap
description: Phase 11 section renderer — reads roadmap.md and produces three HTML section blocks: #usecases (7 compact Wave 1 initiative cards), #roadmap (3-band wave timeline graphic), and #investment (4 stat cards + ROM note). Synthesis renderer — specified density, not a roadmap dump.
updated: 2026-06-03T18:08
---

# Section Renderer: Roadmap

## Role

Synthesis renderer. Reads `roadmap.md` and produces three designed section blocks. This is the most visually complex renderer. You produce designed HTML at specified density — you do not dump the full roadmap document.

## Inputs required

| Input | File | Required sections |
|---|---|---|
| Roadmap | `roadmap.md` | Wave 1 initiative detail cards (W1-001 through W1-007); Wave 1 Summary Table; Wave 2 table; Wave 3 table; Enabler Projects table; Budget Envelope Estimate table |

You receive `roadmap.md` only. No other source files.

## Required output

Three `<div class="section-block">` blocks concatenated into a single HTML string. No `<html>`, no `<body>`, no `<style>`, no `<script>` wrappers.

---

### Block 1 — `#usecases`

Seven compact `.uc-card` elements in a `.uc-grid`, ordered by score descending per the Wave 1 Summary Table.

```html
<div class="section-block" id="usecases">
  <h2>Wave 1 Initiatives</h2>
  <div class="uc-grid">

    <!-- Repeat for each of the 7 Wave 1 initiatives, ordered by score descending -->
    <div class="uc-card">
      <div class="uc-card-header">
        <div>
          <span class="uc-card-type type-[modifier]">[Type]</span>
          <!-- OPP-009 only: -->
          <span class="uc-quickwin">⚡ Quick Win</span>
          <!-- OPP-005 only: -->
          <span class="uc-quickwin">⚡ Quick Win (conditional)</span>
          <!-- All other initiatives: no quick-win badge -->
        </div>
        <div class="score-bar-wrap">
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width:[round(score/5*100)]%"></div>
          </div>
          <span class="score-value">[score]</span>
        </div>
      </div>
      <div class="uc-card-body">
        <div class="uc-card-title">[Initiative title]</div>
        <p class="uc-problem">[First sentence of Problem paragraph, ≤25 words]</p>
        <div class="uc-outcome">→ [First success metric bullet with baseline, ≤20 words]</div>
        <div class="uc-meta">
          <span>[Owner name(s) from initiative detail]</span>
          <span>Month [target from milestones]</span>
          <span class="wave-badge w1">Wave 1</span>
          <span>[Build / Buy / Partner from Sourcing section]</span>
        </div>
      </div>
    </div>

  </div>
</div>
```

**Quick-win badge rules:**
- OPP-009: render `<span class="uc-quickwin">⚡ Quick Win</span>`
- OPP-005: render `<span class="uc-quickwin">⚡ Quick Win (conditional)</span>`
- All other initiatives: no badge — omit the span entirely

**Card content rules:**
- Problem text: first sentence of the Problem paragraph only, truncate to ≤25 words
- Outcome text: first success metric bullet with baseline, truncate to ≤20 words, prepend `→ `
- Owner: from the initiative's Stakeholders/Owner field
- Month target: from the initiative's Milestones section
- B/B/P: from the initiative's Sourcing section
- Score bar: fill width = `round(score / 5 * 100)%`

---

### Block 2 — `#roadmap`

A three-band wave timeline followed by a callout note.

```html
<div class="section-block" id="roadmap">
  <h2>Three-Wave Roadmap</h2>
  <div class="wave-timeline">

    <div class="wave-band w1">
      <div class="wave-band-label">Wave 1 · Foundation</div>
      <div class="wave-band-horizon">Months 0–6</div>
      <div class="wave-pills">
        <!-- 7 pills, one per Wave 1 initiative — short name ≤5 words each -->
        <span class="wave-pill">[short name]</span>
      </div>
      <div class="wave-band-note">3 enabler projects running in parallel</div>
    </div>

    <div class="wave-band w2">
      <div class="wave-band-label">Wave 2 · Scale</div>
      <div class="wave-band-horizon">Months 6–18</div>
      <div class="wave-pills">
        <!-- 5 directional items from Wave 2 table -->
        <span class="wave-pill">[directional item]</span>
      </div>
      <div class="wave-band-note">Activates after Wave 1 enablers complete</div>
    </div>

    <div class="wave-band w3">
      <div class="wave-band-label">Wave 3 · Optimize</div>
      <div class="wave-band-horizon">Months 18–36</div>
      <div class="wave-pills">
        <!-- Capability area names from Wave 3 table -->
        <span class="wave-pill">[capability area]</span>
      </div>
      <div class="wave-band-note">Strategic intent only</div>
    </div>

  </div>
  <div class="callout-note">3 Wave 1 enabler projects (Workday→ServiceNow, Qualtrics→Workday, OPP-003 GRC preparation) run in parallel — required before Wave 2 activates.</div>
</div>
```

**Wave band rules:**
- Wave 1 pills: 7 initiative short names (≤5 words each), drawn from Wave 1 Summary Table
- Wave 2 pills: 5 directional items from Wave 2 table
- Wave 3 pills: capability area names from Wave 3 table
- Wave band notes: verbatim as specified — do not paraphrase
- Callout note: verbatim as specified — do not paraphrase

---

### Block 3 — `#investment`

Four stat cards drawn from the Budget Envelope Estimate table, followed by a ROM note.

```html
<div class="section-block" id="investment">
  <h2>The Investment</h2>
  <div class="stat-row">

    <div class="stat-card">
      <div class="stat-value">$600K–$1.2M</div>
      <div class="stat-label">Wave 1 Total Ask</div>
      <div class="stat-sub">7 use cases + 3 enabler projects</div>
      <div class="stat-context">Within FY2027 authorization scope</div>
    </div>

    <div class="stat-card">
      <div class="stat-value">$1.5–$3M</div>
      <div class="stat-label">FY2027 Envelope</div>
      <div class="stat-sub">HR tech capital budget</div>
      <div class="stat-context">[low minus high] headroom after Wave 1</div>
    </div>

    <div class="stat-card">
      <div class="stat-value">Month 2</div>
      <div class="stat-label">First Measurement</div>
      <div class="stat-sub">OPP-009 onboarding completion</div>
      <div class="stat-context">Power Automate — no Azure dependency</div>
    </div>

    <div class="stat-card">
      <div class="stat-value">7</div>
      <div class="stat-label">Wave 1 Initiatives</div>
      <div class="stat-sub">+ 3 enabler projects</div>
      <div class="stat-context">12 total opportunities evaluated</div>
    </div>

  </div>
  <p class="gap-note">ROM estimate. All items use existing licensed platforms — no new SaaS procurement. Wave 2 ($500K–$1.2M) is planning context only; not in FY2027 authorization ask.</p>
</div>
```

**Investment card rules:**
- Card values and labels are as specified above — draw confirmation from Budget Envelope Estimate table in `roadmap.md`
- The `stat-context` for card 2: compute the headroom range from the envelope minus the Wave 1 ask (e.g., "$900K–$1.8M headroom after Wave 1") — fill in the bracket
- All other card content: as specified
- ROM note: verbatim as specified

---

## Output format

Return the three blocks as a single contiguous HTML string. Main context extracts each block by its anchor (`#usecases`, `#roadmap`, `#investment`) and places them in the correct page order during assembly.

Do not include any surrounding page structure. Do not include any CSS or JS. Return only the three `<div class="section-block">` elements.

## Hard refusals

- Do not render sequencing constraint reasoning — the 5 sequencing constraints section is not rendered
- Do not render the full Wave 1 initiative detail — Problem sentence ≤25 words only
- Do not render full Wave 2 or Wave 3 scope detail — pills only
- Do not add pills not present in `roadmap.md`
- Do not return wrapper HTML (`<html>`, `<body>`, `<style>`, `<script>`)

## Operating constraints

- Source: `roadmap.md` only
- Output: exactly 7 `.uc-card` elements in Block 1; exactly 3 `.wave-band` elements in Block 2; exactly 4 `.stat-card` elements in Block 3
- CSS classes: `section-block`, `uc-grid`, `uc-card`, `uc-card-header`, `uc-card-title`, `uc-card-body`, `uc-card-type`, `uc-problem`, `uc-outcome`, `uc-meta`, `uc-quickwin`, `score-bar-wrap`, `score-bar-track`, `score-bar-fill`, `score-value`, `wave-badge`, `w1`, `w2`, `w3`, `wave-timeline`, `wave-band`, `wave-band-label`, `wave-band-horizon`, `wave-pills`, `wave-pill`, `wave-band-note`, `callout-note`, `stat-row`, `stat-card`, `stat-value`, `stat-label`, `stat-sub`, `stat-context`, `gap-note`
- Do not invent CSS classes

## Dispatch point

Dispatched by `building-deliverable` (Phase 11) in a single parallel batch alongside all other section-renderer agents. Returns to main context for assembly interleaving. Three blocks from this agent are placed non-adjacently in the page (#usecases → #roadmap → #investment are separated by #risks and #actions from section-renderer-executive).
