# Slice 3 · Chunk A — Integrity Checker + Resume Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the *existence ≠ completeness* gap by adding a pure-Python integrity checker that classifies partial-state inconsistencies as auto-repairable or must-surface, and wiring it into the Conductor's resume path.

**Architecture:** A new pure module `state/integrity.py` (detection/classification only, no repair, no subprocess) modelled on `state/state.py` and `state/staleness.py`. A `header_based` flag added to the `Phase`/`Gate` schema lets the checker apply header-dependent checks only to header-based folders (5/6/8/grc), never to field-based `processes/` (Phase 4). A new Conductor SKILL.md section wires it into drive-loop step 1.

**Tech Stack:** Python standard library only (stdlib core — no third-party deps at runtime). pytest for tests (`.venv/bin/python -m pytest`).

## Global Constraints

- **Stdlib only at runtime.** `state/integrity.py` may import only the standard library and other `state.*` modules. No third-party imports. (Verbatim from spec §3.1: "pure Python standard library".)
- **Detection only — never repair.** `check_integrity` performs no mutation, no subprocess, no engine run. Repair is the Conductor's job using existing primitives. (Spec §3.1.)
- **Determinism.** `check_integrity` returns `Issue`s sorted by `(target, kind)`; no mtime, no filesystem-order dependence. (Spec §3.2.)
- **Repair stance:** auto = deterministically re-derivable from sources; surface = needs human content. (Spec §2.)
- **Header-dependent checks (`malformed_item`, header-based `index_orphan_items`) apply only to `header_based=True` folders.** Field-based `processes/` gets only the header-agnostic checks. (Spec §3.2 "Header-based vs field-based folders".)
- **No redundancy:** do not detect *changed* model inputs (owned by `state/staleness.py`) or `.conductor.md` health (owned by `state/conductor_state.py`). Only *absent* `results.json` is flagged. (Spec §6.)
- **Repo-relative targets.** Every `Issue.target` is a path relative to the engagement root (e.g. `scope.md`, `opportunities/_index.md`, `model/results.json`). (Spec §3.1.)
- **Jargon-free narration.** The Conductor narration block leaks no phase/file/id names. (Epic AC-1.)

---

## File Structure

- `state/phases.py` — **modify**: add `header_based: bool = False` to `Phase` and `Gate`; set `True` on phases 5/6/8 and the grc gate.
- `state/integrity.py` — **create**: `Issue` dataclass, helpers (`_folder_targets`, `_index_ids`, `_body_ids`), `check_integrity`, `main` (CLI).
- `state/tests/test_phases.py` — **modify**: assert the `header_based` values.
- `state/tests/test_integrity.py` — **create**: unit tests for every `kind`, classification, ordering, and the staleness-deferral boundary.
- `state/tests/test_integrity_cli.py` — **create**: CLI JSON output + exit codes (mirrors `test_state_cli.py`).
- `skills/conducting-engagement/SKILL.md` — **modify**: add `## Resuming into a messy state` + narration block; reference it from drive-loop step 1.
- `tests/test_conductor_skill.py` — **modify**: static guards for the new section.

---

### Task 1: `header_based` flag on the phase/gate schema

**Files:**
- Modify: `state/phases.py`
- Test: `state/tests/test_phases.py`

**Interfaces:**
- Produces: `Phase.header_based: bool` and `Gate.header_based: bool` (default `False`). `True` for phases id `"5"`, `"6"`, `"8"` and gate id `"grc"`. Consumed by `state/integrity.py` Task 4.

- [ ] **Step 1: Write the failing test**

Add to `state/tests/test_phases.py`:

```python
def test_header_based_flag_marks_extraction_header_folders():
    from state.phases import PHASES, GATES
    by_id = {p.id: p for p in PHASES}
    # Phases whose _index.md is built from <!-- index: id=... --> headers.
    assert by_id["5"].header_based is True
    assert by_id["6"].header_based is True
    assert by_id["8"].header_based is True
    # Phase 4 (processes/) is field-based: index_from_fields, no id= header.
    assert by_id["4"].header_based is False
    # Non-folder phases default False.
    assert by_id["1"].header_based is False
    grc = next(g for g in GATES if g.id == "grc")
    deliverable = next(g for g in GATES if g.id == "deliverable")
    assert grc.header_based is True
    assert deliverable.header_based is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_phases.py::test_header_based_flag_marks_extraction_header_folders -v`
Expected: FAIL — `AttributeError: 'Phase' object has no attribute 'header_based'`.

- [ ] **Step 3: Add the field and set it**

In `state/phases.py`, add the field to both dataclasses (append last, default `False`, so existing positional constructions stay valid):

```python
@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    skill: str
    output: str            # relative path whose existence means the phase is done
    predecessor: str | None  # relative path that must exist for the phase to be available
    header_based: bool = False  # _index.md built from <!-- index: id=... --> headers


@dataclass(frozen=True)
class Gate:
    id: str
    name: str
    output: str            # relative path whose existence means the gate has run
    header_based: bool = False
```

Then set `header_based=True` on the three header-based phases and the grc gate (leave all others at the default). Change these three `PHASES` entries:

```python
    Phase("5", "Opportunities", "ai-process-assessment:identifying-opportunities", "opportunities/_index.md", "processes/_index.md", header_based=True),
    Phase("6", "Scoring", "ai-process-assessment:scoring-opportunities", "scores/_index.md", "opportunities/_index.md", header_based=True),
    Phase("8", "Use-Case Briefs", "ai-process-assessment:packaging-usecases", "usecase-briefs/_index.md", "roadmap.md", header_based=True),
```

And the grc gate:

```python
    Gate("grc", "Governance & Risk (Gate A)", "grc/_index.md", header_based=True),
```

- [ ] **Step 4: Run the phases test + full state suite**

Run: `.venv/bin/python -m pytest state/tests/test_phases.py state/tests/test_state.py -v`
Expected: PASS (the new field is keyword/positional-compatible; `state.state` reads phases by attribute and is unaffected).

- [ ] **Step 5: Commit**

```bash
git add state/phases.py state/tests/test_phases.py
git commit -m "feat(state): header_based flag on Phase/Gate schema (slice3 chunkA)"
```

---

### Task 2: `Issue` dataclass + `check_integrity` skeleton + `empty_output`

**Files:**
- Create: `state/integrity.py`
- Test: `state/tests/test_integrity.py`

**Interfaces:**
- Consumes: `state.phases.PHASES`.
- Produces:
  - `Issue(kind: str, target: str, repair: str, detail: str)` — frozen dataclass.
  - `check_integrity(root) -> list[Issue]` — pure; returns `Issue`s sorted by `(target, kind)`.
  - `empty_output` issue: `kind="empty_output"`, `repair="surface"`, `target` = the phase's repo-relative output path, for any **non-index** phase output that exists but is whitespace-only.

- [ ] **Step 1: Write the failing test**

Create `state/tests/test_integrity.py`:

```python
from state.integrity import Issue, check_integrity


def test_clean_engagement_has_no_issues(engagement):
    root = engagement(**{
        "scope.md": "# Scope\nReal content.\n",
        "context.md": "# Context\nReal content.\n",
    })
    assert check_integrity(root) == []


def test_empty_non_index_output_is_surface(engagement):
    root = engagement(**{"scope.md": "   \n"})  # whitespace only
    issues = check_integrity(root)
    assert issues == [Issue("empty_output", "scope.md", "surface", issues[0].detail)]
    assert issues[0].detail  # non-empty plain-language message


def test_absent_output_is_not_flagged(engagement):
    root = engagement()  # nothing written
    assert check_integrity(root) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.integrity'`.

- [ ] **Step 3: Create the module with the skeleton + `empty_output`**

Create `state/integrity.py`:

```python
"""Partial-state integrity checks over an engagement folder.

Pure functions of the filesystem — no network, no subprocess, no mutation.
Detects and classifies inconsistencies the existence-only phase check in
state.state cannot see (truncated outputs, index/body drift, bad model JSON,
absent results). Repair is the Conductor's job; this module only reports.

Companion to state.staleness (changed inputs) and state.conductor_state
(.conductor.md health) — neither condition is re-checked here.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by absolute path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state.phases import PHASES


@dataclass(frozen=True)
class Issue:
    kind: str
    target: str   # repo-relative path
    repair: str   # "auto" | "surface"
    detail: str


def check_integrity(root) -> list[Issue]:
    root = Path(root)
    issues: list[Issue] = []

    # empty_output: a non-index phase output exists but is blank.
    for p in PHASES:
        if p.output.endswith("/_index.md"):
            continue
        fp = root / p.output
        if fp.exists() and not fp.read_text(encoding="utf-8").strip():
            issues.append(Issue(
                "empty_output", p.output, "surface",
                f"The {p.name} step's output is there but empty — let's redo it.",
            ))

    issues.sort(key=lambda i: (i.target, i.kind))
    return issues
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add state/integrity.py state/tests/test_integrity.py
git commit -m "feat(state): integrity Issue + empty_output check (slice3 chunkA)"
```

---

### Task 3: `bad_json` + `results_missing` (model-input checks)

**Files:**
- Modify: `state/integrity.py`
- Test: `state/tests/test_integrity.py`

**Interfaces:**
- Consumes: `state.phases.MODEL_INPUTS` (dict of stem → key).
- Produces, inside `check_integrity`:
  - `bad_json`: `repair="surface"`, `target="model/<stem>.json"`, for any present `model/<stem>.json` (stem ∈ `MODEL_INPUTS`) that fails `json.loads`.
  - `results_missing`: `repair="auto"`, `target="model/results.json"`, when ≥1 `MODEL_INPUTS` stem file is present **and** `model/results.json` is absent. Partial inputs still fire (engine is PENDING-by-design).

- [ ] **Step 1: Write the failing test**

Append to `state/tests/test_integrity.py`:

```python
def test_bad_model_json_is_surface(engagement):
    root = engagement(**{"model/value.json": "{not valid json"})
    issues = check_integrity(root)
    kinds = {(i.kind, i.target, i.repair) for i in issues}
    assert ("bad_json", "model/value.json", "surface") in kinds


def test_partial_inputs_without_results_fire_results_missing(engagement):
    # Only baselines present (valid after Phase 4) and no results.json yet.
    root = engagement(**{"model/baselines.json": "[]"})
    issues = check_integrity(root)
    assert issues == [Issue("results_missing", "model/results.json", "auto",
                            issues[0].detail)]


def test_inputs_with_results_present_is_clean(engagement):
    root = engagement(**{
        "model/baselines.json": "[]",
        "model/results.json": "{}",
    })
    assert check_integrity(root) == []


def test_no_inputs_means_no_results_missing(engagement):
    root = engagement(**{"scope.md": "content"})
    assert check_integrity(root) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: FAIL — `test_bad_model_json_is_surface` and `test_partial_inputs_without_results_fire_results_missing` fail (no such issues produced yet).

- [ ] **Step 3: Add the model checks**

In `state/integrity.py`, update the import line and insert the model block **before** the `issues.sort(...)` line:

```python
from state.phases import MODEL_INPUTS, PHASES
```

```python
    # model/*.json: malformed inputs (surface) + absent results with inputs (auto).
    model = root / "model"
    any_input = False
    for stem in MODEL_INPUTS:
        mp = model / f"{stem}.json"
        if not mp.exists():
            continue
        any_input = True
        try:
            json.loads(mp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues.append(Issue(
                "bad_json", f"model/{stem}.json", "surface",
                f"The {stem} figures you entered aren't readable — I need them again.",
            ))
    if any_input and not (model / "results.json").exists():
        issues.append(Issue(
            "results_missing", "model/results.json", "auto",
            "The calculated numbers are missing — I can recompute them.",
        ))
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: PASS (all model tests, plus the Task 2 tests still green).

- [ ] **Step 5: Commit**

```bash
git add state/integrity.py state/tests/test_integrity.py
git commit -m "feat(state): integrity bad_json + results_missing checks (slice3 chunkA)"
```

---

### Task 4: Index/body drift — `index_missing_item`, `malformed_item`, `index_orphan_items`

**Files:**
- Modify: `state/integrity.py`
- Test: `state/tests/test_integrity.py`

**Interfaces:**
- Consumes: `state.phases.GATES`, `state.phases.PHASES`, `state.assembly._header_fields`.
- Produces, inside `check_integrity`:
  - `_folder_targets() -> list[tuple[str, bool]]` — `(folder_name, header_based)` for every folder-bearing phase/gate (output ends `/_index.md`).
  - `_index_ids(index_path) -> set[str]` — id-shaped first cells (`^[A-Z]+-\d+$`) of the index table.
  - `_body_ids(folder) -> set[str]` — id-shaped stems of `*.md` files (excluding `_index.md`).
  - `index_missing_item`: `repair="surface"`, `target="<folder>/_index.md"`, one per folder, when indexed ids have no body file. **All folders.**
  - `malformed_item`: `repair="surface"`, `target="<folder>/<id>.md"`, one per header-less body file. **Header-based folders only.**
  - `index_orphan_items`: `repair="auto"`, `target="<folder>/_index.md"`, one per folder, when body ids are not in the index (or the index is absent/empty) — **withheld if any `malformed_item` fired for that folder.** **Header-based folders only.**
  - `empty_output` for a folder index: `target="<folder>/_index.md"`, `repair="surface"`, only when the index exists, is blank, and there are **no** body files to rebuild from.

- [ ] **Step 1: Write the failing tests**

Append to `state/tests/test_integrity.py`. Helper builds an opportunity body with a valid extraction header:

```python
def _opp(idx, proc="PROC-001"):
    return (f"## OPP-{idx} — Example\n"
            f"<!-- index: id=OPP-{idx} process={proc} type=Augmentation "
            f"feasibility=Green data=Green grc=Green struct=addressing-root -->\n\n"
            f"Body text.\n")

_OPP_INDEX_HEADER = ("| OPP-ID | Process |\n| --- | --- |\n")


def test_orphan_body_not_in_index_is_auto(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER,         # lists nothing
        "opportunities/OPP-002.md": _opp("002"),
    })
    issues = check_integrity(root)
    assert Issue("index_orphan_items", "opportunities/_index.md", "auto",
                 issues_by_kind(issues, "index_orphan_items").detail) in issues


def test_absent_index_with_bodies_is_auto(engagement):
    root = engagement(**{
        "opportunities/OPP-001.md": _opp("001"),
        "opportunities/OPP-002.md": _opp("002"),
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_orphan_items", "opportunities/_index.md", "auto") in kinds


def test_indexed_item_with_no_body_is_surface(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER + "| OPP-009 | PROC-001 |\n",
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_missing_item", "opportunities/_index.md", "surface") in kinds


def test_headerless_body_is_malformed_and_withholds_orphan(engagement):
    root = engagement(**{
        "opportunities/_index.md": _OPP_INDEX_HEADER,
        "opportunities/OPP-002.md": _opp("002"),                  # orphan, valid header
        "opportunities/OPP-003.md": "## OPP-003 — No header\n\nbody\n",  # malformed
    })
    issues = check_integrity(root)
    kinds = {(i.kind, i.target) for i in issues}
    assert ("malformed_item", "opportunities/OPP-003.md") in kinds
    # orphan withheld for the whole folder because a malformed body is present
    assert not any(i.kind == "index_orphan_items" for i in issues)


def test_field_based_processes_skip_header_checks(engagement):
    # A valid Phase 4 body has NO id= header (index_from_fields), and is orphan-shaped.
    root = engagement(**{
        "processes/_index.md": "| PROC-ID | Process Name | Baseline |\n| --- | --- | --- |\n",
        "processes/PROC-001.md": "## PROC-001 — Staffing\n<!-- index: baseline=Ready -->\n\nbody\n",
    })
    issues = check_integrity(root)
    assert not any(i.kind == "malformed_item" for i in issues)
    assert not any(i.kind == "index_orphan_items" for i in issues)


def test_field_based_processes_still_flag_missing_item(engagement):
    root = engagement(**{
        "processes/_index.md": ("| PROC-ID | Process Name | Baseline |\n"
                                "| --- | --- | --- |\n| PROC-009 | Ghost | Ready |\n"),
    })
    kinds = {(i.kind, i.target, i.repair) for i in check_integrity(root)}
    assert ("index_missing_item", "processes/_index.md", "surface") in kinds


def test_issues_sorted_by_target_then_kind(engagement):
    root = engagement(**{
        "scope.md": "  ",                                         # empty_output (scope.md)
        "opportunities/_index.md": _OPP_INDEX_HEADER + "| OPP-009 | PROC-001 |\n",  # missing
    })
    issues = check_integrity(root)
    keys = [(i.target, i.kind) for i in issues]
    assert keys == sorted(keys)
```

Add this tiny helper near the top of the test file:

```python
def issues_by_kind(issues, kind):
    return next(i for i in issues if i.kind == kind)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: FAIL — the new drift tests fail (no drift detection yet).

- [ ] **Step 3: Add the drift detection**

In `state/integrity.py`, update the import to add `GATES` and `_header_fields`:

```python
from state.assembly import _header_fields
from state.phases import GATES, MODEL_INPUTS, PHASES
```

Add the module-level id pattern near the top (after imports):

```python
_ID_RE = re.compile(r"[A-Z]+-\d+$")
```

Add the two helpers above `check_integrity`:

```python
def _folder_targets() -> list[tuple[str, bool]]:
    """(folder_name, header_based) for every folder-bearing phase/gate."""
    out = []
    for entry in (*PHASES, *GATES):
        if entry.output.endswith("/_index.md"):
            out.append((entry.output[: -len("/_index.md")], entry.header_based))
    return out


def _index_ids(index_path: Path) -> set[str]:
    """Ids in an _index.md table: first cells matching <PREFIX>-<N>.

    Generalizes state.state's header/separator skip across all folders (which
    carry different headers, and usecase-briefs a title line) by taking only
    id-shaped cells — headers, separators, and prose never match.
    """
    ids: set[str] = set()
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells and _ID_RE.fullmatch(cells[0]):
            ids.add(cells[0])
    return ids


def _body_ids(folder: Path) -> set[str]:
    return {
        p.stem for p in folder.glob("*.md")
        if p.name != "_index.md" and _ID_RE.fullmatch(p.stem)
    }
```

Insert the per-folder block in `check_integrity` **before** `issues.sort(...)`:

```python
    # index/body drift, per folder-bearing phase/gate.
    for folder_name, header_based in _folder_targets():
        folder = root / folder_name
        index_path = folder / "_index.md"
        rel_index = f"{folder_name}/_index.md"
        body_ids = _body_ids(folder)
        index_nonempty = (
            index_path.exists() and bool(index_path.read_text(encoding="utf-8").strip())
        )
        index_ids = _index_ids(index_path) if index_nonempty else set()

        # truncated index with nothing to rebuild from -> surface.
        if index_path.exists() and not index_nonempty and not body_ids:
            issues.append(Issue(
                "empty_output", rel_index, "surface",
                f"The {folder_name.replace('-', ' ')} list is there but empty.",
            ))

        # indexed ids with no body file -> surface (all folders).
        missing = sorted(index_ids - body_ids)
        if missing:
            issues.append(Issue(
                "index_missing_item", rel_index, "surface",
                "Some items are listed but their details are missing: "
                + ", ".join(missing),
            ))

        if header_based:
            malformed = sorted(
                bid for bid in body_ids
                if not _header_fields((folder / f"{bid}.md").read_text(encoding="utf-8"))
            )
            for bid in malformed:
                issues.append(Issue(
                    "malformed_item", f"{folder_name}/{bid}.md", "surface",
                    "One item is incomplete and needs redoing.",
                ))
            orphan = sorted(body_ids - index_ids)
            if orphan and not malformed:
                issues.append(Issue(
                    "index_orphan_items", rel_index, "auto",
                    "Some finished items aren't in the list yet — I can re-add them.",
                ))
```

- [ ] **Step 4: Run the full integrity suite**

Run: `.venv/bin/python -m pytest state/tests/test_integrity.py -v`
Expected: PASS (all drift tests + Tasks 2–3 tests).

- [ ] **Step 5: Commit**

```bash
git add state/integrity.py state/tests/test_integrity.py
git commit -m "feat(state): integrity index/body drift + malformed_item (slice3 chunkA)"
```

---

### Task 5: CLI entry point — JSON output + exit codes

**Files:**
- Modify: `state/integrity.py`
- Test: `state/tests/test_integrity_cli.py`

**Interfaces:**
- Consumes: `check_integrity`, `Issue`.
- Produces: `main(argv=None) -> int` — prints `json.dumps([asdict(i) for i in issues], indent=2)` and returns `0` for a valid directory; prints an error to stderr and returns `2` when the path is not a directory. Mirrors `state.state.main`.

- [ ] **Step 1: Write the failing test**

Create `state/tests/test_integrity_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _run(args):
    return subprocess.run(
        [sys.executable, str(REPO / "state" / "integrity.py"), *args],
        capture_output=True, text=True,
    )


def test_cli_prints_json_and_exits_zero(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("   ")  # one empty_output
    res = _run([str(eng)])
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload == [{
        "kind": "empty_output", "target": "scope.md",
        "repair": "surface", "detail": payload[0]["detail"],
    }]


def test_cli_clean_folder_prints_empty_list(tmp_path):
    eng = tmp_path / "acme"
    eng.mkdir()
    (eng / "scope.md").write_text("real content")
    res = _run([str(eng)])
    assert res.returncode == 0
    assert json.loads(res.stdout) == []


def test_cli_non_directory_exits_two(tmp_path):
    res = _run([str(tmp_path / "does-not-exist")])
    assert res.returncode == 2
    assert "not a directory" in res.stderr
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest state/tests/test_integrity_cli.py -v`
Expected: FAIL — the script has no `main`/`__main__`, so it prints nothing and exits 0 with empty stdout (assertions fail).

- [ ] **Step 3: Add the CLI**

Append to `state/integrity.py`:

```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="state.integrity")
    parser.add_argument("engagement", type=Path, help="path to the engagement folder")
    args = parser.parse_args(argv)
    if not args.engagement.is_dir():
        print(f"not a directory: {args.engagement}", file=sys.stderr)
        return 2
    print(json.dumps([asdict(i) for i in check_integrity(args.engagement)], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the CLI tests**

Run: `.venv/bin/python -m pytest state/tests/test_integrity_cli.py -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add state/integrity.py state/tests/test_integrity_cli.py
git commit -m "feat(state): integrity CLI (JSON out, exit codes) (slice3 chunkA)"
```

---

### Task 6: Conductor wiring — "Resuming into a messy state" section + guards

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md`
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: the `state/integrity.py` CLI (`python3 <engine_root>/state/integrity.py <folder>`), the auto/surface classification, and existing repair primitives (`state.assembly.index_from_headers`, `engine/run.py`, `record_input_hashes`).
- Produces: a `## Resuming into a messy state` section with a fenced `<!-- resume-recovery-narration:start -->`/`:end` block, referenced from drive-loop step 1. Guarded by `tests/test_conductor_skill.py`.

- [ ] **Step 1: Write the failing guard tests**

Add to `tests/test_conductor_skill.py` — append `"## Resuming into a messy state"` to the `REQUIRED_HEADINGS` list, and add:

```python
def test_conductor_resume_recovery_section():
    sec = _section(SKILL.read_text(), "## Resuming into a messy state")
    # Runs the integrity checker by absolute path.
    assert "state/integrity.py" in sec
    # Distinguishes auto-repair from must-surface.
    assert "auto" in sec and "surface" in sec
    # Auto path reuses the existing assembly primitive, not a re-implementation.
    assert "index_from_headers" in sec
    # Surface path is a batched must-ask that does not advance.
    assert "must-ask" in sec
    # Jargon-free narration block is present and fenced.
    assert "<!-- resume-recovery-narration:start -->" in sec
    assert "<!-- resume-recovery-narration:end -->" in sec


def test_conductor_resume_recovery_runs_before_staleness():
    text = SKILL.read_text()
    # The drive loop references the recovery step before the staleness step.
    assert "Resuming into a messy state" in _section(text, "## The drive loop")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v`
Expected: FAIL — section heading missing; new tests fail.

- [ ] **Step 3: Add the section and the drive-loop reference**

In `skills/conducting-engagement/SKILL.md`, add a sentence to drive-loop **step 1** (the `Read state` step) right after the reconcile sentence, so the recovery runs before staleness (step 3):

```markdown
   After reconcile, **check for partial state** — see *Resuming into a messy state* —
   and clear it before staleness and step-selection.
```

Then add this new section immediately **before** the `## Staleness` section:

````markdown
## Resuming into a messy state

A session can end mid-write: a half-saved file, a fan-out that wrote some item
files before crashing, a hand-edit that left an input unreadable. Existence is
not completeness — so on every resume, before staleness and before picking the
next step, run the integrity check and clear what it finds.

1. **Detect:** `python3 <engine_root>/state/integrity.py <folder>` → a JSON list
   of issues, each with `kind`, `target`, `repair` (`auto` | `surface`), and a
   plain-language `detail`.
2. **Auto-repair silently** every `repair: "auto"` issue — these are
   deterministically re-derivable from sources, so no confirmation is needed:
   - `index_orphan_items` → rebuild that folder's `_index.md` from its item files
     with `state.assembly.index_from_headers` (the same primitive the fan-out
     merge uses, so the result is byte-identical to a fresh assembly). Use the
     folder's canonical column tuple (e.g. opportunities: `('OPP-ID', 'id')`, …).
   - `results_missing` → `python3 <engine_root>/engine/run.py <folder>/`, then
     `record_input_hashes` so staleness reads clean.
3. **Surface** every `repair: "surface"` issue as one **batched must-ask** in
   plain language — name what looks incomplete and that you'll redo it together.
   Do not advance past a surface issue (`empty_output`, `bad_json`,
   `index_missing_item`, `malformed_item`).
4. **Re-check:** run the checker again and confirm **only surface issues remain**
   — this catches an auto-repair that failed or introduced a new issue (cap at a
   second pass; if an `auto` issue persists, surface it rather than loop).

`processes/` (Phase 4) is field-based: its orphan auto-repair is deferred (it
needs `index_from_fields`), so a half-finished Phase 4 simply re-drives via the
normal step-selection — unchanged behavior.

Narrate jargon-free — no step, file, or id names:

<!-- resume-recovery-narration:start -->
> Picking up where we left off. A couple of things looked half-finished from
> last time — I've tidied up what I could rebuild automatically. One part didn't
> get saved completely; let's redo that quickly together before we go on.
<!-- resume-recovery-narration:end -->
````

- [ ] **Step 4: Run the guard tests + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS (new guards green; whole suite green).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): resume into a messy state — integrity-driven recovery (slice3 chunkA)"
```

---

## Final verification

- [ ] Run the whole suite: `.venv/bin/python -m pytest -q` — expect all green (287 existing + new).
- [ ] `python3 state/integrity.py sample-pso-delivery/` prints `[]` (the complete sample has no partial state) — a real-data smoke check.
