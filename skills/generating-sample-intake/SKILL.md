---
name: ai-process-assessment:generating-sample-intake
description: Generates a complete set of synthetic intake files for an AI process assessment sample engagement, tailored to any business model. Produces four intake files + README + .sample-run.md marker. Output is immediately runnable via ai-process-assessment:running-sample-engagement.
---

# Generating Sample Intake

## What this skill does

Synthesizes a complete set of sample engagement intake files for a business model you describe. Output: four intake files (`engagement-request.md`, `org-context.md`, `systems-and-data.md`, `interview-notes.md`) + a scenario README, written to `samples/<slug>/intake/`, plus a `.sample-run.md` marker in `sample-<slug>/`.

The generated scenario is built to the same fidelity as the bundled PSO sample: intentional stakeholder conflicts, a GRC-triggering data asset, cost anchors (no invented vendor quotes), and no pre-seeded phase outputs. When this skill completes, the engagement is ready to run end-to-end via `ai-process-assessment:running-sample-engagement`.

## Step 1 — Choose a business model

Present the following options and wait for the user to select one or type their own description:

**A. Retail fulfillment & returns** — mid-size e-commerce retailer, 500–800 employees; warehouse + customer ops team in scope  
**B. Healthcare back-office** — regional health system (5–10 hospitals); revenue cycle + patient access team in scope  
**C. Financial services compliance** — regional bank or credit union; compliance + risk ops team in scope  
**D. Manufacturing operations** — discrete manufacturer (industrial or consumer goods); production planning + quality team in scope  
**E. Other — describe it** — type a brief description: industry, approximate size, team in scope (e.g., "mid-size logistics company, dispatch and fleet ops team")

If the user selects A–D, use the preset description as the business model context. If E, use their free-form description.

## Step 2 — Derive slug and confirm

From the business model description, derive a lowercase kebab-case slug, 3–5 words, max 30 characters. Examples:
- "mid-size e-commerce retailer, warehouse ops" → `ecomm-fulfillment-ops`
- "regional bank, compliance team" → `bank-compliance-ops`
- "regional health system, revenue cycle" → `health-revenue-cycle`
- "discrete manufacturer, production planning" → `mfg-production-ops`

Engagement folder: `sample-<slug>/`  
Intake folder: `samples/<slug>/intake/`

State the proposed names and ask: *"I'll create your scenario at `sample-<slug>/` with intake files at `samples/<slug>/intake/`. Does that look right, or would you like a different slug?"* Wait for confirmation before writing any files.

## Step 3 — Design the scenario (plan before writing)

Before writing any file, sketch the full scenario internally. Every element you plan here must be consistent across all four intake files.

1. **Company profile**: fictional company name, industry, revenue range, total headcount, team in scope (name + headcount), 2–3 key operational KPIs with current vs. target gap (e.g., utilization 68% vs. 75% target; error rate 12% vs. 5% target; DSO 58 days vs. 45-day target).

2. **5–9 in-scope processes**: name each, assign a PROC-ID (PROC-01…PROC-0N), identify the primary operator role, rough volume and FTE.

3. **Stakeholder cast**: sponsor (executive decision-maker), a skeptic (finance/CFO equivalent), at least one protective department head, 3–4 operator-level interviewees. Every named stakeholder needs a name, role, and posture that is consistent across all four files.

4. **Two conflicts**: pick two processes where the sponsor's Round 1 top-down estimate disagrees with the operator's Round 2 bottom-up count. Plan both the disagreement and the Round 4 resolution before writing.

5. **One GRC-triggering opportunity**: at least one process must involve a sensitive data asset (PII, regulated records, client-confidential content, financial data) so the GRC gate fires naturally in Phase 5. The sensitivity must appear in `systems-and-data.md` (marked High) and in the `interview-notes.md` process steps.

6. **Cost anchors**: define a blended labor rate ($/hr), FTE fully-loaded annual cost ($/FTE-year), and 1–2 revenue or cost metrics that let Phase 9 build a ROM business case. Do not invent vendor quotes; missing cost inputs are logged as open items in Phase 9, exactly as in a real engagement.

Before proceeding to Step 4, verify your plan against the **Step 6 Constraints Checklist**. Only begin writing once all items pass.

## Step 4 — Write the files

Write files in this order. Follow each schema exactly.

### 4a. `samples/<slug>/README.md`

