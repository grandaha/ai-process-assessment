# Attribute-Based Deterministic AI-Capability Tagging — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace human-authored Green/Yellow/Red step tags with factual step *attributes* (a fixed vocabulary) that a deterministic engine converts to a color, authored in a separate evidence-cited pass — removing the anchoring bias where the verdict contaminates the step description.

**Architecture:** A new stdlib module `state/capability.py` owns the vocabulary, the two-axis color rule, the `Step capability` table parser (reusing `checkpoint_doc.md_table`), the consecutive-Green chain computation, and validation. Phase 4 authoring is split into two passes (map → capability); Phase 5/6 consume the computed values; the owner renderer keeps the capability table out.

**Tech Stack:** Python stdlib only (`re`). Tests: pytest, run with `python3.13`. Skill/agent changes are Markdown.

## Global Constraints

- Stdlib only — no new dependencies. Pure functions in `state/capability.py`.
- Run tests with: `PYTHONPATH=. python3.13 -m pytest` (python3.14 has broken pyexpat in this env).
- Fixed vocabulary — **enablers:** `structured-data`, `rule-based`, `templated`, `ai-inference`, `accuracy-bounded`; **blockers:** `human-judgment`, `relationship`, `external-dependency`, `physical`, `regulatory-signoff`. An attribute outside this set is a defect.
- Color rule: `has_blocker` = any blocker attribute present **OR** (`ai-inference` present without `accuracy-bounded`). Green = enabler & not has_blocker; Yellow = enabler & has_blocker; Red = has_blocker & no enabler. `accuracy-bounded` without `ai-inference` is a defect. A step with no enabler and no blocker is a defect.
- No `Green/Yellow/Red` token is ever authored by a human — colors are computed only.
- Reuse `checkpoint_doc.md_table()` — do not write a new pipe-table parser.
- The `Step capability` table is assessor-only — it must never appear in the owner process-validation doc.
- `state/capability.py` reads only the prose process files; it touches no `model/*.json` and does not import the financial `engine/`.

---

### Task 1: `state/capability.py` — vocabulary, color rule, parser, chains, validation

**Files:**
- Create: `state/capability.py`
- Test: `state/tests/test_capability.py`

**Interfaces:**
- Consumes: `state.checkpoint_doc.md_table(md) -> (header: list[str], rows: list[list[str]])`.
- Produces:
  - `ENABLERS: set[str]`, `BLOCKERS: set[str]`, `VOCABULARY: set[str]`
  - `compute_color(attributes: Iterable[str]) -> str` — `"Green"|"Yellow"|"Red"`; raises `ValueError` on unknown attr, `accuracy-bounded` without `ai-inference`, or empty/no-enabler-no-blocker.
  - `parse_step_capability(proc_md: str) -> dict[int, dict]` — `{step_no: {"attributes": list[str], "evidence": str}}`.
  - `step_colors(proc_md: str) -> dict[int, str]` — `{step_no: color}` for every capability row.
  - `compute_chains(colors_by_step: dict[int, str]) -> list[tuple[int, int]]` — runs of ≥2 consecutive Green steps as inclusive `(start, end)`.
  - `validate(proc_md: str) -> list[str]` — human-readable defect messages; empty list = valid.

- [ ] **Step 1: Write the failing tests**

Create `state/tests/test_capability.py`:

