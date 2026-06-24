# Slice 2 · Chunk A — Parallel per-process fan-out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the conductor run Phase 5 (opportunity identification) as concurrent per-process subagents whose results merge deterministically into the existing global `OPP-NNN` opportunity log.

**Architecture:** Per-process subagents write provisional opportunities into a staging tree; a new stdlib `state/` helper merges them into canonical `opportunities/` by process order, assigning global ids. Because id assignment is driven by process order (not completion order), concurrent and sequential fan-out produce byte-identical output. The engine, convergence gate, and cross-process chain-detection are unchanged and reused.

**Tech Stack:** Python standard library only (matches `state/`), pytest, markdown skill prose.

Spec: `docs/superpowers/specs/2026-06-21-slice2-parallel-fanout-design.md`.

## Global Constraints

- **Stdlib only.** `state/opportunity_merge.py` imports nothing outside the Python standard library (the core must run in any code sandbox with no pip). Match the existing `state/` modules: `from __future__ import annotations`, a module docstring, pure functions taking `root: Path`.
- **No arithmetic, no value claims.** The merge helper assigns ids and moves/rewrites files only. It computes no numbers — the engine owns all numbers.
- **Staging contract (shared by Task 1 reader and Task 2 writer — use verbatim):**
  - Per-process staging dir: `opportunities/_staging/PROC-NNN/` (e.g. `opportunities/_staging/PROC-003/`).
  - Inside each: one `_index.md` with the canonical 7-column header
    `| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |`
    and one row per opportunity, plus one `OPP-P<nnn>-<seq>.md` file per opportunity.
  - **Provisional id format:** `OPP-P<nnn>-<seq>` where `<nnn>` is the 3-digit numeric part of the owning `PROC-NNN` and `<seq>` is a 2-digit 1-based counter within that process. Example: PROC-003's second opportunity → `OPP-P003-02`. The literal `P` after the first hyphen distinguishes a provisional id (`OPP-P003-02`) from a final id (`OPP-007`).
- **Canonical outputs (unchanged formats):**
  - `opportunities/_index.md` — header `| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |`, rows in assigned-id order.
  - `opportunities/OPP-NNN.md` — one per opportunity, final id `OPP-<nnn>` (3-digit, zero-padded).
