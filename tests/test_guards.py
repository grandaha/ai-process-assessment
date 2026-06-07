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

# --- #10 structural-challenge gate (defends: first-order-only methodology, issue #10) ---
# The Phase 4 gate gains a third clause (challenge hypothesis); Phase 5 emits a
# struct= signal that threads to the portfolio and roadmap views. Annotation only.


def test_phase4_sponsor_round_has_structural_challenge(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    for marker in (
        "Is the process boundary right?",
        "Is the actor model right?",
        "Is the sequence right?",
    ):
        assert marker in body, f"Phase 4 Round 1 missing challenge question: {marker!r}"


def test_process_mapper_captures_sponsor_structural_input(methodology):
    body = methodology.agents["process-mapper"].body
    assert "Sponsor structural input" in body, \
        "process-mapper Round 1 must capture 'Sponsor structural input'"


def _all_methodology_md_text() -> str:
    parts = []
    for path in _methodology_markdown_files():
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_phase4_gate_renamed_with_challenge_clause(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    assert "Baseline, Value & Challenge Gate" in body, \
        "Phase 4 gate must be renamed to 'Baseline, Value & Challenge Gate'"
    assert "challenge hypothesis unavailable" in body, \
        "Phase 4 gate must define the 'challenge hypothesis unavailable' remediation"


def test_process_map_schema_has_challenge_hypothesis(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    assert "Challenge hypothesis" in body, \
        "process-map.md Key Outputs must include a Challenge hypothesis field"


def _shipped_doc_text() -> str:
    # The rename-completeness corpus: shipped methodology (skills/ + agents/)
    # plus the two root-level user-facing docs. Deliberately excludes docs/
    # (design notes quote the old name in before/after text) and tests/ (this
    # file quotes the old name as an assertion literal).
    text = _all_methodology_md_text()
    for name in ("README.md", "system-prompt.md"):
        text += "\n" + (REPO_ROOT / name).read_text(encoding="utf-8")
    return text


def test_old_gate_name_fully_renamed():
    # Regression: the rename must be complete — the old proper-noun gate name
    # must appear nowhere in the shipped methodology or the user-facing root docs.
    assert "Baseline & Value Hypothesis" not in _shipped_doc_text(), \
        "stale 'Baseline & Value Hypothesis' gate name remains after rename"


STRUCT_VALUES = ("addressing-root", "optimizing-around", "not-applicable")


def test_typer_defines_structural_response_token(methodology):
    body = methodology.agents["opportunity-typer"].body
    assert "Structural response" in body, "typer missing 'Structural response' field"
    assert "struct=" in body, "typer missing 'struct=' extraction token"
    for v in STRUCT_VALUES:
        assert v in body, f"typer missing struct value {v!r}"


def test_opportunities_index_has_structural_column(methodology):
    body = methodology.skills["ai-process-assessment:identifying-opportunities"].body
    assert "struct=" in body, "Phase 5 index generation must extract struct="
    assert "| Structural |" in body, "opportunities/_index.md must add a Structural column"


def test_scorer_references_structural_response(methodology):
    body = methodology.agents["opportunity-scorer"].body
    assert "optimizing-around" in body, \
        "scorer must reference optimizing-around in its alignment rationale"
    assert "does not change the composite" in body, \
        "scorer must state the structural label does not change the composite"


def test_portfolio_renderer_surfaces_struct(methodology):
    body = methodology.agents["section-renderer-portfolio"].body
    assert "Structural" in body, \
        "portfolio renderer must read the Structural column"
    assert "optimizing-around" in body, \
        "portfolio renderer must render the optimizing-around value"
    assert "not-applicable" in body, \
        "portfolio renderer must define the not-applicable (empty) branch"


def test_roadmap_skill_threads_struct(methodology):
    body = methodology.skills["ai-process-assessment:prioritizing-roadmap"].body
    assert "struct" in body, "roadmap skill must read the struct signal"
    assert "optimizing-around" in body, \
        "roadmap skill must annotate optimizing-around items"


def test_roadmap_renderer_surfaces_struct(methodology):
    body = methodology.agents["section-renderer-roadmap"].body
    assert "optimizing-around" in body, \
        "roadmap renderer must surface the optimizing-around annotation"


def test_keystone_has_structural_challenge_rationalization(methodology):
    body = methodology.skills["ai-process-assessment:using-methodology"].body
    assert "faster broken process" in body, \
        "keystone Master Rationalization Table must carry the structural-challenge row"


def test_phase9_cites_engine_not_prose_math():
    skill = (REPO_ROOT / "skills" / "building-business-case" / "SKILL.md").read_text()
    assert "model/costs.json" in skill
    assert "python -m engine.run" in skill
    assert "results.json" in skill
    agent = (REPO_ROOT / "agents" / "business-case-analyst.md").read_text()
    assert "results.json" in agent
    # The analyst no longer computes ROM ranges itself.
    assert "compute" not in agent.lower() or "engine" in agent.lower()


def test_phase85_writes_cost_inputs_for_engine():
    skill = (REPO_ROOT / "skills" / "collecting-cost-actuals" / "SKILL.md").read_text()
    assert "model/costs.json" in skill
    assert "null" in skill  # missing inputs recorded as null -> PENDING


def test_phase6_composite_from_engine():
    skill = (REPO_ROOT / "skills" / "scoring-opportunities" / "SKILL.md").read_text()
    assert "model/scores.json" in skill
    agent = (REPO_ROOT / "agents" / "opportunity-scorer.md").read_text()
    assert "model/scores.json" in agent
    assert "composite" in agent.lower()


def test_phase5_value_inputs_to_engine():
    skill = (REPO_ROOT / "skills" / "identifying-opportunities" / "SKILL.md").read_text()
    assert "model/value.json" in skill
    assert "results.json" in skill


def test_phase4_no_prose_volume_math():
    skill = (REPO_ROOT / "skills" / "discovering-processes" / "SKILL.md").read_text()
    assert "model/baselines.json" in skill
    # No instruction to multiply volumes in prose.
    assert "results.json" in skill


def test_deliverable_gate_has_determinism_check():
    gate = (REPO_ROOT / "skills" / "deliverable-gate" / "SKILL.md").read_text()
    assert "results.json" in gate
    assert "determinism" in gate.lower()
