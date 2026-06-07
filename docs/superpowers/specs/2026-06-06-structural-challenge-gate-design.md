# Design — Structural-Challenge Clause for the Phase 4 Gate

**Date:** 2026-06-06
**Status:** Approved design (pre-implementation)
**Author:** Dave Raffaele (with Claude)
**Issue:** #10 — Methodology gap: first-order vs. second-order redesign

---

## 1. Problem

The methodology is an **automation discovery exercise**: it maps existing processes, finds steps where AI or RPA reduces friction, and scores those interventions. Every current phase operates at the **first order** — make the current steps faster, cheaper, or more accurate. The opportunity taxonomy (Chain Automation, RPA, AI Augmentation, …) is also first-order: it presupposes the process shape and asks what automation fits within it.

This produces a category error: **automate a broken process and you get a faster broken process.** The methodology has no point at which it challenges whether the process structure itself is the constraint, so it systematically undervalues the highest-impact interventions — those that redesign the process rather than augment it. Sophisticated clients (the target profile) will notice the roadmap is an optimization of their current operating model; those who notice during the engagement lose confidence, those who notice after are right to question the value delivered.

## 2. Goal

Surface — not solve — the second-order question on every mapped process, and carry the resulting signal through to the deliverable so the client makes an **informed choice**. Achieve this **without a new phase, agent, artifact, or interview round**: capture extends the existing Phase 4 gate; the signal extends the existing Phase 5 typer and rides the existing index/renderer propagation.

## 3. Settled decisions

| Decision | Choice | Rationale |
|---|---|---|
| Placement | **Extend the Phase 4 gate** — no new phase/agent/artifact/round | Per issue #10. The mechanism lives entirely inside Phase 4 (capture) and Phase 5 (signal). |
| Gate rename | **"Baseline & Value Hypothesis Gate" → "Baseline, Value & Challenge Gate"** | The challenge hypothesis becomes a third blocking clause, identical in mechanics to a missing baseline. |
| Authorship | **R1 `process-mapper` captures raw sponsor answers; orchestrator synthesizes the per-process challenge hypothesis at assembly** | Mirrors how baselines work — subagent captures raw material with sources, orchestrator owns the gate, the chain scan, and stable-ID reconciliation. The challenge hypothesis is a cross-process main-context judgment. |
| Questions asked of | **Sponsor (Round 1 only)** | The operator defends the current structure; the sponsor owns the boundary/actor/sequence questions. No new round — folds into the existing Round 1. |
| Phase 5 signal | **`Structural response` field + `struct=` extraction token + `Structural` column in `opportunities/_index.md`** | Threads exactly like the existing Feasibility / Data / GRC flags. |
| Score impact | **None — annotation only** | The issue states the flag "annotates, it does not block." The scorer references the label in rationale but never changes the composite. |
| Propagation scope | **Scope A — faithful-full**: Phase 5 → scores rationale + portfolio view → roadmap | Meets every acceptance criterion. The heavy joins already exist (portfolio renderer already joins `opportunities/_index.md`), so the marginal cost is two light touches. |

## 4. Core principle (the enforceable rule)

> **A process cannot exit Phase 4 without a challenge hypothesis**, exactly as it cannot exit without a baseline. The challenge hypothesis either clears the process as structurally sound, or states a one-paragraph redesign question (boundary / actor model / sequence). The methodology surfaces the question; the client decides whether to pursue it. The Phase 5 signal that flows from it **annotates and never blocks** — an `optimizing-around` opportunity is still created, typed, scored, and sequenced normally.

## 5. The three challenge questions

Asked of the **sponsor** in Round 1, once per process the engagement will map:

1. **Is the process boundary right?** Does the process exist because of a legacy constraint (system limitation, org structure, manual handoff) that AI could eliminate entirely — making the process *unnecessary* rather than faster?
2. **Is the actor model right?** Does the current allocation of steps to roles reflect what those roles should own, or what they were forced to own by capability limits that no longer apply?
3. **Is the sequence right?** Does the order of steps reflect a logical dependency, or a historical artifact of how information used to flow?

Output per process: a one-paragraph **challenge hypothesis** that either clears the process or flags exactly one redesign question. The consultant surfaces; does not solve.

## 6. Data flow

```
Round 1 (Sponsor)
   └─ process-mapper R1  ──► captures "Sponsor structural input" (raw answers, R1-Pk tags)
                                    │
Assembly (orchestrator, main context)
   ├─ reconcile R<N>-Pk tags → stable Process IDs
   ├─ run chain scan
   ├─ apply Baseline, Value & Challenge Gate
   └─ synthesize per-process **challenge hypothesis** ──► process-map.md (new field)
                                    │
Phase 5 (opportunity-typer, per process)
   └─ reads challenge hypothesis ──► sets **Structural response** per OPP
        addressing-root | optimizing-around | not-applicable
        + struct= extraction token
                                    │
   assembly ──► opportunities/_index.md gains **Structural** column
                                    │
        ┌───────────────────────────┴───────────────────────────┐
   Phase 6 (scorer)                                       Phase 7 (roadmap)
   references label in Strategic-Alignment                reads struct from
   rationale; composite UNCHANGED                         opportunities/_index.md;
                                                          annotates optimizing-around
   Phase 11 portfolio renderer                            items in roadmap.md
   surfaces struct badge via its EXISTING                       │
   opportunities/_index.md join                          Phase 11 roadmap renderer
                                                          surfaces annotation on
                                                          affected Wave-1 cards
```

## 7. Field & token definitions

### `process-map.md` — new field
| Field | Content |
|---|---|
| Challenge hypothesis | One paragraph. Either "structurally sound — [why]" or the single surfaced redesign question (boundary / actor / sequence) with its basis. Authored by the orchestrator at assembly from the sponsor's Round-1 answers. |