- **Process order is row order** of `processes/_index.md` (table `| PROC-ID | Process Name | Baseline |`).
- **CHANGELOG:** add under `[Unreleased]` only — **no version bump** (accumulates toward the v2.19.0 release that closes #87).
- **Off-limits:** do not edit `skills/using-methodology/SKILL.md` or `system-prompt.md` (verbatim-sync guard). Do not touch the engine or golden `results.json`.

---

### Task 1: Deterministic merge helper `state/opportunity_merge.py`

**Files:**
- Create: `state/opportunity_merge.py`
- Test: `state/tests/test_opportunity_merge.py`

**Interfaces:**
- Consumes: an engagement `root: Path` containing `processes/_index.md` and `opportunities/_staging/PROC-NNN/` dirs per the staging contract.
- Produces:
  - `merge_staged_opportunities(root: Path) -> list[str]` — assigns global ids, writes `opportunities/OPP-NNN.md` + `opportunities/_index.md`, removes `opportunities/_staging/`, returns the assigned final ids (e.g. `["OPP-001", "OPP-002", ...]`) in order.
  - Helper `_process_order(root: Path) -> list[str]` — returns PROC-IDs in `processes/_index.md` row order.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_opportunity_merge.py`:

```python
from state.opportunity_merge import merge_staged_opportunities, _process_order


def _stage(engagement_root, proc_id, rows):
    """rows: list of (prov_seq, type) -> writes a staging dir for proc_id.

    prov_seq is the 2-digit provisional sequence string, e.g. "01".
    """
    nnn = proc_id.split("-")[1]
    sdir = engagement_root / "opportunities" / "_staging" / proc_id
    sdir.mkdir(parents=True, exist_ok=True)
    header = ("| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
              "|--------|---------|------|-------------|----------------|-----|------------|\n")
    lines = []
    for seq, typ in rows:
        prov = f"OPP-P{nnn}-{seq}"
        lines.append(f"| {prov} | {proc_id} | {typ} | Green | Green | Green | addressing-root |")
        (sdir / f"{prov}.md").write_text(
            f"# {prov}\n\nProcess reference: {proc_id}\nType: {typ}\n"
        )
    (sdir / "_index.md").write_text(header + "\n".join(lines) + "\n")


def _procs_index(engagement_root, proc_ids):
    header = ("| PROC-ID | Process Name | Baseline |\n"
              "|---------|--------------|----------|\n")
    rows = "\n".join(f"| {p} | {p} name | Ready |" for p in proc_ids)
    (engagement_root / "processes").mkdir(parents=True, exist_ok=True)
    (engagement_root / "processes" / "_index.md").write_text(header + rows + "\n")


def test_assigns_global_ids_in_process_order(engagement):
    root = engagement()
    _procs_index(root, ["PROC-001", "PROC-002"])
    _stage(root, "PROC-002", [("01", "RPA")])
    _stage(root, "PROC-001", [("01", "AIAugmentation")])
    assigned = merge_staged_opportunities(root)
    assert assigned == ["OPP-001", "OPP-002"]
    # PROC-001 comes first in process order, so its opp gets OPP-001
    opp1 = (root / "opportunities" / "OPP-001.md").read_text()
    assert "PROC-001" in opp1 and "AIAugmentation" in opp1
    opp2 = (root / "opportunities" / "OPP-002.md").read_text()
    assert "PROC-002" in opp2 and "RPA" in opp2


def test_order_invariant_to_staging_iteration_order(engagement):
    """Determinism: shuffled creation order yields identical canonical output."""
    def build(order):
        root = engagement()
        _procs_index(root, ["PROC-001", "PROC-002", "PROC-003"])
        for p in order:
            _stage(root, p, [("01", "RPA"), ("02", "AIAugmentation")])
        merge_staged_opportunities(root)
        return (root / "opportunities" / "_index.md").read_text()

    a = build(["PROC-003", "PROC-001", "PROC-002"])
    b = build(["PROC-001", "PROC-002", "PROC-003"])
    assert a == b


def test_multiple_opps_per_process_keep_within_process_order(engagement):
    root = engagement()
    _procs_index(root, ["PROC-001"])
    _stage(root, "PROC-001", [("01", "RPA"), ("02", "AIAugmentation")])
    assigned = merge_staged_opportunities(root)
    assert assigned == ["OPP-001", "OPP-002"]
    assert "RPA" in (root / "opportunities" / "OPP-001.md").read_text()
    assert "AIAugmentation" in (root / "opportunities" / "OPP-002.md").read_text()


def test_rewrites_intra_process_chain_reference(engagement):
    root = engagement()
    _procs_index(root, ["PROC-001", "PROC-002"])
    # PROC-002's opp references PROC-002's other opp by provisional id.
    sdir = root / "opportunities" / "_staging" / "PROC-002"
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "_index.md").write_text(
        "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
        "|--------|---------|------|-------------|----------------|-----|------------|\n"
        "| OPP-P002-01 | PROC-002 | ChainAutomation | Green | Green | Green | addressing-root |\n"
        "| OPP-P002-02 | PROC-002 | ChainAutomation | Green | Green | Green | addressing-root |\n"
    )
    (sdir / "OPP-P002-01.md").write_text("# OPP-P002-01\n\nChain: forms with OPP-P002-02\n")
    (sdir / "OPP-P002-02.md").write_text("# OPP-P002-02\n\nProcess reference: PROC-002\n")
    _stage(root, "PROC-001", [("01", "RPA")])  # gets OPP-001
    assigned = merge_staged_opportunities(root)
    assert assigned == ["OPP-001", "OPP-002", "OPP-003"]
    # PROC-002's first opp is OPP-002, its second is OPP-003; the reference must follow.
    text = (root / "opportunities" / "OPP-002.md").read_text()
    assert "OPP-003" in text and "OPP-P002-02" not in text


