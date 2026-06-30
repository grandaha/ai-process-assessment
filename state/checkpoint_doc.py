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

def _split_semicolons(text):
    # top-level (paren-aware) semicolons -> list items; a semicolon inside (...) stays put.
    out, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            out.append(text[start:i]); start = i + 1
    out.append(text[start:])
    return [p.strip() for p in out if p.strip()]

# abbreviations that end in "." but do not end a sentence — don't split right after these.
_ABBREV = ("e.g.", "i.e.", "etc.", "vs.", "Inc.", "Co.", "Ltd.", "No.", "approx.",
           "Dr.", "Mr.", "Ms.", "St.", "Fig.", "cf.")

def _sentences(text):
    # split prose on ". " before a capital; rejoin pieces wrongly split after a known
    # abbreviation. Leaves decimals (0.10) and parenthetical citations intact.
    out = []
    for p in re.split(r"(?<=\.)\s+(?=[A-Z])", text):
        if out and out[-1].endswith(_ABBREV):
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return [s.strip() for s in out if s.strip()]

def _readable(text):
    """Standing readability rule: prose that decomposes into a list renders as bullets, not a
    wall of text. Top-level semicolons -> bullets; else multi-sentence prose -> one bullet per
    sentence; else a single paragraph. `text` should already be _clean_inline'd."""
    text = text.strip()
    if not text:
        return []
    parts = _split_semicolons(text)
    if len(parts) > 1:
        return [docx.bullet_list(parts)]
    sents = _sentences(text)
    if len(sents) > 1:
        return [docx.bullet_list(sents)]
    return [docx.paragraph(text)]

def _grouped_line_blocks(lines):
    """Table-free markdown lines -> docx blocks. Consecutive `-`/`*` lines collapse into one
    bullet_list; consecutive `N.` lines into one numbered_list; a heading line becomes a heading;
    any other prose line goes through the readability rule (_readable). Empty lines are skipped
    without breaking an adjacent list."""
    out, bullets, nums = [], [], []
    def flush():
        if bullets:
            out.append(docx.bullet_list(bullets)); bullets.clear()
        if nums:
            out.append(docx.numbered_list(nums)); nums.clear()
    for s in lines:
        if not s:
            continue
        mb = re.match(r"^[-*]\s+(.*)$", s)
        if mb:
            if nums: flush()
            bullets.append(_clean_inline(mb.group(1).strip()))
            continue
        mn = re.match(r"^\d+\.\s+(.*)$", s)
        if mn:
            if bullets: flush()
            nums.append(_clean_inline(mn.group(1).strip()))
            continue
        flush()
        h = re.match(r"^(#{1,6})\s+(.*)$", s)
        if h:
            out.append(docx.heading(_clean_inline(h.group(2)).strip(), min(len(h.group(1)), 3)))
        else:
            out.extend(_readable(_clean_inline(s)))
    flush()
    return out

def prose_section(title, md, heading):
    body = md_section(md, heading)
    if not body:
        return []
    lines = [line.strip() for line in body.splitlines() if not line.strip().startswith("|")]
    return [docx.heading(title, 2)] + _grouped_line_blocks(lines)


def blocks_from_markdown(text):
    """Render a markdown body as docx blocks: contiguous pipe-table lines become a table;
    consecutive bullets/numbers become real lists; other non-empty lines become
    headings/paragraphs (markers stripped). Adjacent tables with no blank line between them
    render as separate tables."""
    out, tbl, lines = [], [], []
    def _cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]
    def _flush_tbl():
        if tbl:
            h, r = md_table("\n".join(tbl))
            if h:
                out.append(docx.table(h, r))
            tbl.clear()
    def _flush_lines():
        if lines:
            out.extend(_grouped_line_blocks(lines))
            lines.clear()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            _flush_lines()
            # a separator while one is already buffered = a new table started with no blank line:
            # the line just buffered is its header; flush the completed table first.
            if _is_separator(_cells(s)) and any(_is_separator(_cells(t)) for t in tbl):
                header = tbl.pop()
                _flush_tbl()
                tbl.append(header)
            tbl.append(s)
            continue
        _flush_tbl()
        lines.append(s)
    _flush_tbl()
    _flush_lines()
    return out

def full_section(title, md, heading):
    body = md_section(md, heading)
    return [docx.heading(title, 2)] + blocks_from_markdown(body) if body else []

