# state/capability.py — deterministic AI-capability tagging from factual step attributes (#186).
# Stdlib only. No fabrication: the color is COMPUTED from recorded attributes; no human authors a
# color. See docs/superpowers/specs/2026-06-29-attribute-based-capability-tagging-design.md.
import re

from state.checkpoint_doc import md_table

ENABLERS = {"structured-data", "rule-based", "templated", "ai-inference", "accuracy-bounded"}
BLOCKERS = {"human-judgment", "relationship", "external-dependency", "physical", "regulatory-signoff"}
VOCABULARY = ENABLERS | BLOCKERS

def compute_color(attributes):
    """Two-axis rule. Green = enabler & no blocker; Yellow = enabler & blocker; Red = blocker & no
    enabler. ai-inference contributes an implicit verification blocker unless accuracy-bounded is
    present. Raises ValueError on an invalid attribute set."""
    attrs = set(attributes)
    unknown = attrs - VOCABULARY
    if unknown:
        raise ValueError(f"unknown attribute(s): {sorted(unknown)}")
    if "accuracy-bounded" in attrs and "ai-inference" not in attrs:
        raise ValueError("accuracy-bounded requires ai-inference")
    has_enabler = bool(attrs & ENABLERS)
    has_blocker = bool(attrs & BLOCKERS) or ("ai-inference" in attrs and "accuracy-bounded" not in attrs)
    if not has_enabler and not has_blocker:
        raise ValueError("step has no enabler and no blocker")
    if has_enabler and not has_blocker:
        return "Green"
    if has_enabler and has_blocker:
        return "Yellow"
    return "Red"

def _section_body(md, label):
    # Body of a **Label:** section: inline text + following lines, to the next **Bold:** / ### / end.
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=^\*\*[^\n]+?:\*\*|^###\s|\Z)",
                  md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""

def _step_numbers(proc_md):
    body = _section_body(proc_md, "Steps")
    return [int(m.group(1)) for m in re.finditer(r"^\s*(\d+)\.\s+", body, re.MULTILINE)]

def parse_step_capability(proc_md):
    """{step_no: {"attributes": [...], "evidence": str}} from the **Step capability:** table."""
    header, rows = md_table(_section_body(proc_md, "Step capability"))
    out = {}
    for r in rows:
        if not r or not r[0].strip().isdigit():
            continue
        attrs = [a.strip() for a in r[1].split(",") if a.strip()] if len(r) > 1 else []
        evidence = r[2].strip() if len(r) > 2 else ""
        out[int(r[0].strip())] = {"attributes": attrs, "evidence": evidence}
    return out

def step_colors(proc_md):
    """{step_no: color} for every capability row (computed)."""
    return {s: compute_color(row["attributes"]) for s, row in parse_step_capability(proc_md).items()}

def compute_chains(colors_by_step):
    """Runs of >=2 consecutive Green steps as inclusive (start, end). A non-Green or missing step
    number breaks a run."""
    runs, run = [], []
    prev = None
    for s in sorted(colors_by_step):
        contiguous = prev is None or s == prev + 1
        if colors_by_step[s] == "Green" and contiguous:
            run.append(s)
        elif colors_by_step[s] == "Green":
            if len(run) >= 2:
                runs.append((run[0], run[-1]))
            run = [s]
        else:
            if len(run) >= 2:
                runs.append((run[0], run[-1]))
            run = []
        prev = s
    if len(run) >= 2:
        runs.append((run[0], run[-1]))
    return runs

def validate(proc_md):
    """Defect messages (empty = valid): unknown/invalid attributes, missing evidence, empty
    attribute set, accuracy-bounded misuse, and Steps<->capability bijection breaks."""
    defects = []
    steps = set(_step_numbers(proc_md))
    cap_rows = parse_step_capability(proc_md)
    cap_steps = set(cap_rows)
    for s in sorted(steps - cap_steps):
        defects.append(f"step {s}: no Step capability row")
    for s in sorted(cap_steps - steps):
        defects.append(f"Step capability row {s}: no matching step")
    for s in sorted(cap_steps & steps):
        row = cap_rows[s]
        if not row["attributes"]:
            defects.append(f"step {s}: no attributes")
            continue
        if not row["evidence"]:
            defects.append(f"step {s}: attribute has no evidence")
        try:
            compute_color(row["attributes"])
        except ValueError as e:
            defects.append(f"step {s}: {e}")
    return defects
