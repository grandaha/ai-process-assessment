# state/checkpoint_doc.py — deterministic, declarative checkpoint documents (#131).
# Stdlib only. No fabrication: every value is copied from a source file.
import json
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

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

def _clean_inline(s):
    # strip **bold** markers (the only inline emphasis the methodology prose uses).
    # ponytail: leaves single * and _ alone — _ appears in identifiers (PROC_001, file_names).
    return _BOLD_RE.sub(r"\1", s)

def _md_line_block(s):
    """A single non-table markdown line -> a heading/paragraph block, or None if empty."""
    m = re.match(r"^(#{1,6})\s+(.*)$", s)
    if m:
        return docx.heading(_clean_inline(m.group(2)).strip(), min(len(m.group(1)), 3))
    s = re.sub(r"^[-*]\s+", "", s).strip()          # strip a leading bullet marker
    return docx.paragraph(_clean_inline(s)) if s else None

def prose_section(title, md, heading):
    body = md_section(md, heading)
    if not body:
        return []
    out = [docx.heading(title, 2)]
    for line in body.splitlines():
        if line.strip().startswith("|"):            # skip table rows
            continue
        b = _md_line_block(line.strip())
        if b:
            out.append(b)
    return out

def blocks_from_markdown(text):
    """Render a markdown body as docx blocks: contiguous pipe-table lines become a table,
    other non-empty lines become headings/paragraphs (markers stripped). Adjacent tables
    with no blank line between them render as separate tables."""
    out, tbl = [], []
    def _cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]
    def _flush():
        if tbl:
            h, r = md_table("\n".join(tbl))
            if h:
                out.append(docx.table(h, r))
            tbl.clear()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            # a separator while one is already buffered = a new table started with no blank line:
            # the line just buffered is its header; flush the completed table first.
            if _is_separator(_cells(s)) and any(_is_separator(_cells(t)) for t in tbl):
                header = tbl.pop()
                _flush()
                tbl.append(header)
            tbl.append(s)
            continue
        _flush()
        b = _md_line_block(s)
        if b:
            out.append(b)
    _flush()
    return out

def full_section(title, md, heading):
    body = md_section(md, heading)
    return [docx.heading(title, 2)] + blocks_from_markdown(body) if body else []

def _first_table(md):
    """Header+rows of the FIRST contiguous pipe-table block; ([], []) if none."""
    block = []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            block.append(s)
        elif block:
            break
    return md_table("\n".join(block))

def table_section(title, headers, rows):
    return [docx.heading(title, 2), docx.table(headers, rows)] if rows else []

def note(text):
    return [docx.paragraph(text)]

def signoff_block(reviewer_label="Reviewer"):
    return [docx.heading("Sign-off", 2),
            docx.paragraph(f"{reviewer_label}: ______________________"),
            docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
            docx.paragraph("Comments:")]

# ---- registry ----

@dataclass
class Checkpoint:
    id: str
    per_process: bool
    gate: bool
    output: str            # single-doc path, or "{pid}" template for per_process
    outcome: str           # outcome path, "{pid}" template for per_process
    build: Callable        # single: build(root)->blocks ; per_process: build(root, proc_md)->blocks

def _ready_processes(root):
    idx = Path(root) / "processes" / "_index.md"
    if not idx.exists():
        return []
    out = []
    for line in idx.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("PROC-") and cells[2].lower() == "ready":
            out.append(cells[0])
    return out

def _read(root, name):
    p = Path(root) / name
    return p.read_text(encoding="utf-8") if p.exists() else ""

def _require(root, name):
    md = _read(root, name)
    if not md.strip():
        raise FileNotFoundError(f"required source missing or empty: {name}")
    return md

# build functions for scope/baseline/portfolio land in Tasks 3-5.
def _build_process_validation(root, proc_md):
    from state.process_review import build_blocks
    return build_blocks(proc_md)