def test_clears_staging_after_merge(engagement):
    root = engagement()
    _procs_index(root, ["PROC-001"])
    _stage(root, "PROC-001", [("01", "RPA")])
    merge_staged_opportunities(root)
    assert not (root / "opportunities" / "_staging").exists()


def test_empty_staging_returns_no_ids(engagement):
    root = engagement()
    _procs_index(root, ["PROC-001"])
    (root / "opportunities" / "_staging").mkdir(parents=True)
    assert merge_staged_opportunities(root) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest state/tests/test_opportunity_merge.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.opportunity_merge'`.

- [ ] **Step 3: Write the implementation**

Create `state/opportunity_merge.py`:

```python
"""Deterministic merge of per-process staged opportunities into the global log.

Parallel Phase-5 fan-out writes each process's opportunities into
opportunities/_staging/PROC-NNN/ with *provisional* ids (OPP-P<nnn>-<seq>). This
helper assigns the final, portfolio-global OPP-NNN ids by **process order**
(processes/_index.md row order), so concurrent and sequential fan-out produce
byte-identical output. It assigns ids and rewrites files only — it makes no value
claim and computes no number; the engine owns all arithmetic.

Pure stdlib so the core runs in any code sandbox without pip.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

PROVISIONAL_RE = re.compile(r"OPP-P\d{3}-\d+")
_PROC_ROW_RE = re.compile(r"^\|\s*(PROC-\d+)\s*\|")
_STAGE_ROW_RE = re.compile(r"^\|\s*(OPP-P\d{3}-\d+)\s*\|(.*)$")


def _process_order(root: Path) -> list[str]:
    """PROC-IDs in processes/_index.md row order."""
    index = Path(root) / "processes" / "_index.md"
    if not index.exists():
        return []
    order: list[str] = []
    for line in index.read_text().splitlines():
        m = _PROC_ROW_RE.match(line.strip())
        if m:
            order.append(m.group(1))
    return order


def _staged_rows(stage_dir: Path) -> list[tuple[str, str]]:
    """(provisional_id, full_index_row) for one process, in _index.md row order."""
    index = stage_dir / "_index.md"
    rows: list[tuple[str, str]] = []
    if not index.exists():
        return rows
    for line in index.read_text().splitlines():
        m = _STAGE_ROW_RE.match(line.strip())
        if m:
            rows.append((m.group(1), line.rstrip("\n")))
    return rows


def merge_staged_opportunities(root: Path) -> list[str]:
    root = Path(root)
    stage_root = root / "opportunities" / "_staging"
    if not stage_root.exists():
        return []

    # 1. Build the ordered (provisional_id, index_row, source_file) list and the
    #    provisional -> final id map, traversing processes in canonical order.
    ordered: list[tuple[str, str, Path]] = []
    id_map: dict[str, str] = {}
    counter = 0
    for proc_id in _process_order(root):
        stage_dir = stage_root / proc_id
        if not stage_dir.is_dir():
            continue
        for prov, row in _staged_rows(stage_dir):
            counter += 1
            final = f"OPP-{counter:03d}"
            id_map[prov] = final
            ordered.append((prov, row, stage_dir / f"{prov}.md"))

    # 2. Write canonical OPP files, rewriting every provisional id (own + chain
    #    references) to its final id via the global map.
    def remap(text: str) -> str:
        return PROVISIONAL_RE.sub(lambda m: id_map.get(m.group(0), m.group(0)), text)

    for prov, _row, src in ordered:
        final = id_map[prov]
        body = src.read_text() if src.exists() else f"# {prov}\n"
        (root / "opportunities" / f"{final}.md").write_text(remap(body))

    # 3. Write the canonical _index.md (header + remapped rows in assigned order).
    header = (
        "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |\n"
        "|--------|---------|------|-------------|----------------|-----|------------|\n"
    )
    body_rows = "\n".join(remap(row) for _prov, row, _src in ordered)
    out = header + (body_rows + "\n" if body_rows else "")
    (root / "opportunities" / "_index.md").write_text(out)

    # 4. Clear staging — it is an implementation detail, never an output.
    shutil.rmtree(stage_root)

    return [id_map[prov] for prov, _row, _src in ordered]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest state/tests/test_opportunity_merge.py -q`