```python
import pytest
from state import capability as cap

# --- compute_color: the two-axis rule ---
@pytest.mark.parametrize("attrs,expected", [
    (["structured-data", "rule-based"], "Green"),
    (["templated"], "Green"),
    (["ai-inference", "accuracy-bounded"], "Green"),
    (["structured-data", "human-judgment"], "Yellow"),
    (["ai-inference"], "Yellow"),                      # lone ai-inference -> implicit verify blocker
    (["ai-inference", "human-judgment"], "Yellow"),
    (["external-dependency"], "Red"),
    (["relationship", "regulatory-signoff"], "Red"),
])
def test_compute_color(attrs, expected):
    assert cap.compute_color(attrs) == expected

def test_compute_color_unknown_attribute_raises():
    with pytest.raises(ValueError):
        cap.compute_color(["structured-data", "magic"])

def test_compute_color_accuracy_bounded_requires_ai_inference():
    with pytest.raises(ValueError):
        cap.compute_color(["accuracy-bounded", "structured-data"])

def test_compute_color_empty_raises():
    with pytest.raises(ValueError):
        cap.compute_color([])

# --- parse_step_capability + step_colors ---
PROC = """## PROC-001 — Onboarding

**Steps:**
1. Re-keys client details into Teamwork
2. Waits for the client to provide materials
3. Reviews assets and decides whether to proceed

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | both systems API-available |
| 2 | external-dependency | operator: we wait on the client |
| 3 | structured-data, human-judgment | operator: I decide if there is enough |

**Baselines**

| Field | Value |
|---|---|
| Volume | 7/mo |
"""

def test_parse_step_capability():
    parsed = cap.parse_step_capability(PROC)
    assert set(parsed) == {1, 2, 3}
    assert parsed[1]["attributes"] == ["structured-data", "rule-based"]
    assert parsed[2]["evidence"] == "operator: we wait on the client"

def test_step_colors():
    assert cap.step_colors(PROC) == {1: "Green", 2: "Red", 3: "Yellow"}

def test_parse_ignores_unrelated_tables():
    # the Baselines table must not leak into the capability parse
    parsed = cap.parse_step_capability(PROC)
    assert "Volume" not in repr(parsed)

# --- compute_chains ---
def test_compute_chains_consecutive_green_runs():
    colors = {1: "Green", 2: "Green", 3: "Green", 4: "Red", 5: "Green", 6: "Green"}
    assert cap.compute_chains(colors) == [(1, 3), (5, 6)]

def test_compute_chains_single_green_is_not_a_chain():
    assert cap.compute_chains({1: "Green", 2: "Red", 3: "Green"}) == []

# --- validate ---
def test_validate_clean_proc_has_no_defects():
    assert cap.validate(PROC) == []

def test_validate_flags_missing_evidence():
    bad = PROC.replace("| 1 | structured-data, rule-based | both systems API-available |",
                       "| 1 | structured-data, rule-based |  |")
    defects = cap.validate(bad)
    assert any("evidence" in d.lower() and "1" in d for d in defects)

def test_validate_flags_step_capability_mismatch():
    # drop the capability row for step 3 -> bijection broken
    bad = PROC.replace("| 3 | structured-data, human-judgment | operator: I decide if there is enough |\n", "")
    defects = cap.validate(bad)
    assert any("3" in d for d in defects)

def test_validate_flags_unknown_attribute():
    bad = PROC.replace("structured-data, rule-based", "structured-data, magic")
    assert any("magic" in d for d in cap.validate(bad))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONPATH=. python3.13 -m pytest state/tests/test_capability.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'state.capability'`.

- [ ] **Step 3: Implement `state/capability.py`**

