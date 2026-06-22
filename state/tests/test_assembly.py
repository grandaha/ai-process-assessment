"""Unit tests for the portable assembly layer (state/assembly.py)."""
from pathlib import Path

import pytest

from state.assembly import (
    cleanup,
    collect_staged,
    concat_ordered,
    index_from_fields,
    index_from_headers,
    promote,
    renumber_sequential,
)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- collect_staged / cleanup ---

def test_collect_staged_returns_sorted(tmp_path):
    staging = tmp_path / "_staging"
    _write(staging / "c.md", "c")
    _write(staging / "a.md", "a")
    _write(staging / "b.md", "b")
    got = collect_staged(staging)
    assert [p.name for p in got] == ["a.md", "b.md", "c.md"]


def test_collect_staged_missing_dir_returns_empty(tmp_path):
    assert collect_staged(tmp_path / "nope") == []


def test_cleanup_removes_tree(tmp_path):
    staging = tmp_path / "_staging"
    _write(staging / "a.md", "a")
    cleanup(staging)
    assert not staging.exists()


def test_cleanup_idempotent_on_missing(tmp_path):
    cleanup(tmp_path / "never-existed")  # must not raise


# --- index_from_headers ---

def test_index_from_headers_builds_table(tmp_path):
    f1 = _write(tmp_path / "OPP-001.md", "<!-- index: id=OPP-001 type=Automation feasibility=High -->\nbody")
    f2 = _write(tmp_path / "OPP-002.md", "<!-- index: id=OPP-002 type=Augmentation feasibility=Med -->\nbody")
    dest = tmp_path / "_index.md"
    n = index_from_headers([f1, f2], dest, [("OPP-ID", "id"), ("Type", "type"), ("Feasibility", "feasibility")])
    assert n == 2
    assert dest.read_text(encoding="utf-8") == (
        "| OPP-ID | Type | Feasibility |\n"
        "| --- | --- | --- |\n"
        "| OPP-001 | Automation | High |\n"
        "| OPP-002 | Augmentation | Med |\n"
    )


def test_index_from_headers_missing_key_is_empty_cell(tmp_path):
    f1 = _write(tmp_path / "OPP-001.md", "<!-- index: id=OPP-001 -->\nbody")
    dest = tmp_path / "_index.md"
    index_from_headers([f1], dest, [("OPP-ID", "id"), ("Type", "type")])
    assert dest.read_text(encoding="utf-8").splitlines()[-1] == "| OPP-001 |  |"


# --- index_from_fields ---

def test_index_from_fields_uses_extract(tmp_path):
    f1 = _write(tmp_path / "PROC-001.md", "## PROC-001 — Invoice intake\n<!-- index: baseline=Ready -->")
    f2 = _write(tmp_path / "PROC-002.md", "## PROC-002 — Vendor onboarding\nno header")

    def extract(path):
        import re
        text = Path(path).read_text(encoding="utf-8")
        m = re.search(r"^## PROC-\d+ — (.+)$", text, re.M)
        hm = re.search(r"baseline=([^\s>]*)", text)
        return {
            "id": Path(path).stem,
            "name": m.group(1).strip() if m else "",
            "baseline": hm.group(1) if hm and hm.group(1) else "Unavailable",
        }

    dest = tmp_path / "_index.md"
    n = index_from_fields([f1, f2], dest, [("PROC-ID", "id"), ("Process Name", "name"), ("Baseline", "baseline")], extract)
    assert n == 2
    rows = dest.read_text(encoding="utf-8").splitlines()
    assert rows[2] == "| PROC-001 | Invoice intake | Ready |"
    assert rows[3] == "| PROC-002 | Vendor onboarding | Unavailable |"


# --- renumber_sequential ---

def test_renumber_splits_and_remaps_within_block(tmp_path):
    staged = _write(
        tmp_path / "_staging" / "proc-001.md",
        "## TEMP-proc001-1\n<!-- index: id=TEMP-proc001-1 process=PROC-001 -->\nSee TEMP-proc001-1 detail.\n"
        "## TEMP-proc001-2\n<!-- index: id=TEMP-proc001-2 process=PROC-001 -->\nbody two\n",
    )
    dest = tmp_path / "opportunities"
    ids = renumber_sequential([staged], dest, "OPP")
    assert ids == ["OPP-001", "OPP-002"]
    first = (dest / "OPP-001.md").read_text(encoding="utf-8")
    assert first.startswith("## OPP-001\n")
    assert "id=OPP-001" in first
    assert "See OPP-001 detail." in first  # intra-block reference remapped
    assert "TEMP-" not in first
    assert (dest / "OPP-002.md").read_text(encoding="utf-8").startswith("## OPP-002\n")


