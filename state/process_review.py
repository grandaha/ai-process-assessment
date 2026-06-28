# state/process_review.py — render per-process current-state owner-review .docx (#136).
# Pure transform + batch renderer. Stdlib only. No fabrication: every field is copied
# from the PROC file; internal analysis (color notes, conflicts, chain scan, challenge
# hypothesis) is deliberately excluded — see #136 spec.
import re

from state import docx

# Owner-facing single-line fields, in render order. (Conflicts/Chain scan/Challenge
# hypothesis are intentionally absent.)
_FIELDS = [("Trigger", "Trigger"),
           ("Actors", "Actors"),
           ("Decision points", "Decision points"),
           ("Exceptions", "Exceptions"),
           ("Upstream / downstream", "Upstream / downstream")]

def _field(md, label):
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else None

def _title(md):
    m = re.search(r"^##\s*(PROC-\d+)\s*[—-]\s*(.+)$", md, re.MULTILINE)
    return (m.group(1), m.group(2).strip()) if m else ("PROC-???", "Process")

def _steps(md):
    # numbered lines under "**Steps:**" up to the next blank line / bold label;
    # strip the internal "→ …" color note from each.
    block = re.search(r"\*\*Steps:\*\*\s*\n(.*?)(?:\n\s*\n|\n\*\*)", md, re.DOTALL)
    if not block:
        return []
    out = []
    for line in block.group(1).splitlines():
        m = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if m:
            out.append(m.group(1).split(" → ")[0].strip())   # drop color note
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

def build_blocks(proc_md):
    pid, name = _title(proc_md)
    blocks = [docx.heading(f"{pid} — {name}", 1),
              docx.paragraph("Please review the current-state capture of this process below "
                             "and confirm it is accurate, or note what should change.")]
    trigger = _field(proc_md, "Trigger")
    if trigger:
        blocks += [docx.heading("Trigger", 2), docx.paragraph(trigger)]
    steps = _steps(proc_md)
    if steps:
        blocks += [docx.heading("Steps", 2), docx.numbered_list(steps)]
    for label, _ in _FIELDS[1:]:                              # Actors..Upstream/downstream
        val = _field(proc_md, label)
        if val:
            blocks += [docx.heading(label, 2), docx.paragraph(val)]
    bl = _baselines(proc_md)
    if bl:
        blocks += [docx.heading("Baseline figures (for context)", 2),
                   docx.table(["Field", "Value"], bl)]
    blocks += [docx.heading("Sign-off", 2),
               docx.paragraph("Process owner: ______________________"),
               docx.paragraph("Outcome:  [ ] Confirmed    [ ] Changes requested"),
               docx.paragraph("Comments:")]
    return blocks

def _ready_processes(index_md):
    out = []
    for line in index_md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].startswith("PROC-") and cells[2].lower() == "ready":
            out.append(cells[0])
    return out