### `process-mapper` (Round 1) — new captured field
| Field | Content |
|---|---|
| Sponsor structural input | Raw sponsor answers to the three challenge questions, attached to the provisional `R1-Pk` tag. Captured only in Round 1; R2–R4 unaffected. The agent does NOT synthesize the final challenge hypothesis (that is the orchestrator's assembly judgment, like the baseline gate). |

### `opportunity-typer` — new per-opportunity field (#7) + token
- **`Structural response`** — one of `addressing-root` / `optimizing-around` / `not-applicable`, with a one-line rationale citing the process's challenge hypothesis. `not-applicable` = the process was cleared structurally sound (no structural question at stake). Set after the six existing fields; annotates, never blocks.
- **Extraction token** — append `struct=addressing-root|optimizing-around|not-applicable` to the `<!-- index: -->` line. Hyphenated, no spaces, no `&` — same rule as the other tokens.

### `opportunities/_index.md` — new column
`| OPP-ID | Process | Type | Feasibility | Data Readiness | GRC | Structural |` — the index-generation bash loop reads the `struct=` token. The `awk` split that creates per-OPP files is unchanged.

## 8. Per-file changes

| # | File | Change |
|---|---|---|
| 1 | `skills/discovering-processes/SKILL.md` | Add 3 challenge questions to Round 1 description; rename gate → **Baseline, Value & Challenge Gate** + new blocking clause + "challenge hypothesis unavailable" remediation path (mirrors "baseline unavailable"); add `Challenge hypothesis` row to `process-map.md` Key Outputs; add orchestrator assembly step (synthesize per-process challenge hypothesis); add checklist item; add rationalization row; update frontmatter description. |
| 2 | `agents/process-mapper.md` | Round-1 behavior + output schema gain **`Sponsor structural input`** capture (R1 only); refusal rule: do not synthesize the final challenge hypothesis (orchestrator judgment); note R2–R4 unaffected. |
| 3 | `agents/opportunity-typer.md` | Add `challenge hypothesis` to Inputs (part of the process entry); add field #7 **`Structural response`** to per-opportunity assembly + output template; add `struct=` to extraction-header rules; refusal/annotation note (never blocks). |
| 4 | `skills/identifying-opportunities/SKILL.md` | Add `Structural response` to the OPP-NNN entry structure; index-generation bash loop reads `struct=` and emits the **Structural** column; checklist item. |
| 5 | `agents/opportunity-scorer.md` | Strategic Alignment dimension: when the OPP is `optimizing-around`, reference it in the rationale; **composite unchanged**. No new index token/column. |
| 6 | `agents/section-renderer-portfolio.md` | Render a struct badge in the portfolio table, sourced from `opportunities/_index.md` via the **existing** join (new column read + badge note). |
| 7 | `skills/prioritizing-roadmap/SKILL.md` | Read `struct` from `opportunities/_index.md`; annotate `optimizing-around` items in `roadmap.md` Wave tables / Wave-1 cards. |
| 8 | `agents/section-renderer-roadmap.md` | Surface the structural annotation on affected Wave-1 cards when present in `roadmap.md` (does not add pills not present in source). |
| 9 | `skills/using-methodology/SKILL.md` | Add structural-challenge row to the Master Rationalization Table; update gate-name reference; note `challenge hypothesis` in the Phase 4 output description. |

No engagement-folder-convention change (no new file/folder). No `awk` split change. No GRC-gate change.

## 9. Testing & validation

The static test stack (`tests/`, 33 tests on `main`) is the validation surface — this change ships no runtime code.

- The methodology-model parser / guards must **accept the new `struct=` extraction token** and the new `Structural` column in `opportunities/_index.md` (confirm the exact guard files when writing the plan; candidates are the extraction-token and index-shape guards).
- **New guard:** every `opportunities/_index.md` row carries a valid `struct` value (`addressing-root` | `optimizing-around` | `not-applicable`).
- Re-run the full suite; it must stay green. Bump the plugin version on merge (per repo convention).

## 10. Forward-compat with issue #6

Issue #6 will split `process-map.md` / `baselines.md` into `processes/PROC-NNN.md`. The `Challenge hypothesis` field travels with the process entry into `PROC-NNN.md` — #6's per-file schema must carry it. This is a one-line note for #6; it does not block or depend on this work. (If #6 lands first, place the field in `PROC-NNN.md` instead of `process-map.md`; everything downstream is identical.)

## 11. Out of scope

- Solving any redesign (the methodology surfaces the question; the client decides).
- Any change to the composite score or scoring math (annotation only).
- A new phase, agent, artifact, interview round, or engagement-folder entry.
- Issue #6 normalization (independent; see §10).
- GRC-gate behavior.

## 12. Acceptance criteria

- The Phase 4 Round-1 sponsor description includes the three challenge questions; no new interview round is added.
- Every process entry in `process-map.md` carries a `Challenge hypothesis` field, authored by the orchestrator at assembly.
- The Phase 4 gate (now **Baseline, Value & Challenge Gate**) blocks Phase 4 exit on a missing challenge hypothesis, identically to a missing baseline, with a "challenge hypothesis unavailable" remediation path.
- The Phase 5 typer reads the challenge hypothesis and sets `Structural response` (`addressing-root` / `optimizing-around` / `not-applicable`) per opportunity; the `struct=` token and `Structural` column propagate it.
- The label reaches the deliverable: the **portfolio view** via the renderer's existing `opportunities/_index.md` join, and the **roadmap view** via `roadmap.md` annotation.
- The signal never blocks opportunity creation and never changes a composite score — it only annotates.
- The full static test suite passes, including a new guard on the `struct` column.
