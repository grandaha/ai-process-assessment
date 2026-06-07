"""Each phase's declared output token appears in the Engagement Folder
Convention list in the same keystone — the two lists cannot drift."""


def test_every_phase_output_is_in_convention_list(methodology):
    convention = set(methodology.convention_files)
    for p in methodology.phases:
        assert p.output_file in convention, (
            f"Phase {p.phase} output {p.output_file!r} is not in the "
            f"Engagement Folder Convention list: {sorted(convention)}"
        )


def test_convention_list_nonempty_and_includes_core_files(methodology):
    convention = set(methodology.convention_files)
    for required in ("scope.md", "opportunities/", "scores/", "grc/",
                     "evidence-log.md", "deliverable.html"):
        assert required in convention, f"convention list missing {required}"