```
> **Fictional scenario.** All company names, people, and figures are invented for methodology demonstration purposes only.

## Scenario
[One paragraph: company name, industry, what the company does, why they're doing an AI assessment now — tie directly to the KPI gaps from Step 3.]

## In-scope team
[One paragraph: which department/function is in scope, headcount, number of processes covered, primary stakeholders.]

## Why this scenario
[2–3 sentences: what makes this a good methodology test — name the GRC gate, the conflicts, and the cost-anchor pattern explicitly so a new user knows what to look for.]

## Intake files

| File | Phase | Contents |
|---|---|---|
| engagement-request.md | 1 — Scoping | Sponsor memo: ask, scope, constraints, stakeholder postures |
| org-context.md | 2 — Context | Company profile, org structure, AI maturity, political landscape |
| systems-and-data.md | 3 — Tech & Data | System inventory, integrations, data catalog, IT posture |
| interview-notes.md | 4 — Discovery | Four interview rounds with baselines, conflicts, and consolidation |

## No answer key

The methodology must interpret the raw intake. Phase outputs (PROC-NNN.md, OPP-NNN.md, scores, roadmap, business case) are not pre-seeded here.
```

### 4b. `samples/<slug>/intake/engagement-request.md`

```
> **Fictional scenario.** All company names, people, and figures are invented for methodology demonstration purposes only.

**From:** [Sponsor name, title]  
**To:** Assessment team  
**Date:** [plausible date]  
**Re:** AI / automation opportunity assessment — [team in scope]

## The ask
[What the sponsor wants: a ranked, defensible shortlist with a business case strong enough to survive [skeptic's] scrutiny and secure Investment Committee approval.]

## Why now
[Three colliding pressures driving urgency — tie to the KPI gaps: e.g., cost pressure + error rate + capacity constraint. Each pressure gets 1–2 sentences.]

## What I will do with the output
[The decision this engagement enables. Include a target delivery date tied to a budget cycle or leadership review.]

## Rough scope

**In scope:**
- [Process 1 — PROC-01]
- [Process 2 — PROC-02]
- [... one bullet per process]

**Out of scope:**
- [2–4 explicitly excluded areas — e.g., sales pipeline, HR systems, anything outside the team boundary]

## What "good" looks like
- A ranked shortlist of AI/automation opportunities
- Real baselines (volume, cycle time, error rate, FTE) under every savings number
- A ROM business case (AACE Class 5, ±50%) that can go to the Investment Committee
- An organizational-change read on each initiative (who resists, why)

## Constraints you should know

**Budget:** [Dollar amount — e.g., $800K opex envelope for FY27]

**Timeline:** [Target delivery date — e.g., end of Q2 FY27]

**Politics:**
- [Skeptic name], [role] — skeptical; will challenge every assumption. Every number needs a source.
- [Protector name], [role] — protective of [their domain]; will resist anything that touches [sensitive area].
- [Additional stakeholder] — [posture and why it matters]

**Access limitations:** [The sensitive-data constraint that will trigger the GRC gate — e.g., no unrestricted access to [data type]; any use case touching it requires DLP/tenancy isolation review.]

## Who you will talk to

[Prose paragraph listing each interviewee by name and role, with the process area or question domain they cover. Example: "We will start with [Operator 1], [Title], who owns PROC-01 and PROC-02. [Operator 2], [Title], covers PROC-03 and PROC-04. [Adjacent stakeholder], [Title], provides upstream context on [what they receive from the team]." One sentence per interviewee.]
```

### 4c. `samples/<slug>/intake/org-context.md`

