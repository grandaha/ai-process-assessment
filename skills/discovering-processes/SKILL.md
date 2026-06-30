---
name: ai-process-assessment:discovering-processes
description: Phase 4 — evidence-gathering core. Maps processes via four-round interview sequence (sponsor → operator → adjacent → clarification), captures volume/cycle time/error rate/FTE for every process. Enforces the Baseline, Value & Challenge gate. Saves processes/_index.md and processes/PROC-NNN.md per process.
---

# Phase 4: Discovering Processes

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical path for all outputs in this phase. Do not ask the user for the path. Halt if scope.md is absent or the field is missing (return to Phase 1). All file paths below that include `<name>` use this value.
2. Read `tech-inventory.md`, `context.md` — confirm each exists.
3. **Check for a sample-run marker.** After extracting the engagement folder, check whether `<engagement-folder>/.sample-run.md` exists. If present, this is a sample run — read that file silently, extract the `intake_root` field from its YAML frontmatter, and note the Phase Intake Map. At all four interview rounds in the Workflow below, read `<intake_root>/interview-notes.md` instead of conducting live stakeholder interviews.

Gate condition: `tech-inventory.md` must be present before proceeding.

## Role in the system

This is the evidence-gathering core of the methodology. Everything downstream — opportunity identification, scoring, sequencing, brief writing — cites this phase's output. The output is the `processes/` folder: one `processes/PROC-NNN.md` per process (combining process map and baseline metrics in one file) and a machine-readable `processes/_index.md`.

## Gate condition

`tech-inventory.md` must exist. The engagement's `evidence-log.md` should be active and used to record interview rounds. This skill creates the `processes/` folder: `processes/_index.md` and one `processes/PROC-NNN.md` per process.

## Baseline, Value & Challenge Gate

This is the single most load-bearing rule in the methodology.

For every process mapped, `processes/PROC-NNN.md` MUST contain at minimum in its Baselines section:

- **Volume** — transactions per unit time (e.g., "1,200 invoices/month")
- **Cycle time** — median and P90 (e.g., "median 4h, P90 18h")
- **Error / exception rate** — what fraction of transactions deviate from happy path
- **FTE effort estimate** — current human effort consumed (e.g., "2.4 FTE-equivalent")

**No value claim may be made in any subsequent phase without citing a baseline from this file.**

If a baseline cannot be sourced (estimated by an operator, pulled from a system, sampled), the process does not advance to Phase 5. It is logged as "baseline unavailable" with a remediation action.

**Challenge clause (second-order check).** For every process mapped, `processes/PROC-NNN.md` MUST also carry a **challenge hypothesis** (see Key Outputs). Automate a broken process and you get a faster broken process — this clause forces the question of whether the process structure itself is the constraint before any automation is typed. A process with no challenge hypothesis does not advance to Phase 5: it is logged as "challenge hypothesis unavailable" with a remediation action (return to the sponsor for the three structural questions), identically to a missing baseline. The hypothesis *surfaces* the redesign question; it does not solve it, and the signal it produces downstream annotates — it never blocks opportunity creation.

## Recording baselines for the engine

Capture each baseline as raw, sourced inputs in the engagement's `model/baselines.json` — one object per process, keyed by `process_id`: `volume`, `cycle_time_median`, `cycle_time_p90`, `error_rate`, `fte`, and `source`. Use the same `process_id` values that `processes/PROC-NNN.md` assigns, so downstream phases can reference a baseline by id. Do not multiply or annualize any figure in prose — record the raw measured value and its source only. The engine reads `model/baselines.json`, echoes every baseline into `model/results.json` under `baselines.<process_id>`, and resolves the value-hypothesis volume for each opportunity from it (Phase 5). `processes/PROC-NNN.md` is the human-readable, source-cited baseline record; every numeric figure it states must equal its `results.json` source, so the figures are deterministic and auditable. A figure that appears only in `processes/PROC-NNN.md` with no `baselines.json` source is a defect the deliverable-gate must catch.

## Four-Round Interview Sequence

1. **Sponsor — strategic framing + structural challenge.** What does this process exist to achieve? What would success look like to the business? Then ask the three **structural challenge** questions, once per process the engagement will map. Ask the sponsor, not the operator — the operator will defend the current structure:
   - **Is the process boundary right?** Does the process exist because of a legacy constraint (system limitation, org structure, manual handoff) that AI could eliminate entirely — making the process *unnecessary* rather than faster?
   - **Is the actor model right?** Does the current allocation of steps to roles reflect what those roles should own, or what they were forced to own by capability limits that no longer apply?
   - **Is the sequence right?** Does the order of steps reflect a logical dependency, or a historical artifact of how information used to flow?
