# Sample-Run Marker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase skills that perform live elicitation (Phases 1–4) must check for a `.sample-run.md` marker file and substitute the mapped intake file for live interview, so sample runs survive session boundaries without user intervention.

**Architecture:** `running-sample-engagement` writes a `.sample-run.md` marker into `docs/engagements/sample-pso-delivery/` at setup time. Each of the four eliciting phase skills adds a Session Start step that reads the marker when present and routes to the bundled intake file instead of eliciting. Phases 5–11 need no change — they take no new external input. Regression guards in `test_guards.py` verify the contract is present in each skill.

**Tech Stack:** Plain markdown skill files; Python pytest guards (`test_guards.py`).

---

## File Map

| Action | Path |
|---|---|
| Modify | `skills/running-sample-engagement/skill.md` |
| Modify | `skills/scoping-engagement/skill.md` |
| Modify | `skills/mapping-context/skill.md` |
| Modify | `skills/inventorying-tech-data/skill.md` |
| Modify | `skills/discovering-processes/skill.md` |
| Modify | `tests/test_guards.py` |

---

### Task 1: Write failing regression guards

**Files:**
- Modify: `tests/test_guards.py`

The guards go in a new section at the bottom of `test_guards.py`.

- [ ] **Step 1: Add the failing guards**

Append the following block to `tests/test_guards.py`:

```python
# --- #sample-run-marker guard (defends: sample-run context lost at session boundary) ---
# running-sample-engagement must write .sample-run.md so fresh sessions can detect the
# sample context. Every eliciting phase skill (Phases 1–4) must check for that file in
# its Session Start section before falling through to live elicitation.

SAMPLE_RUN_MARKER = ".sample-run.md"
ELICITING_PHASE_SKILLS = {
    "ai-process-assessment:scoping-engagement",
    "ai-process-assessment:mapping-context",
    "ai-process-assessment:inventorying-tech-data",
    "ai-process-assessment:discovering-processes",
}


def test_running_sample_engagement_writes_marker(methodology):
    body = methodology.skills["ai-process-assessment:running-sample-engagement"].body
    assert SAMPLE_RUN_MARKER in body, \
        "running-sample-engagement must write the .sample-run.md marker file in its Setup section"


def test_eliciting_phase_skills_check_sample_run_marker(methodology):
    for sid in sorted(ELICITING_PHASE_SKILLS):
        body = methodology.skills[sid].body
        ss_idx = body.find("## Session Start")
        assert ss_idx != -1, f"{sid} has no Session Start section"
        ss_block = body[ss_idx:]
        nxt = re.search(r"\n## ", ss_block[len("## Session Start"):])
        if nxt:
            ss_block = ss_block[:len("## Session Start") + nxt.start()]
        assert SAMPLE_RUN_MARKER in ss_block, \
            f"{sid} Session Start missing .sample-run.md check"
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py::test_running_sample_engagement_writes_marker tests/test_guards.py::test_eliciting_phase_skills_check_sample_run_marker -v
```

Expected: FAIL — "running-sample-engagement must write the .sample-run.md marker file" and five failures for the phase skills.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_guards.py
git commit -m "test: add sample-run-marker guard (failing — implementation follows)"
```

---

### Task 2: Add marker-writing step to `running-sample-engagement`

**Files:**
- Modify: `skills/running-sample-engagement/skill.md`

The Setup section currently has three numbered steps. Add step 4 between step 3 ("Read the scenario README") and the "Then hand off to Phase 1" line.

- [ ] **Step 1: Write the failing test**

Already written in Task 1. Skip.

- [ ] **Step 2: Insert step 4 into the Setup section**

Find the text:

```
Then hand off to Phase 1 — do **not** do Phase 1's work in this skill.
```

Insert immediately before it:

```
4. **Write the sample-run marker.** Create the engagement folder and write `.sample-run.md` now, before handing off to Phase 1. This marker persists across session boundaries so every phase skill can detect the sample context without user action.

   ```bash
   mkdir -p docs/engagements/sample-pso-delivery
   ```

   Write `docs/engagements/sample-pso-delivery/.sample-run.md` with exactly this content:

   ~~~markdown
   ---
   sample: pso-delivery-team
   intake_root: samples/pso-delivery-team/intake
   ---

   # Sample Run Marker

   This file signals that this engagement folder contains a sample run of the
   `pso-delivery-team` scenario. Phase skills check for this file at Session
   Start and substitute bundled intake files for live elicitation.

   ## Phase Intake Map

   | Phase | Intake file (relative to intake_root) |
   |---|---|
   | 1 — Scoping | engagement-request.md |
   | 2 — Context | org-context.md |
   | 3 — Tech & Data | systems-and-data.md |
   | 4 — Discovery | interview-notes.md |
   ~~~

```

- [ ] **Step 3: Run the marker test to verify it passes**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py::test_running_sample_engagement_writes_marker -v
```

Expected: PASS

