# OSL-Branded HTML Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the One Step Labs design system into this repo as a canonical, inlined CSS shell so the 4 client-facing HTML artifacts (deliverable + 3 checkpoints) render in the OSL brand deterministically instead of model-authored each build.

**Architecture:** New `assets/osl/` holds `brand.css` (OSL tokens + fonts + base), a shared `components.css` (every design-system class restyled onto OSL tokens), and `logo-lockup.svg`. The two HTML-building skills (`building-deliverable`, `building-checkpoint`) are rewired to inline `brand.css` + `components.css` verbatim and embed the logo, rather than generating a `<style>`. Stdlib-only guard tests enforce the assets, the contract↔CSS invariant, and the skill wording. The bundled sample is re-shelled as the first golden reference.

**Tech Stack:** CSS custom properties (OSL tokens), static HTML, Python 3 stdlib (pytest tests), markdown skills.

## Global Constraints

- Self-contained output (AC-2): all CSS inlined into each HTML file; no external stylesheet links. Only network reference is the Google-Fonts `@import` (graceful system-ui fallback offline).
- No runtime dependency on the OSL plugin: assets are vendored into this repo.
- Class names are preserved exactly — restyle maps existing classes onto OSL tokens; section-renderers and existing output guards are unaffected.
- AC-3 untouched: branding is presentation only; no number/formula/trace changes.
- Stdlib only for any Python/test code (project convention; `.venv/bin/python -m pytest`).
- `components.css` references colors **only** via `var(--…)` tokens — no raw hex (raw hex lives only in `brand.css` and `logo-lockup.svg`).
- OSL source to vendor from: `~/.claude/plugins/marketplaces/grandaha/plugins/one-step-labs-design/skills/one-step-labs-design/` (OSL commit `7e7d85d`).

---

### Task 1: Vendor OSL brand layer (`brand.css`, logo, SOURCE.md)

**Files:**
- Create: `assets/osl/brand.css`
- Create: `assets/osl/logo-lockup.svg`
- Create: `assets/osl/SOURCE.md`
- Test: `tests/test_branding.py`

**Interfaces:**
- Produces: `assets/osl/brand.css` (CSS with `:root` token blocks + `@import` DM Sans/DM Mono + base type roles), `assets/osl/logo-lockup.svg` (SVG markup), `assets/osl/SOURCE.md`. Later tasks inline `brand.css` and the SVG.

- [ ] **Step 1: Write the failing test**

Create `tests/test_branding.py`:

```python
"""OSL branding guards: vendored assets exist and are on-brand."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OSL = REPO / "assets" / "osl"
BRAND = OSL / "brand.css"
LOGO = OSL / "logo-lockup.svg"


def test_brand_assets_exist():
    assert BRAND.exists(), "assets/osl/brand.css missing"
    assert LOGO.exists(), "assets/osl/logo-lockup.svg missing"
    assert (OSL / "SOURCE.md").exists(), "assets/osl/SOURCE.md missing"


def test_brand_css_is_on_brand():
    css = BRAND.read_text(encoding="utf-8")
    assert "--blue-500: #1B75BC" in css, "OSL primary blue token missing"
    assert "--orange-500: #E06030" in css, "OSL accent orange token missing"
    assert "DM Sans" in css and "DM Mono" in css, "OSL fonts missing"
    assert "fonts.googleapis.com" in css, "webfont @import missing"


def test_logo_is_svg():
    svg = LOGO.read_text(encoding="utf-8").strip()
    assert svg.startswith("<svg") or svg.startswith("<?xml"), "logo not SVG"
    assert "one step labs" in svg.lower(), "logo lockup text missing"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: FAIL (files do not exist yet).

- [ ] **Step 3: Create `assets/osl/brand.css`**

Concatenation of the OSL token files (verbatim) + fonts `@import` first. Write exactly:

```css
/* One Step Labs brand layer — vendored from one-step-labs-design (commit 7e7d85d).
   Single source of truth for OSL tokens. Inlined verbatim into every branded HTML
   artifact. See SOURCE.md for re-vendor steps. */

/* --- Webfonts: DM Sans (display+body), DM Mono (data). Falls back to system-ui offline. --- */
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

