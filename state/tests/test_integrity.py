from state.integrity import Issue, check_integrity


def test_clean_engagement_has_no_issues(engagement):
    root = engagement(**{
        "scope.md": "# Scope\nReal content.\n",
        "context.md": "# Context\nReal content.\n",
    })
    assert check_integrity(root) == []


def test_empty_non_index_output_is_surface(engagement):
    root = engagement(**{"scope.md": "   \n"})  # whitespace only
    issues = check_integrity(root)
    assert issues == [Issue("empty_output", "scope.md", "surface", issues[0].detail)]
    assert issues[0].detail  # non-empty plain-language message


def test_absent_output_is_not_flagged(engagement):
    root = engagement()  # nothing written
    assert check_integrity(root) == []


def test_bad_model_json_is_surface(engagement):
    root = engagement(**{"model/value.json": "{not valid json"})
    issues = check_integrity(root)
    kinds = {(i.kind, i.target, i.repair) for i in issues}
    assert ("bad_json", "model/value.json", "surface") in kinds


def test_partial_inputs_without_results_fire_results_missing(engagement):
    # Only baselines present (valid after Phase 4) and no results.json yet.
    root = engagement(**{"model/baselines.json": "[]"})
    issues = check_integrity(root)
    assert issues == [Issue("results_missing", "model/results.json", "auto",
                            issues[0].detail)]


def test_inputs_with_results_present_is_clean(engagement):
    root = engagement(**{
        "model/baselines.json": "[]",
        "model/results.json": "{}",
    })
    assert check_integrity(root) == []


def test_no_inputs_means_no_results_missing(engagement):
    root = engagement(**{"scope.md": "content"})
    assert check_integrity(root) == []
