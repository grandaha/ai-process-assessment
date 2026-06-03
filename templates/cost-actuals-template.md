# Cost Actuals — [Engagement Name]

**Engagement:** [Client name — process area]
**Prepared by:** [Name / role]
**Date prepared:** [YYYY-MM-DD]
**Confidence notes:** [Any caveats on the figures below — e.g., "rates are FY2026 loaded actuals from Finance; vendor quotes valid through 2026-09-30"]

---

> **How to use this file**
>
> Copy this file to `docs/engagements/<engagement>/cost-actuals.md` before Phase 9 runs.
> Fill in the fields you have. Leave blank any field where you don't have actuals — Phase 9 will use AACE Class 5 benchmark rates for those lines and flag them.
> Even partial data tightens the estimate. Labor rates alone (Section 1) eliminate the largest single source of ROM variance.

---

## 1. Internal Labor Rates (Fully Burdened $/hr)

Fully burdened = salary + benefits + overhead + margin. Source from Finance or HR.

| Role | Rate ($/hr) | Applies to initiatives | Source / notes |
|---|---|---|---|
| IT admin / systems configuration | | | |
| Enterprise AI / ML engineering team | | | |
| Domain specialist — [specify role, e.g. recruiter, ops analyst] | | | |
| Domain specialist — [specify role] | | | |
| Project / program management | | | |
| Change management / training facilitation | | | |

Add rows as needed for roles specific to this engagement.

---

---

## 2. Initiative Implementation Hours

Hours required to build each Wave 1 initiative. Get from the team lead who will own the build work.

| Initiative | Labor type | Hours estimate | Source / notes |
|---|---|---|---|
| [OPP-NNN — Title] | [e.g., Enterprise AI team — Azure Cognitive Services configuration] | | |

Add one row per Wave 1 initiative. Labor type comes from the brief's Resolution field — who does the work. If the initiative is Buy and the vendor handles implementation with no internal build work, enter 0 or N/A and note "vendor-implemented."

---

## 3. Vendor Quotes Received

Add a row for each Buy or Partner initiative where a formal or informal quote has been received.

| Initiative (OPP-NNN) | Vendor / product | One-time ($) | Annual ($) | Quote date | Quote valid until | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 4. IT Integration Estimates

IT team estimates for enabler work (integration, infrastructure, security review).

| Enabler | Work item | IT labor (hrs) | One-time ($) | Annual ($) | Estimate source | Notes |
|---|---|---|---|---|---|---|
| E1 | | | | | | |
| E2 | | | | | | |
| E3 | | | | | | |

Add rows for any additional enablers from roadmap.md.

---

## 5. Override Notes

Any actual figures that don't fit the tables above — e.g., fixed-fee contractor agreements, pre-negotiated platform credits, known sunk costs.

[Free text — each item on its own line with: what it is, dollar amount, date, and source]

---

## What changes when this file is present

When `cost-actuals.md` exists in the engagement folder, Phase 9 does the following:

- **Labor cost rows** where a rate is supplied: uses the actual rate instead of the benchmark band. Tightens the ROM from ±50% toward ±20–30% on those rows.
- **Initiative hours rows** where hours are supplied: used directly by the business-case-analyst to compute implementation labor cost (hours × rate). Rows marked PENDING or left blank: that cost category shows as PENDING in the business case — the initiative's ROM range will not be calculated until confirmed.
- **Vendor quote rows** where a quote is supplied: replaces the "Requires vendor quote — benchmark-based" flag with the actual figure. Marks those rows as confirmed rather than estimated.
- **IT integration rows** where an estimate is supplied: replaces the hours-derived estimate with the IT-provided figure.
- **Rows with no actuals supplied:** unchanged — benchmark rates and mandatory flags still apply.

The ROM accuracy label remains AACE Class 5 (±50%) for the initiative total unless all major cost categories have actuals. The "What Would Tighten This Estimate" section in business-case.md will list only the fields that remain benchmark-based.
