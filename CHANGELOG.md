# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
