from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
DISC = (REPO / "skills" / "discovering-processes" / "SKILL.md").read_text()
MAPPER = (REPO / "agents" / "process-mapper.md").read_text()
TAGGER = (REPO / "agents" / "step-capability-tagger.md")
ATTRS = ["structured-data", "rule-based", "templated", "ai-inference", "accuracy-bounded",
         "human-judgment", "relationship", "external-dependency", "physical", "regulatory-signoff"]

def test_mapper_no_longer_assigns_colors():
    low = MAPPER.lower()
    assert "green / yellow / red" not in low and "green/yellow/red" not in low
    assert "ai capability per step" not in low      # the old per-step color instruction is gone

def test_tagger_agent_exists_and_lists_vocabulary():
    assert TAGGER.exists(), "agents/step-capability-tagger.md missing"
    text = TAGGER.read_text()
    for a in ATTRS:
        assert a in text, f"tagger missing attribute {a}"
    assert "evidence" in text.lower()               # evidence-cited
    # the two named residual-bias boundaries must have guidance
    assert "ai-inference" in text and "rule-based" in text and "human-judgment" in text

def test_discovering_processes_documents_two_passes_and_table():
    assert "Step capability" in DISC                # the new table section
    for a in ATTRS:
        assert a in DISC, f"discovering-processes missing attribute {a}"
    assert "step-capability-tagger" in DISC         # pass 2 wired
    # no hand-authored colors / hand chain scan remain as authoring instructions
    assert "Green / Yellow / Red" not in DISC and "Green/Yellow/Red" not in DISC

IDENT = (REPO / "skills" / "identifying-opportunities" / "SKILL.md").read_text()
TYPER = (REPO / "agents" / "opportunity-typer.md").read_text()
SCORING = (REPO / "skills" / "scoring-opportunities" / "SKILL.md").read_text()
SCORER = (REPO / "agents" / "opportunity-scorer.md").read_text()

def test_phase5_reads_computed_capability():
    assert "state/capability" in IDENT or "state.capability" in IDENT
    # chain value derived from the FTE baseline (replacing the deleted per-checkpoint prose)
    assert "FTE" in IDENT and "baseline" in IDENT.lower()

def test_phase5_typer_uses_computed_chains():
    assert "state/capability" in TYPER or "state.capability" in TYPER

def test_phase6_consumes_computed_chains():
    assert "state/capability" in SCORING or "state.capability" in SCORING
    assert "state/capability" in SCORER or "state.capability" in SCORER