2. **Operator — actual execution.** Walk through the process as it actually runs. Capture the workarounds, the exceptions, the "we always have to..." moments.
3. **Adjacent — upstream and downstream.** Talk to the people who feed this process and the people who consume its output. Their pain often defines the real opportunity.
4. **Clarification — resolve conflicts.** Where rounds 1–3 disagree, return with specific questions and reconcile. Document the resolved version AND the disagreement.

## Subagent Dispatch

Phase 4 runs as **two sequential passes**. Interview-round synthesis is offloaded to subagents to keep the main context clean. The main context owns the gate decisions; subagents own the per-round write-up and per-process capability tagging.

### Pass 1 — `process-mapper` (steps only)

- **When:** After raw notes for an interview round are captured, dispatch one `process-mapper` subagent per round to synthesize that round into structured `processes/PROC-NNN.md`-ready content. Rounds are independent — dispatch them in a single parallel tool-call batch where notes for more than one round are ready.
- **Pass to each subagent:** engagement folder path, round number, and the raw notes for that round only. The agent reads `tech-inventory.md` itself to extract relevant sections, and applies the `processes/PROC-NNN.md` field schema defined in its own agent spec (which mirrors the Key Outputs below). It derives its own `_staging/phase4/round-N.md` output path from the engagement folder path and round number. Do not pass any file content to the subagent.
- **Return:** Write structured entries to `<engagement-folder>/_staging/phase4/round-N.md`. Return a one-line summary only: "Round N complete: N processes mapped, N baselines captured." The orchestrator assembles `processes/PROC-NNN.md` files from staging files — it does NOT receive entry content from the subagent.
- **What stays in main context:** The Baseline, Value & Challenge gate, the conflict-resolution decision from Round 4, and **synthesizing the per-process challenge hypothesis** from the Round-1 `Sponsor structural input` (one paragraph per process: structurally sound, or the single surfaced redesign question). These are cross-round judgments and must not be delegated. After synthesis, the orchestrator writes one `processes/PROC-NNN.md` per process and **final-numbers the Steps** before Pass 2.

### Pass 2 — `step-capability-tagger` (capability attributes, per process, parallel)

After the orchestrator has assembled and final-numbered the Steps in each `processes/PROC-NNN.md`, dispatch one `step-capability-tagger` subagent per process in a single parallel tool-call batch.

- **Pass to each subagent:** engagement folder path, process ID, path to the assembled `PROC-NNN.md`, and path(s) to the evidence sources (`_staging/phase4/` notes or `evidence-log.md`).
- **Return:** The tagger appends the `**Step capability:**` table to `processes/PROC-NNN.md` (one row per step, every row evidence-cited, only vocabulary attributes). Returns a one-line summary only.
- Chains are computed deterministically by `state/capability.py` from the capability table; chain identification and value assessment are Phase 5 work.

After Pass 2, the orchestrator generates `processes/_index.md` via Bash.

## Phase checklist

- [ ] Confirm `tech-inventory.md` exists
- [ ] Round 1: Sponsor interview(s) — strategic framing; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 2: Operator interview(s) — actual execution; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 3: Adjacent interview(s) — upstream / downstream; record named participants in `evidence-log.md` stakeholder interview log
- [ ] Round 4: Clarification — resolve conflicts; record named participants in `evidence-log.md` stakeholder interview log
- [ ] For every process, capture volume, cycle time (median + P90), error/exception rate, FTE effort
- [ ] Run `step-capability-tagger` (one per process, in parallel) to assign capability attributes — chains are computed deterministically by `state/capability.py` from the capability table; the value of a chain is assessed in Phase 5
- [ ] Apply the Baseline, Value & Challenge gate — flag any process missing baselines
- [ ] For every process, synthesize a challenge hypothesis from the sponsor's structural input; flag any process missing one as "challenge hypothesis unavailable"
- [ ] Save each process to `<name>/processes/PROC-NNN.md` (process map + step capability table + baselines + challenge hypothesis in one file per process)
- [ ] Generate `processes/_index.md` via Bash from extraction headers
- [ ] Confirm all `processes/_index.md` Baseline entries are `Ready` (no `Unavailable` rows advance to Phase 5 unless explicitly scoped out with a documented reason)
- [ ] Confirm `evidence-log.md` stakeholder interview log is complete — one row per session, every participant named
- [ ] Present output summary and key findings to user; wait for explicit approval; then chain to `ai-process-assessment:identifying-opportunities`

