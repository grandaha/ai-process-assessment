"""Smoke tests (AC-2 clean-machine gate).

These tests verify that the plugin loads and the engine imports correctly on a
fresh checkout with only `pip install -r requirements.txt`. If any of these
fail, the install is broken for new users and the release is blocked.
"""
import importlib
import importlib.util


def test_model_loads(methodology):
    """Keystone Phase Map parses and is non-empty."""
    assert methodology.phases, "no phase rows parsed from the keystone Phase Map"
    assert methodology.skills, "no skills loaded"
    assert methodology.agents, "no agents loaded"
    assert methodology.convention_files, "no Engagement Folder Convention files parsed"


def test_engine_imports():
    """AC-2: engine package imports cleanly from a fresh install."""
    import engine
    import engine.model
    import engine.compute
    import engine.run
    import engine.workbook


def test_auto_merge_gate_imports():
    """AC-2: gate module imports without side effects."""
    import pathlib

    spec = importlib.util.spec_from_file_location(
        "auto_merge_gate",
        pathlib.Path(__file__).parent.parent / "scripts" / "auto_merge_gate.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.decide)
    assert callable(mod.parse_verdict)
    assert callable(mod.classify_paths)


def test_requirements_satisfiable():
    """AC-2: declared runtime dependencies are importable."""
    for pkg in ("openpyxl", "pytest"):
        assert importlib.util.find_spec(pkg) is not None, (
            f"Required package '{pkg}' not importable — "
            "run: pip install -r requirements.txt"
        )
