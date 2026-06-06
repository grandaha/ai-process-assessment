"""Anti-regression guards. Each guard names, in a comment, the defect it defends.

This file grows in three tasks:
  Task 7 — data-arch (this section)
  Task 8 — #5 isolation and #8 ordering
"""
import re
from pathlib import Path

from methodology_model import REPO_ROOT

# --- Data-arch guard (defends: per-OPP data-architecture normalization, v2.1.0) ---
# After normalization, per-OPP artifacts live in the opportunities/, scores/, and
# grc/ folders. The monolithic files opportunities.md and scored-opportunities.md
# are retired and must not be referenced anywhere in skills/ or agents/.
#   - (?<![\w-])opportunities\.md  matches the retired monolith but NOT the
#     opportunities/ folder (no ".md") and NOT scored-opportunities.md (preceded by "-").
#   - scored-opportunities\.md     matches the other retired monolith.
RETIRED_FILE_PATTERNS = [
    re.compile(r"(?<![\w-])opportunities\.md"),
    re.compile(r"scored-opportunities\.md"),
]


def _methodology_markdown_files() -> list[Path]:
    return sorted(
        list((REPO_ROOT / "skills").rglob("SKILL.md"))
        + list((REPO_ROOT / "agents").glob("*.md"))
    )


def test_no_retired_monolithic_file_references():
    offenders = []
    for path in _methodology_markdown_files():
        text = path.read_text(encoding="utf-8")
        for pat in RETIRED_FILE_PATTERNS:
            if pat.search(text):
                rel = path.relative_to(REPO_ROOT)
                offenders.append(f"{rel} :: {pat.pattern}")
    assert not offenders, "retired-file references found:\n" + "\n".join(offenders)

# --- #5 isolation guard (defends: engagement-folder root-scatter, issue #5) ---
# Phase 1 (scoping-engagement) ESTABLISHES the Engagement folder field; every
# other output-producing phase skill must READ it back at Session Start, or its
# outputs scatter to the project root when the path is unset.
SELF_READ_MARKER = "extract the `Engagement folder:` field"
SELF_READ_EXEMPT = {"ai-process-assessment:scoping-engagement"}


def test_output_skills_carry_scope_self_read(methodology):
    phase_skill_ids = {p.skill_id for p in methodology.phases}
    for sid in sorted(phase_skill_ids):
        if sid in SELF_READ_EXEMPT:
            continue
        body = methodology.skills[sid].body
        assert SELF_READ_MARKER in body, \
            f"{sid} is missing the scope.md self-read marker (#5 guard)"


# --- #8 ordering guard (defends: Gate B running after Phase 10, issue #8) ---
# Gate B (deliverable-gate) runs BEFORE Phase 10. Three independent checks.

def _session_start_block(body: str) -> str:
    idx = body.find("## Session Start")
    assert idx != -1, "deliverable-gate has no Session Start section"
    rest = body[idx + len("## Session Start"):]
    nxt = re.search(r"\n##\s", rest)
    return rest[: nxt.start()] if nxt else rest


def test_phase10_gated_on_deliverable_gate(methodology):
    phase10 = next(p for p in methodology.phases if p.phase == "10")
    assert "deliverable-gate" in phase10.gate_condition, \
        "Phase 10 gate condition must cite deliverable-gate clearance"


def test_deliverable_gate_does_not_read_exec_summary(methodology):
    gate = methodology.skills["ai-process-assessment:deliverable-gate"]
    block = _session_start_block(gate.body)
    assert "executive-summary.md" not in block, \
        "deliverable-gate Session Start must not read executive-summary.md (it runs before Phase 10)"


def test_sample_sequences_gate_b_before_phase10(methodology):
    sample = methodology.skills["ai-process-assessment:running-sample-engagement"]
    rows = [l for l in sample.body.splitlines() if l.strip().startswith("|")]
    gate_b_idx = phase10_idx = None
    for i, row in enumerate(rows):
        first = row.strip().strip("|").split("|")[0].strip()
        if gate_b_idx is None and first.startswith("Gate B"):
            gate_b_idx = i
        if phase10_idx is None and first.startswith("10 "):
            phase10_idx = i
    assert gate_b_idx is not None, "sample table has no Gate B row"
    assert phase10_idx is not None, "sample table has no Phase 10 row"
    assert gate_b_idx < phase10_idx, \
        "sample sequences Gate B after Phase 10 (#8 regression)"
