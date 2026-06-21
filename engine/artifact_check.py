"""Verify an artifact's figure manifest against the engine's results.json.

A manifest entry is {"value": <number>, "path": "<dotted results path>"}.
Every figure an artifact presents must resolve to that exact contract value —
this is the mechanical no-new-arithmetic guard.
"""
from __future__ import annotations

_DP = 2  # money and scores both carry 2 decimal places


def _resolve(results: dict, path: str):
    cur = results
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def check_manifest(manifest, results) -> list[str]:
    errors: list[str] = []
    for entry in manifest:
        path, value = entry["path"], entry["value"]
        try:
            contract = _resolve(results, path)
        except KeyError:
            errors.append(f"unknown path: {path}")
            continue
        if contract == "PENDING":
            errors.append(f"figure is PENDING, must not appear in an artifact: {path}")
            continue
        if isinstance(contract, dict):
            errors.append(f"path resolves to a group, not a figure: {path}")
            continue
        if round(float(value), _DP) != round(float(contract), _DP):
            errors.append(f"value mismatch at {path}: {value} != {contract}")
    return errors


def verify(manifest, results) -> bool:
    return not check_manifest(manifest, results)
