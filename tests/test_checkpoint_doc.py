# tests/test_checkpoint_doc.py
def test_scope_doc_includes_scope_excludes_internal_context(tmp_path):
    (tmp_path / "scope.md").write_text(
        "**Client:** Acme\n**Sponsor:** Dana\n"
        "## Sponsoring question\nWhich to fund?\n"
        "## In-scope domains\n1. Staffing\n2. Billing\n"
        "## Out-of-scope boundaries\n| Excluded | Rationale |\n|---|---|\n| Sales | other org |\n")
    (tmp_path / "context.md").write_text(
        "## Organization\nAcme does X.\n"
        "## Risk posture\nRisk-averse, burned by Project Swift.\n"
        "## AI / automation maturity\nLow.\n"
        "## Political landscape\nCFO distrusts the CDO.\n")
    from state import checkpoint_doc as cd
    cd.render_checkpoint(str(tmp_path), "scope")
    import zipfile
    with zipfile.ZipFile(tmp_path / "checkpoints" / "checkpoint-scope.docx") as z:
        xml = z.read("word/document.xml").decode().lower()
    assert "which to fund" in xml and "staffing" in xml and "sales" in xml   # scope content in
    for forbidden in ("risk posture", "project swift", "automation maturity", "political", "cfo distrusts"):
        assert forbidden not in xml      # internal context OUT