def _build_baseline(root):
    index = _read(root, "processes/_index.md")
    names = {r[0]: r[1] for r in md_table(index)[1] if r and r[0].startswith("PROC-")}
    try:
        data = json.loads(_read(root, "model/baselines.json") or "{}")
    except ValueError:
        data = {}
    rows = []
    for pid in _ready_processes(root):
        b = data.get(pid, {})
        def g(k): return b.get(k) or "PENDING"
        rows.append([pid, names.get(pid, ""), g("volume"), g("cycle_time"), g("error_rate"), g("fte")])
    blocks = [docx.heading("As-Is Baselines — For Your Confirmation", 1)]
    blocks += note("Please confirm these baseline figures for each process, or note corrections.")
    blocks += table_section("Baselines",
        ["Process", "Name", "Volume", "Cycle time", "Error/exception", "FTE"], rows)
    blocks += signoff_block("Sponsor / process owners")
    return blocks

CHECKPOINTS = {
    "process-validation": Checkpoint(
        "process-validation", per_process=True, gate=True,
        output="checkpoints/process-validation/{pid}.docx",
        outcome="checkpoints/process-validation/CP-{pid}-outcome.md",
        build=_build_process_validation),
    # "scope"/"baseline"/"portfolio" added in Tasks 3-5.
}

CHECKPOINTS["baseline"] = Checkpoint(
    "baseline", per_process=False, gate=False,
    output="checkpoints/checkpoint-baseline.docx",
    outcome="checkpoints/CP-baseline-outcome.md", build=_build_baseline)

# Context sections that must never reach the client doc (CP1 guard).
_SCOPE_EXCLUDE = ("risk posture", "ai / automation maturity", "ai/automation maturity",
                  "automation maturity", "political landscape")

def _build_scope(root):
    scope = _read(root, "scope.md")
    context = _read(root, "context.md")
    blocks = [docx.heading("Engagement Scope — For Your Confirmation", 1)]
    for label in ("Client", "Sponsor", "Decision-maker"):
        blocks += field_section(label, scope, label)
    blocks += prose_section("Sponsoring question", scope, "Sponsoring question")
    blocks += prose_section("In scope", scope, "In-scope domains")
    h, r = md_table(scope, after_heading="Out-of-scope boundaries")
    blocks += table_section("Out of scope", h, r)
    # context.md: include only non-internal sections (exclude the CP1-guarded ones).
    for m in re.finditer(r"^##\s+(.+?)\s*$", context, re.MULTILINE):
        title = m.group(1).strip()
        if title.strip().lower() in _SCOPE_EXCLUDE:
            continue
        blocks += prose_section(title, context, title)
    blocks += note("Please confirm the scope above is correct, or note what should change.")
    blocks += signoff_block("Sponsor / decision-maker")
    return blocks

CHECKPOINTS["scope"] = Checkpoint(
    "scope", per_process=False, gate=False,
    output="checkpoints/checkpoint-scope.docx",
    outcome="checkpoints/CP-scope-outcome.md", build=_build_scope)

def _build_tech_data(root):
    md = _require(root, "tech-inventory.md")
    blocks = [docx.heading("Technology & Data Inventory — For Your Confirmation", 1)]
    blocks += note("Please confirm your systems and data-sensitivity classifications are "
                   "captured correctly — these drive the downstream governance review.")
    # ponytail: tech-inventory.md is entirely client-facing — every section renders, no exclusion.
    for m in re.finditer(r"^##\s+(.+?)\s*$", md, re.MULTILINE):
        title = m.group(1).strip()
        blocks += full_section(title, md, title)
    blocks += signoff_block("IT lead / sponsor")
    return blocks

CHECKPOINTS["tech-data"] = Checkpoint(
    "tech-data", per_process=False, gate=False,
    output="checkpoints/checkpoint-tech-data.docx",
    outcome="checkpoints/CP-tech-data-outcome.md", build=_build_tech_data)

def _build_use_case_briefs(root):
    idx = _require(root, "usecase-briefs/_index.md")
    blocks = [docx.heading("Use-Case Briefs — For Your Review", 1)]
    blocks += note("These are the packaged use cases. Confirm each reflects how the work really "
                   "happens, or note corrections.")
    h, r = md_table(idx)                                  # the UC↔OPP mapping table
    blocks += table_section("Brief index", h, r)
    for uc in sorted((Path(root) / "usecase-briefs").glob("UC-*.md")):
        text = uc.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
        title = m.group(1).strip() if m else uc.stem
        th, tr = _first_table(text)                       # only the Field/Value summary; later tables intentionally dropped
        blocks += [docx.heading(title, 2)]
        if tr:
            blocks += [docx.table(th, tr)]   # table only — the UC title is the heading above
    blocks += signoff_block("Sponsor / process owners")
    return blocks