- [ ] **Step 4: Run all guards to make sure nothing else broke**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py -v
```

Expected: Only the five `test_eliciting_phase_skills_check_sample_run_marker` parametrized cases still fail; everything else passes.

- [ ] **Step 5: Commit**

```bash
git add skills/running-sample-engagement/skill.md
git commit -m "feat: running-sample-engagement writes .sample-run.md marker at setup"
```

---

### Task 3: Add sample-run check to Phase 1 (`scoping-engagement`)

**Files:**
- Modify: `skills/scoping-engagement/skill.md`

Phase 1 is a special case: it asks for the engagement name before any files exist, so the check happens after the name is resolved.

The Session Start section currently reads:

```
1. Ask the user for the engagement name. This becomes the folder path `docs/engagements/<name>/`. Accept any lowercase, kebab-case, or alphanumeric string. Reject placeholder strings like `<name>`, `<fill in>`, or empty input — halt and re-ask.
2. Run `mkdir -p docs/engagements/<name>/` to create the engagement folder before writing any files.
3. No predecessor files required — this is Phase 1.
```

- [ ] **Step 1: Write the failing test**

Already written in Task 1. Skip.

- [ ] **Step 2: Add the sample-run check as step 3, renumber the old step 3 to step 4**

Replace the Session Start block so it reads:

```
1. Ask the user for the engagement name. This becomes the folder path `docs/engagements/<name>/`. Accept any lowercase, kebab-case, or alphanumeric string. Reject placeholder strings like `<name>`, `<fill in>`, or empty input — halt and re-ask.
2. Run `mkdir -p docs/engagements/<name>/` to create the engagement folder before writing any files.
3. **Check for a sample-run marker.** After creating the engagement folder, check whether `docs/engagements/<name>/.sample-run.md` exists. If present, this is a sample run — read that file silently. At the live-sponsor-interview step in the Workflow below, read the intake file listed for Phase 1 in the marker's Phase Intake Map (`<intake_root>/engagement-request.md`) instead of interviewing a live sponsor.
4. No predecessor files required — this is Phase 1.
```

- [ ] **Step 3: Run the Phase 1 marker test**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py::test_eliciting_phase_skills_check_sample_run_marker -v -k scoping
```

Expected: PASS for `scoping-engagement`.

- [ ] **Step 4: Run all guards**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py -v
```

Expected: Four `test_eliciting_phase_skills_check_sample_run_marker` cases still failing; all others pass.

- [ ] **Step 5: Commit**

```bash
git add skills/scoping-engagement/skill.md
git commit -m "feat: Phase 1 checks .sample-run.md before live elicitation"
```

---

### Task 4: Add sample-run check to Phases 2, 3, and 4

**Files:**
- Modify: `skills/mapping-context/skill.md`
- Modify: `skills/inventorying-tech-data/skill.md`
- Modify: `skills/discovering-processes/skill.md`

All three follow the same pattern: they already read `scope.md` in step 1. The marker check goes as step 3 in each.

- [ ] **Step 1: Write the failing test**

Already written in Task 1. Skip.

- [ ] **Step 2: Add step 3 to `mapping-context` Session Start**

The current Session Start ends at step 2. Append step 3:

```
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently. At the live-interview step in the Workflow below, read the intake file listed for Phase 2 in the marker's Phase Intake Map (`<intake_root>/org-context.md`) instead of interviewing a live sponsor or operator.
```

- [ ] **Step 3: Add step 3 to `inventorying-tech-data` Session Start**

The current Session Start ends at step 2. Append step 3:

```
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently. At the live-interview step in the Workflow below, read the intake file listed for Phase 3 in the marker's Phase Intake Map (`<intake_root>/systems-and-data.md`) instead of interviewing a live IT stakeholder.
```

- [ ] **Step 4: Add step 3 to `discovering-processes` Session Start**

The current Session Start ends at step 2. Append step 3:

```
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently. At all four interview rounds in the Workflow below, read the intake file listed for Phase 4 in the marker's Phase Intake Map (`<intake_root>/interview-notes.md`) instead of conducting live stakeholder interviews.
```

- [ ] **Step 5: Run all four eliciting-phase tests**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest tests/test_guards.py::test_eliciting_phase_skills_check_sample_run_marker -v
```

Expected: All four PASS.

- [ ] **Step 6: Run the full test suite**

```bash
cd /Users/daveraffaele/Desktop/plugins/ai-process-assessment && python -m pytest -v
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add skills/mapping-context/skill.md skills/inventorying-tech-data/skill.md skills/discovering-processes/skill.md
git commit -m "feat: Phases 2-4 check .sample-run.md before live elicitation"
```

---

### Task 5: Open PR

- [ ] **Step 1: Push branch and open PR**

```bash
git push -u origin claude/funny-chatterjee-b00e9f
gh pr create \
  --title "feat: .sample-run.md marker persists sample context across session boundaries" \
  --body "$(cat <<'EOF'
## Problem

`running-sample-engagement` establishes the phase→intake-file mapping but that context doesn't survive the session boundary. A fresh session invoking any Phase 1–4 skill goes straight to live elicitation with no awareness of the sample path.

## Fix

Option 1 (marker file):

- `running-sample-engagement` now writes `docs/engagements/sample-pso-delivery/.sample-run.md` at setup time. The marker records the `intake_root` and a per-phase intake-file map.
- Each of the four eliciting phase skills (Phases 1–4) adds a Session Start step that checks for `.sample-run.md` and routes to the bundled intake file when present.
- Regression guards in `test_guards.py` verify the marker-write instruction exists in `running-sample-engagement` and the marker-check exists in every eliciting phase skill's Session Start section.

## Test plan
- [ ] `test_running_sample_engagement_writes_marker` passes
- [ ] `test_eliciting_phase_skills_check_sample_run_marker` passes for all four skills
- [ ] Full suite green

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 2: Verify the PR URL is returned and share it**