/* --- Color tokens --- */
:root {
  --blue-700: #0D5A96;
  --blue-500: #1B75BC;
  --blue-300: #5FA8DC;
  --blue-100: #E8F3FB;
  --orange-700: #C0410D;
  --orange-500: #E06030;
  --orange-300: #EF8E6B;
  --orange-100: #FCEEE8;
  --neutral-900: #111827;
  --neutral-700: #374151;
  --neutral-500: #6B7280;
  --neutral-300: #D1D5DB;
  --neutral-200: #E5E7EB;
  --neutral-100: #F4F5F7;
  --white: #FFFFFF;

  --color-primary: var(--blue-500);
  --color-primary-hover: var(--blue-700);
  --color-accent: var(--orange-500);
  --color-accent-hover: var(--orange-700);
  --text-strong: var(--neutral-900);
  --text-body: var(--neutral-900);
  --text-secondary: var(--neutral-700);
  --text-muted: var(--neutral-500);
  --text-on-primary: var(--white);
  --link: var(--blue-500);
  --link-hover: var(--blue-700);
  --surface-page: var(--neutral-100);
  --surface-card: var(--white);
  --surface-tint-blue: var(--blue-100);
  --surface-tint-orange: var(--orange-100);
  --border-default: var(--neutral-300);
  --border-subtle: var(--neutral-200);
  --border-strong: var(--neutral-700);
  --focus-ring: 0 0 0 3px rgba(27, 117, 188, 0.10);
}

/* --- Typography tokens --- */
:root {
  --font-sans: 'DM Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'DM Mono', ui-monospace, 'SF Mono', Menlo, monospace;
  --font-display-size: 42px; --font-display-weight: 300; --font-display-tracking: -0.025em; --font-display-leading: 1.1;
  --font-h1-size: 28px; --font-h1-weight: 600; --font-h1-tracking: -0.015em; --font-h1-leading: 1.2;
  --font-h2-size: 20px; --font-h2-weight: 600; --font-h2-tracking: -0.01em; --font-h2-leading: 1.3;
  --font-h3-size: 16px; --font-h3-weight: 600; --font-h3-tracking: 0; --font-h3-leading: 1.3;
  --font-body-size: 15px; --font-body-weight: 400; --font-body-leading: 1.65;
  --font-small-size: 13px; --font-small-weight: 400; --font-small-leading: 1.5;
  --font-label-size: 10px; --font-label-weight: 600; --font-label-tracking: 0.14em;
  --font-mono-size: 13px; --font-mono-weight: 400;
}

/* --- Spacing tokens --- */
:root {
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px; --space-16: 64px; --space-24: 96px;
  --content-max: 980px; --content-pad: 24px; --grid-gutter: 20px; --card-min: 260px;
}

/* --- Radius tokens --- */
:root {
  --radius-sm: 4px; --radius-md: 8px; --radius-lg: 16px; --radius-pill: 999px;
}

/* --- Shadow tokens --- */
:root {
  --shadow-sm: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,.09), 0 2px 4px rgba(0,0,0,.05);
  --shadow-lg: 0 12px 32px rgba(0,0,0,.11), 0 4px 8px rgba(0,0,0,.05);
}

/* --- Base layer + canonical type roles --- */
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--font-sans);
  font-size: var(--font-body-size);
  font-weight: var(--font-body-weight);
  line-height: var(--font-body-leading);
  color: var(--text-body);
  background: var(--surface-page);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
