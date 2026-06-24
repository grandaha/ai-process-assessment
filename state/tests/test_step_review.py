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


from state.step_review import render_review, review_path
import pytest


def test_review_path_fragmented_and_single():
    assert review_path("5") == "reviews/05-opportunities.md"
    assert review_path("4") == "reviews/04-processes.md"
    assert review_path("7") == "roadmap.md"            # single-doc -> source
    with pytest.raises(ValueError):
        review_path("99")


def test_render_review_consolidates_index_and_items(engagement):
    root = engagement(**{
        "opportunities/_index.md": "| OPP-ID | Type |\n| --- | --- |\n| OPP-001 | Aug |\n",
        "opportunities/OPP-001.md": "## OPP-001 — Invoice\n\nFirst body.\n",
        "opportunities/OPP-002.md": "## OPP-002 — Status\n\nSecond body.\n",
    })
    out = render_review(root, "5")
    assert "# Review — Opportunities (opportunities/)" in out
    assert "## Summary" in out and "| OPP-ID | Type |" in out
    # both item bodies present, in id order
    assert out.index("OPP-001 — Invoice") < out.index("OPP-002 — Status")
    assert "First body." in out and "Second body." in out


def test_render_review_rejects_single_doc_phase(engagement):
    root = engagement(**{"roadmap.md": "x"})
    with pytest.raises(ValueError):
        render_review(root, "7")


def test_render_review_deterministic(engagement):
    root = engagement(**{
        "scores/_index.md": "| OPP-ID |\n",
        "scores/OPP-001.md": "## OPP-001 — S\n\nb\n",
    })
    assert render_review(root, "6") == render_review(root, "6")