## Key outputs

### processes/_index.md

Machine-readable index generated from extraction headers after all `PROC-NNN.md` files are written.

| Column | Content |
|---|---|
| PROC-ID | Stable process identifier (PROC-001, PROC-002, …) |
| Process Name | Descriptive name from the `## PROC-NNN —` heading |
| Baseline | `Ready` if all four baseline fields are present and sourced; `Unavailable` otherwise |

### processes/PROC-NNN.md

One file per process. Contains both process map fields and baseline fields in a single combined file. Each file carries an extraction header on the line immediately after the `## PROC-NNN` heading.

```markdown
## PROC-001 — [Process Name]
<!-- index: baseline=Ready -->

**Trigger:** [what initiates the process]

### Process Map

**Steps:** [actual steps as executed — action only; AI capability is assigned in the Step capability table below]
**Actors:** [roles, systems, external parties]
**Decision points:** [where humans exercise judgment; what informs the call]
**Exceptions:** [common deviations and how they're handled]
**Upstream / downstream:** [what feeds this; what consumes its output]
**Conflicts:** [where interview rounds disagreed; resolution]
**Challenge hypothesis:** [one paragraph: "structurally sound — [why]" OR the single surfaced redesign question (boundary / actor model / sequence) with its basis]

**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | [attributes from fixed vocabulary] | [evidence citation] |

### Baselines

| Field | Value | Source | Confidence |
|---|---|---|---|
| Volume | [transactions per unit time] | [source] | [High/Medium/Low] |
| Cycle time | [median] / [P90] | [source] | [High/Medium/Low] |
| Error / exception rate | [fraction off happy path] | [source] | [High/Medium/Low] |
| FTE effort | [current human effort] | [source] | [High/Medium/Low] |
```

### Step capability table

Appended to each `processes/PROC-NNN.md` by the `step-capability-tagger` (Pass 2). One row per step; every row cites evidence; only vocabulary attributes.

**Fixed vocabulary** (10 attributes — use only these; color is computed by `state/capability.py`):

| Attribute | Meaning | Class |
|---|---|---|
| `structured-data` | works on structured/digital data (fields, records, APIs) | enabler |
| `rule-based` | deterministic logic — if/then, thresholds, lookups | enabler |
| `templated` | templated/parameterized generation (standard emails, forms) | enabler |
| `ai-inference` | extraction / classification / drafting from messy input | enabler (probabilistic) |
| `accuracy-bounded` | a measurable accuracy threshold governs the AI output (valid only with `ai-inference`) | enabler (qualifier) |
| `human-judgment` | discretion/interpretation/tradeoff a human makes each instance | blocker |
| `relationship` | interpersonal — negotiation, trust, client management | blocker |
| `external-dependency` | blocked on a party outside the firm | blocker |
| `physical` | requires a real-world/offline act | blocker |
| `regulatory-signoff` | a regulation/policy mandates a human be accountable | blocker |

**Table format:**

```
**Step capability:**
| Step | Attributes | Evidence |
|---|---|---|
| 1 | structured-data, rule-based | both systems API-available (tech-inventory) |
```

**Computed color rule:** `state/capability.py` maps the attribute list to Green (enablers only, no blockers) / Yellow (mix or probabilistic) / Red (any blocker present). Never write a color in `PROC-NNN.md` — the engine computes it.

**Extraction header rules:** The `<!-- index: -->` line must immediately follow the `## PROC-NNN` heading (line 2 of the file). Set `baseline=Ready` when all four baseline fields carry a real sourced value; set `baseline=Unavailable` when any field is missing or unconfirmed. Spaces in the value are not permitted — use `Ready` or `Unavailable` exactly.

