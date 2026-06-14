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
