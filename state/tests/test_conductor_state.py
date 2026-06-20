from state.conductor_state import (
    read_conductor, write_conductor, record_input_hashes, CONDUCTOR_FILE,
    reconcile_engine_root,
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


def test_engine_root_round_trips(tmp_path):
    write_conductor(tmp_path, {"engine_root": "/old/install"})
    assert read_conductor(tmp_path)["engine_root"] == "/old/install"


def test_reconcile_restamps_when_live_root_differs(tmp_path):
    write_conductor(tmp_path, {"register": "operator", "engine_root": "/old/install"})
    result = reconcile_engine_root(tmp_path, "/new/install")
    assert result == "/new/install"
    data = read_conductor(tmp_path)
    assert data["engine_root"] == "/new/install"
    assert data["register"] == "operator"  # other keys preserved


def test_reconcile_stamps_when_absent(tmp_path):
    write_conductor(tmp_path, {"register": "operator"})
    result = reconcile_engine_root(tmp_path, "/new/install")
    assert result == "/new/install"
    assert read_conductor(tmp_path)["engine_root"] == "/new/install"


def test_reconcile_no_write_when_matching(tmp_path):
    write_conductor(tmp_path, {"engine_root": "/same/install"})
    before = (tmp_path / ".conductor.md").read_text()
    result = reconcile_engine_root(tmp_path, "/same/install")
    after = (tmp_path / ".conductor.md").read_text()
    assert result == "/same/install"
    assert before == after  # idempotent: no rewrite when already correct
