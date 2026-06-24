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
