# Release Process Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make releases reproducible and un-rushable — a `vX.Y.Z` tag push builds the zip, runs tests, and creates a complete GitHub Release automatically, while CI guards against version drift and `*.zip` artifacts can never be committed.

**Architecture:** Five components. (1) `.gitignore` stops zip artifacts at the source. (2) A small tested Python script extracts a version's notes from `CHANGELOG.md`. (3) `tests/test_plugin_manifest.py` is extended to assert all three version files agree and a CHANGELOG section exists — drift fails CI at PR time. (4) `.github/workflows/release.yml` turns a tag push into a Release (version check → tests → zip → notes → asset), with `workflow_dispatch` for recovery. (5) A one-time backfill gives the seven tag-only versions real Releases.

**Tech Stack:** GitHub Actions, first-party `gh` CLI + `GITHUB_TOKEN`, Python 3 stdlib, pytest, `git archive`.

**Delivery:** Code changes (Tasks 1–4, 6) land on one branch → PR → merge. Operational steps (Task 5 validation, Task 7 backfill) run from `main` after merge. Spec: `docs/superpowers/specs/2026-06-09-release-process-design.md`.

---

## File Structure

- `.gitignore` — add `*.zip` (Task 1).
- `.github/scripts/extract_changelog.py` — **new.** Pure `extract(changelog, version)` fn + CLI. Sole owner of "turn CHANGELOG into release notes" (Task 2).
- `tests/test_changelog_extract.py` — **new.** Unit tests for the extractor (Task 2).
- `tests/test_plugin_manifest.py` — **modify.** Add `marketplace.json` agreement + CHANGELOG-section checks (Task 3).
- `.github/workflows/release.yml` — **new.** The release automation (Task 4).
- `CONTRIBUTING.md` — **modify.** Add a "Releasing" section; fix stale test count (Task 6).

---

## Task 1: Stop zip artifacts from being committable

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add the ignore rule**

