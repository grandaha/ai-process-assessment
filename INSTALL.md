# Install Guide — AI & Automation Use Case Identification Methodology Plugin

Pick the environment that matches you:

- **[Option A — Claude Code](#option-a--claude-code)** (plugin; full feature set incl. the math engine)
- **[Option B — Claude Cowork](#option-b--claude-cowork)** (plugin; desktop agentic work)
- **[Option C — Claude.ai Projects](#option-c--claudeai-projects)** (no install; paste system prompt + upload knowledge)
- **[Option D — Per-engagement CLAUDE.md](#option-d--per-engagement-claudemd-lightest)** (lightest; any Claude interface)

Options A and B install the same plugin and get the deterministic math engine (code execution). Options C and D run the methodology from prompts/knowledge; numeric figures render "pending engine" without a code-execution environment.

---

## Option A — Claude Code

Requires Claude Code 2.0.13 or later.

### 1. Add the marketplace and install (recommended)

In a Claude Code session, type:

```
/plugin marketplace add grandaha/ai-process-assessment
/plugin install ai-process-assessment@onesteplabs
```

`/plugin marketplace add` reads `.claude-plugin/marketplace.json` from the GitHub repo; `/plugin install` installs the plugin (the `@onesteplabs` suffix is the marketplace name). Refresh later with `/plugin marketplace update onesteplabs`.

> The `/plugin` slash commands run in the Claude Code CLI (`claude` in a terminal). In the VSCode extension, use the manual registration below.

### 2. Manual registration (VSCode extension, or local/unpublished use)

If you cloned the repo and want to run it locally without the marketplace, make the session-start hook executable:

```bash
chmod +x hooks/session-start.sh
```

Then edit `~/.claude/plugins/installed_plugins.json` and add this entry inside the `"plugins"` object:

```json
"ai-process-assessment@local": [
  {
    "scope": "local",
    "installPath": "/absolute/path/to/ai-process-assessment",
    "version": "2.10.0",
    "installedAt": "2026-05-08T21:44:01.000Z",
    "lastUpdated": "2026-05-08T21:44:01.000Z",
    "projectPath": "/absolute/path/to/your/vault"
  }
]
```

Replace both paths: `installPath` points to this plugin folder; `projectPath` is the working folder where the plugin should activate.

### 3. Set up the math engine

The plugin computes every number with a deterministic Python engine (see [Python math engine](#python-math-engine-required-for-any-shipped-number) below). Run `pip install -r requirements.txt` once.

### 4. Restart, verify, and start

Start a new session — the session-start hook injects the keystone. Type anything; the model should acknowledge it is operating inside the methodology and ask for an engagement prompt. If not, check that `hooks/hooks.json` is present, `hooks/session-start.sh` is executable, and `skills/using-methodology/SKILL.md` exists. Then say **"scope this engagement"** to begin Phase 1, or **"run the sample engagement"** for the bundled demo (see [Try the sample](#try-the-bundled-sample-engagement)).

---

## Option B — Claude Cowork

Claude Cowork (the desktop agentic mode) uses the **same plugin format** as Claude Code. Requires the latest Claude desktop app (macOS or Windows) and a paid plan (Pro, Max, Team, or Enterprise).

### 1. Open the Plugins panel

In the Claude desktop app, switch to the **Cowork** tab, then open **Customize → Plugins**.

### 2. Add this repo as a marketplace

Under **Personal plugins**, click **+ → Add marketplace → from a GitHub repository**, and enter:

```
grandaha/ai-process-assessment
```

Then click **Install** on the `ai-process-assessment` plugin. (Alternatively, **upload a custom plugin file** if you have a local build, e.g. the release zip.) Plugins you add yourself are saved locally to your computer.

### 3. Use it

Type `/` or click the **+** button in a Cowork (or chat) session to see the methodology's skills. Start with **"scope this engagement"**, or **"run the sample engagement"** for the demo. Because Cowork can execute code and touch local files, the deterministic math engine and the `financial-model.xlsx` workbook work fully here.

---

## Option C — Claude.ai Projects

No install required. Works in any Claude.ai Project.

### 1. Create a Claude.ai Project

claude.ai → Projects → New Project. Name it (e.g., "AI Use Case Assessment").

### 2. Paste the system prompt

Open `system-prompt.md`, copy its full contents (including the `<EXTREMELY_IMPORTANT>` wrapper), and paste into Project → Settings → System Prompt. Save.

### 3. Upload knowledge files

**Skills** (upload each `SKILL.md`):
- `skills/scoping-engagement/SKILL.md`
- `skills/mapping-context/SKILL.md`
- `skills/inventorying-tech-data/SKILL.md`
- `skills/discovering-processes/SKILL.md`
- `skills/identifying-opportunities/SKILL.md`
- `skills/scoring-opportunities/SKILL.md`
- `skills/prioritizing-roadmap/SKILL.md`
- `skills/packaging-usecases/SKILL.md`
- `skills/collecting-cost-actuals/SKILL.md`
- `skills/building-business-case/SKILL.md`
- `skills/building-executive-summary/SKILL.md`
- `skills/building-deliverable/SKILL.md`
- `skills/governance-risk-gate/SKILL.md`
- `skills/deliverable-gate/SKILL.md`
- `skills/running-sample-engagement/SKILL.md`

**Agents** (upload all):
- `agents/process-mapper.md`
- `agents/opportunity-typer.md`
- `agents/opportunity-scorer.md`
- `agents/opportunity-reviewer.md`
- `agents/grc-reviewer.md`
- `agents/usecase-brief-drafter.md`
- `agents/business-case-analyst.md`
- `agents/executive-summary-drafter.md`
- `agents/executive-summary-reviewer.md`
- `agents/section-renderer-executive.md`
- `agents/section-renderer-problem.md`
- `agents/section-renderer-portfolio.md`
- `agents/section-renderer-roadmap.md`
- `agents/section-renderer-evidence.md`

**Engagement context** (optional but recommended): a filled-in `CLAUDE.md`, plus intake documents (org charts, system inventories, process lists, prior assessments).

> **Numbers:** Claude.ai Projects cannot run the Python engine unless the analysis/code tool is available. Without it, the methodology runs but numeric figures render "pending engine." Enable the analysis tool, or finalize numbers in Claude Code / Cowork.

### 4. Start a conversation

Every conversation in the Project inherits the keystone via the system prompt. Say **"scope this engagement"** to begin. For a new engagement, start a new conversation and upload a fresh `CLAUDE.md`.

---

## Option D — Per-engagement CLAUDE.md (lightest)

No plugin system or Project required. Works with any Claude interface.

1. Create an engagement folder `<client-name>/` at the project root.
2. Fill in `CLAUDE.md` (Client/Initiative, Engagement folder, Sponsor, Decision-maker, Timeline) and document any deliberate overrides in the Overrides table.
3. Paste the full contents of `skills/using-methodology/SKILL.md` at the top of your system prompt, wrapped in `<EXTREMELY_IMPORTANT>` tags, then paste your filled-in `CLAUDE.md` below it.
4. At the start of each phase, paste the relevant `SKILL.md` into context. The skill chain references tell you which one comes next.

---

## Try the bundled sample engagement

Before a live engagement, run the included demo to see all eleven phases and both gates end-to-end on fictional data. Say **"run the sample engagement"** — the model invokes `ai-process-assessment:running-sample-engagement`, which feeds the intake files in `samples/pso-delivery-team/intake/` through the methodology and produces a complete run under `sample-pso-delivery/`, ending in `deliverable.html`. See `samples/pso-delivery-team/README.md`.

In Claude.ai Projects (Option C) or the lightweight setup (Option D), attach the four `samples/pso-delivery-team/intake/` files to the conversation (or keep them in Project knowledge) so the run can read them at Phases 1–4.

---

## Engagement Folder Convention

Every engagement produces files in sequence under `<name>/` at the project root:

| Phase | Output |
|---|---|
| 1 — Scoping | `scope.md` |
| 2 — Context Mapping | `context.md` |
| 3 — Tech & Data Inventory | `tech-inventory.md` |
| 4 — Process Discovery | `processes/` (`_index.md` + `PROC-NNN.md` per process) |
| 5 — Opportunity Identification | `opportunities/` (`_index.md` + `OPP-NNN.md` per opportunity) |
| Gate A — GRC Review | `grc/` (`_index.md` + `OPP-NNN.md` per flagged opportunity; only when Gate A ran) |
| 6 — Opportunity Scoring | `scores/` (`_index.md` + `OPP-NNN.md` per opportunity) |
| 7 — Prioritization & Roadmap | `roadmap.md` |
| 8 — Use Case Packaging | `usecase-briefs/` (`_index.md` + `UC-NNN.md` per opportunity) |
| 8.5 — Cost Actuals | `cost-actuals.md` |
| 9 — Business Case | `business-case.md`, `model/` (inputs + `results.json`), `financial-model.xlsx` |
| 10 — Executive Summary | `executive-summary.md` |
| 11 — Deliverable | `deliverable.html` |
| Running log | `evidence-log.md` |

Each phase skill checks that its predecessor file exists before producing output. If a file is missing, the skill halts and tells you what is needed.

---

## Subagent Dispatch

Subagents fire automatically at quality gates — no setup required; the phase skills dispatch them. Examples:

| Subagent | When it fires | What it checks |
|---|---|---|
| `opportunity-reviewer` | After scoring, after roadmap, after packaging | Evidence sourcing, type consistency, brief completeness, Build/Buy/Partner presence |
| `grc-reviewer` | Inside the GRC gate, for each flagged opportunity | Regulatory exposure, model risk, auditability, failure consequence |

Subagents operate without shared session context — they receive only the document under review. This is intentional.

---

## Python math engine (required for any shipped number)

The methodology computes every number with a deterministic Python engine (`engine/`). Set it up once:

```bash
pip install -r requirements.txt   # openpyxl, pytest, formulas
python -m pytest engine/tests -q  # verify the golden-number suite passes
```

Each numeric phase writes structured inputs to the engagement's `model/*.json`, then runs `python -m engine.run <engagement-folder>/` to produce `model/results.json` and `financial-model.xlsx`. Without a code-execution environment the methodology still runs, but figures render "pending engine."

---

## Running the tests

The plugin ships a static test suite (Layer 1) that checks the methodology
graph and guards against known regressions. It is LLM-free and runs in seconds.

```bash
make install   # pip install -r requirements.txt
make test      # pytest -q
```

Or directly: `pytest` from the repo root. The suite parses the keystone Phase
Map in `skills/using-methodology/SKILL.md` and asserts every skill, agent,
chain link, and output file conforms to it — plus the engine's golden-number suite.

### Pre-push test gate (optional, recommended)

A tracked git hook (`.githooks/pre-push`) runs the suite before every push and
aborts the push if it fails — a free stand-in for branch protection. Enable it
once per clone:

```bash
git config core.hooksPath .githooks
```

It uses `.venv/bin/python` if present, skips gracefully if pytest isn't
installed, and can be bypassed for a one-off with `git push --no-verify`.

---

## Troubleshooting

**Model skips a phase or ignores the gate condition**
Check that the keystone (`using-methodology/SKILL.md`) was loaded. In Claude Code / Cowork, confirm the session-start hook ran. In Claude.ai Projects, confirm the system prompt contains the full `<EXTREMELY_IMPORTANT>` block.

**"I don't see the skill" in Claude Code**
Run `/plugin list` and confirm `ai-process-assessment` appears. If you added the marketplace, try `/plugin marketplace update onesteplabs` then reinstall.

**Plugin doesn't appear in Cowork**
Confirm you're on the latest desktop app and a paid plan, and that the marketplace was added under **Customize → Plugins → Personal plugins**. Type `/` to list available skills.

**Hook does not fire on session start**
Confirm `async: false` in `hooks/hooks.json` — async hooks can miss the first user turn.

**The model produces output before the predecessor file exists**
Re-invoke the correct phase skill directly, or add a note to the engagement `CLAUDE.md`. The gate condition is enforced by the model reading the skill — if the skill wasn't invoked, the gate didn't run.

**GRC gate fires on an opportunity that doesn't need it**
Add a `CLAUDE.md` override entry with rationale. The deliverable gate audits the override before external sharing.