**Assembly — after all synthesis is complete, generate the index:**
```bash
PYTHONPATH="<engine_root>" python3 -c "
import re
from pathlib import Path
from state.assembly import index_from_fields, cleanup

def extract(path):
    text = Path(path).read_text(encoding='utf-8')
    m = re.search(r'^## PROC-\d+ — (.+)\$', text, re.M)
    hm = re.search(r'baseline=([^\s>]*)', text)
    return {
        'id': Path(path).stem,
        'name': m.group(1).strip() if m else '',
        'baseline': hm.group(1) if hm and hm.group(1) else 'Unavailable',
    }

files = sorted(Path('<name>/processes').glob('PROC-*.md'))
index_from_fields(files, '<name>/processes/_index.md',
                  [('PROC-ID', 'id'), ('Process Name', 'name'), ('Baseline', 'baseline')], extract)
cleanup('<name>/_staging/phase4')
"
```
Verify: `ls <name>/processes/PROC-*.md | wc -l`

## Stakeholder Interview Log

After each interview round, append rows to the `## Stakeholder Interview Log` section of `evidence-log.md`. This section is rendered directly in the Evidence tab of the deliverable — it is the auditable record of who contributed to the engagement.

**Required format in `evidence-log.md`:**

```markdown
## Stakeholder Interview Log

| Name | Role | Round | Date | Topics Covered |
|---|---|---|---|---|
| Jennifer Walsh | VP HR Operations | R1 — Sponsor | 2026-05-01 | Strategic framing, constraints, baseline estimates |
| Maria Santos | Sr. Director, HRBPs | R2 — Operator | 2026-05-03 | Req review process, HRBP touchpoints, change mgmt posture |
| [Name] | [Role] | R2 — Operator | [Date] | [Topics] |
```

**Rules:**
- Every participant must be named — no role-only rows (e.g., "3 Recruiters" is not acceptable)
- If a participant requests anonymity, record their role and a note: e.g., "Anonymous — Senior Recruiter (anonymized at participant request)"
- One row per session; if the same person appears in multiple rounds, add a row for each round
- Date is the actual session date, not the phase date
- Topics Covered is a short phrase — enough to reconstruct what was asked

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The sponsor described the process — we don't need to interview operators." | Sponsors describe the process as it should run. Operators describe how it does run. The gap is the opportunity. |
| "Baselines are nice-to-have; we can estimate value." | Estimated value without a baseline is a guess that survives until delivery. Baselines are a hard gate — no value claim survives without one. |
| "Cycle time is hard to get — we'll use 'a few days'." | "A few days" is unfalsifiable. Median + P90 forces honesty and exposes long-tail pain. |
| "FTE effort estimates are sensitive — we'll skip them." | FTE is the most credible value lever to a CFO. Capture it with appropriate framing, not by omission. |
| "Two interview rounds is enough." | Two rounds gives you the sponsor's view and the operator's view but no triangulation. Adjacent and clarification rounds catch what the first two miss. |
| "Recording participant names is administrative overhead — we know who we talked to." | The stakeholder interview log is the only record that survives the engagement. Without it, the deliverable cannot answer "who did you talk to?" — the first question any skeptical executive will ask. Record as you go; reconstructing it from memory at the end is error-prone and often incomplete. |
| "The process works — we just need to automate the slow steps." | Automate a broken process and you get a faster broken process. The challenge hypothesis forces the second-order question — is the boundary, actor model, or sequence itself the constraint? — before any automation is typed. Surface it; the client decides. |

## Handoff Protocol

**Output rule:** Do NOT reproduce the contents of `processes/PROC-NNN.md` or `processes/_index.md` in this response. State the file paths only. Present findings as bullets — do not quote or echo file content.

Before invoking the next skill, Janice must surface the phase output to the user:

1. **Name the file(s) written** and their path
2. **Summarize key findings** in 3–5 bullets — the most important decisions, flags, or measurements from this phase
3. **State the next phase** and what it will do in one sentence
4. **Wait for explicit user approval** — "proceed," "go ahead," "yes," or equivalent

**Do not auto-chain.** Every phase transition is a human decision. If the user says "stop," "hold," or does not respond with approval, do not proceed to the next phase.

Key findings to surface for this phase: processes mapped (count), baselines captured, any "baseline unavailable" flags, stakeholder interview log completeness.

**Session boundary:** After the user approves `processes/_index.md`, this phase session is complete. Instruct the user to start a fresh Claude Code session and invoke `ai-process-assessment:identifying-opportunities` to begin Phase 5. Do not continue methodology work in this session.

## Chain to next skill

→ `ai-process-assessment:identifying-opportunities` (after `processes/_index.md` is saved)
