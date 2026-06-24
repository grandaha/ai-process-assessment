# Conversational Onboarding (AI-First First-Run) — Design

**Foundation #86, workstream 3.B.** The last remaining Foundation piece, after §3.C (data
contract, merged `e0d058a`) and the portability/runtime work.

**Status:** approved 2026-06-21. Supersedes the §3.B sketch in
`docs/superpowers/specs/2026-06-19-public-ai-first-distribution-design.md`.

---

## 0. North star

Install → the AI welcomes a stranger with a short, warm, **capability-framed** greeting
(not the raw keystone/methodology dump) and offers the paths that make sense for what
already exists: **start** a new assessment, **continue** an existing one, or **run the
sample**. The README is for the curious, not the path. "Run the sample" is a first-class
conversational entry, not a documentation step.

This is **prose only** — a behavioral change to the front-door skill plus one hook-line
tweak and two guards. No engine, state, or data changes.

---

## 1. The gap this closes

- The **session-start hook** already injects a path-agnostic, model-facing front-door note
  (`Plugin root: …` + command forms + one jargon-free line). It is *context for the
  model*, not a specified user-facing greeting, and it does not present the sample or
  continue as paths.
- **`conducting-engagement`** triggers only on a clear assess-opener, and its **Intake**
  jumps straight to register-inference + Phase 1. There is **no proactive greeting** for a
  stranger who opens with "hi" / "what is this" / nothing, and **"run the sample"** lives
  in a separate skill the user must already know to ask for.

3.B adds a first-contact greeting behavior to the front door that resolves what exists and
offers the right paths — reusing the Conductor's existing drive-loop step-0 engagement
resolution.

---

## 2. First-contact decision tree

Lives in a new `## First contact` section of `skills/conducting-engagement/SKILL.md`,
between "When this skill runs" and "Intake."

**Fires only on an ambiguous cold first-contact** — a fresh session where the user has NOT
already given a clear assess-request and is NOT clearly resuming. On a clear request → skip
the greeting, start. On a clear "continue/resume" → resolve and pick up, no greeting.

When it fires, resolve existing engagements (folders containing a `.conductor.md` whose
work is incomplete — the same resolution the drive loop's step 0 performs) and offer:

| Engagements found | Greeting offers |
|---|---|
| **Zero** | **{ Start a new assessment · Run the sample }** |
| **One** | **{ Continue "*&lt;name&gt;*" where you left off · Start new · Run the sample }** — Continue leads |
| **Multiple** | greet + **list them**, then **{ Continue one (which?) · Start new · Run the sample }** |

Continue appears only when there is something to continue.

---

## 3. The greeting copy

Warm, capability-framed, jargon-free — no phase names, no "11-phase methodology," no
commands. Base form (zero engagements):

> Hi — I'm your AI assessment guide. I turn plain-language goals into **audited numbers**
> on where AI and automation can save your team time and money. You don't need to know any
> steps or commands — just talk to me.
>
> Want to:
> - **Start an assessment** — tell me the team, process, or goal you want to look at.
> - **See it work first** — I'll run a complete sample on a realistic (fictional) company,
>   end to end.

When resumable engagements exist, a **Continue** bullet is prepended and leads:

> - **Continue "*Acme billing*"** — pick up where we left off. *(or, if >1: a short list to
>   choose from)*

The greeting example in the skill is wrapped in a stable delimiter (an HTML comment pair
`<!-- greeting:start -->` … `<!-- greeting:end -->`) so the jargon-free guard can slice
exactly that block.

---

## 4. Routing

- **Start an assessment** → flow into the existing **Intake** (register inference → Phase
  1). If the user's choice already names a target ("start — my billing team"), go straight
  in without re-asking.
- **Run the sample** → chain to **`ai-process-assessment:running-sample-engagement`**, which
  owns the A/B bundled-vs-generated scenario chooser. No duplication of that logic here.
- **Continue "*&lt;name&gt;*"** → enter the **drive loop at step 0** with that engagement
  resolved; if more than one, list and let the user pick.

### Hook line tweak

One wording change to `hooks/session-start.sh` and `hooks/session-start.ps1`: the closing
line points to the skill's behavior — "if you're starting fresh I'll greet you with your
options — start one, continue an existing one, or run a sample" — instead of only "tell me
what you'd like to assess." The hook stays **dumb**: it still always-fires, still performs
no detection, and the cold-vs-resume-vs-ambiguous branching stays in the skill. The two
hook scripts must stay in sync (same closing line, modulo shell syntax).

---

## 5. Testing

LLM-free presence/property guards, in the existing `tests/` house style:

1. **`test_conductor_has_first_contact_offer`** — `conducting-engagement`'s body contains
   the `## First contact` section, presents all three path labels (Start / Continue / Run
   the sample), and names `ai-process-assessment:running-sample-engagement` as the sample
   route.
2. **`test_greeting_is_jargon_free`** — the greeting block (sliced between
   `<!-- greeting:start -->` and `<!-- greeting:end -->`) contains none of a methodology
   blocklist: the tokens `Phase 1`…`Phase 11`, `GRC`, `convergence`, `deliverable-gate`,
   and any `ai-process-assessment:` skill-id. Operationalizes "not the raw keystone dump"
   and supports the program's AC-1 (no methodology vocabulary on the user channel).
3. **`tests/test_session_start_hook.py`** — update existing assertions for the tweaked
   closing line; both `.sh` and `.ps1` carry the same offer wording.

Constraints the guards must not break:
- `skills/using-methodology/SKILL.md` and `system-prompt.md` are **untouched**
  (verbatim-sync guard).
- Skill registry is unchanged (no new skill; `conducting-engagement` already counts).

---

## 6. Decomposition

One cohesive prose change with its guards — a **single task**:
- `## First contact` section in `conducting-engagement` (decision tree §2, greeting §3 with
  the delimiter, routing §4).
- Hook closing-line tweak in both `.sh` and `.ps1`.
- The two new guards + the updated hook test.
- CHANGELOG `[Unreleased]` entry. **No version bump** (Foundation chunk, matches #90/#91).

Small enough that inline execution is reasonable; the execution-choice at plan time decides.

---

## 7. Out of v1 (YAGNI)

- No GUI/menu rendering — the offer is conversational text.
- No persisted "onboarding completed" flag — first-contact is inferred from session + folder
  state, not a stored bit.
- No changes to `running-sample-engagement`'s internals (it already has the scenario chooser).
- No engine / state / data-contract changes.

---

## 8. Forward compatibility

This finishes Foundation #86. The first-contact resolution reuses the drive-loop step-0
logic, so when Slice 2 (#87) adds adaptive/granular-autonomy behavior, the greeting's
path-resolution does not need to change — only the post-choice flow it hands off to.
