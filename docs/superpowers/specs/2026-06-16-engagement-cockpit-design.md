# Engagement Cockpit — Design

**Date:** 2026-06-16
**Status:** Approved for planning
**Author:** Dave + Claude

## Problem

The AI & Automation process-assessment methodology is a powerful, well-structured
asset, but operating an engagement means living in a terminal and hunting through
a folder of markdown files. There is no single place to see *where an engagement
stands*, *read the outputs*, *correct them*, or *kick off the next phase*. The
value is real but buried.

## Goal

A **local cockpit** — a single-page web app over one engagement folder — that lets
the operator (Dave / the team) see live engagement state, read every deliverable in
one place, drive phases without typing terminal commands, and correct outputs
safely. **Claude Code remains the reasoning engine**; the cockpit is the control
surface and dashboard over it. The methodology, subagents, gates, and deterministic
engine are reused unchanged.

## Users & Success Criteria

- **User:** Dave and the delivery team running engagements. Not clients, not a
  hosted SaaS. Runs on the operator's machine against local engagement folders.
- **Success:** A team member opens the cockpit on an engagement and can, without
  touching the terminal: (1) see exactly which of the 11 phases + 2 gates are done /
  in-progress / blocked and why; (2) read any deliverable including the final
  `deliverable.html`; (3) press "Run" on the next eligible phase and watch it
  execute live; (4) correct a score or input and have the numbers re-derive
  correctly. If the cockpit nails this, it is opened for every engagement.

## Non-Goals (YAGNI)

- No multi-tenant auth, hosting, or client self-service (that is the *future* SaaS
  horizon — see "Two Horizons").
- No reimplementation of methodology logic, gate rules, or the math engine in the
  app. The app **reads state and presses buttons**; Claude Code + the engine own
  the logic.
- No editing of derived files (`results.json`, `*.xlsx`, `deliverable.html`) by
  hand — those are regenerated.
- No cloud Managed Agents API in this phase.

## Two Horizons (context, not scope)

The bridge mechanism has two flavors that map to two product horizons:

- **Local headless Claude Code → the team cockpit (this spec).** Drives real local
  folders with the locally-installed plugin (skills + subagents).
- **Managed Agents API (cloud) → a future client-facing SaaS.** Hosted, sandboxed,
  would require re-exposing the methodology as MCP tools. Explicitly out of scope;
  noted so today's choices don't foreclose it.

## Key Insight: State Is Already Legible On Disk

The methodology already stores all the state a cockpit needs. No inference or
prose-scraping required.

- **Phase progress = file existence.** The phase map in
  `skills/using-methodology/SKILL.md` is a state machine. Each phase has a defined
  output file/folder and a gate condition ("prior file exists"):

  | Phase | Output (presence ⇒ done) |
  |---|---|
  | 1 Scope | `scope.md` |
  | 2 Context | `context.md` |
  | 3 Tech/Data | `tech-inventory.md` |
  | 4 Discovery | `processes/_index.md` (+ `PROC-NNN.md`) |
  | 5 Opportunities | `opportunities/_index.md` (+ `OPP-NNN.md`) |
  | 6 Scoring | `scores/_index.md` (+ `OPP-NNN.md`) |
  | 7 Roadmap | `roadmap.md` |
  | 8 Use-case briefs | `usecase-briefs/_index.md` (+ `UC-NNN.md`) |
  | 8.5 Cost actuals | `cost-actuals.md` |
  | 9 Business case | `business-case.md` |
  | 10 Exec summary | `executive-summary.md` (+ clearance in `evidence-log.md`) |
  | 11 Deliverable | `deliverable.html` |
  | Gate A GRC | `grc/_index.md` (triggered by non-Green flag in `opportunities/_index.md`) |
  | Gate B Deliverable | clearance recorded in `evidence-log.md` |

- **Numbers live in `model/*.json`** (single source of truth) and `model/results.json`
  (derived by the engine). The cockpit reads structured JSON for scores/value/costs.
- **The final artifact is `deliverable.html`** — self-contained; the cockpit embeds it.

The cockpit encodes this same phase table once, as data, and derives all status from
the filesystem.

## Architecture

A thin **Python backend** + a **single-page frontend**, both local.

```
┌─────────────────────────────┐        ┌──────────────────────────────┐
│  Frontend (SPA, OSL brand)  │  HTTP  │  Backend (Python, local)     │
│  - Phase-map status board   │ <────> │  - State API (folder → JSON) │
│  - Deliverable / md reader  │  SSE   │  - Folder-watch → SSE        │
│  - Run buttons (per phase)  │ <───── │  - Bridge: claude -p runner  │
│  - Editor (scores/inputs)   │ ─────> │  - Engine write-back runner  │
└─────────────────────────────┘        └──────────────┬───────────────┘
                                                       │ subprocess
                          ┌────────────────────────────┴───────────────┐
                          │  Local Claude Code (claude -p, plugin       │
                          │  loaded) + engine (python -m engine.run)    │
                          └─────────────────────────────────────────────┘
```

### Components (each a unit with one purpose)

1. **State reader** (`cockpit/state.py`)
   - *Does:* given an engagement folder path, returns a JSON snapshot: per-phase
     status (`done | in-progress | blocked | available`), gate status, the reason a
     phase is blocked, and parsed `model/*.json` + `results.json` values.
   - *Depends on:* the filesystem + the encoded phase table. No Claude, no network.
   - *Testable:* pure function of a folder; fixture folders → expected snapshots.

