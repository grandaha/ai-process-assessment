# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.30.0] - 2026-06-29

### Added
- **Opportunities checkpoint now carries per-opportunity detail** (#168). Previously the
  opportunities review doc rendered only the code index (OPP-ID / process / type / ratings),
  leaving a reader unable to tell what any opportunity actually was. It now keeps that table as
  an at-a-glance overview and, below it, renders each opportunity's name plus its client-facing
  fields — Type, what it is (hypothesis), expected value, governance & risk, and systems & data —
  read verbatim from `opportunities/OPP-NNN.md`. The assessor-derivation fields (Type source,
  Chain formation, Structural response) are excluded, consistent with the owner-vs-analysis split.

## [2.29.0] - 2026-06-29

### Changed
- **Step color ratings removed from the owner process-validation doc** (#165). The per-step
  Green/Yellow/Red ratings are assessor analysis (they drive the chain scan / opportunity
  identification, like Conflicts / Chain scan / Challenge hypothesis), not owner-facing
  current-state. Steps now render as clean numbered actions. The ratings remain in
  `processes/PROC-NNN.md` and surface client-facing as the opportunity landscape. This replaces
  the #162 sub-bullet treatment and reliably strips every rating variant (including compound
  ones like `Yellow/GRC-flagged` that the original #148 strip missed). Paragraph spacing and the
  footer wordmark centering from 2.28.0 are unchanged.

## [2.28.0] - 2026-06-29

### Changed
- **Process step ratings render as indented sub-bullets** (#162). Each process step now shows a
  clean numbered action with its Green/Yellow/Red rating and rationale as an indented sub-bullet
  beneath it, instead of being embedded in (or stripped from) the step text. The split anchors on
  the bolded rating, so an em-dash inside an action no longer truncates it, and compound ratings
  like `Yellow/GRC-flagged` are handled.
- **Document spacing and footer alignment** (#162). Added breathing room between paragraphs/bullets
  (default after-spacing + 1.15 line spacing, with space before headings), and vertically centered
  the `one step labs` footer wordmark against the dot-mark.

## [2.27.2] - 2026-06-29

### Changed
- **Footer logo size** (#157). Bumped the OSL dot-mark in the document footer from ~20px to ~28px
  for more presence and better balance with the wordmark.

## [2.27.1] - 2026-06-29

### Added
- **OSL dot-mark logo in document footers** (#157). The footer now shows the actual One Step Labs
  dot-mark (a vendored transparent PNG, `assets/osl/logo-mark.png`) alongside the live-text
  `one step labs` wordmark — the full lockup, on every page of every checkpoint/review `.docx`.
  If the logo asset is ever unavailable the footer degrades to the wordmark (with an orange
  signature dot) and never fails generation.

## [2.27.0] - 2026-06-29

### Added
- **OSL-branded document template** (#154). Every generated checkpoint/review `.docx` now carries
  a One Step Labs page footer on every page — the `one step labs` wordmark with the signature
  orange dot over a subtle rule, mirroring the OSL `.doc-footer` convention (DM Sans, brand
  colors). Baked into the single shared generator, so all current and future documents inherit it.

### Changed
- **Document headings match the OSL design system** (#154). Headings now render in OSL
  neutral-900 (`#111827`) on the OSL type scale, with brand blue reserved as an accent —
  previously every heading used the accent blue.

### Fixed
- **Actors readability** (#154). The per-process *Actors* field — a single semicolon-separated
  line in the source — now renders as a real bullet list (one participant per line) instead of a
  wall of text. The split is parenthesis-aware, so a semicolon inside an actor's parenthetical
  (e.g. "(execution, Step 6; checklist items, Step 3)") no longer breaks the entry.

## [2.26.1] - 2026-06-29

### Fixed
- **Baseline checkpoint crash** (#149). `python3 -m state.checkpoint_doc <engagement> baseline`
  crashed (`AttributeError: 'list' object has no attribute 'get'`) because the renderer assumed
  `model/baselines.json` was a dict keyed by process id with a `cycle_time` field. The engine
  actually reads and writes a list of per-process objects (`cycle_time_median` / `cycle_time_p90`,
  numeric `error_rate` / `fte`). The baseline document now renders correctly — cycle time as
  median / P90, error rate as a percentage — with `PENDING` for any ready process lacking a
  baseline entry.

## [2.26.0] - 2026-06-29

### Fixed
- **Process-validation document quality** (#148). The per-process validation `.docx` renderer
  now captures full multi-item fields — *Decision points* and *Exceptions* no longer drop all
  but the first item — strips leaked step ratings (`— **Green/Yellow/Red** (rationale)`), and
  renders clean step actions. This closes the parity gap with the v2.25.1 checkpoint renderer.

### Added
- **List-aware document rendering** (#148). New `docx.bullet_list` plus consecutive-list
  grouping in the shared markdown→blocks renderer: bulleted source renders as a real `•` list
  and numbered source as a numbered list across all checkpoint/review documents.

## [2.25.1] - 2026-06-28

### Fixed
- **Review-doc prose fidelity** (#144). Generated Word review docs no longer show raw markdown
  markers: `**bold**` emphasis is stripped and `###` sub-headings become real document headings.
  Adjacent tables with no blank line between them now render as separate tables instead of
  merging into one garbled table. (Single `_`/`*` are left alone so identifiers like `PROC_001`
  survive.)

## [2.25.0] - 2026-06-28

### Added
- **Per-phase review documents** (#99). The Conductor now offers an optional, client-facing
  Word review doc at four more phase boundaries — tech & data (P3, IT confirms the systems +
  data-sensitivity that drive governance), opportunity landscape (P5), use-case briefs (P8),
  and business case (P9). Each renders deterministically from the phase's source files (on the
  #131 registry) with a sign-off block; offered/opt-in, not gates. Adding a future per-phase
  artifact is now a registry entry.

## [2.24.0] - 2026-06-28

### Changed
- **Interim checkpoints are now deterministic Word (`.docx`) documents** (#131). scope,
  baseline, portfolio, and process-validation all render from one declarative registry +
  shared layer (`state/checkpoint_doc.py` on `state/docx.py`) — identical every run,
  client-commentable. Replaces the per-checkpoint LLM HTML renderers (the three
  `section-renderer-checkpoint-*` agents and deliverable-gate Checkpoint Mode are deleted).
  The Phase 11 deliverable stays HTML. The scope CP1 internal-context exclusion now lives in
  code with an integration test. Adding a future per-phase checkpoint is now a registry entry
  (foundation for #99; delivers the interim half of #120).

## [2.23.0] - 2026-06-28

### Added
- **Current-state process-validation checkpoint** (#136). A new per-process, owner-facing
  checkpoint after Phase 4 emits one editable Word (`.docx`) per in-scope process — the
  step-by-step current-state map for that owner to confirm — and **hard-gates Phase 5** until
  every process has a recorded sign-off. Includes a stdlib-only `.docx` generator
  (`state/docx.py`) reusable by #131.

## [2.22.4] - 2026-06-26

### Fixed
- **OSL logo is now the name-only lockup** (#132). The vendored logo carried an outdated
  "Coaching · Consulting" tagline. Re-vendored the corrected name-only lockup (dot-mark +
  "one step labs" wordmark, tagline removed) from `one-step-labs-design`, updated the golden
  reference and `SOURCE.md` provenance, and added a branding guard so the tagline can't
  drift back.

## [2.22.3] - 2026-06-26

### Changed
- **First-contact greeting now advertises the sample-scenario choice** (#128). The "See it
  work first" path read as one fixed sample, hiding that you choose the scenario. It now says
  you pick: a ready-made professional-services demo, or a fresh one for your world (retail,
  healthcare, finance, manufacturing, or describe your own). Wording-only; conversational
  prose, greeting stays jargon-free.

## [2.22.2] - 2026-06-25

### Fixed
- **First contact is now consistent across runs and openers** (#125). The same opener used to
  behave differently from one run to the next, because a fuzzy "clear request → skip the
  greeting and start" branch sometimes skipped the path offer entirely. First contact now
  follows the same conversational shape every time, regardless of phrasing: always reflect the
  user's intent back and confirm in one line — a named target only fills in what gets reflected
  — then offer the paths. The canonical reflect-and-confirm line lives in a jargon-free
  narration block (same convention as the greeting), with guards in `tests/test_onboarding.py`.
  Stays conversational prose only — no UI/widget mechanism — so it holds across Claude Code,
  Cowork, and Claude.ai.

## [2.22.1] - 2026-06-25

### Fixed
- **Sample run is now Conductor-driven end to end** (#122). Resolves two defects hit when
  running the sample through `conducting-engagement`:
  - **Generated sample not resumable.** The Conductor's resume resolution (first-contact
    and drive-loop step 0) keyed only on `.conductor.md`, so a freshly generated sample —
    which has only `.sample-run.md` until Phase 1 stamps `.conductor.md` — reported "No
    existing engagements to resume" despite existing on disk. Resolution now recognizes a
    `.sample-run.md`-only folder as resumable, restoring the intended sample-mode design.
  - **Legacy manual session-restart handoffs.** `running-sample-engagement`,
    `generating-sample-intake`, `building-checkpoint`, and the PSO sample README told the
    user to "start a new/fresh session and invoke a skill" between phases, contradicting
    the Conductor's autonomous-driver contract. Continuation now routes through the
    Conductor (subagent isolation, pause only at genuine touchpoints); the user is never
    asked to restart a session or name a phase skill. Sample mode drives the sample exactly
    like a real engagement.

### Added
- `generating-sample-intake` verifies every intake file exists on disk before confirming
  success (defensive assert-before-claim).
- Anti-regression guards in `tests/test_guards.py` for all three behaviors
  (no manual-restart handoffs; generator verifies on disk; Conductor resume detects
  `.sample-run.md`).

## [2.22.0] - 2026-06-24

OSL-branded HTML artifacts: the client-facing HTML (the Phase 11 deliverable and the
3 stakeholder checkpoints) now renders in the One Step Labs brand, deterministically.

### Added
- **Vendored OSL design system** under `assets/osl/`: `brand.css` (OSL color/type/
  spacing/radius/shadow tokens + DM Sans/DM Mono webfonts), a shared `components.css`
  (every deliverable/checkpoint design-system class restyled onto OSL tokens, two-hue
  palette — blue leads, orange sparingly, neutral structure), `logo-lockup.svg`, and
  `SOURCE.md` recording the vendor provenance + re-vendor steps. Self-contained (AC-2):
  the CSS is inlined; the only network reference is the webfont `@import`, with a
  system-ui fallback offline. No runtime dependency on the OSL plugin.
- **Golden reference output** under a tracked `golden/` directory
  (`golden/pso-delivery/deliverable.html`) — the bundled PSO deliverable re-shelled in
  the OSL brand, kept under version control so a live run can't clobber it. Seeds #120.
- Guard tests (`tests/test_branding.py`): vendored assets exist and are on-brand;
  every CSS class in the deliverable contract is defined in `components.css`;
  `components.css` uses color tokens only (no raw hex); the skills inline the vendored
  shell verbatim; the golden reference is OSL-branded with no dangling CSS variables.

### Changed
- `building-deliverable` and `building-checkpoint` now **inline the vendored OSL shell
  verbatim** (`brand.css` + `components.css`) and embed the logo in the masthead,
  instead of the model authoring the `<style>` block on every build. The CSS class
  contract is unchanged (section-renderers and existing output guards are unaffected);
  only the source of the styling moved from per-build authoring to the vendored file.
- Regenerated `system-prompt.md` is unaffected (branding is not in the keystone).

### Notes
- This makes the brand/CSS layer deterministic. Making the document *structure*
  deterministic (so agents stop composing the deliverable body from scratch) is
  tracked separately in #120; the new `golden/` reference is its seed example.

## [2.21.1] - 2026-06-24

Onboarding fix: the Conductor's first-contact greeting — including the **"run a
sample"** offer — now reliably fires on a fresh session.

### Fixed
- **Keystone never routed to the Conductor.** `skills/using-methodology/SKILL.md`
  (loaded at session start) had zero references to
  `ai-process-assessment:conducting-engagement`, so on a cold or vague opener the
  model had no instruction to invoke the front door. The greeting and the sample-run
  offer lived only inside the Conductor skill and never triggered. Added a **Front
  Door** section, a When-to-Invoke row, a Routing-Logic entry, and a Chain-to-next
  link that all route first contact through the Conductor before any phase skill.
- Regenerated `system-prompt.md` (the Claude.ai Projects copy-paste surface) to
  mirror the updated keystone.
- Added a regression guard (`tests/test_onboarding.py`) asserting the keystone
  routes first contact to the Conductor before Phase 1 scoping.

## [2.21.0] - 2026-06-24

Slice 4 — Step Reviews: a new operator-facing output tier. As you move through the
assessment, each step now has a readable working document you can review and revise
before the next step builds on it — distinct from the client checkpoints and the final
deliverable.

### Added
- **Step review documents (Slice 4 Chunk A).** A new pure module `state/step_review.py`
  consolidates a fragmented step (process discovery, opportunities, scoring, use-case briefs
  — otherwise split across an index + per-item files) into one readable review document, each
  item anchored by id. It parses inline `> 💬` comments, renders a **Change history** that is
  a view of the decision log scoped to the step's items (original comment → what changed →
  when), and preserves unresolved comments across regeneration (orphans surface under
  "Unanchored comments", never dropped). Steps that already have one clean document use it
  directly. The conductor surfaces the review read-only at each step boundary. No new content
  — pure consolidation; no engine/math change.
- **Inline comments + conflict pushback (Slice 4 Chunk B).** The operator marks the review up
  inline (`> 💬 @OPP-3 …`); the conductor works through the comments, routing each through the
  audited edit engine (Slice 2 edit-splicing) and re-deriving downstream via staleness — never
  losing a comment (comment-preserving regeneration; drain-before-overwrite before a staleness
  re-drive of a single-document surface). It **pushes back** rather than complying blindly when
  a comment conflicts with the evidence, the methodology, the cascade, a prior decision, or
  another comment — firm-and-teaching; the operator decides and the override is logged. A new
  `comment:` decision-log field captures the operator's verbatim words for the change history.
  Conductor behavior only — no new engine code.

## [2.20.0] - 2026-06-24

Slice 3 — Polish + Flywheel (closes #88): the conductor recovers gracefully from a
messy or half-finished engagement, can tell you where things stand in plain language,
and quietly makes the methodology sharper over time.

### Added
- **Messy/partial-state handling + resume hardening (Slice 3 Chunk A, #88).** A new
  pure-Python integrity checker (`state/integrity.py`) closes the *existence ≠ completeness*
  gap: a truncated phase output, an index that drifted from its item files, malformed
  `model/*.json`, or absent `results.json` are now detected and classified as
  auto-repairable (deterministically re-derivable — rebuild an index, re-run the engine) or
  must-surface (needs human content). On resume the conductor self-heals the derivable set
  silently and surfaces the rest as one batched must-ask. Header-based folders (Phases 5/6
  and Gate A) are rebuilt via the assembly layer; field-based `processes/` and the
  hand-assembled `usecase-briefs/` index are deferred, never destructively rebuilt.
  Reconciled with staleness and `.conductor.md` health to avoid redundant detection.
- **`conductor-status` surfacing (Slice 3 Chunk B, #88).** A pure-Python status projection
  (`state/status.py`) composes the existing readers — content state, interaction state,
  staleness, and partial state — into one human-oriented view (progress, current step,
  what's blocked, what needs attention, working mode, complete). The conductor narrates it
  jargon-free when you ask "where are we?"; it is read-only and never advances the drive
  loop. Not the removed SSE cockpit dashboard. Suppresses a false "stale" alarm when no
  hash baseline has been recorded.
- **Improvement-flywheel auto-flagging (Slice 3 Chunk C, #88).** When the conductor catches
  itself reaching for a methodology shortcut (the *holding the line* moment), it now refuses
  it and auto-writes a structured RED entry to the engagement's `improvement-log.md` via a
  pure, append-safe helper (`state/improvement_log.py`) — turning the refusal into durable
  signal. GREEN (the rationalization-table row) and REFACTOR (gate tightening) remain
  human-approved; narration is conditional on a successful write.

## [2.19.0] - 2026-06-24

Slice 2 — Adaptive + Parallel + Editable (closes #87): the conductor handles a
multi-process engagement concurrently, lets the user correct anything in plain
language, and adapts its autonomy, teaching register, and posture to the human
within an unbreakable must-ask floor.

### Added
- **Parallel per-process opportunity identification (Slice 2 Chunk A, #87).** On a
  multi-process engagement the conductor now finds opportunities across all processes
  concurrently — one per-process pass each, merged in process order into a single
  byte-identical result — including cross-process automation chains. Degrades to sequential
  where concurrent dispatch is unavailable; a single process's failure re-runs only that
  process. No engine/math change; reuses the portable assembly layer.
- **Edit & interruption splicing (Slice 2 Chunk B, #87).** The user can correct anything in plain
  language at any point — a number, a classification, or a decision. The conductor routes the
  correction to the right audited mechanism, re-runs the pipeline, and reports exactly what changed
  (backed by the new deterministic `state/results_diff.py`). Replaces the old spreadsheet "what-if",
  stricter because it re-runs the audited engine. No engine/math change.
- **Adaptive interaction (Slice 2 Chunk C, #87).** The conductor adapts to the human: pace and trust
  expressed in plain language at any point become per-class autonomy; should-confirm items batch into
  one reviewable digest when speed is wanted; the register (operator vs consultant) drives the
  teaching voice; and the must-ask floor never collapses — under pressure the conductor holds the
  line firm-and-teaching (human reason + fastest honest path), never refuse-and-quote. The engine of
  AC-1. No new code.

### Changed
- Phase 5 opportunity assembly now uses the portable stdlib `state.assembly` layer instead of inline `awk`, so it runs on Python-only surfaces and is deterministic regardless of subagent completion order (#100).
- Phase 6 score assembly now promotes and indexes scored files via the portable `state.assembly` layer; the engine composite-math step is unchanged (#100).
- Gate A (GRC) assembly now uses the portable `state.assembly` layer, removing the inline `mv`/`awk`-style shell and the zsh read-only-`status` workaround (#100).
- Phase 4 `processes/_index.md` assembly now uses the portable `state.assembly` layer instead of an inline `for`/`grep`/`sed` shell loop (#100).

## [2.18.0] - 2026-06-21

_Foundation milestone: cross-surface stdlib runtime, Excel removal, verifiable data contract + on-demand artifacts, and conversational onboarding._

### Added
- **Conversational onboarding.** On a fresh session the assistant now greets you and offers to start a new assessment, continue an existing one, or run the bundled sample — no commands or methodology vocabulary required. The session-start front door names the same three paths. (`conducting-engagement` first-contact flow.)
- **Verifiable data contract + on-demand artifacts.** The engine now emits `model/trace.json` — per-figure provenance (`inputs × formula = result` + source) for every number in `results.json`, documented as a versioned public contract (`docs/data-contract.md`, v1.0). A new `generate-artifact` skill renders any requested artifact (CFO show-your-work audit, one-pager, CSV) from that contract under a mechanical no-new-arithmetic guard; binary formats (`.xlsx`/`.pptx`/`.docx`/`.pdf`) are produced by the host surface, so the plugin stays pure-stdlib.

### Removed
- Excel/CFO workbook export (`financial-model.xlsx`) and the `openpyxl` dependency. Correctness is proven by the deterministic engine plus the audit chain; every figure lives in `model/results.json`. The `--no-workbook` flag is gone (a stray `--no-workbook` is now a silently-ignored no-op).

### Changed
- **Engine + state core is now stdlib-only.** `engine.run` (compute path) and all
  `state/` helpers run with no third-party imports: `.conductor.md` is stored as
  stdlib JSON (was pyyaml), and the unused `formulas` dependency was removed. This
  lets the auditable numbers run in any code sandbox (Claude Code, Cowork,
  Claude.ai). Guarded by `engine/tests/test_stdlib_core.py`.
- **Runs from any install path.** The engine and state CLIs (`engine/run.py`,
  `state/state.py`) now self-locate, so they run by absolute path from any working
  directory (no more `ModuleNotFoundError` outside the repo root). The session-start
  hook injects the plugin root as a front-door note (always-fire; set
  `AI_ASSESSMENT_SILENT=1` to opt out), `.conductor.md` records `engine_root`
  (surfaced in the `state.state` snapshot and reconciled via `reconcile_engine_root`
  when the install path changes), and the four standalone numeric skills resolve it
  at their own Session Start.
- **Operator prerequisite is bare `python3`.** The five operational skills now invoke
  every engine/state command by absolute path
  (`python3 <engine_root>/engine/run.py <folder>/`), and the Conductor's
  prerequisites describe pure stdlib — no venv, no `pip install` (the prior
  venv/`pyyaml` setup note from 2.17.0 is gone; `pyyaml`/`pytest` are dev/test-only
  deps). Guarded by `tests/test_portable_skill_commands.py`.

## [2.17.0] — 2026-06-19

### Added
- **Engine: `wave1_aggregate.investment_point`** (#82) — a deterministic Wave-1
  central investment estimate (sum of member initiative totals; PENDING if any
  member is PENDING), sitting at the midpoint of the ±50% ROM band. Gives the
  business case a sourced point total to cite instead of summing initiative totals
  in prose — the arithmetic-in-prose defect the deliverable-gate blocks on.
  `building-business-case` now cites it and explicitly forbids the prose sum.

### Fixed
- **GRC-gate skill index Bash used a read-only `status` variable** (#78) — `status`
  is read-only in zsh (alias of `$?`), so `grc/_index.md` generation errored on zsh
  hosts. Renamed the loop variable.

### Changed
- **`conducting-engagement`: documented the venv/deps prerequisite** (#79) — the
  state helpers import `pyyaml` and the engine imports `openpyxl`/`formulas`; a bare
  `python3` without them fails at first contact. Added a one-time setup note.
- **`conducting-engagement`: explicit pre-Phase-6 gate check** (#80) — per-phase
  status is gate-independent; the drive loop now spells out that Gate A is signalled
  in the `state.state` `gates` array (not `phases`) and must be consulted before any
  portfolio phase.
- **`identifying-opportunities`: documented the value-model unit convention** (#81)
  — the engine does not annualize; `rate` must carry the period + per-unit dollar
  basis. Added the FTE-effort and per-transaction recipes with a worked example.
- **Sample: added a PROC-07 (forecasting/EAC) operator walkthrough** (#83) to
  `interview-notes.md` — previously the only process without a dedicated Round-2
  operator section. Baseline figures unchanged.

_All six items surfaced by the #65 end-to-end Conductor validation._

## [2.16.0] — 2026-06-18

### Changed
- **Renamed the `cockpit/` package to `state/`.** With the dashboard gone (#73),
  "cockpit" was a misnomer — the package is just the methodology's deterministic
  state layer (`phases`, `state`, `staleness`, `overrides`, `conductor_state`).
  Renamed for honesty; kept as a top-level package separate from `engine/` (which
  owns the deterministic-math layer) since the two are distinct concerns. Updated
  the `conducting-engagement` skill commands (`python -m state.state`,
  `from state.conductor_state import ...`, etc.), `pytest.ini` testpaths, its
  regression guard, and all intra-package and test imports. No functional change;
  full suite green. (#74)

## [2.15.0] — 2026-06-18

### Removed
- **Cockpit dashboard layer.** Deleted the FastAPI web view over an engagement
  folder (`cockpit/server.py`, `cockpit/watch.py`, `cockpit/__main__.py`,
  `cockpit/web/`, `cockpit/tests/test_server.py`). The `conducting-engagement`
  Conductor (v2.14.0, #58) makes it redundant — the AI derives and narrates state
  conversationally, so the passive dashboard added cost without a consumer (nothing
  imported it). (#73)
- **Heaviest runtime dependencies.** Dropped `fastapi`, `uvicorn`, `watchfiles`,
  `httpx`, and `anyio` from `requirements.txt` (used only by the deleted dashboard).
  Leaves `pytest`, `pyyaml`, `openpyxl`, `formulas`. (#73)

### Changed
- **Cockpit is now the state layer, not a control surface.** The package keeps only
  the load-bearing helpers the Conductor depends on (`state.py`, `phases.py`,
  `staleness.py`, `overrides.py`, `conductor_state.py`); `README.md` and the package
  docstring rewritten accordingly. Helper test suite unchanged and green. (#73)

## [2.14.0] — 2026-06-18

### Added
- **Engagement Conductor (Slice 1 — Drive).** A new `conducting-engagement` skill turns the
  methodology into an AI-first product: a long-lived supervisor that derives state from the
  engagement folder, interviews only for gaps, dispatches phases, runs the deterministic
  engine, and stops only at genuine human touchpoints. It honors `using-methodology` as the
  rulebook — no phase-skipping, no arithmetic in prose. Serves both a consultant and an
  untrained operator from one product; the driver adapts (register + autonomy), not the user.
  (Epic #58.)
- **Cockpit helper modules backing the Conductor:**
  - `python -m cockpit.state <folder>` — one-shot JSON state snapshot CLI. (#60)
  - `cockpit/staleness.py` — content-hash (SHA-256) staleness detection over `model/*.json`
    inputs, chosen over mtime because the repo lives in a sync-managed folder. (#61)
  - `cockpit/overrides.py` — reconciles a state snapshot with authorized CLAUDE.md
    Methodology Overrides; fail-closed on placeholder/incomplete rows. (#62)
  - `cockpit/conductor_state.py` — typed read/write of the Conductor's private
    `.conductor.md` (register, autonomy, version stamp, deferred processes, input hashes). (#63)

### Fixed
- **CI gate gap:** `pytest -q` now collects `cockpit/tests` (added to `testpaths` with a
  regression guard). The 33-test cockpit suite was previously never run in CI. (#59)

### Changed
- **Conductor skill:** override rows must name a phase by its output filename or skill dir
  token to take effect; the skill now instructs the driver to surface prose-only override
  rows as a must-ask rather than silently ignoring them.

## [2.13.1] — 2026-06-17

### Fixed
- **Cockpit:** `/favicon.ico` now returns `204 No Content` instead of `404`. Browsers
  request the favicon automatically on every page load; the SPA ships no icon, so the
  404 was logged on each visit. The new route silences it. (+1 test, 33 total.)

## [2.13.0] — 2026-06-17

### Added
- **Engagement Cockpit — Slice 1 (read-only)** (`cockpit/`): a local single-page web
  dashboard over one engagement folder. The board shows live phase/gate status and
  renders every deliverable in one navigable place; the parsed financial model is exposed
  in the snapshot API (UI rendering of the model is deferred to a later slice). Claude
  Code remains the reasoning engine — this slice reads state and does not run Claude or
  edit files (driving phases and editing-through-the-engine are Slices 2 and 3). Part of #53.
  - `cockpit/phases.py` encodes the methodology's 12-phase + 2-gate map as data (single
    source of truth: `skills/using-methodology/SKILL.md`).
  - `cockpit/state.py` — pure `read_state(engagement_dir)` snapshot builder: per-phase
    status (done/available/blocked) derived purely from file existence, GRC/deliverable
    gate detection (GRC triggered by non-Green flags in `opportunities/_index.md`), and
    parsed `model/results.json` + input presence.
  - `cockpit/server.py` (FastAPI) — `/api/state`, `/api/file` + `/api/file-raw` (shared
    traversal guard), `/api/events` (SSE), and the static SPA shell.
  - `cockpit/watch.py` — `watchfiles`-backed async snapshot stream so the board updates
    live as files land while phases run in the terminal.
  - `cockpit/web/` — dependency-free vanilla-JS phase-map board + deliverable reader.
  - `cockpit/__main__.py` — `python -m cockpit <engagement-folder> [--port 8765]`.
  - 32 tests; new web deps (fastapi, uvicorn, watchfiles, httpx).

## [2.12.0] — 2026-06-16

### Added
- **Checkpoint 3 — Portfolio & Roadmap Review** (`portfolio`): the third and final
  stakeholder-validation checkpoint on the v2.10.0 pattern, rendered after Phase 7 so the
  decision-maker, sponsor, and IT lead validate the prioritized portfolio, wave sequencing,
  quick wins, dependencies, and investment envelope before Phase 8. Completes the
  three-checkpoint pattern and closes #49.
  - New bespoke data-driven renderer `section-renderer-checkpoint-portfolio` (emits
    `#portfolio`, `#scoring`, `#roadmap`, `#validate`). Renders the full analytical work
    product including per-OPP six-dimension scoring detail; renders only the
    OPPs/initiatives/waves that exist (no hardcoded counts or sample values).
  - `building-checkpoint` registry row, Session Start predecessor check
    (`roadmap.md` + `scores/_index.md`), shell sticky-nav, per-field route-back
    (score → Phase 6, sequencing → Phase 7; re-stamp via the owning phase, not the engine —
    `engine.run` is a Phase 9 step), and chain-to-next-skill.
  - `deliverable-gate` Checkpoint Mode `portfolio` case (Completeness, Evidence,
    Determinism — composites trace to `model/scores.json`; `opportunity-reviewer` not
    dispatched).
  - Keystone Routing Logic + When-to-Invoke wiring, mirrored to `system-prompt.md`.

## [2.11.0] — 2026-06-16

### Added
- **Checkpoint 1 — Scope & Context Alignment** (second checkpoint on the v2.10.0 pattern).
  After Phase 2, the `building-checkpoint` skill (new `scope` registry row) renders
  `checkpoints/checkpoint-scope.html` from `scope.md` + `context.md` so the sponsor and
  decision-maker confirm the engagement framing — sponsoring question, decision-maker,
  scope, success criteria, and the shareable strategic context — before tech inventory
  (Phase 3) and discovery (Phase 4). Synthesis-only; PENDING for absent fields.
- **`section-renderer-checkpoint-scope`** — data-driven renderer emitting `#scope`,
  `#context`, `#validate`. **Renders only the shareable framing context** (business model,
  strategic priorities, funding model) and **never exposes internal consultant assessments**
  — the political landscape, the `Risk posture` cultural read, the AI-maturity self-assessment,
  or org structure. A new guard (`test_scope_renderer_excludes_internal_context`) locks this in.

### Changed
- **`deliverable-gate` Checkpoint Mode** gains a `scope` case (Completeness + Evidence;
  Determinism N/A — no figures yet). Terminal path unchanged.
- **Per-field route-back:** a scope-field correction routes to Phase 1, a context-field
  correction to Phase 2. Keystone + `system-prompt.md` recommend the scope checkpoint after
  Phase 2 / before Phase 3 (recommended-and-recorded). Registered via the test allow-list
  (no new skill; agent count 15 → 16).

## [2.10.0] — 2026-06-16

### Added
- **Stakeholder validation checkpoints** — the methodology's first interim, client-facing
  artifact. New `building-checkpoint` skill (registry-driven; Checkpoint 2 "baseline" wired)
  renders `checkpoints/checkpoint-baseline.html` after Phase 4 so process owners and the
  sponsor can confirm the process maps and baseline metrics — and decide the challenge
  hypotheses — before opportunities, scores, roadmap, and the business case are built on
  them. Synthesis-only: every figure traces to `processes/PROC-NNN.md` / `model/baselines.json`;
  absent metrics render as PENDING.
- **`section-renderer-checkpoint-baseline`** — data-driven renderer (renders whatever metrics
  each process actually has, unlike the sample-specific Phase 11 renderers); emits `#baselines`
  and `#validate` blocks.
- **Checkpoint feedback loop** — `templates/checkpoint-outcome-template.md`; a "Changes
  Requested" outcome routes back to Phase 4 (correct source → regenerate → re-run engine).
  Recommended-and-recorded, not a hard gate (CLAUDE.md can make it mandatory).

### Changed
- **`deliverable-gate` gains a backward-compatible Checkpoint Mode** — runs the integrity
  dimensions (Evidence, Determinism, Completeness) over only the files that exist at a
  checkpoint, treating later-phase files as legitimately absent. The terminal gate path is
  unchanged. A missing `model/baselines.json` does not clear the baseline checkpoint.
- Keystone + `system-prompt.md` wire the checkpoint (engagement-folder `checkpoints/` convention,
  routing recommendation after Phase 4, when-to-invoke trigger). Registered via the test
  allow-list, not the Phase Map (it is cross-cutting, not a linear phase).

### Tests
- Allow-list + count updates for the new skill/agent; new `test_system_prompt_envelope_balanced`
  guard so a dropped mirror wrapper tag can no longer pass silently.

## [2.9.0] — 2026-06-14

### Added
- **Autonomous PR auto-review/fix/merge loop** — new `auto-review.yml` workflow runs on every
  PR to `main`: `claude-code-action` reviews the PR and returns a structured verdict, a
  deterministic gate (`scripts/auto_merge_gate.py`) decides, and test-covered Python that
  passes review auto-merges once CI is green. Rejected Python is auto-fixed and re-reviewed
  (bounded to 3 rounds); anything touching markdown gets review/fix-for-Python but always
  waits for a human to merge.
- **`scripts/auto_merge_gate.py`** — pure, fully-tested decision module (verdict parsing that
  fails closed, path classification, merge-eligibility predicate, fixer-dispatch logic) with
  43 unit tests.

### Security
- The fixer agent has **no push or merge authority** (the workflow owns both); the merge is
  double-gated behind a `security`-label block and the `AUTO_MERGE_ENABLED` repo variable
  (report-only by default). Workflow inputs are passed via `env:` (no `${{ }}` in shell
  bodies) to prevent command injection, and the job is guarded to this repo (no fork PRs).

## [2.8.3] — 2026-06-10

### Added
- **Auto-tag on merge** — new `auto-tag.yml` workflow reads `plugin.json` version on every
  push to main and creates the matching `vX.Y.Z` tag if it doesn't exist. This triggers
  `release.yml` automatically, removing the manual tag-push step.
- **`make bump VERSION=x.y.z`** — Makefile target that updates the version in all three
  manifest files (`plugin.json`, `marketplace.json`, `INSTALL.md`) in one command.

## [2.8.2] — 2026-06-10

### Changed
- **Engagement folders moved to project root** — removed the `docs/engagements/` prefix
  everywhere. Engagements now live at `<name>/` directly in the project root. Phase 1
  (`scoping-engagement`) already prompts for the name; it now uses that name as the full
  folder path.
- **Auto-gitignore on engagement creation** — `scoping-engagement` now appends `<name>/`
  to `.gitignore` immediately after `mkdir`, so client data is protected without any manual
  step.
- **Reserved-name guard** — Phase 1 now rejects engagement names that collide with existing
  repo structure (`docs`, `skills`, `templates`, `samples`, `tests`, `agents`, `engine`,
  `hooks`, `.claude`).

## [2.8.1] — 2026-06-10

### Fixed
- **Phase 9 gate now checks `model/scores.json`** — the engine input file written by Phase 6
  was missing from the "Verify the inputs exist" step in `building-business-case/SKILL.md`.
  A missing `scores.json` would cause the engine to fail silently rather than halting with a
  clear gate error pointing back to Phase 6. Closes #32.

## [2.8.0] — 2026-06-09

### Changed
- **Phase 4 `processes/` folder model** — replaces the two monolithic `process-map.md` and
  `baselines.md` outputs with a per-process folder structure, matching the pattern already
  used by `opportunities/`, `scores/`, and `grc/`.
  - Each process is now a single `processes/PROC-NNN.md` file containing the process map
    (steps, actors, decision points, chain scan, challenge hypothesis) AND baseline metrics
    (volume, cycle time, FTE effort, error rate) in one place.
  - `processes/_index.md` is machine-generated via Bash from extraction headers
    (`<!-- index: baseline=Ready -->`), providing a gate-checkable summary of all processes.
  - Phase 5 gate now checks `processes/_index.md` instead of `process-map.md` + `baselines.md`.
  - Phase 5 typer and Phase 6 scorer subagents each receive one `processes/PROC-NNN.md` file
    instead of sections from two separate files, eliminating context bloat that scaled linearly
    with engagement size.
  - All downstream phases (7–11) updated to read from `processes/PROC-NNN.md`.
  - Retirement guard added to `test_guards.py` — any re-introduction of `process-map.md` or
    `baselines.md` in skills/ or agents/ fails immediately.

## [2.7.0] — 2026-06-09

### Changed
- **Data architecture convergence** — the deterministic engine is now the single
  arithmetic executor across every phase, with one structured owning phase, one
  write site, and a real engine consumer for every numeric input.
  - **Engine reads `baselines.json` (F1, F5).** Phase 4 baselines are now a live
    engine input keyed by `process_id`. `value.json` no longer carries a literal
    `volume`; each entry references a baseline via `process_id` + optional
    `volume_fraction`, and the engine resolves `volume = baseline.volume ×
    volume_fraction`. Raw baselines are echoed into `results.json`, making the
    determinism claim true. Eliminates duplicated, drift-prone volume figures.
  - **Phase 7 writes `initiatives.json` (F2).** Wave assignment is structured by
    the phase that decides it, not re-transcribed downstream.
  - **Phase 9 is read-only (F4).** The business-case phase verifies the four
    input files exist, runs the engine, and cites results — it never re-writes an
    input. Single-write ownership of every `model/*.json` is codified in the
    methodology keystone.
  - **`--no-workbook` flag (F3).** Phase 5 computes value ranges into
    `results.json` without emitting a premature CFO workbook.
  - **Cost percentages are per-initiative inputs (F6).** `change_mgmt_pct` and
    `contingency_pct` are recorded in `costs.json` by Phase 8.5, not treated as
    engine constants.
- Fixed a stale `marketplace.json` (version `2.5.1` → `2.7.0`; license
  `MIT` → `Apache-2.0`) and a duplicate workflow step number in Phase 7.

### Tests
- Engine suite 37 → 47 (new baseline-resolution, volume-fraction, baseline-echo,
  PENDING-on-missing-baseline, and `--no-workbook` coverage).

## [2.6.0] — 2026-06-09

### Added
- Plugin marketplace manifest (`.claude-plugin/marketplace.json`) — the repo is
  now one-add installable in Claude Code (`/plugin marketplace add ...`) and
  Claude Cowork (Add marketplace from GitHub repo).
- CI: `@claude` PR-review workflow (`.github/workflows/claude.yml`), authenticated
  via a Claude subscription OAuth token and pinned to a `claude-code-action`
  release.
- CI: Dependabot config (`.github/dependabot.yml`) — grouped weekly updates for
  GitHub Actions and pip dependencies.
- A tracked pre-push test gate (`.githooks/pre-push`) that runs the suite before
  every push; enable with `git config core.hooksPath .githooks`.
- Improvement Log (`improvement-log.md`) — structured schema for recording
  methodology regressions, their causes, and resolutions; documented in keystone
  and README.
- `running-sample-engagement` writes a `.sample-run.md` marker file at setup;
  Phases 1–4 check for this marker and skip live elicitation automatically.
- This `CHANGELOG.md`.

### Changed
- Docs: refreshed `README.md` and `INSTALL.md` with install instructions for
  Claude Code, Claude Cowork, and Claude.ai Projects; corrected the phase map
  (11 phases + 8.5 + two gates), agent list, and repository layout.
- Regenerated `system-prompt.md` to mirror the current keystone verbatim (a guard
  test now enforces the sync); fixed the keystone intro phase count.
- CI: `actions/checkout` bumped to v6 and `actions/setup-python` to v6.
- Raised `requirements.txt` floors to current releases (`pytest>=9.0.3`,
  `pyyaml>=6.0.3`, `openpyxl>=3.1.5`, `formulas>=1.3.4`).

### Fixed
- Explicit `intake_root` extraction instruction in all four eliciting phase skills.
- Step 4 tool instruction clarified; removed bash block inconsistency in
  `running-sample-engagement`.

## [2.5.1] — 2026-06-07

### Fixed
- Exact workbook ↔ `results.json` rounding parity: every downstream workbook
  formula is now `ROUND(...,2)` (value, cost roll-up, ROM, Wave-1 aggregate,
  payback), and `compute.cost_structure` rounds at each step from rounded
  predecessors, so the auditable `.xlsx` reproduces `results.json` cell-for-cell
  even on fractional inputs (#9 follow-up).

## [2.5.0] — 2026-06-07

### Added
- Deterministic math engine (`engine/`): a pure-Python, unit-tested module that
  computes every methodology number (value ranges, score composites, cost
  structures, AACE Class 5 ROM ranges, Wave-1 aggregate, payback). Emits a
  canonical `model/results.json` and an auditable `financial-model.xlsx` with
  live, cross-app (Excel / Google Sheets / Apple Numbers) cell formulas (#9).
- Determinism integrity dimension in the deliverable-gate: every markdown figure
  must equal its `results.json` source; PENDING renders as PENDING, never a
  fabricated number.

### Changed
- Phases 4, 5, 6, 8.5, and 9 now write `model/*.json`, run the engine, and cite
  `results.json` — no arithmetic is performed in prose. The keystone documents
  the no-prose-arithmetic rule and the `model/` engagement-folder convention.
- `INSTALL.md` gains a Python engine setup step; pytest `testpaths` now covers
  `engine/tests`.

## [2.4.0] — 2026-06-07

### Added
- Structural-challenge gate in Phase 4 (addressing-root vs optimizing-around
  signal), threaded through scoring, portfolio, and roadmap views (#10).

## [2.3.0] — 2026-06-06

### Added
- "Running the tests" documentation for the static test suite.

## [2.2.0] — 2026-06-05

### Added
- Bundled sample engagement (fictional Lattice Consulting PSO) and the
  `running-sample-engagement` skill — a full end-to-end demo over all phases and
  both gates (#7).

## [2.1.0] — 2026-06-05

### Changed
- Normalized the data architecture into per-OPP files
  (`opportunities/OPP-NNN.md`, `scores/OPP-NNN.md`, `grc/OPP-NNN.md`), retiring
  the monolithic `opportunities.md` / `scored-opportunities.md`.

### Fixed
- Engagement-folder isolation, extraction-header handling, OPP-ID renumbering,
  and the Phase 10 gate (closes #1–#5).

## [2.0.0] — 2026-06-05

### Changed
- Context-bloat fixes: explicit session boundaries, self-read of prior outputs,
  no-echo handoffs, and summarize-on-return between phases.

[Unreleased]: https://github.com/grandaha/ai-process-assessment/compare/v2.6.0...HEAD
[2.6.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.5.1...v2.6.0
[2.5.1]: https://github.com/grandaha/ai-process-assessment/compare/v2.5.0...v2.5.1
[2.5.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/grandaha/ai-process-assessment/releases/tag/v2.0.0
