# Install Guide — AI & Automation Use Case Identification Methodology Plugin

Three deployment options. Pick the one that matches your environment.

---

## Option A — Claude Code Plugin (Full)

Requires Claude Code 2.0.13 or later.

> **Note:** The `/plugin install` slash command only works in the Claude Code CLI (`claude` in terminal). It is not available in the VSCode extension. If you are using the VSCode extension, follow the manual registration step below instead.

### 1. Make the session-start hook executable

```bash
chmod +x hooks/session-start.sh
```

### 2a. Install via CLI (Claude Code terminal only)

Open a terminal, `cd` to the project root, run `claude` to start a session, then type:

```
/plugin install ai-process-assessment@claude-plugins-official
```

If the plugin is not yet published to the marketplace, use the manual registration path below.

### 2b. Manual registration (VSCode extension or unpublished plugin)

Edit `~/.claude/plugins/installed_plugins.json` and add the following entry inside the `"plugins"` object:

```json
"ai-process-assessment@local": [
  {
    "scope": "local",
    "installPath": "/absolute/path/to/ai-usecase-methodology",
    "version": "1.8.0",
    "installedAt": "2026-05-08T21:44:01.000Z",
    "lastUpdated": "2026-05-08T21:44:01.000Z",
    "projectPath": "/absolute/path/to/your/vault"
  }
]
```

Replace both paths with the actual absolute paths on your machine. `installPath` points to this plugin folder; `projectPath` is the vault root where the plugin should activate.

### 3. Restart Claude Code

Start a new session. The session-start hook fires automatically and injects the keystone skill into context.

### 4. Verify

Type anything in a new session. The model should acknowledge it is operating inside the methodology and ask for an engagement prompt. If it does not, check:

- `hooks/hooks.json` is present
- `hooks/session-start.sh` is executable
- `skills/using-methodology/SKILL.md` exists

### 5. Start an engagement

Say: **"scope this engagement"** — the model will invoke `ai-process-assessment:scoping-engagement` and begin Phase 1.

---

## Option B — Claude.ai Projects (Zero Infrastructure)

No Claude Code required. Works in any Claude.ai Project.

### 1. Create a Claude.ai Project

Go to claude.ai → Projects → New Project. Give it a name (e.g., "AI Use Case Assessment").

### 2. Paste the system prompt

1. Open `system-prompt.md` from this folder
2. Copy the full contents (everything, including the `<EXTREMELY_IMPORTANT>` wrapper)
3. In your Project → Settings → System Prompt, paste the contents
4. Save

### 3. Upload knowledge files

Upload the following as Project knowledge files:

**Skills** (upload each SKILL.md):
- `skills/scoping-engagement/SKILL.md`
- `skills/mapping-context/SKILL.md`
- `skills/inventorying-tech-data/SKILL.md`
- `skills/discovering-processes/SKILL.md`
- `skills/identifying-opportunities/SKILL.md`
- `skills/scoring-opportunities/SKILL.md`
- `skills/prioritizing-roadmap/SKILL.md`
- `skills/packaging-usecases/SKILL.md`
- `skills/building-business-case/SKILL.md`
- `skills/building-executive-summary/SKILL.md`
- `skills/building-deliverable/SKILL.md`
- `skills/governance-risk-gate/SKILL.md`
- `skills/deliverable-gate/SKILL.md`

**Agents** (upload all):
- `agents/opportunity-reviewer.md`
- `agents/grc-reviewer.md`
- `agents/opportunity-scorer.md`
- `agents/usecase-brief-drafter.md`
- `agents/executive-summary-drafter.md`
- `agents/section-renderer-executive.md`
- `agents/section-renderer-problem.md`
- `agents/section-renderer-portfolio.md`
- `agents/section-renderer-roadmap.md`
- `agents/section-renderer-evidence.md`

**Engagement context** (optional but recommended):
- A filled-in `CLAUDE.md` for the specific engagement
- Intake documents: org charts, system inventories, process lists, prior assessments

