from state.conductor_state import write_conductor
from state.staleness import hash_inputs
from state.status import status_view


def test_fresh_engagement_projection(engagement):
    root = engagement(**{"scope.md": "# Scope\ncontent\n"})
    v = status_view(root)
    assert v["engagement"] == root.name
    assert v["progress"]["done"] == 1 and v["progress"]["total"] == 12
    assert v["progress"]["percent"] == round(100 * 1 / 12)
    # Phase 1 done -> Phase 2 is the current step.
    assert v["current_step"]["id"] == "2"
    # interaction empty on a fresh engagement (no .conductor.md)
    assert v["interaction"]["register"] is None
    assert v["interaction"]["autonomy"] is None
    assert v["interaction"]["deferred_processes"] == []
    assert v["interaction"]["open_decisions"] == []
    # nothing needs attention
    assert v["attention"] == {"gates_due": [], "stale_inputs": [], "partial_state": []}
    assert v["complete"] is False


def test_blocked_phases_listed(engagement):
    root = engagement(**{"scope.md": "x"})
    v = status_view(root)
    blocked_ids = {b["id"] for b in v["blocked"]}
    assert "3" in blocked_ids  # Tech & Data waits on Context
    b3 = next(b for b in v["blocked"] if b["id"] == "3")
    assert b3["waiting_on"]  # carries a reason string


def test_interaction_surfaced_from_conductor(engagement):
    root = engagement(**{"scope.md": "x"})
    write_conductor(root, {
        "register": "operator",
        "autonomy": {"should_confirm": "batched"},
        "deferred_processes": ["PROC-009"],
        "open_decisions": ["scope-boundary"],
    })
    v = status_view(root)
    assert v["interaction"]["register"] == "operator"
    assert v["interaction"]["autonomy"] == "batched"
    assert v["interaction"]["deferred_processes"] == ["PROC-009"]
    assert v["interaction"]["open_decisions"] == ["scope-boundary"]


def test_complete_requires_all_phases_grc_and_gate_b(engagement):
    # Every phase output present (folder indexes carry a bare header, no data rows
    # -> no drift, GRC not-required), plus Gate B clearance.
    files = {
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n", "opportunities/_index.md": "| OPP-ID |\n",
        "scores/_index.md": "| OPP-ID |\n", "roadmap.md": "x",
        "usecase-briefs/_index.md": "| UC-NNN |\n", "cost-actuals.md": "x",
        "business-case.md": "x", "executive-summary.md": "x", "deliverable.html": "x",
        "evidence-log.md": "x",
    }
    root = engagement(**files)
    v = status_view(root)
    assert v["current_step"] is None
    assert v["progress"]["percent"] == 100
    assert v["attention"]["gates_due"] == []
    assert v["attention"]["partial_state"] == []
    assert v["complete"] is True


def test_done_except_gate_b_is_not_complete(engagement):
    files = {
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n", "opportunities/_index.md": "| OPP-ID |\n",
        "scores/_index.md": "| OPP-ID |\n", "roadmap.md": "x",
        "usecase-briefs/_index.md": "| UC-NNN |\n", "cost-actuals.md": "x",
        "business-case.md": "x", "executive-summary.md": "x", "deliverable.html": "x",
    }  # no evidence-log.md
    root = engagement(**files)
    v = status_view(root)
    assert v["current_step"] is None
    assert "deliverable" in v["attention"]["gates_due"]
    assert v["complete"] is False


def test_determinism(engagement):
    root = engagement(**{"scope.md": "x"})
    assert status_view(root) == status_view(root)


def test_attention_stale_inputs(engagement):
    # Record a hash for baselines, then change the file -> staleness fires.
    root = engagement(**{"model/baselines.json": '[{"process_id": "PROC-001"}]'})
    recorded = hash_inputs(root)              # current hash of baselines.json
    write_conductor(root, {"model_input_hashes": recorded})
    (root / "model" / "baselines.json").write_text('[{"process_id": "PROC-002"}]')
    v = status_view(root)
    assert "baselines" in v["attention"]["stale_inputs"]


def test_attention_partial_state_carries_detail(engagement):
    root = engagement(**{"scope.md": "   "})  # whitespace-only -> empty_output
    v = status_view(root)
    ps = v["attention"]["partial_state"]
    assert any(i["kind"] == "empty_output" and i["target"] == "scope.md"
               and i["repair"] == "surface" and i["detail"] for i in ps)


def test_attention_grc_gate_due(engagement):
    # An opportunities index with a Yellow GRC flag makes Gate A required. A valid
    # matching body keeps Chunk A integrity quiet so the assertion targets gates_due.
    idx = ("| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
           "| --- | --- | --- | --- | --- | --- | --- |\n"
           "| OPP-001 | PROC-001 | AIAugmentation | Green | Green | Yellow | addressing-root |\n")
    root = engagement(**{
        "scope.md": "x", "context.md": "x", "tech-inventory.md": "x",
        "processes/_index.md": "| PROC-ID |\n",
        "opportunities/_index.md": idx,
        "opportunities/OPP-001.md": ("## OPP-001 — X\n<!-- index: id=OPP-001 process=PROC-001 "
                                     "type=AIAugmentation feasibility=Green data=Green grc=Yellow "
                                     "struct=addressing-root -->\n\nbody\n"),
    })
    v = status_view(root)
    assert "grc" in v["attention"]["gates_due"]
