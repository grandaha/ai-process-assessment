# Static Test Stack (Layer 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a deterministic, LLM-free `pytest` suite that parses the keystone Phase Map as the single source of truth and asserts every skill, agent, chain link, and output file conforms to it — plus anti-regression guards for the #5, #8, data-arch, and version-drift defect classes.

**Architecture:** One parser (`tests/methodology_model.py`) reads the keystone table in `skills/using-methodology/SKILL.md` plus every `skills/*/SKILL.md` and `agents/*.md` into frozen dataclasses, exposed once per session via a `methodology` fixture in `tests/conftest.py`. Eight test modules assert structure against that model. A `.github/workflows/test.yml` runs the suite on push and PR.

**Tech Stack:** Python 3.12, `pytest`, `pyyaml` (frontmatter parsing), Python stdlib `re`/`json`/`pathlib`. No LLM, no network.

---

## Source-of-truth facts (verified against the repo at commit 77bc786)

These are the ground-truth values the tests assert against. They were read directly from the repo while writing this plan; an implementer does not need to re-derive them, but every one is checked by a test so drift is caught.

- **16 skills** in `skills/*/SKILL.md`; **14 agents** in `agents/*.md` (was 13 — Task 4 surfaced a dangling `process-mapper` dispatch with no agent file and the agent was authored; see "Execution deviations").
- **Skill frontmatter** `name` is namespaced: `ai-process-assessment:<dir-name>` (e.g. `ai-process-assessment:scoping-engagement`).
- **Agent frontmatter** `name` is the bare filename stem (e.g. `business-case-analyst`), not namespaced.
- **Phase Map** has **14 rows**: phases `1 2 3 4 5 6 7 8 8.5 9 10 11` then `Gate A` then `Gate B`.
- **14 phase skill IDs** (one per row); the **2 non-phase skills** are `using-methodology` (keystone) and `running-sample-engagement` (meta).
- **plugin.json** lives at `.claude-plugin/plugin.json`, currently `"version": "2.2.0"`.
- **INSTALL.md** references the version once, in a JSON snippet: `"version": "2.2.0",` (line ~38).
- **scope.md self-read marker** present verbatim in all 13 output-producing phase skills (every phase skill *except* `scoping-engagement`): the substring `` extract the `Engagement folder:` field ``.
- **All 14 agents are referenced** by at least one skill → there are **no orphan agents** today (orphan-agent allow-list is empty).
- **Chain links** form one connected path: scoping→mapping-context→inventorying-tech-data→discovering-processes→identifying-opportunities→governance-risk-gate→scoring-opportunities→prioritizing-roadmap→packaging-usecases→collecting-cost-actuals→building-business-case→deliverable-gate→building-executive-summary→building-deliverable (**terminal — no `→` arrow**).
- **Data-arch residual (the one day-one failure):** `scored-opportunities.md` is still referenced in 6 places — `agents/section-renderer-portfolio.md` (lines 3, 11, 17, 19, 108) and `skills/building-deliverable/SKILL.md` (line ~185). Task 7 fixes these so the data-arch guard asserts strict-zero.

---

## File Structure

**New files (all created by this plan):**

| File | Responsibility |
|---|---|
| `requirements.txt` | Pin `pytest`, `pyyaml`. |
| `pytest.ini` | `testpaths = tests`; rootdir config so bare `pytest` finds the suite. |
| `Makefile` | `make install`, `make test`. |
| `tests/methodology_model.py` | THE parser. Keystone table + skill/agent frontmatter + chain targets + convention list → frozen dataclasses. The only file that reads the repo's prose; every test reads *it*. |
| `tests/conftest.py` | Session-scoped `methodology` fixture; puts `tests/` on `sys.path`. |
| `tests/test_smoke.py` | Model loads (Task 1 sanity; smallest possible exercise of the parser). |
| `tests/test_manifest.py` | Phase Map well-formed; row count; phase labels/order; unique skill IDs. |
| `tests/test_skills.py` | Every phase skill ID resolves; frontmatter valid; `name` matches dir; no orphan skills. |
| `tests/test_agents.py` | Agent frontmatter valid; `name` matches filename; referenced agents resolve; orphan-agent soft check. |
| `tests/test_chain.py` | Every chain target resolves; the chain forms one connected path covering all 14 phase skills. |
| `tests/test_outputs.py` | Each phase's declared output token is in the Engagement Folder Convention list. |
| `tests/test_guards.py` | Anti-regression guards: data-arch (strict-zero), #5 isolation, #8 ordering. |
| `tests/test_plugin_manifest.py` | plugin.json valid + semver + matches INSTALL.md; optional soft tag check. |
| `.github/workflows/test.yml` | CI: pytest on push + PR. |

**Existing files modified (Task 7 remediation + Task 11 docs/version):**

| File | Change | Task |
|---|---|---|
| `agents/section-renderer-portfolio.md` | Rewrite to join the normalized folders (`scores/_index.md` + `opportunities/_index.md` + `opportunities/OPP-NNN.md` titles + `roadmap.md` waves); drop all `scored-opportunities.md` refs; fix "7 dimensions"→"6", "12 rows"→dynamic. | 7 |
| `skills/building-deliverable/SKILL.md` | Source-file existence list: replace `scored-opportunities.md` with `scores/_index.md`. | 7 |
| `INSTALL.md` | Add "Running the tests" section; bump version `2.2.0`→`2.3.0`. | 11 |
| `.claude-plugin/plugin.json` | Bump version `2.2.0`→`2.3.0`. | 11 |

