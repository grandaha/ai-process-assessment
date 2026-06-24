from state.step_review import Comment, extract_comments


def test_extract_explicit_anchor():
    text = "## OPP-001 — X\nbody\n\n> 💬 @OPP-003 this is augmentation\n"
    cs = extract_comments(text)
    assert cs == [Comment(anchor="OPP-003", body="@OPP-003 this is augmentation", line=4)]


def test_extract_positional_anchor():
    text = "## OPP-002 — Y\nbody\n\n> 💬 should be augmentation\n"
    cs = extract_comments(text)
    assert cs[0].anchor == "OPP-002"
    assert cs[0].body == "should be augmentation"


def test_extract_multiple_and_heading_switch():
    text = ("## OPP-001 — A\n> 💬 first\n"
            "## OPP-002 — B\n> 💬 second\n")
    cs = extract_comments(text)
    assert [(c.anchor, c.body) for c in cs] == [("OPP-001", "first"), ("OPP-002", "second")]


def test_extract_none_when_no_comments():
    assert extract_comments("## OPP-001 — A\njust content\n") == []


def test_extract_anchor_none_before_any_heading():
    cs = extract_comments("> 💬 orphan comment\n")
    assert cs[0].anchor is None