```python
# state/capability.py — deterministic AI-capability tagging from factual step attributes (#186).
# Stdlib only. No fabrication: the color is COMPUTED from recorded attributes; no human authors a
# color. See docs/superpowers/specs/2026-06-29-attribute-based-capability-tagging-design.md.
import re

from state.checkpoint_doc import md_table

ENABLERS = {"structured-data", "rule-based", "templated", "ai-inference", "accuracy-bounded"}
BLOCKERS = {"human-judgment", "relationship", "external-dependency", "physical", "regulatory-signoff"}
VOCABULARY = ENABLERS | BLOCKERS

def compute_color(attributes):
    """Two-axis rule. Green = enabler & no blocker; Yellow = enabler & blocker; Red = blocker & no
    enabler. ai-inference contributes an implicit verification blocker unless accuracy-bounded is
    present. Raises ValueError on an invalid attribute set."""
    attrs = set(attributes)
    unknown = attrs - VOCABULARY
    if unknown:
        raise ValueError(f"unknown attribute(s): {sorted(unknown)}")
    if "accuracy-bounded" in attrs and "ai-inference" not in attrs:
        raise ValueError("accuracy-bounded requires ai-inference")
    has_enabler = bool(attrs & ENABLERS)
    has_blocker = bool(attrs & BLOCKERS) or ("ai-inference" in attrs and "accuracy-bounded" not in attrs)
    if not has_enabler and not has_blocker:
        raise ValueError("step has no enabler and no blocker")
    if has_enabler and not has_blocker:
        return "Green"
    if has_enabler and has_blocker:
        return "Yellow"
    return "Red"

def _section_body(md, label):
    # Body of a **Label:** section: inline text + following lines, to the next **Bold:** / ### / end.
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=^\*\*[^\n]+?:\*\*|^###\s|\Z)",
                  md, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""

def _step_numbers(proc_md):
    body = _section_body(proc_md, "Steps")
    return [int(m.group(1)) for m in re.finditer(r"^\s*(\d+)\.\s+", body, re.MULTILINE)]

def parse_step_capability(proc_md):
    """{step_no: {"attributes": [...], "evidence": str}} from the **Step capability:** table."""
    header, rows = md_table(_section_body(proc_md, "Step capability"))
    out = {}
    for r in rows:
        if not r or not r[0].strip().isdigit():
            continue
        attrs = [a.strip() for a in r[1].split(",") if a.strip()] if len(r) > 1 else []
        evidence = r[2].strip() if len(r) > 2 else ""
        out[int(r[0].strip())] = {"attributes": attrs, "evidence": evidence}
    return out

def step_colors(proc_md):
    """{step_no: color} for every capability row (computed)."""
    return {s: compute_color(row["attributes"]) for s, row in parse_step_capability(proc_md).items()}

def compute_chains(colors_by_step):
    """Runs of >=2 consecutive Green steps as inclusive (start, end). A non-Green or missing step
    number breaks a run."""
    runs, run = [], []
    prev = None
    for s in sorted(colors_by_step):
        contiguous = prev is None or s == prev + 1
        if colors_by_step[s] == "Green" and contiguous:
            run.append(s)
        elif colors_by_step[s] == "Green":
            if len(run) >= 2:
                runs.append((run[0], run[-1]))
            run = [s]
        else:
            if len(run) >= 2:
                runs.append((run[0], run[-1]))
            run = []
        prev = s
    if len(run) >= 2:
        runs.append((run[0], run[-1]))
    return runs

def validate(proc_md):
    """Defect messages (empty = valid): unknown/invalid attributes, missing evidence, empty
    attribute set, accuracy-bounded misuse, and Steps<->capability bijection breaks."""
    defects = []
    steps = set(_step_numbers(proc_md))
    cap_rows = parse_step_capability(proc_md)
    cap_steps = set(cap_rows)
    for s in sorted(steps - cap_steps):
        defects.append(f"step {s}: no Step capability row")
    for s in sorted(cap_steps - steps):
        defects.append(f"Step capability row {s}: no matching step")
    for s in sorted(cap_steps & steps):
        row = cap_rows[s]
        if not row["attributes"]:
            defects.append(f"step {s}: no attributes")
            continue
        if not row["evidence"]:
            defects.append(f"step {s}: attribute has no evidence")
        try:
            compute_color(row["attributes"])
        except ValueError as e:
            defects.append(f"step {s}: {e}")
    return defects
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONPATH=. python3.13 -m pytest state/tests/test_capability.py -q`
Expected: PASS (all tests).

- [ ] **Step 5: Run the full suite (no regressions)**

Run: `PYTHONPATH=. python3.13 -m pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add state/capability.py state/tests/test_capability.py
git commit -m "feat: state/capability.py — deterministic attribute-based capability tagging (#186)"
```

