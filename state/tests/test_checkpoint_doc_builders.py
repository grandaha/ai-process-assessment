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

def test_full_section_renders_prose_and_tables():
    md = """## 3. Data asset catalog
Polaris holds operational truth.

| Asset | Sensitivity |
|---|---|
| Deliverables | High |

Shadow spreadsheets exist.
## 4. Next
other
"""
    blocks = cd.full_section("Data assets", md, "3. Data asset catalog")
    assert blocks[0] == {"type": "heading", "text": "Data assets", "level": 2}
    types = [b["type"] for b in blocks]
    assert "table" in types and "paragraph" in types          # both rendered
    tbl = next(b for b in blocks if b["type"] == "table")
    assert tbl["headers"] == ["Asset", "Sensitivity"] and tbl["rows"] == [["Deliverables", "High"]]
    paras = [b["text"] for b in blocks if b["type"] == "paragraph"]
    assert "Polaris holds operational truth." in paras and "Shadow spreadsheets exist." in paras
    assert "4. Next" not in repr(blocks)                       # stops at next section

def test_prose_section_keeps_bold_leader():
    md = "## S\n**Important:** do it.\n## T\n"
    blocks = cd.prose_section("S", md, "S")
    assert any(b["text"] == "**Important:** do it." for b in blocks)   # bold not stripped
