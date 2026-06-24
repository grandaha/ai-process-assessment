# Slice 2 · Chunk B — Edit & interruption splicing (design)

**Date:** 2026-06-24
**Status:** Design (approved in brainstorming; pending written-spec review)
**Umbrella:** `2026-06-19-public-ai-first-distribution-design.md` §3.D · issue **#87** · epic **#85**.

> Chunk B of three. A = parallel per-process fan-out (merged, #102). C = granular autonomy +
> register-teaching + holding-the-line. Each ships its own spec → plan → PR, accumulating under
> CHANGELOG `[Unreleased]`; one `v2.19.0` release closes #87.

---

## 1. What the user experiences (AI-first)

At any point in an engagement the user can interrupt in plain language to correct something —
*"no, our loaded rate is $200, not $185"*, *"that's augmentation, not automation"*, *"actually
billing is out of scope"*. The AI understands the correction, fixes the **right** thing, re-runs
the audited pipeline, and tells them in plain language **what changed**: *"That drops the business
case from $1.4M to $1.1M and pushes the status-assembly opportunity into next year."* The user
never hears "model input", "Phase 6", or "OPP-003". This is where the old spreadsheet "what-if"
now lives — **stricter**, because it re-runs the audited engine instead of a fragile live formula.

## 2. What already exists (the back half)

The **staleness re-drive machinery is built and shipped** (Slice 1):

- `state/staleness.py` `changed_inputs()` — content-hash detection of which `model/*.json` inputs
  changed (iCloud-safe; not mtime).
- The conductor drive loop + **Staleness** section: when an input changes, re-run the engine,
  re-drive every downstream portfolio phase, record affected ratifications as
  `invalidated-by-staleness`, re-surface them per their touchpoint class, then re-record hashes
  via `record_input_hashes()`.
- The **decision log** already records both parties (`proposed_by` / `decided_by` / `disposition`,
  append-only, never overwrites a prior entry).
- **Chunk A** (merged): conductor-owned per-process Phase 5 fan-out with single-process mode and a
  deterministic process-order merge.

So "apply correction → recompute → cascade → re-surface decisions" already works. Chunk B adds the
**front half** (intake + classification + routing) and the **delta report**.

## 3. Scope

**In:**
- A universal plain-language **interruption intake**: the conductor recognizes a correction at any
  point and handles it before resuming.
- A **classifier** that routes the correction to one of three *already-built* owning-artifact
  mechanisms (§4).
- A **confidence / confirm gate** (§5): act-then-show by default; confirm-first only when the
  mapping is ambiguous or the correction re-opens a human-only must-ask.
- A deterministic **delta report** helper (§6) the conductor narrates from.
- Both-parties **decision-log** entries for user-initiated corrections (§7).

**Out (deferred follow-up):** a *sandboxed* what-if **preview** — "show me the impact of $200
without committing." That needs a throwaway copy of `model/` + an isolated engine run + discard
(real blast radius). §3.D's framing ("re-runs the audited pipeline — stricter") makes the committed
edit **with a delta report** the what-if; transient preview is a later chunk if demanded.

**Out:** any engine/math change; the staleness, hashing, convergence, and Chunk-A fan-out
machinery already exist and are reused unchanged.

## 4. The classifier — three routes, all mechanisms already built

The **interface** accepts any correction in plain language (AC-1: the user never learns the
model-input/prose distinction). The **rigor** is in routing: the AI never free-edits arbitrary
files — it writes only through an *owning artifact* with an audited re-drive path, preserving AC-3
(every number traces `results.json` → tested formula → sourced `model/*.json`).

| Correction (plain language) | Owning artifact | Re-drive mechanism (status) |
|---|---|---|
| numeric assumption — "rate $200", "500/month", value range | the owning `model/*.json` field, addressed via `docs/data-contract.md` (e.g. `model/costs.json#OPP-001…`, `model/baselines.json#PROC-003.volume`) | edit the value → engine re-run → staleness cascade ✅ exists |
| structural — "augmentation not automation", "do invoicing first" | the owning **phase** output (opportunity type in `opportunities/`, sequencing in `roadmap.md`) | re-run the owning phase → staleness cascade ✅ exists (same route-back the conductor uses for checkpoint/gate rejections) |
| human-only — "out of scope", "buy not build" | the must-ask **touchpoint** | re-open that decision ✅ exists (touchpoint taxonomy) |

**Routing reference.** `docs/data-contract.md` documents each `model/*.json` field and its source
path convention (`model/value.json#OPP-001.improvement_low`), which is exactly how the classifier
maps a phrase ("rate", "volume", "improvement") to the owning field.

**Structural route reuses Chunk A.** Re-typing one opportunity re-drives **only that process's**
Phase 5 via Chunk A's single-process mode, then re-merges via `renumber_sequential`; the staleness
cascade carries the change into scoring/roadmap/business-case. (Interaction caveat in §8.)

## 5. Confidence / confirm gate (act-then-show default)

Corrections are cheap and reversible (a value edit plus an append-only log entry), and **the delta
report is the confirmation after the fact.** So the default is **apply, then show what changed.**

Confirm *first* only when:
- **the mapping is ambiguous** — "not sure if you mean the cost rate or the value-improvement rate;
  which?" (an interpretation question, not a permission question); or
- **the correction re-opens a human-only must-ask** — scope boundaries, Build/Buy/Partner, cost
  actuals (these are *always* must-ask, every mode, per the touchpoint taxonomy).

**Reconciliation with the autonomy preset (no conflict, no pre-emption).** Act-then-show governs
*applying the correction the user explicitly stated* — re-confirming what they just told you is
redundant. The **downstream re-opened ratifications** produced by the staleness cascade still
follow the **existing touchpoint taxonomy and autonomy preset** unchanged: guided mode pauses on
should-confirm items; autonomous mode batches them. Chunk B does **not** alter that behavior, and
**autonomous batching remains Chunk C's scope** (the taxonomy marks it "Slice 2" = C). Chunk B only
adds the edit front-door and the delta report.

## 6. The delta report — the only new code

Truth is computed deterministically; the conductor writes the human story from it (the same
split the whole system uses: engine/helpers own numbers, the conductor owns the voice).

```
state/results_diff.py
  diff_results(before: dict, after: dict) -> list[Change]   # Change: path, before, after
```

- The conductor snapshots `results.json` (reads it into memory or copies it aside) **before**
  applying the edit, then calls `diff_results(before, after)` **after** the re-drive.
- Generic and recursive: walks two `results.json` structures and returns every changed leaf
  (value totals, score composites, business-case total, roadmap order) with before/after. No
  hardcoded key knowledge.
- **Stdlib only**, **no arithmetic** (comparison and equality only — all numbers were produced by
  the engine), deterministic (stable ordering of returned changes).
- **Reusable:** the existing staleness re-drive can narrate its delta with the same helper (today
  it re-opens decisions but reports no numeric delta).
- The conductor reads the structured changes and narrates the salient ones in **jargon-free** plain
  language (no `OPP-NNN`, no `model/*.json`, no "Phase N").

Because this chunk carries a wired Python helper (with tests), it is expected to be
**auto-merge-eligible**, unlike Chunk A's markdown-only HOLD.

## 7. Decision log — both parties, exact enum

Every user-initiated correction is logged append-only, never overwriting the original — preserving
the override corpus the Slice-3 flywheel will mine. Using the existing enum verbatim
(`decided_by: agent-auto | human-ratified | human-overrode`;
`disposition: accepted | edited | overridden→<X> | invalidated-by-{…}`):

- **Correction of an AI draft** (the AI proposed X, the human says Y):
  `proposed_by: agent`, `decided_by: human-overrode`, `disposition: overridden→Y`.
- **Fresh user-supplied fact** (no prior AI claim, or correcting a placeholder):
  `proposed_by: human`, `decided_by: human-ratified`, `disposition: edited`.

Terminology note: "override" here is the **decision-log** sense (human-overrides-agent). It is
distinct from the **CLAUDE.md methodology overrides** handled by `state/overrides.py` (authorized
phase skips). Chunk B does **not** touch that machinery and reserves the word accordingly.

## 8. Mid-flight splicing & the Chunk-A interaction

- **Splicing.** An interruption is handled at the drive-loop boundary: apply the edit → re-drive
  affected downstream → the existing loop re-plans the next step. No half-finished destructive work;
  the correction changes inputs and the staleness machinery takes over.
- **Chunk-A renumber caveat.** A structural correction that re-drives one process's Phase 5
  inherits Chunk A's global-`OPP-NNN` renumber behavior **only if the opportunity count changes**
  (add/remove). A pure re-type (same count) is id-stable. A count change legitimately invalidates
  downstream decisions and prior `OPP-NNN` evidence pointers — which the existing
  `invalidated-by-staleness` re-surfacing already handles. Document, don't special-case.

## 9. Testable acceptance (guards)

1. **Intake & three routes:** the conductor's edit section names the universal plain-language
   intake and all three routes (model-input edit / owning-phase re-run / reopen human-only
   must-ask).
2. **Confirm gate:** prose states the act-then-show default and the two confirm-first exceptions
   (ambiguous mapping; human-only must-ask), and explicitly defers downstream re-surfacing to the
   existing touchpoint taxonomy + autonomy preset (no batching here).
3. **Delta determinism:** `diff_results` returns the same changes in the same order regardless of
   dict insertion order; identical inputs → empty diff; nested numeric changes are detected.
4. **Both-parties logging:** prose specifies both decision-log mappings using the exact enum
   values, and that entries are append-only (never overwrite the AI proposal).
5. **Jargon-free delta narration:** the user-facing delta narration block carries no `OPP-`,
   `model/`, `_staging`, `renumber`, or `Phase N` tokens (reuse the §3.B jargon-guard pattern).

## 10. Files touched

- `skills/conducting-engagement/SKILL.md` — new `## Edit & interruption splicing` section
  (intake, classifier/routes, confirm gate, both-parties logging, delta narration block).
- `state/results_diff.py` (new) + `state/tests/test_results_diff.py` — the delta helper
  (guards 3).
- `tests/` — conductor-prose guards (1, 2, 4, 5).
- `CHANGELOG.md` under `[Unreleased]`; **no version bump** (accumulates toward `v2.19.0`).

**Not touched:** `skills/using-methodology/SKILL.md` / `system-prompt.md` (verbatim-sync, off-limits);
golden `results.json` (no arithmetic); `state/staleness.py`, `state/overrides.py`,
`state/assembly.py`, the engine (all reused as-is).