---

### Task 2: Phase 4 authoring — format + two-pass skill + slimmed mapper + new tagger agent

**Files:**
- Modify: `skills/discovering-processes/SKILL.md`
- Modify: `agents/process-mapper.md`
- Create: `agents/step-capability-tagger.md`
- Test: `tests/test_capability_methodology.py`

**Interfaces:**
- Consumes: the `state/capability.py` vocabulary (Task 1) — the agent docs must list the exact 10 attributes and the rule.
- Produces: the `**Step capability:**` table format that `state/capability.py` parses (columns `Step | Attributes | Evidence`); a `process-mapper` that emits steps-only; a `step-capability-tagger` agent.

- [ ] **Step 1: Write the failing test**

Create `tests/test_capability_methodology.py`:

```python
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
DISC = (REPO / "skills" / "discovering-processes" / "SKILL.md").read_text()
MAPPER = (REPO / "agents" / "process-mapper.md").read_text()
TAGGER = (REPO / "agents" / "step-capability-tagger.md")
ATTRS = ["structured-data", "rule-based", "templated", "ai-inference", "accuracy-bounded",
         "human-judgment", "relationship", "external-dependency", "physical", "regulatory-signoff"]

def test_mapper_no_longer_assigns_colors():
    low = MAPPER.lower()
    assert "green / yellow / red" not in low and "green/yellow/red" not in low
    assert "ai capability per step" not in low      # the old per-step color instruction is gone

def test_tagger_agent_exists_and_lists_vocabulary():
    assert TAGGER.exists(), "agents/step-capability-tagger.md missing"
    text = TAGGER.read_text()
    for a in ATTRS:
        assert a in text, f"tagger missing attribute {a}"
    assert "evidence" in text.lower()               # evidence-cited
    # the two named residual-bias boundaries must have guidance
    assert "ai-inference" in text and "rule-based" in text and "human-judgment" in text

def test_discovering_processes_documents_two_passes_and_table():
    assert "Step capability" in DISC                # the new table section
    for a in ATTRS:
        assert a in DISC, f"discovering-processes missing attribute {a}"
    assert "step-capability-tagger" in DISC         # pass 2 wired
    # no hand-authored colors / hand chain scan remain as authoring instructions
    assert "Green / Yellow / Red" not in DISC and "Green/Yellow/Red" not in DISC
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_capability_methodology.py -q`
Expected: FAIL — `agents/step-capability-tagger.md` missing; color strings still present.

- [ ] **Step 3: Create `agents/step-capability-tagger.md`**

Write a new agent doc with these sections (match the house style of `agents/process-mapper.md`):

- **Frontmatter:** `name: ai-process-assessment:step-capability-tagger`, a one-line description.
- **Role:** assign factual capability attributes to each *already-fixed* step; never edit step text; never write a color (the engine computes it).
- **Inputs:** the engagement folder, the process id, the path to `processes/PROC-NNN.md` (with the **final-numbered** Steps), and the interview evidence (`_staging/phase4/` notes or `evidence-log.md`).
- **The fixed vocabulary** — reproduce the table verbatim:

  | Attribute | Meaning | Class |
  |---|---|---|
  | `structured-data` | works on structured/digital data (fields, records, APIs) | enabler |
  | `rule-based` | deterministic logic — if/then, thresholds, lookups | enabler |
  | `templated` | templated/parameterized generation (standard emails, forms) | enabler |
  | `ai-inference` | extraction / classification / drafting from messy input | enabler (probabilistic) |
  | `accuracy-bounded` | a measurable accuracy threshold governs the AI output (valid only with `ai-inference`) | enabler (qualifier) |
  | `human-judgment` | discretion/interpretation/tradeoff a human makes each instance | blocker |
  | `relationship` | interpersonal — negotiation, trust, client management | blocker |
  | `external-dependency` | blocked on a party outside the firm | blocker |
  | `physical` | requires a real-world/offline act | blocker |
  | `regulatory-signoff` | a regulation/policy mandates a human be accountable | blocker |

