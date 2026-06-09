#!/usr/bin/env python3
"""Extract one version's release notes from a Keep-a-Changelog CHANGELOG.md.

Used by .github/workflows/release.yml. Kept tiny and import-safe so the test
suite can exercise `extract` directly.
"""
import re
import sys
from pathlib import Path


def extract(changelog: str, version: str) -> str:
    """Return the body of the `## [version]` section (header line excluded).

    Stops at the next `## [` header. Raises KeyError if the section is absent.
    """
    lines = changelog.splitlines()
    header_re = re.compile(r"^## \[" + re.escape(version) + r"\]")
    next_re = re.compile(r"^## \[")
    start = None
    for i, line in enumerate(lines):
        if header_re.match(line):
            start = i
            break
    if start is None:
        raise KeyError(f"no CHANGELOG section for version {version!r}")
    body = []
    for line in lines[start + 1:]:
        if next_re.match(line):
            break
        body.append(line)
    return "\n".join(body).strip() + "\n"


def main(argv) -> int:
    if len(argv) != 2:
        print("usage: extract_changelog.py <version>", file=sys.stderr)
        return 2
    version = argv[1]
    changelog_path = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
    try:
        notes = extract(changelog_path.read_text(encoding="utf-8"), version)
    except KeyError as e:
        print(f"::error::{e}", file=sys.stderr)
        return 1
    sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
