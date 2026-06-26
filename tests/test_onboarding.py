"""Conversational onboarding (Foundation #86 3.B) guards.

The front-door skill must offer the three first-contact paths, and its user-facing
greeting must stay free of methodology jargon (the "not the raw keystone dump" rule).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONDUCTOR = REPO / "skills" / "conducting-engagement" / "SKILL.md"
KEYSTONE = REPO / "skills" / "using-methodology" / "SKILL.md"

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


def test_keystone_routes_first_contact_to_conductor():
    """The keystone is loaded at session start; it must route the first turn to the
    Conductor so first contact (greeting + sample offer) actually fires. Without this
    wiring the greeting lives only inside conducting-engagement and never triggers on a
    cold/vague opener — the onboarding regression that hid the 'run a sample' path.
    """
    body = KEYSTONE.read_text(encoding="utf-8")
    assert "ai-process-assessment:conducting-engagement" in body, \
        "keystone must name the Conductor so first-contact (greeting + sample offer) fires"
    assert "front door" in body.lower(), \
        "keystone must designate the Conductor as the front door for cold/vague openers"
    # The Conductor must be the FIRST destination, not a passing mention that could be
    # demoted below the phase skills. Guard ordering: the Conductor is referenced before
    # the Phase 1 scoping skill in the "Chain to next skill" footer.
    chain = body[body.index("## Chain to next skill"):]
    conductor_at = chain.find("ai-process-assessment:conducting-engagement")
    scoping_at = chain.find("ai-process-assessment:scoping-engagement")
    assert conductor_at != -1 and scoping_at != -1 and conductor_at < scoping_at, \
        "keystone chain must route to the Conductor before Phase 1 scoping (front door first)"


def test_greeting_is_jargon_free():
    body = _body()
    start = body.find("<!-- greeting:start -->")
    end = body.find("<!-- greeting:end -->")
    assert start != -1 and end != -1 and end > start, \
        "greeting must be wrapped in <!-- greeting:start --> ... <!-- greeting:end -->"
    greeting = body[start:end]
    for token in GREETING_BLOCKLIST:
        assert token not in greeting, f"greeting leaks methodology jargon: {token!r}"


def test_first_contact_always_reflects_and_confirms():
    """First contact must ALWAYS reflect the user's intent back and confirm before
    advancing — and the legacy 'clear request -> skip the greeting and start' bypass that
    let a target-less opener skip straight in (the #125 non-determinism) must be gone."""
    body = _body()
    assert "skip the greeting and start" not in body, \
        "legacy skip-the-greeting bypass must be removed (caused inconsistent first contact, #125)"
    assert "reflect their intent back and confirm" in body.lower(), \
        "first contact must instruct the Conductor to reflect intent back and confirm every time"


def test_reflect_confirm_narration_is_jargon_free():
    """The canonical reflect-and-confirm line is the user-facing text; like every other
    narration block it must be fenced and free of methodology jargon."""
    body = _body()
    start = body.find("<!-- reflect-confirm:start -->")
    end = body.find("<!-- reflect-confirm:end -->")
    assert start != -1 and end != -1 and end > start, \
        "reflect-confirm narration must be wrapped in <!-- reflect-confirm:start --> ... :end -->"
    narration = body[start:end]
    for token in GREETING_BLOCKLIST:
        assert token not in narration, f"reflect-confirm narration leaks jargon: {token!r}"