- **Decision guidance for the two residual-bias boundaries** (with worked examples):
  - `ai-inference` vs `rule-based`: if the logic is deterministic (lookup/threshold/templated), use `rule-based`; if it requires probabilistic extraction/classification/generation from messy input, use `ai-inference` (and add `accuracy-bounded` only if a measurable accuracy/acceptance criterion is cited in evidence).
  - `human-judgment` vs `rule-based`: if a completeness/threshold check fully decides the outcome, it is `rule-based`; if a person must exercise discretion or weigh a tradeoff on each instance, it is `human-judgment`. (Worked: "PM decides if there's *enough* to proceed" → `human-judgment`; "system checks all required fields present" → `rule-based`.)
- **Output format** — append a `**Step capability:**` markdown table to `processes/PROC-NNN.md` (or write to the staging file the orchestrator assembles), one row per step:

  ```
  **Step capability:**
  | Step | Attributes | Evidence |
  |---|---|---|
  | 1 | structured-data, rule-based | both systems API-available (tech-inventory) |
  ```
- **Hard rules:** every step gets exactly one row (1:1 with the Steps list); every row cites evidence; only vocabulary attributes; never write Green/Yellow/Red.

- [ ] **Step 4: Slim `agents/process-mapper.md`**

Remove every instruction to assign AI capability / colors. Specifically (inventory all):
- Behavior step that says "mark AI-capable (Green) / Uncertain (Yellow) / Not AI-capable (Red)" → replace with "capture the step action only; do NOT assess AI capability — a separate `step-capability-tagger` pass does that."
- The field-schema row "AI capability per step | …" → remove.
- Any refusal rule / output-template line carrying `Green/Yellow/Red` → remove.
- The output-template step line `[step → Green/Yellow/Red, with what makes Red/Yellow hard]` → `[step action only]`.

- [ ] **Step 5: Update `skills/discovering-processes/SKILL.md`**

- Document Phase 4 as two passes: Pass 1 `process-mapper` (steps only) → orchestrator assembles + **final-numbers** the Steps → Pass 2 `step-capability-tagger` (per-process, parallel) assigns the `**Step capability:**` table.
- Add the vocabulary table (reproduce from Task 2 Step 3) and the computed-color rule (reference `state/capability.py`).
- Document the `**Step capability:**` table format.
- Remove the old per-step color instruction (checklist line "assign AI capability flag (Green/Yellow/Red)"), the hand-written **Chain scan** authoring step ("Run chain scan — identify consecutive Green runs…"), the "what stays in main context" chain-scan ownership line, and the fragmentation rationalization-table row that references hand counting — replacing the chain-scan checklist item with: "chains are computed deterministically by `state/capability.py` from the capability table; the value of a chain is assessed in Phase 5."
- Update the `PROC-NNN.md` **Key Outputs / template** so the Steps block is action-only and a `**Step capability:**` table follows. Leave the **Challenge hypothesis** section unchanged (it is separate from the chain scan).

- [ ] **Step 6: Run the test to verify it passes**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_capability_methodology.py -q`
Expected: PASS.

- [ ] **Step 7: Run the full suite + grep guard**

Run: `PYTHONPATH=. python3.13 -m pytest -q` → PASS.
Run: `grep -rniE "green ?/ ?yellow ?/ ?red" skills/discovering-processes/SKILL.md agents/process-mapper.md` → expected: no matches (no orphaned color instructions).

- [ ] **Step 8: Commit**

```bash
git add skills/discovering-processes/SKILL.md agents/process-mapper.md agents/step-capability-tagger.md tests/test_capability_methodology.py
git commit -m "feat: Phase 4 two-pass authoring — steps-only mapper + step-capability-tagger (#186)"
```

---

### Task 3: Phase 5 + Phase 6 consumption (computed colors/chains; FTE-derived chain value)

**Files:**
- Modify: `skills/identifying-opportunities/SKILL.md`
- Modify: `agents/opportunity-typer.md`
- Modify: `skills/scoring-opportunities/SKILL.md`
- Modify: `agents/opportunity-scorer.md`
- Test: extend `tests/test_capability_methodology.py`

**Interfaces:**
- Consumes: `state/capability.py` `step_colors()` / `compute_chains()` (computed), and `model/baselines.json` FTE (existing) for chain value.
- Produces: Phase 5/6 docs that read computed capability instead of prose colors + hand chain scan.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_capability_methodology.py`:

