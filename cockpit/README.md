# Cockpit — engagement state helpers

The state layer the `conducting-engagement` Conductor depends on. Pure, file-derived
helpers that read an engagement folder and report where the methodology stands. No
web server, no UI — the Conductor reads state and narrates it conversationally.

## Modules

- `state.py` — derives phase/gate status purely from file existence, using the
  methodology's phase map (`skills/using-methodology/SKILL.md`). A pure function of
  the folder. Run as a CLI for a one-shot JSON snapshot:

      python -m cockpit.state path/to/engagement-folder

- `phases.py` — the phase/gate map that `state.py` reads.
- `staleness.py` — content-hash (SHA-256) staleness detection over `model/*.json`
  inputs (hash, not mtime, because the repo lives in a sync-managed folder).
- `overrides.py` — reconciles a state snapshot with authorized CLAUDE.md Methodology
  Overrides; fail-closed on placeholder/incomplete rows.
- `conductor_state.py` — typed read/write of the Conductor's private `.conductor.md`
  (register, autonomy, version stamp, deferred processes, input hashes).

## Test

    pytest cockpit/
