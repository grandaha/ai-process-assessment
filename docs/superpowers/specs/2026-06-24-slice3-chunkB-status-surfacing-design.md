# Slice 3 · Chunk B — `conductor-status` surfacing

**Part of:** Epic #85 → Slice 3 (#88), spec §3.E.
**Date:** 2026-06-24. **Depends on:** Chunk A (`state/integrity.py`, merged #107).

## 1. Problem

A user mid-engagement asks "where are we?" / "what's left?" / "what needs me?" Today the
Conductor must hand-assemble an answer from several places: the raw `state.state` snapshot
(content progress), `.conductor.md` (interaction state — register, autonomy, deferred
processes, open decisions), `state.staleness` (changed inputs), and now
`state.integrity` (partial state). There is no single, tested projection that says, in one
read, *where the engagement stands and what needs attention* — so the answer is
reconstructed ad hoc each time and risks drift across surfaces.

The spec calls for "a lightweight `conductor-status` view derived from `.conductor.md` +
`state.state`" — explicitly **not** the removed SSE cockpit dashboard (only state helpers
remain).

## 2. Goal

A **pure-Python status projection** (`state/status.py`) that composes the existing readers
into one human-oriented view: progress, the current/next step, what is blocked, what needs
attention (gate due, stale inputs, partial state), and the interaction mode. A CLI prints
it as JSON (same shape as the other `state/*` tools). A Conductor section narrates it
**jargon-free** on demand. No new persisted state, no dashboard, no new dependencies.

Non-goals: no UI/server; no new file formats; no recomputation of anything the composed
functions already produce; no LLM in the projection (pure, testable).

## 3. Design

### 3.1 New unit — `state/status.py`

Pure function of the filesystem, composing the existing pure readers. No mutation, no
subprocess, no network. Stdlib + `state.*` only.

```python
def status_view(root) -> dict:
    """A presentation projection of an engagement's standing, composed from
    state.state (content), state.conductor_state (interaction), state.staleness
    (changed inputs), and state.integrity (partial state). Pure; deterministic."""
```

Composition (no re-derivation):
- `snap = state.state.read_state(root)` → `engagement`, `progress`, `phases`, `gates`,
  `model`.
- `conductor = state.conductor_state.read_conductor(root)` → `register`,
  `autonomy.should_confirm`, `deferred_processes`, `open_decisions`,
  `model_input_hashes`.
- `stale = state.staleness.changed_inputs(root, conductor.get("model_input_hashes", {}))`.
- `issues = state.integrity.check_integrity(root)`.

`read_state` internally reads `.conductor.md` once (for `engine_root`); `status_view`
reads it again for the full interaction dict. Both are pure and the file is tiny — the
second read is acceptable; a code comment will note it so a future maintainer doesn't
mistake it for an oversight.

### 3.2 Projection shape

Let `grc_status` / `deliverable_status` be the `status` of the matching entry in
`snap["gates"]` (grc ∈ {`done`,`required`,`not-required`}; deliverable ∈ {`done`,`not-run`}),
and `current_step` be the first phase whose status is `"available"` (see note below):

```python
{
  "engagement": snap["engagement"],
  "progress": {"done": d, "total": t, "percent": int(round(100*d/t))},   # t>0 always
  "current_step": {"id", "name"} of the first phase with status == "available",
                  else None (all done),
  "blocked": [ {"id", "name", "waiting_on": blocked_reason} for phases status=="blocked" ],
  "attention": {
     "gates_due": [...],                          # see below; [] if none
     "stale_inputs": stale,                       # list[str] stems, [] if none
     "partial_state": [ {"kind", "target", "repair", "detail"} for i in issues ],  # [] if clean
  },
  "interaction": {
     "register": conductor.get("register"),                 # "consultant"|"operator"|None
     "autonomy": conductor.get("autonomy", {}).get("should_confirm"),   # may be None
     "deferred_processes": conductor.get("deferred_processes", []),
     "open_decisions": conductor.get("open_decisions", []),
  },
  "complete": (current_step is None and grc_status != "required"
               and deliverable_status == "done"),
}
```

where
```python
gates_due = []
if grc_status == "required":
    gates_due.append("grc")
if current_step is None and deliverable_status != "done":
    gates_due.append("deliverable")   # all phase work done; final clearance still owed
```

Notes:
- **`current_step` uses only `"available"`.** `read_state` produces exactly `"done"` /
  `"available"` / `"blocked"` — never `"overridden"` (that value comes from
  `state.overrides.reconcile`, which needs CLAUDE.md). **Scope decision:** `status_view`
  reflects *raw* phase availability and does **not** apply CLAUDE.md overrides; the drive
  loop owns override-adjusted stepping (drive-loop step 2). Folding overrides in is a
  possible later enhancement; it is out of scope here to avoid CLAUDE.md path-resolution in
  a pure projection. Documented so the omission is a decision, not a bug.
- The status strings come from `state.state` verbatim — this projection never recomputes
  phase status or gate logic.
