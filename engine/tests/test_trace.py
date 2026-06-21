"""Tests for engine.trace — per-figure provenance output."""
import ast
import operator
import re
from pathlib import Path

from engine.run import build_results
from engine.trace import CONTRACT_VERSION, build_trace

FIXTURE = Path(__file__).parent / "fixtures" / "lattice" / "model"

# Leaf figure paths we expect provenance for, derived from results.json structure.
def _numeric_leaf_paths(results: dict) -> set[str]:
    paths = set()
    def walk(node, prefix):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(node, (int, float)) or node == "PENDING":
            paths.add(prefix)
    # Exclude label strings explicitly.
    walk(results, "")
    return {p for p in paths if not p.endswith("rom_label")}

# A figure's provenance is ONE node (a range figure covers both endpoints), so a
# results leaf is "covered" if descending the trace by the same path hits a node
# carrying a "formula" key at or before the leaf.
def _covered(trace: dict, path: str) -> bool:
    cur = trace
    for part in path.split("."):
        if isinstance(cur, dict) and "formula" in cur:
            return True
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return isinstance(cur, dict) and "formula" in cur

def test_contract_version_is_1_0():
    assert CONTRACT_VERSION == "1.0"
    assert build_trace(FIXTURE)["contract_version"] == "1.0"

def test_trace_covers_results():
    results = build_results(FIXTURE)
    trace = build_trace(FIXTURE)
    for path in _numeric_leaf_paths(results):
        assert _covered(trace, path), f"no provenance for {path}"

def test_trace_inputs_trace_to_model():
    trace = build_trace(FIXTURE)
    src_re = re.compile(r"^model/(\w+)\.json#([\w-]+)\.(\w+)$")
    def check(node):
        if isinstance(node, dict):
            if node.get("formula") == "passthrough":
                assert src_re.match(node["source"]), node["source"]
            for inp in node.get("inputs", []):
                src = inp["source"]
                if src.startswith("results:"):
                    continue  # intra-contract reference to an upstream computed figure
                assert src_re.match(src), src
            for v in node.values():
                check(v)
    check(trace)

# Evaluate the arithmetic embedded in each step string and assert it is sound.
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv}
def _eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval").body
    def ev(n):
        if isinstance(n, ast.BinOp):
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.Constant):
            return n.value
        raise ValueError(expr)
    return ev(tree)

def test_trace_steps_are_arithmetically_sound():
    # Only two-`=` steps of the form `name = <expr> = <number>` carry arithmetic;
    # single-value (`tech_cost = 80000`) and descriptive aggregate steps are skipped.
    trace = build_trace(FIXTURE)
    def check(node):
        if isinstance(node, dict):
            for step in node.get("steps", []):
                if step.count("=") < 2:
                    continue
                lhs, rhs = step.split("=", 1)[1].rsplit("=", 1)
                try:
                    expected = float(rhs)
                except ValueError:
                    continue
                expr = lhs.replace("×", "*").replace("÷", "/")  # normalize math glyphs
                assert abs(_eval(expr) - expected) < 0.01, step
            for v in node.values():
                check(v)
    check(trace)


import json, shutil
from engine.run import main

def test_main_writes_trace_json(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    main([str(eng)])
    trace = json.loads((eng / "model" / "trace.json").read_text())
    assert trace["contract_version"] == "1.0"
    assert "costs" in trace
