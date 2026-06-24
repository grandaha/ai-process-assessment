from state.integrity import Issue, check_integrity


def issues_by_kind(issues, kind):
    return next(i for i in issues if i.kind == kind)


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


def _opp(idx, proc="PROC-001"):
    return (f"## OPP-{idx} — Example\n"
            f"<!-- index: id=OPP-{idx} process={proc} type=Augmentation "
            f"feasibility=Green data=Green grc=Green struct=addressing-root -->\n\n"
            f"Body text.\n")

_OPP_INDEX_HEADER = ("| OPP-ID | Process |\n| --- | --- |\n")


def test_orphan_body_not_in_index_is_auto(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER,         # lists nothing
        "opportunities/OPP-002.md": _opp("002"),
    })
    issues = check_integrity(root)
    assert Issue("index_orphan_items", "opportunities/_index.md", "auto",
                 issues_by_kind(issues, "index_orphan_items").detail) in issues


def test_absent_index_with_bodies_is_auto(engagement):
    root = engagement(**{
        "opportunities/OPP-001.md": _opp("001"),
        "opportunities/OPP-002.md": _opp("002"),
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_orphan_items", "opportunities/_index.md", "auto") in kinds


def test_indexed_item_with_no_body_is_surface(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER + "| OPP-009 | PROC-001 |\n",
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_missing_item", "opportunities/_index.md", "surface") in kinds


def test_headerless_body_is_malformed_and_withholds_orphan(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER,
        "opportunities/OPP-002.md": _opp("002"),                  # orphan, valid header
        "opportunities/OPP-003.md": "## OPP-003 — No header\n\nbody\n",  # malformed
    })
    issues = check_integrity(root)
    kinds = {(i.kind, i.target) for i in issues}
    assert ("malformed_item", "opportunities/OPP-003.md") in kinds
    # orphan withheld for the whole folder because a malformed body is present
    assert not any(i.kind == "index_orphan_items" for i in issues)


def test_field_based_processes_skip_header_checks(engagement):
    # A valid Phase 4 body has NO id= header (index_from_fields), and is orphan-shaped.
    root = engagement(**{
        "processes/_index.md": "| PROC-ID | Process Name | Baseline |\n| --- | --- | --- |\n",
        "processes/PROC-001.md": "## PROC-001 — Staffing\n<!-- index: baseline=Ready -->\n\nbody\n",
    })
    issues = check_integrity(root)
    assert not any(i.kind == "malformed_item" for i in issues)
    assert not any(i.kind == "index_orphan_items" for i in issues)


def test_field_based_processes_still_flag_missing_item(engagement):
    root = engagement(**{
        "processes/_index.md": ("| PROC-ID | Process Name | Baseline |\n"
                                "| --- | --- | --- |\n| PROC-009 | Ghost | Ready |\n"),
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_missing_item", "processes/_index.md", "surface") in kinds


def test_usecase_briefs_handassembled_index_is_clean(engagement):
    # Phase 8's index is hand-assembled with markdown-link ids and a rich table
    # that index_from_headers cannot reproduce; it is header_based=False, so a
    # complete usecase-briefs folder must NOT report orphan/malformed drift
    # (a false positive there would trigger a destructive auto-rebuild).
    root = engagement(**{
        "usecase-briefs/_index.md": (
            "# Use-Case Briefs — Master Index\n\n"
            "| UC-NNN | OPP ref | Title |\n| --- | --- | --- |\n"
            "| [UC-001](UC-001.md) | OPP-001 | Status assembly |\n"
        ),
        "usecase-briefs/UC-001.md": (
            "# UC-001 — Status assembly\n"
            "<!-- index: id=UC-001 opp=OPP-001 -->\n\nBody.\n"
        ),
    })
    issues = check_integrity(root)
    assert not any(i.kind == "index_orphan_items" for i in issues)
    assert not any(i.kind == "malformed_item" for i in issues)


def test_issues_sorted_by_target_then_kind(engagement):
    root = engagement(**{
        "scope.md": "  ",                                         # empty_output (scope.md)
        "opportunities/_index.md": _OPP_INDEX_HEADER + "| OPP-009 | PROC-001 |\n",  # missing
    })
    issues = check_integrity(root)
    keys = [(i.target, i.kind) for i in issues]
    assert keys == sorted(keys)