2. **Folder watcher** (`cockpit/watch.py`)
   - *Does:* watches the engagement folder; on change, recomputes the snapshot and
     pushes it to connected clients via SSE.
   - *Depends on:* state reader + a file-watch lib (`watchfiles`).

3. **Claude bridge** (`cockpit/bridge.py`)
   - *Does:* runs one phase by spawning local Claude Code:
     `claude -p "<phase invocation>" --output-format stream-json
      --permission-mode <bounded> --allowedTools <engine+file writes>
      --plugin-dir <this repo> --add-dir <engagement>` with `cwd` = engagement
     folder. Parses the `stream-json` event stream and relays tool-use / message
     events to the frontend over SSE.
   - *Depends on:* the installed `claude` CLI (v2.1+) and this plugin.
   - *Safety:* refuses to launch a phase whose predecessor file does not exist
     (gate-awareness reuses the state reader). Permission mode is bounded — the
     allowlist permits the engine and engagement-folder writes, not arbitrary
     destructive actions.

4. **Engine write-back** (`cockpit/edits.py`)
   - *Does:* applies an edit to a `model/*.json` input (respecting single-write
     ownership), then runs `python -m engine.run <engagement>/` to regenerate
     `results.json` + workbook. Never edits derived files directly.
   - *Depends on:* the existing engine (`engine/run.py`) as the only math I/O
     boundary — this preserves the "no arithmetic in prose / model is source of
     truth" rule.

5. **Web server** (`cockpit/server.py`)
   - *Does:* serves the SPA, the state API, the SSE stream, the run endpoint, and
     the edit endpoint. FastAPI (or stdlib if we want zero deps).

6. **Frontend** (`cockpit/web/`)
   - *Does:* phase-map board, reader (markdown render + `deliverable.html` embed),
     per-phase Run buttons with live stream view, and the edit forms. One Step Labs
     brand via the `one-step-labs-design` skill.

## Data Flow

- **Read:** browser → `GET /state` → state reader scans folder → JSON snapshot.
  Watcher pushes updated snapshots over SSE on any file change (live-fill).
- **Run:** browser → `POST /run/{phase}` → bridge validates gate → spawns
  `claude -p` in the engagement folder → streams events over SSE → files land →
  watcher pushes new snapshot → UI updates. Closes on process exit.
- **Edit:** browser → `POST /edit` with a model input change → edits writer updates
  the owning `model/*.json` → runs the engine → `results.json` changes → watcher
  pushes new snapshot.

## Delivery Slices

Sequenced so value lands early and risk stays back-loaded.

### Slice 1 — Read-only cockpit (lowest risk, ships first)
- State reader + encoded phase table.
- Server + SPA shell with the phase-map status board.
- Reader view: render each markdown deliverable + embed `deliverable.html`.
- Folder watcher + SSE so the board updates live as files change while you run
  phases the old way (in the terminal).
- **No Claude invocation yet.** Proves the state model end to end.

### Slice 2 — Drive (headline capability)
- Claude bridge: per-phase Run button → `claude -p` streamed to the UI.
- Gate-awareness: Run is disabled/blocked for phases whose predecessor is missing,
  with the reason shown (reuses state reader).
- Bounded permission mode + tool allowlist.

### Slice 3 — Edit + polish
- Edit scores/inputs in-app, routed through `python -m engine.run`.
- "Watch it assemble" animation as phases complete.
- Brand polish.

## Error Handling

- **Bridge process fails / non-zero exit:** surface the captured stream + exit code
  in the UI; leave the folder as-is (Claude's own writes are atomic per file). No
  partial cockpit state — the next snapshot reflects whatever files actually exist.
- **Edit produces a PENDING / invalid model:** the engine already renders missing
  inputs as `PENDING` rather than fabricating; the cockpit shows PENDING plainly and
  does not block.
- **Gate violation (run a phase too early):** rejected before spawning Claude, with
  the blocking reason from the state reader.
- **Stale SSE / disconnect:** client re-fetches `GET /state` on reconnect.

## Testing

- **State reader:** fixture engagement folders at various phase completions →
  asserted snapshots (pure, fast, the core of correctness).
- **Edit/engine path:** edit a fixture `model/scores.json` → run engine → assert
  `results.json` changed as expected (reuses existing engine tests' fixtures).
- **Bridge:** unit-test the command construction + stream-json parsing against
  recorded event fixtures; a single guarded integration test that actually spawns
  `claude -p` on the sample engagement behind a marker (not in default CI).
- **Server:** endpoint tests with a temp engagement folder.

## Open Questions / Risks

1. **Backend deps:** FastAPI + `watchfiles` + Anthropic Agent SDK vs. stdlib-only.
   Lean FastAPI for ergonomics; confirm in planning.
2. **Phase invocation strings:** the exact prompt the bridge sends per phase (e.g.
   "invoke `ai-process-assessment:scoring-opportunities` for this engagement").
   Derive from the routing table in `using-methodology/SKILL.md`.
3. **Long-running phases:** phases that dispatch many subagents can run for minutes;
   the UI must show sustained progress and allow cancel (kill the subprocess).
4. **Where the cockpit lives:** new `cockpit/` package in this repo vs. a separate
   tool. Default: in-repo, so the team gets it with the plugin.
5. **Auth for the bridge:** local `claude` uses the operator's existing Claude
   auth — confirm no extra API key needed for the team-local use case.
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
