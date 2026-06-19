# Security Policy

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security vulnerabilities. Instead, use [GitHub's private vulnerability reporting](https://github.com/grandaha/ai-process-assessment/security/advisories/new) (Security → Advisories → Report a vulnerability). We aim to respond within 7 days and to publish a fix or mitigation within 30 days.

## CI security model for fork pull requests

This repository runs an automated PR review, fix, and merge loop (introduced in v2.9.0). The loop uses repository secrets (`CLAUDE_CODE_OAUTH_TOKEN`, `WORKFLOW_PAT`) and can push commits and merge PRs. The following controls are in place to protect against untrusted fork code:

### auto-review.yml (auto-review / fix / merge loop)

This workflow is **skipped entirely for fork PRs** via an explicit job-level condition:

```yaml
if: >-
  github.event.pull_request.draft == false &&
  github.event.pull_request.head.repo.full_name == github.repository
```

A PR from a fork (`head.repo.full_name != github.repository`) causes the job to be skipped. No secrets are accessed, no code is executed, and no merge can be triggered.

### test.yml (CI tests)

This workflow uses the `pull_request` event (not `pull_request_target`), which GitHub sandboxes: **secrets are not available** to workflows triggered by fork PRs via the `pull_request` event. The test runner installs only declared dependencies from `requirements.txt` and runs the static, LLM-free test suite. There are no network calls to external services in the test suite.

### claude.yml (@claude bot)

The `@claude` bot workflow is triggered by `issue_comment`, `pull_request_review_comment`, `pull_request_review`, and `issues` events. Unlike `pull_request`, these events run with **base-repo context and have access to secrets** even when the triggering comment is on a fork PR.

**Mitigation in place:** The auto-review loop is already scoped to same-repo PRs. The `@claude` bot does not have permission to merge PRs or modify protected branches — those actions require `WORKFLOW_PAT`, which is only used in the auto-review loop.

**Remaining exposure:** A maintainer (or any user with write access to the base repo) commenting `@claude` on a fork PR will trigger the bot with access to `CLAUDE_CODE_OAUTH_TOKEN`. External contributors who open fork PRs **cannot themselves trigger the bot** — `issue_comment` on a PR fires in base-repo context, but the bot only responds to comments containing `@claude`. If a fork contributor posts `@claude` on their own PR, the workflow fires with secrets available.

**Recommended additional control (requires manual workflow update):** Add a check to `claude.yml` that restricts `@claude` triggers to users with `write` or higher association:

```yaml
if: |
  contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association)
```

This is not yet in place and requires a maintainer to update `.github/workflows/claude.yml`.

### Deterministic gate (scripts/auto_merge_gate.py)

The merge gate module is explicitly listed as a protected file:

```python
PROTECTED_FILES = ("scripts/auto_merge_gate.py",)
```

Any PR that touches this file routes to human review, not auto-merge, regardless of the Claude verdict.

## Secrets in use

| Secret | Purpose | Scope |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code authentication for the review and @claude bot | Used in `auto-review.yml` and `claude.yml` |
| `WORKFLOW_PAT` | Push commits and merge PRs (bypasses GITHUB_TOKEN cascade restriction) | Used in `auto-review.yml` and `auto-tag.yml` |

Neither secret is logged or printed by any step. The `WORKFLOW_PAT` is used only in the same-repo-only auto-review workflow.

## Engagement data

Never commit client or engagement data to this repository. Engagement folders live at the project root and must be added to `.gitignore` by name before any commit. The `.gitignore` already excludes `sample-pso-delivery/` (the bundled demo output) and `docs/superpowers/` (internal planning).