### 4. Start a new conversation

Every conversation in the Project inherits the keystone automatically.

Say: **"scope this engagement"** to begin Phase 1.

### Updating for a new engagement

The system prompt and skill files are static. For each new engagement:
1. Create a new conversation in the Project
2. Upload a freshly filled-in `CLAUDE.md` as a knowledge file (or add it to the system prompt's override section)
3. Optionally upload engagement-specific intake documents

---

## Option C — Per-Engagement CLAUDE.md (Lightest)

No plugin system or Project required. Works with any Claude interface.

### 1. Create an engagement folder

```
docs/engagements/<client-name>/
```

### 2. Fill in CLAUDE.md

Open `CLAUDE.md` and fill in the engagement fields:

```
Client / Initiative: <name>
Engagement folder: docs/engagements/<name>/
Sponsor: <name, role>
Decision-maker: <name, role>
Timeline: <dates>
```

Document any deliberate methodology overrides in the Overrides table.

### 3. Paste the keystone at the top of your system prompt

Copy the full contents of `skills/using-methodology/SKILL.md` and paste it at the top of your system prompt, wrapped in `<EXTREMELY_IMPORTANT>` tags:

```
<EXTREMELY_IMPORTANT>
[paste SKILL.md contents here]
</EXTREMELY_IMPORTANT>
```

Then paste your filled-in `CLAUDE.md` below it.

### 4. Reference skills manually

At the start of each phase, paste the relevant `SKILL.md` into your context (or into the system prompt for the session). The skill chain references tell you which one comes next.

---

## Engagement Folder Convention

Every engagement produces files in sequence under `docs/engagements/<name>/`:

| Phase | File created |
|---|---|
| 1 — Scoping | `scope.md` |
| 2 — Context Mapping | `context.md` |
| 3 — Tech & Data Inventory | `tech-inventory.md` |
| 4 — Process Discovery | `process-map.md`, `baselines.md` |
| 5 — Opportunity Identification | `opportunities.md` |
| 6 — Opportunity Scoring | `scored-opportunities.md` |
| 7 — Prioritization & Roadmap | `roadmap.md` |
| 8 — Use Case Packaging | `usecase-briefs.md` |
| Running log | `evidence-log.md` |

Each phase skill checks that its predecessor file exists before producing any output. If a file is missing, the skill halts and tells you what is needed.

---

## Subagent Dispatch

Two subagents fire automatically at quality gates — no setup required. The phase skills dispatch them.

| Subagent | When it fires | What it checks |
|---|---|---|
| `opportunity-reviewer` | After scoring, after roadmap, after packaging | Evidence sourcing, type consistency, brief completeness, Build/Buy/Partner presence |
| `grc-reviewer` | Inside the GRC gate, for each flagged opportunity | Regulatory exposure, model risk, auditability, failure consequence |

Both agents operate without shared session context — they receive only the document under review. This is intentional.

---

## Troubleshooting

**Model skips a phase or ignores the gate condition**
Check that the keystone (`using-methodology/SKILL.md`) was loaded. In Option A, confirm the session-start hook ran. In Option B, confirm the system prompt contains the full `<EXTREMELY_IMPORTANT>` block.

**"I don't see the skill" error in Claude Code**
Verify the plugin is installed: run `/plugin list` and confirm `ai-process-assessment` appears.

**Hook does not fire on session start**
Confirm `async: false` in `hooks/hooks.json` — async hooks can miss the first user turn.

**The model produces output before the predecessor file exists**
Add an explicit note to the relevant `CLAUDE.md` override, or re-invoke the correct phase skill directly. The gate condition is enforced by the model reading the skill — if the skill wasn't invoked, the gate didn't run.

**GRC gate fires on an opportunity that doesn't need it**
Add a CLAUDE.md override entry with rationale. The deliverable gate will audit the override before external sharing.
