# Per-Phase Review Documents — Design

**Issue:** #99 · **Date:** 2026-06-28 · **Status:** approved (brainstorming)

## Problem

An engagement generates client-worthy content at many phases, but the client sees a document
only at the existing checkpoints (scope, baseline, portfolio, process-validation) and the final
Phase 11 deliverable. Several phases produce content the client never sees until the end:

- **Phase 3 — tech & data inventory** (`tech-inventory.md`): systems, data assets + **data
  sensitivity**, shadow IT. Notably, the data-sensitivity classification **drives the GRC gate**
  (Phase 5/6) — so a wrong classification mis-fires governance. IT confirming this early is
  high-value.
- **Phase 5 — opportunity landscape** (`opportunities/_index.md`): the catalog of identified
  opportunities, only re-surfaced (scored) at the Phase 7 portfolio.
- **Phase 8 — use-case briefs** (`usecase-briefs/`): the most client-tangible detail.
- **Phase 9 — business case** (`business-case.md`): the funding argument, only seen rolled into
  Phase 11.

#131 built the mechanism to render any checkpoint as a deterministic Word doc from a declarative
registry. This issue uses it to add per-phase **review documents**, and adds the Conductor
behavior to **offer** them at each phase boundary.

## Goal

Add four per-phase review documents (P3, P5, P8, P9) as deterministic Word docs on the #131
registry, each with a sign-off block, and have the Conductor **offer** each at its phase
boundary (opt-in, not forced).

## Model (decided in brainstorming)

- **User-facing review document** per phase — the client reads it to confirm the phase's content
  was captured right.
- **Offered, not forced.** At the phase boundary the Conductor asks "want a review doc for this
  step?" — a should-confirm decision point. Opt-in.
- **Sign-off block included on all** — uniform and cheap; used when it matters, harmless when not.
- **Not hard gates.** These are recommended-and-recorded (like scope/baseline/portfolio).
  process-validation keeps its hard gate (#136); these four do not block.

## Non-goals

- Not changing the existing 4 checkpoints' behavior (scope/baseline/portfolio recommended;
  process-validation hard-gated).
- Phase 11 `deliverable.html` untouched; `generate-artifact` on-demand path untouched.
- No new analytical content — every value copied verbatim from the phase's source file(s).
- Not adding docs for phases without client-worthy standalone output (P6 scoring, P8.5 cost
  actuals interview, P10 exec summary = the deliverable).

## Architecture

Reuses #131 wholesale: `state/checkpoint_doc.py` (helpers + builders + `Checkpoint` registry +
`render_checkpoint` driver) and `state/docx.py`. **No new module.** Four new registry entries +
a small `build` fn each, plus Conductor + building-checkpoint wiring.

### New registry entries (all `per_process=False`, `gate=False`, sign-off included)

| id | Insert after | Audience | Sources | Output |
|---|---|---|---|---|
| `tech-data` | Phase 3 | IT lead + sponsor | `tech-inventory.md` | `checkpoints/checkpoint-tech-data.docx` |
| `opportunities` | Phase 5 | Sponsor + decision-maker | `opportunities/_index.md` | `checkpoints/checkpoint-opportunities.docx` |
| `use-case-briefs` | Phase 8 | Sponsor + process owners | `usecase-briefs/_index.md`, `usecase-briefs/UC-NNN.md` | `checkpoints/checkpoint-use-case-briefs.docx` |
| `business-case` | Phase 9 | Decision-maker + sponsor | `business-case.md` | `checkpoints/checkpoint-business-case.docx` |

Outcome record for each: `checkpoints/CP-<id>-outcome.md` (Outcome: Pending), like the others.

### Per-entry content (verbatim from source, via existing builders)

- **tech-data** — `prose_section` over the key `## N.` sections of `tech-inventory.md`: System
  inventory, Data asset catalog (incl. sensitivity), Shadow IT, IT governance posture. Confirm
  note ("confirm your systems and data sensitivity are captured correctly") + sign-off. Excludes
  the internal "Phase-3 input-contract notes" section.
- **opportunities** — `table_from_index` over `opportunities/_index.md` (OPP-ID, Process, Type,
  Feasibility, Data Readiness, GRC, Structural) + confirm note + sign-off.
- **use-case-briefs** — index table from `usecase-briefs/_index.md`, then a `prose_section` per
  `UC-NNN.md` (title + summary fields) + sign-off. (One doc covering all briefs.)
- **business-case** — `prose_section` over `business-case.md` key headings (The decision, Wave
  scope, per-initiative cost, per-initiative value) + confirm note + sign-off.

### Conductor — offer at phase boundary (the new behavior)

`conducting-engagement` already offers checkpoints at insertion points (should-confirm). Extend
that insertion list so the Conductor, at the end of Phases 3, 5, 8, and 9, **offers** the
corresponding review doc in plain language ("Want a short doc on [what we captured] you can share
or confirm?"). On yes → `building-checkpoint <id>`. Opt-in; declining is fine; nothing blocks.

Narrate jargon-free (no phase numbers, file names, or ids), consistent with existing narration.

### building-checkpoint

Add the four ids to Session Start wired-values + predecessor checks (tech-data→`tech-inventory.md`;
opportunities→`opportunities/_index.md`; use-case-briefs→`usecase-briefs/_index.md`;
business-case→`business-case.md`). Routing already general (#131): `python3 -m state.checkpoint_doc <name> <id>`.

## Data flow

```
Phase N completes → Conductor offers the review doc (should-confirm) →
  on yes: building-checkpoint <id> → python3 -m state.checkpoint_doc <folder> <id>
    → registry[id].build(root) → blocks → docx → checkpoint-<id>.docx + CP-<id>-outcome.md (Pending)
  → client reads/optionally signs off (recorded); no gate, no route-back required
```

## Testing

- Each new entry renders a valid `.docx` (valid zip + parses) with expected content from a fixture
  source + a sign-off block; tech-data **excludes** the input-contract notes section.
- Registry has the 4 new ids with `gate=False`.
- `building-checkpoint` Session Start lists the 4 new ids + predecessor checks (guard).
- `conducting-engagement` offers the 4 docs at their phase boundaries (guard: the insertion list
  references each id at its phase); the offer is should-confirm, not a hard gate.
- Existing 4 checkpoints + process-validation gate unchanged (regression).

## Ponytail notes

- No new module/abstraction — four small `build` fns + registry entries on the #131 layer; reuse
  the existing builders (no new parsing primitives expected). 
- Sign-off block reused uniformly (`signoff_block`).
- Tests: valid-zip + content, not byte-golden.

## Open questions

None blocking. Confirmed: all four (P3/P5/P8/P9); offered (opt-in) not forced; sign-off included
on all; not hard gates.
