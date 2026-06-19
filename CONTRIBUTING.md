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

The suite is LLM-free and runs in seconds. The full suite must pass before a PR will be accepted. This is also the **clean-machine smoke check (AC-2)**: if `pip install -r requirements.txt && pytest -q` fails on a fresh clone, the plugin is broken for new users and the release is blocked.

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

## Fork PRs and the automated review loop

If you are an external contributor, open a PR **from a fork**. A few things to know:

- **CI tests run on your fork PR** via the `test` workflow. The test suite is LLM-free and does not use any secrets, so it runs exactly as on an internal PR.
- **The auto-review / fix / merge loop does NOT run on fork PRs.** It is explicitly skipped when `head.repo.full_name != github.repository`. A maintainer will review your PR manually.
- **`@claude` bot:** Do not expect `@claude` to respond on your fork PR — maintainers may invoke it internally during review, but it does not automatically respond to fork PR comments.
- **Auto-merge is disabled for fork PRs** — all fork PRs require a human approval and merge.

See [SECURITY.md](SECURITY.md) for the full CI security model.

## Releasing

Releases are automated. To cut version `X.Y.Z`:

1. Bump the version in three files so CI stays green: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `INSTALL.md`. (A guard test fails if they disagree.)
2. Add a `## [X.Y.Z] — <date>` section to `CHANGELOG.md` describing the changes.
3. Tag and push:

   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z — <summary>"
   git push origin vX.Y.Z
   ```

The `release` workflow then verifies the tag matches the manifest, runs the test suite (AC-2 clean-machine check), builds `ai-process-assessment-vX.Y.Z.zip` with `git archive`, extracts the notes from `CHANGELOG.md`, and publishes a GitHub Release with the zip attached. Never commit the zip — release artifacts live only on GitHub Releases. If a release fails partway, re-run it from the Actions tab via **Run workflow** (the `release` workflow accepts a tag input and is idempotent).

## Reporting security issues

Do **not** open a public issue for security vulnerabilities. See [SECURITY.md](SECURITY.md) for the responsible disclosure process.

## Engagement data

Never commit client or engagement data. Engagement folders live at the project root and must be gitignored by name — add each engagement folder to `.gitignore` before committing.