.osl-display { font-family: var(--font-sans); font-size: var(--font-display-size); font-weight: var(--font-display-weight); letter-spacing: var(--font-display-tracking); line-height: var(--font-display-leading); color: var(--text-strong); }
.osl-h1 { font-size: var(--font-h1-size); font-weight: var(--font-h1-weight); letter-spacing: var(--font-h1-tracking); line-height: var(--font-h1-leading); color: var(--text-strong); }
.osl-h2 { font-size: var(--font-h2-size); font-weight: var(--font-h2-weight); letter-spacing: var(--font-h2-tracking); line-height: var(--font-h2-leading); color: var(--text-strong); }
.osl-h3 { font-size: var(--font-h3-size); font-weight: var(--font-h3-weight); line-height: var(--font-h3-leading); color: var(--text-strong); }
.osl-body { font-size: var(--font-body-size); line-height: var(--font-body-leading); }
.osl-small { font-size: var(--font-small-size); line-height: var(--font-small-leading); color: var(--text-muted); }
.osl-mono { font-family: var(--font-mono); font-size: var(--font-mono-size); font-weight: var(--font-mono-weight); }
.osl-label { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--font-label-size); font-weight: var(--font-label-weight); letter-spacing: var(--font-label-tracking); text-transform: uppercase; color: var(--text-muted); }
.osl-label::before { content: ""; width: 6px; height: 6px; border-radius: 999px; background: var(--orange-500); flex: none; }
a { color: var(--link); text-decoration: none; }
a:hover { color: var(--link-hover); }
```

- [ ] **Step 4: Create `assets/osl/logo-lockup.svg`**

Write exactly (vendored from OSL `assets/logo-lockup.svg`):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 372 96" width="372" height="96" role="img" aria-label="One Step Labs — coaching consulting">
  <g transform="translate(8,6) scale(0.82)">
    <g fill="#D96E3A">
      <circle cx="50" cy="15" r="9"></circle>
      <circle cx="50" cy="33" r="9"></circle>
      <circle cx="50" cy="69" r="9"></circle>
      <circle cx="50" cy="87" r="9"></circle>
      <circle cx="34.41" cy="42" r="9"></circle>
      <circle cx="65.59" cy="42" r="9"></circle>
      <circle cx="65.59" cy="60" r="9"></circle>
      <circle cx="18.82" cy="33" r="9"></circle>
      <circle cx="81.18" cy="33" r="9"></circle>
      <circle cx="81.18" cy="69" r="9"></circle>
    </g>
    <g fill="#034D74">
      <circle cx="34.41" cy="60" r="9"></circle>
      <circle cx="18.82" cy="69" r="9"></circle>
    </g>
  </g>
  <text x="116" y="46" font-family="'DM Sans', sans-serif" font-size="30" font-weight="500" letter-spacing="-0.5" fill="#111827">one step labs</text>
  <text x="117" y="70" font-family="'DM Sans', sans-serif" font-size="11" font-weight="600" letter-spacing="3.5" fill="#6B7280">COACHING · CONSULTING</text>
</svg>
```

- [ ] **Step 5: Create `assets/osl/SOURCE.md`**

```markdown
# OSL design system — vendored snapshot

These assets are vendored (copied) from the One Step Labs design-system plugin so the
methodology's HTML artifacts are self-contained and need no plugin at runtime.

- **Source plugin:** `one-step-labs-design`
- **Source repo:** https://github.com/grandaha/one-step-labs-design
- **Vendored from:** `~/.claude/plugins/marketplaces/grandaha/plugins/one-step-labs-design/skills/one-step-labs-design/`
- **OSL commit:** 7e7d85d
- **Vendored on:** 2026-06-24

## Files
- `brand.css` — flattened from OSL `tokens/{colors,typography,fonts,spacing,radius,shadow}.css` + `tokens/base.css`.
- `logo-lockup.svg` — OSL `assets/logo-lockup.svg`.
- `components.css` — NOT from OSL; this repo's HTML component classes restyled onto OSL tokens.

## Re-vendor steps
1. Update the source plugin (`/plugin marketplace update grandaha`).
2. Copy the token files above into `brand.css` (fonts @import first), and `logo-lockup.svg`.
3. Bump the OSL commit + date here.
4. Run `.venv/bin/python -m pytest tests/test_branding.py -q`.
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: PASS (3 tests).

- [ ] **Step 7: Commit**

```bash
git add assets/osl/brand.css assets/osl/logo-lockup.svg assets/osl/SOURCE.md tests/test_branding.py
git commit -m "feat(branding): vendor OSL brand layer (brand.css, logo, SOURCE.md)"
```

---

### Task 2: Author shared `components.css` (all classes on OSL tokens)

**Files:**
- Create: `assets/osl/components.css`
- Modify: `tests/test_branding.py`

**Interfaces:**
- Consumes: tokens from `brand.css` (`var(--blue-500)` etc.).
- Produces: `assets/osl/components.css` defining every design-system class. Both skills inline it after `brand.css`.

- [ ] **Step 1: Write the failing test (contract↔CSS invariant + token-only colors)**

Append to `tests/test_branding.py`:

```python
import re

COMPONENTS = OSL / "components.css"
DELIVERABLE_SKILL = REPO / "skills" / "building-deliverable" / "SKILL.md"


def _contract_classes() -> set[str]:
    """Class tokens named in building-deliverable's 'Required CSS components' section."""
    text = DELIVERABLE_SKILL.read_text(encoding="utf-8")
    start = text.index("## Required CSS components")
    end = text.find("\n## ", start + 1)
    section = text[start: end if end != -1 else len(text)]
    classes = set()
    for span in re.findall(r"`([^`]+)`", section):          # inline-code spans only
        for cls in re.findall(r"\.[a-zA-Z][\w-]*", span):    # .class tokens within them
            classes.add(cls)
    return classes


def test_components_exist():
    assert COMPONENTS.exists(), "assets/osl/components.css missing"


