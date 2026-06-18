"""The conducting-engagement skill must carry its load-bearing sections."""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "conducting-engagement" / "SKILL.md"

REQUIRED_HEADINGS = [
    "## Intake",
    "## The drive loop",
    "## Execution model",
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
