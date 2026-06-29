# state/process_review.py — render per-process current-state owner-review .docx (#136).
# Pure transform + batch renderer. Stdlib only. No fabrication: every field is copied
# from the PROC file; internal analysis (em-dash color notes, conflicts, chain scan,
# challenge hypothesis) is deliberately excluded — see #136 spec.
import re

from state import docx
from state.checkpoint_doc import blocks_from_markdown, _clean_inline


def _field_body(md, label):
    # Full body of a **Label:** field: inline text on the label line plus any following
    # lines, up to the next **Bold:** field, ### heading, or end of file.
    m = re.search(
        rf"^\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=^\*\*[^\n]+?:\*\*|^###\s|\Z)",
        md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else None


def _title(md):
    m = re.search(r"^##\s*(PROC-\d+)\s*[—-]\s*(.+)$", md, re.MULTILINE)
    return (m.group(1), m.group(2).strip()) if m else ("PROC-???", "Process")


def _steps(md):
    # numbered lines under "**Steps:**" up to the next blank line / bold label. Each step is
    # "action — **Rating** (rationale)"; return (action, note) so the renderer can show the
    # rating + rationale as an indented sub-bullet. The action may itself contain em-dashes,
    # so split on the bolded rating (" — **"), not the first dash.
    block = re.search(r"\*\*Steps:\*\*\s*\n(.*?)(?:\n\s*\n|\n\*\*)", md, re.DOTALL)
    if not block:
        return []
    out = []
    for line in block.group(1).splitlines():
        m = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if not m:
            continue
        text = m.group(1).strip()
        rating = re.match(r"^(.*?)\s+—\s+(\*\*.*)$", text)          # action — **Rating** (…)
        if rating:
            action, note = rating.group(1), rating.group(2)
        elif " → " in text:                                         # legacy arrow form
            action, note = text.split(" → ", 1)
        else:
            action, note = text, None
        out.append((_clean_inline(action).strip(),
                    _clean_inline(note).strip() if note else None))
    return out


def _baselines(md):
    # rows of the "### Baselines" table → [(Field, Value)] (drop Source/Confidence cols).
    sec = md.split("### Baselines", 1)
    if len(sec) < 2:
        return []
    rows = []
    for line in sec[1].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[0] != "Field" and not cells[0].startswith("---"):
            rows.append([cells[0], cells[1]])
    return rows


def _split_actors(body):
    # Split the Actors line into one item per participant on TOP-LEVEL semicolons only —
    # semicolons inside parentheses (e.g. "(execution, Step 6; checklist items, Step 3)")
    # belong to one actor and must not split it.
    out, depth, start = [], 0, 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            out.append(body[start:i])
            start = i + 1
    out.append(body[start:])
    return [_clean_inline(p.strip()) for p in out if p.strip()]

def build_blocks(proc_md):
    pid, name = _title(proc_md)
    blocks = [docx.heading(f"{pid} — {name}", 1),
              docx.paragraph("Please review the current-state capture of this process below "
                             "and confirm it is accurate, or note what should change.")]
    trigger = _field_body(proc_md, "Trigger")
    if trigger:
        blocks += [docx.heading("Trigger", 2)] + blocks_from_markdown(trigger)
    steps = _steps(proc_md)
    if steps:
        blocks.append(docx.heading("Steps", 2))
        for i, (action, note) in enumerate(steps, 1):
            blocks.append(docx.paragraph(f"{i}. {action}"))
            if note:
                blocks.append(docx.bullet_list([note], indent=720))   # rating + rationale, indented
    for label in ("Actors", "Decision points", "Exceptions", "Upstream / downstream"):
        body = _field_body(proc_md, label)
        if not body:
            continue
        # Actors is a single semicolon-separated line in the source — split it into a real
        # bullet list (verbatim text) instead of one run-on paragraph (#154).
        if label == "Actors" and not body.lstrip().startswith(("-", "*")):
            blocks += [docx.heading(label, 2), docx.bullet_list(_split_actors(body))]
        else:
            blocks += [docx.heading(label, 2)] + blocks_from_markdown(body)
    bl = _baselines(proc_md)
    if bl:
        blocks += [docx.heading("Baseline figures (for context)", 2),
                   docx.table(["Field", "Value"], bl)]
    blocks += [docx.heading("Sign-off", 2),
               docx.paragraph("Process owner: ______________________"),
               docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
               docx.paragraph("Comments:")]
    return blocks