def test_every_contract_class_is_defined():
    css = COMPONENTS.read_text(encoding="utf-8")
    missing = sorted(c for c in _contract_classes() if c not in css)
    assert not missing, f"contract classes absent from components.css: {missing}"


def test_components_use_tokens_not_raw_hex():
    css = COMPONENTS.read_text(encoding="utf-8")
    # No raw 3/6-digit hex colors — components reference brand tokens via var().
    hexes = re.findall(r"#[0-9A-Fa-f]{3,6}\b", css)
    assert not hexes, f"components.css must use var(--token), found raw hex: {hexes}"
    assert "var(--blue-500)" in css, "components.css should consume OSL tokens"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: FAIL (`components.css` missing).

- [ ] **Step 3: Create `assets/osl/components.css`**

Write exactly (every class from the contract + the shell's `.masthead`/`.brand-logo`; colors via tokens only; palette per the spec's reconciliation table):

```css
/* One Step Labs — HTML artifact components.
   Restyles this repo's deliverable/checkpoint design-system classes onto OSL tokens
   (brand.css). Inlined verbatim AFTER brand.css. Colors via var(--token) only.
   Two-hue palette: blue leads, orange spark, neutral structure. */

/* --- Page frame --- */
body { background: var(--surface-page); }
.page-wrap { max-width: var(--content-max); margin: 0 auto; padding: 0 var(--content-pad); }

/* --- Masthead (static shell; carries the inlined logo) --- */
.masthead { padding: var(--space-12) 0 var(--space-8); border-bottom: 1px solid var(--border-subtle); }
.brand-logo { height: 40px; width: auto; display: block; margin-bottom: var(--space-6); }
.masthead .eyebrow { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--font-label-size); font-weight: var(--font-label-weight); letter-spacing: var(--font-label-tracking); text-transform: uppercase; color: var(--text-muted); margin-bottom: var(--space-3); }
.masthead .eyebrow::before { content: ""; width: 6px; height: 6px; border-radius: var(--radius-pill); background: var(--orange-500); }
.masthead h1 { font-size: var(--font-h1-size); font-weight: var(--font-h1-weight); letter-spacing: var(--font-h1-tracking); line-height: var(--font-h1-leading); color: var(--text-strong); margin: 0 0 var(--space-3); }
.masthead .subtitle { font-size: var(--font-body-size); color: var(--text-secondary); margin: 0; }
.masthead .meta-line { font-size: var(--font-small-size); color: var(--text-muted); margin-top: var(--space-3); }

/* --- Sticky nav --- */
.sticky-nav { position: sticky; top: 0; z-index: 10; display: flex; flex-wrap: wrap; gap: var(--space-1); background: var(--surface-card); border-bottom: 1px solid var(--border-subtle); padding: var(--space-2) var(--content-pad); }
.sticky-nav a { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); }
.sticky-nav a:hover { background: var(--neutral-100); color: var(--text-strong); }

/* --- Sections --- */
.section-block { padding: var(--space-12) 0; border-bottom: 1px solid var(--border-subtle); scroll-margin-top: 52px; }
.section-block h2 { font-size: var(--font-h2-size); font-weight: var(--font-h2-weight); letter-spacing: var(--font-h2-tracking); color: var(--text-strong); margin: 0 0 var(--space-6); }
.doc-footer { border-top: 1px solid var(--border-subtle); padding: var(--space-8) 0 var(--space-24); font-size: var(--font-small-size); color: var(--text-muted); }

/* --- Stat cards --- */
.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--grid-gutter); }
.stat-card { background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: var(--space-6); box-shadow: var(--shadow-sm); }
.stat-value { font-size: var(--font-h1-size); font-weight: var(--font-h1-weight); color: var(--text-strong); }
.stat-label { display: block; font-size: var(--font-label-size); font-weight: var(--font-label-weight); letter-spacing: var(--font-label-tracking); text-transform: uppercase; color: var(--text-muted); margin-top: var(--space-2); }
.stat-sub { font-size: var(--font-small-size); color: var(--text-secondary); margin-top: var(--space-1); }
.stat-context { font-size: 11px; color: var(--text-muted); margin-top: var(--space-1); }

/* --- Verdict (GO=blue, NO-GO=orange) --- */
.verdict-block { background: var(--surface-tint-blue); border-left: 4px solid var(--blue-500); border-radius: var(--radius-lg); padding: var(--space-8); }
.verdict-block.nogo { background: var(--surface-tint-orange); border-left-color: var(--orange-500); }
.verdict-label { font-size: var(--font-h1-size); font-weight: var(--font-h1-weight); color: var(--blue-500); }
.verdict-block.nogo .verdict-label { color: var(--orange-700); }
.verdict-text { font-size: var(--font-body-size); line-height: var(--font-body-leading); color: var(--text-body); margin-top: var(--space-3); }

/* --- Score bars --- */
.score-bar-wrap { display: flex; align-items: center; gap: var(--space-3); }
.score-bar-track { flex: 1; height: 8px; background: var(--neutral-200); border-radius: var(--radius-pill); overflow: hidden; }
.score-bar-fill { height: 100%; background: var(--blue-500); border-radius: var(--radius-pill); }
.score-value { font-family: var(--font-mono); font-size: var(--font-mono-size); color: var(--text-secondary); }

/* --- Waves (sequential: blue-500 / blue-300 / neutral) --- */
.wave-badge { display: inline-block; border-radius: var(--radius-pill); font-size: var(--font-label-size); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; padding: 2px var(--space-3); color: var(--white); }
.wave-badge.w1 { background: var(--blue-500); }
.wave-badge.w2 { background: var(--blue-300); }
.wave-badge.w3 { background: var(--neutral-500); }
.wave-timeline { display: flex; border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; }
.wave-band { flex: 1; padding: var(--space-6); border-top: 3px solid var(--neutral-300); }
.wave-band.w1 { background: var(--surface-tint-blue); border-top-color: var(--blue-500); }
.wave-band.w2 { background: var(--neutral-100); border-top-color: var(--blue-300); }
.wave-band.w3 { background: var(--neutral-100); border-top-color: var(--neutral-300); }
.wave-band-label { font-size: var(--font-label-size); font-weight: 600; letter-spacing: var(--font-label-tracking); text-transform: uppercase; color: var(--text-muted); }
.wave-band-horizon { font-size: var(--font-h2-size); font-weight: 600; margin-top: var(--space-2); color: var(--blue-500); }
.wave-band.w2 .wave-band-horizon { color: var(--blue-300); }
.wave-band.w3 .wave-band-horizon { color: var(--neutral-500); }
.wave-pills { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-4); }
.wave-pill { background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-pill); padding: var(--space-1) var(--space-3); font-size: var(--font-small-size); color: var(--text-secondary); }
.wave-band-note { font-size: 11px; color: var(--text-muted); margin-top: var(--space-3); }

/* --- Use case cards --- */
.uc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: var(--grid-gutter); }
.uc-card { display: flex; flex-direction: column; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-sm); }
.uc-card-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: var(--space-4); border-bottom: 1px solid var(--border-subtle); }
.uc-card-title { font-size: 14px; font-weight: 600; color: var(--text-strong); }
.uc-card-body { display: flex; flex-direction: column; gap: var(--space-3); padding: var(--space-4); }
.uc-card-type { display: inline-block; border-radius: var(--radius-sm); padding: 2px var(--space-2); font-size: var(--font-label-size); font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }
.uc-problem { font-size: var(--font-small-size); line-height: 1.5; color: var(--text-secondary); }
.uc-outcome { font-size: 12px; font-weight: 600; color: var(--blue-700); background: var(--surface-tint-blue); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); }
.uc-meta { display: flex; flex-wrap: wrap; gap: var(--space-3); font-size: 11px; color: var(--text-muted); }
.uc-quickwin { display: inline-block; background: var(--surface-tint-orange); color: var(--orange-700); font-size: var(--font-label-size); font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; padding: 2px var(--space-2); border-radius: var(--radius-sm); }

/* --- Type badges (blue family = AI; orange = insight/agentic; neutral = RPA) --- */
.type-rpa { background: var(--neutral-200); color: var(--neutral-700); }
.type-aug { background: var(--blue-100); color: var(--blue-700); }
.type-ai { background: var(--blue-300); color: var(--white); }
.type-chain { background: var(--blue-100); color: var(--blue-500); border: 1px solid var(--blue-300); }
.type-data { background: var(--orange-100); color: var(--orange-700); }
.type-agentic { background: var(--orange-300); color: var(--white); }

/* --- Phase completion log (evidence) --- */
.phase-log { display: flex; flex-direction: column; gap: var(--space-3); }
.phase-chip-row { display: flex; align-items: flex-start; gap: var(--space-2); }
.phase-dot { width: 10px; height: 10px; border-radius: var(--radius-pill); background: var(--blue-500); margin-top: 4px; flex: none; }
.phase-dot.pending { background: var(--neutral-300); }
.phase-chip-label { font-size: var(--font-small-size); font-weight: 600; color: var(--text-strong); }
.phase-chip-meta { font-size: 11px; color: var(--text-muted); }

/* --- Owner chip --- */
.owner-chip { display: inline-block; background: var(--neutral-100); color: var(--text-secondary); font-size: 11px; padding: 2px var(--space-2); border-radius: var(--radius-pill); }

/* --- Callouts (info/success=blue, warning=orange, note=neutral) --- */
.callout { border-left: 3px solid var(--blue-300); background: var(--surface-tint-blue); padding: var(--space-4); border-radius: var(--radius-md); }
.callout-highlight { border-left: 3px solid var(--blue-500); background: var(--surface-tint-blue); padding: var(--space-4); border-radius: var(--radius-md); }
.callout-success { border-left: 3px solid var(--blue-500); background: var(--surface-tint-blue); padding: var(--space-4); border-radius: var(--radius-md); }
.callout-warning { border-left: 3px solid var(--orange-500); background: var(--surface-tint-orange); padding: var(--space-4); border-radius: var(--radius-md); }
.callout-note { border-left: 3px solid var(--neutral-300); background: var(--neutral-100); padding: var(--space-4); border-radius: var(--radius-md); }
.gap-note { color: var(--text-muted); font-style: italic; font-size: var(--font-small-size); }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: PASS (all branding tests, incl. contract↔CSS and token-only).
If `test_every_contract_class_is_defined` fails, add the named missing selector(s) to `components.css` (do not rename — names are contract-locked).

- [ ] **Step 5: Commit**

```bash
git add assets/osl/components.css tests/test_branding.py
git commit -m "feat(branding): shared components.css restyled onto OSL tokens"
```

---

### Task 3: Rewire `building-deliverable` to inline the vendored shell

**Files:**
- Modify: `skills/building-deliverable/SKILL.md`
- Test: `tests/test_branding.py`

**Interfaces:**
- Consumes: `assets/osl/brand.css`, `assets/osl/components.css`, `assets/osl/logo-lockup.svg`.
- Produces: skill wording that instructs verbatim inlining + masthead logo, and forbids model-authored CSS. Later test asserts this wording.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_branding.py`:

