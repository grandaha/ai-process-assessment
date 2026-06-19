# Process Discovery Interview Notes — Lattice Consulting Delivery Org

> **Sample intake document — fictional.** Feeds Phase 4 (Process Discovery). Organized as the methodology's four-round sequence (sponsor → operator → adjacent → clarification). Contains the volume / cycle-time / error-rate / FTE baselines that every downstream value claim must cite, plus three cross-round conflicts to reconcile. All names, numbers, and systems invented. See `../README.md`.

**Processes covered (7):**

| ID | Process | Primary operator |
|---|---|---|
| PROC-01 | Staffing & Resource Assignment | Priya Nair (RMO) |
| PROC-02 | SOW / Proposal Creation | Tom Bradley (Engagement Mgmt) |
| PROC-03 | Weekly Status Reporting | Sofia Reyes (PM) |
| PROC-04 | Time Entry & Approval | James Carter (consultant) / Greg Olsen (finance) |
| PROC-05 | Deliverable QA Review | Aisha Khan (Quality Office) |
| PROC-06 | Invoicing & Billing Reconciliation | Greg Olsen (Project Finance) |
| PROC-07 | Project Financial Forecasting (EAC) | Sofia Reyes (PM) |

---

# ROUND 1 — Sponsor (strategic framing)

**Participant:** Dana Okafor, Chief Delivery Officer — **2026-05-06** — Topics: strategic framing across all seven processes, rough baselines, constraints.

Dana's framing: "Every one of these processes is administrative overhead between a consultant and billable work. I don't need them to disappear, I need them to stop eating half a day a week per person. Tell me where the time actually goes."

Process-by-process, as the sponsor sees it (note: several of these are *estimates from the top*, to be checked against operators):

- **PROC-01 Staffing.** Exists to put the right people on the right projects fast. Dana's view: "takes too long, and we redo a lot of it." Rough guess: a few days per staffing decision, "maybe a fifth get redone."
- **PROC-02 SOW creation.** Exists to scope and price engagements. Dana: "Our SOWs are copy-paste from the last one. Quality is uneven and margin errors slip through."
- **PROC-03 Status reporting.** Exists to keep clients informed and surface risk. Dana's estimate: **"A status report is what, 30 minutes? Half an hour. The PMs do them every week."** *(Flag: this estimate conflicts with the operator round — see Conflict A.)*
- **PROC-04 Time entry.** Exists to capture billable hours. Dana: "Late and sloppy. It delays billing and we leak revenue. I don't have a number."
- **PROC-05 QA review.** Exists to protect deliverable quality and the firm's reputation. Dana: "Bottlenecked on senior people. And the misses are expensive when they reach the client."
- **PROC-06 Invoicing.** Exists to convert delivered work to cash. Dana: "Slow. Lots of rebills. This is the DSO problem. Also the one Marcus is most scarred about after Swift."
- **PROC-07 Forecasting / EAC.** Exists to see margin erosion before it happens. Dana: "We find out about overruns at month close, which is too late."

Constraint reminders from Dana: $1.5M envelope, decision by September, CFO is the skeptic, Priya is protective of staffing, Quality Office is wary of AI QA, client deliverable content is confidential.

---

# ROUND 2 — Operators (actual execution)

## PROC-01 — Staffing & Resource Assignment

**Participant:** Priya Nair, Director, Resource Management Office — **2026-05-11** — Topics: staffing process walkthrough, availability data, rework.

**Trigger:** A project is won (or a roll-off creates a gap) and a staffing request enters the RMO queue.

**Steps as actually executed:**
1. Engagement manager submits a staffing request (role, skills, start date, duration) — often by Slack or email, not always in Polaris.
2. RMO analyst checks the **Staffing Grid** (Excel) for who is actually available — *not* Polaris, because "Polaris is always a week behind reality."
3. Analyst cross-checks skills — but skills tags in Polaris are incomplete, so this is largely from memory and relationships.
4. Analyst proposes 1–3 candidates back to the engagement manager.
5. Engagement manager and practice lead negotiate / push back ("I want a senior, not that person").
6. Assignment confirmed and *then* entered into Polaris (often days after the real decision).

**Decision points:** candidate selection (judgment-heavy — skills, client fit, development goals), and conflict resolution when two projects want the same person.

**Exceptions:** double-bookings (the Grid and Polaris disagree), last-minute client start-date changes, "soft" swaps where someone is quietly moved without a formal re-request.