**A note on TDD for this plan.** Most tests here are *characterization/guard* tests over artifacts that are already correct, so they go green on first run (spec §8: "must run green against the repository as it stands today; a failure on day one means a real residual defect or a parser bug — both worth surfacing"). For those, the discipline is: write the test, run it, **confirm PASS**; if it fails, you found a real defect — stop and surface it. **Task 7 is the one classic red→green cycle**: its data-arch guard fails first (catches the 6 residual refs), and the remediation edits make it pass.

---

## Task 1: Scaffolding — config, parser, fixture, smoke test

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `Makefile`
- Create: `tests/methodology_model.py`
- Create: `tests/conftest.py`
- Test: `tests/test_smoke.py`

- [ ] **Step 1: Create `requirements.txt`**

```
pytest>=8.0
pyyaml>=6.0
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
# When issue #9 lands, append engine/tests to testpaths:
#   testpaths = tests engine/tests
```

- [ ] **Step 3: Create `Makefile`** (indentation MUST be tabs, not spaces)

```makefile
.PHONY: install test

install:
	pip install -r requirements.txt

test:
	pytest -q
```

- [ ] **Step 4: Commit the scaffolding**

```bash
git add requirements.txt pytest.ini Makefile
git commit -m "test: add pytest scaffolding (requirements, pytest.ini, Makefile)

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

- [ ] **Step 5: Write the failing smoke test** — `tests/test_smoke.py`

```python
"""Smoke test: the methodology model parses and is non-empty."""


def test_model_loads(methodology):
    assert methodology.phases, "no phase rows parsed from the keystone Phase Map"
    assert methodology.skills, "no skills loaded"
    assert methodology.agents, "no agents loaded"
    assert methodology.convention_files, "no Engagement Folder Convention files parsed"
