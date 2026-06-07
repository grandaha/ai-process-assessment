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
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        # Several skill/agent `description:` values legitimately contain an
        # unquoted colon (e.g. "...five constraints: dependency..." or
        # "...section: phase completion chips..."). Claude Code's own loader
        # accepts these; strict YAML rejects them. Do NOT "fix" the descriptions
        # to satisfy the parser — recover the simple scalar fields ourselves.
        # Frontmatter here is only single-line `name:`/`description:` scalars, so
        # splitting on the first colon yields the full value intact.
        result: dict = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                result[key.strip()] = val.strip()
        return result


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
    """First backticked file/folder token in a table cell (else first word).

    Returns "" for an empty cell so a malformed row surfaces as a clean
    test_every_phase_has_an_output_token failure rather than crashing the
    fixture for every test.
    """
    cell = cell.strip()
    m = _BACKTICK_RE.search(cell)
    if m:
        token = m.group(1)
    else:
        words = cell.split()
        token = words[0] if words else ""
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
