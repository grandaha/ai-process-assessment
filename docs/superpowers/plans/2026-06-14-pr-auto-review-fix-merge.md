# PR Auto-Review-Fix-Merge Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On every PR to `main`, Claude reviews it; test-covered Python that Claude approves auto-merges once CI is green; Python that Claude rejects is auto-fixed and re-reviewed (bounded to 3 rounds); anything touching markdown gets the same review/fix-for-Python treatment but always waits for a human to merge.

**Architecture:** A single GitHub Actions workflow (`auto-review.yml`) is the deterministic orchestrator. It invokes `claude-code-action` twice as the only non-deterministic steps — once to **review** (returns a structured verdict), once to **fix** (Python only, edits + commits, never pushes). All decision logic lives in a tested Python module `scripts/auto_merge_gate.py`; the workflow is thin glue. The workflow owns the push (with a PAT so the re-review re-triggers) and the merge. The agent has zero merge/push authority.

**Tech Stack:** GitHub Actions (YAML + bash + `gh` CLI), `anthropics/claude-code-action@v1`, Python 3.12 + pytest (matching the repo's existing 121-test suite), Claude subscription auth via `CLAUDE_CODE_OAUTH_TOKEN`.

**Spec:** `docs/superpowers/specs/2026-06-14-pr-auto-review-fix-merge-design.md`

---

## Key facts this plan relies on (confirmed against claude-code-action docs, 2026-06-14)

- `prompt:` input puts the action in automation mode (runs immediately, no `@claude` mention needed).
- `--json-schema '<schema>'` in `claude_args` makes the action emit a validated JSON string in the **`structured_output`** step output. This is the primary verdict channel.
- The action's Claude is **system-prompt-blocked from `git push`/`merge`/rebase** even if the Bash tools are granted. So the **workflow** does the push; Claude only edits + commits.
- Events made with the default `GITHUB_TOKEN` do **not** trigger downstream workflow runs. The fixer's push must use a **PAT** (`secrets.WORKFLOW_PAT`) so the `synchronize` event re-runs this workflow (the re-review edge).
- Auth: `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` (already a repo secret). **Do not** set `anthropic_api_key` (would bill per-token).
- Success of the fixer is detected by **a new local commit**, never by exit code.

## File structure

- **Create** `scripts/auto_merge_gate.py` — pure decision logic + a CLI. Responsibilities: parse the review verdict (fails closed), classify changed-file paths, compute auto-merge eligibility, decide whether the fixer should run. No I/O beyond reading CLI args and printing `key=value` decision lines.
- **Create** `tests/test_auto_merge_gate.py` — unit tests for every function in the module.
- **Create** `.github/workflows/auto-review.yml` — the orchestrator workflow.
- **Modify** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `INSTALL.md`, `CHANGELOG.md` — version bump on finish (per repo release convention).

## Manual prerequisites (the human does these once — they cannot be scripted)

These are required before the workflow can function. Document them in the PR description.

1. **Create a fine-grained PAT** named e.g. `auto-review-loop`, scoped to this repo, with **Repository permissions: Contents: Read and write, Pull requests: Read and write, Workflows: Read** (Workflows read only — the fixer never edits workflow files). Store it as repo secret **`WORKFLOW_PAT`**.
   - `gh secret set WORKFLOW_PAT --body '<token>'`
2. **Create the `security` label** (hard-block for auto-merge):
   - `gh label create security --color B60205 --description "Risk/judgment work — never auto-merges" || true`
3. **Create the report-only toggle** as a repo variable, default off:
   - `gh variable set AUTO_MERGE_ENABLED --body "false"`
   - Phase 2 of rollout flips this to `"true"` after the real-PR smoke test.

---

## Task 1: Verdict parser (`parse_verdict`)

**Files:**
- Create: `scripts/auto_merge_gate.py`
- Create: `tests/test_auto_merge_gate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auto_merge_gate.py
"""Unit tests for the deterministic auto-merge gate logic.

The gate is the single most safety-critical piece: it decides whether an
LLM-reviewed PR auto-merges. Every ambiguity must fail closed (never merge).
"""
import sys
from pathlib import Path

# scripts/ is not on the path by default; add it (mirrors conftest's pattern).
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import auto_merge_gate as gate  # noqa: E402


class TestParseVerdict:
    def test_structured_output_automerge_is_yes(self):
        assert gate.parse_verdict('{"verdict": "AUTOMERGE"}', None) == "YES"

    def test_structured_output_hold_is_no(self):
        assert gate.parse_verdict('{"verdict": "HOLD"}', None) == "NO"

    def test_falls_back_to_token_in_review_text(self):
        assert gate.parse_verdict(None, "Looks good.\nAUTOMERGE: YES") == "YES"

    def test_token_no_in_review_text(self):
        assert gate.parse_verdict("", "Needs work.\nAUTOMERGE: NO") == "NO"

    def test_no_wins_over_yes_when_both_present(self):
        # Fail-safe: if the text is contradictory, treat as NO.
        assert gate.parse_verdict(None, "AUTOMERGE: YES ... actually AUTOMERGE: NO") == "NO"

    def test_missing_everything_is_unknown(self):
        assert gate.parse_verdict(None, None) == "UNKNOWN"

    def test_garbage_structured_output_falls_back_then_unknown(self):
        assert gate.parse_verdict("not json", "no token here") == "UNKNOWN"

    def test_unknown_is_not_yes(self):
        # The whole point: UNKNOWN must never be treated as approval.
        assert gate.parse_verdict(None, "") != "YES"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'auto_merge_gate'`.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/auto_merge_gate.py
"""Deterministic decision logic for the PR auto-review-fix-merge loop.

Pure functions + a thin CLI. No network calls. The workflow gathers facts
(verdict, changed files, CI status, labels, round) and asks this module for a
single decision. Every ambiguity fails closed: when in doubt, do NOT merge.
"""
from __future__ import annotations

import json


def parse_verdict(structured_output: str | None, review_text: str | None) -> str:
    """Return 'YES', 'NO', or 'UNKNOWN'.

    Primary channel: structured_output JSON with a 'verdict' of AUTOMERGE/HOLD.
    Fallback: an 'AUTOMERGE: YES'/'AUTOMERGE: NO' token in the review prose.
    Fails closed — anything ambiguous or missing returns 'UNKNOWN'.
    """
    if structured_output:
        try:
            data = json.loads(structured_output)
            verdict = str(data.get("verdict", "")).upper()
            if verdict == "AUTOMERGE":
                return "YES"
            if verdict == "HOLD":
                return "NO"
        except (ValueError, AttributeError):
            pass  # fall through to token parsing

    if review_text:
        body = review_text.upper()
        if "AUTOMERGE: NO" in body:   # checked first — NO wins, fail-safe
            return "NO"
        if "AUTOMERGE: YES" in body:
            return "YES"

    return "UNKNOWN"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py -q`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/auto_merge_gate.py tests/test_auto_merge_gate.py
git commit -m "feat(auto-merge): verdict parser that fails closed"
```

---

## Task 2: Path classifier (`classify_paths`)

**Files:**
- Modify: `scripts/auto_merge_gate.py`
- Modify: `tests/test_auto_merge_gate.py`

- [ ] **Step 1: Write the failing test** (append to the test file)

```python
class TestClassifyPaths:
    def test_python_only(self):
        c = gate.classify_paths(["engine/foo.py", "tests/test_foo.py"])
        assert c == {"python_only": True, "touches_markdown": False, "touches_protected": False}

    def test_scripts_dir_is_python(self):
        c = gate.classify_paths(["scripts/helper.py"])
        assert c["python_only"] is True

    def test_markdown_flagged(self):
        c = gate.classify_paths(["skills/scoping-engagement/SKILL.md"])
        assert c["touches_markdown"] is True
        assert c["python_only"] is False

    def test_mixed_python_and_markdown_is_not_python_only(self):
        c = gate.classify_paths(["engine/foo.py", "README.md"])
        assert c["python_only"] is False
        assert c["touches_markdown"] is True

    def test_path_outside_allowlist_is_not_python_only(self):
        c = gate.classify_paths(["src/whatever.py"])  # not under an allowed prefix
        assert c["python_only"] is False

    def test_workflow_file_is_protected(self):
        c = gate.classify_paths([".github/workflows/auto-review.yml"])
        assert c["touches_protected"] is True
        assert c["python_only"] is False

    def test_gate_module_itself_is_protected(self):
        # Never auto-merge changes to the auto-merge logic.
        c = gate.classify_paths(["scripts/auto_merge_gate.py"])
        assert c["touches_protected"] is True
        assert c["python_only"] is False

    def test_empty_changeset_is_not_python_only(self):
        c = gate.classify_paths([])
        assert c["python_only"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py::TestClassifyPaths -q`
Expected: FAIL — `AttributeError: module 'auto_merge_gate' has no attribute 'classify_paths'`.

- [ ] **Step 3: Write minimal implementation** (add to `scripts/auto_merge_gate.py`)

```python
# --- path classification ---

ALLOWED_PREFIXES = ("engine/", "tests/", "scripts/")
MARKDOWN_SUFFIXES = (".md",)
# Never auto-merge changes to the loop's own machinery, even though they live
# under allowed prefixes. claude-code-action also cannot edit .github/ files,
# but we guard it deterministically regardless.
PROTECTED_PREFIXES = (".github/",)
PROTECTED_FILES = ("scripts/auto_merge_gate.py",)


def classify_paths(changed_files: list[str]) -> dict:
    """Classify a PR's changed-file set for merge eligibility.

    python_only is True iff there is at least one changed file and ALL changed
    files are under an allowed prefix, none are markdown, and none are protected.
    """
    touches_markdown = any(
        f.endswith(MARKDOWN_SUFFIXES) for f in changed_files
    )
    touches_protected = any(
        f in PROTECTED_FILES or f.startswith(PROTECTED_PREFIXES)
        for f in changed_files
    )
    all_allowed = bool(changed_files) and all(
        f.startswith(ALLOWED_PREFIXES) for f in changed_files
    )
    python_only = all_allowed and not touches_markdown and not touches_protected
    return {
        "python_only": python_only,
        "touches_markdown": touches_markdown,
        "touches_protected": touches_protected,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py::TestClassifyPaths -q`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/auto_merge_gate.py tests/test_auto_merge_gate.py
git commit -m "feat(auto-merge): path classifier (python-only vs markdown vs protected)"
```

---

## Task 3: Eligibility + fixer-dispatch decision (`decide`)

**Files:**
- Modify: `scripts/auto_merge_gate.py`
- Modify: `tests/test_auto_merge_gate.py`

- [ ] **Step 1: Write the failing test** (append)

```python
class TestDecide:
    def _decide(self, **kw):
        defaults = dict(
            verdict="YES",
            ci_passed=True,
            changed_files=["engine/foo.py"],
            labels=[],
            round_count=0,
            max_rounds=3,
        )
        defaults.update(kw)
        return gate.decide(**defaults)

    def test_python_approved_green_merges(self):
        d = self._decide()
        assert d["decision"] == "merge"

    def test_ci_red_does_not_merge(self):
        d = self._decide(ci_passed=False)
        assert d["decision"] == "human"
        assert "ci" in d["reason"].lower()

    def test_security_label_blocks_merge(self):
        d = self._decide(labels=["security"])
        assert d["decision"] == "human"
        assert "security" in d["reason"].lower()

    def test_approved_markdown_waits_for_human(self):
        d = self._decide(changed_files=["skills/x/SKILL.md"])
        assert d["decision"] == "human"
        assert "markdown" in d["reason"].lower()

    def test_unknown_verdict_never_merges(self):
        d = self._decide(verdict="UNKNOWN")
        assert d["decision"] != "merge"

    def test_rejected_python_under_cap_dispatches_fixer(self):
        d = self._decide(verdict="NO", round_count=0)
        assert d["decision"] == "fix"

    def test_rejected_python_at_cap_stops(self):
        d = self._decide(verdict="NO", round_count=3)
        assert d["decision"] == "human"
        assert "round" in d["reason"].lower()

    def test_rejected_markdown_never_fixes(self):
        # Vector B guard: the fixer must never touch markdown.
        d = self._decide(verdict="NO", changed_files=["skills/x/SKILL.md"])
        assert d["decision"] == "human"

    def test_protected_file_never_merges_even_if_approved(self):
        d = self._decide(changed_files=["scripts/auto_merge_gate.py"])
        assert d["decision"] == "human"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py::TestDecide -q`
Expected: FAIL — `AttributeError: ... has no attribute 'decide'`.

- [ ] **Step 3: Write minimal implementation** (add to module)

```python
# --- top-level decision ---

RISK_LABELS = ("security",)


def decide(
    verdict: str,
    ci_passed: bool,
    changed_files: list[str],
    labels: list[str],
    round_count: int,
    max_rounds: int = 3,
) -> dict:
    """Return {'decision': 'merge'|'fix'|'human', 'reason': str}.

    'merge' = eligible to auto-merge (the workflow still honors report-only mode).
    'fix'   = dispatch the Python-only fixer, then push + re-review.
    'human' = leave the PR for a person; reason explains why.
    Fail-safe: any path that isn't clearly 'merge' or 'fix' returns 'human'.
    """
    paths = classify_paths(changed_files)
    has_risk_label = any(lbl in RISK_LABELS for lbl in labels)

    if verdict == "YES":
        if has_risk_label:
            return {"decision": "human", "reason": "carries a security/risk label"}
        if not ci_passed:
            return {"decision": "human", "reason": "CI is not green"}
        if paths["touches_protected"]:
            return {"decision": "human", "reason": "touches protected machinery (.github/ or gate module)"}
        if not paths["python_only"]:
            return {"decision": "human", "reason": "approved, but touches markdown — ready for you to merge"}
        return {"decision": "merge", "reason": "python-only, approved, CI green"}

    if verdict == "NO":
        if not paths["python_only"]:
            return {"decision": "human", "reason": "rejected and touches markdown — fixer cannot edit prose"}
        if round_count >= max_rounds:
            return {"decision": "human", "reason": f"max auto-fix rounds ({max_rounds}) reached"}
        return {"decision": "fix", "reason": "python-only rejection under the round cap"}

    return {"decision": "human", "reason": f"verdict {verdict} — failing closed"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py -q`
Expected: PASS (all classes, ~25 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/auto_merge_gate.py tests/test_auto_merge_gate.py
git commit -m "feat(auto-merge): top-level decide() combining verdict, CI, paths, labels, rounds"
```

---

## Task 4: CLI wrapper for the gate module

The workflow calls the module as a subprocess and reads decision values from stdout (one `key=value` per line, ready to append to `$GITHUB_OUTPUT`).

**Files:**
- Modify: `scripts/auto_merge_gate.py`
- Modify: `tests/test_auto_merge_gate.py`

- [ ] **Step 1: Write the failing test** (append)

```python
import subprocess


class TestCli:
    SCRIPT = REPO_ROOT / "scripts" / "auto_merge_gate.py"

    def _run(self, args):
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args],
            capture_output=True, text=True,
        )

    def test_cli_emits_merge_decision(self):
        r = self._run([
            "--verdict", "YES",
            "--ci-passed", "true",
            "--changed-files", "engine/foo.py",
            "--labels", "",
            "--round", "0",
        ])
        assert r.returncode == 0
        assert "decision=merge" in r.stdout

    def test_cli_emits_reason(self):
        r = self._run([
            "--verdict", "YES",
            "--ci-passed", "false",
            "--changed-files", "engine/foo.py",
            "--labels", "",
            "--round", "0",
        ])
        assert "decision=human" in r.stdout
        assert "reason=" in r.stdout

    def test_cli_handles_multiple_changed_files_and_labels(self):
        r = self._run([
            "--verdict", "YES",
            "--ci-passed", "true",
            "--changed-files", "engine/foo.py\nREADME.md",
            "--labels", "security\nbug",
            "--round", "0",
        ])
        assert "decision=human" in r.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py::TestCli -q`
Expected: FAIL — the script has no CLI yet (no `decision=` in stdout / nonzero exit).

- [ ] **Step 3: Write minimal implementation** (append to module)

```python
# --- CLI ---

def _parse_bool(s: str) -> bool:
    return s.strip().lower() in ("true", "1", "yes", "success")


def _split_lines(s: str) -> list[str]:
    return [line.strip() for line in s.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Auto-merge gate decision.")
    p.add_argument("--verdict", required=True)            # YES | NO | UNKNOWN
    p.add_argument("--ci-passed", required=True)          # true/false/success
    p.add_argument("--changed-files", default="")         # newline-separated
    p.add_argument("--labels", default="")                # newline-separated
    p.add_argument("--round", type=int, default=0)
    p.add_argument("--max-rounds", type=int, default=3)
    args = p.parse_args(argv)

    result = decide(
        verdict=args.verdict.strip().upper(),
        ci_passed=_parse_bool(args.ci_passed),
        changed_files=_split_lines(args.changed_files),
        labels=_split_lines(args.labels),
        round_count=args.round,
        max_rounds=args.max_rounds,
    )
    print(f"decision={result['decision']}")
    print(f"reason={result['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_auto_merge_gate.py -q`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/auto_merge_gate.py tests/test_auto_merge_gate.py
git commit -m "feat(auto-merge): CLI wrapper emitting GITHUB_OUTPUT-style decision lines"
```

---

## Task 5: The orchestrator workflow (review + gate, report-only first)

This task creates the workflow with the **review** step and the **gate decision**, but the merge is gated behind `vars.AUTO_MERGE_ENABLED` (default `false` → logs "would merge"). The fixer is added in Task 6. Workflows can't be pytest-tested; verification is the real-PR smoke test in Task 7.

**Files:**
- Create: `.github/workflows/auto-review.yml`

- [ ] **Step 1: Create the workflow file**

```yaml
name: auto-review

# Runs on every PR to main. Reviews via claude-code-action, then a deterministic
# gate decides: auto-merge (python-only, approved, green), dispatch the fixer
# (python-only rejection), or leave it for a human. See
# docs/superpowers/specs/2026-06-14-pr-auto-review-fix-merge-design.md
on:
  pull_request:
    types: [opened, ready_for_review, synchronize]
    branches: [main]

concurrency:
  # One run per PR; a new push cancels the in-flight run (avoids racing reviews).
  group: auto-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

permissions:
  contents: write
  pull-requests: write
  id-token: write
  actions: read

jobs:
  review-and-gate:
    # Skip drafts and skip the loop's own fixer commits triggering noise is fine
    # (they SHOULD re-review). Only skip if the PR is a draft.
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    steps:
      - name: Checkout PR head
        uses: actions/checkout@v6
        with:
          fetch-depth: 0
          # PAT so any push we make later re-triggers this workflow (synchronize).
          token: ${{ secrets.WORKFLOW_PAT }}
          ref: ${{ github.event.pull_request.head.ref }}

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Collect PR facts
        id: facts
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
          PR: ${{ github.event.pull_request.number }}
        run: |
          # Changed files (newline-separated).
          gh pr view "$PR" --json files --jq '.files[].path' > changed_files.txt
          # Labels (newline-separated).
          gh pr view "$PR" --json labels --jq '.labels[].name' > labels.txt
          # Round = number of prior auto-fix commits on this branch (marker in msg).
          ROUND=$(git log --pretty=%s origin/main..HEAD | grep -c '^fix(auto):' || true)
          {
            echo "round=$ROUND"
            echo "changed_files<<EOF"; cat changed_files.txt; echo "EOF"
            echo "labels<<EOF"; cat labels.txt; echo "EOF"
          } >> "$GITHUB_OUTPUT"

      - name: Claude review
        id: review
        uses: anthropics/claude-code-action@v1.0.140
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          prompt: |
            Review this pull request for correctness and BEHAVIOR PRESERVATION.
            Focus on real defects, regressions, and broken tests — not style.
            Post a concise human-readable review comment on the PR, and also
            return your verdict via the structured output schema:
              - verdict: "AUTOMERGE" if the change is correct and safe to merge,
                otherwise "HOLD".
              - summary: one sentence.
            If you are unsure, choose "HOLD".
          claude_args: |
            --json-schema '{"type":"object","properties":{"verdict":{"type":"string","enum":["AUTOMERGE","HOLD"]},"summary":{"type":"string"}},"required":["verdict"]}'

      - name: Parse verdict
        id: verdict
        env:
          STRUCTURED: ${{ steps.review.outputs.structured_output }}
        run: |
          # Reuse the tested module for verdict parsing (DRY, fails closed).
          V=$(python - <<'PY'
          import os, sys
          sys.path.insert(0, "scripts")
          import auto_merge_gate as g
          print(g.parse_verdict(os.environ.get("STRUCTURED") or None, None))
          PY
          )
          echo "verdict=$V" >> "$GITHUB_OUTPUT"

      - name: Wait for tests check
        id: ci
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          # Poll the 'tests' check on the head SHA. Do NOT use `gh pr checks --watch`
          # (it would wait on THIS workflow too and deadlock). Wait specifically
          # for the test workflow's check run.
          PASSED=false
          for i in $(seq 1 60); do          # up to ~10 min (60 * 10s)
            STATUS=$(gh api "repos/${GITHUB_REPOSITORY}/commits/${HEAD_SHA}/check-runs" \
              --jq '.check_runs[] | select(.name=="test") | .conclusion' | head -n1)
            STATE=$(gh api "repos/${GITHUB_REPOSITORY}/commits/${HEAD_SHA}/check-runs" \
              --jq '.check_runs[] | select(.name=="test") | .status' | head -n1)
            if [ "$STATE" = "completed" ]; then
              [ "$STATUS" = "success" ] && PASSED=true
              break
            fi
            sleep 10
          done
          echo "passed=$PASSED" >> "$GITHUB_OUTPUT"
        # NOTE: the check-run name "test" matches the job id in test.yml. Confirm
        # during smoke test (Task 7) and adjust the select() name if needed.

      - name: Gate decision
        id: gate
        run: |
          python scripts/auto_merge_gate.py \
            --verdict "${{ steps.verdict.outputs.verdict }}" \
            --ci-passed "${{ steps.ci.outputs.passed }}" \
            --changed-files "${{ steps.facts.outputs.changed_files }}" \
            --labels "${{ steps.facts.outputs.labels }}" \
            --round "${{ steps.facts.outputs.round }}" \
            >> "$GITHUB_OUTPUT"

      - name: Merge (or report-only)
        if: steps.gate.outputs.decision == 'merge'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
          PR: ${{ github.event.pull_request.number }}
          ENABLED: ${{ vars.AUTO_MERGE_ENABLED }}
        run: |
          if [ "$ENABLED" = "true" ]; then
            gh pr merge "$PR" --squash --delete-branch
            echo "Auto-merged PR #$PR."
          else
            echo "REPORT-ONLY: would merge PR #$PR (${{ steps.gate.outputs.reason }})."
          fi

      - name: Leave for human
        if: steps.gate.outputs.decision == 'human'
        env:
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
          PR: ${{ github.event.pull_request.number }}
        run: |
          gh pr comment "$PR" --body "🤖 auto-review: leaving this for a human — ${{ steps.gate.outputs.reason }}."
```

- [ ] **Step 2: Validate the YAML locally**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/auto-review.yml'))" && echo OK`
Expected: `OK` (no YAML syntax errors). *(Install pyyaml if missing: `pip install pyyaml`.)*

- [ ] **Step 3: Run the full test suite (must stay green)**

Run: `.venv/bin/pytest -q`
Expected: PASS — existing 121 + new gate tests.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/auto-review.yml
git commit -m "feat(auto-review): orchestrator workflow — review + gate (report-only)"
```

---

## Task 6: Add the fixer step (Python-only edit + workflow push)

**Files:**
- Modify: `.github/workflows/auto-review.yml`

- [ ] **Step 1: Add the fixer + push steps** (insert AFTER the "Leave for human" step)

```yaml
      - name: Claude fixer (python only)
        if: steps.gate.outputs.decision == 'fix'
        id: fix
        uses: anthropics/claude-code-action@v1.0.140
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          prompt: |
            A reviewer rejected this PR. Read the review feedback on the PR and
            address it by editing ONLY Python files under engine/, tests/, or
            scripts/. Do NOT edit any markdown, docs, or workflow files. Run the
            tests with pytest. Stage and commit your changes with a commit
            message that starts EXACTLY with "fix(auto): ". Do not push.
          claude_args: |
            --allowedTools "Edit,Read,Write,Bash(pytest*),Bash(git add*),Bash(git commit*),Bash(git status*),Bash(git diff*)"
            --disallowedTools "Bash(git push*),Bash(git merge*),Bash(git checkout*),Bash(git rebase*)"

      - name: Push fix if a commit landed
        if: steps.gate.outputs.decision == 'fix'
        env:
          PR: ${{ github.event.pull_request.number }}
          GH_TOKEN: ${{ secrets.WORKFLOW_PAT }}
        run: |
          # Success = a real new commit, never the action's exit code.
          NEW=$(git rev-list --count "origin/${{ github.event.pull_request.head.ref }}..HEAD" 2>/dev/null || echo 0)
          if [ "$NEW" != "0" ] && [ -n "$NEW" ]; then
            git push origin "HEAD:${{ github.event.pull_request.head.ref }}"
            echo "Pushed $NEW fix commit(s); synchronize will trigger re-review."
          else
            gh pr comment "$PR" --body "🤖 auto-review: the fixer produced no commit — leaving this for a human."
          fi
```

- [ ] **Step 2: Validate the YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/auto-review.yml'))" && echo OK`
Expected: `OK`.

- [ ] **Step 3: Full suite green**

Run: `.venv/bin/pytest -q`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/auto-review.yml
git commit -m "feat(auto-review): python-only fixer + PAT push (re-review loop)"
```

---

## Task 7: Rollout — real-PR smoke test, then enable

**This is the most important task. The source pattern's hardest-won lesson: the gate passed all unit tests and two static reviews while being completely inert; the bugs only surfaced against a real PR.** Do NOT skip to enabling merge.

- [ ] **Step 1: Open this feature's PR (report-only is the default state)**

Confirm `vars.AUTO_MERGE_ENABLED` is `false` (`gh variable get AUTO_MERGE_ENABLED`). Open the PR for this branch (the finishing task below). The `auto-review` workflow will run on it.

- [ ] **Step 2: Verify the review path on a Python PR**

On a small throwaway PR that changes only a Python file under `engine/` or `tests/`:
- Confirm the `Claude review` step produced a `structured_output` (check the step log) and `Parse verdict` set `verdict=YES`/`NO`.
- Confirm `Wait for tests check` resolved `passed=true` (and that the `select(.name=="test")` filter actually matched — if `passed` is always false, the check-run name is wrong; fix the `select()` name).
- Confirm `Gate decision` printed the expected `decision=` and `Merge (or report-only)` logged **`REPORT-ONLY: would merge`** (NOT an actual merge).

- [ ] **Step 3: Verify the fixer loop**

On a throwaway Python PR with a deliberate, reviewer-catchable defect (e.g. an obviously wrong return value with a failing test):
- Confirm the review returns HOLD → `decision=fix` → the fixer commits `fix(auto): ...` → `Push fix` pushes → a NEW `auto-review` run starts (proves the PAT re-triggers `synchronize`).
- Confirm `round` increments and that after 3 fix rounds the gate switches to `decision=human` with a "max rounds" comment.

- [ ] **Step 4: Verify the markdown guard**

On a throwaway PR that edits a `skills/**/*.md` file:
- Confirm `decision=human` with reason mentioning markdown, and that the fixer step is **skipped** (never edits prose). This is the Vector B guard — verify it directly.

- [ ] **Step 5: Enable auto-merge**

Once Steps 2–4 are verified against real PRs:
```bash
gh variable set AUTO_MERGE_ENABLED --body "true"
```
Re-run/confirm one Python PR actually squash-merges and deletes its branch.

- [ ] **Step 6: Record the rollout outcome** in `improvement-log.md` (one line: date, what was verified, that merge is now enabled).

```bash
git add improvement-log.md
git commit -m "docs: record auto-review loop rollout + enablement"
```

---

## Finishing the branch (per repo convention)

After all tasks complete and the suite is green:

- [ ] Bump the version in the 3 files + CHANGELOG: `make bump VERSION=<next>` then add a `## [<next>] — 2026-06-14` CHANGELOG entry describing the auto-review loop.
- [ ] Commit the bump: `git add -A && git commit -m "chore: bump to <next>"`.
- [ ] Open the PR to `main` with a description that includes the **manual prerequisites** (PAT, `security` label, `AUTO_MERGE_ENABLED` variable) so they're not forgotten.
- [ ] This PR itself becomes the first real smoke-test subject (report-only).

---

## Self-review notes

- **Spec coverage:** review-request → Task 5 (`Claude review` step + `synchronize` trigger); deterministic gate → Tasks 1–4 + `Gate decision`/`Merge` steps; fixer (python-only, no markdown, no push) → Task 6; round cap → `decide()` + `round` fact; `security` block → `decide()`; path allowlist / Vector B guard → `classify_paths` + `decide()`; report-only rollout → `AUTO_MERGE_ENABLED` + Task 7; verdict fails-closed → `parse_verdict`; "new commit not exit code" → Task 6 push step; PAT re-trigger → checkout token + push.
- **Must-resolve items from the spec:** all four resolved — claude-code-action invocation (Tasks 5/6), verdict capture (structured_output + token fallback), wait-for-CI (check-runs poll, not `--watch`), token/trigger chaining (PAT in checkout + push).
- **Known smoke-test-only unknowns (flagged in Task 7, not guessable):** the exact check-run name for the test workflow (`select(.name=="test")`), and whether `--json-schema` suppresses the human-readable review comment. Both are verified against a real PR before enabling merge.
