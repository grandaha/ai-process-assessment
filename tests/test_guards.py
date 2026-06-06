"""Anti-regression guards. Each guard names, in a comment, the defect it defends.

This file grows in three tasks:
  Task 7 — data-arch (this section)
  Task 8 — #5 isolation and #8 ordering
"""
import re
from pathlib import Path

from methodology_model import REPO_ROOT

# --- Data-arch guard (defends: per-OPP data-architecture normalization, v2.1.0) ---
# After normalization, per-OPP artifacts live in the opportunities/, scores/, and
# grc/ folders. The monolithic files opportunities.md and scored-opportunities.md
# are retired and must not be referenced anywhere in skills/ or agents/.
#   - (?<![\w-])opportunities\.md  matches the retired monolith but NOT the
#     opportunities/ folder (no ".md") and NOT scored-opportunities.md (preceded by "-").
#   - scored-opportunities\.md     matches the other retired monolith.
RETIRED_FILE_PATTERNS = [
    re.compile(r"(?<![\w-])opportunities\.md"),
    re.compile(r"scored-opportunities\.md"),
]


def _methodology_markdown_files() -> list[Path]:
    return sorted(
        list((REPO_ROOT / "skills").rglob("SKILL.md"))
        + list((REPO_ROOT / "agents").glob("*.md"))
    )


def test_no_retired_monolithic_file_references():
    offenders = []
    for path in _methodology_markdown_files():
        text = path.read_text(encoding="utf-8")
        for pat in RETIRED_FILE_PATTERNS:
            if pat.search(text):
                rel = path.relative_to(REPO_ROOT)
                offenders.append(f"{rel} :: {pat.pattern}")
    assert not offenders, "retired-file references found:\n" + "\n".join(offenders)
