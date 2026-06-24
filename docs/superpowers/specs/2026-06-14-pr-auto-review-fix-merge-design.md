# PR Auto-Review-Fix-Merge Loop — Design

**Date:** 2026-06-14
**Status:** Approved for planning
**Author:** Dave (with Claude)

## Summary

An autonomous loop that runs on every pull request to `main`: Claude reviews the
PR, and if it finds issues, a Claude fixer addresses them and pushes; the PR is
re-reviewed; this repeats until the review passes (bounded). A deterministic gate
then auto-merges — but **only for test-covered Python** (`engine/`, `tests/`,
`scripts/`) with green CI. PRs touching markdown get the same auto-review + (Python-
only) auto-fix but stop at "approved — ready for the user to merge," keeping a
human on untested, published methodology content.

This is a deliberate adaptation of the "Autonomous Code-Quality Routine"
pattern (Grandaha platform). Two differences from the source:

1. **No finder.** The source ran a scheduled job that hunted the codebase for
   problems and filed labeled issues. Here, **the trigger is a PR the user
   deliberately opens** — there is no autonomous issue-hunting, no dedup
   problem, and no blast-radius question from auto-filed work.
2. **Review→fix→re-review loop.** The source built a fix from an issue once.
   Here, the loop iterates: Claude reviews, the fixer addresses feedback, and
   the PR is re-reviewed until it passes or a round cap is hit.

What is preserved from the source (its whole point): **deterministic code
orchestrates; the LLM only does the creative step (review, fix). The merge is
performed only by a deterministic gate — the agent has zero merge authority.**

## Goals

- Every PR to `main` is automatically reviewed by Claude — the user never has to
  manually request review.
- **Test-covered Python PRs** that Claude approves are auto-merged (squash,
  delete branch) once CI is green.
- PRs Claude does not approve have their **Python** issues auto-fixed by Claude
  and are re-reviewed, looping until approval or a round cap.
- The whole thing is hands-off for Python: the user opens a PR and, in the normal
  case, returns to a merged PR with a clean history.

## Safe Class (what may auto-merge)

The auto-merge gate distinguishes two classes by **changed-file path**:

- **Auto-merge eligible (the "safe class"):** a PR whose changed files are *all*
  under `engine/`, `tests/`, or `scripts/` — the test-covered Python. The 121
  pytest tests are the behavior backstop.
- **Human-merge only:** any PR that touches markdown (`skills/`, `agents/`,
  `system-prompt.md`, `templates/`, `docs/`, `*.md`) or any path outside the
  allowlist. These still get auto-review + (Python-only) auto-fix and can reach
  `AUTOMERGE: YES`, but the gate stops at "approved — ready for the user to
  merge." A human always clicks merge on untested prose.

Rationale: markdown is the product's methodology content, has **no test
backstop**, and ships to everyone via the published marketplace plugin. A
semantic regression there is silent and high-blast-radius, so it keeps a human
in the loop. (See Risks → "the two vectors".)

## Non-Goals

- **No autonomous issue-finding.** No finder, no scheduled codebase scan, no
  auto-filed issues. (Explicitly dropped from the source pattern.)
- **No autonomous authoring of methodology.** The fixer never edits markdown
  (see "the two vectors"); Claude cannot review-and-merge its own prose changes.
- Not a replacement for the user's own judgment on large/architectural PRs — the
  round cap, the human-merge class, and report-only rollout exist to keep a human
  in the loop where the loop should not run unattended.

## Current-State Facts (verified 2026-06-13)

- **CI signal:** [`.github/workflows/test.yml`](../../../.github/workflows/test.yml)
  runs `pytest -q` on every push and PR. **121 tests** currently. This is the
  gate's "CI green" signal (the `tests` workflow conclusion).
- **Reviewer:** [`.github/workflows/claude.yml`](../../../.github/workflows/claude.yml)
  runs `anthropics/claude-code-action@v1.0.140` when a comment/review/issue
  contains `@claude`. Authenticates via the `CLAUDE_CODE_OAUTH_TOKEN` secret
  (Claude subscription, **no GitHub App**), so it posts as **`github-actions[bot]`**,
  not `claude[bot]`. It already has `contents: write` and `pull-requests: write`.
- **No finder, no orchestrator script, no `code-quality`/`security` labels** exist
  yet. (`security` label will be created; `code-quality` is not needed in this
  design since there is no safe-class path restriction.)
- Repo composition: ~70% markdown (skills, agents, system-prompt, templates,
  docs), ~30% Python (`engine/`, `tests/`). Only the Python is test-covered.

## Architecture

Three additions, all GitHub Actions, reusing the existing reviewer + CI:

```
User opens a PR to main
        │
        ▼
  review-request.yml ── posts "@claude review … end with AUTOMERGE: YES/NO"
        │                (fires on opened, ready_for_review, synchronize)
        ▼
  claude.yml (existing) ── @claude reviews, posts verdict as github-actions[bot]
        │
        ▼
  gate.yml  (pure shell/gh — NO Claude here)
   ├─ parse verdict (fails closed on missing / NO / empty)
   │
   ├─ AUTOMERGE: YES ──► wait for `tests` check
   │                      ├─ CI green AND no `security` label AND
   │                      │    all changed files under engine|tests|scripts
   │                      │      ──► squash-merge + delete branch
   │                      └─ otherwise (incl. any markdown touched)
   │                           ──► leave PR open for a human ("approved, ready to merge")
   │
   └─ AUTOMERGE: NO  ──► round cap reached?
                          ├─ yes ──► post "max auto-fix rounds reached — over to you", stop
                          └─ no  ──► Python-only changes requested?
                                       ├─ no (markdown feedback) ──► leave for human, stop
                                       └─ yes ──► dispatch the FIXER step
                                            (claude-code-action: edit/commit/PUSH Python only, no merge)
                                            └─ push triggers synchronize ──► re-review (loop top)
```

### Component 1 — `review-request.yml`

- **Trigger:** `pull_request` types `[opened, ready_for_review, synchronize]`,
  base branch `main`.
- **Action:** post a PR comment:
  > `@claude` Please review this PR for correctness and behavior-preservation.
  > End your review with a final line that is exactly `AUTOMERGE: YES` or
  > `AUTOMERGE: NO`.
- **Why `synchronize`:** every new commit — whether the user's or the fixer's —
  triggers a fresh review. This is the loop's re-review edge; no separate
  re-trigger plumbing is needed.
- **Loop-safety note:** the comment is posted by `github-actions[bot]`. The gate
  only ever acts on the *reviewer's* verdict, never on the request comment, so
  the request itself cannot trip the gate.

### Component 2 — `gate.yml` (deterministic merge gate)

- **Trigger:** `pull_request_review` types `[submitted]` **and**
  `issue_comment` types `[created]` (the `@claude` action may emit its verdict as
  a review or as a comment — to be confirmed at planning time; the gate handles
  both).
- **Guard:** only proceed when the actor is the trusted reviewer
  `github-actions[bot]`. (If a Claude GitHub App is ever installed, also match
  `claude[bot]`.)
- **Pure shell + `gh`. No Claude invocation in this workflow.**
- **Verdict parse:** uppercase the body; `AUTOMERGE: NO` → NO; `AUTOMERGE: YES`
  present (and not NO) → YES; anything else (missing/empty) → **fails closed**
  (treated as not-approved).
- **On YES:**
  1. Wait for the `tests` check to reach a conclusion (poll `gh pr checks`).
  2. Determine the changed-file set (`gh pr view --json files`) and apply the
     **path allowlist**: every changed file must be under `engine/`, `tests/`,
     or `scripts/`.
  3. Merge **only if** CI conclusion is `success` **AND** the PR carries no
     `security` label **AND** the path allowlist holds.
  4. `gh pr merge --squash --delete-branch`.
  5. Any failure of these conditions → leave the PR open (fail-safe). For an
     approved PR that fails *only* the path check (touches markdown), post
     "approved — ready for you to merge" so the user knows it's their click.
- **On NO:** hand off to the fixer (Component 3), subject to the round cap **and**
  the Python-only rule — if the requested changes are to markdown, the fixer is
  not dispatched; the PR is left for the user with the review feedback intact.

### Component 3 — the fixer (a step within `gate.yml`)

- Invoked only on `AUTOMERGE: NO`, only when under the round cap, **and only when
  the requested changes are to Python** (`engine/`, `tests/`, `scripts/`).
- Runs `claude-code-action` (subscription auth) prompted to: read the review
  feedback on this PR, make the changes **to Python files only**, run the tests,
  commit, and push to the PR branch.
- **Tool authority:** edit/write/commit/push to the PR branch, **restricted to
  the Python paths**. **No markdown edits, no merge, no branch deletion, no
  force-push to other branches.** The push re-triggers `review-request.yml` via
  `synchronize`.
- **Markdown feedback is never auto-applied.** This is the structural guarantee
  that Claude cannot author-and-merge its own methodology prose (Vector B). If a
  review's feedback concerns markdown, the gate leaves the PR for the user.
- **Round cap = 3.** Tracked with a label `auto-fix-round-N` (or an equivalent
  counter read off the PR). On the 4th NO, the gate does **not** dispatch the
  fixer; it posts `max auto-fix rounds reached — over to you` and stops.

