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

The suite is LLM-free and runs in seconds. All 100 tests must pass before a PR will be accepted.

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

## Engagement data

Never commit client or engagement data. `docs/engagements/` is gitignored — keep it that way.
