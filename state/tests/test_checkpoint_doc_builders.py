from state import checkpoint_doc as cd

MD = """**Client:** Lattice Consulting Group
# Title
## Sponsoring question
Which initiative should we fund?

Second para.
## Out-of-scope boundaries
| Excluded | Rationale |
|---|---|
| Sales | Different org. |
"""

def test_md_field():
    assert cd.md_field(MD, "Client") == "Lattice Consulting Group"
    assert cd.md_field(MD, "Nope") is None

def test_md_section():
    sec = cd.md_section(MD, "Sponsoring question")
    assert "Which initiative" in sec and "Second para." in sec
    assert "Out-of-scope" not in sec   # stops at next ##

def test_md_table():
    headers, rows = cd.md_table(MD, after_heading="Out-of-scope boundaries")
    assert headers == ["Excluded", "Rationale"]
    assert rows == [["Sales", "Different org."]]   # separator row dropped

def test_field_section_and_signoff():
    assert cd.field_section("Client", MD, "Client")[0]["type"] == "heading"
    assert any("Confirmed" in b.get("text","") for b in cd.signoff_block())

def test_prose_section_paragraphs():
    blocks = cd.prose_section("Sponsoring question", MD, "Sponsoring question")
    texts = [b["text"] for b in blocks if b["type"] == "paragraph"]
    assert "Which initiative should we fund?" in texts and "Second para." in texts