## Safety Invariants (non-negotiable — from the source's hard-won lessons)

1. **Merge is deterministic-only.** The reviewer and fixer agents never merge.
   Only `gate.yml` shell logic merges.
2. **Machine-readable verdict, fails closed.** Key off `AUTOMERGE: YES/NO`;
   missing/empty/NO never merges.
3. **Reviewer author matched** as `github-actions[bot]` (OAuth, no App). A verdict
   from any other author is ignored.
4. **Bounded loop.** Max 3 fix rounds, then human handoff. No infinite ping-pong.
5. **CI green is mandatory** even when the verdict is YES — the fixer's own
   commits must keep all 121 tests passing.
6. **`security` label is a hard block** — never auto-merges.
7. **Path allowlist for auto-merge.** Only PRs whose changed files are all under
   `engine/`, `tests/`, `scripts/` can auto-merge. Any markdown touched → human
   merge, even when approved.
8. **Fixer never edits markdown.** Structural guarantee against Vector B — Claude
   cannot author-and-merge its own methodology prose.
9. **Fail-safe direction always.** Every ambiguity or failure leaves the PR open
   for a human. Inert is acceptable; wrong-merge is not.
10. **Exit-code-0 is not trusted** for the fixer — success is detected by a real
    new commit on the branch, never by the agent's exit code.

## Rollout (the single most important step)

The source's hardest-won lesson: *the gate passed all unit tests and two static
reviews while being completely inert; the bugs only surfaced against a real PR.*

Therefore:

1. **Phase 1 — report-only.** `gate.yml` ships with the merge step replaced by a
   log line (`would merge PR #N: CI=<x>, verdict=<y>, security=<z>`). The fixer
   loop is **live** (it's lower-risk and we want to exercise it), but no
   auto-merge happens.
2. **Smoke-test against a real PR.** Open a throwaway PR, watch the full loop:
   review → (induce a NO) → fix → re-review → YES → confirm the gate logs the
   correct "would merge" decision and the conditions evaluated correctly.
3. **Phase 2 — enable merge.** Flip the report-only flag once the real-PR run is
   verified. Keep the round cap and `security` block.

## Planning-Time Must-Resolve (do not guess)

- Exact `claude-code-action` invocation for the **fixer** role (commit-and-push
  mode with restricted tools) — confirm from official docs / claude-code-guide.
- Exactly how the `@claude` action emits its verdict (PR review body vs. issue
  comment) so the gate's parser and trigger match reality.
- How to reliably "wait for the `tests` check" from the review-triggered gate
  (poll vs. re-trigger on `check_suite`/`workflow_run` completed).
- Whether GitHub's default `GITHUB_TOKEN`-triggered events can re-trigger other
  workflows (the `synchronize` from the fixer's push must trigger
  `review-request.yml`; a push made with the default token may not trigger
  downstream `pull_request` workflows — may require a PAT or the OAuth-action's
  push to carry the right token).

## Risks

### The two vectors (the markdown discussion)

- **Vector A — the user's own markdown PR is approved and merged.** *Mitigated by
  the human-merge class:* markdown PRs never auto-merge; the user clicks merge.
  Residual risk is normal "review might miss something" on the user's own work.
- **Vector B — Claude authors a markdown change and merges its own prose** (review
  → fixer edits skill → Claude approves its own edit → merged, unread, untested,
  shipped to the published plugin). *Structurally eliminated:* the fixer is
  forbidden from editing markdown, and the path allowlist blocks markdown from
  auto-merge. Claude cannot both author and merge methodology content.

The published-plugin amplifier (a silent methodology regression ships to all
installers and surfaces only during a real engagement) is the reason markdown
keeps a human in the loop despite the cost to hands-off velocity.

### Remaining risks

- **Fixer modifies the user's own PR (Python).** The fixer pushes commits onto
  the user's branch and those can auto-merge. Intended (PR = handoff signal);
  squash-merge keeps history tidy.
- **Token/trigger chaining** (see must-resolve) — if the fixer's push doesn't
  re-trigger review, the loop stalls (fail-safe: PR stays open, no harm).
- **Cost.** Each round is a review + a fix invocation on the subscription
  (≈zero marginal cost via OAuth, never per-token API) — ensure `ANTHROPIC_API_KEY`
  is unset in the workflow env.
- **Path-classification correctness.** The allowlist must be exact — a
  mis-classified markdown file slipping into "Python" would defeat the guard.
  Belongs in the real-PR smoke test.

## Out of Scope / Future

- Auto-merge for markdown (would require a methodology-regression test harness
  first — not currently feasible).
- Run summary / Telegram notification on merge (the repo has a telegram skill;
  could be added later).
- Re-introducing a finder for autonomous backlog improvement.
