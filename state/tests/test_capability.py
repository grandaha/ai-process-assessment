import pytest
from state import capability as cap

# --- compute_color: the two-axis rule ---
@pytest.mark.parametrize("attrs,expected", [
    (["structured-data", "rule-based"], "Green"),
    (["templated"], "Green"),
    (["ai-inference", "accuracy-bounded"], "Green"),
    (["structured-data", "human-judgment"], "Yellow"),
    (["ai-inference"], "Yellow"),                      # lone ai-inference -> implicit verify blocker
    (["ai-inference", "human-judgment"], "Yellow"),
    (["external-dependency"], "Red"),
    (["relationship", "regulatory-signoff"], "Red"),
])
def test_compute_color(attrs, expected):
    assert cap.compute_color(attrs) == expected

def test_compute_color_unknown_attribute_raises():
    with pytest.raises(ValueError):
        cap.compute_color(["structured-data", "magic"])

def test_compute_color_accuracy_bounded_requires_ai_inference():
    with pytest.raises(ValueError):
        cap.compute_color(["accuracy-bounded", "structured-data"])

def test_compute_color_empty_raises():
    with pytest.raises(ValueError):
        cap.compute_color([])

# --- parse_step_capability + step_colors ---
PROC = """## PROC-001 — Onboarding

**Steps:**
1. Re-keys client details into Teamwork
2. Waits for the client to provide materials
3. Reviews assets and decides whether to proceed

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | both systems API-available |
| 2 | external-dependency | operator: we wait on the client |
| 3 | structured-data, human-judgment | operator: I decide if there is enough |

**Baselines**

| Field | Value |
|---|---|
| Volume | 7/mo |
"""

def test_parse_step_capability():
    parsed = cap.parse_step_capability(PROC)
    assert set(parsed) == {1, 2, 3}
    assert parsed[1]["attributes"] == ["structured-data", "rule-based"]
    assert parsed[2]["evidence"] == "operator: we wait on the client"

def test_step_colors():
    assert cap.step_colors(PROC) == {1: "Green", 2: "Red", 3: "Yellow"}

def test_parse_ignores_unrelated_tables():
    # the Baselines table must not leak into the capability parse
    parsed = cap.parse_step_capability(PROC)
    assert "Volume" not in repr(parsed)

# --- compute_chains ---
def test_compute_chains_consecutive_green_runs():
    colors = {1: "Green", 2: "Green", 3: "Green", 4: "Red", 5: "Green", 6: "Green"}
    assert cap.compute_chains(colors) == [(1, 3), (5, 6)]

def test_compute_chains_single_green_is_not_a_chain():
    assert cap.compute_chains({1: "Green", 2: "Red", 3: "Green"}) == []

# --- validate ---
def test_validate_clean_proc_has_no_defects():
    assert cap.validate(PROC) == []

def test_validate_flags_missing_evidence():
    bad = PROC.replace("| 1 | structured-data, rule-based | both systems API-available |",
                       "| 1 | structured-data, rule-based |  |")
    defects = cap.validate(bad)
    assert any("evidence" in d.lower() and "1" in d for d in defects)

def test_validate_flags_step_capability_mismatch():
    # drop the capability row for step 3 -> bijection broken
    bad = PROC.replace("| 3 | structured-data, human-judgment | operator: I decide if there is enough |\n", "")
    defects = cap.validate(bad)
    assert any("3" in d for d in defects)

def test_validate_flags_unknown_attribute():
    bad = PROC.replace("structured-data, rule-based", "structured-data, magic")
    assert any("magic" in d for d in cap.validate(bad))
