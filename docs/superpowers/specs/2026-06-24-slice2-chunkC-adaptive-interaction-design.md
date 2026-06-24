# Slice 2 · Chunk C — Adaptive interaction (granular autonomy + register-teaching + holding-the-line) — design

**Date:** 2026-06-24
**Status:** Design (approved in brainstorming; pending written-spec review)
**Umbrella:** `2026-06-19-public-ai-first-distribution-design.md` §3.D · issue **#87** · epic **#85**.

> Chunk C of three — the last. A = parallel per-process fan-out (merged, #102). B = edit &
> interruption splicing (merged, #103). This chunk is the **engine of AC-1**. Its merge sets up the
> single `v2.19.0` release that closes #87.

---

## 1. What the user experiences (AI-first)

The user never configures anything. They express pace and trust in plain language, at any point —
*"stop asking me about the small stuff"*, *"slow down and walk me through these"*, *"I trust you on
the analysis, but check anything cost-related with me"*. The conductor adapts how much it pauses,
explains in the register that fits them, and — when pushed to cut a genuine corner — holds the line
while teaching why. A non-expert who has never heard the methodology's vocabulary reaches a
defensible deliverable in plain language (**AC-1**).

## 2. What already exists / what's new

- **Register** (consultant vs operator) is inferred and stamped at intake — but **drives no
  behavior afterward** (it is referenced only at intake). Making the drive loop *consume* it is new.
- **Autonomy preset** (guided/autonomous) is stamped, but the touchpoint taxonomy explicitly defers
  **"Autonomous batching is Slice 2"** — so autonomous mode does not yet batch should-confirm items.
  That batching is this chunk.
- **Holding-the-line** does not exist at all — new.
- `write_conductor(root, data)` already serializes an arbitrary dict to `.conductor.md`, and
  `autonomy` is not consumed by any `state.py` logic — so a richer per-class autonomy map is a
  **schema convention the conductor maintains, not new code**. **Chunk C ships zero new Python.**

## 3. The unifying mechanism — adapt to the human, within unbreakable invariants

All three §3.D pieces are one behavior. The split that makes it AI-native (the Chunk B lesson): the
**flexibility lives in the interface** (say anything, anytime), the **rigor lives in the
invariants**.

### 3.1 Adaptive autonomy (interface = plain language)
- The user never picks a preset or edits a config. They express pace/trust intent in plain
  language, **at any point in the engagement** (not just intake).
- The conductor **interprets** that intent into **per-class** behavior and **persists** it in
  `.conductor.md` under `autonomy` (a richer dict written via the existing `write_conductor`; the
  user never sees or edits it). Shape, by convention:
  ```
  autonomy: {
    should_confirm: "guided" | "batched" | "auto",   # default-class behavior for should-confirm
    per_class: { "<class or item>": "ask" | "auto" }  # plain-language overrides the conductor records
  }
  ```
  `per_class` carries only what the user has actually expressed (e.g. `"costs": "ask"`,
  `"scoring rationale": "auto"`); everything unstated follows `should_confirm`.
- **should-confirm batching:** when the user wants speed, should-confirm items are **accumulated
  and surfaced together as one reviewable digest** at a natural boundary (e.g. before a gate or at
  phase-group completion), each labeled so the user can correct any one of them — nothing is
  silently skipped (still auditable), and nothing pauses them mid-flow. This replaces the
  taxonomy's "Autonomous batching is Slice 2" placeholder.

### 3.2 The invariant (the line that cannot move)
- **must-ask never collapses** — in any mode, under any pressure, regardless of expressed autonomy:
  scope boundaries, out-of-scope process additions, cost actuals, checkpoint outcomes, gate
  dispositions, Build/Buy/Partner. These are genuinely human-only and protect **AC-3** (trust).
- "Just do everything, don't ask me" raises should-confirm toward `auto`/`batched` and never asks
  can-infer — but it **cannot** skip a must-ask. A per-class override can only *tighten* a
  should-confirm item to `ask`, or relax a should-confirm item to `auto`; it can never relax a
  must-ask.

### 3.3 Holding-the-line (enforcement of the floor, under pressure)
- When an impatient user pushes to skip a must-ask ("just give me the number, skip this"), honor the
  **spirit** (move faster everywhere else; batch the rest) while holding the **floor**: explain, in
  one plain sentence, *why this specific input is what makes the number real* and offer the fastest
  honest path to it — *"this one number is what makes the $1.3M defensible; 30 seconds and it's
  yours."*
- **Firm and teaching, never refuse-and-quote.** Do not cite phase names, rules, or the methodology
  at the user; give the human reason the gate exists and the quickest way through it. Holding the
  line is never a wall — it is the shortest honest path.

### 3.4 Register drives the teaching voice
- The stamped `register` conditions *how* the conductor explains throughout the drive loop, not just
  at intake:
  - **operator** (own team, no methodology training) → teach as you go: plain-language "here's why
    this matters / what this means", anticipate confusion, explain before asking.
  - **consultant** (domain-fluent, relaying interviews) → terse and domain-fluent: no hand-holding,
    assume the vocabulary, move fast.
- Register sets the *voice*; autonomy sets the *cadence*; the must-ask floor is the same for both.

## 4. Files touched

- `skills/conducting-engagement/SKILL.md`:
  - **Intake** — update the autonomy step so the stamped `autonomy` uses the §3.1 shape, and note
    that pace/trust can be (re)expressed any time, not only at intake.
  - **New section `## Adaptive autonomy & holding the line`** — §3.1–3.3 (per-class interpretation +
    persistence, should-confirm batching/digest, the must-ask invariant, holding-the-line posture).
  - **Execution model / drive loop** — weave register-driven teaching (§3.4) into how the conductor
    talks (a short "register voice" note where it asks/explains).
  - **Touchpoint taxonomy** — replace the should-confirm row's "(Autonomous batching is Slice 2)"
    with the now-implemented batched-digest behavior, and state the must-ask "every mode, any
    pressure" invariant explicitly.
- `tests/test_conductor_skill.py` — guards (§6).
- `CHANGELOG.md` under `[Unreleased]`; **no version bump in the chunk PR**. The chunk's merge
  triggers the separate `v2.19.0` release that closes #87 (see §7).

**Not touched:** `skills/using-methodology/SKILL.md` / `system-prompt.md` (verbatim-sync, off-limits);
golden `results.json`; any `state/` or `engine/` code (zero new Python).

## 5. Conflict check (done)

- **must-ask floor** aligns verbatim with the existing must-ask taxonomy row — no new must-ask
  items invented, none removed.
- **Chunk B deferral fulfilled:** Chunk B's edit section says downstream re-surfacing "defers to the
  existing touchpoint taxonomy + autonomy preset; batching of those is **Chunk C**, not here." After
  Chunk C, batching exists; B's deferral remains correct (it points at the now-complete behavior) —
  no contradiction, no edit to B's section required.
- **Autonomy schema** extends what intake currently stamps (`autonomy.should_confirm`); intake prose
  is updated to the §3.1 shape so the stamp and the consumer agree. `state.py` ignores `autonomy`,
  so no state-logic change.
- **Terminology:** "autonomy" here is the conductor's interaction cadence — distinct from CLAUDE.md
  methodology overrides (`state/overrides.py`), which are untouched.

## 6. Testable acceptance (guards)

1. **Adaptive autonomy + persistence:** the new section states that pace/trust is expressed in plain
   language (any time), interpreted into per-class behavior, and persisted in `.conductor.md`
   `autonomy` (the user never edits it).
2. **should-confirm batching:** the section and the taxonomy describe should-confirm items being
   batched into one reviewable digest (each labeled/correctable; nothing silently skipped) — and the
   taxonomy no longer says "Autonomous batching is Slice 2".
3. **must-ask invariant:** the section states must-ask never collapses in any mode or under any
   pressure, and that autonomy can never relax a must-ask.
4. **Holding-the-line:** the section states the firm-and-teaching posture (honor the spirit, hold the
   floor, give the human reason + fastest path) and **forbids** refuse-and-quote (no citing phase
   names/rules at the user).
5. **Register-driven teaching:** the execution model states that `register` drives the teaching
   voice downstream (operator → teach-as-you-go; consultant → terse), not just at intake.

(Guards are static string-presence over the skill prose — the repo's established convention.)

## 7. Release (closes #87)

This is the final chunk. After it merges, cut **`v2.19.0`** (CHANGELOG `[Unreleased]` → dated
section) per the repo's release process; that release **closes #87** (Slice 2: Adaptive + Parallel +
Editable) and the epic-#85 Slice-2 milestone. The release itself is a separate step after merge, not
part of the chunk PR.