def _labeled_sections(md):
    """[(label, body)] for each top-of-line `**Label:**` field, body running to the next such
    label or end — captures inline text plus any following block lines (lists, prose, tables)."""
    return [(m.group(1).strip(), m.group(2).strip()) for m in re.finditer(
        r"^\*\*([^\n*]+?):\*\*[ \t]*(.*?)(?=^\*\*[^\n*]+?:\*\*|\Z)",
        md, re.MULTILINE | re.DOTALL)]

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
    items: Callable        # None = single doc; else items(root)->[(item_id, item_md), ...]
    gate: bool
    output: str            # single-doc path, or "{id}" template for per-item checkpoints
    outcome: str           # outcome path, "{id}" template for per-item checkpoints
    build: Callable        # single: build(root)->blocks ; per-item: build(root, item_md)->blocks

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

def _process_items(root):
    # per-item source for process-validation: (PROC-id, brief md) for each Ready process.
    out = []
    for pid in _ready_processes(root):
        proc = Path(root) / "processes" / f"{pid}.md"
        if proc.exists():
            out.append((pid, proc.read_text(encoding="utf-8")))
    return out

def _opportunity_items(root):
    # per-item source for opportunities: (OPP-id, brief md) for each OPP-NNN.md.
    return [(f.stem, f.read_text(encoding="utf-8"))
            for f in sorted((Path(root) / "opportunities").glob("OPP-*.md"))]

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
        data = json.loads(_read(root, "model/baselines.json") or "[]")
    except ValueError:
        data = []
    # model/baselines.json is the engine INPUT shape: a list of per-process objects, each with a
    # process_id (#149). Index by process_id so we can look one up per ready process.
    by_pid = ({d["process_id"]: d for d in data if isinstance(d, dict) and "process_id" in d}
              if isinstance(data, list) else {})
    def _num(v): return "PENDING" if v is None or v == "" else v
    def _cycle(b):                                    # median + P90 in one cell
        m, p = b.get("cycle_time_median"), b.get("cycle_time_p90")
        if m is None and p is None:
            return "PENDING"
        return f"{m if m is not None else '—'} / {p if p is not None else '—'}"
    def _pct(v): return f"{round(v * 100)}%" if isinstance(v, (int, float)) else "PENDING"
    def _fte(v): return f"{v:.2f}" if isinstance(v, (int, float)) else "PENDING"
    rows = []
    for pid in _ready_processes(root):
        b = by_pid.get(pid, {})
        rows.append([pid, names.get(pid, ""), _num(b.get("volume")),
                     _cycle(b), _pct(b.get("error_rate")), _fte(b.get("fte"))])
    blocks = [docx.heading("As-Is Baselines — For Your Confirmation", 1)]
    blocks += note("Please confirm these baseline figures for each process, or note corrections.")
    blocks += table_section("Baselines",
        ["Process", "Name", "Volume", "Cycle time (median / P90)", "Error/exception", "FTE"], rows)
    blocks += signoff_block("Sponsor / process owners")
    return blocks

CHECKPOINTS = {
    "process-validation": Checkpoint(
        "process-validation", items=_process_items, gate=True,
        output="checkpoints/process-validation/{id}.docx",
        outcome="checkpoints/process-validation/CP-{id}-outcome.md",
        build=_build_process_validation),
    # "scope"/"baseline"/"portfolio" added in Tasks 3-5.
}

CHECKPOINTS["baseline"] = Checkpoint(
    "baseline", items=None, gate=False,
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
    "scope", items=None, gate=False,
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
    "tech-data", items=None, gate=False,
    output="checkpoints/checkpoint-tech-data.docx",
    outcome="checkpoints/CP-tech-data-outcome.md", build=_build_tech_data)

def _usecase_items(root):
    # per-item source for use-case-briefs: (UC-id, brief md) for each UC-NNN.md.
    return [(f.stem, f.read_text(encoding="utf-8"))
            for f in sorted((Path(root) / "usecase-briefs").glob("UC-*.md"))]

def _build_one_usecase_brief(root, uc_md):
    # One document per brief: title + every **Label:** section (Situation / Complication /
    # Resolution / Action / …) as a sub-heading + body via the shared renderer (so the
    # readability rule applies — Action / Risks become bullet lists). Whole brief is client-facing.
    m = re.search(r"^#+\s+(.+?)\s*$", uc_md, re.MULTILINE)
    blocks = [docx.heading(m.group(1).strip() if m else "Use-Case Brief", 1)]
    blocks += note("Confirm this use case reflects how the work really happens, or note corrections.")
    for label, body in _labeled_sections(uc_md):
        blocks.append(docx.heading(label, 2))
        blocks += blocks_from_markdown(body) if body else []
    blocks += signoff_block("Sponsor / process owner")
    return blocks

CHECKPOINTS["use-case-briefs"] = Checkpoint(
    "use-case-briefs", items=_usecase_items, gate=False,
    output="checkpoints/use-case-briefs/{id}.docx",
    outcome="checkpoints/use-case-briefs/CP-{id}-outcome.md", build=_build_one_usecase_brief)