Expected: PASS (7 passed).

- [ ] **Step 5: Run the full suite to confirm no regression**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest -q`
Expected: PASS (all pre-existing tests + the 7 new ones).

- [ ] **Step 6: Commit**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment
git add state/opportunity_merge.py state/tests/test_opportunity_merge.py
git commit -m "feat(state): deterministic per-process opportunity merge helper"
```

---

### Task 2: `identifying-opportunities` — explicit single-process-scoped staging

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md`
- Test: `tests/test_identifying_opportunities_staging.py`

**Interfaces:**
- Consumes: nothing from earlier tasks at runtime; must produce staging files that match the Global Constraints staging contract that Task 1's `merge_staged_opportunities` reads.
- Produces: skill prose describing single-process-scoped dispatch.

This task adds a section to the Phase 5 skill telling it that, **when dispatched for a single `PROC-NNN`**, it reads only that process and writes provisional opportunities into the staging tree (instead of writing canonical `opportunities/OPP-NNN.md` directly). The existing whole-portfolio behavior is retained for the N=1 / sequential path.

- [ ] **Step 1: Write the failing guard test**

Create `tests/test_identifying_opportunities_staging.py`:

```python
"""Phase 5 must support single-process-scoped dispatch into the staging tree
(the unit of parallel fan-out — Slice 2 Chunk A)."""
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "identifying-opportunities" / "SKILL.md"


def test_skill_documents_single_process_scoped_dispatch():
    text = SKILL.read_text()
    assert "## Single-process-scoped dispatch" in text, \
        "Phase 5 skill must document single-process-scoped dispatch for fan-out"


def test_skill_names_the_staging_path_and_provisional_id_format():
    text = SKILL.read_text()
    assert "opportunities/_staging/" in text, "must name the staging path"
    assert "OPP-P" in text, "must specify the provisional id format (OPP-P<nnn>-<seq>)"


def test_skill_keeps_whole_portfolio_path():
    text = SKILL.read_text()
    # The unscoped path (writing canonical OPP-NNN files) must still be described.
    assert "opportunities/_index.md" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_identifying_opportunities_staging.py -q`
Expected: FAIL — the `## Single-process-scoped dispatch` heading and staging tokens are absent.

- [ ] **Step 3: Add the section to the skill**

Append this section to `skills/identifying-opportunities/SKILL.md` (after the existing "Role in the system"/"Gate condition" material, before the per-OPP structure if present; placement is not asserted — only the content is):

```markdown
## Single-process-scoped dispatch

This phase runs in two modes:

- **Whole-portfolio (default / N=1 / sequential):** type every process's
  opportunities and write the canonical `opportunities/OPP-NNN.md` files and
  `opportunities/_index.md` directly, as described above.
- **Single-process-scoped (parallel fan-out):** when the conductor dispatches you
  for exactly **one** `PROC-NNN`, read only that process's `processes/PROC-NNN.md`
  (plus `tech-inventory.md` and `context.md`) and write your opportunities into the
  staging tree — never the canonical files. Another step assigns the final global ids.

  Write into `opportunities/_staging/PROC-NNN/`:
  - one `OPP-P<nnn>-<seq>.md` per opportunity, where `<nnn>` is this process's 3-digit
    number and `<seq>` is a 2-digit 1-based counter (e.g. PROC-003's second opportunity
    is `OPP-P003-02`);
  - an `_index.md` with the standard 7-column header and one row per opportunity, using
    those provisional ids.

  Reference another opportunity **only within your own process**, by its provisional id
  (cross-process chains are detected later, after the merge). Do not invent global
  `OPP-NNN` ids — they would collide with other processes running concurrently.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_identifying_opportunities_staging.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment
git add skills/identifying-opportunities/SKILL.md tests/test_identifying_opportunities_staging.py
git commit -m "feat(phase5): single-process-scoped dispatch into staging tree"
```

