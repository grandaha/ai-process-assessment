"""Deterministic structural delta over two ``results.json`` snapshots.

Pure comparison — no arithmetic (every number was already produced by the
engine). Dicts are recursed into dotted paths; every other value (scalars and
lists) is compared as a single leaf, so a reordered list is reported as one
whole-list change. Output is sorted by path, so the same inputs always yield
the same change list regardless of dict insertion order. Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass


class _Missing:
    """Sentinel for a key absent on one side of the diff."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "MISSING"


MISSING = _Missing()


@dataclass(frozen=True)
class Change:
    path: str
    before: object
    after: object


def _walk(before, after, prefix, out):
    if isinstance(before, dict) and isinstance(after, dict):
        for key in set(before) | set(after):
            path = f"{prefix}.{key}" if prefix else str(key)
            _walk(before.get(key, MISSING), after.get(key, MISSING), path, out)
        return
    if before != after:
        out.append(Change(path=prefix, before=before, after=after))


def diff_results(before: dict, after: dict) -> list[Change]:
    """Return the changed leaves between two ``results.json`` structures,
    sorted by path. Added key → ``before is MISSING``; removed → ``after is
    MISSING``."""
    out: list[Change] = []
    _walk(before, after, "", out)
    return sorted(out, key=lambda c: c.path)