**Baseline (Priya, sampled from RMO logs):**
- **Volume:** ~**140 staffing actions/month** (new assignments + re-rolls).
- **Cycle time:** **median 3 business days**, **P90 11 business days** from request to confirmed assignment.
- **Error/exception rate:** **22%** of assignments are formally reassigned after first confirmation ("hard rework"). *(Priya is firm on 22%. See Conflict B — Lena thinks it's higher.)*
- **FTE effort:** **3.5 FTE** across the RMO doing this.
- **Source confidence:** Medium (sampled from RMO request logs, not a clean system report).

Priya's posture, unprompted: "I will tell you now — if this turns into 'the system decides who staffs what,' it will not work and I will not support it. The judgment is the job. A tool that hands me a good shortlist faster? That I'd take."

## PROC-02 — SOW / Proposal Creation

**Participant:** Tom Bradley, Engagement Manager (Strategy & Ops) — **2026-05-11** — Topics: SOW drafting, scoping, rate cards, rework.

**Trigger:** A pursuit reaches the stage where a written SOW/proposal is needed.

**Steps:**
1. Engagement manager finds the "closest" prior SOW in Confluence/SharePoint and copies it.
2. Edits scope, deliverables, assumptions by hand.
3. Builds the staffing/price model in a spreadsheet using the rate card (which lives in a separate doc and is sometimes out of date).
4. Routes to legal for terms and to finance for margin sign-off.
5. Iterates — legal and finance frequently send it back.
6. Final SOW issued to client.

**Decision points:** scope boundaries, pricing/discount, risk assumptions. Judgment-heavy.

**Exceptions:** non-standard terms, custom pricing, multi-phase work.

**Baseline (Tom, estimated):**
- **Volume:** ~**20 SOWs/month** (~60/quarter).
- **Cycle time:** **median 6 business days**, **P90 19 business days** from "we need an SOW" to issued.
- **Error/exception rate:** **30%** require a legal/finance rework loop; **12%** ship with a margin or rate error caught only later.
- **FTE effort:** ~**2.2 FTE-equivalent** of engagement-manager time.
- **Source confidence:** Medium (Tom's estimate plus a count of SOWs issued last quarter).

Tom, candidly: "Half the team already drafts these in ChatGPT and then sanitizes them. Nobody will say that out loud, but it's true."

## PROC-03 — Weekly Status Reporting

**Participant:** Sofia Reyes, Senior Project Manager — **2026-05-12** — Topics: status report assembly, data sources, effort, forecasting (PROC-07 below).

**Trigger:** Weekly cadence; each active project produces a client status report.

**Steps:**
1. PM pulls hours/burn from **Polaris**.
2. PM pulls current financials from **NetSuite** extracts (or a personal spreadsheet, because intra-month NetSuite numbers lag).
3. PM scans **Slack** threads and emails for risks/issues/decisions.
4. PM reformats all of it into the **client's** status template (varies by client).
5. PM writes narrative (accomplishments, next steps, risks, RAG status).
6. PM sends; sometimes a practice lead reviews first.

**Decision points:** RAG status judgment, what risk to surface vs. manage quietly, narrative framing for the client.

**Exceptions:** client-specific templates, escalations, reports that need rework when the financials turn out stale.

**Baseline (Sofia, with a 15-report stopwatch sample she ran for this engagement):**
- **Volume:** ~**180 active projects**, each weekly → ~**720 status reports/month**.
- **Cycle time (effort):** **median 90 minutes** per report, **P90 4 hours** for complex/multi-workstream projects. *(This directly contradicts Dana's "30 minutes." See Conflict A.)*
- **Error/exception rate:** **15%** go out with financials that are stale or get corrected after the fact.
- **FTE effort:** ~**5.5 FTE-equivalent** of PM time across the portfolio — the single largest administrative load in delivery.
- **Source confidence:** Medium-High (Polaris gives exact report counts; effort is a 15-report timed sample).

Sofia: "The narrative is mine — that's judgment. But 60–70% of the time is just *gathering and reformatting* numbers that already exist in three systems. That part is soul-crushing and it's most of the clock."

## PROC-05 — Deliverable QA Review

**Participant:** Aisha Khan, Quality Office Lead — **2026-05-12** — Topics: QA gate, reviewer capacity, defects, standards.

**Trigger:** A client deliverable is ready for release and enters the QA queue.

**Steps:**
1. Consultant submits deliverable to the QA queue (SharePoint + a Confluence checklist).
2. A senior/principal reviewer is assigned (scarce capacity).
3. Reviewer checks against the QA checklist: completeness, accuracy, brand/format, client-readiness.
4. Reviewer returns comments; consultant revises.
5. Re-review if needed; sign-off; release to client.

**Decision points:** "is this client-ready" — heavily judgment-based; brand and reputational risk live here.

**Exceptions:** rush deliverables that skip or shortcut QA; high-stakes deliverables that get extra scrutiny.

**Baseline (Aisha, estimated from QA queue):**
- **Volume:** ~**250 deliverables/month** through the QA gate.
- **Cycle time:** **median 1.5 business days**, **P90 6 business days** (waiting on a free senior reviewer is the bottleneck).
- **Error/exception rate:** **20%** returned for revision; **~5%** ship with a defect that reaches the client (rework + relationship cost).
- **FTE effort:** ~**2.5 FTE-equivalent** of senior/principal time — expensive time.
- **Source confidence:** Medium (QA queue logs + Aisha's estimate of reviewer hours).

Aisha, guarded: "If you're going to tell me an AI grades our deliverables, stop. These contain client-confidential material and the standard *is* the firm's reputation. A tool that runs the mechanical checklist — formatting, completeness, broken cross-references — so my seniors spend their judgment on the substance? Different conversation. But the content cannot leave our walls."

## PROC-06 — Invoicing & Billing Reconciliation

**Participant:** Greg Olsen, Billing Manager, Project Finance — **2026-05-13** — Topics: invoicing, reconciliation, time-entry quality (finance side), Swift history.

**Trigger:** Billing period close; eligible time and expense must become invoices.

**Steps:**
1. Nightly Polaris→NetSuite batch lands time/expense in NetSuite — but ~25% needs adjustment because project/task codes map badly.
2. Billing analyst reconciles time against project billing rules (rate cards, caps, fixed-fee schedules, non-billable exclusions).
3. Analyst corrects miscoded or late time entries (chasing PMs and consultants).
4. Draft invoice generated; reviewed against the SOW terms.
5. Routed for PM/partner approval.
6. Issued to client; disputes handled downstream.

**Decision points:** what is billable vs. write-off, how to apply caps and fixed-fee milestones, dispute resolution.

**Exceptions:** disputed invoices, fixed-fee milestone timing, out-of-scope work, credit/rebill.

**Baseline (Greg, from NetSuite — system-pulled):**
- **Volume:** ~**480 invoices/month**.
- **Cycle time:** **median 5 business days**, **P90 16 business days** from period close to invoice issued. This is the core driver of the **58-day DSO**.
- **Error/exception rate:** **25%** of invoices require an adjustment or rebill; **~9%** are formally disputed by clients.
- **FTE effort:** ~**3.2 FTE** in the billing team.
- **Source confidence:** **High** (NetSuite billing records).

**On time-entry quality (PROC-04, finance side):** "People think their timesheets are clean. They are not. Our Polaris audit shows **18% of entries get corrected** after submission — wrong project code, wrong task, wrong day. And about **8% come in after the billing cutoff**, which is straight revenue leakage when it slips a period or gets written off." *(See Conflict C — the PMs think it's ~5%.)*

**On Swift, unprompted:** "Whatever you recommend on invoicing — do not call it RPA and do not promise it'll run unattended on day one. Swift promised that. It's a four-letter word here now."

## PROC-04 — Time Entry & Approval (operator + finance views)

Captured across Sofia (approver) in Round 2 and Greg (finance) above; consultant view comes in Round 3 (James Carter).

**Trigger:** Weekly timesheet deadline; consultants log billable/non-billable hours by project/task.

**Steps:**
1. Consultant enters hours in Polaris against project/task codes (often Friday afternoon, from memory).
2. Consultant submits timesheet.
3. Manager reviews and approves (or returns).
4. Finance catches and corrects errors the manager missed; chases late entries before billing cutoff.

**Decision points:** correct project/task coding, billable vs. non-billable classification.

**Exceptions:** late entries past cutoff, miscoded time, retroactive corrections.

**Baseline:**
- **Volume:** ~**420 consultants × weekly = ~1,680 timesheets/month**; ~**34,000 individual time entries/month**.
- **Cycle time:** on-time submission only **62%**; approval **median 2 business days**, **P90 9 business days**.
- **Error/exception rate:** **18% of entries corrected** after submission (Polaris audit, High confidence); **8% late past billing cutoff**.
- **FTE effort:** ~**3.0 FTE** combined (manager approval time + finance correction/chasing).
- **Source confidence:** **High** for the 18%/8% (Polaris audit); Medium for FTE split.

**Sofia's operator view (from her 05-12 interview):** "Honestly most timesheets are fine. Maybe **5%** need a fix when I approve them." *(Conflict C: contradicts the 18% Polaris audit Greg cites.)*

## PROC-07 — Project Financial Forecasting (EAC)

**Participant:** Sofia Reyes, Senior Project Manager — **2026-05-12** — Topics: EAC update walkthrough, data sources, effort, accuracy (continued from her PROC-03 interview).

**Trigger:** Monthly forecasting cadence (and ad hoc when a project's burn looks off); each active project produces an updated Estimate-at-Completion.

**Steps as actually executed:**
1. PM pulls actuals-to-date (hours burned, expenses) from **Polaris**.
2. PM pulls revenue/cost recognized from **NetSuite** — but only month-end close is trustworthy, so mid-month the PM falls back to a **personal spreadsheet tracker** to approximate intra-month position.
3. PM estimates remaining effort (ETC) per workstream from memory and the plan.
4. PM computes EAC (actuals + ETC) and compares to budget/SOW to flag margin erosion.
5. PM updates the forecast in Polaris and surfaces material variances in the status report / to the practice lead.

**Decision points:** ETC judgment per workstream (how much work is really left), whether a variance is signal or noise, when to escalate a margin slip.

**Exceptions:** scope changes mid-engagement, fixed-fee milestone timing, late-landing expenses, projects where the PM distrusts the NetSuite number and forecasts entirely off the personal tracker.

**Baseline (Sofia, estimated from the PM forecasting cadence):**
- **Volume:** ~**180 EAC updates/month** (≈ one per active project).
- **Cycle time (effort):** **median 3 hours** per project forecast, **P90 1.5 business days** for complex multi-workstream projects.
- **Error/exception rate:** **28% of forecasts are off by more than 10%** by the time the project closes *(matches Marcus's R3 figure — see below)*.
- **FTE effort:** ~**3.0 FTE-equivalent** of PM time across the portfolio.
- **Source confidence:** Medium (EAC update counts from Polaris; accuracy from Marcus's close-variance figure; effort is Sofia's estimate).

Sofia: "The forecast is only as good as my intra-month number, and I don't trust it until close. So I keep my own sheet, which means the 'official' forecast and my real one drift. By the time NetSuite tells the truth at close, the margin's already gone — it's a visibility problem, not a math problem."

---

# ROUND 3 — Adjacent (upstream / downstream)

## Marcus Bell, CFO — **2026-05-18** — Topics: downstream of forecasting & invoicing; DSO; ROI bar; Swift.

- Consumes PROC-06 (invoicing → cash) and PROC-07 (forecasts → margin management). "DSO is my problem and invoicing speed is most of it. If you can compress the close-to-invoice cycle, that's real cash, and I can measure it."
- On forecasting: "I find out about margin erosion at month close. **28% of our project forecasts are off by more than 10%** by the time we close. That's not a rounding error, that's flying blind." *(Baseline for PROC-07 accuracy — see below.)*
- The ROI bar: "I chair the committee. After Swift, the bar is: show me the baseline, show me a credible sourcing plan, and don't tell me it's free or unattended. I would rather fund one thing that works than three things that might."

## Lena Park, Technology Practice Lead — **2026-05-19** — Topics: consumes staffing & status; client-facing pain.

- On staffing (PROC-01): "It is slow and **it feels like a third of my staffing gets redone** — somebody's not actually available, or the skills don't match and we swap them out a week in." *(Conflict B: Lena's ~33% vs. Priya's 22%.)*
- On status reporting (PROC-03): "My PMs lose most of a day a week to status reports. I'd rather they spend that hour with the client than reformatting numbers."
- Posture: a likely early adopter if a tool genuinely speeds staffing or status. Impatient with pilots that don't ship.

## James Carter, Senior Consultant — **2026-05-20** — Topics: time entry (upstream of billing), deliverable production (upstream of QA), shadow tools.

- On time entry (PROC-04): "I do my whole week Friday at 5pm from memory. Of course it's wrong sometimes. Then finance pings me Monday to fix codes." Confirms the burden and the error mechanism behind Greg's 18%.
- On deliverables (PROC-05): "I draft in ChatGPT, then rewrite so it's ours and so I'm not pasting client names into it. Everybody does. QA then catches my formatting and cross-reference misses — which honestly a tool could catch before it ever gets to a senior."
- On admin generally: "Status, time, internal updates — it's easily a day a week that isn't client work. That's the stuff that makes people leave."

---

# ROUND 4 — Clarification (resolve conflicts)

**Participants:** Dana Okafor, Priya Nair, Sofia Reyes, Greg Olsen, Lena Park — **2026-05-26** — Topics: reconcile the three cross-round conflicts; lock baselines.

### Conflict A — Status report effort (PROC-03)
- **Disagreement:** Dana (R1) estimated **30 minutes** per status report. Sofia (R2) measured **median 90 minutes, P90 4 hours** from a 15-report timed sample.
- **Resolution:** Sofia's **sampled measurement wins** — it is evidence, Dana's was a top-of-head estimate. Recorded baseline: **median 90 min, P90 4 h**. Logged that the sponsor materially underestimated this load (a useful finding in itself — the admin drag is ~3x what leadership assumed).

### Conflict B — Staffing rework rate (PROC-01)
- **Disagreement:** Priya (R2) said **22%** of assignments are reworked. Lena (R3) said it "feels like **a third**."
- **Resolution:** The two are measuring different things. **22% are formal "hard" reassignments** evidenced in Polaris (someone is officially pulled and replaced). Lena's higher number also counts **"soft" swaps** — quiet mid-engagement changes never logged as a re-request — estimated at an additional **~13%**. Recorded baseline: **22% hard reassignment (Medium confidence, Polaris-evidenced)**, with a noted **+13% soft-swap** rate (Low confidence, estimated). Both travel forward; do not collapse them.

### Conflict C — Time-entry error rate (PROC-04)
- **Disagreement:** Sofia (R2, approver) estimated **~5%** of timesheets need fixing. Greg (R2, finance) cited a Polaris audit showing **18% of entries corrected**.
- **Resolution:** The **18% Polaris audit wins** (High confidence, system-pulled). Sofia's 5% is manager *perception* — understated because **finance silently corrects many entries** without bouncing them back to the approving manager, so PMs never see the true rate. Recorded baseline: **18% corrected, 8% late past cutoff (High confidence)**.

---

# CONSOLIDATED BASELINE TABLE

This table is the source for `baselines.md`. Every value claim in Phases 5–9 must cite one of these rows.

| Process | Volume | Cycle time (median / P90) | Error / exception | FTE effort | Source confidence |
|---|---|---|---|---|---|
| **PROC-01** Staffing | ~140 staffing actions/mo | 3 d / 11 d | 22% hard reassign (+13% soft, low conf.) | 3.5 FTE | Medium |
| **PROC-02** SOW creation | ~20 SOWs/mo | 6 d / 19 d | 30% legal/finance rework; 12% margin errors | 2.2 FTE | Medium |
| **PROC-03** Status reporting | ~720 reports/mo | 90 min / 4 h (per report) | 15% sent with stale financials | 5.5 FTE | Medium-High |
| **PROC-04** Time entry & approval | ~1,680 timesheets/mo (~34,000 entries) | approval 2 d / 9 d; 62% on-time submit | 18% corrected; 8% late past cutoff | 3.0 FTE | High |
| **PROC-05** Deliverable QA | ~250 deliverables/mo | 1.5 d / 6 d | 20% revised; 5% defects reach client | 2.5 FTE | Medium |
| **PROC-06** Invoicing | ~480 invoices/mo | 5 d / 16 d (close→issue) | 25% adjusted/rebilled; 9% disputed | 3.2 FTE | High |
| **PROC-07** Forecasting / EAC | ~180 EAC updates/mo | 3 h / 1.5 d (per project) | 28% forecasts off >10% at close | 3.0 FTE | Medium |

**Firm-level anchors (for value math):** ~420 billable consultants; blended bill rate **$225/hr**; utilization **68% actual vs. 75% target** (~**$2M revenue per utilization point**, ~$14M for the 7-point gap); DSO **58 days vs. 45 target**; fully-loaded consultant cost ~**$130K/FTE-year**. Total in-scope administrative effort across the seven processes ≈ **23 FTE**.

**Per-step AI-capability and chain-scan notes** (for the process map): PROC-03 (status) is the strongest chain candidate — steps 1–4 (pull Polaris → pull NetSuite → scan Slack → reformat to template) are consecutive data-gathering/formatting steps a system can do, with the human judgment isolated to step 5 (narrative/RAG). PROC-06 (invoicing) has a similar gather-reconcile-draft run, but is politically radioactive (Swift) and GRC-sensitive (commercial data). PROC-05 (QA) splits cleanly into mechanical checks (AI-capable) and substantive judgment (human) — but is gated by the client-confidential / DLP constraint. PROC-01 (staffing) is augmentation-only by sponsor mandate (Priya). PROC-04 (time entry) suits anomaly-flagging + code suggestion. PROC-02 (SOW) is augmentation with a commercial-data / shadow-ChatGPT governance flag. PROC-07 (forecasting) is Data & Analytics (predictive), not automation.
