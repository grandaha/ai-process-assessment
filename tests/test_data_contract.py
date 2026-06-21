import json
import shutil
from pathlib import Path

from engine.run import build_results, main
from engine.artifact_check import check_manifest
from engine.trace import CONTRACT_VERSION

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "engine" / "tests" / "fixtures" / "lattice" / "model"
CONTRACT_DOC = REPO / "docs" / "data-contract.md"

# A tracked fixture (the bundled sample-pso-delivery/ engagement is gitignored, so it
# is absent in CI — the end-to-end audit test must own its inputs + expected artifact).
SAMPLE_MODEL = REPO / "tests" / "fixtures" / "contract-sample" / "model"
SAMPLE_AUDIT = REPO / "tests" / "fixtures" / "contract-sample" / "cfo-audit.md"
SAMPLE_MANIFEST = REPO / "tests" / "fixtures" / "contract-sample" / "cfo-audit.manifest.json"


def test_contract_doc_lists_all_results_keys():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    for key in build_results(FIXTURE):
        assert key in doc, f"data-contract.md omits results key: {key}"


def test_contract_doc_documents_version():
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    assert CONTRACT_VERSION in doc
    assert "trace.json" in doc
    assert "contract_version" in doc


def test_sample_audit_verifies_against_freshly_built_contract(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(SAMPLE_MODEL, eng / "model")
    main([str(eng)])  # regenerate results.json + trace.json from the sample inputs
    results = json.loads((eng / "model" / "results.json").read_text())
    manifest = json.loads(SAMPLE_MANIFEST.read_text())
    assert check_manifest(manifest, results) == []


def test_sample_audit_prose_shows_each_manifest_figure():
    audit = SAMPLE_AUDIT.read_text(encoding="utf-8")
    manifest = json.loads(SAMPLE_MANIFEST.read_text())
    for entry in manifest:
        money = f"{round(float(entry['value'])):,}"  # e.g. 754000.0 -> "754,000"
        assert money in audit, f"audit prose missing figure {entry['path']} ({money})"
