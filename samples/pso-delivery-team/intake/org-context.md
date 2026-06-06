# Organizational Context Pack — Lattice Consulting Group, Delivery Org

> **Sample intake document — fictional.** Feeds Phase 2 (Context Mapping). Prepared by the CDO's chief of staff as a briefing for the assessment team. All details invented. See `../README.md`.

---

## 1. The firm and how it makes money

**Lattice Consulting Group** is a mid-size technology and management consulting firm. ~$240M annual revenue, ~600 employees, of whom ~420 are billable consultants. Three practices:

- **Technology** (~190 consultants) — systems implementation, data, cloud
- **Strategy & Operations** (~140 consultants) — operating-model and process work
- **Change & Adoption** (~90 consultants) — org change, training, adoption

Revenue is roughly **65% time-and-materials, 35% fixed-fee**. Blended realized bill rate is about **$225/hour**. The firm makes money on the spread between bill rate and fully-loaded consultant cost, multiplied by **utilization** (billable hours ÷ available hours).

**Where the margin pressure lives:** utilization. Target is 75%; the org is running at **68%** this year. Every point of utilization across 420 consultants is material — roughly **$2M of annual revenue per point** at current rates (~420 consultants × ~2,080 available hrs × 1% × $225). The 7-point gap is worth on the order of **$14M** in annual revenue and is the single biggest drag on delivery margin. Secondary leaks: time that never gets billed because it is entered late or miscoded (revenue leakage), and slow invoicing that pushes **DSO to ~58 days** against a 45-day target, tying up cash.

## 2. Strategic priorities (FY27 planning cycle)

In priority order, as set by the executive team for FY27:

1. **Lift utilization from 68% to 73%.** The board has made this the headline delivery metric.
2. **Reduce DSO from 58 to 45 days.** CFO-owned; driven mostly by invoicing speed and rebill rate.
3. **Improve consultant retention.** Voluntary attrition is ~17%. Exit interviews repeatedly cite "administrative burden" and "too much time on non-billable busywork" — status reports, time entry, internal reporting.
4. **Grow the fixed-fee mix** beyond 35%, which requires tighter scoping and forecasting so fixed-fee work does not erode margin.

The throughline Dana (CDO) is pushing: **take administrative load off consultants and project managers** — that helps utilization (more billable hours), retention (less busywork), and cash (faster, cleaner invoicing) at the same time.

## 3. Org structure relevant to scope

The delivery org reports to **Dana Okafor, Chief Delivery Officer.** Under Dana:

- **Practices** (Technology / Strategy & Ops / Change), each led by a Practice Lead. Practice leads own consultant careers and client relationships. (Technology practice lead: **Lena Park.**)
- **Resource Management Office (RMO)** — central function that staffs consultants to projects. Led by **Priya Nair.** This is a shared service across practices; the seam between RMO ("who is available") and practice leads ("who I want on my project") is a frequent friction point.
- **Project Finance** — billing, invoicing, project-level financial control. Billing Manager: **Greg Olsen.** Dotted line to the CFO org.
- **Quality Office** — sets deliverable standards and runs QA gates. Led by **Aisha Khan.**
- **Project managers** sit inside practices but operate firm-wide methods. Senior PM **Sofia Reyes** is a representative operator for status and forecasting.

Key seams (where ownership is unclear or contested):
- RMO vs. practice leads on staffing authority
- Project Finance vs. delivery PMs on who owns forecast accuracy
- Quality Office vs. engagement teams on how much QA is "enough"

## 4. AI / automation maturity

**Honest assessment: low-to-moderate.** Two data points the team should weigh:

- **Prior win (modest):** In 2025 the firm built a proposal-analytics dashboard on top of Salesforce that gave practice leads visibility into win rates by offering and pursuit team. It is used and liked. It was analytics, not automation — no process was changed, just measured.
- **Prior failure (consequential):** In 2024 the firm ran **"Project Swift,"** a custom-built RPA program aimed at automating invoice generation. It overran its budget by roughly 2x, never reached reliable production, and was quietly shelved. The fallout: the CFO, Marcus Bell, became deeply skeptical of automation business cases, and IT became gun-shy about custom builds. **Any automation recommendation that pattern-matches to Swift — especially around invoicing — starts with a credibility deficit.**

There is no MLOps capability, no model monitoring, and no internal AI engineering team. There **is** shadow adoption: a meaningful number of consultants quietly use public ChatGPT to draft SOWs and deliverables. This is technically against the (draft) usage policy and is a live data-governance concern, not an endorsed capability.

## 5. Funding model

- Transformation is **opex-funded** out of a delivery transformation pool. Dana controls roughly **$1.5M discretionary + committee-gated** for FY27.
- Anything above that, or anything requiring capital/custom build, goes to the **Investment Committee**, which **Marcus Bell (CFO) chairs.** The committee meets quarterly; the FY27 cycle decision point is **October 2026.**
- **ROI ownership:** Dana owns the delivery transformation P&L impact. This means whoever sponsors an initiative also owns defending its realized benefit a year later — which makes Dana conservative about overclaiming.
- Preference is strongly toward **buy/configure over build** post-Swift. SaaS with a real security story is fundable; "we'll build a custom agent" is a hard sell.

## 6. Risk posture

**Moderately conservative, with one sharp edge: client confidentiality.** Lattice's deliverables contain client-confidential material, some under NDA. The firm's reputation depends on never leaking it. Practical implications:

- Anything that would send client deliverable content to an external LLM **without** data-protection controls (DLP, tenancy isolation, redaction) is effectively blocked until those controls exist.
- Internal operational data (time, utilization, project financials) is far less sensitive and can move more freely.
- The firm is in a regulated-adjacent posture: not itself heavily regulated, but it serves regulated clients who impose security requirements through contracts.
- Recent incident memory: no data breach, but Project Swift left a "we got burned by overpromising" scar that functions like a risk event.

## 7. Political landscape

| Stakeholder | Role | Posture | Why it matters |
|---|---|---|---|
| **Dana Okafor** | CDO (sponsor / decision-maker) | Aligned, but conservative | Owns the recommendation and its realized ROI; will not overclaim |
| **Marcus Bell** | CFO (committee chair) | Skeptical | Post-Swift; gates funding; demands hard numbers and a credible sourcing story |
| **Priya Nair** | RMO Director | Protective / can veto in practice | Sees staffing judgment as her team's craft; will resist anything framed as "algorithm decides staffing" |
| **Aisha Khan** | Quality Office Lead | Wary | Concerned AI QA undermines deliverable standards and firm reputation |
| **Lena Park** | Technology Practice Lead | Pragmatic, mildly impatient | Wants faster staffing and less PM admin; a likely early adopter if the tool actually helps |
| **Consultants (e.g., James Carter)** | Operators | Frustrated with admin, quietly pro-tool | Already using shadow ChatGPT; want the busywork gone |

Coalition reality: Dana + practice leads + consultants broadly want the admin burden reduced. The friction points are Marcus (cost/ROI credibility), Priya (staffing autonomy), and Aisha (quality standards). An initiative that wins needs to either avoid those three pressure points or address them head-on with framing and controls.
