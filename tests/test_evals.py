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


# scorer_consistency tests
from state.evals import scorer_consistency

_SCORE = """### Dimensional Scores
| Dimension | Score | Source citation |
|---|---|---|
| Value Potential | {v}/5 | x |
| Technical Feasibility | 3/5 | x |
| Data Readiness | 3/5 | x |
| Org Change Readiness | 3/5 | x |
| Strategic Alignment | 3/5 | x |
| Time to Value | 3/5 | x |

**Classification:** {b}
"""


def _run(v, b):
    return _SCORE.format(v=v, b=b)


def test_scorer_stable():
    res = scorer_consistency([_run(4, "Build")] * 5)
    assert res["agent"] == "opportunity-scorer"
    assert res["n_runs"] == 5
    assert res["unstable"] is False
    assert res["dimensions"]["Value Potential"]["spread"] == 0
    assert res["bbp"]["modal"] == "Build"
    assert res["bbp"]["modal_agreement"] == 1.0


def test_scorer_dimension_spread_unstable():
    res = scorer_consistency([_run(2, "Build"), _run(4, "Build"), _run(2, "Build")])
    assert res["dimensions"]["Value Potential"]["spread"] == 2
    assert res["unstable"] is True


def test_scorer_bbp_disagreement_unstable():
    res = scorer_consistency([_run(3, "Build"), _run(3, "Partner"), _run(3, "Build")])
    assert res["bbp"]["modal"] == "Build"
    assert res["bbp"]["modal_agreement"] < 1.0
    assert res["unstable"] is True


def test_scorer_drops_incomplete_runs():
    res = scorer_consistency([_run(4, "Build"), "no table here", _run(4, "Build")])
    assert res["n_runs"] == 2


# write_target and build_index tests
import json
from pathlib import Path

from state.evals import write_target

_TAG_TABLE = """**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data | s |
"""


def test_write_target_tagger(tmp_path):
    d = tmp_path / "_staging" / "evals" / "phase4" / "PROC-001"
    d.mkdir(parents=True)
    for k in (1, 2, 3):
        (d / f"run-{k}.md").write_text(_TAG_TABLE, encoding="utf-8")
    out = write_target(str(tmp_path), "phase4", "PROC-001")
    data = json.loads(Path(out).read_text(encoding="utf-8"))
    assert data["target"] == "PROC-001"
    assert data["phase"] == "phase4"
    assert data["agent"] == "step-capability-tagger"
    assert data["unstable_step_count"] == 0
    idx = (tmp_path / "evals" / "_index.md").read_text(encoding="utf-8")
    assert "PROC-001" in idx
    assert "Stable" in idx


def test_write_target_unknown_phase(tmp_path):
    d = tmp_path / "_staging" / "evals" / "phaseX" / "PROC-001"
    d.mkdir(parents=True)
    (d / "run-1.md").write_text(_TAG_TABLE, encoding="utf-8")
    try:
        write_target(str(tmp_path), "phaseX", "PROC-001")
        assert False, "expected ValueError"
    except ValueError:
        pass