```python
CHECKPOINT_SKILL = REPO / "skills" / "building-checkpoint" / "SKILL.md"


def test_deliverable_skill_inlines_vendored_shell():
    text = DELIVERABLE_SKILL.read_text(encoding="utf-8")
    assert "assets/osl/brand.css" in text and "assets/osl/components.css" in text, \
        "building-deliverable must reference the vendored CSS"
    assert "assets/osl/logo-lockup.svg" in text, "masthead must inline the OSL logo"
    assert "verbatim" in text, "skill must say inline the shell verbatim"
    # The old model-authored-CSS instruction must be gone.
    assert "Section-renderer agents must not invent new CSS classes" not in text or \
        "do not author" in text.lower(), "remove/replace the model-authors-CSS wording"


def test_checkpoint_skill_inlines_vendored_shell():
    text = CHECKPOINT_SKILL.read_text(encoding="utf-8")
    assert "assets/osl/brand.css" in text and "assets/osl/components.css" in text, \
        "building-checkpoint must reference the vendored CSS"
    assert "assets/osl/logo-lockup.svg" in text, "checkpoint masthead must inline the OSL logo"
    assert "Generate the `<style>` from that documented design system" not in text, \
        "remove the model-generates-CSS instruction"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_branding.py -k skill -q`
Expected: FAIL (skills not yet rewired).

