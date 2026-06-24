# Design — Static Test Stack (Layer 1)

**Date:** 2026-06-06
**Status:** Approved design (pre-implementation)
**Author:** Dave Raffaele (with Claude)

---

## 1. Problem

The plugin is a methodology made of prose. Sixteen `skills/*/SKILL.md` files and thirteen `agents/*.md` definitions encode the entire engagement flow as gate instructions the model is *asked* to honor. Its correctness invariants — phase order, gate sequencing, output-file conventions, the engagement-folder isolation rule, the per-OPP data-architecture normalization — live in that prose and are verified only by hand: reading skills, running ad hoc greps, eyeballing the sample.

Every recent defect was caught and fixed manually, with no regression net behind it:

- **#5** — engagement-folder isolation: files landed in the project root when the path was unset.
- **#8** — Gate B ordering: the sample skill sequenced the deliverable gate *after* Phase 10.
- **Data-architecture normalization** — skills referenced the retired monolithic files (`opportunities.md`, `scored-opportunities.md`) after the move to per-OPP folders.
- **Version drift** — `plugin.json` lagged at v1.9.0 while `INSTALL.md` and the git tag had moved on.

There is no test infrastructure at all: no runner, no CI, no `requirements.txt`. Nothing stops any of these from silently returning.

## 2. Goal

Stand up the first layer of a test stack: **deterministic, LLM-free, CI-runnable static checks** over the repository's markdown + JSON artifacts. The suite must

1. verify the methodology graph is internally consistent (phases, skills, agents, chains, outputs), and
2. encode **anti-regression guards** for the specific defect classes already fixed by hand, so they cannot silently come back.

This is **Layer 1** of a three-layer vision. The full picture:

| Layer | What it proves | Nature | Status |
|---|---|---|---|
| **1 — Static / structural** | The artifacts are internally consistent; fixed bugs stay fixed | Deterministic, no LLM, seconds in CI | **This spec** |
| 2 — Math-engine unit tests | The numbers are computed correctly | Deterministic Python, golden numbers | Issue #9 (separate) |
| 3 — Behavioral evals | The prose-gates actually govern an LLM run | LLM-in-the-loop, slow, flaky | Future, separate |

Only Layer 1 is in scope here. The design leaves clean slots for 2 and 3.

## 3. Settled decisions

| Decision | Choice | Rationale |
|---|---|---|
| Layer | **Static / structural only** | Cheapest, deterministic, and the layer that would have caught every hand-fixed defect. Independent of #9. |
| Runner | **Python + `pytest`** | Issue #9's math engine is already specced as `pytest`. One runner, one CI job, one `requirements.txt` for both layers. Trivial markdown/JSON parsing via `pyyaml` + stdlib. |
| Source of truth | **Parse the keystone Phase Map** | The table in `using-methodology/SKILL.md` already declares every phase's Skill ID, gate condition, and output file. It *is* the manifest; the other 15 skills are supposed to conform. No new artifact — the canonical doc gets enforced rather than duplicated. |
| v1 coverage | **Graph integrity + anti-regression guards** | The structural skeleton plus guards encoding #5, #8, data-arch, and version drift. |
| Version invariant | **Internal consistency, not tag-equality** | `version == latest git tag` would flake red on every release-prep commit (bump precedes tag). Internal consistency (`plugin.json` ↔ `INSTALL.md`) is the drift that actually bit us and never flakes. |
| Sample/hook checks | **Deferred to a named fast-follow** | Keeps v1 focused; both are listed in §9. |

## 4. Core principle

> **The keystone Phase Map is the single source of truth for the methodology's shape. Every other artifact is tested for conformance to it.** A skill, agent, chain link, or output file that disagrees with the keystone is a defect the suite must catch.

The suite reads the methodology into one structured model, then asserts every file in the repo agrees with that model. The "expected" structure is never hand-copied into test code — it is parsed from the doc that already governs it, so the tests cannot drift from the methodology.

## 5. Architecture

### 5.1 Layout

