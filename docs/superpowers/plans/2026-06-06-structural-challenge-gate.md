# Structural-Challenge Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Phase 4 gate with a third clause — a per-process *challenge hypothesis* (first-order vs. second-order redesign) — and thread an `addressing-root` / `optimizing-around` / `not-applicable` signal from Phase 5 into the portfolio and roadmap views, annotation-only.

**Architecture:** Pure methodology-document change (markdown skills + agents). No runtime code. The validation surface is the static `tests/` pytest stack: each task adds a guard to `tests/test_guards.py` that asserts the instruction text is present, then the markdown edit makes it pass — TDD for documents, the established pattern in this repo (`SELF_READ_MARKER`, retired-file guards, etc.).

**Tech Stack:** Markdown (Claude Code skills/agents), pytest guards over the methodology model (`tests/methodology_model.py` fixture `methodology`).

**Source spec:** `docs/superpowers/specs/2026-06-06-structural-challenge-gate-design.md`

---

## Conventions for every task

- **Run tests with:** `/opt/homebrew/bin/python3.13 -m pytest -q` (system `python3` is 3.9 with no deps; `pytest` on PATH also works). Run from repo root.
- **Commit trailer (repo convention — all recent commits use it):**
  ```
  Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
  ```
- **Branch:** already on `feature/structural-challenge-gate`.
- New guards all go in `tests/test_guards.py`. Add this section header comment once, above the first new guard (Task 1):
  ```python
  # --- #10 structural-challenge gate (defends: first-order-only methodology, issue #10) ---
  # The Phase 4 gate gains a third clause (challenge hypothesis); Phase 5 emits a
  # struct= signal that threads to the portfolio and roadmap views. Annotation only.
  ```
- The `methodology` fixture exposes `.skills[skill_id].body` and `.agents[name].body` (full file text). Skill IDs are `ai-process-assessment:<dir>`; agent names are bare stems (e.g. `opportunity-typer`).

---

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `skills/discovering-processes/SKILL.md` | Phase 4: sponsor questions, gate rename + clause, schema field, assembly synthesis | 1, 2 |
| `agents/process-mapper.md` | R1 capture of sponsor structural input; gate-name rename | 1, 2 |
| `skills/using-methodology/SKILL.md` | Keystone: gate-name rename, rationalization row, Phase-4 note | 2, 6 |
| `skills/running-sample-engagement/SKILL.md` | Gate-name rename (one line) | 2 |
| `agents/opportunity-typer.md` | Phase 5: `Structural response` field + `struct=` token | 3 |
| `skills/identifying-opportunities/SKILL.md` | Phase 5: OPP entry field, index `Structural` column | 3 |
| `agents/opportunity-scorer.md` | Scores: reference label in Strategic Alignment rationale | 4 |
| `agents/section-renderer-portfolio.md` | Portfolio view: struct badge via existing join | 4 |
| `skills/prioritizing-roadmap/SKILL.md` | Roadmap: read struct, annotate `optimizing-around` items | 5 |
| `agents/section-renderer-roadmap.md` | Roadmap view: surface annotation on Wave-1 cards | 5 |
| `.claude-plugin/plugin.json`, `INSTALL.md` | Version bump 2.3.0 → 2.4.0 | 7 |
| `tests/test_guards.py` | New anti-regression guards | 1–6 |

---

### Task 1: Phase 4 capture — sponsor questions + process-mapper R1 field

**Files:**
- Modify: `skills/discovering-processes/SKILL.md` (Round 1 description, ~line 41)
- Modify: `agents/process-mapper.md` (Round 1 behavior, per-process entry, output template)
- Test: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guards**

Add to `tests/test_guards.py` (after the section-header comment from Conventions):

```python
def test_phase4_sponsor_round_has_structural_challenge(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    for marker in (
        "Is the process boundary right?",
        "Is the actor model right?",
        "Is the sequence right?",
    ):
        assert marker in body, f"Phase 4 Round 1 missing challenge question: {marker!r}"


def test_process_mapper_captures_sponsor_structural_input(methodology):
    body = methodology.agents["process-mapper"].body
    assert "Sponsor structural input" in body, \
        "process-mapper Round 1 must capture 'Sponsor structural input'"
```

