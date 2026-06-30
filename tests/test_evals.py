from state.evals import tagger_consistency

_STABLE = """**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | sys |
| 2 | human-judgment | pm |
"""

_RUN_GREEN = """**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data | sys |
"""

_RUN_YELLOW = """**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, human-judgment | sys |
"""


def test_tagger_all_stable():
    res = tagger_consistency([_STABLE] * 5)
    assert res["agent"] == "step-capability-tagger"
    assert res["n_runs"] == 5
    assert res["unstable_step_count"] == 0
    assert all(s["color_unanimous"] for s in res["steps"])
    assert all(s["jaccard_mean"] == 1.0 for s in res["steps"])


def test_tagger_color_flip_is_unstable():
    res = tagger_consistency([_RUN_GREEN, _RUN_YELLOW, _RUN_GREEN])
    s1 = res["steps"][0]
    assert s1["step"] == 1
    assert s1["colors"] == ["Green", "Yellow", "Green"]
    assert s1["color_unanimous"] is False
    assert s1["unstable"] is True
    assert res["unstable_step_count"] == 1
    assert 0.0 < s1["jaccard_mean"] < 1.0
