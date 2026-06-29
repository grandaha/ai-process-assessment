# tests/test_doc_rendering.py — renderer-output tests (#148). Run with python3.13.
import zipfile

from state import docx
from state import checkpoint_doc as cd


def _types(blocks):
    return [b["type"] for b in blocks]


def test_bullet_list_factory():
    b = docx.bullet_list(["a", "b"])
    assert b == {"type": "bullet_list", "items": ["a", "b"]}


def test_bullet_list_renders_with_bullet_glyph(tmp_path):
    out = tmp_path / "d.docx"
    docx.build_docx([docx.bullet_list(["first", "second"])], str(out))
    with zipfile.ZipFile(out) as z:
        body = z.read("word/document.xml").decode("utf-8")
    assert "• first" in body
    assert "• second" in body


def test_blocks_from_markdown_groups_consecutive_bullets():
    blocks = cd.blocks_from_markdown("- one\n- two\n- three")
    assert _types(blocks) == ["bullet_list"]
    assert blocks[0]["items"] == ["one", "two", "three"]


def test_blocks_from_markdown_groups_consecutive_numbers():
    blocks = cd.blocks_from_markdown("1. one\n2. two")
    assert _types(blocks) == ["numbered_list"]
    assert blocks[0]["items"] == ["one", "two"]


def test_blocks_from_markdown_strips_bold_in_list_items():
    blocks = cd.blocks_from_markdown("- a **bold** item")
    assert blocks[0]["items"] == ["a bold item"]


def test_blocks_from_markdown_preserves_interleaved_prose_and_table():
    md = "Intro line\n\n- b1\n- b2\n\n| H1 | H2 |\n|---|---|\n| x | y |"
    blocks = cd.blocks_from_markdown(md)
    t = _types(blocks)
    assert t == ["paragraph", "bullet_list", "table"]
    assert blocks[1]["items"] == ["b1", "b2"]
    assert blocks[2]["headers"] == ["H1", "H2"]


def test_blocks_from_markdown_switches_bullet_to_number_into_two_lists():
    blocks = cd.blocks_from_markdown("- a\n1. b")
    assert _types(blocks) == ["bullet_list", "numbered_list"]
