# Release Process — Design

**Date:** 2026-06-09
**Status:** Approved (pending user review)
**Author:** Dave Raffaele + Claude

## Problem

Releases were hand-run and error-prone. Symptoms observed:

- **Build artifacts leaked into the working tree.** `*.zip` is not gitignored, so `ai-process-assessment-v2.6.0.zip` sat untracked and could have been committed.
- **Tag/Release gap.** Nine tags exist (`v2.0.0`–`v2.7.0`) but only two GitHub Releases (`v2.5.1`, `v2.7.0`). Seven versions have no downloadable artifact.
- **Version drift.** `marketplace.json` silently fell to `2.5.1` while `plugin.json` was `2.6.0`. Three files carry the version and nothing enforced their agreement.
- **No automation.** Every step (bump, tag, build zip, create release, attach asset, write notes) was manual, so steps got skipped under time pressure.

## Decisions (settled with user)

| Question | Decision |
|---|---|
| Where do release zips live? | **GitHub Releases only.** Never commit binaries. The Releases page is the version archive. |
| How are releases created? | **Automated GitHub Actions workflow** triggered on tag push. |
| Backfill old versions? | **Yes — all 7** (`v2.0.0`–`v2.6.0`), making the Releases page a gapless archive. |
| Workflow trigger | **Tag push (`v*.*.*`) + `workflow_dispatch`** for manual recovery. |
| Docs | Short "Releasing" blurb in `CONTRIBUTING.md`. |
| Release action | First-party `gh` CLI + built-in `GITHUB_TOKEN` (no third-party action). |

## Components

### 1. `.gitignore` — root-cause fix

Add `*.zip`. Remove the local `ai-process-assessment-v2.7.0.zip` from the working tree (already attached to its Release). Build artifacts can never be committed again.

### 2. `.github/workflows/release.yml` — release automation

**Triggers:** `push` on tags matching `v*.*.*`; plus `workflow_dispatch` (with a `tag` input) for re-running a failed release without re-tagging.

**Permissions:** `contents: write` (required to create a Release).

**Steps, each gating the next:**

1. **Checkout** at the tag, `fetch-depth: 0` (so `git archive` and CHANGELOG are available).
2. **Version-consistency check.** Derive `TAG_VERSION` from the tag (strip leading `v`). Read the version from `.claude-plugin/plugin.json`. Assert equal; fail with a clear message otherwise. *(This is what would have caught the 2.5.1 drift at release time.)*
3. **Test gate.** `setup-python` 3.12 → `pip install -r requirements.txt` → `pytest -q`. Mirrors `test.yml`. No green tests, no release.
4. **Build zip.** `git archive --format=zip -o ai-process-assessment-v${TAG_VERSION}.zip ${TAG}` — root-level files, matching existing artifact naming.
5. **Extract notes.** `awk`/`sed` the `## [X.Y.Z]` section out of `CHANGELOG.md` into a notes file.
6. **Create the Release.** `gh release create "$TAG" ai-process-assessment-v${TAG_VERSION}.zip --title "..." --notes-file notes.md` using `GITHUB_TOKEN`. Idempotency: if the Release already exists (manual dispatch re-run), `gh release upload --clobber` the asset and `gh release edit` the notes instead of failing.

### 3. `tests/test_version_consistency.py` — drift guard (defense in depth)

A unit test asserting:
- The version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `INSTALL.md` all match.
- `CHANGELOG.md` has a `## [<version>]` section for that version.

Runs in `test.yml` on every PR/push, so drift fails **before** a tag is ever cut — complementing the workflow's release-time check.

### 4. Backfill — one-time

For each tag `v2.0.0 … v2.6.0`:
1. Extract its CHANGELOG section → notes.
2. `git archive --format=zip` from the tag → versioned zip.
3. `gh release create <tag> <zip> --title "<tag>" --notes-file notes`. Backfilled Releases use the plain tag as the title (e.g. `v2.4.0`) since CHANGELOG sections carry no descriptive title — no titles are invented. (The two existing Releases keep their richer hand-written titles; only the seven new ones use the plain form.)

All seven versions have CHANGELOG entries, so notes are sourced, not invented. Verify each Release (asset attached, notes present) before the next. The zips built here are transient (gitignored, deleted after upload).

### 5. `CONTRIBUTING.md` — "Releasing" section

~5 lines: bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `INSTALL.md`; add a `CHANGELOG.md` section; `git tag -a vX.Y.Z -m ...`; `git push origin vX.Y.Z`. The workflow builds the zip, creates the Release, and attaches the asset. Note the version-consistency guard will fail the workflow if the three files disagree.

## Out of scope

- Changing the version-bump from manual to automated (e.g. release-please). The manual bump + guard test is sufficient and keeps the human in control of semver.
- Signing/notarizing artifacts.
- Backfilling `v1.x` (pre-2.0 history not in scope).

## Success criteria

- Pushing a `vX.Y.Z` tag (after a version bump) produces a complete GitHub Release — zip asset + CHANGELOG notes — with zero manual steps after the push.
- A version-drift across the three files fails CI before tagging.
- The Releases page lists every `v2.x` version with a downloadable zip.
- No `*.zip` can be committed to the repo.
