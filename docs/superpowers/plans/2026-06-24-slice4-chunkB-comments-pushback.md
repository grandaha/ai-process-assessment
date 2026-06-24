# Slice 4 · Chunk B — Inline Comments + Conflict Pushback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the read-only step reviews from Chunk A into a two-way loop — the operator marks up the review inline, the conductor works through the comments (routing them through the audited edit engine), pushes back on conflicts, and leaves an audit-backed change history.

**Architecture:** Pure conductor behavior in `skills/conducting-engagement/SKILL.md` plus a one-field schema addition to the decision-log template; **no new Python** (the renderer/extractor shipped in Chunk A; the revision path is Slice 2 edit-splicing; the cascade is Slice 3 staleness; pushback composes holding-the-line + gates + decision log + flywheel). Enforced by static string-presence guards over the skill prose, the repo's convention.

**Tech Stack:** Markdown skill prose; pytest static guards (`tests/test_conductor_skill.py`). No code changes to `state/`.

## Global Constraints

- **No new Python.** Chunk B is conductor prose + guards + the decision-log `comment:` field. (Spec §12.)
- **The comment round-trip routes through edit-splicing** (Slice 2 Chunk B) — classify → owning artifact → re-run; never free-edit. (Spec §4.2.)
- **Comment-aware lifecycle invariants:** never silently regenerate a document carrying unresolved comments; regeneration is comment-preserving; a resolved comment moves into the Change-history view (sourced from the decision log); **drain-before-overwrite** on a staleness re-drive of a single-doc surface. (Spec §5.)
- **`comment:` is a distinct decision-log field** (verbatim operator comment), separate from `rationale:`; optional, so existing entries stay valid. (Spec §3.3.)
- **Conflict pushback — five classes** (evidence/grounding, methodology/rationalization, cascade/consistency, prior-decision, intra-batch), firm-and-teaching, never silent compliance against evidence/method, the operator decides and the override is logged. (Spec §6.)
- **Jargon-free narration** in any new fenced block. (Epic AC-1.)
- **Verification:** local `.venv/bin/python -m pytest` (GitHub Actions is over quota this month — subagent reviews + local pytest are the gates; no `@claude`/CI).

---

## File Structure

- `skills/conducting-engagement/SKILL.md` — **modify**: add `comment:` to the decision-log entry template (Task 1); expand `## Step reviews` with the comment-aware lifecycle (Task 2); add the conflict-pushback subsection (Task 3).
- `tests/test_conductor_skill.py` — **modify**: guards for each (Tasks 1–3).

---

### Task 1: `comment:` field in the decision-log entry template

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (the `## Decision log` entry template)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Produces: a `comment:` line in the decision-log entry template, documented as the verbatim operator comment for review-comment-driven entries (optional otherwise). Consumed by Chunk A's `render_change_history` (which already reads `comment:`).

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_conductor_skill.py`:

```python
def test_decision_log_has_comment_field():
    sec = _section(SKILL.read_text(), "## Decision log")
    # The entry template carries a distinct verbatim-comment field for review-driven edits.
    assert "comment:" in sec
    assert "verbatim" in sec.lower()
    # It is distinct from rationale (which may be the conductor's counter-argument).
    assert "rationale:" in sec
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_decision_log_has_comment_field -v`
Expected: FAIL — no `comment:` / `verbatim` in the Decision log section.

- [ ] **Step 3: Add the field to the template**

In `skills/conducting-engagement/SKILL.md`, in the `## Decision log` entry template, add a `comment:` line after `rationale:` and before `evidence:`:

```
- rationale: <why>
- comment: <verbatim operator review comment, when this entry was driven by a step-review comment; omit otherwise>
- evidence: <file path + section/anchor, or model/*.json key>
```

Then, in the prose just below the template, add one sentence:

```markdown
When an entry is driven by a step-review comment, record the operator's words **verbatim** in
`comment:` — distinct from `rationale:` (which may be your counter-argument on an override).
The step-review Change-history view reads `comment:` to show *original comment → what changed*.
```

- [ ] **Step 4: Run the guard + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): comment: field in decision-log template (slice4 chunkB)"
```

---

### Task 2: Comment-aware lifecycle in `## Step reviews`

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (`## Step reviews`)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: `state/step_review.py` (render + `extract_comments`, Chunk A), edit-splicing (*Edit & interruption splicing*), the decision-log `comment:` field (Task 1).
- Produces: the `## Step reviews` section now describes the full two-way lifecycle. Retains the tokens Chunk A's guard checks (`state/step_review.py`, "read-only" for surfacing, "fragmented", the `step-review-narration` fences).

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_conductor_skill.py`:

```python
def test_step_review_comment_lifecycle():
    sec = _section(SKILL.read_text(), "## Step reviews")
    # Inline comment convention is named.
    assert "💬" in sec
    # Comments are read back and routed through the audited edit engine.
    assert "extract" in sec.lower() or "read" in sec.lower()
    assert "Edit & interruption splicing" in sec
    # The no-silent-clobber + drain-before-overwrite invariants are stated.
    assert "unresolved" in sec.lower()
    assert "drain" in sec.lower() or "before" in sec.lower()
    # Resolved comments move into the change history (not deleted into the void).
    assert "change history" in sec.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_step_review_comment_lifecycle -v`
Expected: FAIL — the read-only section lacks the lifecycle.

- [ ] **Step 3: Expand the `## Step reviews` section**

In `skills/conducting-engagement/SKILL.md`, **replace** the paragraph that begins "In this revision the review is **read-only**: you present it; corrections still flow through *Edit & interruption splicing* (the inline-comment round-trip lands in a later revision)." with:

