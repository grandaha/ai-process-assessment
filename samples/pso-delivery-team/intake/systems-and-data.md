# Systems & Data Inventory Pack — Lattice Consulting Group

> **Sample intake document — fictional.** Feeds Phase 3 (Technology & Data Inventory). Compiled from a walkthrough with **Ravi Shah, IT Director**, plus operator confirmations. All systems and figures invented. See `../README.md`.

---

## 1. System inventory

| System | Category | Role in delivery | Owner | Lifecycle | API |
|---|---|---|---|---|---|
| **Polaris PSA** | Professional Services Automation | System of record for projects, resource scheduling, and time entry | IT / Delivery Ops | Stable, core | REST API, well-documented |
| **Salesforce** | CRM | Pipeline, accounts, opportunity → project handoff | Growth org | Stable | Strong API |
| **NetSuite** | ERP / Finance | Billing, invoicing, GL, expenses, revenue recognition | Finance (CFO org) | Stable, tightly governed | API available, finance-gated |
| **SharePoint** | Document repository | Client deliverables, working files | IT | Stable | Graph API; content is unstructured |
| **Confluence** | Knowledge base | Methodology, SOW templates, QA checklists, playbooks | Quality Office | Stable but uneven upkeep | API available |
| **Slack** | Collaboration | Project comms, status threads, approvals chatter | IT | Stable | API available |
| **"Staffing Grid"** | Shadow spreadsheet | RMO's real working view of consultant availability | RMO (Priya's team) | Unmanaged | None — it is an Excel workbook |

**IT team size:** 8 people total. There is no dedicated data engineering or ML function.

## 2. Integration & API map

| Integration | Mechanism | Reliability | Known gap |
|---|---|---|---|
| Polaris → NetSuite (time → billing) | Nightly batch export | Lossy | ~25% of resulting invoices need manual adjustment; mapping of project/task codes to billing items is brittle |
| Salesforce → Polaris (won deal → new project) | **Manual re-keying** at project setup | Manual | No integration; project setup data is re-typed, introducing errors and delay |
| Staffing Grid ↔ Polaris | **None** | — | The authoritative availability view (Grid) and the system of record (Polaris) drift apart constantly |
| Polaris → Slack / Confluence | None automated | — | Status content is assembled by hand from multiple sources |
| NetSuite → reporting | Scheduled extracts | OK | Month-end close only; no intra-month financial truth without manual pulls |

The integration story is the core technical reality: **Polaris holds good operational data, but the connective tissue between Polaris, NetSuite, Salesforce, and the Staffing Grid is manual or batch.** Most of the administrative drag the CDO is worried about lives in these seams.

## 3. Data asset catalog

| Data asset | Location | Quality | Refresh | Sensitivity |
|---|---|---|---|---|
| Time entries / timesheets | Polaris | **High** — system-captured; auditable | Daily | Low (internal ops) |
| Project & resource schedule | Polaris | **Medium-High** — accurate where kept current; availability lags reality | Daily | Low |
| Consultant skills / profiles | Polaris (+ Staffing Grid notes) | **Medium** — skills tags incomplete and stale | Ad hoc | Low |
| Billing / invoices / AR | NetSuite | **High** — finance-controlled | Monthly close | Medium (commercial) |
| Pipeline / opportunity data | Salesforce | **Medium** — opportunity stages applied inconsistently | Continuous | Medium (commercial) |
| Client deliverables | SharePoint | **Low structure** — unstructured docs, inconsistent tagging, no reliable metadata | On save | **High — client-confidential, some under NDA** |
| SOW templates / methodology | Confluence | **Medium** — some templates outdated | Ad hoc | Medium |
| Availability working view | Staffing Grid (Excel) | **Medium, but authoritative in practice** — what RMO actually uses | Manual, several times/week | Low |

## 4. Foundational enabler gaps

These are the prerequisites that are **missing** and would block or constrain AI/automation if not addressed:

- **No identity/SSO model for non-human agents.** Service accounts are ad hoc; there is no clean way to give an AI agent scoped, auditable access.
- **No observability/logging for AI.** Nothing to monitor model behavior, capture prompts/outputs, or audit decisions in production.
- **No MLOps.** No model deployment, versioning, or monitoring pipeline.
- **No DLP / data-loss-prevention for client-confidential content.** This is the binding constraint on anything touching SharePoint deliverables with an external LLM. Until DLP/tenancy isolation exists, deliverable content cannot leave the controlled environment.
- **No data catalog or master data management.** Skills, project, and client reference data are not reconciled across systems.

## 5. IT governance posture

- **Change control:** biweekly Change Advisory Board (CAB). Anything touching production goes through it.
- **Security review:** mandatory for anything that touches client data or external services. This is the gate that will catch deliverable-content use cases.
- **Cloud:** Microsoft/Azure tenant. There is an active interest in **Microsoft Copilot** as a "buy, don't build" path, partly because it lands inside the existing security boundary.
- **LLM usage policy:** in **draft**. Public ChatGPT use by consultants is technically prohibited but unenforced — a policy and enforcement gap, not a sanctioned capability.
- **Speed vs. rigor:** rigor-leaning. Security review and CAB add weeks, not days. This matters for sequencing — enabler work has lead time.

## 6. Build / Buy / Partner posture

- **Strong post-Swift preference for buy/configure over custom build.** Project Swift was a custom RPA build that failed; the organizational antibodies to "we'll build it ourselves" are active.
- Small IT team (8) means **limited internal build capacity** — another argument for SaaS/configure.
- Existing **Microsoft relationship** makes Copilot-style and Azure-native options the path of least resistance through security review.
- Partner appetite exists for vendors who bring a **security and compliance story** that survives the security review gate.

## 7. Shadow IT (surfaced during the walkthrough)

- **The Staffing Grid.** The RMO's Excel workbook is, in practice, the real source of truth for who is available — more current than Polaris. Any staffing solution that ignores it is automating the wrong source.
- **Public ChatGPT for drafting.** Consultants use it for SOW and deliverable first drafts. It is fast and they like it; it is also an uncontrolled path for potentially confidential content to leave the firm. Both a risk to manage and a signal of genuine demand.
- **Personal tracking spreadsheets.** Several PMs keep their own project financial trackers because they do not trust the intra-month numbers, duplicating what Polaris/NetSuite should provide.