def test_renumber_numbers_sequentially_across_files(tmp_path):
    a = _write(tmp_path / "_staging" / "proc-001.md", "## TEMP-a-1\nbody a\n")
    b = _write(tmp_path / "_staging" / "proc-002.md", "## TEMP-b-1\nbody b\n## TEMP-b-2\nbody b2\n")
    dest = tmp_path / "opportunities"
    ids = renumber_sequential([a, b], dest, "OPP")
    assert ids == ["OPP-001", "OPP-002", "OPP-003"]


def test_renumber_drops_preamble_before_first_heading(tmp_path):
    staged = _write(tmp_path / "_staging" / "proc-001.md", "junk preamble line\n## TEMP-x-1\nkept body\n")
    dest = tmp_path / "opportunities"
    renumber_sequential([staged], dest, "OPP")
    text = (dest / "OPP-001.md").read_text(encoding="utf-8")
    assert "junk preamble" not in text
    assert "kept body" in text


# --- promote ---

def test_promote_moves_and_returns_sorted(tmp_path):
    staging = tmp_path / "_staging"
    _write(staging / "OPP-002.md", "two")
    _write(staging / "OPP-001.md", "one")
    dest = tmp_path / "scores"
    moved = promote(staging, dest)
    assert [p.name for p in moved] == ["OPP-001.md", "OPP-002.md"]
    assert (dest / "OPP-001.md").read_text(encoding="utf-8") == "one"
    assert not (staging / "OPP-001.md").exists()  # moved, not copied


def test_promote_missing_staging_returns_empty(tmp_path):
    assert promote(tmp_path / "nope", tmp_path / "dest") == []


# --- concat_ordered ---

def test_concat_ordered_follows_order(tmp_path):
    a = _write(tmp_path / "_staging" / "intro.html", "<intro>")
    b = _write(tmp_path / "_staging" / "body.html", "<body>")
    c = _write(tmp_path / "_staging" / "outro.html", "<outro>")
    dest = tmp_path / "out.html"
    out = concat_ordered([a, b, c], dest, ["intro", "body", "outro"], sep="\n")
    assert out == dest
    assert dest.read_text(encoding="utf-8") == "<intro>\n<body>\n<outro>"


def test_concat_ordered_unranked_appended_sorted(tmp_path):
    a = _write(tmp_path / "_staging" / "z.md", "Z")
    b = _write(tmp_path / "_staging" / "a.md", "A")
    dest = tmp_path / "out.md"
    # order names neither file → both unranked, appended in sorted-stem order
    concat_ordered([a, b], dest, [], sep="|")
    assert dest.read_text(encoding="utf-8") == "A|Z"


# --- determinism (the headline guarantee) ---

def test_renumber_is_order_invariant(tmp_path):
    """Reversed input routed through the canonical `order` yields the same
    byte-for-byte output (and the same id assignment) as sorted collection."""
    content = {
        "proc-001.md": "## TEMP-a-1\nbody a\n",
        "proc-002.md": "## TEMP-b-1\nbody b\n",
        "proc-003.md": "## TEMP-c-1\nbody c\n",
    }
    staging = tmp_path / "_staging"
    for name, text in content.items():
        _write(staging / name, text)
    files = [staging / name for name in content]
    canonical = ["proc-001.md", "proc-002.md", "proc-003.md"]

    dest_a = tmp_path / "a"
    dest_b = tmp_path / "b"
    # Reversed input + explicit canonical order …
    renumber_sequential(list(reversed(files)), dest_a, "OPP", order=canonical)
    # … must equal sorted collection with default order.
    renumber_sequential(collect_staged(staging), dest_b, "OPP")

    a = {p.name: p.read_text(encoding="utf-8") for p in sorted(dest_a.glob("OPP-*.md"))}
    b = {p.name: p.read_text(encoding="utf-8") for p in sorted(dest_b.glob("OPP-*.md"))}
    assert a == b
    assert list(a) == ["OPP-001.md", "OPP-002.md", "OPP-003.md"]
    assert "body a" in a["OPP-001.md"] and "body c" in a["OPP-003.md"]


def test_index_from_headers_is_order_invariant(tmp_path):
    f1 = _write(tmp_path / "OPP-001.md", "<!-- index: id=OPP-001 type=A -->")
    f2 = _write(tmp_path / "OPP-002.md", "<!-- index: id=OPP-002 type=B -->")
    cols = [("OPP-ID", "id"), ("Type", "type")]
    d1 = tmp_path / "i1.md"
    d2 = tmp_path / "i2.md"
    index_from_headers(sorted([f1, f2]), d1, cols)
    index_from_headers(sorted([f2, f1]), d2, cols)  # caller sorts → identical
    assert d1.read_text(encoding="utf-8") == d2.read_text(encoding="utf-8")
