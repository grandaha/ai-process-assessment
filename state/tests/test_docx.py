import zipfile
from xml.etree import ElementTree as ET
from state import docx

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def _document_xml(path):
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        assert {"[Content_Types].xml", "_rels/.rels",
                "word/document.xml", "word/styles.xml"} <= names
        return z.read("word/document.xml").decode("utf-8")

def test_build_docx_valid_and_has_content(tmp_path):
    out = tmp_path / "x.docx"
    blocks = [
        docx.heading("Title", 1),
        docx.paragraph("Hello <world> & co"),   # must be XML-escaped
        docx.numbered_list(["first", "second"]),
        docx.table(["A", "B"], [["1", "2"]]),
    ]
    docx.build_docx(blocks, str(out))
    xml = _document_xml(str(out))
    ET.fromstring(xml)                       # parses = well-formed
    assert "Hello &lt;world&gt; &amp; co" in xml
    assert "1. first" in xml and "2. second" in xml
    assert xml.count("<w:tbl") >= 1
