from state.staleness import hash_inputs, changed_inputs


def test_hash_inputs_only_includes_present_files(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    hashes = hash_inputs(root)
    assert set(hashes) == {"baselines"}
    assert len(hashes["baselines"]) == 64  # sha256 hex


def test_no_change_when_content_identical(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    assert changed_inputs(root, recorded) == []


def test_detects_changed_content(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    (root / "model" / "baselines.json").write_text('{"a": 2}')
    assert changed_inputs(root, recorded) == ["baselines"]


def test_new_input_counts_as_changed(engagement):
    root = engagement(**{"model/baselines.json": '{"a": 1}'})
    recorded = hash_inputs(root)
    (root / "model" / "value.json").write_text('{"v": 1}')
    assert changed_inputs(root, recorded) == ["value"]


def test_deleted_input_counts_as_changed(engagement):
    root = engagement(**{"model/scores.json": "[]"})
    recorded = hash_inputs(root)
    (root / "model" / "scores.json").unlink()
    assert changed_inputs(root, recorded) == ["scores"]
