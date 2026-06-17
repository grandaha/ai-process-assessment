import json

from cockpit.state import read_state


def test_empty_engagement_only_phase1_available(engagement):
    root = engagement()  # no files
    snap = read_state(root)
    by_id = {p["id"]: p for p in snap["phases"]}
    assert by_id["1"]["status"] == "available"
    assert by_id["2"]["status"] == "blocked"
    assert by_id["2"]["blocked_reason"] == "Waiting on Scope (scope.md)"
    assert snap["progress"] == {"done": 0, "total": 12}


def test_done_phase_unlocks_next(engagement):
    root = engagement("scope.md")
    by_id = {p["id"]: p for p in read_state(root)["phases"]}
    assert by_id["1"]["status"] == "done"
    assert by_id["2"]["status"] == "available"
    assert by_id["3"]["status"] == "blocked"


def test_progress_counts_done_phases(engagement):
    root = engagement("scope.md", "context.md", "tech-inventory.md")
    assert read_state(root)["progress"] == {"done": 3, "total": 12}


def test_folder_index_counts_as_done(engagement):
    root = engagement("scope.md", "context.md", "tech-inventory.md",
                      "processes/_index.md")
    by_id = {p["id"]: p for p in read_state(root)["phases"]}
    assert by_id["4"]["status"] == "done"
    assert by_id["5"]["status"] == "available"


def test_snapshot_top_level_fields(engagement):
    root = engagement()
    snap = read_state(root)
    assert snap["engagement"] == "acme-engagement"
    assert snap["path"] == str(root)


OPPS_HEADER = (
    "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
    "|--------|---------|------|-------------|----------------|-----|------------|\n"
)


def test_grc_not_required_when_no_opportunities(engagement):
    root = engagement()
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "not-required"


def test_grc_not_required_when_all_green(engagement):
    body = "| OPP-001 | PROC-001 | RPA | Green | Green | Green | None |\n"
    root = engagement(**{"opportunities/_index.md": OPPS_HEADER + body})
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "not-required"


def test_grc_required_when_non_green_flag(engagement):
    body = (
        "| OPP-001 | PROC-001 | RPA | Green | Green | Green | None |\n"
        "| OPP-002 | PROC-002 | Agentic | Yellow | Green | Red | None |\n"
    )
    root = engagement(**{"opportunities/_index.md": OPPS_HEADER + body})
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "required"
    assert gates["grc"]["reason"] == "1 opportunity flagged Yellow/Red"


def test_grc_required_plural_when_multiple_flags(engagement):
    body = (
        "| OPP-001 | PROC-001 | RPA | Yellow | Green | Yellow | None |\n"
        "| OPP-002 | PROC-002 | Agentic | Yellow | Green | Red | None |\n"
    )
    root = engagement(**{"opportunities/_index.md": OPPS_HEADER + body})
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "required"
    assert gates["grc"]["reason"] == "2 opportunities flagged Yellow/Red"


def test_grc_done_when_grc_index_exists(engagement):
    body = "| OPP-002 | PROC-002 | Agentic | Yellow | Green | Red | None |\n"
    root = engagement(**{
        "opportunities/_index.md": OPPS_HEADER + body,
        "grc/_index.md": "cleared",
    })
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["grc"]["status"] == "done"


def test_deliverable_gate_done_when_evidence_log_exists(engagement):
    root = engagement("evidence-log.md")
    gates = {g["id"]: g for g in read_state(root)["gates"]}
    assert gates["deliverable"]["status"] == "done"
    assert read_state(engagement())  # absent -> not-run path covered below


def test_deliverable_gate_not_run_when_absent(engagement):
    gates = {g["id"]: g for g in read_state(engagement())["gates"]}
    assert gates["deliverable"]["status"] == "not-run"


def test_model_results_none_when_absent(engagement):
    snap = read_state(engagement())
    assert snap["model"]["results"] is None
    assert snap["model"]["inputs_present"] == {
        "baselines": False, "value": False, "scores": False,
        "initiatives": False, "costs": False,
    }


def test_model_results_parsed_when_present(engagement):
    results = {"investment": {"low": 100, "high": 200}}
    root = engagement(**{
        "model/results.json": json.dumps(results),
        "model/scores.json": "[]",
    })
    snap = read_state(root)
    assert snap["model"]["results"] == results
    assert snap["model"]["inputs_present"]["scores"] is True
    assert snap["model"]["inputs_present"]["costs"] is False


def test_model_results_none_when_corrupt(engagement):
    root = engagement(**{"model/results.json": "{not json"})
    assert read_state(root)["model"]["results"] is None