- `percent` is integer-rounded; `total` is the phase count (always ≥ 1), so no div-by-zero.
- **`partial_state` carries `detail`** (the integrity module's human-language hint) so the
  Conductor narrates from it directly rather than re-deriving meaning from `kind`/`repair`
  codes.
- **`gates_due`** generalizes gate attention: `grc` when the GRC gate is `required`;
  `deliverable` once all phase work is done but Gate B clearance (`evidence-log.md`) is not
  yet recorded. The deliverable gate is never `"required"` (it is `"not-run"` by default),
  so it is surfaced via the all-phases-done condition, not via a `required` status.
- **`complete`** means the engagement is genuinely finished: all phases done, GRC not
  outstanding, and Gate B clearance recorded.
- **Absent model inputs are intentionally not a separate `attention` signal:** an input not
  yet provided is conveyed by `current_step` being that input's phase (e.g. cost actuals),
  and the engine renders absent inputs as `PENDING` by design. Surfacing a separate
  "missing inputs" list would duplicate `current_step` and add phase-awareness the
  projection deliberately avoids.
- The projection tolerates a fresh/empty engagement (`read_conductor` → `{}` →
  interaction fields are `None`/`[]`; `current_step` is Phase 1).

### 3.3 CLI entry

`python3 <engine_root>/state/status.py <folder>` prints `json.dumps(status_view(...),
indent=2)`, exit `0` for a valid directory, exit `2` (stderr `not a directory: <path>`)
otherwise — identical contract to `state/state.py` and `state/integrity.py`.

### 3.4 Conductor wiring — "Status on demand"

A new `## Status on demand` section in `skills/conducting-engagement/SKILL.md`: when the
user asks where things stand ("where are we?", "what's left?", "what do you need from
me?", "status?"), read `state/status.py <folder>` and **narrate it jargon-free** — no
phase numbers, file names, skill names, or internal ids. Cover, in plain language:
- how far along (progress percent / the "done of total" as a friendly phrase),
- what's happening next (the current step, described by what it *does*, not its name),
- anything that needs them (a decision to confirm, something to redo, stale numbers being
  re-run) — drawn from `attention` and `open_decisions`,
- the working mode only if relevant (e.g. "I'm moving autonomously; say the word to slow
  down").

Narration block, fenced for the guard like the existing ones:

```
<!-- status-narration:start -->
> We're about two-thirds of the way through. Right now I'm lining up which opportunities
> to take forward; next I'll put rough numbers to them. Nothing's waiting on you at the
> moment — I'll flag it the moment something needs your call.
<!-- status-narration:end -->
```

This section is **read-only** — surfacing status never advances the drive loop or mutates
state.

## 4. Files

- **Create** `state/status.py` — `status_view(root) -> dict`, `main` (CLI).
- **Create** `state/tests/test_status.py` — unit tests for the projection (composition,
  current_step selection, attention buckets, empty/fresh engagement, complete state).
- **Create** `state/tests/test_status_cli.py` — CLI JSON + exit codes (mirrors
  `test_integrity_cli.py`).
- **Modify** `skills/conducting-engagement/SKILL.md` — add `## Status on demand` + fenced
  narration block.
- **Modify** `tests/test_conductor_skill.py` — static guards for the new section.

## 5. Testing strategy

- **`state/tests/test_status.py`**: build engagement folders in `tmp_path` and assert the
  projection fields:
  - fresh engagement (only `scope.md`) → `progress.done==1`-style counts from `read_state`,
    `current_step` is the first available phase, `interaction.register is None`,
    `attention` all-empty.
  - with `.conductor.md` stamped (via `write_conductor`) → `register`/`autonomy`/
    `deferred_processes`/`open_decisions` surfaced from it.
  - stale input (recorded hash ≠ current) → `attention.stale_inputs` non-empty; reuses the
    `staleness` boundary, not a re-implementation.
  - partial state (e.g. an empty phase output) → `attention.partial_state` carries the
    integrity issue's `kind`/`target`/`repair`/**`detail`**.
  - grc gate required (non-green flag in `opportunities/_index.md`) → `"grc" in
    attention.gates_due`.
  - all phases done but `evidence-log.md` absent → `"deliverable" in attention.gates_due`
    and `complete is False`.
  - all phases done + grc satisfied + `evidence-log.md` present → `current_step is None`,
    `gates_due == []`, `complete is True`, `progress.percent == 100`.
  - determinism: `status_view` called twice on the same folder is equal.
- **`state/tests/test_status_cli.py`**: JSON parse + exit 0 on a valid dir; exit 2 on a
  non-dir.
- **`tests/test_conductor_skill.py`**: guard the `## Status on demand` section — present,
  references `state/status.py`, read-only (does not advance), narration block fenced and
  jargon-free.
- Full suite stays green.

## 6. Reconciliation (against existing machinery)

- **Not a duplicate of `state.state`**: `read_state` is the raw content snapshot;
  `status_view` is a *presentation composition* that adds interaction state (`.conductor.md`),
  folds in staleness + integrity, and computes the human-oriented `current_step`/`attention`
  summary. It calls `read_state`, never re-derives phase status.
- **Reuses, never re-implements** `read_conductor`, `changed_inputs`, `check_integrity`.
- **Not the cockpit dashboard** (removed #73/#75): no server, no SSE, no polling — a single
  pure projection + CLI + conductor narration.
- **Matches the `state/*` CLI contract** (pure function + thin `main`, JSON out, exit 0/2,
  absolute-path invocation) established by `state.state`, `state.integrity`.