```
> **Fictional scenario.** All company names, people, and figures are invented for methodology demonstration purposes only.

*Prepared by [role, e.g., the CFO's chief of staff]*

## 1. The company and how it makes money
[Revenue, total headcount, team in scope headcount, core business model in 3–4 sentences. Include 2–3 key operational/financial metrics with current vs. target values — these become the value anchors for Phase 7 roadmap and Phase 9 business case.]

## 2. Strategic priorities ([FY year] planning cycle)
1. [Priority tied to KPI gap #1]
2. [Priority tied to KPI gap #2]
3. [Priority tied to KPI gap #3]
4. [Optional 4th priority]

## 3. Org structure relevant to scope
[Narrative org chart: who the sponsor reports to, which functions are in scope, named leaders per function. 3–5 sentences.]

**Key seams:** [1–2 sentences on contested ownership between functions — equivalent to PSO's "RMO vs. Practices" tension. This feeds the political risk section of Phase 7.]

## 4. AI / automation maturity
[Honest assessment: low / low-to-moderate / moderate.]

**Prior win:** [One successful automation or data project — name it, give a date, describe the outcome briefly. This establishes credibility and a reference point.]

**Prior failure or false start:** [One failed or shelved initiative — name it, give a date, describe what went wrong. This is critical for political context; the skeptic stakeholder's posture traces here.]

**Shadow adoption:** [1–2 examples of unofficial AI tool use — the demand signal and the governance risk that will drive GRC gate activity.]

## 5. Funding model
[Opex budget pool size. Approval authority (name + role). Decision cycle timing. Preference for build vs. buy vs. configure — and why (post-failure bias, team size, preferred vendor ecosystem).]

## 6. Risk posture
[What data is the sharp edge. What the binding condition is for sensitive-use cases (DLP, tenancy isolation, access controls). Regulatory posture (regulated, regulated-adjacent, or unregulated but risk-conscious).]

## 7. Political landscape

| Stakeholder | Role | Posture | Why it matters |
|---|---|---|---|
| [Sponsor] | [Title] | Champion | [What they'll do with the output] |
| [Skeptic] | [Title] | Skeptical | [Their concern — usually cost or past failure] |
| [Protector] | [Title] | Protective of [domain] | [What they'll resist and why] |
| [Operator archetype] | [Title] | Cautious / curious | [How operator sentiment will affect adoption] |
| [... 1–2 additional rows as needed] | | | |
```

### 4d. `samples/<slug>/intake/systems-and-data.md`

```
> **Fictional scenario.** All company names, people, and figures are invented for methodology demonstration purposes only.

*Compiled from a walkthrough with [name], [role — e.g., IT Director or Head of Operations].*

## 1. System inventory

| System | Category | Role in delivery | Owner | Lifecycle | API |
|---|---|---|---|---|---|
| [Core system] | [Category] | [What it does for the in-scope processes] | [Owner team] | [Active / Legacy / Sunset] | [Yes / No / Limited] |
| [... 5–8 rows; include at least one shadow-IT / unofficial system at the bottom] |

## 2. Integration & API map

| Integration | Mechanism | Reliability | Known gap |
|---|---|---|---|
| [System A] → [System B] | [Batch / API / Manual re-key] | [High / Medium / Low / Unreliable] | [What data is lost or delayed] |
| [... 4–6 rows; include at least one manual re-keying gap and one batch process with data quality loss] |

## 3. Data asset catalog

| Data asset | Location | Quality | Refresh | Sensitivity |
|---|---|---|---|---|
| [Asset name] | [System] | [High / Medium / Low] | [Real-time / Daily / Weekly / Manual] | [Low / Medium / High] |
| [... 6–9 rows; the GRC-triggering asset must appear here marked High sensitivity] |

## 4. Foundational enabler gaps
- [No SSO model or identity layer for AI agents]
- [No AI observability / audit logging]
- [No DLP or access controls for [sensitive data type] — binding constraint for GRC-flagged use cases]
- [No data catalog or MDM — data quality assertions are informal]
- [... 1–2 additional gaps relevant to the scenario]

## 5. IT governance posture
[Approval cadence, security review process, preferred cloud/vendor, AI policy status (draft / approved / none), overall posture descriptor (risk-leaning / pragmatic / permissive).]

## 6. Build / Buy / Partner posture
[Narrative preference with context: post-failure bias toward buy/configure, team size constraint, preferred vendor ecosystem or relationship, any known vendor evaluations in progress.]

## 7. Shadow IT
- [Unofficial tool #1]: [what it does, who uses it, why it exists — the demand signal]
- [Unofficial tool #2]: [governance risk it represents]
- [... 1–2 additional items]
```

### 4e. `samples/<slug>/intake/interview-notes.md`

This is the most complex file. Write all four rounds.