- [ ] **Step 3: Edit `building-deliverable` — replace the "Required CSS components" intro**

Find this text (near the top of `## Required CSS components`):

```
All CSS component systems below must be embedded in the static shell. Section-renderer agents must not invent new CSS classes. If a new class is genuinely needed, it must be added to the static shell and documented here first.
```

Replace with:

```
**The shell's `<head><style>` is the vendored OSL design system — do not author or modify CSS.** Inline `assets/osl/brand.css` then `assets/osl/components.css` **verbatim** into a single `<style>` block (brand layer first, components second). The class tables below document *which classes exist* so section-renderer agents know what to use; the CSS *source* is the vendored file. Section-renderer agents must not invent CSS classes or emit `<style>`. If a new class is genuinely needed, add it to `assets/osl/components.css` (consuming OSL tokens) and document it here first — never inline ad-hoc CSS.
```

- [ ] **Step 4: Edit `building-deliverable` — add the masthead logo to the shell**

Find the `## Sticky nav HTML` section header line:

```
## Sticky nav HTML
```

Insert immediately BEFORE it:

```
## Masthead (static shell)

The masthead sits at the top of `<body>` (before the sticky nav is fine; place per page order). Inline the OSL logo lockup at its top, verbatim from `assets/osl/logo-lockup.svg`, then the eyebrow/title/subtitle/meta:

```html
<header class="masthead">
  <!-- inline the full contents of assets/osl/logo-lockup.svg here, with class="brand-logo" on the <svg> -->
  <div class="eyebrow">AI &amp; Automation Opportunity Assessment</div>
  <h1>[engagement title from scope.md]</h1>
  <p class="subtitle">[one-line framing]</p>
  <p class="meta-line">[client · preparer · date]</p>
