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

def test_prose_section_strips_bold_leader():
    md = "## S\n**Important:** do it.\n## T\n"
    blocks = cd.prose_section("S", md, "S")
    assert any(b["text"] == "Important: do it." for b in blocks)   # bold markers stripped
    assert not any("**" in b.get("text", "") for b in blocks)

def test_blocks_from_markdown_strips_bold_and_converts_headings():
    md = "### Cost structure\n**Implementation:** $111k of labor.\n"
    blocks = cd.blocks_from_markdown(md)
    assert {"type": "heading", "text": "Cost structure", "level": 3} in blocks
    para = next(b for b in blocks if b["type"] == "paragraph")
    assert para["text"] == "Implementation: $111k of labor."
    assert "**" not in para["text"] and "###" not in repr(blocks)

def test_blocks_from_markdown_splits_adjacent_tables():
    # two pipe-tables with NO blank line between them must not merge
    md = ("| Cost | Est |\n|---|---|\n| Labor | $1 |\n"
          "| Value | Cat |\n|---|---|\n| Revenue | High |\n")
    tables = [b for b in cd.blocks_from_markdown(md) if b["type"] == "table"]
    assert len(tables) == 2
    assert tables[0]["headers"] == ["Cost", "Est"] and tables[0]["rows"] == [["Labor", "$1"]]
    assert tables[1]["headers"] == ["Value", "Cat"] and tables[1]["rows"] == [["Revenue", "High"]]

def test_clean_inline_preserves_underscores():
    # identifiers with underscores must survive untouched (no italic/underscore stripping)
    blocks = cd.blocks_from_markdown("See PROC_001 and model_baselines.json.\n")
    assert blocks[0]["text"] == "See PROC_001 and model_baselines.json."
