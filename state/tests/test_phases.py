import dataclasses

import pytest

from state.phases import PHASES, GATES, Phase


def test_twelve_phases_in_methodology_order():
    ids = [p.id for p in PHASES]
    assert ids == ["1", "2", "3", "4", "5", "6", "7", "8", "8.5", "9", "10", "11"]


def test_first_phase_has_no_predecessor():
    assert PHASES[0].predecessor is None
    assert PHASES[0].output == "scope.md"


def test_each_later_phase_predecessor_is_prior_output():
    for prev, cur in zip(PHASES, PHASES[1:]):
        assert cur.predecessor == prev.output


def test_phase_5_outputs_opportunities_index():
    phase5 = next(p for p in PHASES if p.id == "5")
    assert phase5.output == "opportunities/_index.md"
    assert phase5.skill == "ai-process-assessment:identifying-opportunities"


def test_gates_present():
    gate_ids = [g.id for g in GATES]
    assert gate_ids == ["grc", "deliverable"]
    grc = GATES[0]
    assert grc.output == "grc/_index.md"
    assert GATES[1].output == "evidence-log.md"


def test_phase_is_frozen_dataclass():
    p = PHASES[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.id = "x"


def test_header_based_flag_marks_extraction_header_folders():
    from state.phases import PHASES, GATES
    by_id = {p.id: p for p in PHASES}
    # Phases whose _index.md is built from <!-- index: id=... --> headers.
    assert by_id["5"].header_based is True
    assert by_id["6"].header_based is True
    assert by_id["8"].header_based is True
    # Phase 4 (processes/) is field-based: index_from_fields, no id= header.
    assert by_id["4"].header_based is False
    # Non-folder phases default False.
    assert by_id["1"].header_based is False
    grc = next(g for g in GATES if g.id == "grc")
    deliverable = next(g for g in GATES if g.id == "deliverable")
    assert grc.header_based is True
    assert deliverable.header_based is False