```markdown
**Surfacing** a review is read-only — presenting it never advances the drive loop or mutates
anything. **Working through comments** is the two-way half: the operator marks the review up
inline and you apply the agreed changes through the audited pipeline.
```

Then, immediately before the `<!-- step-review-narration:start -->` block, insert:

````markdown
### Working through comments

The operator annotates the review **inline** — a blockquote led by `> 💬`, anchored to the
item with `@<ID>` or by sitting under that item's heading:

```
> 💬 @OPP-3 this is augmentation, not automation — a human still signs off
```

Lifecycle (never lose a comment, never silently overwrite):

1. **Generate** — render the review fresh (Chunk A) when the step completes.
2. **Annotate** — the operator adds `> 💬` comments and saves.
3. **Intake** — when they say they've commented (or on request), read the document and
   extract its comments (`state.step_review.extract_comments`).
4. **Work through (with pushback — below)** — for each comment: route it through *Edit &
   interruption splicing* (classify → fix the owning artifact → re-run the audited engine);
   log the decision with the operator's words **verbatim** in the decision-log `comment:`
   field. Staleness re-derives downstream.
5. **Regenerate** — re-render the review: resolved comments move into the **Change history**
   (the decision-log view); unresolved comments are preserved at their anchor.

Invariants:
- **Never silently regenerate** a review that still carries unresolved comments;
  regeneration is comment-preserving (an orphaned comment lands under *Unanchored comments*,
  never dropped).
- **Drain before overwrite.** A single-document surface (e.g. `scope.md`) is also rewritten
  out-of-band when a **staleness re-drive** re-runs that phase. Before any re-drive
  overwrites a surface carrying unresolved comments, drain them first — process them, or
  re-inject them at their anchors in the re-driven document (orphaned anchors surface, never
  silently dropped). Check for unresolved comments at the top of any single-doc re-drive.
````

- [ ] **Step 4: Run the guards + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS — the new guard and the Chunk A `test_conductor_step_reviews_section` both green (the retained tokens still present).

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): step-review comment-aware lifecycle (slice4 chunkB)"
```

---

### Task 3: Conflict pushback

**Files:**
- Modify: `skills/conducting-engagement/SKILL.md` (`## Step reviews` — add a pushback subsection)
- Test: `tests/test_conductor_skill.py`

**Interfaces:**
- Consumes: *Adaptive autonomy & holding the line*, the deliverable-gate evidence discipline, `state.staleness`, the decision log, the improvement flywheel (Slice 3 C).
- Produces: a `### Pushing back on conflicts` subsection enumerating the five conflict classes and the firm-and-teaching posture, within `## Step reviews`.

- [ ] **Step 1: Write the failing guard test**

Add to `tests/test_conductor_skill.py`:

```python
def test_step_review_conflict_pushback():
    sec = _section(SKILL.read_text(), "## Step reviews")
    low = sec.lower()
    # Firm-and-teaching, not silent compliance; the operator still decides.
    assert "holding the line" in low or "firm" in low
    # The five conflict classes are all present.
    assert "evidence" in low                    # evidence / grounding
    assert "rationalization" in low or "methodology" in low
    assert "cascade" in low or "consistency" in low
    assert "prior decision" in low or "decision log" in low
    assert "contradict" in low or "conflicting comments" in low or "each other" in low
    # An override is the operator's call, and it's logged.
    assert "override" in low and "log" in low
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py::test_step_review_conflict_pushback -v`
Expected: FAIL — no pushback subsection yet.

- [ ] **Step 3: Add the pushback subsection**

In `skills/conducting-engagement/SKILL.md`, immediately **after** the *Working through comments* subsection (before the narration block), insert:

````markdown
### Pushing back on conflicts

Comments are not applied blindly. As you work through each one, check it against what you
already know, and on a conflict **surface it and reason it through** — firm-and-teaching (the
human reason + the fastest honest path), the *holding the line* posture. You do not refuse
(the operator is the decision-maker) and you do not silently comply against the evidence or
the method; the operator decides, and any override is logged in the decision log.

- **Evidence / grounding** — a comment to change a figure that is *computed* from a sourced
  input: you can't overwrite a computed result (it breaks traceability); offer to change the
  underlying assumption instead.
- **Methodology / rationalization** — a comment that is really a shortcut (e.g. "skip the
  governance check on this one" while it's flagged): hold the line, and auto-flag it to the
  improvement log (the flywheel).
- **Cascade / consistency** — a change that makes the portfolio internally inconsistent (a
  sequencing/dependency clash): surface the inconsistency before applying.
- **Prior decision** — a comment that reverses something already settled in the decision
  log: name it ("you decided X earlier — override it?") and log the override if they confirm.
- **Conflicting comments** — two comments in the same pass that contradict each other:
  surface both and ask which governs.
````

- [ ] **Step 4: Run the guards + full suite**

Run: `.venv/bin/python -m pytest tests/test_conductor_skill.py -v && .venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/conducting-engagement/SKILL.md tests/test_conductor_skill.py
git commit -m "feat(conductor): step-review conflict pushback (slice4 chunkB)"
```

---

## Final verification

- [ ] Whole suite: `.venv/bin/python -m pytest -q` — all green.
- [ ] Re-read the assembled `## Step reviews` section end-to-end: surfacing (read-only) → working through comments (lifecycle + invariants) → pushing back on conflicts → jargon-free narration. Confirm it reads as one coherent flow and the Chunk A guards (`test_conductor_step_reviews_section`, `test_conductor_step_review_narration_is_jargon_free`) still pass.