---

### Task 3: `conducting-engagement` — fan-out orchestration + CHANGELOG

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_parallel_fanout.py`

**Interfaces:**
- Consumes: Task 1's `merge_staged_opportunities` (named in prose as the merge step) and Task 2's staging contract.
- Produces: drive-loop prose that triggers fan-out, dispatches per process, merges, then runs the existing chain-detection; plus failure + degradation rules.

- [ ] **Step 1: Write the failing guard test**

Create `tests/test_parallel_fanout.py`:

```python
"""Conductor must orchestrate parallel per-process Phase 5 fan-out (Slice 2 Chunk A)."""
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "conducting-engagement" / "SKILL.md"


def _body() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_has_fanout_section():
    assert "## Parallel per-process fan-out" in _body()


def test_trigger_requires_two_or_more_ready_processes():
    body = _body()
    # The trigger must be conditioned on >=2 processes; N=1 stays sequential.
    assert "two or more" in body or "≥2" in body or ">= 2" in body
    assert "single process" in body.lower() or "n=1" in body.lower()


def test_names_merge_step_and_chain_detection_order():
    body = _body()
    assert "merge_staged_opportunities" in body, "must name the deterministic merge step"
    # Chain-detection runs AFTER the merge.
    merge_at = body.find("merge_staged_opportunities")
    chain_at = body.find("chain-detection", merge_at)
    assert chain_at != -1, "chain-detection must be described after the merge"


def test_describes_batch_failure_and_degradation():
    body = _body().lower()
    assert "re-dispatch" in body and "only that process" in body
    assert "sequential" in body  # graceful degradation where no concurrent dispatch


def test_fanout_narration_is_jargon_free():
    """The user-facing line the AI says during fan-out must not leak machinery terms."""
    body = _body()
    start = body.find("<!-- fanout-line:start -->")
    end = body.find("<!-- fanout-line:end -->")
    assert start != -1 and end != -1, "fan-out user line must be delimited for the guard"
    line = body[start:end]
    for token in ("subagent", "Phase 5", "OPP-", "_staging", "merge_staged_opportunities"):
        assert token not in line, f"fan-out user line leaks machinery token: {token!r}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_parallel_fanout.py -q`
Expected: FAIL — the `## Parallel per-process fan-out` section and delimiters are absent.

- [ ] **Step 3: Add the fan-out section to the conductor skill**

Insert this section into `skills/conducting-engagement/SKILL.md` immediately after the `## Elastic processes & convergence` section (it builds on convergence):

