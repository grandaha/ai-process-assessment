"""The conducting-engagement skill must carry its load-bearing sections."""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "conducting-engagement" / "SKILL.md"

REQUIRED_HEADINGS = [
    "## Intake",
    "## The drive loop",
    "## Execution model",
    "## Parallel per-process fan-out",
    "## Touchpoint taxonomy",
    "## Adaptive autonomy & holding the line",
    "## Elastic processes & convergence",
    "## Decision log",
    "## Status on demand",
    "## Resuming into a messy state",
    "## Staleness",
    "## Edit & interruption splicing",
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
    # Conductor's merge block carries the canonical index column tuple.
    assert "('OPP-ID', 'id')" in sec
    # Cross-process chain-detection runs after the merge.
    assert "chain-detection" in sec


def test_conductor_fanout_degradation_and_failure():
    sec = _section(SKILL.read_text(), "## Parallel per-process fan-out")
    # Cross-surface degradation: same per-process work, run sequentially, identical result.
    assert "Degradation" in sec
    assert "sequentially" in sec
    # Per-process failure: re-dispatch only the failed process; merge waits for the full set.
    assert "re-dispatch only that process" in sec
    assert "do not merge until the full set is staged" in sec


def test_fanout_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- fanout-narration:start -->")
    end = text.find("<!-- fanout-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "fan-out narration must be wrapped in <!-- fanout-narration:start --> ... :end -->"
    narration = text[start:end]
    forbidden = ["subagent", "OPP-", "_staging", "renumber"] + [f"Phase {n}" for n in range(1, 12)]
    for token in forbidden:
        assert token not in narration, f"narration leaks methodology jargon: {token!r}"
    # It states the 'whole board at once' promise in plain language.
    assert "together" in narration.lower()


def test_conductor_edit_splicing_intake_and_routes():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # Universal plain-language intake, handled at the drive-loop boundary.
    assert "plain language" in sec
    assert "drive-loop boundary" in sec
    # Three routes.
    assert "model/*.json" in sec          # numeric route
    assert "re-run the owning phase" in sec  # structural route
    assert "single-process mode" in sec      # structural re-type reuses Chunk A
    assert "re-open that must-ask" in sec     # human-only route
    # Delta report hookup to the Task 1 helper.
    assert "state.results_diff" in sec
    assert "diff_results" in sec


def test_conductor_edit_confirm_gate():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # Act-then-show default.
    assert "act-then-show" in sec
    # The two confirm-first exceptions.
    assert "ambiguous" in sec
    assert "must-ask" in sec
    # Downstream re-surfacing defers to the existing contract; no new batching here.
    assert "touchpoint taxonomy" in sec
    assert "autonomy preset" in sec
    assert "Chunk C" in sec


def test_conductor_edit_logs_both_parties():
    sec = _section(SKILL.read_text(), "## Edit & interruption splicing")
    # AI-draft correction mapping.
    assert "human-overrode" in sec
    assert "overridden→" in sec
    # Fresh user-fact mapping.
    assert "human-ratified" in sec
    assert "edited" in sec
    # Append-only, never overwrite the AI proposal.
    assert "append-only" in sec


def test_conductor_edit_delta_narration_is_jargon_free():
    text = SKILL.read_text()
    start = text.find("<!-- edit-delta-narration:start -->")
    end = text.find("<!-- edit-delta-narration:end -->")
    assert start != -1 and end != -1 and end > start, \
        "delta narration must be wrapped in <!-- edit-delta-narration:start --> ... :end -->"
    narration = text[start:end]
    forbidden = ["OPP-", "model/", "_staging", "renumber"] + [f"Phase {n}" for n in range(1, 12)]
    for token in forbidden:
        assert token not in narration, f"delta narration leaks jargon: {token!r}"


def test_conductor_adaptive_autonomy():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    # Plain-language interface, any time.
    assert "plain language" in sec
    # Interpreted into per-class behavior and persisted (conductor-maintained).
    assert "per-class" in sec
    assert "per_class" in sec
    assert "write_conductor" in sec
    assert "never sees or edits" in sec


def test_conductor_should_confirm_batching():
    text = SKILL.read_text()
    sec = _section(text, "## Adaptive autonomy & holding the line")
    assert "reviewable digest" in sec
    assert "silently skipped" in sec
    # The taxonomy placeholder is replaced by the implemented behavior.
    assert "Autonomous batching is Slice 2" not in text


def test_conductor_must_ask_invariant():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    assert "must-ask never collapses" in sec
    assert "any pressure" in sec
    assert "never** relax a must-ask" in sec or "never relax a must-ask" in sec
    assert "Touchpoint taxonomy" in sec
    # Validate that the canonical taxonomy floor carries the trust-critical categories.
    text = SKILL.read_text()
    for item in ("scope boundaries", "decision-maker", "cost actuals", "gate dispositions", "Build/Buy/Partner"):
        assert item in text, f"must-ask taxonomy floor missing: {item!r}"


def test_conductor_holding_the_line():
    sec = _section(SKILL.read_text(), "## Adaptive autonomy & holding the line")
    assert "firm and teaching" in sec
    assert "never refuse-and-quote" in sec
    assert "shortest honest path" in sec


def test_conductor_register_drives_teaching():
    text = SKILL.read_text()
    assert "Register voice" in text
    assert "teach as you go" in text
    assert "terse and domain-fluent" in text


def test_conductor_resume_recovery_section():
    sec = _section(SKILL.read_text(), "## Resuming into a messy state")
    # Runs the integrity checker by absolute path.
    assert "state/integrity.py" in sec
    # Distinguishes auto-repair from must-surface.
    assert "auto" in sec and "surface" in sec
    # Auto path reuses the existing assembly primitive, not a re-implementation.
    assert "index_from_headers" in sec
    # Surface path is a batched must-ask that does not advance.
    assert "must-ask" in sec
    # Jargon-free narration block is present and fenced.
    assert "<!-- resume-recovery-narration:start -->" in sec
    assert "<!-- resume-recovery-narration:end -->" in sec


def test_conductor_resume_recovery_runs_before_staleness():
    text = SKILL.read_text()
    # The drive loop references the recovery step before the staleness step.
    assert "Resuming into a messy state" in _section(text, "## The drive loop")


def test_conductor_status_on_demand_section():
    sec = _section(SKILL.read_text(), "## Status on demand")
    # Reads the status projection by absolute path.
    assert "state/status.py" in sec
    # Read-only: surfacing status never advances the drive loop.
    assert "read-only" in sec.lower() or "does not advance" in sec.lower()
    # Jargon-free narration block is present and fenced.
    assert "<!-- status-narration:start -->" in sec
    assert "<!-- status-narration:end -->" in sec
