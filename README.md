# AI & Automation Use Case Identification Methodology

An evidence-gated, structured methodology for identifying, scoring, and sequencing AI and automation opportunities in a client or internal engagement. It ships as a Claude plugin (skills + agents + a deterministic math engine) that runs in **Claude Code**, **Claude Cowork**, or **Claude.ai Projects**.

## Purpose

This methodology imposes discipline on use case identification work. It prevents the most common failures: premature solutions, value claims without baselines, unlabeled opportunity types, and roadmaps assembled from intuition rather than evidence. It is designed for consulting practitioners and operational-excellence teams running AI/automation discovery engagements.

The work moves through **11 phases and 2 gates**, each with a gate condition that must be satisfied before the next phase can begin. Every value claim must trace to a sourced baseline, and every number is computed by a deterministic engine — never asserted in prose.

---

## Install

The plugin works in three environments. Full step-by-step instructions for each are in **[INSTALL.md](INSTALL.md)**; the short version:

| Environment | Quick start |
|---|---|
| **Claude Code** | `/plugin marketplace add grandaha/ai-process-assessment` then `/plugin install ai-process-assessment@onesteplabs` |
| **Claude Cowork** | Cowork → **Customize → Plugins → Personal plugins → + → Add marketplace** → add the GitHub repo `grandaha/ai-process-assessment`, then install the plugin |
| **Claude.ai Projects** | Paste `system-prompt.md` into the Project system prompt and upload the `skills/` and `agents/` files as Project knowledge |

After install, start an engagement by saying **"scope this engagement"**, or **"run the sample engagement"** to watch the full flow on bundled fictional data.

> **Code execution** (Claude Code / Cowork) is required for the deterministic math engine to compute and ship numbers. In Claude.ai Projects without the analysis tool, the methodology still runs but numeric figures render "pending engine."

---

## Deterministic math engine

The methodology performs **no arithmetic in prose**. Every number is either a directly-sourced input recorded in the engagement's `model/*.json` files, or a value computed by the deterministic Python engine in `engine/` (`python -m engine.run <engagement-folder>/`) and read back from `model/results.json`. The engine also emits `financial-model.xlsx`, an auditable workbook with live formulas that opens and recomputes in Excel, Google Sheets, and Apple Numbers. `model/*.json` is the single source of truth; the deliverable-gate enforces that every figure in the markdown deliverables equals its `results.json` value. A missing input renders as **PENDING**, never a fabricated number. See [INSTALL.md](INSTALL.md) for engine setup.

---

## The methodology at a glance

| Phase | Skill | Output |
|---|---|---|
| 1 — Scoping | `scoping-engagement` | `scope.md` |
| 2 — Context mapping | `mapping-context` | `context.md` |
| 3 — Tech & data inventory | `inventorying-tech-data` | `tech-inventory.md` |
| 4 — Process discovery | `discovering-processes` | `process-map.md`, `baselines.md` |
| 5 — Opportunity identification | `identifying-opportunities` | `opportunities/` |
| 6 — Scoring | `scoring-opportunities` | `scores/` |
| 7 — Roadmap | `prioritizing-roadmap` | `roadmap.md` |
| 8 — Use case packaging | `packaging-usecases` | `usecase-briefs/` |
| 8.5 — Cost actuals | `collecting-cost-actuals` | `cost-actuals.md` |
| 9 — Business case | `building-business-case` | `business-case.md` |
| 10 — Executive summary | `building-executive-summary` | `executive-summary.md` |
| 11 — Deliverable | `building-deliverable` | `deliverable.html` |
| Gate A — GRC | `governance-risk-gate` | `grc/` |
| Gate B — Deliverable gate | `deliverable-gate` | clearance in `evidence-log.md` |

The keystone (`using-methodology`) holds the authoritative Phase Map, opportunity taxonomy, and the Master Rationalization Table; it is loaded into every session. `running-sample-engagement` drives the bundled Lattice Consulting demo end-to-end.

---

## Repository layout

