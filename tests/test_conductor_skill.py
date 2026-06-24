"""The conducting-engagement skill must carry its load-bearing sections."""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "conducting-engagement" / "SKILL.md"

REQUIRED_HEADINGS = [
    "## Intake",
    "## The drive loop",
    "## Execution model",
    "## Parallel per-process fan-out",
    "## Touchpoint taxonomy",
    "## Elastic processes & convergence",
    "## Decision log",
    "## Staleness",
    "## Failure & rejection handling",
]


def test_skill_exists():
    assert SKILL.exists()


def test_skill_has_all_load_bearing_sections():
    text = SKILL.read_text()
    missing = [h for h in REQUIRED_HEADINGS if h not in text]
    assert not missing, f"conducting-engagement SKILL.md missing sections: {missing}"


def test_skill_names_both_parties_in_decision_log():
    text = SKILL.read_text()
    assert "proposed_by" in text and "decided_by" in text and "disposition" in text


def _section(text: str, header: str) -> str:
    start = text.find(header)
    assert start != -1, f"missing section: {header!r}"
    nxt = text.find("\n## ", start + len(header))
    return text[start: nxt if nxt != -1 else len(text)]


def test_conductor_owns_phase5_fanout():
    sec = _section(SKILL.read_text(), "## Parallel per-process fan-out")
    # Trigger: two or more processes with ready baselines.
    assert "≥2" in sec
    assert "Baseline = Ready" in sec
    # Conductor dispatches one subagent per process (not a single headless Phase 5).
    assert "one subagent per process" in sec
    # Merge reuses the portable assembly layer, in process order.
    assert "from state.assembly import" in sec
    assert "renumber_sequential" in sec
    # Cross-process chain-detection runs after the merge.
    assert "chain-detection" in sec
