# Portable Assembly Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the inline-shell assemblers in the four fan-out phases that use them (Phase 4, Phase 5, Phase 6, Gate A) with calls to one shared, tested, stdlib-only `state/assembly.py` toolkit — making assembly portable to Python-only surfaces (Claude.ai) and deterministic.

**Architecture:** A new `state/assembly.py` module exposes seven small composable primitives (`collect_staged`, `renumber_sequential`, `index_from_headers`, `index_from_fields`, `promote`, `concat_ordered`, `cleanup`). Each fan-out skill replaces its `awk`/`mv`/`for f in` block with a one-line `PYTHONPATH="<engine_root>" python3 -c "from state.assembly import …"` call — the same invocation pattern the skills already use for `state.conductor_state`. Migrations are behavior-preserving: same canonical files, same `_index.md` columns, same ids. `concat_ordered` is built and tested now but wired to no phase (it serves the deferred main-context follow-up).

**Tech Stack:** Python 3 (standard library only — `pathlib`, `re`, `shutil`), pytest. Skill bodies are markdown invoking Python via `python3 -c`.

**Spec:** `docs/superpowers/specs/2026-06-22-portable-assembly-layer-design.md` (#100, under epic #85).

## Global Constraints

- **Stdlib only.** `state/assembly.py` imports nothing outside the Python standard library. No third-party imports, no project imports beyond stdlib.
- **No arithmetic, no value claims.** The layer orchestrates files only. All numbers stay in the engine. `model/*.json` and `results.json` are never written or read by this module. Phase 6's inline composite-math Python (`re.findall` over dimension rows → `model/scores.json`) is **kept verbatim** — only the surrounding `mv` and shell index loop are replaced.
- **Behavior-preserving.** Canonical artifacts (`processes/`, `opportunities/`, `scores/`, `grc/`, every `_index.md`) keep the same structure, ids, and columns. The `<!-- index: key=val ... -->` extraction-header format and the `## TEMP-<token>` provisional-id format are unchanged. The **only** accepted cosmetic difference: the `_index.md` separator row renders as `| --- | --- | … |` (one `---` per column) instead of the prior hand-sized dashes — markdown renders identically and no test or golden pins it. Column header labels and all data cells are byte-preserved.
- **Determinism.** Id assignment and index/concat ordering follow a canonical order (sorted filenames, or an explicit `order` argument) — never subagent completion order. No primitive uses `iterdir`/`glob` for ordering without sorting.
- **Off-limits files:** `skills/using-methodology/SKILL.md` and `system-prompt.md` (verbatim-sync guard). The engine (`engine/`) and golden `results.json`. None of these are touched by any task.
- **Agents unchanged.** `opportunity-typer`, `opportunity-scorer`, the renderers, etc. already write the staging files. Only the orchestrator-side assembler (skill prose) changes.
- **Skill→Python invocation pattern (use verbatim):** `PYTHONPATH="<engine_root>" python3 -c "from state.assembly import …; …"`. Every fan-out skill already has a `**Session Start — resolve `engine_root`:**` preamble defining `<engine_root>` as the absolute plugin root; reuse it, add no new plumbing. `state/` is a sibling of `engine/` under that root, so `from state.assembly import …` resolves.
- **Python interpreter for local runs:** use `.venv/bin/python` (bare `python`/`python3` lacks the project venv). Run tests with `.venv/bin/python -m pytest`.
- **CHANGELOG** under `[Unreleased]`, **no per-task version bump**; one release closes #100 at branch finish.
- **Watch for iCloud `" 2"` duplicate files** (e.g. `test_assembly 2.py`) — they break pytest collection. If `pytest` reports an import-file-mismatch or a doubled test, delete the `* 2.py` duplicate (confirm a tracked original exists first).

---

### Task 1: Build `state/assembly.py` + full unit tests

Build the complete toolkit and its tests. No skill is wired in this task — this is the foundation Tasks 2–5 call into.

**Files:**
- Create: `state/assembly.py`
- Create: `state/tests/test_assembly.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces (the surface Tasks 2–5 rely on — exact signatures):
  - `collect_staged(staging_dir) -> list[Path]` — staged files sorted; `[]` if dir absent.
  - `renumber_sequential(files, dest_dir, prefix, *, order=None) -> list[str]` — split `## TEMP-<token>` blocks into `<dest_dir>/<PREFIX>-NNN.md`, remap each block's own temp token to its final id, return assigned ids.
  - `index_from_headers(files, dest_index, columns) -> int` — build `_index.md` from each file's `<!-- index: -->` header; `columns` is `list[(Header, key)]`; returns row count.
  - `index_from_fields(files, dest_index, columns, extract) -> int` — same, but field values come from `extract(path) -> dict`.
  - `promote(staging_dir, dest_dir, *, pattern="*.md") -> list[Path]` — move matching staged files to `dest_dir`, return moved paths sorted.
  - `concat_ordered(files, dest_file, order, *, sep="\n") -> Path` — concatenate `files` in `order` (matched against file stems) into `dest_file`.
  - `cleanup(staging_dir) -> None` — remove staging tree, idempotent.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_assembly.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_assembly.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.assembly'` (collection error before any test runs).

- [ ] **Step 3: Write `state/assembly.py`**

Create `state/assembly.py`:

```python
"""Portable staging-to-canonical assembly for the fan-out phases.

The methodology's fan-out phases dispatch one subagent per unit, each writing to
`<engagement>/_staging/<phase>/<unit>.md`. This module assembles the canonical
artifacts from those staging files: it splits/renumbers provisional ids, builds
`_index.md` tables, promotes files to their canonical folder, concatenates in a
fixed order, and clears staging.

Stdlib only — so it runs in any Python sandbox, including Claude.ai's Python-only
code tool — and it computes **no numbers**: all arithmetic stays in the engine.
Ordering is always canonical (sorted filenames, or an explicit ``order``), never
subagent completion order, so output is byte-identical regardless of dispatch
timing.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

# An extraction header:  <!-- index: id=OPP-001 type=Automation ... -->
_INDEX_RE = re.compile(r"<!--\s*index:(.*?)-->", re.DOTALL)
_KV_RE = re.compile(r"(\w+)=([^\s>]*)")
# A provisional heading:  ## TEMP-<token>   (token may contain hyphens/digits)
_TEMP_HEADING_RE = re.compile(r"^##\s+(TEMP-\S+)", re.MULTILINE)


def collect_staged(staging_dir) -> list[Path]:
    """Return staged files in deterministic (sorted) order; ``[]`` if absent."""
    d = Path(staging_dir)
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file())


def _header_fields(text: str) -> dict[str, str]:
    m = _INDEX_RE.search(text)
    return dict(_KV_RE.findall(m.group(1))) if m else {}


def _render_table(columns, rows) -> str:
    """``columns``: list of ``(Header, key)``; ``rows``: list of dicts."""
    headers = [h for h, _ in columns]
    keys = [k for _, k in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(k, "") for k in keys) + " |")
    return "\n".join(lines) + "\n"


def renumber_sequential(files, dest_dir, prefix, *, order=None) -> list[str]:
    """Split staged files containing ``## TEMP-<token>`` blocks into one
    canonical ``<dest_dir>/<PREFIX>-NNN.md`` per block.

    Blocks are numbered sequentially across ``files`` (reordered to ``order`` —
    a list of file names — when given, else taken as passed). Each block's own
    provisional ``TEMP-`` token is rewritten to its final ``<PREFIX>-NNN`` id
    throughout that block (heading + body), matching the legacy awk. Text before
    the first heading in a file is discarded (the awk emits nothing while no
    output file is open). Returns the assigned ids in order.
    """
    paths = [Path(f) for f in files]
    if order is not None:
        rank = {name: i for i, name in enumerate(order)}
        paths = sorted(paths, key=lambda p: (rank.get(p.name, len(rank)), p.name))
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    assigned: list[str] = []
    n = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        matches = list(_TEMP_HEADING_RE.finditer(text))
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end]
            temp_id = m.group(1)
            n += 1
            final_id = f"{prefix}-{n:03d}"
            block = block.replace(temp_id, final_id)
            (dest / f"{final_id}.md").write_text(block, encoding="utf-8")
            assigned.append(final_id)
    return assigned


def index_from_headers(files, dest_index, columns) -> int:
    """Rebuild ``_index.md`` at ``dest_index`` from each file's
    ``<!-- index: key=val ... -->`` header. ``columns`` is an ordered list of
    ``(Header, key)``; a missing key yields an empty cell. Returns row count."""
    rows = [_header_fields(Path(f).read_text(encoding="utf-8")) for f in files]
    Path(dest_index).write_text(_render_table(columns, rows), encoding="utf-8")
    return len(rows)


def index_from_fields(files, dest_index, columns, extract) -> int:
    """Like :func:`index_from_headers`, but field values come from
    ``extract(path) -> dict`` — for phases whose source of truth is the
    assembled file body, not an extraction header (Phase 4). Returns row count."""
    rows = [extract(Path(f)) for f in files]
    Path(dest_index).write_text(_render_table(columns, rows), encoding="utf-8")
    return len(rows)


def promote(staging_dir, dest_dir, *, pattern="*.md") -> list[Path]:
    """Move per-unit staged files matching ``pattern`` to ``dest_dir``. Returns
    the moved destination paths, sorted. Missing staging dir → ``[]``."""
    src = Path(staging_dir)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    sources = sorted(src.glob(pattern)) if src.is_dir() else []
    for p in sources:
        target = dest / p.name
        shutil.move(str(p), str(target))
        moved.append(target)
    return moved


def concat_ordered(files, dest_file, order, *, sep="\n") -> Path:
    """Concatenate ``files`` into ``dest_file`` in ``order`` (a list of unit ids
    matched against file stems). Files whose stem is not in ``order`` are
    appended last in sorted-stem order. Format-agnostic (md or html). Returns
    ``dest_file``."""
    paths = [Path(f) for f in files]
    rank = {uid: i for i, uid in enumerate(order)}
    ordered = sorted(paths, key=lambda p: (rank.get(p.stem, len(rank)), p.name))
    body = sep.join(p.read_text(encoding="utf-8") for p in ordered)
    out = Path(dest_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    return out


def cleanup(staging_dir) -> None:
    """Remove the staging tree (idempotent; no error if absent)."""
    shutil.rmtree(Path(staging_dir), ignore_errors=True)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest state/tests/test_assembly.py -v`
Expected: PASS — all tests green.

- [ ] **Step 5: Run the full suite to confirm no regression**

Run: `.venv/bin/python -m pytest`
Expected: PASS — prior baseline (256) plus the new assembly tests, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add state/assembly.py state/tests/test_assembly.py
git commit -m "feat(state): portable stdlib assembly toolkit for fan-out phases (#100)"
```

---

### Task 2: Migrate Phase 5 (the awk) → `state.assembly`

Replace the `awk` renumber block and the index `for` loop in `identifying-opportunities` with `collect_staged` → `renumber_sequential` → `index_from_headers` → `cleanup`. The `opportunity-typer` agent, the `## TEMP-<token>` format, and the `<!-- index: -->` header format are unchanged.

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md` (the "Assembly: After all agents complete, assemble with Bash" section)
- Modify: `tests/test_guards.py` (add the Phase 5 migration guard)
- Modify: `CHANGELOG.md` (under `[Unreleased]`)

**Interfaces:**
- Consumes from Task 1: `collect_staged`, `renumber_sequential`, `index_from_headers`, `cleanup`.

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_guards.py`:

```python
# --- Portable-assembly guards (defends: shell assemblers replaced by state.assembly, #100) ---

def test_phase5_assembly_uses_portable_layer(methodology):
    body = methodology.skills["ai-process-assessment:identifying-opportunities"].body
    # The portable layer is invoked …
    assert "from state.assembly import" in body
    assert "renumber_sequential" in body
    # … and the legacy shell assembler is gone.
    assert "awk '/^## TEMP-" not in body
    assert "for f in" not in body
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase5_assembly_uses_portable_layer -v`
Expected: FAIL — the skill still contains `awk '/^## TEMP-` and `for f in`, and lacks `from state.assembly import`.

- [ ] **Step 3: Replace the assembler in the skill**

In `skills/identifying-opportunities/SKILL.md`, find the assembly section. It currently contains an `awk` block (Part A — split + renumber `TEMP-`→`OPP-NNN`), a `for f in <name>/opportunities/OPP-*.md` index loop (Part B), and a `rm -rf <name>/_staging/phase5` cleanup. Replace **all three shell blocks** with this single block (keep the surrounding prose, the staging contract, and the `mkdir -p <name>/opportunities` intent):

````markdown
**Assembly (portable):** After all agents complete, assemble with one call into the tested `state.assembly` layer. `<engine_root>` is the absolute plugin root resolved at Session Start.

```bash
PYTHONPATH="<engine_root>" python3 -c "
from state.assembly import collect_staged, renumber_sequential, index_from_headers, cleanup
staged = collect_staged('<name>/_staging/phase5')
ids = renumber_sequential(staged, '<name>/opportunities', 'OPP')
index_from_headers(
    ['<name>/opportunities/%s.md' % i for i in ids],
    '<name>/opportunities/_index.md',
    [('OPP-ID', 'id'), ('Process', 'process'), ('Type', 'type'),
     ('Feasibility', 'feasibility'), ('Data Readiness', 'data'),
     ('GRC', 'grc'), ('Structural', 'struct')],
)
cleanup('<name>/_staging/phase5')
"
```

`renumber_sequential` splits each staged `proc-*.md` at its `## TEMP-<token>` headings, assigns global `OPP-NNN` ids in staged-file order (which equals process order — `proc-001`, `proc-002`, … sort to `PROC-001`, `PROC-002`, …), and remaps each opportunity's provisional token to its final id throughout its block. `index_from_headers` rebuilds `opportunities/_index.md` from the `<!-- index: -->` headers. Output is byte-identical regardless of subagent completion order.
````

Preserve every other line of the section (the dispatch contract, the typer's `## TEMP-`/extraction-header description, any notes). Only the three shell blocks are replaced.

- [ ] **Step 4: Run the guard to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase5_assembly_uses_portable_layer -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS — including the existing `test_opportunities_index_has_structural_column` and `test_typer_defines_structural_response_token` guards (the `Structural` column and typer tokens are preserved).

- [ ] **Step 6: Update CHANGELOG and commit**

Add under `[Unreleased]` in `CHANGELOG.md` (create the section if absent; do **not** bump the version):

```markdown
### Changed
- Phase 5 opportunity assembly now uses the portable stdlib `state.assembly` layer instead of inline `awk`, so it runs on Python-only surfaces and is deterministic regardless of subagent completion order (#100).
```

```bash
git add skills/identifying-opportunities/SKILL.md tests/test_guards.py CHANGELOG.md
git commit -m "refactor(phase5): replace awk assembler with portable state.assembly (#100)"
```

---

### Task 3: Migrate Phase 6 (scores) → `state.assembly`

Replace the `mv` (Part A) and the index `for` loop (Part C) in `scoring-opportunities`. **Keep Part B — the inline composite-math Python that stamps composites and writes `model/scores.json` — exactly as it is** (engine territory).

**Files:**
- Modify: `skills/scoring-opportunities/SKILL.md` (the "Assembly: After all scorer agents complete…" section)
- Modify: `tests/test_guards.py` (add the Phase 6 migration guard)
- Modify: `CHANGELOG.md` (under `[Unreleased]`)

**Interfaces:**
- Consumes from Task 1: `promote`, `index_from_headers`, `cleanup`.

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_guards.py`:

```python
def test_phase6_assembly_uses_portable_layer(methodology):
    body = methodology.skills["ai-process-assessment:scoring-opportunities"].body
    assert "from state.assembly import" in body
    assert "promote(" in body
    # Legacy file-move and index loop gone …
    assert "mv <name>/_staging/phase6" not in body
    assert "for f in <name>/scores/OPP-*.md" not in body
    # … but the engine composite math stays (model/scores.json still written here).
    assert "model/scores.json" in body
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase6_assembly_uses_portable_layer -v`
Expected: FAIL — skill still has `mv <name>/_staging/phase6` and the `for f in <name>/scores/OPP-*.md` loop.

- [ ] **Step 3: Replace Part A and Part C in the skill**

In `skills/scoring-opportunities/SKILL.md`, the assembly section runs three blocks in order: **Part A** (`mkdir -p <name>/scores` + `mv <name>/_staging/phase6/OPP-*.md <name>/scores/`), **Part B** (the `python3 -c "..."` that computes composites, stamps `composite=` into each file, and writes `model/scores.json`), **Part C** (the `for f in <name>/scores/OPP-*.md` loop building `scores/_index.md`), then a `rm -rf <name>/_staging/phase6 ...` cleanup.

Replace **Part A** with:

```bash
PYTHONPATH="<engine_root>" python3 -c "from state.assembly import promote; promote('<name>/_staging/phase6', '<name>/scores')"
```

Leave **Part B unchanged** (verbatim — it owns the composite arithmetic and `model/scores.json`; it must run *after* Part A and *before* Part C so it stamps the moved files).

Replace **Part C and the cleanup** with:

```bash
PYTHONPATH="<engine_root>" python3 -c "
from pathlib import Path
from state.assembly import index_from_headers, cleanup
files = sorted(Path('<name>/scores').glob('OPP-*.md'))
index_from_headers(files, '<name>/scores/_index.md',
                   [('OPP-ID', 'id'), ('Composite', 'composite'), ('Horizon', 'horizon'), ('B/B/P', 'bbp')])
cleanup('<name>/_staging/phase6')
"
```

Keep the prose that explains the three-step order and that Part B is engine math.

- [ ] **Step 4: Run the guard to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase6_assembly_uses_portable_layer -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS — including `test_phase6_composite_from_engine` (Part B's composite/`model/scores.json` logic is untouched).

- [ ] **Step 6: Update CHANGELOG and commit**

Add under `[Unreleased] → Changed` in `CHANGELOG.md`:

```markdown
- Phase 6 score assembly now promotes and indexes scored files via the portable `state.assembly` layer; the engine composite-math step is unchanged (#100).
```

```bash
git add skills/scoring-opportunities/SKILL.md tests/test_guards.py CHANGELOG.md
git commit -m "refactor(phase6): portable promote+index assembly, keep engine math (#100)"
```

---

### Task 4: Migrate Gate A (GRC) → `state.assembly`

Replace the `mv` (Part A) and the index `for` loop (Part B) in `governance-risk-gate`. The Python index also removes the zsh `status`-is-read-only gotcha that the shell version had to work around.

**Files:**
- Modify: `skills/governance-risk-gate/SKILL.md` (the "Assemble GRC reviews to canonical folder via Bash" section)
- Modify: `tests/test_guards.py` (add the Gate A migration guard)
- Modify: `CHANGELOG.md` (under `[Unreleased]`)

**Interfaces:**
- Consumes from Task 1: `promote`, `index_from_headers`, `cleanup`.

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_guards.py`:

```python
def test_gate_a_assembly_uses_portable_layer(methodology):
    body = methodology.skills["ai-process-assessment:governance-risk-gate"].body
    assert "from state.assembly import" in body
    assert "promote(" in body
    assert "mv <name>/_staging/grc" not in body
    assert "for f in <name>/grc/OPP-*.md" not in body
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_gate_a_assembly_uses_portable_layer -v`
Expected: FAIL — skill still has the `mv <name>/_staging/grc` and the `for f in <name>/grc/OPP-*.md` loop.

- [ ] **Step 3: Replace the assembler in the skill**

In `skills/governance-risk-gate/SKILL.md`, the section has **Part A** (`mkdir -p <name>/grc` + `mv <name>/_staging/grc/OPP-*.md <name>/grc/`), **Part B** (the `for f in <name>/grc/OPP-*.md` loop building `grc/_index.md` with `id`/`status`/`conditions`, including the zsh read-only-`status` comment), and a `rm -rf <name>/_staging/grc` cleanup. Replace **all of it** with:

```bash
PYTHONPATH="<engine_root>" python3 -c "
from pathlib import Path
from state.assembly import promote, index_from_headers, cleanup
promote('<name>/_staging/grc', '<name>/grc')
files = sorted(Path('<name>/grc').glob('OPP-*.md'))
index_from_headers(files, '<name>/grc/_index.md',
                   [('OPP-ID', 'id'), ('Status', 'status'), ('Conditions', 'conditions')])
cleanup('<name>/_staging/grc')
"
```

Keep the surrounding prose describing what GRC assembly produces.

- [ ] **Step 4: Run the guard to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_gate_a_assembly_uses_portable_layer -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS.

- [ ] **Step 6: Update CHANGELOG and commit**

Add under `[Unreleased] → Changed` in `CHANGELOG.md`:

```markdown
- Gate A (GRC) assembly now uses the portable `state.assembly` layer, removing the inline `mv`/`awk`-style shell and the zsh read-only-`status` workaround (#100).
```

```bash
git add skills/governance-risk-gate/SKILL.md tests/test_guards.py CHANGELOG.md
git commit -m "refactor(gate-a): portable GRC assembly via state.assembly (#100)"
```

---

### Task 5: Migrate Phase 4 (process index) → `state.assembly`

Replace the index `for` loop in `discovering-processes` with `index_from_fields` plus a small inline `extract` that reads each `PROC-NNN.md`'s id (filename), name (heading), and baseline (index header, default `Unavailable`). Cross-round synthesis still writes the `processes/PROC-NNN.md` files in main context — only the index loop and cleanup change.

**Files:**
- Modify: `skills/discovering-processes/SKILL.md` (the "Assembly — after all synthesis is complete, generate the index" section)
- Modify: `tests/test_guards.py` (add the Phase 4 migration guard)
- Modify: `CHANGELOG.md` (under `[Unreleased]`)

**Interfaces:**
- Consumes from Task 1: `index_from_fields`, `cleanup`.

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_guards.py`:

```python
def test_phase4_index_uses_portable_layer(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    assert "from state.assembly import" in body
    assert "index_from_fields" in body
    assert "for f in <name>/processes/PROC-*.md" not in body
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase4_index_uses_portable_layer -v`
Expected: FAIL — skill still has the `for f in <name>/processes/PROC-*.md` loop.

- [ ] **Step 3: Replace the index loop in the skill**

In `skills/discovering-processes/SKILL.md`, the assembly section builds `processes/_index.md` with a `for f in <name>/processes/PROC-*.md` loop (id from `basename`, name from the `## PROC-NNN — <name>` heading via `sed`, baseline from the `<!-- index: baseline=… -->` header, default `Unavailable`), then runs `rm -rf <name>/_staging/phase4`. Replace **both** with:

```bash
PYTHONPATH="<engine_root>" python3 -c "
import re
from pathlib import Path
from state.assembly import index_from_fields, cleanup

def extract(path):
    text = Path(path).read_text(encoding='utf-8')
    m = re.search(r'^## PROC-\d+ — (.+)\$', text, re.M)
    hm = re.search(r'baseline=([^\s>]*)', text)
    return {
        'id': Path(path).stem,
        'name': m.group(1).strip() if m else '',
        'baseline': hm.group(1) if hm and hm.group(1) else 'Unavailable',
    }

files = sorted(Path('<name>/processes').glob('PROC-*.md'))
index_from_fields(files, '<name>/processes/_index.md',
                  [('PROC-ID', 'id'), ('Process Name', 'name'), ('Baseline', 'baseline')], extract)
cleanup('<name>/_staging/phase4')
"
```

Note the heading separator is an em-dash (`—`); copy it verbatim from the existing skill. Preserve the prose that cross-round synthesis writes the `PROC-NNN.md` files before this index step.

- [ ] **Step 4: Run the guard to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_guards.py::test_phase4_index_uses_portable_layer -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest`
Expected: PASS — including the Phase 4 structural-challenge guards (`test_phase4_*`), which are unaffected.

- [ ] **Step 6: Update CHANGELOG and commit**

Add under `[Unreleased] → Changed` in `CHANGELOG.md`:

```markdown
- Phase 4 `processes/_index.md` assembly now uses the portable `state.assembly` layer instead of an inline `for`/`grep`/`sed` shell loop (#100).
```

```bash
git add skills/discovering-processes/SKILL.md tests/test_guards.py CHANGELOG.md
git commit -m "refactor(phase4): portable process-index assembly via state.assembly (#100)"
```

---

## Notes for the executor

- **Branch:** start fresh off `main` (b6076d9). Do **not** build on the abandoned `feat/slice2-parallel-fanout` branch. Suggested name: `feat/portable-assembly-layer`.
- **Auto-merge expectation:** this branch mixes Python (`state/`, `tests/`) with methodology markdown (`skills/`). Per the repo's auto-review loop, markdown changes are human-merge-only, and the gate may also HOLD `state/assembly.py` as an "unwired helper" because its only callers are skill-prose `python3 -c` strings, not Python imports — that is expected, not a defect. Plan on a **human merge with a short decision comment** explaining both (consumed by skill prose; markdown in the diff).
- **git push** to github.com hangs on HTTP/2 — use `git -c http.version=HTTP/1.1 push` when the time comes.
- **Final whole-branch review** (SDD): dispatch on the most capable model; point it at the full branch diff and this plan.
- **Out of scope (deferred follow-up, #100 part 2):** Phases 8, 9, 11, and checkpoints assemble in main context, not shell. `concat_ordered` is built and tested here for them but wired to nothing. See spec §6.
```