CHECKPOINTS["use-case-briefs"] = Checkpoint(
    "use-case-briefs", per_process=False, gate=False,
    output="checkpoints/checkpoint-use-case-briefs.docx",
    outcome="checkpoints/CP-use-case-briefs-outcome.md", build=_build_use_case_briefs)

def _build_portfolio(root):
    roadmap = _read(root, "roadmap.md")
    blocks = [docx.heading("Opportunity Portfolio & Roadmap — For Your Confirmation", 1)]
    blocks += prose_section("Sequencing", roadmap, "Sequencing thesis")
    wh, wr = md_table(roadmap, after_heading="Wave summary")
    blocks += table_section("Roadmap waves", wh, wr)
    sh, sr = md_table(_read(root, "scores/_index.md"))
    blocks += table_section("Scored opportunities", sh, sr)
    blocks += note("Please confirm the prioritization and sequencing, or note changes.")
    blocks += signoff_block("Decision-maker / sponsor")
    return blocks

CHECKPOINTS["portfolio"] = Checkpoint(
    "portfolio", per_process=False, gate=False,
    output="checkpoints/checkpoint-portfolio.docx",
    outcome="checkpoints/CP-portfolio-outcome.md", build=_build_portfolio)

def _build_business_case(root):
    md = _require(root, "business-case.md")
    blocks = [docx.heading("Business Case — For Your Review", 1)]
    blocks += note("Confirm the cost and value figures and the funding recommendation, or tell "
                   "us what to revisit.")
    for m in re.finditer(r"^##\s+(.+?)\s*$", md, re.MULTILINE):
        title = m.group(1).strip()
        blocks += full_section(title, md, title)
    blocks += signoff_block("Decision-maker / sponsor")
    return blocks

CHECKPOINTS["business-case"] = Checkpoint(
    "business-case", per_process=False, gate=False,
    output="checkpoints/checkpoint-business-case.docx",
    outcome="checkpoints/CP-business-case-outcome.md", build=_build_business_case)

def _build_opportunities(root):
    h, r = md_table(_require(root, "opportunities/_index.md"))
    blocks = [docx.heading("Opportunity Landscape — For Your Review", 1)]
    blocks += note("Here are the opportunities we identified. Tell us if any are missing or "
                   "mischaracterized before we score and prioritize them.")
    blocks += table_section("Opportunities", h, r)
    blocks += signoff_block("Sponsor / decision-maker")
    return blocks

CHECKPOINTS["opportunities"] = Checkpoint(
    "opportunities", per_process=False, gate=False,
    output="checkpoints/checkpoint-opportunities.docx",
    outcome="checkpoints/CP-opportunities-outcome.md", build=_build_opportunities)

def render_checkpoint(engagement_dir, checkpoint_id):
    cp = CHECKPOINTS[checkpoint_id]
    root = Path(engagement_dir)
    written = []
    if cp.per_process:
        for pid in _ready_processes(root):
            proc = root / "processes" / f"{pid}.md"
            if not proc.exists():
                continue
            out = root / cp.output.format(pid=pid)
            out.parent.mkdir(parents=True, exist_ok=True)
            docx.build_docx(cp.build(root, proc.read_text(encoding="utf-8")), str(out))
            written.append(str(out))
            oc = root / cp.outcome.format(pid=pid)
            if not oc.exists():
                oc.write_text(f"# {pid} — outcome\n\nOutcome: Pending\n", encoding="utf-8")
    else:
        out = root / cp.output
        out.parent.mkdir(parents=True, exist_ok=True)
        docx.build_docx(cp.build(root), str(out))
        written.append(str(out))
        oc = root / cp.outcome
        if not oc.exists():
            oc.write_text(f"# {checkpoint_id} — outcome\n\nOutcome: Pending\n", encoding="utf-8")
    return written

if __name__ == "__main__":
    print("\n".join(render_checkpoint(sys.argv[1], sys.argv[2])))
