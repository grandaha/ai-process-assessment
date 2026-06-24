# Remove the Excel Workbook Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Excise the `financial-model.xlsx` workbook export, its `openpyxl` dependency, and every methodology instruction that references it — leaving `model/results.json` as the sole numeric artifact.

**Architecture:** The deterministic engine already writes `model/results.json` as the source of truth; the workbook was a derived, openpyxl-rendered copy gated behind a `--no-workbook` flag (made optional in #90). This plan deletes the workbook module, its lazy invocation in `run.py`, its tests, the dependency, and all prose/skill instructions that tell the AI to produce or link the xlsx. Correctness coverage is unchanged: the golden-number suite pins `results.json` directly.

**Tech Stack:** Python 3 (stdlib only on the engine path), pytest.

## Global Constraints

- **Golden numbers stay byte-identical.** `model/results.json` for the lattice fixture must not change. The round-at-each-step behavior in `engine/compute.py` is preserved — only its *comment* changes. No edit may alter any compute output.
- **Do NOT change `python -m engine.run` invocation style.** Rewriting to path-agnostic `python3 <root>/...` forms is a separate later chunk. This plan only removes xlsx / `--no-workbook` text; leave the `python -m …` form as-is everywhere.
- **Keep client-Excel sample content untouched.** `samples/pso-delivery-team/intake/interview-notes.md` and `samples/pso-delivery-team/intake/systems-and-data.md` reference the *client's* "Staffing Grid" Excel — legitimate domain content, not our artifact. Do not edit them. (`agents/opportunity-scorer.md` line 37 "excellent" is a false-positive substring — leave it.)
- **`requirements.txt` keeps `pyyaml`** (used by `tests/methodology_model.py`). Only `openpyxl` is removed.
- **`system-prompt.md` embeds the `using-methodology` body verbatim** (sync guard at `tests/test_guards.py:308`). Any edit to `skills/using-methodology/SKILL.md` must be mirrored character-for-character in `system-prompt.md`.
- **Backward-compat:** after Task 1, a stray `--no-workbook` arg is a silently-ignored no-op (it starts with `--`, so it is filtered out of positionals and otherwise ignored). No caller breaks during the transition.
- Run the full suite (`python -m pytest -q`) at each task's end; it must stay green (currently 211 passing, minus the workbook tests this plan deletes).

---

### Task 1: Remove the workbook from the engine runtime and its tests

**Files:**
- Modify: `engine/run.py` (docstring line 1; `main()` lines 85-107)
- Delete: `engine/workbook.py`
- Delete: `engine/tests/test_workbook.py`
- Delete: `engine/tests/test_workbook_equality.py`
- Modify/Test: `engine/tests/test_run.py:104-117`

**Interfaces:**
- Consumes: `build_results(model_dir) -> dict`, `main(argv=None) -> int` (unchanged signatures).
- Produces: `main()` writes only `model/results.json` and returns 0; no `.xlsx` is ever created. `engine.workbook` no longer exists — nothing may import it after this task.

- [ ] **Step 1: Replace the two workbook tests in `engine/tests/test_run.py` with a no-xlsx test**

Delete these two existing tests (lines 104-117):

```python
def test_no_workbook_flag_skips_xlsx_but_writes_results(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    rc = main([str(eng), "--no-workbook"])
    assert rc == 0
    assert (eng / "model" / "results.json").exists()
    assert not (eng / "financial-model.xlsx").exists()


def test_default_run_still_writes_workbook(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    main([str(eng)])
    assert (eng / "financial-model.xlsx").exists()
```

Replace them with a single test:

```python
def test_run_writes_results_and_never_an_xlsx(tmp_path):
    eng = tmp_path / "engagement"
    shutil.copytree(FIXTURE, eng / "model")
    rc = main([str(eng)])
    assert rc == 0
    assert (eng / "model" / "results.json").exists()
    assert list(eng.glob("*.xlsx")) == []
```

- [ ] **Step 2: Run the new test — it fails because the default run still writes the xlsx**

Run: `python -m pytest engine/tests/test_run.py::test_run_writes_results_and_never_an_xlsx -v`
Expected: FAIL — `assert list(eng.glob("*.xlsx")) == []` fails (a `financial-model.xlsx` is produced).

- [ ] **Step 3: Strip the workbook block from `engine/run.py`**

Change the module docstring's first line from:

```python
"""CLI / module entry: read model/*.json -> compute -> write results.json + .xlsx.
```

to:

```python
"""CLI / module entry: read model/*.json -> compute -> write results.json.
```

Replace the entire `main()` body (lines 85-107) with:

```python
def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    positional = [a for a in argv if not a.startswith("--")]
    if not positional:
        print("usage: python -m engine.run <engagement-folder>/", file=sys.stderr)
        return 2
    engagement = Path(positional[0])
    model_dir = engagement / "model"
    results = build_results(model_dir)
    (model_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0
```

(Leave the top-level imports of `engine.compute` and `engine.model` unchanged — `build_results` still uses `load_inputs`.)

- [ ] **Step 4: Delete the workbook module and its two test files**

```bash
git rm engine/workbook.py engine/tests/test_workbook.py engine/tests/test_workbook_equality.py
```

- [ ] **Step 5: Run the engine test suite — all green, no xlsx**

Run: `python -m pytest engine/tests -q`
Expected: PASS. The new `test_run_writes_results_and_never_an_xlsx` passes; no test imports `engine.workbook`.

- [ ] **Step 6: Commit**

```bash
git add engine/run.py engine/tests/test_run.py
git commit -m "refactor(engine): drop financial-model.xlsx workbook export"
```

---

### Task 2: Simplify the stdlib-core guard test

**Files:**
- Modify/Test: `engine/tests/test_stdlib_core.py`

**Interfaces:**
- Consumes: `engine.run.main` under a meta_path import blocker for `yaml`/`openpyxl`/`formulas`.
- Produces: a guard proving the core path runs with no third-party deps and never reaches for `openpyxl`/`formulas`.

- [ ] **Step 1: Delete the now-obsolete "degrades without openpyxl" test**

There is no longer a default workbook path, so remove this whole test from `engine/tests/test_stdlib_core.py`:

```python
def test_engine_run_default_path_degrades_without_openpyxl(tmp_path):
    model = _seed_model(tmp_path)
    script = f'''
from engine.run import main
rc = main([{str(tmp_path)!r}])  # no --no-workbook
assert rc == 0, rc
from pathlib import Path
assert (Path({str(model)!r}) / "results.json").exists()
assert not (Path({str(tmp_path)!r}) / "financial-model.xlsx").exists()
print("OK")
'''
    res = _run(script)
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout
```

- [ ] **Step 2: Drop the dead `--no-workbook` arg from the core-path test**

In `test_engine_run_core_path_needs_no_third_party_deps`, change:

```python
rc = main([{str(tmp_path)!r}, "--no-workbook"])
```

to:

```python
rc = main([{str(tmp_path)!r}])
```

(Leave `_BLOCKED = {"yaml", "openpyxl", "formulas"}` as-is — keeping `openpyxl`/`formulas` blocked is now a regression guard: if anyone re-adds a workbook import to `run.py`, this test fails.)

- [ ] **Step 3: Run the stdlib guard — green**

Run: `python -m pytest engine/tests/test_stdlib_core.py -v`
Expected: PASS — `test_engine_run_core_path_needs_no_third_party_deps` and `test_conductor_state_needs_no_yaml` pass; the deleted test is gone.

- [ ] **Step 4: Commit**

```bash
git add engine/tests/test_stdlib_core.py
git commit -m "test(engine): simplify stdlib-core guard after workbook removal"
```

---

### Task 3: Drop the openpyxl dependency and reword engine comments

**Files:**
- Modify: `requirements.txt`
- Modify: `.github/dependabot.yml:15`
- Modify: `engine/compute.py:52-53`
- Modify: `engine/model.py:8`

**Interfaces:**
- Produces: a dependency set with no `openpyxl`; engine comments that no longer mention the workbook. No behavior change.

- [ ] **Step 1: Remove `openpyxl` from `requirements.txt`**

Change the file from:

```
pytest>=9.0.3
pyyaml>=6.0.3
openpyxl>=3.1.5
```

to:

```
pytest>=9.0.3
pyyaml>=6.0.3
```

- [ ] **Step 2: Update the dependabot comment**

In `.github/dependabot.yml`, change line 15 from:

```
  # Engine runtime/test deps (openpyxl, formulas, pytest, pyyaml).
```

to:

```
  # Engine runtime/test deps (pytest, pyyaml).
```

- [ ] **Step 3: Reword the rounding comment in `engine/compute.py`**

Change lines 52-53 from:

```python
    # Round at each step from rounded predecessors so the workbook (whose cells
    # reference other rounded cells) reproduces these figures exactly.
```

to:

```python
    # Round at each step from rounded predecessors so each displayed total
    # equals the sum of the rounded line items above it (no penny drift).
```

(The rounding *behavior* is unchanged — only the comment.)

- [ ] **Step 4: Reword the PENDING comment in `engine/model.py`**

Change line 8 from:

```python
# Never replaced by a fabricated number — surfaced as-is in results.json and the workbook.
```

to:

```python
# Never replaced by a fabricated number — surfaced as-is in results.json.
```

- [ ] **Step 5: Run the full suite + confirm golden numbers unchanged**

Run: `python -m pytest -q`
Expected: PASS. In particular `engine/tests/test_lattice_golden.py` passes — `results.json` is byte-identical (comment-only edits).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .github/dependabot.yml engine/compute.py engine/model.py
git commit -m "build: drop openpyxl dependency; reword workbook comments"
```

---

### Task 4: Purge the workbook from `building-deliverable` and flip its guard

**Files:**
- Modify: `skills/building-deliverable/SKILL.md:231`
- Modify/Test: `tests/test_guards.py:272-274`

**Interfaces:**
- Consumes: `REPO_ROOT` (already imported in `tests/test_guards.py`).
- Produces: a guard `test_deliverable_has_no_workbook_reference` asserting the deliverable skill never mentions the xlsx.

- [ ] **Step 1: Flip the deliverable guard to assert absence**

In `tests/test_guards.py`, replace:

```python
def test_deliverable_links_workbook():
    deliv = (REPO_ROOT / "skills" / "building-deliverable" / "SKILL.md").read_text()
    assert "financial-model.xlsx" in deliv
```

with:

```python
def test_deliverable_has_no_workbook_reference():
    deliv = (REPO_ROOT / "skills" / "building-deliverable" / "SKILL.md").read_text()
    assert "financial-model.xlsx" not in deliv
    assert "workbook" not in deliv.lower()
```

- [ ] **Step 2: Run the flipped guard — it fails because the skill still links the xlsx**

Run: `python -m pytest tests/test_guards.py::test_deliverable_has_no_workbook_reference -v`
Expected: FAIL — `"financial-model.xlsx" not in deliv` fails (line 231 still references it).

- [ ] **Step 3: Remove the workbook sentence from `building-deliverable/SKILL.md`**

Change line 231 from:

```
Link `financial-model.xlsx` as a downloadable artifact in the HTML deliverable (e.g. in the investment/roadmap section), and pull all headline figures from `model/results.json` — renderers cite computed results, they never recompute. The workbook lets a skeptical reviewer inspect and flex the math.
```

to:

```
Pull all headline figures from `model/results.json` — renderers cite computed results, they never recompute. A skeptical reviewer can re-run the deterministic engine against `model/*.json` to verify every figure.
```

- [ ] **Step 4: Run the flipped guard — green**

Run: `python -m pytest tests/test_guards.py::test_deliverable_has_no_workbook_reference -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/building-deliverable/SKILL.md tests/test_guards.py
git commit -m "docs(deliverable): remove workbook link; guard its absence"
```

---

### Task 5: Purge the workbook from all remaining docs and lock it with a guard

**Files:**
- Modify: `README.md:31,94,103`
- Modify: `INSTALL.md:86,182,209,213`
- Modify: `system-prompt.md:75,87,144`
- Modify: `skills/using-methodology/SKILL.md:69,81,138`
- Modify: `skills/building-business-case/SKILL.md:27,128,143`
- Modify: `skills/collecting-cost-actuals/SKILL.md:102`
- Modify: `skills/conducting-engagement/SKILL.md:26`
- Modify: `skills/identifying-opportunities/SKILL.md:44,53`
- Modify: `skills/scoring-opportunities/SKILL.md:99`
- Modify/Test: `tests/test_guards.py` (add two guards)
- Modify: `CHANGELOG.md` (Unreleased)

**Interfaces:**
- Produces: guards `test_methodology_docs_have_no_workbook_references` and `test_openpyxl_not_a_dependency`.

- [ ] **Step 1: Add the two lock guards to `tests/test_guards.py`**

Append:

```python
def test_methodology_docs_have_no_workbook_references():
    targets = [
        "README.md", "INSTALL.md", "system-prompt.md",
        "skills/using-methodology/SKILL.md",
        "skills/building-business-case/SKILL.md",
        "skills/collecting-cost-actuals/SKILL.md",
        "skills/conducting-engagement/SKILL.md",
        "skills/identifying-opportunities/SKILL.md",
        "skills/scoring-opportunities/SKILL.md",
    ]
    for rel in targets:
        text = (REPO_ROOT / rel).read_text()
        assert "financial-model.xlsx" not in text, rel
        assert "--no-workbook" not in text, rel


def test_openpyxl_not_a_dependency():
    assert "openpyxl" not in (REPO_ROOT / "requirements.txt").read_text()
```

- [ ] **Step 2: Run the new guards — they fail (docs still reference the xlsx)**

Run: `python -m pytest tests/test_guards.py::test_methodology_docs_have_no_workbook_references -v`
Expected: FAIL — the first target still contains `financial-model.xlsx`.

- [ ] **Step 3: Edit `README.md`**

Line 31 — remove the workbook sentence. Change:

```
or a value computed by the deterministic Python engine in `engine/` (`python -m engine.run <engagement-folder>/`) and read back from `model/results.json`. The engine also emits `financial-model.xlsx`, an auditable workbook with live formulas that opens and recomputes in Excel, Google Sheets, and Apple Numbers. `model/*.json` is the single source of truth;
```

to:

```
or a value computed by the deterministic Python engine in `engine/` (`python -m engine.run <engagement-folder>/`) and read back from `model/results.json`. `model/*.json` is the single source of truth;
```

Line 94 — change `model, compute, workbook, run + tests` to `model, compute, run + tests`.

Line 103 — change `engine deps (openpyxl, formulas, pytest, pyyaml)` to `engine deps (pytest, pyyaml)`.

- [ ] **Step 4: Edit `INSTALL.md`**

Line 86 — change:

```
Because Cowork can execute code and touch local files, the deterministic math engine and the `financial-model.xlsx` workbook work fully here.
```

to:

```
Because Cowork can execute code and touch local files, the deterministic math engine works fully here.
```

Line 182 — change the Phase 9 row from:

```
| 9 — Business Case | `business-case.md`, `model/` (inputs + `results.json`), `financial-model.xlsx` |
```

to:

```
| 9 — Business Case | `business-case.md`, `model/` (inputs + `results.json`) |
```

Line 209 — change `pip install -r requirements.txt   # openpyxl, pytest, formulas` to `pip install -r requirements.txt   # pytest, pyyaml`.

Line 213 — change `runs `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`.` to `runs `python -m engine.run <engagement-folder>/` to produce `model/results.json`.`

- [ ] **Step 5: Edit `skills/using-methodology/SKILL.md` AND `system-prompt.md` with identical text**

> The sync guard (`tests/test_guards.py:308`) requires the `using-methodology` body to appear verbatim in `system-prompt.md`. Make these three edits identically in BOTH files (`using-methodology` lines 69/81/138, `system-prompt` lines 75/87/144).

Edit A — change:

```
`model/*.json` is the single source of truth for every number; `results.json` and `financial-model.xlsx` are both derived from it.
```

to:

```
`model/*.json` is the single source of truth for every number; `results.json` is derived from it.
```

Edit B — change:

```
`model/results.json` and `financial-model.xlsx` are derived outputs, regenerated by `python -m engine.run` — never hand-edited.
```

to:

```
`model/results.json` is a derived output, regenerated by `python -m engine.run` — never hand-edited.
```

Edit C — delete this bullet line entirely:

```
- `financial-model.xlsx` — auditable workbook with live formulas (Apple Numbers / Google Sheets compatible)
```

- [ ] **Step 6: Edit `skills/building-business-case/SKILL.md`**

Line 27 — change:

```
2. **Run the engine:** `python -m engine.run <engagement-folder>/`. This reads the input files, writes `model/results.json`, and produces `financial-model.xlsx` (the CFO-facing workbook is a Phase 9 deliverable).
```

to:

```
2. **Run the engine:** `python -m engine.run <engagement-folder>/`. This reads the input files and writes `model/results.json`.
```

Line 128 — change `Run `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`` to `Run `python -m engine.run <engagement-folder>/` to produce `model/results.json``.

Line 143 — change `Then run `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`. Then, for each Wave 1 initiative` to `Then run `python -m engine.run <engagement-folder>/` to produce `model/results.json`. Then, for each Wave 1 initiative`.

- [ ] **Step 7: Edit `skills/collecting-cost-actuals/SKILL.md`**

Line 102 — change `it will render as PENDING in the business case and the workbook until supplied` to `it will render as PENDING in the business case until supplied`.

- [ ] **Step 8: Edit `skills/conducting-engagement/SKILL.md` (xlsx clause only)**

> Remove ONLY the openpyxl/formulas/workbook clause. Leave the `pyyaml` prerequisite wording for the portability chunk to overhaul.

Lines 25-27 — change:

```
modules need third-party deps — `state.conductor_state`/`overrides`/`staleness` import
`pyyaml`; `engine.run`/`engine.workbook` import `openpyxl` + `formulas`. A bare
`python`/`python3` without them will fail at first contact. Once per machine:
```

to:

```
modules need third-party deps — `state.conductor_state`/`overrides`/`staleness` import
`pyyaml`. A bare `python`/`python3` without it will fail at first contact. Once per machine:
```

- [ ] **Step 9: Edit `skills/identifying-opportunities/SKILL.md`**

Line 44 — change `Then run `python -m engine.run <engagement-folder>/ --no-workbook` (see Phase-5 note below) and cite` to `Then run `python -m engine.run <engagement-folder>/` and cite`.

Line 53 — delete the entire Phase-5 note paragraph:

```
**Phase-5 note — `--no-workbook`.** Phase 5 runs the engine only to compute the value ranges into `results.json`; it must **not** emit the CFO workbook. Always pass `--no-workbook`: `python -m engine.run <engagement-folder>/ --no-workbook`. `financial-model.xlsx` is a Phase 9 deliverable produced once costs, scores, and wave assignments exist — running the full engine here would write a workbook full of PENDING cost and score cells.
```

- [ ] **Step 10: Edit `skills/scoring-opportunities/SKILL.md`**

Line 99 — change `The full engine run (which produces `model/results.json` and `financial-model.xlsx`) happens in Phase 9` to `The full engine run (which produces `model/results.json`) happens in Phase 9`.

- [ ] **Step 11: Run the lock guards + sync guard — green**

Run: `python -m pytest tests/test_guards.py -q`
Expected: PASS — `test_methodology_docs_have_no_workbook_references`, `test_openpyxl_not_a_dependency`, and the system-prompt sync guard all pass (using-methodology edits were mirrored exactly in system-prompt.md).

- [ ] **Step 12: Add the CHANGELOG entry**

Under `## [Unreleased]` in `CHANGELOG.md`, add:

```markdown
### Removed
- Excel/CFO workbook export (`financial-model.xlsx`) and the `openpyxl` dependency. Correctness is proven by the deterministic engine plus the audit chain; every figure lives in `model/results.json`. The `--no-workbook` flag is gone (a stray `--no-workbook` is now a silently-ignored no-op).
```

- [ ] **Step 13: Run the full suite — all green**

Run: `python -m pytest -q`
Expected: PASS.

- [ ] **Step 14: Commit**

```bash
git add README.md INSTALL.md system-prompt.md skills/ tests/test_guards.py CHANGELOG.md
git commit -m "docs: purge financial-model.xlsx from methodology; guard its absence"
```

---

## Self-Review

**1. Spec coverage** (against the removal directive "no Excel at all"):
- Engine runtime xlsx → Task 1 (run.py, workbook.py). ✓
- Workbook tests → Task 1 (deleted) + Task 2 (stdlib guard). ✓
- openpyxl dependency → Task 3 (requirements, dependabot). ✓
- Engine comments → Task 3. ✓
- Deliverable link + guard → Task 4. ✓
- All skill/doc prose + `--no-workbook` text → Task 5. ✓
- Lock guards (docs + dependency) → Task 5. ✓
- Client-Excel samples preserved → Global Constraints (untouched). ✓

**2. Placeholder scan:** none — every edit shows exact before/after text and exact commands.

**3. Consistency:** `main()`'s positional filter (`a.startswith("--")`) makes a stray `--no-workbook` a no-op, consistent with the backward-compat constraint. The `using-methodology` ↔ `system-prompt.md` edits are specified as identical to satisfy the verbatim sync guard. `test_openpyxl_not_a_dependency` (Task 5) aligns with the `openpyxl` line removed in Task 3.