```

- [ ] **Step 6: Run it to verify it fails**

Run: `pytest tests/test_smoke.py -q`
Expected: FAIL — `fixture 'methodology' not found` (conftest/parser do not exist yet).

- [ ] **Step 7: Write the parser** — `tests/methodology_model.py`

```python
"""Parse the methodology into a frozen, testable model.

Single source of truth: the Phase Map table in skills/using-methodology/SKILL.md.
Every test asserts the rest of the repo conforms to what this parser reads.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS_DIR = REPO_ROOT / "agents"
KEYSTONE = SKILLS_DIR / "using-methodology" / "SKILL.md"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_ARROW_RE = re.compile(r"→\s*`([^`]+)`")


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PhaseRow:
    phase: str            # "1".."11", "8.5", "Gate A", "Gate B"
    skill_id: str         # "ai-process-assessment:scoping-engagement"
    gate_condition: str   # raw text of the gate-condition cell
    output_file: str      # leading file/folder token, backticks stripped


@dataclass(frozen=True)
class SkillDoc:
    skill_id: str         # frontmatter `name`
    dir_name: str         # directory stem under skills/
    description: str
    body: str             # full file text
    chain_target: str | None  # skill_id from "Chain to next skill", or None
    path: Path


@dataclass(frozen=True)
class AgentDoc:
    name: str             # frontmatter `name` (bare stem)
    description: str
    body: str
    path: Path


@dataclass(frozen=True)
class Methodology:
    phases: list[PhaseRow]
    skills: dict[str, SkillDoc]   # keyed by skill_id
    agents: dict[str, AgentDoc]   # keyed by name
    convention_files: list[str]   # tokens from the Engagement Folder Convention list


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def section(text: str, header: str) -> str:
    """Return the slice from `header` up to the next `## ` heading (or EOF)."""
    start = text.find(header)
    if start == -1:
        raise ValueError(f"section not found: {header!r}")
    rest = text[start + len(header):]
    nxt = re.search(r"\n##\s", rest)
    return rest[: nxt.start()] if nxt else rest


def _strip_backticks(cell: str) -> str:
    return cell.strip().strip("`").strip()


def _leading_token(cell: str) -> str:
    """First backticked file/folder token in a table cell (else first word)."""
    cell = cell.strip()
    m = _BACKTICK_RE.search(cell)
    token = m.group(1) if m else cell.split()[0]
    return token.strip().rstrip(",")


def _is_table_row(line: str) -> bool:
    return line.strip().startswith("|")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


# --------------------------------------------------------------------------- #
# Loaders
# --------------------------------------------------------------------------- #
def parse_phase_map() -> list[PhaseRow]:
    text = KEYSTONE.read_text(encoding="utf-8")
    block = section(text, "## Phase Map")
    rows: list[PhaseRow] = []
    for line in block.splitlines():
        if not _is_table_row(line):
            continue
        cells = _cells(line)
        if len(cells) < 5:
            continue
        if cells[0] == "Phase":                       # header row
            continue
        if set(cells[0]) <= {"-", ":"}:               # separator row
            continue
        rows.append(
            PhaseRow(
                phase=cells[0],
                skill_id=_strip_backticks(cells[1]),
                gate_condition=cells[3],
                output_file=_leading_token(cells[4]),
            )
        )
    return rows


def parse_convention_files() -> list[str]:
    text = KEYSTONE.read_text(encoding="utf-8")
    block = section(text, "## Engagement Folder Convention")
    files: list[str] = []
    for line in block.splitlines():
        if line.strip().startswith("- "):
            m = _BACKTICK_RE.search(line)
            if m:
                files.append(m.group(1).strip())
    return files


def _chain_target(text: str) -> str | None:
    idx = text.find("## Chain to next skill")
    if idx == -1:
        return None
    m = _ARROW_RE.search(text[idx:])
    return m.group(1).strip() if m else None


def load_skills() -> dict[str, SkillDoc]:
    skills: dict[str, SkillDoc] = {}
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        skill_id = (fm.get("name") or "").strip()
        skills[skill_id] = SkillDoc(
            skill_id=skill_id,
            dir_name=path.parent.name,
            description=(fm.get("description") or "").strip(),
            body=text,
            chain_target=_chain_target(text),
            path=path,
        )
    return skills


def load_agents() -> dict[str, AgentDoc]:
    agents: dict[str, AgentDoc] = {}
    for path in sorted(AGENTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        name = (fm.get("name") or "").strip()
        agents[name] = AgentDoc(
            name=name,
            description=(fm.get("description") or "").strip(),
            body=text,
            path=path,
        )
    return agents


def build_methodology() -> Methodology:
    return Methodology(
        phases=parse_phase_map(),
        skills=load_skills(),
        agents=load_agents(),
        convention_files=parse_convention_files(),
    )
```

- [ ] **Step 8: Write the fixture** — `tests/conftest.py`

```python
import sys
from pathlib import Path

import pytest

# Make methodology_model importable regardless of pytest rootdir.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from methodology_model import build_methodology  # noqa: E402


@pytest.fixture(scope="session")
def methodology():
    return build_methodology()
```

- [ ] **Step 9: Run the smoke test to verify it passes**

Run: `pytest tests/test_smoke.py -q`
Expected: PASS (1 passed).

- [ ] **Step 10: Commit the parser, fixture, smoke test**

```bash
git add tests/methodology_model.py tests/conftest.py tests/test_smoke.py
git commit -m "test: methodology parser, session fixture, smoke test

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 2: Manifest tests — Phase Map shape, order, uniqueness

**Files:**
- Test: `tests/test_manifest.py`

- [ ] **Step 1: Write the tests** — `tests/test_manifest.py`

```python
"""The keystone Phase Map parses to the expected shape and order."""

EXPECTED_PHASES = [
    "1", "2", "3", "4", "5", "6", "7", "8", "8.5", "9", "10", "11",
    "Gate A", "Gate B",
]


def test_phase_map_row_count(methodology):
    assert len(methodology.phases) == 14


def test_phase_labels_in_canonical_order(methodology):
    labels = [p.phase for p in methodology.phases]
    assert labels == EXPECTED_PHASES


def test_skill_ids_unique(methodology):
    ids = [p.skill_id for p in methodology.phases]
    assert len(ids) == len(set(ids)), "duplicate skill IDs in the Phase Map"


def test_every_phase_has_a_skill_id(methodology):
    for p in methodology.phases:
        assert p.skill_id.startswith("ai-process-assessment:"), p


def test_every_phase_has_an_output_token(methodology):
    for p in methodology.phases:
        assert p.output_file, f"phase {p.phase} has no output token"


def test_numeric_phases_ascending(methodology):
    nums = [float(p.phase) for p in methodology.phases
            if p.phase not in ("Gate A", "Gate B")]
    assert nums == sorted(nums)
```

- [ ] **Step 2: Run and verify all pass**

Run: `pytest tests/test_manifest.py -q`
Expected: PASS (6 passed). If `test_phase_labels_in_canonical_order` fails, the parser mis-read the table or the keystone changed — investigate before proceeding.

- [ ] **Step 3: Commit**

```bash
git add tests/test_manifest.py
git commit -m "test: Phase Map manifest shape, order, and uniqueness

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 3: Skill tests — existence, frontmatter, no orphans

**Files:**
- Test: `tests/test_skills.py`

- [ ] **Step 1: Write the tests** — `tests/test_skills.py`

```python
"""Every Phase Map skill ID resolves to a well-formed SKILL.md; no orphans."""

# Skills intentionally absent from the Phase Map:
#   using-methodology     — the keystone (carries the map itself)
#   running-sample-engagement — meta entry point for the bundled demo
ALLOWLIST_NON_PHASE = {
    "ai-process-assessment:using-methodology",
    "ai-process-assessment:running-sample-engagement",
}


def test_every_phase_skill_id_has_a_skill_file(methodology):
    for p in methodology.phases:
        assert p.skill_id in methodology.skills, \
            f"Phase {p.phase} skill ID has no skills/*/SKILL.md: {p.skill_id}"


def test_every_skill_has_name_frontmatter(methodology):
    for skill in methodology.skills.values():
        assert skill.skill_id, f"missing frontmatter name: {skill.path}"
        assert skill.skill_id.startswith("ai-process-assessment:"), skill.path


def test_every_skill_has_description_frontmatter(methodology):
    for skill in methodology.skills.values():
        assert skill.description, f"missing frontmatter description: {skill.path}"


def test_skill_name_matches_directory(methodology):
    for skill in methodology.skills.values():
        assert skill.skill_id == f"ai-process-assessment:{skill.dir_name}", \
            f"name/dir mismatch: {skill.skill_id} in {skill.path}"


def test_no_orphan_skills(methodology):
    phase_ids = {p.skill_id for p in methodology.phases}
    allowed = phase_ids | ALLOWLIST_NON_PHASE
    orphans = [sid for sid in methodology.skills if sid not in allowed]
    assert not orphans, f"skills not in Phase Map or allow-list: {orphans}"


def test_skill_count(methodology):
    # 14 phase skills + 2 allow-listed non-phase skills.
    assert len(methodology.skills) == 16
```

- [ ] **Step 2: Run and verify all pass**

Run: `pytest tests/test_skills.py -q`
Expected: PASS (6 passed).

- [ ] **Step 3: Commit**

```bash
git add tests/test_skills.py
git commit -m "test: skill existence, frontmatter, name/dir match, no orphans

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 4: Agent tests — frontmatter, referenced-agent resolution, orphan soft check

**Files:**
- Test: `tests/test_agents.py`

- [ ] **Step 1: Write the tests** — `tests/test_agents.py`

```python
"""Agents are well-formed; every agent referenced by a skill resolves."""
import re

# Backticked bare-identifier tokens captured by the dispatch-phrasing patterns
# below that are NOT agents. Empty today; populate (with a comment) only if
# test_referenced_agents_resolve surfaces a false positive during implementation.
NON_AGENT_TOKENS: set[str] = set()

# Agents referenced by no skill. Empty today — all 14 agents are referenced.
ORPHAN_AGENT_ALLOWLIST: set[str] = set()

# Phrasings that unambiguously introduce an agent. Each requires the ENTIRE
# backtick span to be a bare identifier (open-backtick + token + close-backtick),
# so file tokens like `process-map.md` or `_staging/phase6/OPP.md` never match.
_REF_PATTERNS = [
    re.compile(r"`([a-z][a-z0-9-]+)`\s+subagent"),          # "`name` subagent"
    re.compile(r"[Dd]ispatch[^`\n]{0,40}?`([a-z][a-z0-9-]+)`"),  # "dispatch ... `name`"
    re.compile(r"`([a-z][a-z0-9-]+)`\s*←"),                 # "`name` ← ..." (renderer arrow)
]


def test_every_agent_has_name_frontmatter(methodology):
    for agent in methodology.agents.values():
        assert agent.name, f"missing frontmatter name: {agent.path}"


def test_every_agent_has_description_frontmatter(methodology):
    for agent in methodology.agents.values():
        assert agent.description, f"missing frontmatter description: {agent.path}"


def test_agent_name_matches_filename(methodology):
    for agent in methodology.agents.values():
        assert agent.name == agent.path.stem, \
            f"name/filename mismatch: {agent.name} in {agent.path}"


def test_agent_count(methodology):
    # 14 after Task 4 surfaced and fixed the missing process-mapper agent.
    assert len(methodology.agents) == 14


def _referenced_agent_tokens(methodology) -> set[str]:
    """Tokens captured by the dispatch-phrasing patterns across all skill bodies,
    minus the NON_AGENT_TOKENS allow-list. Does NOT pre-filter by existence, so a
    dispatched-but-missing agent is caught by test_referenced_agents_resolve."""
    tokens: set[str] = set()
    for skill in methodology.skills.values():
        for pat in _REF_PATTERNS:
            for m in pat.finditer(skill.body):
                tok = m.group(1)
                if tok not in NON_AGENT_TOKENS:
                    tokens.add(tok)
    return tokens


def test_referenced_agents_resolve(methodology):
    # Every agent a skill dispatches must exist as a file in agents/.
    for tok in sorted(_referenced_agent_tokens(methodology)):
        assert tok in methodology.agents, (
            f"a skill dispatches an agent with no file: {tok!r} "
            f"(if this token is not an agent, add it to NON_AGENT_TOKENS)"
        )


def test_no_unexpected_orphan_agents(methodology):
    # Soft check: agents referenced by no skill at all. Allow-list is empty today.
    referenced: set[str] = set()
    for skill in methodology.skills.values():
        for name in methodology.agents:
            if name in skill.body:
                referenced.add(name)
    orphans = set(methodology.agents) - referenced - ORPHAN_AGENT_ALLOWLIST
    assert not orphans, f"agents referenced by no skill: {sorted(orphans)}"
```

- [ ] **Step 2: Run and verify all pass**

Run: `pytest tests/test_agents.py -q`
Expected: PASS (6 passed). If `test_no_unexpected_orphan_agents` fails, an agent is genuinely unreferenced — add it to `ORPHAN_AGENT_ALLOWLIST` with a comment only if that is intentional, else fix the dangling reference.

- [ ] **Step 3: Commit**

```bash
git add tests/test_agents.py
git commit -m "test: agent frontmatter, reference resolution, orphan soft check

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 5: Chain tests — every link resolves; one connected path

**Files:**
- Test: `tests/test_chain.py`

- [ ] **Step 1: Write the tests** — `tests/test_chain.py`

```python
"""Chain-to-next-skill links resolve and form one connected phase path."""

ENTRY_SKILL = "ai-process-assessment:scoping-engagement"
TERMINAL_SKILL = "ai-process-assessment:building-deliverable"


def test_every_chain_target_resolves(methodology):
    for skill in methodology.skills.values():
        if skill.chain_target is None:
            continue
        assert skill.chain_target in methodology.skills, \
            f"{skill.skill_id} chains to unknown skill: {skill.chain_target}"


def test_chain_forms_one_connected_path(methodology):
    # Walk from the Phase 1 entry skill following chain_target until terminal,
    # detecting cycles. The walk must cover every phase skill and end at Phase 11.
    visited: list[str] = []
    seen: set[str] = set()
    current = ENTRY_SKILL
    while current is not None and current not in seen:
        seen.add(current)
        visited.append(current)
        skill = methodology.skills.get(current)
        if skill is None:
            break
        current = skill.chain_target

    assert visited[-1] == TERMINAL_SKILL, \
        f"chain did not terminate at Phase 11: ended at {visited[-1]}"

    phase_ids = {p.skill_id for p in methodology.phases}
    missing = phase_ids - set(visited)
    assert not missing, f"chain does not cover these phase skills: {sorted(missing)}"


def test_terminal_skill_has_no_chain_target(methodology):
    assert methodology.skills[TERMINAL_SKILL].chain_target is None
```

- [ ] **Step 2: Run and verify all pass**

Run: `pytest tests/test_chain.py -q`
Expected: PASS (3 passed). `test_chain_forms_one_connected_path` visits all 14 phase skills (scoping → … → building-deliverable). A failure means a chain link was retargeted or broken.

- [ ] **Step 3: Commit**

```bash
git add tests/test_chain.py
git commit -m "test: chain links resolve and form one connected phase path

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 6: Output-conformance tests — declared outputs vs convention list

**Files:**
- Test: `tests/test_outputs.py`

- [ ] **Step 1: Write the tests** — `tests/test_outputs.py`

```python
"""Each phase's declared output token appears in the Engagement Folder
Convention list in the same keystone — the two lists cannot drift."""


def test_every_phase_output_is_in_convention_list(methodology):
    convention = set(methodology.convention_files)
    for p in methodology.phases:
        assert p.output_file in convention, (
            f"Phase {p.phase} output {p.output_file!r} is not in the "
            f"Engagement Folder Convention list: {sorted(convention)}"
        )


def test_convention_list_nonempty_and_includes_core_files(methodology):
    convention = set(methodology.convention_files)
    for required in ("scope.md", "opportunities/", "scores/", "grc/",
                     "evidence-log.md", "deliverable.html"):
        assert required in convention, f"convention list missing {required}"
```

- [ ] **Step 2: Run and verify all pass**

Run: `pytest tests/test_outputs.py -q`
Expected: PASS (2 passed). All 14 phase output tokens (`scope.md`, `context.md`, `tech-inventory.md`, `process-map.md`, `opportunities/`, `scores/`, `roadmap.md`, `usecase-briefs/`, `cost-actuals.md`, `business-case.md`, `executive-summary.md`, `deliverable.html`, `grc/`, `evidence-log.md`) are present in the convention list.

- [ ] **Step 3: Commit**

```bash
git add tests/test_outputs.py
git commit -m "test: phase outputs conform to Engagement Folder Convention list

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 7: Data-arch guard + remediation (red → green)

This is the one classic TDD cycle: the guard fails first (catches the 6 residual `scored-opportunities.md` references the v2.1.0 normalization missed), then the remediation makes it pass. The remediation rewrites the portfolio renderer to join the normalized folders — the architecturally correct fix, since Phase 11 is an assembly phase.

**Files:**
- Test: `tests/test_guards.py` (data-arch section only; #5 and #8 added in Task 8)
- Modify: `agents/section-renderer-portfolio.md`
- Modify: `skills/building-deliverable/SKILL.md`

- [ ] **Step 1: Write the data-arch guard** — create `tests/test_guards.py`

```python
"""Anti-regression guards. Each guard names, in a comment, the defect it defends.

