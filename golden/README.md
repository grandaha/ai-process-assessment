# Golden reference outputs

Canonical, hand-reviewed reference renders of the methodology's client-facing
HTML, kept under version control so they can't be clobbered by a live engagement
run (which writes into gitignored engagement folders like `sample-pso-delivery/`).

These serve two purposes:
1. A visual reference of the One Step Labs brand applied to a real deliverable.
2. The seed examples for making deliverable/checkpoint **structure** deterministic
   (issue #120) — you need a known-good example to anchor that work.

## Contents
- `pso-delivery/deliverable.html` — the bundled PSO sample, Phase 11 deliverable,
  re-shelled in the OSL brand (`assets/osl/brand.css` + `components.css`).

## Regenerating
A golden file is updated deliberately, not by a live run: re-render the sample
deliverable, confirm it looks right, then copy it here and re-run
`.venv/bin/python -m pytest tests/test_branding.py -q`.
