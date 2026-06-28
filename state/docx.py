# state/docx.py — minimal stdlib .docx (WordprocessingML) generator. No third-party deps.
# ponytail: only the block types the process review needs; add more when a caller needs them.
# ponytail: numbered_list renders as "N. text" paragraphs — avoids the fiddly numbering.xml part.
import zipfile
from xml.sax.saxutils import escape

_CT = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

_DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

_STYLES = ('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DM Sans" w:hAnsi="DM Sans"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'''
 + ''.join(
     f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
     f'<w:pPr><w:outlineLvl w:val="{n-1}"/></w:pPr>'
     f'<w:rPr><w:b/><w:color w:val="1B75BC"/><w:sz w:val="{sz}"/></w:rPr></w:style>'
     for n, sz in ((1, 36), (2, 28), (3, 24)))
 + '</w:styles>')

_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

def _p(text, style=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

def _tbl(headers, rows):
    def _row(cells, bold=False):
        b = '<w:rPr><w:b/></w:rPr>' if bold else ''
        tcs = ''.join(
            f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>'
            f'<w:p><w:r>{b}<w:t xml:space="preserve">{escape(str(c))}</w:t></w:r></w:p></w:tc>'
            for c in cells)
        return f'<w:tr>{tcs}</w:tr>'
    borders = '<w:tblBorders>' + ''.join(
        f'<w:{s} w:val="single" w:sz="4" w:color="CCCCCC"/>'
        for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + '</w:tblBorders>'
    return (f'<w:tbl><w:tblPr>{borders}</w:tblPr>'
            + _row(headers, bold=True) + ''.join(_row(r) for r in rows) + '</w:tbl>')

def _block(b):
    t = b["type"]
    if t == "heading":
        return _p(b["text"], style=f'Heading{b.get("level", 1)}')
    if t == "paragraph":
        return _p(b["text"])
    if t == "numbered_list":
        return ''.join(_p(f"{i}. {item}") for i, item in enumerate(b["items"], 1))
    if t == "table":
        return _tbl(b["headers"], b["rows"])
    raise ValueError(f"unknown block type: {t}")

def build_docx(blocks, out_path):
    body = ''.join(_block(b) for b in blocks)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document {_NS}><w:body>{body}'
                '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr></w:body></w:document>')
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/document.xml", document)
    return out_path

def heading(text, level=1): return {"type": "heading", "text": text, "level": level}
def paragraph(text): return {"type": "paragraph", "text": text}
def numbered_list(items): return {"type": "numbered_list", "items": list(items)}
def table(headers, rows): return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}
