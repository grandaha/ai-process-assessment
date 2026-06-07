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
