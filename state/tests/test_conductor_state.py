from state.conductor_state import (
    read_conductor, write_conductor, record_input_hashes, CONDUCTOR_FILE,
)


def test_read_absent_returns_empty(engagement):
    assert read_conductor(engagement()) == {}


def test_write_then_read_roundtrips(engagement):
    root = engagement()
    data = {
        "register": "operator",
        "autonomy": {"should_confirm": "guided"},
        "methodology_version": "2.13.1",
        "deferred_processes": [],
    }
    write_conductor(root, data)
    assert (root / CONDUCTOR_FILE).exists()
    assert read_conductor(root) == data


def test_record_input_hashes_persists_current_model(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    write_conductor(root, {"register": "consultant"})
    updated = record_input_hashes(root)
    assert "baselines" in updated["model_input_hashes"]
    assert read_conductor(root)["model_input_hashes"] == updated["model_input_hashes"]
    assert read_conductor(root)["register"] == "consultant"  # preserved
