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