Append to `.gitignore` (after the `*.swo` block near the top, or at end — order doesn't matter):

```
# Release build artifacts (zips live on GitHub Releases, never in the repo)
*.zip
```

- [ ] **Step 2: Remove the stray local artifact**

```bash
rm -f ai-process-assessment-v2.7.0.zip
```

- [ ] **Step 3: Verify the rule works**

Run: `touch test-artifact.zip && git status --porcelain | grep -c "\.zip" ; rm -f test-artifact.zip`
Expected: prints `0` (the zip is ignored, not shown as untracked).

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore *.zip — release artifacts live on GitHub Releases, not in the repo"
```

---

## Task 2: CHANGELOG → release-notes extractor (tested)

**Files:**
- Create: `.github/scripts/extract_changelog.py`
- Test: `tests/test_changelog_extract.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_changelog_extract.py`:

```python
import importlib.util

import pytest

from methodology_model import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "extract_changelog",
    REPO_ROOT / ".github" / "scripts" / "extract_changelog.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
extract = _mod.extract


SAMPLE = """# Changelog

## [Unreleased]

## [2.7.0] — 2026-06-09

### Changed
- Data architecture convergence.

## [2.6.0] — 2026-06-09

### Added
- Old stuff.
"""


def test_extracts_named_section_body_only():
    out = extract(SAMPLE, "2.7.0")
    assert "### Changed" in out
    assert "Data architecture convergence." in out
    # Stops at the next section header — does not bleed into 2.6.0.
    assert "Old stuff" not in out
    assert "## [2.6.0]" not in out


def test_section_header_line_is_not_included():
    out = extract(SAMPLE, "2.7.0")
    assert "## [2.7.0]" not in out


def test_missing_version_raises_keyerror():
    with pytest.raises(KeyError):
        extract(SAMPLE, "9.9.9")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_changelog_extract.py -v`
Expected: FAIL — `FileNotFoundError` / import error because `.github/scripts/extract_changelog.py` does not exist yet.

- [ ] **Step 3: Write the extractor**

Create `.github/scripts/extract_changelog.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_changelog_extract.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Verify the CLI against the real CHANGELOG**

Run: `python .github/scripts/extract_changelog.py 2.7.0`
Expected: prints the v2.7.0 section body (starts with `### Changed`), no header line, stops before `## [2.6.0]`.

Run: `python .github/scripts/extract_changelog.py 9.9.9; echo "exit=$?"`
Expected: prints `::error::...` to stderr and `exit=1`.

- [ ] **Step 6: Commit**

```bash
git add .github/scripts/extract_changelog.py tests/test_changelog_extract.py
git commit -m "feat(release): tested CHANGELOG release-notes extractor"
```

---

## Task 3: Version-drift guard — extend the manifest test

**Files:**
- Modify: `tests/test_plugin_manifest.py`

The existing file already checks `plugin.json` semver and `plugin.json` ↔ `INSTALL.md`. Add the missing `marketplace.json` agreement (the file that drifted to 2.5.1) and a CHANGELOG-section presence check.

- [ ] **Step 1: Add the two new tests**

In `tests/test_plugin_manifest.py`, add the `MARKETPLACE_JSON` and `CHANGELOG_MD` paths next to the existing `PLUGIN_JSON` / `INSTALL_MD` constants (after line 16):

```python
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"
```

Then append these two tests at the end of the file:

```python
def test_marketplace_json_version_matches_plugin_json():
    version = _plugin_version()
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])
    match = next((p for p in plugins if p.get("name") == "ai-process-assessment"), None)
    assert match is not None, "ai-process-assessment entry missing from marketplace.json"
    assert match.get("version") == version, \
        f"marketplace.json version {match.get('version')} != plugin.json version {version}"


def test_changelog_has_section_for_current_version():
    version = _plugin_version()
    changelog = CHANGELOG_MD.read_text(encoding="utf-8")
    assert re.search(r"^## \[" + re.escape(version) + r"\]", changelog, re.MULTILINE), \
        f"CHANGELOG.md has no '## [{version}]' section"
```

- [ ] **Step 2: Run the new tests to verify they pass (current state is in sync)**

Run: `python -m pytest tests/test_plugin_manifest.py -v`
Expected: PASS — all versions are currently `2.7.0` and the CHANGELOG has a `[2.7.0]` section.

- [ ] **Step 3: Prove the guard actually guards (temporary red)**

A guard test that only ever passes is worthless. Introduce drift, confirm red, revert, confirm green:

```bash
# Break marketplace.json version, confirm the guard catches it
python - <<'PY'
import json, pathlib
p = pathlib.Path(".claude-plugin/marketplace.json")
d = json.loads(p.read_text())
d["plugins"][0]["version"] = "0.0.1"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
python -m pytest tests/test_plugin_manifest.py::test_marketplace_json_version_matches_plugin_json -q
```
Expected: FAIL (`marketplace.json version 0.0.1 != plugin.json version 2.7.0`).

```bash
# Revert and confirm green
git checkout .claude-plugin/marketplace.json
python -m pytest tests/test_plugin_manifest.py -q
```
Expected: PASS. **Confirm `git status` shows `marketplace.json` clean before committing.**

- [ ] **Step 4: Commit**

```bash
git add tests/test_plugin_manifest.py
git commit -m "test(release): guard marketplace.json version + CHANGELOG section against drift"
```

---

## Task 4: Release automation workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/release.yml`:

```yaml
name: release

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:
    inputs:
      tag:
        description: "Tag to (re)release, e.g. v2.7.0"
        required: true

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Resolve tag
        id: tag
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "tag=${{ github.event.inputs.tag }}" >> "$GITHUB_OUTPUT"
          else
            echo "tag=${GITHUB_REF_NAME}" >> "$GITHUB_OUTPUT"
          fi

      - uses: actions/checkout@v6
        with:
          ref: ${{ steps.tag.outputs.tag }}
          fetch-depth: 0

      - name: Verify tag matches manifest version
        run: |
          TAG="${{ steps.tag.outputs.tag }}"
          TAG_VERSION="${TAG#v}"
          MANIFEST_VERSION="$(python -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")"
          if [ "$TAG_VERSION" != "$MANIFEST_VERSION" ]; then
            echo "::error::Tag $TAG (version $TAG_VERSION) != plugin.json version $MANIFEST_VERSION"
            exit 1
          fi

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -q

      - name: Build release zip
        run: |
          TAG="${{ steps.tag.outputs.tag }}"
          git archive --format=zip -o "ai-process-assessment-${TAG}.zip" "$TAG"

      - name: Extract release notes
        run: |
          TAG="${{ steps.tag.outputs.tag }}"
          python .github/scripts/extract_changelog.py "${TAG#v}" > RELEASE_NOTES.md
          echo "----- notes -----"; cat RELEASE_NOTES.md

      - name: Create or update GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          TAG="${{ steps.tag.outputs.tag }}"
          ASSET="ai-process-assessment-${TAG}.zip"
          if gh release view "$TAG" >/dev/null 2>&1; then
            gh release upload "$TAG" "$ASSET" --clobber
            gh release edit "$TAG" --notes-file RELEASE_NOTES.md
          else
            gh release create "$TAG" "$ASSET" --title "$TAG" --notes-file RELEASE_NOTES.md
          fi
```

- [ ] **Step 2: Verify the YAML is valid**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('valid yaml')"`
Expected: prints `valid yaml` (no exception).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "feat(release): tag-push workflow builds zip + creates GitHub Release (version-checked, test-gated)"
```

---

## Task 6: Document the release ritual

**Files:**
- Modify: `CONTRIBUTING.md`

(Task 5 — workflow validation — runs after merge; see the Post-Merge section. Numbered 5/6 to keep code tasks together.)

- [ ] **Step 1: Fix the stale test count**

In `CONTRIBUTING.md`, under `## Running tests`, replace:

```markdown
The suite is LLM-free and runs in seconds. All 100 tests must pass before a PR will be accepted.
```

with:

```markdown
The suite is LLM-free and runs in seconds. The full suite must pass before a PR will be accepted.
```

- [ ] **Step 2: Add the Releasing section**

In `CONTRIBUTING.md`, after the `## Pull request guidelines` section and before `## Engagement data`, insert:

```markdown
## Releasing

Releases are automated. To cut version `X.Y.Z`:

1. Bump the version in three files so CI stays green: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `INSTALL.md`. (A guard test fails if they disagree.)
2. Add a `## [X.Y.Z] — <date>` section to `CHANGELOG.md` describing the changes.
3. Tag and push:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z — <summary>"
   git push origin vX.Y.Z
   ```

The `release` workflow then verifies the tag matches the manifest, runs the test suite, builds `ai-process-assessment-vX.Y.Z.zip` with `git archive`, extracts the notes from `CHANGELOG.md`, and publishes a GitHub Release with the zip attached. Never commit the zip — release artifacts live only on GitHub Releases. If a release fails partway, re-run it from the Actions tab via **Run workflow** (the `release` workflow accepts a tag input and is idempotent).
```

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: document the automated release process; fix stale test count"
```

---

## Task 7: Land the code changes (branch → PR → merge)

- [ ] **Step 1: Confirm full suite green before pushing**

Run: `python -m pytest -q`
Expected: PASS (115 prior + 3 extractor + 2 manifest = 120 tests).

- [ ] **Step 2: Push the branch and open a PR**

This work should be on a branch named `feat/release-automation` (create it before Task 1 if not already). Push and open a PR:

```bash
git push -u origin feat/release-automation
gh pr create --base main \
  --title "Release automation: tag-push workflow, drift guards, gitignore zips" \
  --body "Implements docs/superpowers/specs/2026-06-09-release-process-design.md. A vX.Y.Z tag push now builds the zip, runs tests, and publishes a GitHub Release automatically. Adds version-drift guards (marketplace.json + CHANGELOG) and gitignores *.zip. Backfill of the 7 tag-only releases runs after merge."
```

- [ ] **Step 3: Request review and merge**

Comment `@claude review` on the PR, address any findings, then merge with `--merge --delete-branch` once green.

---

## Post-Merge — operational steps (run from `main`)

### Task 5 (validation): Exercise the workflow against a known-good release

Once `release.yml` is on `main`, `workflow_dispatch` is available.

- [ ] **Step 1: Re-run the v2.7.0 release through the workflow**

```bash
git checkout main && git pull
gh workflow run release.yml -f tag=v2.7.0
sleep 10 && gh run list --workflow=release.yml -L 1
```

- [ ] **Step 2: Watch it and confirm success**

```bash
RUN_ID=$(gh run list --workflow=release.yml -L 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN_ID" --exit-status
```
Expected: the run passes. The v2.7.0 Release's asset is re-uploaded (`--clobber`) and its notes are re-set from CHANGELOG. Confirm the v2.7.0 Release still has exactly one `ai-process-assessment-v2.7.0.zip` asset:

Run: `gh release view v2.7.0 --json assets -q '[.assets[].name]'`
Expected: `["ai-process-assessment-v2.7.0.zip"]`

### Task 7 (backfill): Create the 7 missing Releases

Backfill reads the **current** `CHANGELOG.md` (on `main`, which has every historical section — old tags predate the CHANGELOG) and builds each zip from its tag.

- [ ] **Step 1: Backfill loop**

```bash
cd "$(git rev-parse --show-toplevel)"
for tag in v2.0.0 v2.1.0 v2.2.0 v2.3.0 v2.4.0 v2.5.0 v2.6.0; do
  ver="${tag#v}"
  if gh release view "$tag" >/dev/null 2>&1; then
    echo "SKIP $tag (release exists)"; continue
  fi
  python .github/scripts/extract_changelog.py "$ver" > "/tmp/notes-$ver.md" || { echo "no notes for $ver"; continue; }
  git archive --format=zip -o "ai-process-assessment-$tag.zip" "$tag"
  gh release create "$tag" "ai-process-assessment-$tag.zip" --title "$tag" --notes-file "/tmp/notes-$ver.md"
  rm -f "ai-process-assessment-$tag.zip"
done
```

- [ ] **Step 2: Verify the archive is gapless**

Run: `gh release list -L 12`
Expected: every `v2.0.0`–`v2.7.0` tag now has a Release. v2.7.0 is Latest.

Run: `for t in v2.0.0 v2.1.0 v2.2.0 v2.3.0 v2.4.0 v2.5.0 v2.6.0; do echo "$t: $(gh release view $t --json assets -q '[.assets[].name]|join(",")')"; done`
Expected: each line shows its `ai-process-assessment-<tag>.zip` asset.

- [ ] **Step 3: Confirm no stray zips remain locally**

Run: `ls *.zip 2>/dev/null && echo "STRAY ZIP" || echo "clean"`
Expected: `clean`.

---

## Self-Review

**Spec coverage:**
- Part 1 (`*.zip` gitignore + remove local zip) → Task 1. ✅
- Part 2 (release workflow: version check → tests → zip → notes → asset; tag push + dispatch; gh CLI) → Task 4 (+ extractor in Task 2). ✅
- Part 3 (drift guard test: 3 files agree + CHANGELOG section) → Task 3. ✅
- Part 4 (backfill all 7) → Task 7 (post-merge). ✅
- Part 5 (CONTRIBUTING blurb) → Task 6. ✅
- Decision "gh CLI not third-party action" → Task 4 uses `gh` + `GITHUB_TOKEN`. ✅
- Decision "workflow_dispatch recovery" → Task 4 trigger + Task 5 validation exercises it. ✅
- Success criterion "tag push → complete Release, zero manual steps" → Task 4. ✅
- Success criterion "drift fails CI before tagging" → Task 3 (PR-time) + Task 4 verify step (release-time). ✅
- Success criterion "every v2.x has a downloadable zip" → Task 7. ✅
- Success criterion "no *.zip committable" → Task 1. ✅

**Placeholder scan:** No TBD/TODO. Every code step shows complete content; every command shows expected output.

**Type/name consistency:** `extract(changelog, version)` defined in Task 2 is imported identically in its test and called in Task 4's workflow via the CLI `main`. Asset name `ai-process-assessment-${TAG}.zip` is identical across Task 4 build/create steps, Task 5 verify, and Task 7 backfill. The three version files named in Task 3 match those in the Task 6 docs and the spec's touch-point list.

**Note on numbering:** Tasks run 1→2→3→4→6 (code, pre-merge), then 5 (validation) and 7 (backfill) post-merge. The out-of-order 5/6 keeps all code tasks contiguous before the PR.
