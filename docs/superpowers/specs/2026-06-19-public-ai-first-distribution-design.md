# Public, AI-First Distribution — Design

**Date:** 2026-06-19
**Status:** Design (approved in brainstorming; pending written-spec review)
**Supersedes/extends:** `2026-06-17-engagement-conductor-design.md` (Conductor), epic #58 slice definitions
**Spec home:** local (`docs/superpowers/` is gitignored)

---

## 0. North star

A **public** Claude plugin that **anyone** — not just trained consultants — installs and uses by **talking to it in plain language**, and that is an **AI-first workflow**: the AI *drives* a rigorous AI/automation-opportunity assessment end-to-end. The human is a **decision-maker and a domain source, never a tool operator.** They never invoke a skill, learn a phase name, open a file, or run a command. They describe their situation, answer what the AI asks, make the calls only a human can make, and get a defensible result plus whatever artifact they request.

The 11-phase methodology, the deterministic engine, and the gates are **invisible trust-machinery** that keep the AI honest (every number sourced, nothing fabricated). They are never the interface. The `conducting-engagement` Conductor is the AI-first driver that hides them.

### 0.1 Locked decisions (2026-06-19)

1. **Distribution = public open-source** — public repo + public marketplace, Apache-2.0. Zero per-user support, so the product must run on a stranger's machine unattended.
2. **All slices before one public launch** — Slice 1 is done (validated end-to-end, issue #65). Build Slice 2 + Slice 3 + distribution hardening, then launch once.
3. **Slice frame = merged** (reconciles the spec §13 and epic #58):
   - **Slice 2 — Adaptive + Parallel + Editable.**
   - **Slice 3 — Polish + Flywheel.**

### 0.2 Launch-blocking acceptance criteria

- **AC-1 (AI-first / "anyone"):** a non-expert who has never heard the methodology's vocabulary completes a full assessment to a defensible deliverable **using only natural language** — zero phase names, file names, or commands leaked into the conversation.
- **AC-2 (runs anywhere there's code):** a fresh `/plugin install` on a clean machine runs the bundled sample end-to-end and produces **real numbers** (not PENDING) with no manual path/dependency/venv steps.
- **AC-3 (trust):** every number in every artifact traces to `results.json` → a tested formula → a sourced `model/*.json` input; the deliverable-gate blocks anything that doesn't.
- **AC-4 (cross-surface):** methodology works in Claude Code, Cowork, and Claude.ai; real numbers wherever a code/analysis tool exists; graceful PENDING where it doesn't.

---

## 1. The experience we are building (experience-first)

> Written from what the **person** feels. The machinery that makes each true is in §3+.

**First contact.** They install the plugin and start a session. The AI greets them: *"I help teams find where AI and automation actually pay off. Tell me about the team or process you're thinking about — or say 'run the sample' to watch a full example first."* No README required. (§3.B)

**Driving.** They say *"help me find automation wins in our billing team."* The AI infers whether they're a consultant relaying interviews or an operator describing their own team, confirms in one sentence, and takes it from there — asking only the questions a human can answer, in plain language, teaching as it goes if they're an operator. It never says "Phase 4" or "OPP-003." (§3.D / Slice 2)

**The hard parts stay human.** When a real decision appears — what's in scope, is this score right, build vs. buy, does this opportunity clear governance — the AI stops and asks, plainly, and records the answer. Everything else it just does. (Touchpoint taxonomy, Slice 1.)

**Correcting it.** They can interrupt at any time — *"no, our rate is $200, not $185"* — and the AI edits the input, re-runs the math, re-checks everything downstream that depended on it, and tells them what changed. (§3, Slice 2 Edit.)

**Getting artifacts.** They ask for whatever they need — *"give me a board deck,"* *"export this to our Excel template,"* *"show me the math behind the $1.3M."* The AI generates it from the verified data, never inventing a number. (§3.C)

**Trusting it.** Every figure can be traced to its source and re-derived identically. If a skeptical CFO asks "where did this come from," the AI can show the inputs, the formula, and the citation — exactly. (§2)

---

## 2. The trust substrate (why the numbers are believable)

The original reason for the live-formula Excel export was *proof the calculations are right.* That concern is now solved more rigorously than a workbook ever could:

- **Tested formulas.** `engine/compute.py` is the single source of formula truth; the golden-number suite asserts each formula against known-correct outputs. (Proof the formula is right, not just visible.)
- **Reproducibility.** Re-running the engine yields byte-identical `results.json`. (Excel recalc varies by version/locale — it was the *fragile* link.)
- **Enforced audit chain.** Every figure traces `results.json` → formula → sourced `model/*.json` input; the deliverable-gate *blocks* arithmetic-in-prose. (Demonstrated live in #65, which caught a fabricated `~$1.3M` prose sum.)
- **Determinism.** No randomness; single-write input ownership.

**Therefore the xlsx export is dropped.** It is a redundant, lossy, fragile re-presentation of guarantees the data layer already makes — and the heaviest dependency. Correctness is proven by the engine + audit chain; the workbook is removed.

---

## 3. Workstreams

Sequencing = **Approach A** (runtime-first, public-polish-last): **D1 → Slice 2 → Slice 3 → D2**, with the data-contract pivot (§3.C) folded into D1.

### 3.A — D1: cross-surface runtime (the foundation)

**Experience:** the user just talks; numbers appear; nothing about Python, paths, or installs ever surfaces.

The "must run in Claude Code **and** Cowork **and** Claude.ai" requirement forces a **stdlib-only compute core**, so the auditable numbers run in *any* code sandbox, not just a shell with pip.

1. **Stdlib-only core.** Drop the phantom `formulas` dep (imported nowhere). Lazy-import the workbook (now removed — §3.C) so `engine.run` needs no third-party deps. Replace `pyyaml` in `state/conductor_state.py` (2 calls, trivial frontmatter) with stdlib. Result: `engine.run` + all of `state/` run on bare `python` — no venv, no pip.
2. **Import-path wrapper.** `bin/aipa-engine` / `bin/aipa-state` set `PYTHONPATH` to the plugin root so `engine`/`state` resolve from a user's own project dir. Skills call the wrapper, never bare `python -m …`. (Fixes the import failure that made the engine unrunnable when installed.)
3. **Path-agnostic session-start hook.** Replace the hook hardcoded to the author's machine path + stale plugin name; gate on plugin/skill presence, and use it for the AI-first welcome (§3.B).
4. **Cross-surface execution:** Claude Code / Cowork = first-class (engine runs as a plugin). Claude.ai = stdlib core runs via the code/analysis tool when present (real numbers), graceful PENDING when absent; methodology ports via system-prompt + knowledge files.
5. **Clean-machine smoke test** (CI, container, `/plugin install`, run sample, assert real numbers) = the AC-2 gate.

### 3.B — Conversational onboarding (AI-first first-run)

**Experience:** install → the AI welcomes you and offers to start or to run the sample. The README is for the curious, not the path.

- Session-start surfaces a short, warm, capability-framed greeting (not the raw keystone dump). The keystone still loads for the model; the *user* sees an invitation.
- "Run the sample" is a first-class conversational entry, not a doc step.

### 3.C — Data contract + artifact generation (replaces the xlsx)

**Experience:** the user asks for any artifact in their own words; the AI produces it from verified data, never inventing a number.

- Promote `model/*.json` + `results.json` to a **documented, versioned schema** — the engine's public API and single source of truth.
- New **`generate-artifact` skill:** renders any user-requested output (deck, CSV, their Excel template, one-pager, chart, the audit view) *from* the data contract under a **no-new-arithmetic guard** — any new number must go through the engine, never be computed in the artifact. Ships a built-in **CFO "show-your-work" audit template** (per-figure `inputs × formula = result` + source citation), the legible proof the xlsx used to carry.
- **Remove** `engine/workbook.py`, `formulas`, `openpyxl`, and the workbook tests; drop `financial-model.xlsx` from the required engagement-folder convention (artifacts are generated on demand, not built by default).

### 3.D — Slice 2: Adaptive + Parallel + Editable

**Experience:** the AI handles a multi-process engagement smoothly, adapts to who it's talking to, and lets you correct it mid-stream by just saying so.

- **Parallel per-process fan-out** (headline): per-process **headless** phases (Phase 4 synthesis, Phase 5 opportunity ID) run as concurrent subagents, one per process. The convergence gate + cross-process chain-detection pass (already modeled in Slice 1) gate the merged results. *Fan-out is headless work only — never parallel live interviews.*
- **Edit / interruption-splicing** (absorbs epic #58's "Edit"): user interrupts in plain language → AI edits the owning model input → re-runs the engine → **staleness re-drives** affected downstream phases → logs a both-parties `human-overrode` decision and reports what changed. *This is where the old xlsx "what-if" now lives — stricter, because it re-runs the audited pipeline.*
- **Granular autonomy** (per touchpoint-class) with should-confirm batching in autonomous mode.
- **Register-driven teaching** (consultant vs. operator) and **holding-the-line** posture toward an impatient non-expert (firm-but-teaching, not refuse-and-quote). *This is the engine of AC-1.*

### 3.E — Slice 3: Polish + Flywheel

**Experience:** the AI recovers gracefully from mess, shows you what it's doing, and quietly gets better over time.

- Graceful **messy/partial-state** handling (half-written files, manual edits, interrupted phases) + multi-session resume hardening.
- **Live-status surfacing** — a lightweight `conductor-status` view derived from `.conductor.md` + `state.state`. *(Not the old SSE cockpit dashboard, which was removed in #73/#75; only state helpers remain.)*
- **Improvement-flywheel hook:** the Conductor auto-flags rationalization escapes it encounters into `improvement-log.md` (RED); a human still approves the GREEN/REFACTOR.

### 3.F — D2: public-grade launch gate

**Experience:** a stranger finds the plugin, installs it, and it just works — and a contributor can open a PR safely.

- Flip repo **private → public** + public marketplace entry; stranger-grade README/INSTALL trimmed to the paths that actually work; sample as a one-command demo; CONTRIBUTING + issue/PR templates.
- **Harden CI for a public repo (security-critical):** the auto-review-fix-merge loop (live since v2.9.0) is built for a *private, trusted* repo. Public = untrusted fork PRs. Gate auto-merge to maintainers only, run **secret-free CI** on fork PRs, and scope the @claude review bot so forks cannot exfiltrate secrets or auto-merge malicious code.
- License/secrets scrub (hardcoded paths gone, hook generic, sample clearly fictional ✓); clean-machine smoke (§3.A) as a release-blocking check; extend existing release automation for public releases.

---

## 4. Testing strategy

- **Static suite (LLM-free)** — methodology-graph guards + engine golden numbers — runs on every PR (already exists; keep).
- **Stdlib-core test** — proves `engine.run` + `state/` run with zero third-party deps (guards AC-2/AC-4).
- **Clean-machine install smoke** — container → `/plugin install` → run sample → assert real numbers; release-blocking (AC-2).
- **AC-1 acceptance rehearsal** — a scripted "non-expert, plain-language only" run of the sample that asserts no methodology vocabulary leaked to the user channel (best-effort heuristic + manual sign-off).
- **Per-surface manual verification checklists** for Cowork + Claude.ai (documented; can't be fully automated).

---

## 5. Sequencing & decomposition

Each workstream gets its own spec → plan → implementation cycle. Build order:

1. **D1 + 3.C** (runtime + data-contract pivot) — foundation; changes how every skill invokes the engine, so it must precede slice work.
2. **3.B** (conversational onboarding) — small, can land with D1.
3. **Slice 2** (§3.D) — built/validated on the D1 runtime.
4. **Slice 3** (§3.E).
5. **D2** (§3.F) — final launch gate.

This spec is the **program** design. The first implementation plan should cover **D1 + 3.C + 3.B** (the foundation milestone); Slice 2, Slice 3, and D2 each get their own plan when reached.

---

## 6. Risks & open questions

- **Claude.ai is genuinely constrained.** It does not "install plugins" like Code/Cowork; the engine runs there only via the code/analysis tool + uploaded knowledge files. AC-4 promises real numbers *where a code tool exists*, PENDING otherwise — we should not overpromise a seamless plugin install on claude.ai web.
- **AC-1 is hard to test automatically.** "Zero jargon leaked" needs a heuristic + human sign-off; risk of subjective pass/fail. Define the bar concretely in the Slice 2 plan.
- **Public-repo security** is the highest-consequence D2 item; mis-scoped fork CI could leak secrets. Treat as its own hardening task with explicit review.
- **`pyyaml` removal** touches `state/conductor_state.py` — small but in the resume/staleness path; needs its own tests.
- **Stdlib-core refactor** must keep the golden numbers byte-identical (regression risk on the `--no-workbook` path and frontmatter parsing).
