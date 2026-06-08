# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/grandaha/ai-process-assessment/compare/v2.5.1...HEAD
[2.5.1]: https://github.com/grandaha/ai-process-assessment/compare/v2.5.0...v2.5.1
[2.5.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/grandaha/ai-process-assessment/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/grandaha/ai-process-assessment/releases/tag/v2.0.0