- [ ] **Step 2: Run guards to verify they fail**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "structural_challenge or structural_input"`
Expected: 2 FAILED (markers not yet in the docs).

- [ ] **Step 3: Add the three challenge questions to Round 1**

In `skills/discovering-processes/SKILL.md`, replace the Round 1 list item (currently):

```
1. **Sponsor — strategic framing.** What does this process exist to achieve? What would success look like to the business?
```

with:

```
1. **Sponsor — strategic framing + structural challenge.** What does this process exist to achieve? What would success look like to the business? Then ask the three **structural challenge** questions, once per process the engagement will map. Ask the sponsor, not the operator — the operator will defend the current structure:
   - **Is the process boundary right?** Does the process exist because of a legacy constraint (system limitation, org structure, manual handoff) that AI could eliminate entirely — making the process *unnecessary* rather than faster?
   - **Is the actor model right?** Does the current allocation of steps to roles reflect what those roles should own, or what they were forced to own by capability limits that no longer apply?
   - **Is the sequence right?** Does the order of steps reflect a logical dependency, or a historical artifact of how information used to flow?
```

- [ ] **Step 4: Add Sponsor structural input capture to process-mapper (Round 1 only)**

In `agents/process-mapper.md`, in the Behavior section, replace the Round 1 bullet (currently):

```
- **Round 1 — Sponsor (strategic framing):** what the process exists to achieve, what success looks like to the business, constraints, and any baseline estimates the sponsor offered (mark these Low confidence unless system-sourced).
```

with:

```
- **Round 1 — Sponsor (strategic framing):** what the process exists to achieve, what success looks like to the business, constraints, and any baseline estimates the sponsor offered (mark these Low confidence unless system-sourced). **Also capture the sponsor's raw answers to the three structural challenge questions** (boundary / actor model / sequence) in a `Sponsor structural input` field per process. Capture the answers verbatim-in-substance; do NOT synthesize the final challenge hypothesis — that is the orchestrator's assembly judgment, like the baseline gate.
```

Then add a refusal rule. In the Refusal rules list, after the "Refuse to run the chain scan or apply the Baseline gate" line, add:

```
- Refuse to synthesize the final per-process challenge hypothesis — capture the sponsor's raw structural answers only (Round 1). Synthesis and the gate are main-context judgments at assembly.
```

Then add the field to the Round-1 output template. In the `## R<N>-P<k>` entry structure code block, after the `**AI capability per step:**` line, add:

```
**Sponsor structural input:** [Round 1 only — sponsor's raw answers to the boundary / actor model / sequence questions for this process] OR "not captured this round."
```

