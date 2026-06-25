# OSL-Branded HTML Artifacts — Design

**Date:** 2026-06-24
**Status:** Approved (design); ready for implementation plan
**Related:** #120 (future: deterministic deliverable/interim *structure*, this spec does brand/CSS only)

## Goal

Make the methodology's client-facing HTML render in the One Step Labs brand,
**deterministically**, by vendoring the OSL design system into this repo as a canonical
CSS shell that the HTML-building skills inline **verbatim** — instead of the model
free-authoring the `<style>` block on every build.

## Problem this fixes

The HTML artifacts have **no canonical CSS in the repo today**. `building-deliverable`
documents a *class contract* (class name → purpose) but the actual `<style>` block —
colors, fonts, every rule — is written fresh by the model each build. The bundled
sample's generic slate/blue palette was model-invented that run, sourced from nothing.
`building-checkpoint` reuses the same class names but likewise regenerates the CSS.

Result: branding can't be applied by editing one file, and styling is non-deterministic.

## Scope

**In — the only 4 client-facing HTML files, via 2 skills:**
- `deliverable.html` (Phase 11, `building-deliverable`)
- `checkpoint-scope.html`, `checkpoint-baseline.html`, `checkpoint-portfolio.html`
  (`building-checkpoint`; checkpoint classes are a **subset** of the deliverable's)

**Out:**
- Markdown working docs (all phase outputs, operator step-reviews, logs) — no CSS.
- `generate-artifact` — emits `.md`/`.csv` only today; no current HTML surface. (If an
  HTML artifact type is added later, it reuses the same vendored shell.)
- **Document structure/content determinism** — tracked in #120. This spec makes the
  *look* deterministic; the body is still model-assembled from sourced data.
- Font binary embedding (true-offline fidelity) — deferred; we use the Google-Fonts
  `@import` + system fallback, exactly as the OSL system itself ships fonts.
- OSL sync automation — manual re-vendor with a documented `SOURCE.md` for now.

## Global constraints

- **Self-contained output (AC-2):** all CSS is inlined into each HTML file; no external
  stylesheet links. The only network reference is the Google-Fonts `@import` for the
  webfonts, which degrades to the system-ui fallback offline.
- **No runtime dependency on the OSL plugin:** assets are vendored into this repo; a
  rendered deliverable must work on a client machine with no plugins installed.
- **Class names are preserved exactly.** Restyling maps existing classes onto OSL
  tokens; section-renderers and existing output guards are unaffected.
- **AC-3 untouched:** branding is presentation only; no number, formula, or trace
  changes. Renderers still cite `results.json`.
- **Stdlib only:** any helper/test is pure Python standard library (project convention).

## Architecture

### OSL source to vendor from

The OSL design system ships as the `one-step-labs-design` plugin. Vendor from the
installed copy at
`~/.claude/plugins/marketplaces/grandaha/plugins/one-step-labs-design/skills/one-step-labs-design/`
— specifically `tokens/{colors,typography,fonts,spacing,radius,shadow}.css`, `tokens/base.css`,
and `assets/logo-lockup.svg`. Record the exact OSL version/commit in `SOURCE.md`.

### Vendored assets — new directory `assets/osl/`

| File | Contents | Source |
|---|---|---|
| `brand.css` | Google-Fonts `@import`; the OSL `:root` token sets (colors, typography, spacing, radius, shadow); base type roles (`.osl-display/.osl-h1/...`); logo styles | Flattened from the OSL system's `tokens/*.css` + `base.css` |
| `components.css` | **Every** design-system component class (below), restyled to consume `var(--…)` OSL tokens. Shared by both surfaces. | Rewritten from the `building-deliverable` class contract |
| `logo-lockup.svg` | Brand lockup, inlined into each masthead | OSL `assets/logo-lockup.svg` |
| `SOURCE.md` | OSL repo URL + vendored version/commit + re-vendor steps | new |

Both surfaces' `<head><style>` = `brand.css` then `components.css`, inlined **verbatim**.
The checkpoint uses a subset of `components.css` — no separate checkpoint stylesheet.

`components.css` must define all classes from `building-deliverable`'s "Required CSS
components": `.sticky-nav`(+`a`), `.section-block`(+`h2`), `.doc-footer`; `.stat-row`,
`.stat-card/.stat-value/.stat-label/.stat-sub/.stat-context`; `.verdict-block/
.verdict-label/.verdict-text`; `.score-bar-wrap/.score-bar-track/.score-bar-fill/
.score-value`; `.wave-badge`+`.w1/.w2/.w3`, `.wave-timeline/.wave-band(.w1/.w2/.w3)/
.wave-band-label/.wave-band-horizon/.wave-pills/.wave-pill/.wave-band-note`; `.uc-grid/
.uc-card/.uc-card-header/.uc-card-title/.uc-card-body/.uc-card-type/.uc-problem/
.uc-outcome/.uc-meta/.uc-quickwin`; type badges `.type-rpa/.type-aug/.type-ai/.type-chain/
.type-data/.type-agentic`; `.phase-log/.phase-chip-row/.phase-dot(.pending)/
.phase-chip-label/.phase-chip-meta`; `.owner-chip`; `.callout/.callout-highlight/
.callout-warning/.callout-note/.callout-success/.gap-note`.

### Palette reconciliation (the one real design decision)

The deliverable uses a 6-color semantic palette (purple/teal/amber/green/etc.). OSL is a
deliberate **two-hue system**: *blue leads; orange is a spark used sparingly; neutrals
carry structure.* The semantic colors collapse onto OSL's available tokens by this
governing principle and table:

- **green → blue** (confidence/success), **amber/yellow → orange** (spark/attention),
  **gray → neutral**.

| Element | OSL mapping |
|---|---|
| Verdict GO | `--blue-500` label on `--blue-100` block |
| Verdict NO-GO / conditional | `--orange-700` label on `--orange-100` block |
| Wave w1 / w2 / w3 (sequential) | `--blue-500` / `--blue-300` / `--neutral-500`; bands tinted `--blue-100` / `--blue-100` (lighter) / `--neutral-100` |
| `.type-rpa` (mechanical) | bg `--neutral-200`, text `--neutral-700` |
| `.type-aug` | bg `--blue-100`, text `--blue-700` |
| `.type-ai` (Automation) | bg `--blue-300`, text `--white` |
| `.type-chain` | bg `--blue-100`, text `--blue-500`, 1px `--blue-300` border |
| `.type-data` (insight) | bg `--orange-100`, text `--orange-700` |
| `.type-agentic` (high autonomy) | bg `--orange-300`, text `--white` |
| `.uc-outcome` (was green-on-green) | text `--blue-700` on `--blue-100` |
| `.uc-quickwin` (was yellow) | bg `--orange-100`, text `--orange-700` |
| `.phase-dot` complete / pending | `--blue-500` / `--neutral-300` |
| `.callout` (info) | left border `--blue-500`, tint `--blue-100` |
| `.callout-highlight` / `.callout-success` | left border `--blue-500`, tint `--blue-100` |
| `.callout-warning` | left border `--orange-500`, tint `--orange-100` |
| `.callout-note` | left border `--neutral-300`, tint `--neutral-100` |
| `.gap-note` | `--neutral-500`, italic |

Rationale: blue family spans the deterministic→automation AI types; orange (the sparing
accent) marks the higher-spark end (data insight, agentic) and attention states; neutral
is RPA/structure. The uppercase tracked label carries final disambiguation. The
regenerated sample is the visual sanity check; fine contrast tuning happens there.

### Fonts & logo

- `brand.css` opens with the OSL Google-Fonts `@import` (DM Sans + DM Mono). Fallback
  stack `system-ui, -apple-system, 'Segoe UI', sans-serif` keeps offline output clean.
- `logo-lockup.svg` is inlined into each masthead (top of `<body>`, above the verdict /
  checkpoint header). SVG is small and self-contained.

## Skill changes

### `building-deliverable`
- Replace "Required CSS components / embed in the static shell" with: **the shell
  `<head><style>` is `assets/osl/brand.css` + `assets/osl/components.css`, inlined
  verbatim — do not author or modify CSS.** Keep the class-contract tables as
  documentation of *which classes exist* (renderers need that), annotated that the CSS
  *source* is now the vendored file.
- Add a masthead instruction: inline `assets/osl/logo-lockup.svg`.
- Rationalization table: "invent a CSS class / author the visual" → forbidden; the shell
  is vendored and authoritative.

### `building-checkpoint`
- "Checkpoint shell": replace "generate the `<style>` from the documented design system"
  with the same verbatim-inline of `brand.css` + `components.css`, plus the masthead
  logo. Keep the interim "INTERIM — for stakeholder validation" footer treatment.

## Testing (guards)

New `tests/test_branding.py` (stdlib only):
1. **Assets exist & on-brand:** `assets/osl/{brand.css,components.css,logo-lockup.svg}`
   exist; `brand.css` contains `--blue-500: #1B75BC`, `DM Sans`, and the Google-Fonts
   `@import`; `logo-lockup.svg` is non-empty SVG.
2. **Contract ↔ CSS (new invariant):** every class named in the `building-deliverable`
   contract tables is defined in `components.css` (closes the gap that let styling
   drift). Parse class names from the skill, assert each `.<class>` selector appears.
3. **Skills inline the vendored shell:** `building-deliverable` and `building-checkpoint`
   instruct inlining `brand.css` + `components.css` verbatim and forbid model-authored
   CSS (assert the new wording present, old "generate the `<style>`" wording absent).
4. **No off-brand leakage in vendored CSS:** `components.css` references colors only via
   `var(--…)` tokens (no raw hex except inside `brand.css`).

Existing output guards continue to pass (class names unchanged).

## Sample regeneration (the seed for #120)

Because class names are preserved, regenerate the bundled reference by swapping the
sample's `<style>` for the vendored shell and adding the masthead logo:
- `sample-pso-delivery/deliverable.html` — re-shelled to OSL brand.
- Any sample checkpoint HTML present — same.

This branded sample becomes the first real golden example feeding #120.

## Work units (for the plan)

1. Vendor `assets/osl/` — `brand.css`, `logo-lockup.svg`, `SOURCE.md`.
2. Author `assets/osl/components.css` (all classes, OSL tokens, palette table).
3. Rewire `building-deliverable` (inline shell, masthead logo, rationalization table).
4. Rewire `building-checkpoint` (inline shell, masthead logo).
5. `tests/test_branding.py` guards.
6. Regenerate the branded sample reference output(s).
