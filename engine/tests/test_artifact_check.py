# engine/tests/test_artifact_check.py
from pathlib import Path

from engine.run import build_results
from engine.artifact_check import check_manifest, verify

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"

def test_clean_manifest_verifies():
    results = build_results(FIXTURE)
    total = results["costs"]["OPP-001"]["total"]
    manifest = [{"value": total, "path": "costs.OPP-001.total"}]
    assert check_manifest(manifest, results) == []
    assert verify(manifest, results) is True

def test_rounding_tolerance():
    results = build_results(FIXTURE)
    total = results["costs"]["OPP-001"]["total"]
    manifest = [{"value": round(total) + 0.004, "path": "costs.OPP-001.total"}]
    assert verify(manifest, results) is True  # equal after 2dp rounding

def test_invented_number_rejected():
    results = build_results(FIXTURE)
    manifest = [{"value": 999999.0, "path": "costs.OPP-001.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "costs.OPP-001.total" in errs[0]
    assert verify(manifest, results) is False

def test_unknown_path_rejected():
    results = build_results(FIXTURE)
    manifest = [{"value": 1.0, "path": "costs.OPP-999.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "unknown path" in errs[0]

def test_pending_figure_rejected():
    results = build_results(FIXTURE)
    results["costs"]["OPP-001"]["total"] = "PENDING"
    manifest = [{"value": 0, "path": "costs.OPP-001.total"}]
    errs = check_manifest(manifest, results)
    assert len(errs) == 1 and "PENDING" in errs[0]

def test_range_endpoint_paths():
    results = build_results(FIXTURE)
    low = results["wave1_aggregate"]["investment"]["low"]
    manifest = [{"value": low, "path": "wave1_aggregate.investment.low"}]
    assert verify(manifest, results) is True