```python
IDENT = (REPO / "skills" / "identifying-opportunities" / "SKILL.md").read_text()
TYPER = (REPO / "agents" / "opportunity-typer.md").read_text()
SCORING = (REPO / "skills" / "scoring-opportunities" / "SKILL.md").read_text()
SCORER = (REPO / "agents" / "opportunity-scorer.md").read_text()

def test_phase5_reads_computed_capability():
    assert "state/capability" in IDENT or "state.capability" in IDENT
    # chain value derived from the FTE baseline (replacing the deleted per-checkpoint prose)
    assert "FTE" in IDENT and "baseline" in IDENT.lower()

def test_phase5_typer_uses_computed_chains():
    assert "state/capability" in TYPER or "state.capability" in TYPER

def test_phase6_consumes_computed_chains():
    assert "state/capability" in SCORING or "state.capability" in SCORING
    assert "state/capability" in SCORER or "state.capability" in SCORER
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_capability_methodology.py -q`
Expected: FAIL — the four docs don't yet reference `state/capability`.

- [ ] **Step 3: Update Phase 5 docs**

- `skills/identifying-opportunities/SKILL.md` + `agents/opportunity-typer.md`: where they currently "review the chain scan from `processes/PROC-NNN.md`" and read per-step colors, change to "read the **computed** per-step colors and consecutive-Green chains from `state/capability.py` (`step_colors`, `compute_chains`) — these are derived, not authored." For the **Chain formation** field's "current human effort at each eliminated checkpoint": specify it is **derived from the process FTE baseline** (`model/baselines.json` `fte`) allocated across the chain's eliminated steps, cited as the source — replacing the per-checkpoint effort the old chain-scan prose carried. Keep hypothesis-before-value unchanged.

- [ ] **Step 4: Update Phase 6 docs**

- `skills/scoring-opportunities/SKILL.md` + `agents/opportunity-scorer.md`: change the chain-scan input references (Value Potential, Execution Horizon) to consume the **computed** chains + the Phase-5-derived chain value, rather than the deleted prose chain-scan section.

- [ ] **Step 5: Run the test + full suite**

Run: `PYTHONPATH=. python3.13 -m pytest tests/test_capability_methodology.py -q` → PASS.
Run: `PYTHONPATH=. python3.13 -m pytest -q` → PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/identifying-opportunities/SKILL.md agents/opportunity-typer.md skills/scoring-opportunities/SKILL.md agents/opportunity-scorer.md tests/test_capability_methodology.py
git commit -m "feat: Phase 5/6 consume computed capability + FTE-derived chain value (#186)"
```

---

### Task 4: Owner-doc guard + integration on a new-format sample

**Files:**
- Test: `state/tests/test_capability_integration.py`
- (Only if the guard test fails) Modify: `state/process_review.py`

**Interfaces:**
- Consumes: `state.capability` (Task 1), `state.process_review.build_blocks` (existing renderer).
- Produces: proof that a new-format `PROC` computes the expected colors/chains and that the owner doc excludes the `Step capability` table.

- [ ] **Step 1: Write the failing test**

Create `state/tests/test_capability_integration.py`:

```python
from state import capability as cap
from state import process_review as pr