```
> **Fictional scenario.** All company names, people, and figures are invented for methodology demonstration purposes only.

| ID | Process | Primary operator |
|---|---|---|
| PROC-01 | [Process name] | [Role] |
| PROC-02 | [Process name] | [Role] |
| [... one row per process] |

# ROUND 1 — Sponsor (strategic framing)

**Participant:** [Sponsor name, title]  
**Date:** [Date — before Round 2]  
**Topic:** Top-down strategic framing

[For each process, one short paragraph with the sponsor's top-down estimate of volume, effort, or impact. Where a conflict is seeded, append the flag inline:]

> (Flag: this estimate conflicts with the operator round — see Conflict A.)

[Repeat for Conflict B on the other seeded process.]

# ROUND 2 — Operators (actual execution)

## [Process name] (PROC-01)

**Participant:** [Operator name, title]  
**Date:** [Date]  
**Topic:** [Process name] — end-to-end execution

**Trigger:** [What starts this process]

**Steps:**
1. [Step 1]
2. [Step 2]
3. [... numbered steps as actually executed]

**Decision points:** [Where human judgment is required]

**Exceptions:** [Known exception types and frequencies]

**Baseline (source, method):**
- Volume: [quantity/period, e.g., "~180 cases/month"]
- Cycle time: median [X] [unit], P90 [Y] [unit]
- Error/exception rate: [%] ([what it means in practice])
- FTE effort: [N] FTE ([qualifier — e.g., "blended across senior and junior staff"])
- Source confidence: [High / Medium-High / Medium / Low]

> "[Verbatim operator quote that captures the pain point or a key nuance]"

[Repeat this H2 block for every process in Round 2. For the two conflict processes, use numbers that disagree with Round 1.]

[If two operator roles each have a distinct view of the same process (e.g., an approver and a submitter both touch the same process but see it differently), write two H2 blocks for that process — one per participant — and note in both that their views are reconciled in Round 4. This is the mechanism that produces a third conflict when the scenario warrants it.]

# ROUND 3 — Adjacent (upstream / downstream)

## [Adjacent stakeholder name] ([Role])

**Date:** [Date]

[Narrative — not structured baseline format. This stakeholder contributes upstream/downstream perspective: what they receive from the in-scope team, what errors or delays they absorb, what they wish were different. Include the data points that raise or reinforce the two conflicts.]

[Repeat for 2–3 adjacent stakeholders.]

# ROUND 4 — Clarification (resolve conflicts)

**Participants:** [Group session attendees]  
**Date:** [Date — last of the four rounds]

### Conflict A — [Process name] ([what disagreed, e.g., "volume estimate"])

**Disagreement:** [Sponsor said X; operator said Y. Adjacent stakeholder data suggested Z.]

**Resolution:** [How it was resolved — e.g., "Operator's system pull (High confidence) accepted as baseline; sponsor's estimate reflected aspirational target, not current state."]

**Recorded baseline:** [Final agreed value with confidence rating]

### Conflict B — [Process name] ([what disagreed])

**Disagreement:** [...]

**Resolution:** [...]

**Recorded baseline:** [...]

[Add a ### Conflict C (and D, etc.) section for each additional conflict seeded in Rounds 1–3. Every seeded conflict must be resolved here before the Consolidated Baseline Table.]

# CONSOLIDATED BASELINE TABLE

| Process | Volume | Cycle time (median / P90) | Error / exception | FTE effort | Source confidence |
|---|---|---|---|---|---|
| PROC-01 — [name] | [volume] | [median] / [P90] | [rate] | [N FTE] | [rating] |
| [... one row per process] |

**[Company name] firm-level anchors (for Phase 9 business case):**
- [N] [role] staff in scope across all processes
- Blended labor rate: $[X]/hr
- FTE fully-loaded cost: ~$[Y]K/FTE-year
- [Key revenue or cost metric #1 with current value]
- [Key revenue or cost metric #2 with current value]
- Total estimated FTE effort in scope: ~[N] FTE administrative / coordination burden

**Capability evidence — neutral facts only, never a verdict:**

Do **not** write any AI-capability rating, color, or chain-membership conclusion anywhere in the intake. In the new Phase 4 flow the `step-capability-tagger` derives each step's capability *attributes* (and the engine computes the colors and chains) from the factual evidence you already wrote — pre-stating a conclusion here re-introduces the anchoring bias the new flow exists to remove. Instead, make sure the raw evidence each process needs is present and *discriminating*:

- **Round 2 step verbs and decision points** carry whether work is rule-based or human-judgment.
- **Trigger and inputs** carry whether data arrives structured or unstructured.
- **Exception rate and types** (already in each baseline) carry the accuracy bounds.
- **`systems-and-data.md`** carries the API availability and data sensitivity for every system a process touches.

Vary this across the process set so the derived capability mix is non-trivial: include at least one process whose steps are clearly rule-based on structured data, at least one dominated by human judgment or relationship work, and at least one that touches the High-sensitivity asset. State each of these as a plain fact in the step descriptions and the systems/data tables — never as a capability rating.
```

