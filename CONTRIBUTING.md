# Contributing

Thanks for your interest in improving this plugin.

## Setup

```bash
git clone https://github.com/grandaha/ai-process-assessment
cd ai-process-assessment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Enable the pre-push test gate (recommended):

```bash
git config core.hooksPath .githooks
```

## Running tests

```bash
pytest -q
```

The suite is LLM-free and runs in seconds. The full suite must pass before a PR will be accepted.

## What to work on

Check the [open issues](https://github.com/grandaha/ai-process-assessment/issues) for ideas. Good first contributions:

- Methodology improvements (skill files in `skills/`)
- New or improved agent prompts (`agents/`)
- Engine accuracy or coverage (`engine/`)
- Additional test coverage (`tests/`, `engine/tests/`)

## Pull request guidelines

- One logical change per PR.
- If you change a skill or agent, verify the corresponding tests still pass and add new ones for any new behavior.
- If you change a number the engine produces, update the golden fixtures in `engine/tests/fixtures/`.
- Keep `CHANGELOG.md` updated under `[Unreleased]` using [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

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

## Engagement data

Never commit client or engagement data. Engagement folders live at the project root and must be gitignored by name — add each engagement folder to `.gitignore` before committing.
