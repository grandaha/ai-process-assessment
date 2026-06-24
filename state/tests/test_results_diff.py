"""Unit tests for the deterministic results delta (state/results_diff.py)."""
from state.results_diff import MISSING, Change, diff_results


def test_identical_inputs_yield_no_changes():
    a = {"value": {"OPP-001": {"low": 700000, "high": 1050000}}}
    assert diff_results(a, dict(a)) == []


def test_nested_numeric_change_detected():
    before = {"value": {"OPP-001": {"low": 700000}}}
    after = {"value": {"OPP-001": {"low": 800000}}}
    assert diff_results(before, after) == [
        Change(path="value.OPP-001.low", before=700000, after=800000)
    ]


def test_added_key_uses_missing_sentinel_for_before():
    before = {"costs": {}}
    after = {"costs": {"OPP-002": 5000}}
    assert diff_results(before, after) == [
        Change(path="costs.OPP-002", before=MISSING, after=5000)
    ]


def test_removed_key_uses_missing_sentinel_for_after():
    before = {"costs": {"OPP-002": 5000}}
    after = {"costs": {}}
    assert diff_results(before, after) == [
        Change(path="costs.OPP-002", before=5000, after=MISSING)
    ]


def test_list_value_compared_as_leaf():
    # roadmap order is a list — a reorder is one whole-list change, not per-element.
    before = {"roadmap": ["OPP-001", "OPP-002"]}
    after = {"roadmap": ["OPP-002", "OPP-001"]}
    assert diff_results(before, after) == [
        Change(path="roadmap", before=["OPP-001", "OPP-002"], after=["OPP-002", "OPP-001"])
    ]


def test_result_is_sorted_by_path_regardless_of_insertion_order():
    before = {"b": 1, "a": 1}
    after = {"b": 2, "a": 2}
    # Insertion order is b, a — but output must be sorted by path: a, then b.
    assert [c.path for c in diff_results(before, after)] == ["a", "b"]