```markdown
## Parallel per-process fan-out

When the next step is opportunity identification (Phase 5) and **two or more**
in-scope processes have `Baseline = Ready`, run it as concurrent per-process work
instead of one sequential pass. With a **single process** (N=1) — or on a surface
without concurrent dispatch — run it sequentially; the result is identical.

To the user this is one beat, no machinery:

<!-- fanout-line:start -->
> Great — I've mapped all your processes. Now I'm finding automation and AI
> opportunities across them together; I'll come back with the combined picture.
<!-- fanout-line:end -->

Then:

1. **Fan out.** Dispatch one subagent per Ready process, each scoped to a single
   `PROC-NNN`, running `ai-process-assessment:identifying-opportunities` in its
   single-process-scoped mode. Each writes provisional opportunities into
   `opportunities/_staging/PROC-NNN/` (it returns only a one-line confirmation — hand
   work as files, never as pasted content). Disjoint staging dirs → no write conflict.
2. **Merge deterministically.** Once every Ready process is staged, assign final global
   ids by process order:
   `PYTHONPATH="<engine_root>" python3 -c "from state.opportunity_merge import merge_staged_opportunities; merge_staged_opportunities('<folder>')"`.
   This writes the canonical `opportunities/OPP-NNN.md` + `opportunities/_index.md` and
   clears staging. Because ids follow process order, concurrent and sequential fan-out
   produce identical output.
3. **Cross-process chain-detection.** Run the convergence chain-detection scan (above)
   over the merged `opportunities/`, in the context where every process's opportunities
   are visible. Per-process subagents could not see cross-boundary chains; you must.

**Batch failure:** if one process's subagent fails, re-dispatch **only that process** —
the others' staged work is kept. Do not merge until the full set of Ready processes is
staged (convergence already requires every in-scope process).

**Degradation:** on a surface without concurrent dispatch (e.g. Claude.ai), run the
per-process subagents one at a time into the same staging layout, then merge identically.
Fan-out is an optimization; the sequential path is the invariant.
```

- [ ] **Step 4: Add the CHANGELOG entry**

In `CHANGELOG.md`, under the existing `## [Unreleased]` heading, add an `### Added` entry (create the `### Added` subheading under `[Unreleased]` if it is not already there):

```markdown
- **Parallel per-process opportunity identification.** On a multi-process engagement the
  assistant now finds opportunities across all processes concurrently, then merges them
  into one portfolio with stable, reproducible ids — the same result whether run in
  parallel or sequentially. (Slice 2 · #87)
```

- [ ] **Step 5: Run the guard test and the full suite**

Run: `cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_parallel_fanout.py -q && python -m pytest -q`
Expected: PASS — the 5 new fan-out guards pass and the whole suite is green.

- [ ] **Step 6: Commit**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment
git add skills/conducting-engagement/SKILL.md tests/test_parallel_fanout.py CHANGELOG.md
git commit -m "feat(conductor): parallel per-process Phase 5 fan-out + deterministic merge"
```

---

## Self-Review

**1. Spec coverage:**
- §1 user experience → Task 3 `<!-- fanout-line -->` + jargon guard. ✓
- §2 scope (P5 fan-out, no engine change) → Tasks 1–3, no engine file touched. ✓
- §3 deterministic merge by process order → Task 1 (`merge_staged_opportunities`, order-invariance test). ✓
- §3.1 staging layout → Global Constraints staging contract + Task 2. ✓
- §3.2 tested `state/` helper → Task 1. ✓
- §4 orchestration (trigger, dispatch, merge, degradation) → Task 3. ✓
- §4 single-process-scoped dispatch → Task 2. ✓
- §5 batch failure → Task 3 guard `test_describes_batch_failure_and_degradation`. ✓
- §7 guards 1–5 → guard 1 (Task 1 order-invariance), 2 (Task 3 trigger), 3 (Task 1 disjoint-by-construction + staging contract), 4 (Task 3 batch failure), 5 (Task 3 jargon line). ✓
- §8 files touched → matches Tasks 1–3; `using-methodology`/`system-prompt.md` untouched, engine untouched. ✓

**2. Placeholder scan:** No TBD/TODO; every code and prose block is complete. ✓

**3. Type consistency:** `merge_staged_opportunities(root: Path) -> list[str]` and `_process_order(root: Path) -> list[str]` are used identically in Task 1's tests and impl and named verbatim in Task 3's prose + guard. Provisional id `OPP-P<nnn>-<seq>` and staging path `opportunities/_staging/PROC-NNN/` are identical across Global Constraints, Task 1 regex (`OPP-P\d{3}-\d+`), Task 2 prose, and Task 3 guard. ✓