```
ai-process-assessment/
├── .claude-plugin/
│   ├── plugin.json                 ← plugin manifest (name, version)
│   └── marketplace.json            ← marketplace manifest (one-add install)
├── skills/                         ← one SKILL.md per phase + gates + keystone
│   ├── using-methodology/          ← KEYSTONE (auto-loaded; Phase Map, taxonomy, rules)
│   ├── scoping-engagement/         ← Phase 1
│   ├── mapping-context/            ← Phase 2
│   ├── inventorying-tech-data/     ← Phase 3
│   ├── discovering-processes/      ← Phase 4 (+ Baseline, Value & Challenge gate)
│   ├── identifying-opportunities/  ← Phase 5
│   ├── scoring-opportunities/      ← Phase 6
│   ├── prioritizing-roadmap/       ← Phase 7
│   ├── packaging-usecases/         ← Phase 8
│   ├── collecting-cost-actuals/    ← Phase 8.5
│   ├── building-business-case/     ← Phase 9
│   ├── building-executive-summary/ ← Phase 10
│   ├── building-deliverable/       ← Phase 11
│   ├── governance-risk-gate/       ← Gate A (GRC)
│   ├── deliverable-gate/           ← Gate B (final integrity, incl. determinism check)
│   └── running-sample-engagement/  ← bundled end-to-end demo
├── agents/                         ← subagents dispatched by the phase skills
│   ├── process-mapper.md             ← Phase 4: one interview round → process-map/baselines
│   ├── opportunity-typer.md          ← Phase 5: types opportunities (chain scan + taxonomy)
│   ├── opportunity-scorer.md         ← Phase 6: per-OPP 6-dimension scorer
│   ├── opportunity-reviewer.md       ← structured-skeptic reviewer (scores, roadmap, briefs)
│   ├── grc-reviewer.md               ← Gate A: independent risk/legal/compliance reviewer
│   ├── usecase-brief-drafter.md      ← Phase 8: per-UC SCRA brief
│   ├── business-case-analyst.md      ← Phase 9: per-initiative cost + value blocks
│   ├── executive-summary-drafter.md  ← Phase 10: single-pass exec-summary writer
│   ├── executive-summary-reviewer.md ← Phase 10: independent exec-summary reviewer
│   └── section-renderer-*.md         ← Phase 11: parallel HTML section renderers
│       (executive · problem · portfolio · roadmap · evidence)
├── engine/                         ← deterministic math engine (model, compute, workbook, run + tests)
├── templates/                      ← reusable templates (e.g. cost-actuals worksheet)
├── samples/                        ← bundled Lattice Consulting sample engagement (intake + README)
├── hooks/                          ← session-start hooks (auto-load the keystone)
├── system-prompt.md                ← Claude.ai Projects: paste into the Project system prompt
├── CLAUDE.md                       ← per-engagement override template
├── INSTALL.md                      ← full install guide (Claude Code / Cowork / Claude.ai)
├── CHANGELOG.md                    ← version history (Keep a Changelog)
├── improvement-log.md              ← cross-engagement rationalization escape log
├── requirements.txt                ← engine deps (openpyxl, formulas, pytest, pyyaml)
└── pytest.ini                      ← static test suite config
```

---

## Running the tests

The plugin ships a static test suite (LLM-free, runs in seconds) that parses the keystone Phase Map and guards against known regressions, plus the engine's golden-number suite.

```bash
pip install -r requirements.txt
pytest -q
```

A tracked pre-push hook (`.githooks/pre-push`) runs the suite before every push — enable it once per clone with `git config core.hooksPath .githooks`. See [INSTALL.md](INSTALL.md) for details.

---

## Updating the methodology

When a rationalization is encountered that the methodology did not catch, follow the RED-GREEN-REFACTOR loop:

1. **RED** — prepend a new entry to [`improvement-log.md`](improvement-log.md) at the repo root: what shortcut was taken, what it produced, why it wasn't caught, and which row you're adding. Write the entry before the table row.
2. **GREEN** — add a row to the rationalization table of the relevant `SKILL.md` naming the shortcut and the correct reframe. If the escape is general, also add it to the master table in `using-methodology/SKILL.md`.
3. **REFACTOR** — if the escape is systematic, tighten the gate or checklist step that should have caught it, and update the keystone (`using-methodology/SKILL.md`) and `system-prompt.md` if a keystone rule changed (run `pytest` — the mirror guard enforces the sync).

The rationalization tables are the durability mechanism: each real engagement that surfaces a new shortcut makes the methodology more resilient.

---

## License

MIT © Dave Raffaele

<!-- auto-review smoke test: markdown guard (remove me) -->
