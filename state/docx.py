# state/docx.py — minimal stdlib .docx (WordprocessingML) generator. No third-party deps.
# ponytail: only the block types the process review needs; add more when a caller needs them.
# ponytail: numbered_list renders as "N. text" paragraphs — avoids the fiddly numbering.xml part.
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

# The OSL dot-mark, vendored as a transparent PNG (Word can't embed the SVG). Sibling of
# state/ at the plugin root: <root>/assets/osl/logo-mark.png. See assets/osl/SOURCE.md.
_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "osl" / "logo-mark.png"

def _logo_png_bytes():
    # Returns the mark PNG bytes, or None if the asset is unavailable (footer then degrades to
    # wordmark-only — a missing logo must never crash deliverable generation).
    try:
        return _LOGO_PATH.read_bytes()
    except OSError:
        return None

def _content_types(has_logo):
    png = '<Default Extension="png" ContentType="image/png"/>' if has_logo else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + png +
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
            '</Types>')

_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

_DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''

_FOOTER_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                'Target="media/logo-mark.png"/></Relationships>')

# logo-mark.png is 300x306 px; render it ~20px tall in the footer. 1 px = 9525 EMU (96 dpi).
_LOGO_CY = 20 * 9525
_LOGO_CX = _LOGO_CY * 300 // 306

# Inline-picture run for the dot-mark (blip rId1 in the footer's rels).
_LOGO_DRAWING = (
    '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
    f'<wp:extent cx="{_LOGO_CX}" cy="{_LOGO_CY}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
    '<wp:docPr id="1" name="OSL mark"/>'
    '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
    '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    '<pic:pic><pic:nvPicPr><pic:cNvPr id="1" name="OSL mark"/><pic:cNvPicPr/></pic:nvPicPr>'
    '<pic:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
    f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{_LOGO_CX}" cy="{_LOGO_CY}"/></a:xfrm>'
    '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
    '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')

_WORDMARK = ('<w:r><w:rPr><w:color w:val="6B7280"/><w:sz w:val="18"/></w:rPr>'
             '<w:t xml:space="preserve"> one step labs</w:t></w:r>')

# Orange text dot — the brand cue when the logo image is unavailable.
_DOT = '<w:r><w:rPr><w:color w:val="E06030"/><w:sz w:val="18"/></w:rPr><w:t>●</w:t></w:r>'

_FTR_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
           'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
           'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
           'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"')

def _footer_xml(has_logo):
    # OSL-branded page footer: subtle top rule (#E5E7EB) + the dot-mark logo (or an orange text
    # dot when the image is unavailable) + the muted (#6B7280) "one step labs" wordmark.
    mark = _LOGO_DRAWING if has_logo else _DOT
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:ftr {_FTR_NS}>'
            '<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="6" w:space="6" w:color="E5E7EB"/></w:pBdr></w:pPr>'
            + mark + _WORDMARK + '</w:p></w:ftr>')

_STYLES = ('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DM Sans" w:hAnsi="DM Sans"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'''
 + ''.join(
     f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
     f'<w:pPr><w:outlineLvl w:val="{n-1}"/></w:pPr>'
     f'<w:rPr><w:b/><w:color w:val="111827"/><w:sz w:val="{sz}"/></w:rPr></w:style>'
     for n, sz in ((1, 42), (2, 30), (3, 24)))
 + '</w:styles>')

_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
       'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

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
    if t == "bullet_list":
        return ''.join(_p(f"• {item}") for item in b["items"])
    if t == "table":
        return _tbl(b["headers"], b["rows"])
    raise ValueError(f"unknown block type: {t}")

def build_docx(blocks, out_path):
    body = ''.join(_block(b) for b in blocks)
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document {_NS}><w:body>{body}'
                '<w:sectPr><w:footerReference w:type="default" r:id="rId2"/>'
                '<w:pgSz w:w="12240" w:h="15840"/></w:sectPr></w:body></w:document>')
    logo = _logo_png_bytes()
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _content_types(logo is not None))
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/styles.xml", _STYLES)
        z.writestr("word/footer1.xml", _footer_xml(logo is not None))
        if logo is not None:
            z.writestr("word/_rels/footer1.xml.rels", _FOOTER_RELS)
            z.writestr("word/media/logo-mark.png", logo)
        z.writestr("word/document.xml", document)
    return out_path

def heading(text, level=1): return {"type": "heading", "text": text, "level": level}
def paragraph(text): return {"type": "paragraph", "text": text}
def numbered_list(items): return {"type": "numbered_list", "items": list(items)}
def bullet_list(items): return {"type": "bullet_list", "items": list(items)}
def table(headers, rows): return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}