- [ ] **Step 5: Run guards to verify they pass**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "structural_challenge or structural_input"`
Expected: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add skills/discovering-processes/SKILL.md agents/process-mapper.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(phase4): capture sponsor structural-challenge answers (#10)

Round 1 sponsor interview gains the three structural challenge
questions (boundary / actor model / sequence); process-mapper captures
the raw answers in a Sponsor structural input field. Synthesis stays in
main context.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 2: Phase 4 gate rename + challenge clause + schema field + assembly synthesis

**Files:**
- Modify: `skills/discovering-processes/SKILL.md` (gate section, Key Outputs, Subagent Dispatch, checklist, rationalization, frontmatter)
- Modify: `agents/process-mapper.md` (3 rename occurrences + frontmatter shorthand)
- Modify: `skills/using-methodology/SKILL.md` (line 93 rename)
- Modify: `skills/running-sample-engagement/SKILL.md` (line 17 rename)
- Test: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guards**

Add to `tests/test_guards.py`:

```python
def _all_methodology_md_text() -> str:
    parts = []
    for path in _methodology_markdown_files():
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_phase4_gate_renamed_with_challenge_clause(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    assert "Baseline, Value & Challenge Gate" in body, \
        "Phase 4 gate must be renamed to 'Baseline, Value & Challenge Gate'"
    assert "challenge hypothesis unavailable" in body, \
        "Phase 4 gate must define the 'challenge hypothesis unavailable' remediation"


def test_process_map_schema_has_challenge_hypothesis(methodology):
    body = methodology.skills["ai-process-assessment:discovering-processes"].body
    assert "Challenge hypothesis" in body, \
        "process-map.md Key Outputs must include a Challenge hypothesis field"


def test_old_gate_name_fully_renamed():
    # Regression: the rename must be complete — the old proper-noun gate name
    # must appear nowhere in skills/ or agents/.
    assert "Baseline & Value Hypothesis" not in _all_methodology_md_text(), \
        "stale 'Baseline & Value Hypothesis' gate name remains after rename"
```

- [ ] **Step 2: Run guards to verify they fail**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "gate_renamed or challenge_hypothesis or fully_renamed"`
Expected: 3 FAILED.

- [ ] **Step 3: Rename the gate heading and add the challenge clause**

In `skills/discovering-processes/SKILL.md`, change the gate heading:

```
## Baseline & Value Hypothesis Gate
```

to:

```
## Baseline, Value & Challenge Gate
```

Then, at the end of that section — immediately after the line that ends `It is logged as "baseline unavailable" with a remediation action.` — add:

```

**Challenge clause (second-order check).** For every process mapped, `process-map.md` MUST also carry a **challenge hypothesis** (see Key Outputs). Automate a broken process and you get a faster broken process — this clause forces the question of whether the process structure itself is the constraint before any automation is typed. A process with no challenge hypothesis does not advance to Phase 5: it is logged as "challenge hypothesis unavailable" with a remediation action (return to the sponsor for the three structural questions), identically to a missing baseline. The hypothesis *surfaces* the redesign question; it does not solve it, and the signal it produces downstream annotates — it never blocks opportunity creation.
```

- [ ] **Step 4: Add the Challenge hypothesis field to process-map.md Key Outputs**

In the `### process-map.md` table, after the `| Chain scan | ... |` row, add:

```
| Challenge hypothesis | One paragraph per process, authored by the orchestrator at assembly from the sponsor's Round-1 structural answers. Either "structurally sound — [why]" or the single surfaced redesign question (boundary / actor model / sequence) with its basis. Surfaces the question; does not solve it. |
```

- [ ] **Step 5: Add the assembly synthesis step and checklist item**

In the Subagent Dispatch section, replace the "What stays in main context" bullet:

```
- **What stays in main context:** The Baseline & Value Hypothesis gate, the chain scan across the assembled map, and the conflict-resolution decision from Round 4. These are cross-round judgments and must not be delegated.
```

with:

```
- **What stays in main context:** The Baseline, Value & Challenge gate, the chain scan across the assembled map, the conflict-resolution decision from Round 4, and **synthesizing the per-process challenge hypothesis** from the Round-1 `Sponsor structural input` (one paragraph per process: structurally sound, or the single surfaced redesign question). These are cross-round judgments and must not be delegated.
```

In the Phase checklist, after the `- [ ] Apply Baseline & Value Hypothesis gate ...` line (which you will edit in Step 6), add a new checklist item:

```
- [ ] For every process, synthesize a challenge hypothesis from the sponsor's structural input; flag any process missing one as "challenge hypothesis unavailable"
```

- [ ] **Step 6: Rename the remaining occurrences (complete the rename)**

Make these exact replacements so `test_old_gate_name_fully_renamed` passes:

`skills/discovering-processes/SKILL.md`
- Frontmatter description: `Enforces Baseline & Value Hypothesis gate.` → `Enforces the Baseline, Value & Challenge gate.`
- Subagent Dispatch bullet: handled in Step 5.
- Checklist: `- [ ] Apply Baseline & Value Hypothesis gate — flag any process missing baselines` → `- [ ] Apply the Baseline, Value & Challenge gate — flag any process missing baselines`

`agents/process-mapper.md` (3 occurrences)
- Role paragraph: `the Baseline & Value Hypothesis gate, the chain scan` → `the Baseline, Value & Challenge gate, the chain scan`
- Refusal rule: `apply the Baseline & Value Hypothesis gate` → `apply the Baseline, Value & Challenge gate`
- Dispatch point paragraph: `applies the Baseline & Value Hypothesis gate.` → `applies the Baseline, Value & Challenge gate.`

`skills/using-methodology/SKILL.md`
- `- `baselines.md` — Phase 4 (load-bearing — see Baseline & Value Hypothesis gate)` → `- `baselines.md` — Phase 4 (load-bearing — see Baseline, Value & Challenge gate)`

`skills/running-sample-engagement/SKILL.md`
- `The Baseline & Value Hypothesis gate, the GRC gate,` → `The Baseline, Value & Challenge gate, the GRC gate,`

- [ ] **Step 7: Add the rationalization row**

In `skills/discovering-processes/SKILL.md` Rationalization Table, add a row at the end:

```
| "The process works — we just need to automate the slow steps." | Automate a broken process and you get a faster broken process. The challenge hypothesis forces the second-order question — is the boundary, actor model, or sequence itself the constraint? — before any automation is typed. Surface it; the client decides. |
```

- [ ] **Step 8: Run guards (and full suite) to verify pass**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "gate_renamed or challenge_hypothesis or fully_renamed"`
Expected: 3 PASSED.
Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED (no count guards affected — no new files).

- [ ] **Step 9: Commit**

```bash
git add skills/discovering-processes/SKILL.md agents/process-mapper.md skills/using-methodology/SKILL.md skills/running-sample-engagement/SKILL.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(phase4): rename gate to Baseline, Value & Challenge + add clause (#10)

The Phase 4 gate gains a third blocking clause — a per-process challenge
hypothesis synthesized at assembly. Missing hypothesis logs "challenge
hypothesis unavailable" and blocks Phase 5, identical to a missing
baseline. Renames the gate everywhere and adds the Key Outputs field,
assembly step, checklist item, and rationalization row.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 3: Phase 5 signal — Structural response field + struct= token + index column

**Files:**
- Modify: `agents/opportunity-typer.md` (Inputs, per-opportunity assembly, output template, extraction-header rules, refusal rules)
- Modify: `skills/identifying-opportunities/SKILL.md` (OPP-NNN entry structure, index-gen bash loop, checklist)
- Test: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guards**

Add to `tests/test_guards.py`:

```python
STRUCT_VALUES = ("addressing-root", "optimizing-around", "not-applicable")


def test_typer_defines_structural_response_token(methodology):
    body = methodology.agents["opportunity-typer"].body
    assert "Structural response" in body, "typer missing 'Structural response' field"
    assert "struct=" in body, "typer missing 'struct=' extraction token"
    for v in STRUCT_VALUES:
        assert v in body, f"typer missing struct value {v!r}"


def test_opportunities_index_has_structural_column(methodology):
    body = methodology.skills["ai-process-assessment:identifying-opportunities"].body
    assert "struct=" in body, "Phase 5 index generation must extract struct="
    assert "Structural" in body, "opportunities/_index.md must add a Structural column"
```

- [ ] **Step 2: Run guards to verify they fail**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "structural_response_token or structural_column"`
Expected: 2 FAILED.

- [ ] **Step 3: Add challenge hypothesis to the typer Inputs table**

In `agents/opportunity-typer.md`, in the Inputs required table, after the `| Process entry | ... |` row, add:

```
| Challenge hypothesis | The process's challenge hypothesis from `process-map.md` — whether the process was cleared structurally sound or carries a surfaced redesign question (boundary / actor model / sequence) |
```

- [ ] **Step 4: Add field #7 to the per-opportunity assembly**

In the "Per-opportunity assembly (mandatory order)" list, after item `6. **Data / system dependencies** ...`, add:

```
7. **Structural response** — read the process's challenge hypothesis and set one of: `addressing-root` (the process carries a surfaced redesign question and this opportunity addresses it), `optimizing-around` (the process carries a surfaced redesign question and this opportunity optimizes around it rather than resolving it), or `not-applicable` (the process was cleared structurally sound — no structural question at stake). Add a one-line rationale citing the challenge hypothesis. This field annotates only — it never blocks opportunity creation and never changes a score.
```

- [ ] **Step 5: Add the output-template field and extraction token**

In the markdown output template code block, replace the extraction-header line:

```
<!-- index: id=TEMP-<process-id>-<N> process=<process-id> type=<type-code> feasibility=<Green|Yellow|Red> data=<Green|Yellow|Red> grc=<Green|Yellow|Red> -->
```

with:

```
<!-- index: id=TEMP-<process-id>-<N> process=<process-id> type=<type-code> feasibility=<Green|Yellow|Red> data=<Green|Yellow|Red> grc=<Green|Yellow|Red> struct=<addressing-root|optimizing-around|not-applicable> -->
```

And after the `**Data / system dependencies:**` line in the same template, add:

```

**Structural response:** [addressing-root / optimizing-around / not-applicable] — [one-line rationale citing the process's challenge hypothesis]
```

- [ ] **Step 6: Extend the extraction-header rules and refusal rules**

In the "Extraction header rules" paragraph, append:

```
 The `struct` token takes exactly one of `addressing-root`, `optimizing-around`, or `not-applicable` (hyphenated, no spaces) — same whitespace-boundary rule as the other tokens.
```

In the Refusal rules list, add:

```
- The Structural response annotates only — never refuse to create, or down-rank, an opportunity because it is `optimizing-around`. Label it honestly and let it flow.
```

- [ ] **Step 7: Add the entry-structure row to the Phase 5 skill**

In `skills/identifying-opportunities/SKILL.md`, in the "OPP-NNN Entry Structure" table, after the `| GRC flag | ... |` row, add:

```
| Structural response | `addressing-root` / `optimizing-around` / `not-applicable` — set against the process's challenge hypothesis from `process-map.md`. Annotates only; never blocks. |
```

- [ ] **Step 8: Wire the struct column into the index-generation bash loop**

In the index-generation bash block, change the header echo:

```
  echo "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC |" > docs/engagements/<name>/opportunities/_index.md
  echo "|--------|---------|------|-------------|----------------|-----|" >> docs/engagements/<name>/opportunities/_index.md
```

to:

```
  echo "| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |" > docs/engagements/<name>/opportunities/_index.md
  echo "|--------|---------|------|-------------|----------------|-----|------------|" >> docs/engagements/<name>/opportunities/_index.md
```

Then, in the per-file loop, after the `grc=$(...)` line, add:

```
    struct=$(echo "$header" | grep -o 'struct=[^ >]*' | cut -d= -f2)
```

and change the row echo:

```
    echo "| $id | $proc | $type | $feas | $data | $grc |" >> docs/engagements/<name>/opportunities/_index.md
```

to:

```
    echo "| $id | $proc | $type | $feas | $data | $grc | $struct |" >> docs/engagements/<name>/opportunities/_index.md
```

- [ ] **Step 9: Add the checklist item**

In the Phase checklist, after `- [ ] Set GRC flag ...`, add:

```
- [ ] Set Structural response (addressing-root / optimizing-around / not-applicable) against the process's challenge hypothesis
```

- [ ] **Step 10: Run guards (and full suite)**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "structural_response_token or structural_column"`
Expected: 2 PASSED.
Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED.

- [ ] **Step 11: Commit**

```bash
git add agents/opportunity-typer.md skills/identifying-opportunities/SKILL.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(phase5): emit addressing-root/optimizing-around struct signal (#10)

The opportunity-typer reads the challenge hypothesis and sets a
Structural response per opportunity, carried by a struct= extraction
token into a new Structural column in opportunities/_index.md.
Annotation only — never blocks, never changes a score.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 4: Propagation to scores + portfolio view

**Files:**
- Modify: `agents/opportunity-scorer.md` (Strategic Alignment dimension note)
- Modify: `agents/section-renderer-portfolio.md` (Structural column via existing join)
- Test: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guards**

Add to `tests/test_guards.py`:

```python
def test_scorer_references_structural_response(methodology):
    body = methodology.agents["opportunity-scorer"].body
    assert "optimizing-around" in body, \
        "scorer must reference optimizing-around in its alignment rationale"
    assert "does not change the composite" in body, \
        "scorer must state the structural label does not change the composite"


def test_portfolio_renderer_surfaces_struct(methodology):
    body = methodology.agents["section-renderer-portfolio"].body
    assert "Structural" in body, \
        "portfolio renderer must read the Structural column"
    assert "optimizing-around" in body, \
        "portfolio renderer must render the optimizing-around badge"
```

- [ ] **Step 2: Run guards to verify they fail**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "scorer_references or portfolio_renderer_surfaces"`
Expected: 2 FAILED.

- [ ] **Step 3: Add the Strategic Alignment note to the scorer**

In `agents/opportunity-scorer.md`, immediately after the "Categorical rule:" paragraph that ends `...name the specific content.`, add a new paragraph:

```
**Structural response (read-through, no score change).** The opportunity carries a `Structural response` from Phase 5 (`addressing-root` / `optimizing-around` / `not-applicable`). When it is `optimizing-around`, note that fact in the Strategic Alignment rationale so the score's reasoning is honest about what the opportunity does and does not resolve. This is a read-through annotation only: it does not change the Strategic Alignment score and does not change the composite. The methodology surfaces the trade-off; it does not penalize it.
```

- [ ] **Step 4: Add the Structural column to the portfolio renderer**

In `agents/section-renderer-portfolio.md`, add a source row. After the table row that reads `| Opportunity types | `opportunities/_index.md` | ... |`, add:

```
| Structural response | `opportunities/_index.md` | `Structural` column — `addressing-root` / `optimizing-around` / `not-applicable` per OPP |
```

In the `<thead>` row, after `<th>Type</th>`, add:

```
        <th>Structural</th>
```

In the `<tbody>` template row, after the Type `<td>...</td>` cell, add:

```
        <td>[render the Structural value from opportunities/_index.md: show a muted "optimizing-around" badge when the value is optimizing-around; render nothing for not-applicable; show "addressing-root" when addressing-root]</td>
```

Then add a rendering rule. After the "**Type column — use the correct modifier class:**" block, add:

```
**Structural column — surface the trade-off:**
- `optimizing-around` → render a muted badge labelled `optimizing-around` (this opportunity speeds a process the challenge hypothesis flagged for redesign)
- `addressing-root` → render the plain text `addressing-root`
- `not-applicable` → render nothing (process was cleared structurally sound)

Source the value from the `Structural` column of `opportunities/_index.md` via the existing OPP-ID join. Do not change rank or score — this column is informational.
```

- [ ] **Step 5: Run guards (and full suite)**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "scorer_references or portfolio_renderer_surfaces"`
Expected: 2 PASSED.
Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED.

- [ ] **Step 6: Commit**

```bash
git add agents/opportunity-scorer.md agents/section-renderer-portfolio.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(scores): surface struct label in scoring rationale + portfolio (#10)

The scorer references an optimizing-around label in its Strategic
Alignment rationale without changing the composite; the portfolio
renderer adds a Structural column sourced from opportunities/_index.md
via its existing join.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 5: Propagation to roadmap

**Files:**
- Modify: `skills/prioritizing-roadmap/SKILL.md` (read struct, annotate optimizing-around items)
- Modify: `agents/section-renderer-roadmap.md` (surface annotation on Wave-1 cards)
- Test: `tests/test_guards.py`

- [ ] **Step 1: Write the failing guards**

Add to `tests/test_guards.py`:

```python
def test_roadmap_skill_threads_struct(methodology):
    body = methodology.skills["ai-process-assessment:prioritizing-roadmap"].body
    assert "struct" in body, "roadmap skill must read the struct signal"
    assert "optimizing-around" in body, \
        "roadmap skill must annotate optimizing-around items"


def test_roadmap_renderer_surfaces_struct(methodology):
    body = methodology.agents["section-renderer-roadmap"].body
    assert "optimizing-around" in body, \
        "roadmap renderer must surface the optimizing-around annotation"
```

- [ ] **Step 2: Run guards to verify they fail**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "roadmap_skill_threads or roadmap_renderer_surfaces"`
Expected: 2 FAILED.

- [ ] **Step 3: Read the prioritizing-roadmap structure for exact anchors**

Run: `grep -n "## Session Start\|Read \`scores\|roadmap.md\|Wave 1\|## Workflow\|## Phase checklist" skills/prioritizing-roadmap/SKILL.md`
Use the output to locate (a) the Session Start read list and (b) the Wave-1 initiative-detail / Phase checklist sections referenced below. (The file reads `scores/_index.md` at Session Start; the edits below attach to that read and to the Wave-1 output.)

- [ ] **Step 4: Add the struct read at Session Start**

In `skills/prioritizing-roadmap/SKILL.md` Session Start, in the numbered read list, after the `Read \`scores/_index.md\`` step, add a new step (renumber following items if numbered):

```
- Read `opportunities/_index.md` — for the `Structural` column. Any Wave-1 opportunity whose Structural value is `optimizing-around` must be annotated in `roadmap.md` (see Workflow).
```

- [ ] **Step 5: Add the annotation instruction to the Workflow**

In the Workflow section, add a step:

```
- **Structural annotation.** For every opportunity sequenced into a wave, look up its `Structural` value in `opportunities/_index.md`. For each `optimizing-around` item, add a one-line annotation to its entry in the Wave summary table and its Wave-1 initiative-detail card: `Structural: optimizing-around — speeds a process the Phase 4 challenge hypothesis flagged for redesign.` This is informational; it does not change wave placement. `addressing-root` and `not-applicable` items need no annotation.
```

- [ ] **Step 6: Add the checklist item**

In the Phase checklist, add:

```
- [ ] Annotate every `optimizing-around` Wave-1 item in roadmap.md (Structural read-through; does not change sequencing)
```

- [ ] **Step 7: Surface the annotation in the roadmap renderer**

In `agents/section-renderer-roadmap.md`, in the `#usecases` Wave-1 card rendering rules, add:

```
**Structural annotation (when present in `roadmap.md`):** If a Wave-1 initiative card carries a `Structural: optimizing-around` annotation, render it as a muted footnote line on that card: `optimizing-around — speeds a process flagged for redesign`. Render nothing when the annotation is absent. Do not invent the annotation — surface it only when it is present in `roadmap.md`.
```

- [ ] **Step 8: Run guards (and full suite)**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "roadmap_skill_threads or roadmap_renderer_surfaces"`
Expected: 2 PASSED.
Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED.

- [ ] **Step 9: Commit**

```bash
git add skills/prioritizing-roadmap/SKILL.md agents/section-renderer-roadmap.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(roadmap): annotate optimizing-around items in roadmap view (#10)

Phase 7 reads the Structural column from opportunities/_index.md and
annotates optimizing-around items in roadmap.md; the roadmap renderer
surfaces the annotation as a muted footnote on affected Wave-1 cards.
Informational only — does not change sequencing.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 6: Keystone — rationalization row + Phase-4 note

**Files:**
- Modify: `skills/using-methodology/SKILL.md` (Master Rationalization Table, Phase Map Phase-4 description cell)
- Test: `tests/test_guards.py`

(The keystone gate-name rename was completed in Task 2.)

- [ ] **Step 1: Write the failing guard**

Add to `tests/test_guards.py`:

```python
def test_keystone_has_structural_challenge_rationalization(methodology):
    body = methodology.skills["ai-process-assessment:using-methodology"].body
    assert "faster broken process" in body, \
        "keystone Master Rationalization Table must carry the structural-challenge row"
```

- [ ] **Step 2: Run guard to verify it fails**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "keystone_has_structural"`
Expected: 1 FAILED.

- [ ] **Step 3: Add the Master Rationalization Table row**

In `skills/using-methodology/SKILL.md`, in the Master Rationalization Table, add a row at the end:

```
| "Map it, find the slow steps, automate them — that's the engagement." | First-order automation of a process whose structure is the real constraint produces a faster broken process. The Phase 4 challenge hypothesis surfaces the second-order question (boundary / actor model / sequence); the addressing-root vs. optimizing-around signal carries it to the client. Surface it; the client decides. |
```

- [ ] **Step 4: Note the challenge hypothesis in the Phase Map (safe column)**

In the Phase Map table, in the **Phase 4 row**, edit only the third cell (the "what it does" description — NOT the gate or output cells, which the test parser reads). Change:

```
| 4 | `ai-process-assessment:discovering-processes` | Four-round interviews, baseline metrics | `tech-inventory.md` exists | `process-map.md`, `baselines.md` |
```

to:

```
| 4 | `ai-process-assessment:discovering-processes` | Four-round interviews, baseline metrics, challenge hypothesis | `tech-inventory.md` exists | `process-map.md`, `baselines.md` |
```

- [ ] **Step 5: Run guard + full suite (verify parser unaffected)**

Run: `/opt/homebrew/bin/python3.13 -m pytest tests/test_guards.py -q -k "keystone_has_structural"`
Expected: 1 PASSED.
Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED — in particular `test_manifest.py` (Phase Map shape) and `test_outputs.py` (output token) stay green, confirming the Phase-4 description edit did not disturb the parsed columns.

- [ ] **Step 6: Commit**

```bash
git add skills/using-methodology/SKILL.md tests/test_guards.py
git commit -m "$(cat <<'EOF'
feat(keystone): add structural-challenge rationalization row (#10)

Master Rationalization Table gains the first-order-vs-second-order row;
the Phase Map Phase-4 description notes the challenge hypothesis.

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

### Task 7: Version bump + final full-suite verification

**Files:**
- Modify: `.claude-plugin/plugin.json` (version 2.3.0 → 2.4.0)
- Modify: `INSTALL.md` (version string → 2.4.0)
- Test: `tests/test_plugin_manifest.py` (existing — enforces plugin.json ↔ INSTALL.md equality)

- [ ] **Step 1: Bump plugin.json**

In `.claude-plugin/plugin.json`, change `"version": "2.3.0"` to `"version": "2.4.0"`.

- [ ] **Step 2: Bump INSTALL.md to match**

In `INSTALL.md`, find the `"version": "2.3.0"` string and change it to `"version": "2.4.0"`.
(Confirm the only version occurrence with: `grep -n '"version"' INSTALL.md`.)

- [ ] **Step 3: Run the full suite**

Run: `/opt/homebrew/bin/python3.13 -m pytest -q`
Expected: all PASSED — including `test_install_md_version_matches_plugin_json` and `test_version_not_behind_latest_tag` (2.4.0 ≥ latest tag).

- [ ] **Step 4: Confirm the count guards are still correct**

Run: `/opt/homebrew/bin/python3.13 -m pytest -q -k "count"`
Expected: PASSED — `test_agent_count == 14` and `test_skill_count == 16` are unchanged (this work added no skills or agents).

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json INSTALL.md
git commit -m "$(cat <<'EOF'
chore: bump to v2.4.0 — structural-challenge gate (#10)

Co-Authored-By: ai-cockpit-admin <akaraff@gmail.com>
EOF
)"
```

---

## Self-Review

**1. Spec coverage** — every spec section maps to a task:

| Spec section | Task |
|---|---|
| §5 three challenge questions (sponsor, Round 1) | 1 |
| §7 `Sponsor structural input` capture | 1 |
| §3/§4 gate rename + blocking clause + remediation | 2 |
| §7 `process-map.md` Challenge hypothesis field | 2 |
| §6 orchestrator assembly synthesis | 2 |
| §7 `Structural response` field + `struct=` token | 3 |
| §7 `opportunities/_index.md` Structural column | 3 |
| §8 #5 scorer rationale (no score change) | 4 |
| §8 #6 portfolio renderer badge (existing join) | 4 |
| §8 #7 roadmap skill annotation | 5 |
| §8 #8 roadmap renderer surfacing | 5 |
| §8 #9 keystone rationalization + gate-name + Phase-4 note | 2 (rename) + 6 (row/note) |
| §9 test guards | every task |
| §9 version bump | 7 |
| §10 forward-compat with #6 | documentation note in spec; no task (independent) |
| §11 out of scope (no score change, no new file/agent/round) | enforced by guards in 4 (no composite change) + count check in 7 |

No spec requirement is left without a task.

**2. Placeholder scan** — no "TBD"/"handle appropriately"; every edit step shows the exact anchor text and exact replacement; every guard step shows complete pytest code. Task 5 Step 3 is an explicit `grep` to confirm anchors in a file whose interior line numbers were not pre-read — that is a real investigation step, not a placeholder, and the subsequent edits name the target sections precisely.

**3. Type consistency** — the three struct values are spelled identically everywhere: `addressing-root`, `optimizing-around`, `not-applicable` (defined once as `STRUCT_VALUES` in Task 3's guard and reused). The token is `struct=` in the typer (Task 3), the index loop (Task 3), the portfolio source row (Task 4). The gate name is `Baseline, Value & Challenge Gate` consistently (Task 2). Guard function names are unique. The marker strings asserted in guards (`"Structural response"`, `"challenge hypothesis unavailable"`, `"Baseline, Value & Challenge Gate"`, `"faster broken process"`, `"does not change the composite"`, `"optimizing-around"`) each match text written into the markdown in the same or an earlier task.