def _confidence_cell(root, opp_id):
    # Reads the scorer confidence sidecar for one opportunity. "—" when evals were not run.
    p = Path(root) / "evals" / f"{opp_id}.evals.json"
    if not p.exists():
        return "—"
    d = json.loads(p.read_text(encoding="utf-8"))
    if not d.get("unstable"):
        return "Stable"
    parts = []
    lo, hi = d.get("composite_min"), d.get("composite_max")
    if lo is not None and hi is not None and lo != hi:
        parts.append(f"composite {lo}–{hi}")
    vals = d.get("bbp", {}).get("values", [])
    if vals and len(set(vals)) > 1:
        parts.append(" / ".join(f"{c}×{vals.count(c)}" for c in dict.fromkeys(vals)))
    return "⚠ Needs review — " + ("; ".join(parts) if parts else "dimension scores varied")


def _with_confidence(root, headers, rows):
    # Append a Confidence column keyed on the row's OPP-id (first cell). If no opportunity has
    # a sidecar (evals not run), leave the table unchanged — no empty column, no PENDING.
    if not headers:
        return headers, rows
    cells = [_confidence_cell(root, r[0]) if r else "—" for r in rows]
    if all(c == "—" for c in cells):
        return headers, rows
    return headers + ["Confidence"], [r + [c] for r, c in zip(rows, cells)]

def _build_portfolio(root):
    roadmap = _read(root, "roadmap.md")
    blocks = [docx.heading("Opportunity Portfolio & Roadmap — For Your Confirmation", 1)]
    blocks += prose_section("Sequencing", roadmap, "Sequencing thesis")
    wh, wr = md_table(roadmap, after_heading="Wave summary")
    blocks += table_section("Roadmap waves", wh, wr)
    sh, sr = md_table(_read(root, "scores/_index.md"))
    sh, sr = _with_confidence(str(root), sh, sr)
    blocks += table_section("Scored opportunities", sh, sr)
    blocks += note("Please confirm the prioritization and sequencing, or note changes.")
    blocks += signoff_block("Decision-maker / sponsor")
    return blocks

CHECKPOINTS["portfolio"] = Checkpoint(
    "portfolio", items=None, gate=False,
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
    "business-case", items=None, gate=False,
    output="checkpoints/checkpoint-business-case.docx",
    outcome="checkpoints/CP-business-case-outcome.md", build=_build_business_case)

# Per-opportunity fields to surface, in render order: (source label, client-facing heading).
# The assessor-derivation fields (Type source / Chain formation / Structural response) and the
# <!-- index --> comment are intentionally excluded — same owner-vs-analysis split as processes.
_OPP_FIELDS = [("Type", "Type"),
               ("Hypothesis", "What it is"),
               ("Value hypothesis", "Expected value"),
               ("GRC flag", "Governance & risk"),
               ("Data / system dependencies", "Systems & data")]

def _build_one_opportunity(root, opp_md):
    # One document per opportunity: title + the client-facing fields, each routed through the
    # readability rule (_readable). The assessor-derivation fields (Type source / Chain formation /
    # Structural response) and the <!-- index --> comment are excluded — owner-vs-analysis split.
    m = re.search(r"^#+\s+(.+?)\s*$", opp_md, re.MULTILINE)
    blocks = [docx.heading(m.group(1).strip() if m else "Opportunity", 1)]
    blocks += note("Confirm this opportunity reflects a real improvement and is correctly "
                   "characterized, or note what should change.")
    for src_label, disp in _OPP_FIELDS:
        v = md_field(opp_md, src_label)
        if v:
            blocks += [docx.heading(disp, 2)] + _readable(_clean_inline(v))
    blocks += signoff_block("Sponsor / decision-maker")
    return blocks

CHECKPOINTS["opportunities"] = Checkpoint(
    "opportunities", items=_opportunity_items, gate=False,
    output="checkpoints/opportunities/{id}.docx",
    outcome="checkpoints/opportunities/CP-{id}-outcome.md", build=_build_one_opportunity)

def render_checkpoint(engagement_dir, checkpoint_id):
    cp = CHECKPOINTS[checkpoint_id]
    root = Path(engagement_dir)
    written = []
    if cp.items is not None:
        for item_id, item_md in cp.items(root):
            out = root / cp.output.format(id=item_id)
            out.parent.mkdir(parents=True, exist_ok=True)
            docx.build_docx(cp.build(root, item_md), str(out))
            written.append(str(out))
            oc = root / cp.outcome.format(id=item_id)
            if not oc.exists():
                oc.write_text(f"# {item_id} — outcome\n\nOutcome: Pending\n", encoding="utf-8")
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