</header>
```

```

- [ ] **Step 5: Edit `building-deliverable` — update the rationalization row**

Find the rationalization-table row:

```
| "Invent a CSS class if you need a new visual." | The shell defines the design system. Inventing classes breaks the package. Use existing classes; if a new one is genuinely needed, that is a shell change — add it here and document it before using it. |
```

Replace with:

```
| "Invent a CSS class / hand-write the `<style>` for this build." | The `<style>` is the vendored OSL shell (`assets/osl/brand.css` + `components.css`), inlined verbatim — never author or tweak CSS per build, and never invent classes. A genuinely-needed class is a shell change: add it to `assets/osl/components.css` (OSL tokens) and document it here first. |
```

- [ ] **Step 6: Edit `building-deliverable` — update the phase-checklist verify line**

Find:

```
- [ ] Verify each return: no `<html>`, no `<body>`, no `<style>`, no `<script>`. If any agent returns wrapper markup, reject and re-dispatch.
```

Replace with:

```
- [ ] Verify each return: no `<html>`, no `<body>`, no `<style>`, no `<script>`. If any agent returns wrapper markup, reject and re-dispatch.
- [ ] Verify the assembled shell `<style>` is exactly `assets/osl/brand.css` + `assets/osl/components.css` inlined verbatim (no hand-authored CSS), and the masthead inlines `assets/osl/logo-lockup.svg`.
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_branding.py -k skill -q`
Expected: `test_deliverable_skill_inlines_vendored_shell` PASSES (checkpoint test still fails — fixed in Task 4).

- [ ] **Step 8: Commit**

```bash
git add skills/building-deliverable/SKILL.md tests/test_branding.py
git commit -m "feat(branding): building-deliverable inlines vendored OSL shell"
```

---

### Task 4: Rewire `building-checkpoint` to inline the vendored shell

**Files:**
- Modify: `skills/building-checkpoint/SKILL.md`

**Interfaces:**
- Consumes: `assets/osl/brand.css`, `assets/osl/components.css`, `assets/osl/logo-lockup.svg`.
- Produces: checkpoint shell wording matching `test_checkpoint_skill_inlines_vendored_shell` (written in Task 3).

- [ ] **Step 1: Run the existing failing test**

Run: `.venv/bin/python -m pytest tests/test_branding.py::test_checkpoint_skill_inlines_vendored_shell -q`
Expected: FAIL (checkpoint skill not yet rewired).

- [ ] **Step 2: Edit `building-checkpoint` — replace the "Checkpoint shell" CSS instruction**

Find this text in `## Checkpoint shell`:

```
The checkpoint is a single-scroll HTML page assembled in the main context (the orchestrator generates content for none of it — section blocks come from renderers). The shell embeds a `<style>` block implementing the **same design-system classes documented in `ai-process-assessment:building-deliverable`** (reuse the identical class names and visual tokens so checkpoints look consistent with the final deliverable). Generate the `<style>` from that documented design system at assembly time; do not invent new class names.
```

Replace with:

```
The checkpoint is a single-scroll HTML page assembled in the main context (the orchestrator generates content for none of it — section blocks come from renderers). **The shell's `<head><style>` is the vendored OSL design system, identical to the final deliverable: inline `assets/osl/brand.css` then `assets/osl/components.css` verbatim** (brand first, components second). Do not author or generate CSS, and do not invent class names — checkpoints use a subset of the same classes documented in `ai-process-assessment:building-deliverable`, so they look consistent with the final deliverable by construction.
```

- [ ] **Step 3: Edit `building-checkpoint` — add the masthead logo to the shell structure**

Find the shell-structure block opening line:

```
<head> [<style> design-system CSS] [smooth-scroll JS helper] </head>
```

