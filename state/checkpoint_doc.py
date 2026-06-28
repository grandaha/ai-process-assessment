# state/checkpoint_doc.py — deterministic, declarative checkpoint documents (#131).
# Stdlib only. No fabrication: every value is copied from a source file.
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from state import docx

# ---- markdown helpers ----
def md_field(md, label):
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else None

def md_section(md, heading):
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None

def _is_separator(cells):
    return all(set(c) <= set("-: ") and c for c in cells)

def md_table(md, after_heading=None):
    text = md if after_heading is None else (md_section(md, after_heading) or "")
    parsed = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if _is_separator(cells):
            continue
        parsed.append(cells)
    return (parsed[0], parsed[1:]) if parsed else ([], [])

# ---- section builders (each returns a list of docx blocks) ----
def field_section(title, md, label):
    v = md_field(md, label)
    return [docx.heading(title, 2), docx.paragraph(v)] if v else []

def prose_section(title, md, heading):
    body = md_section(md, heading)
    if not body:
        return []
    out = [docx.heading(title, 2)]
    for line in body.splitlines():
        s = line.strip().lstrip("-* ").strip()
        if s and not s.startswith("|"):     # skip table rows; keep prose + bullets as paragraphs
            out.append(docx.paragraph(s))
    return out

def table_section(title, headers, rows):
    return [docx.heading(title, 2), docx.table(headers, rows)] if rows else []

def note(text):
    return [docx.paragraph(text)]

def signoff_block(reviewer_label="Reviewer"):
    return [docx.heading("Sign-off", 2),
            docx.paragraph(f"{reviewer_label}: ______________________"),
            docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
            docx.paragraph("Comments:")]
