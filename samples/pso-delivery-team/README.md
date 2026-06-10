# Sample Engagement — Lattice Consulting Group (PSO Delivery Team)

**This is fictional sample data.** Every name, number, system, and quote in this folder is invented for demonstration. "Lattice Consulting Group," its people, and its systems do not exist. Do not treat any figure here as a real benchmark.

## What this is

A complete set of **raw intake materials** for a demonstration engagement, plus a skill that runs them through the full AI & Automation Use Case Identification methodology (Phases 1–11 + the two gates) end to end — no live client required.

The scenario is deliberately self-referential: the engagement assesses a **professional services organization's own delivery team** — how a consulting firm staffs projects, writes SOWs, reports status, enters time, reviews deliverables, invoices, and forecasts margin — and where AI/automation could help. It's a domain every installer of this plugin already understands, which makes it a good teaching example and a good regression check after changing the methodology.

## The scenario in one paragraph

Lattice Consulting Group (~$240M revenue, ~420 billable consultants) has a delivery-margin problem: utilization is 68% against a 75% target, consultants are drowning in administrative work, and DSO is creeping toward 60 days. The CDO, **Dana Okafor**, wants a ranked, defensible shortlist of delivery-side AI/automation opportunities to take into the FY27 budget cycle — and has to defend it to a CFO who was burned by a failed automation program ("Project Swift"). The intake materials give the methodology everything it needs to scope the decision, map context, inventory systems, discover seven delivery processes with real baselines, and carry them through to a client-ready deliverable.

## Files

| File | Feeds | What it contains |
|---|---|---|
| `intake/engagement-request.md` | Phase 1 — Scoping | The sponsor's brief: the ask, the named decision-maker, scope, success criteria, budget/timeline, political sensitivities |
| `intake/org-context.md` | Phase 2 — Context | Business model, margin pressure, strategic priorities, org structure, AI maturity (one prior win, one prior failure), funding model, risk posture, political landscape |
| `intake/systems-and-data.md` | Phase 3 — Tech & Data | Systems of record, integrations, data assets with quality/cadence, enabler gaps, IT governance, build/buy posture, shadow IT |
| `intake/interview-notes.md` | Phase 4 — Discovery | Four-round interview material for seven processes, each with volume / cycle time (median + P90) / error rate / FTE effort, plus three cross-round conflicts to reconcile and a consolidated baseline table |

The seven processes: staffing & resource assignment, SOW creation, weekly status reporting, time entry & approval, deliverable QA review, invoicing & billing reconciliation, and project financial forecasting (EAC).

## How to run it

Invoke the **`ai-process-assessment:running-sample-engagement`** skill (say something like *"run the sample engagement"* or *"test the methodology"*). It is a guided entry point — **not** a shortcut. It:

1. Points you at `intake/` as the source material for Phases 1–4.
2. Has you invoke `ai-process-assessment:scoping-engagement` and proceed through the normal phase chain.
3. Wherever a phase would interview a live human, you read the corresponding intake file instead.
4. **Preserves every normal gate and session boundary** — you approve each phase transition and restart sessions exactly as in a real engagement.
5. Produces a complete engagement under `sample-pso-delivery/`, terminating in `deliverable.html`.

There is no answer key and no pre-filled phase output. Phases 1–4 interpret the raw intake into structured outputs; Phases 5–11 do the analysis. The baselines in `interview-notes.md` are constructed to support the value claims the later phases derive — so a faithful run should not produce orphan value hypotheses.

## What it's good for

- **Learning** the methodology by watching it run on a realistic case.
- **Demonstrating** the full pipeline to a prospective user or stakeholder.
- **Regression-testing** after a change: run the sample and confirm every phase still produces its output file and the gates still fire (the scenario is built so Gate A — GRC — actually triggers on the deliverable-content and commercial-data opportunities).

The resulting `deliverable.html` doubles as the canonical reference example of what a finished engagement looks like.