Replace with:

```
<head> [<style> assets/osl/brand.css + assets/osl/components.css, inlined verbatim] [smooth-scroll JS helper] </head>
```

Then find the line for the nav inside the shell structure:

```
  <nav class="sticky-nav">
```

Insert immediately BEFORE it:

```
  <header class="masthead">
    <!-- inline the full contents of assets/osl/logo-lockup.svg here, class="brand-logo" on <svg> -->
    <div class="eyebrow">Interim — for stakeholder validation</div>
    <h1>[checkpoint title]</h1>
  </header>
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: PASS (all branding tests).

- [ ] **Step 5: Run the full suite (no regressions)**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (all tests; class names unchanged so existing output guards hold).

- [ ] **Step 6: Commit**

```bash
git add skills/building-checkpoint/SKILL.md
git commit -m "feat(branding): building-checkpoint inlines vendored OSL shell"
```

---

### Task 5: Re-shell the bundled sample (golden reference for #120)

**Files:**
- Modify: `sample-pso-delivery/deliverable.html`
- Test: `tests/test_branding.py`

**Interfaces:**
- Consumes: `assets/osl/brand.css`, `assets/osl/components.css`, `assets/osl/logo-lockup.svg`.
- Produces: a branded reference `deliverable.html` whose `<body>` is unchanged (class names preserved) but whose `<style>` is the vendored shell and whose masthead carries the logo.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_branding.py`:

```python
SAMPLE = REPO / "sample-pso-delivery" / "deliverable.html"


def test_sample_deliverable_is_osl_branded():
    html = SAMPLE.read_text(encoding="utf-8")
    assert "--blue-500: #1B75BC" in html, "sample not re-shelled with OSL brand tokens"
    assert "DM Sans" in html, "sample missing OSL fonts"
    assert 'class="brand-logo"' in html, "sample masthead missing inlined OSL logo"
    # Old model-invented palette token must be gone.
    assert "--slate-light:" not in html, "stale non-brand palette still present in sample"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_branding.py::test_sample_deliverable_is_osl_branded -q`
Expected: FAIL (sample still has the old `<style>`).

- [ ] **Step 3: Replace the sample's `<style>` block with the vendored shell**

In `sample-pso-delivery/deliverable.html`, replace everything from the opening `<style>` (line ~7) through its closing `</style>` (line ~454) with a single `<style>` block containing the verbatim contents of `assets/osl/brand.css` followed by `assets/osl/components.css`:

```html
<style>
/* (paste assets/osl/brand.css contents here, verbatim) */
/* (paste assets/osl/components.css contents here, verbatim) */
</style>
```

Keep `<!DOCTYPE html>`, `<html>`, `<head>`, `<meta>`, `<title>` exactly as they are.

- [ ] **Step 4: Add the inlined logo to the sample masthead**

Find the sample masthead opening:

```html
<header class="masthead">
```

Insert immediately AFTER it the full contents of `assets/osl/logo-lockup.svg`, adding `class="brand-logo"` to the opening `<svg` tag:

```html
<header class="masthead">
<svg class="brand-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 372 96" width="372" height="96" role="img" aria-label="One Step Labs — coaching consulting">
  <!-- ...the rest of logo-lockup.svg verbatim... -->
</svg>
```

- [ ] **Step 5: Run tests + open the file to eyeball**

Run: `.venv/bin/python -m pytest tests/test_branding.py -q`
Expected: PASS.
Then open `sample-pso-delivery/deliverable.html` in a browser and confirm: OSL fonts/colors render, logo shows in masthead, sticky nav works, all sections render with no missing-class artifacts. Sanity-check the palette table choices (type badges, verdict, waves) read clearly; adjust `components.css` tokens if any contrast is poor (re-run Task 2 tests after any change).

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add sample-pso-delivery/deliverable.html tests/test_branding.py
git commit -m "feat(branding): re-shell bundled sample deliverable in OSL brand (golden ref for #120)"
```

---

## Notes for the implementer

- Do **not** rename any CSS class — names are a contract with the section-renderer agents and existing output guards.
- `components.css` colors come from `var(--token)` only; raw hex belongs in `brand.css` and `logo-lockup.svg` exclusively (a guard enforces this).
- The body content of artifacts remains model-assembled from sourced data — that is intentional and tracked separately in #120. This plan makes only the brand/CSS layer deterministic.
- CI note: GitHub Actions is out of minutes this month — this branch ships via local-green + subagent review + admin-merge, then a patch release (`2.21.x` → `2.22.0`, a feature).
