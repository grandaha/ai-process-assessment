from pathlib import Path

from engine.run import build_results
from engine.trace import CONTRACT_VERSION, build_trace

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"
CONTRACT_DOC = REPO / "docs" / "data-contract.md"


def test_contract_doc_lists_all_results_keys():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    for key in build_results(FIXTURE):
        assert key in doc, f"data-contract.md omits results key: {key}"


def test_contract_doc_documents_version():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    assert CONTRACT_VERSION in doc
    assert "trace.json" in doc
    assert "contract_version" in doc