# A full new-format process: action-only Steps + a Step capability table (no colors authored).
PROC = """## PROC-001 — Client Onboarding

**Trigger:** A deal closes.

### Process Map

**Steps:**
1. Re-keys client details into Teamwork
2. Builds the task list from the Notion checklist
3. Waits for the client to provide materials
4. Reviews assets and decides whether to proceed

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | both systems API-available (tech-inventory) |
| 2 | structured-data, templated | Notion checklist is templated |
| 3 | external-dependency | operator: we wait on the client |
| 4 | structured-data, human-judgment | operator: I decide if there is enough |

**Actors:** PM team; HubSpot; Teamwork.
"""

def test_colors_and_chains_computed():
    assert cap.step_colors(PROC) == {1: "Green", 2: "Green", 3: "Red", 4: "Yellow"}
    assert cap.compute_chains(cap.step_colors(PROC)) == [(1, 2)]

def test_validate_clean():
    assert cap.validate(PROC) == []

def test_owner_doc_excludes_capability_table():
    blocks = pr.build_blocks(PROC)
    text = " ".join(b.get("text", "") + " ".join(b.get("items", [])) for b in blocks)
    assert "Step capability" not in text            # assessor-only
    for a in ("structured-data", "external-dependency", "human-judgment"):
        assert a not in text                        # no attributes leak into the owner doc
    # the clean step actions DO render
    assert any(b["type"] == "numbered_list" for b in blocks)
    steps = next(b for b in blocks if b["type"] == "numbered_list")
    assert steps["items"][0] == "Re-keys client details into Teamwork"
```

- [ ] **Step 2: Run the test to verify it fails (or surfaces a needed guard)**

Run: `PYTHONPATH=. python3.13 -m pytest state/tests/test_capability_integration.py -q`
Expected: `test_colors_and_chains_computed` and `test_validate_clean` FAIL only if Task 1 is incomplete (they should PASS). `test_owner_doc_excludes_capability_table`: if it FAILS because `build_blocks` renders the capability table or attributes, proceed to Step 3; if it PASSES (the renderer's field allowlist already excludes it), skip Step 3.

- [ ] **Step 3: (Conditional) guard the renderer**

Only if Step 2 showed leakage: in `state/process_review.py`, ensure `build_blocks` renders only the known owner fields (Trigger, Steps, Actors, Decision points, Exceptions, Upstream/downstream, Baselines, Sign-off) and never the `Step capability` section. (The current allowlist design should already do this — add an explicit skip only if a leak is observed.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `PYTHONPATH=. python3.13 -m pytest state/tests/test_capability_integration.py -q`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `PYTHONPATH=. python3.13 -m pytest -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add state/tests/test_capability_integration.py state/process_review.py
git commit -m "test: capability integration + owner-doc guard for new format (#186)"
```

---

## Self-Review

- **Spec coverage:** rule model + vocabulary (Task 1); two-pass authoring + format + slimmed mapper + new tagger (Task 2); Phase 5 *and* Phase 6 consumption + FTE-derived chain value (Task 3); owner-doc guard + integration + worked colors (Task 4). Validation/gate rules → `validate()` (Task 1) + grep guard (Task 2). `md_table` reuse → Task 1 Step 3. "Inventory every color/chain mention" → Task 2 Steps 4-5 + grep guard. Sample-intake generator note from the spec is **not** in scope of these tasks (the user is running a fresh test); flagged here so it is a conscious omission, not a gap.
- **Placeholder scan:** none — `state/capability.py` and all tests are complete code; doc tasks give exact edits + presence tests.
- **Type consistency:** `compute_color(attributes)->str`, `parse_step_capability->dict[int,dict]`, `step_colors->dict[int,str]`, `compute_chains(dict)->list[tuple]`, `validate->list[str]` are used consistently across Tasks 1/3/4. The `Step capability` table columns (`Step | Attributes | Evidence`) match between the tagger output (Task 2), the parser (Task 1), and the fixtures (Tasks 1/4).