This file grows in three tasks:
  Task 7 — data-arch (this section)
  Task 8 — #5 isolation and #8 ordering
"""
import re
from pathlib import Path

from methodology_model import REPO_ROOT

# --- Data-arch guard (defends: per-OPP data-architecture normalization, v2.1.0) ---
# After normalization, per-OPP artifacts live in the opportunities/, scores/, and
# grc/ folders. The monolithic files opportunities.md and scored-opportunities.md
# are retired and must not be referenced anywhere in skills/ or agents/.
#   - (?<![\w-])opportunities\.md  matches the retired monolith but NOT the
#     opportunities/ folder (no ".md") and NOT scored-opportunities.md (preceded by "-").
#   - scored-opportunities\.md     matches the other retired monolith.
RETIRED_FILE_PATTERNS = [
    re.compile(r"(?<![\w-])opportunities\.md"),
    re.compile(r"scored-opportunities\.md"),
]


def _methodology_markdown_files() -> list[Path]:
    return sorted(
        list((REPO_ROOT / "skills").rglob("SKILL.md"))
        + list((REPO_ROOT / "agents").glob("*.md"))
    )


def test_no_retired_monolithic_file_references():
    offenders = []
    for path in _methodology_markdown_files():
        text = path.read_text(encoding="utf-8")
        for pat in RETIRED_FILE_PATTERNS:
            if pat.search(text):
                rel = path.relative_to(REPO_ROOT)
                offenders.append(f"{rel} :: {pat.pattern}")
    assert not offenders, "retired-file references found:\n" + "\n".join(offenders)
```

- [ ] **Step 2: Run to verify it FAILS (catches the residual)**

Run: `pytest tests/test_guards.py -q`
Expected: FAIL — offenders list names `agents/section-renderer-portfolio.md :: scored-opportunities\.md` and `skills/building-deliverable/SKILL.md :: scored-opportunities\.md`.

- [ ] **Step 3: Rewrite `agents/section-renderer-portfolio.md`**

Replace the file's content from the top through the `## Inputs required` section, and update the subtitle, row-count language, and operating-constraints source line. Apply these exact edits:

**3a. Frontmatter `description` (line 3)** — replace:
```
description: Phase 11 section renderer — reads scored-opportunities.md and produces the #portfolio section: a 12-row visual table with type badges, score bars, and wave pills. Renders the ranked portfolio table only — not the per-OPP dimensional score detail.
```
with:
```
description: Phase 11 section renderer — assembles the #portfolio ranked table by joining scores/_index.md, opportunities/_index.md, and roadmap.md. Visual table with type badges, score bars, and wave pills — one row per scored opportunity. Does not render per-OPP dimensional score detail.
```

**3b. `## Role` paragraph (line 11)** — replace:
```
Synthesis renderer. Reads only the `## Ranked Portfolio` table from `scored-opportunities.md`. Renders it as a designed HTML table with type badges, score bars, and wave pills. Does NOT render the individual per-OPP dimensional score entries below the ranked portfolio table.
```
with:
```
Synthesis renderer. Assembles the ranked portfolio by joining the normalized Phase 6/5/7 folders on OPP-ID, then renders one designed HTML table with type badges, score bars, and wave pills. Does NOT render per-OPP dimensional score detail (the six-dimension tables in `scores/OPP-NNN.md`).
```

**3c. `## Inputs required` table + the paragraph after it (lines 15-19)** — replace:
```
| Input | File | Required section |
|---|---|---|
| Scored opportunities | `scored-opportunities.md` | `## Ranked Portfolio` table only |

You receive `scored-opportunities.md` only. No other source files. Read only the `## Ranked Portfolio` table — stop there. Do not process the per-OPP dimensional detail sections that follow it.
```
with:
```
| Input | File | What to read |
|---|---|---|
| Composite scores + sourcing | `scores/_index.md` | `OPP-ID \| Composite \| Horizon \| B/B/P` table — the ranking source |
| Opportunity types | `opportunities/_index.md` | `OPP-ID \| Process \| Type \| ...` table — the Type per OPP |
| Opportunity titles | `opportunities/OPP-NNN.md` | the `## OPP-NNN — [title]` header line, per OPP |
| Wave assignment | `roadmap.md` | which wave (Foundation→1, Scale→2, Optimize→3) each OPP is sequenced into |

Join the four sources on OPP-ID. Rank rows by composite score, descending. Do not read or render the six-dimension detail in `scores/OPP-NNN.md`.
```

**3d. Output-block subtitle (line 28)** — replace:
```
  <p style="color:#64748b; font-size:13px;">12 opportunities evaluated — scored across 7 dimensions</p>
```
with:
```
  <p style="color:#64748b; font-size:13px;">[N] opportunities evaluated — scored across 6 dimensions</p>
```

**3e. Output-block row comment (line 42)** — replace:
```
      <!-- One row per ranked portfolio entry — 12 rows total -->
```
with:
```
      <!-- One row per scored opportunity, ranked by composite score descending -->
```

**3f. Hard refusals (line 101-102)** — replace:
```
- Do not render dimensional score tables — the per-OPP scored entries below `## Ranked Portfolio` are not rendered
- Do not omit any of the 12 portfolio rows
```
with:
```
- Do not render dimensional score tables — the six-dimension entries in `scores/OPP-NNN.md` are not rendered
- Do not omit any scored opportunity — render one row per OPP-ID present in `scores/_index.md`
```

**3g. Operating constraints (lines 108-109)** — replace:
```
- Source: `scored-opportunities.md` — `## Ranked Portfolio` section only
- Row count: exactly 12 rows (one per opportunity)
```
with:
```
- Sources: `scores/_index.md` (composite + B/B/P), `opportunities/_index.md` (type), `opportunities/OPP-NNN.md` (title), `roadmap.md` (wave)
- Row count: one row per OPP-ID in `scores/_index.md`
```

- [ ] **Step 4: Fix `skills/building-deliverable/SKILL.md` source list (line ~185)**

Replace:
```
- [ ] Confirm all 5 source files exist: `executive-summary.md`, `baselines.md`, `scored-opportunities.md`, `roadmap.md`, `evidence-log.md`
```
with:
```
- [ ] Confirm all 5 source files exist: `executive-summary.md`, `baselines.md`, `scores/_index.md`, `roadmap.md`, `evidence-log.md`
```

- [ ] **Step 5: Run the guard to verify it now PASSES**

Run: `pytest tests/test_guards.py -q`
Expected: PASS (1 passed).

- [ ] **Step 6: Re-run the full suite to confirm no collateral breakage**

Run: `pytest -q`
Expected: all tests pass (the renderer/source-list edits do not touch any structure the other tests assert).

- [ ] **Step 7: Commit (test + remediation together — the green of one red→green cycle)**

```bash
git add tests/test_guards.py agents/section-renderer-portfolio.md skills/building-deliverable/SKILL.md
git commit -m "test+fix: data-arch guard; rewrite portfolio renderer to join normalized folders

Guard asserts zero references to the retired opportunities.md /
scored-opportunities.md monoliths. Remediation rewrites
section-renderer-portfolio to assemble the ranked table from
scores/_index.md + opportunities/_index.md + roadmap.md (the v2.1.0
normalization left it pointed at the retired file), and fixes
building-deliverable's source-file list. Also corrects stale
'7 dimensions' (now 6) and hardcoded '12 rows' (now dynamic).

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 8: #5 isolation guard + #8 ordering guard

**Files:**
- Modify: `tests/test_guards.py` (append)

- [ ] **Step 1: Append the #5 and #8 guards to `tests/test_guards.py`**

```python
# --- #5 isolation guard (defends: engagement-folder root-scatter, issue #5) ---
# Phase 1 (scoping-engagement) ESTABLISHES the Engagement folder field; every
# other output-producing phase skill must READ it back at Session Start, or its
# outputs scatter to the project root when the path is unset.
SELF_READ_MARKER = "extract the `Engagement folder:` field"
SELF_READ_EXEMPT = {"ai-process-assessment:scoping-engagement"}


def test_output_skills_carry_scope_self_read(methodology):
    phase_skill_ids = {p.skill_id for p in methodology.phases}
    for sid in sorted(phase_skill_ids):
        if sid in SELF_READ_EXEMPT:
            continue
        body = methodology.skills[sid].body
        assert SELF_READ_MARKER in body, \
            f"{sid} is missing the scope.md self-read marker (#5 guard)"


# --- #8 ordering guard (defends: Gate B running after Phase 10, issue #8) ---
# Gate B (deliverable-gate) runs BEFORE Phase 10. Three independent checks.

def _session_start_block(body: str) -> str:
    idx = body.find("## Session Start")
    assert idx != -1, "deliverable-gate has no Session Start section"
    rest = body[idx + len("## Session Start"):]
    nxt = re.search(r"\n##\s", rest)
    return rest[: nxt.start()] if nxt else rest


def test_phase10_gated_on_deliverable_gate(methodology):
    phase10 = next(p for p in methodology.phases if p.phase == "10")
    assert "deliverable-gate" in phase10.gate_condition, \
        "Phase 10 gate condition must cite deliverable-gate clearance"


def test_deliverable_gate_does_not_read_exec_summary(methodology):
    gate = methodology.skills["ai-process-assessment:deliverable-gate"]
    block = _session_start_block(gate.body)
    assert "executive-summary.md" not in block, \
        "deliverable-gate Session Start must not read executive-summary.md (it runs before Phase 10)"


def test_sample_sequences_gate_b_before_phase10(methodology):
    sample = methodology.skills["ai-process-assessment:running-sample-engagement"]
    rows = [l for l in sample.body.splitlines() if l.strip().startswith("|")]
    gate_b_idx = phase10_idx = None
    for i, row in enumerate(rows):
        first = row.strip().strip("|").split("|")[0].strip()
        if gate_b_idx is None and first.startswith("Gate B"):
            gate_b_idx = i
        if phase10_idx is None and first.startswith("10 "):
            phase10_idx = i
    assert gate_b_idx is not None, "sample table has no Gate B row"
    assert phase10_idx is not None, "sample table has no Phase 10 row"
    assert gate_b_idx < phase10_idx, \
        "sample sequences Gate B after Phase 10 (#8 regression)"
```

- [ ] **Step 2: Run the guards and verify all pass**

Run: `pytest tests/test_guards.py -q`
Expected: PASS (5 passed total — 1 data-arch + 1 #5 + 3 #8).

- [ ] **Step 3: Commit**

```bash
git add tests/test_guards.py
git commit -m "test: #5 isolation guard and #8 Gate-B-ordering guard (three checks)

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 9: Plugin manifest + version-consistency tests

**Files:**
- Test: `tests/test_plugin_manifest.py`

- [ ] **Step 1: Write the tests** — `tests/test_plugin_manifest.py`

```python
"""plugin.json is valid + semver, and its version matches INSTALL.md.

