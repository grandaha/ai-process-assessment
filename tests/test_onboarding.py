"""Conversational onboarding (Foundation #86 3.B) guards.

The front-door skill must offer the three first-contact paths, and its user-facing
greeting must stay free of methodology jargon (the "not the raw keystone dump" rule).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONDUCTOR = REPO / "skills" / "conducting-engagement" / "SKILL.md"

# Tokens that mean "the user is being shown the methodology", which the greeting must avoid.
GREETING_BLOCKLIST = (
    [f"Phase {n}" for n in range(1, 12)]
    + ["GRC", "convergence", "deliverable-gate", "ai-process-assessment:"]
)


def _body() -> str:
    return CONDUCTOR.read_text(encoding="utf-8")


def test_conductor_has_first_contact_offer():
    body = _body()
    assert "## First contact" in body, "conducting-engagement is missing the First contact section"
    for label in ("Start an assessment", "Continue", "Run the sample"):
        assert label in body, f"first-contact offer missing the path label: {label!r}"
    assert "ai-process-assessment:running-sample-engagement" in body, \
        "first-contact flow must route the sample to running-sample-engagement"


def test_greeting_is_jargon_free():
    body = _body()
    start = body.find("<!-- greeting:start -->")
    end = body.find("<!-- greeting:end -->")
    assert start != -1 and end != -1 and end > start, \
        "greeting must be wrapped in <!-- greeting:start --> ... <!-- greeting:end -->"
    greeting = body[start:end]
    for token in GREETING_BLOCKLIST:
        assert token not in greeting, f"greeting leaks methodology jargon: {token!r}"