## Step 5 — Write the `.sample-run.md` marker

Create `sample-<slug>/` if it does not already exist. Write `sample-<slug>/.sample-run.md` with exactly this content (substitute `<slug>` throughout):

```markdown
---
sample: <slug>
intake_root: samples/<slug>/intake
---

# Sample Run Marker

This file signals that this engagement folder contains a sample run of the
`<slug>` scenario. Phase skills check for this file at Session Start and
substitute bundled intake files for live elicitation.

## Phase Intake Map

| Phase | Intake file (relative to intake_root) |
|---|---|
| 1 — Scoping | engagement-request.md |
| 2 — Context | org-context.md |
| 3 — Tech & Data | systems-and-data.md |
| 4 — Discovery | interview-notes.md |
```

## Step 6 — Constraints checklist

Before writing any file, verify your scenario plan satisfies all of these. If any are unmet, revise the plan before writing.

- [ ] 5–9 in-scope processes with PROC-IDs
- [ ] All named stakeholders are consistent across all four files (same name, role, posture everywhere)
- [ ] At least 2 conflicts seeded in Rounds 1–3 and resolved in Round 4
- [ ] At least 1 data asset marked High sensitivity in systems-and-data.md (drives GRC gate)
- [ ] At least 1 shadow-IT tool in systems-and-data.md
- [ ] Cost anchors present (blended rate + FTE cost + ≥1 revenue/cost metric); no invented vendor quotes
- [ ] The prior failure / false start in org-context.md connects to the skeptic's posture
- [ ] No phase outputs pre-seeded (raw intake only)

## Step 7 — Verify, then confirm and return control

**Verify before you claim anything.** Never report files you did not write. After the
writes, **verify every intake file exists on disk** — list each expected path and confirm
it is present and non-empty before producing the confirmation block:

```bash
for f in \
  samples/<slug>/README.md \
  samples/<slug>/intake/engagement-request.md \
  samples/<slug>/intake/org-context.md \
  samples/<slug>/intake/systems-and-data.md \
  samples/<slug>/intake/interview-notes.md \
  sample-<slug>/.sample-run.md ; do
  [ -s "$f" ] && echo "OK   $f" || echo "MISSING $f"
done
```

If any path reports `MISSING` (or the folder was never created), **stop and say so plainly**
— do not narrate a scenario that is not on disk. Re-create the missing file, or surface the
failure to the user. Only once every path reads `OK` do you confirm what was created:

```
Generated scenario: [Company name]
Slug: <slug>
Engagement folder: sample-<slug>/
Intake files written (verified on disk):
  samples/<slug>/README.md
  samples/<slug>/intake/engagement-request.md
  samples/<slug>/intake/org-context.md
  samples/<slug>/intake/systems-and-data.md
  samples/<slug>/intake/interview-notes.md
Sample run marker: sample-<slug>/.sample-run.md

Processes in scope: PROC-01 through PROC-0N ([N] processes)
Conflicts seeded: Conflict A ([process]), Conflict B ([process])
GRC trigger: [process + data asset]
```

**Then return control to whoever invoked you — never hand the user a manual restart.**
Continuation is the Conductor's job, not the user's:

- **Invoked from the Conductor / `running-sample-engagement` (the normal path):** return
  silently with the engagement name (`sample-<slug>`) and intake root
  (`samples/<slug>/intake`). The Conductor picks up in sample mode and drives Phase 1
  itself, reading `samples/<slug>/intake/engagement-request.md` in place of a live sponsor
  interview. Do **not** tell the user to restart a session or invoke a skill.
- **Invoked truly standalone** (no Conductor in the loop): say the scenario is ready and
  offer to run it now — then continue into `ai-process-assessment:conducting-engagement`
  in this same session, which detects the `.sample-run.md` marker and drives. The user
  never needs to know a phase name or a skill id.

## Chain to next skill

→ `ai-process-assessment:running-sample-engagement` (after generation is complete)