Version invariant is INTERNAL CONSISTENCY (plugin.json <-> INSTALL.md), not
tag-equality — a bump legitimately precedes its git tag during release prep.
The tag comparison below is an optional, skip-on-absence soft check.
"""
import json
import re
import subprocess

from methodology_model import REPO_ROOT

import pytest

PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
INSTALL_MD = REPO_ROOT / "INSTALL.md"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def _plugin_version() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def test_plugin_json_is_valid_json_with_version():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert "version" in data
    assert data.get("name") == "ai-process-assessment"


def test_plugin_version_is_semver():
    version = _plugin_version()
    assert SEMVER_RE.match(version), f"not valid semver: {version}"


def test_install_md_version_matches_plugin_json():
    version = _plugin_version()
    install = INSTALL_MD.read_text(encoding="utf-8")
    m = re.search(r'"version":\s*"([^"]+)"', install)
    assert m, "no version string found in INSTALL.md"
    assert m.group(1) == version, \
        f"INSTALL.md version {m.group(1)} != plugin.json version {version}"


def _semver_tuple(v: str) -> tuple[int, int, int]:
    core = v.lstrip("v").split("-")[0].split("+")[0]
    parts = core.split(".")
    return tuple(int(x) for x in (parts + ["0", "0", "0"])[:3])


def test_version_not_behind_latest_tag():
    # Optional soft check; skips cleanly when git/tags are unavailable.
    try:
        out = subprocess.run(
            ["git", "tag", "--list", "v*"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git unavailable")
    tags = [t for t in out.split() if SEMVER_RE.match(t.lstrip("v"))]
    if not tags:
        pytest.skip("no semver tags present")
    latest = max(tags, key=_semver_tuple)
    assert _semver_tuple(_plugin_version()) >= _semver_tuple(latest), \
        f"plugin.json version {_plugin_version()} is behind latest tag {latest}"
```

- [ ] **Step 2: Run and verify pass (tag check may skip)**

Run: `pytest tests/test_plugin_manifest.py -q`
Expected: PASS (3 passed, 1 skipped) or (4 passed) depending on whether tags are present locally. `test_install_md_version_matches_plugin_json` must pass (both are `2.2.0` right now).

- [ ] **Step 3: Commit**

```bash
git add tests/test_plugin_manifest.py
git commit -m "test: plugin.json valid + semver + INSTALL.md version consistency

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 10: CI workflow

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Create `.github/workflows/test.yml`**

```yaml
name: tests

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          # fetch tags so the optional soft tag check in test_plugin_manifest
          # has something to compare against (the test skips if none).
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
```

- [ ] **Step 2: Run the full suite locally one more time**

Run: `pytest -q`
Expected: all tests pass (one skip possible for the tag check if no local tags).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: run pytest suite on push and pull_request

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Task 11: INSTALL.md "Running the tests" + version bump to 2.3.0

The version-consistency test requires plugin.json and INSTALL.md to move together. Bump both in one commit so the suite stays green.

**Files:**
- Modify: `INSTALL.md` (add section + bump version)
- Modify: `.claude-plugin/plugin.json` (bump version)

- [ ] **Step 1: Add a "Running the tests" section to `INSTALL.md`**

Append this section (place it near the end, before any "Troubleshooting"/footer section if one exists):

```markdown
## Running the tests

The plugin ships a static test suite (Layer 1) that checks the methodology
graph and guards against known regressions. It is LLM-free and runs in seconds.

```bash
make install   # pip install -r requirements.txt  (pytest, pyyaml)
make test      # pytest -q
```

Or directly: `pytest` from the repo root. The suite parses the keystone Phase
Map in `skills/using-methodology/SKILL.md` and asserts every skill, agent,
chain link, and output file conforms to it.
```

- [ ] **Step 2: Bump the version in `INSTALL.md`** (the JSON snippet, line ~38)

Replace `"version": "2.2.0",` with `"version": "2.3.0",`.

- [ ] **Step 3: Bump the version in `.claude-plugin/plugin.json`** (line 4)

Replace `"version": "2.2.0",` with `"version": "2.3.0",`.

- [ ] **Step 4: Run the manifest tests to confirm consistency holds**

Run: `pytest tests/test_plugin_manifest.py -q`
Expected: PASS — `test_install_md_version_matches_plugin_json` confirms both are now `2.3.0`.

- [ ] **Step 5: Run the entire suite**

Run: `pytest -q`
Expected: full green (one skip possible for the tag check). This is the acceptance gate for the plan.

- [ ] **Step 6: Commit**

```bash
git add INSTALL.md .claude-plugin/plugin.json
git commit -m "docs: add Running the tests section; bump to v2.3.0

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>"
```

---

## Acceptance criteria (from spec §11)

- [ ] `pytest` runs from the repo root with no arguments and discovers `tests/`.
- [ ] The parser reads the keystone Phase Map, all 16 skills, and all 14 agents into one model exposed as the `methodology` fixture.
- [ ] Graph-integrity tests pass: every phase Skill ID resolves to a real skill with valid frontmatter whose `name` matches its directory; every referenced agent exists; every chain link resolves and the chain covers all phase skills ending at Phase 11; declared output tokens are in the convention list; phase order is canonical.
- [ ] Anti-regression guards pass and would fail if reintroduced: zero retired-monolith references; every output-producing phase skill except `scoping-engagement` carries the scope.md self-read; `deliverable-gate` does not read `executive-summary.md` and Phase 10 is gated on its clearance; the sample sequences Gate B before Phase 10.
- [ ] `plugin.json` is valid semver and consistent with `INSTALL.md` (both `2.3.0`).
- [ ] The GitHub Actions workflow runs the suite on push and PR.
- [ ] Each anti-regression guard names, in a comment, the issue/defect it defends.

## Out of scope (named fast-follows, spec §9)

- Sample-fixture consistency (Lattice `$225/hr`, `~$130K/FTE`, name consistency).
- Hook validity (`session-start.sh` shellcheck; `hooks*.json` script existence).
- Math-engine golden tests (issue #9 — shares this runner and `requirements.txt`).
- Behavioral / LLM-in-the-loop evals (Layer 3 — separate design).

## Self-review notes

- **Spec coverage:** every §6 catalog item maps to a task — 6.1 graph integrity → Tasks 2-6; 6.2 guards → Tasks 7-8; 6.3 manifest/version → Task 9; §7 CI/workflow → Tasks 10-11. Build order §10 followed (scaffold+parser → graph tests → guards → CI/docs/version).
- **Placeholder scan:** no TBD/TODO; all code blocks and commands are concrete. The renderer subtitle `[N] opportunities` and `[title]`/`[type label]` tokens in Task 7 are intentional *runtime template placeholders inside the agent prose* (the renderer fills them per engagement), not plan placeholders.
- **Type consistency:** dataclass field names (`phase`, `skill_id`, `gate_condition`, `output_file`, `chain_target`, `convention_files`) and `REPO_ROOT` are used identically across `methodology_model.py`, `conftest.py`, and all test modules. `section()` defined once in the parser; the #8 guard uses a local `_session_start_block` helper (does not depend on the parser's `section()` to keep the guard self-contained).
- **Day-one expectation:** all tasks green except Task 7's guard, which is red until its remediation step — by design.

## Execution deviations

Surprises found while executing the plan, and how they were resolved. Each is a real residual defect or environment fact the plan did not anticipate (spec §8: a day-one failure surfaces something worth fixing).

- **Task 1 — YAML frontmatter is not strict-parseable.** Several skill/agent `description:` values legitimately contain unquoted colons (`...five constraints: dependency...`, `...section: phase completion chips...`). Claude Code's loader accepts these; `yaml.safe_load` raises. `parse_frontmatter` was given a fallback that recovers the simple `name`/`description` scalars by splitting on the first colon. The descriptions were NOT contorted to satisfy the parser — the parser was made tolerant.
- **Task 4 — `discovering-processes` dispatched a `process-mapper` subagent with no agent file.** The phrasing matched the four sibling fan-out phases that each have a dedicated agent (`opportunity-typer`, `opportunity-scorer`, etc.), so the agent was clearly intended and simply never authored. Resolution (user-confirmed: "create the agent now"): authored `agents/process-mapper.md` mirroring `opportunity-typer`'s I/O discipline and refusal rules, specialized to Phase 4 per-round synthesis; agent count moved 13 → 14 (reflected in `test_agent_count` and the source-of-truth facts above).