```
tests/
  conftest.py              # session-scoped fixtures exposing the parsed model
  methodology_model.py     # THE parser — keystone table + skill/agent frontmatter → dataclasses
  test_manifest.py         # keystone Phase Map well-formed; phase order; gate ordering
  test_skills.py           # all skills exist; frontmatter valid; name == Skill ID; no orphans
  test_agents.py           # referenced agents exist; frontmatter valid
  test_chain.py            # every "Chain to next skill" resolves and matches the phase sequence
  test_outputs.py          # declared output files match the Engagement Folder Convention list
  test_guards.py           # anti-regression guards (#5, #8, data-arch)
  test_plugin_manifest.py  # plugin.json valid + version internal consistency
requirements.txt           # pytest, pyyaml
pytest.ini                 # testpaths, rootdir config
Makefile                   # make install / make test
.github/workflows/test.yml # pytest on push + PR
```

### 5.2 #9 forward-compatibility

The math engine keeps its own `engine/tests/` per its spec. A single `pytest` invocation from the repo root discovers both `tests/` and `engine/tests/`. One runner, one `requirements.txt` (Layer 2 appends `openpyxl` and a formula evaluator when #9 lands), one CI job. Nothing here forces #9 to move or restructure.

### 5.3 The parser (`methodology_model.py`)

The heart of the stack. Three loaders compose into one frozen model, built once per session and shared via fixtures.

| Function | Reads | Produces |
|---|---|---|
| `parse_phase_map()` | the markdown table in `skills/using-methodology/SKILL.md` | `list[PhaseRow]` — `phase`, `skill_id`, `gate_condition`, `output_file`. Strips backticks; extracts the leading file/folder token from the output column. |
| `load_skills()` | glob `skills/*/SKILL.md` | `dict[skill_id, SkillDoc]` — frontmatter (`name`, `description`), full body, the "Chain to next skill" target, and presence-markers (e.g. the scope.md self-read). |
| `load_agents()` | glob `agents/*.md` | `dict[name, AgentDoc]` — frontmatter (`name`, `description`). |

Dataclasses (`PhaseRow`, `SkillDoc`, `AgentDoc`, and an aggregate `Methodology`) keep each test reading as an assertion about structure rather than a string-grep. `conftest.py` exposes a session-scoped `methodology` fixture so parsing happens once.

**Parsing notes.** The Phase Map is a GitHub-flavored markdown table: rows start with `|`, row two is the `---` separator, Skill IDs are backtick-wrapped (`` `ai-process-assessment:scoping-engagement` ``). The output column carries trailing prose (`scores/ (folder: _index.md + ...)`); the parser keeps only the leading token. Frontmatter is the `---`-delimited YAML block at the top of each file.

## 6. Test catalog (v1)

### 6.1 Graph integrity (core)

- **Manifest shape** — the Phase Map parses to the expected set of rows; Skill IDs are unique; the phase sequence is the canonical `1 → 11` plus `8.5`, `Gate A`, `Gate B`.
- **Skill existence & frontmatter** — every Skill ID in the table has a matching `skills/<dir>/SKILL.md`; every `SKILL.md` has valid YAML frontmatter; frontmatter `name` equals the Skill ID.
- **No orphan skills** — every `skills/*/SKILL.md` is either in the Phase Map or on the allow-list `{using-methodology (keystone), running-sample-engagement (meta)}`.
- **Agent existence & frontmatter** — every agent named in a skill's Subagent Dispatch section exists in `agents/`; every `agents/*.md` has valid frontmatter. (Orphan-agent detection — agents referenced by nothing — starts as a reported/allow-listed soft check, since the correct allow-list is discovered during implementation.)
- **Chain integrity** — every "Chain to next skill" target resolves to a real skill ID and is consistent with the keystone phase sequence.
- **Output conformance** — each phase's declared output file in the Phase Map matches the Engagement Folder Convention list in the same keystone; the two lists cannot drift.

### 6.2 Anti-regression guards

| Guard | Defends | Assertion |
|---|---|---|
| **Data-arch** | per-OPP normalization | Zero references to `opportunities\.md` or `scored-opportunities\.md` across `skills/` and `agents/`. Regex anchors the escaped `.md` so the `opportunities/` folder never false-matches. |
| **#5 isolation** | engagement-folder root-scatter | Every output-producing skill (all phases + both gates, **except** `scoping-engagement`, which *establishes* the field) contains the scope.md self-read marker (`Engagement folder:` extraction at Session Start). |
| **#8 ordering** | Gate B running after Phase 10 | Three checks: Phase 10's gate condition cites deliverable-gate clearance; `deliverable-gate`'s Session-Start read-list does **not** include `executive-summary.md`; the `running-sample-engagement` phase table sequences Gate B before Phase 10. |

### 6.3 Plugin manifest & version

- `plugin.json` is valid JSON and parses.
- `plugin.json.version` is valid semver, **and** matches the version string referenced in `INSTALL.md` (the exact drift that bit us).
- *(optional, non-blocking)* `version >= latest git tag` — a soft check that tolerates release-prep commits where the bump legitimately precedes the tag.

## 7. CI & developer workflow

- **`requirements.txt`** — `pytest`, `pyyaml`.
- **`pytest.ini`** — sets `testpaths` and rootdir so `pytest` from the repo root finds `tests/` (and later `engine/tests/`).
- **`Makefile`** — `make install` → `pip install -r requirements.txt`; `make test` → `pytest -q`.
- **`.github/workflows/test.yml`** — runs on `push` and `pull_request`: `ubuntu-latest`, `setup-python` (3.12), install requirements, `pytest`. Checkout uses `fetch-depth: 0` and fetches tags **only** to support the optional soft tag check.
- **`INSTALL.md`** — gains a short "Running the tests" section.

## 8. Testing & trust

The suite is **tested behavior, not generated-per-run** — the parser and assertions are fixed code reviewed once. Trust comes from the parser being small and the assertions being explicit. Where a guard targets a specific past defect, an inline comment names the issue it defends so a future reader understands why the check exists. The suite must run green against the repository as it stands today (the hand-fixes are already in place); a failure on day one means either a real residual defect or a parser bug, both of which are worth surfacing.

## 9. Out of scope for v1 (named fast-follows)

- **Sample-fixture consistency** — codify the Lattice greps: blended rate `$225/hr`, fully-loaded `~$130K/FTE`, and consistent people/systems names across the four intake files. Next after v1.
- **Hook validity** — `session-start.sh` is valid bash (e.g. `shellcheck`); `hooks.json` / `hooks-cursor.json` reference scripts that exist.
- **Math-engine golden tests** — issue #9; this stack leaves the `engine/tests/` slot and shared runner open for it.
- **Behavioral / LLM-in-the-loop evals** — Layer 3; a separate effort with its own design.

## 10. Build order

1. `requirements.txt`, `pytest.ini`, `Makefile`, `methodology_model.py` + `conftest.py` — the parser and fixtures, with a smoke test that the model loads.
2. `test_manifest.py`, `test_skills.py`, `test_agents.py`, `test_chain.py`, `test_outputs.py` — graph integrity, green against today's repo.
3. `test_guards.py`, `test_plugin_manifest.py` — anti-regression and version guards.
4. `.github/workflows/test.yml` + `INSTALL.md` "Running the tests" section + version bump.

## 11. Acceptance criteria

- `pytest` runs from the repo root with no arguments and discovers the `tests/` suite.
- The parser reads the keystone Phase Map, all 16 skills, and all 13 agents into one model exposed as a fixture.
- Graph-integrity tests pass against the current repo: every Skill ID resolves to a real skill with valid frontmatter whose `name` matches; every referenced agent exists; every chain link resolves and follows the phase sequence; declared output files match the Engagement Folder Convention list; the phase sequence and gate ordering are correct.
- Anti-regression guards pass and would fail if their defect were reintroduced: no retired-monolithic-file references; every output-producing skill (except `scoping-engagement`) carries the scope.md self-read; `deliverable-gate` does not read `executive-summary.md` and Phase 10 is gated on its clearance.
- `plugin.json` is valid semver and consistent with `INSTALL.md`.
- A GitHub Actions workflow runs the suite on push and PR and reports green.
- Each anti-regression guard names, in a comment, the issue it defends.

## 12. Appendix — guard-to-defect traceability

| Defect | Issue | Guard that now defends it |
|---|---|---|
| Engagement files scatter to project root | #5 | scope.md self-read present in every output-producing skill |
| Gate B sequenced after Phase 10 | #8 | Phase 10 gated on deliverable-gate; gate doesn't read exec-summary; sample table order |
| Skills reference retired monolithic files | data-arch norm | zero `opportunities.md` / `scored-opportunities.md` references |
| `plugin.json` version lags `INSTALL.md` / tag | version drift | semver + `plugin.json` ↔ `INSTALL.md` consistency |
