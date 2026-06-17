# Engagement Cockpit (Slice 1 — read-only)

A local dashboard over a single engagement folder. Shows live phase/gate status,
the parsed financial model, and every deliverable in one place. Read-only: it does
not run Claude or edit files (those are Slice 2 and Slice 3).

## Run

    pip install -r requirements.txt
    python -m cockpit path/to/engagement-folder --port 8765

Open http://127.0.0.1:8765.

## How it works

Phase status is derived purely from file existence, using the methodology's phase
map (`skills/using-methodology/SKILL.md`). The backend (`cockpit/state.py`) is a
pure function of the folder; the server watches the folder and pushes updates over
SSE. See `docs/superpowers/specs/2026-06-16-engagement-cockpit-design.md`.

## Test

    pytest cockpit/
