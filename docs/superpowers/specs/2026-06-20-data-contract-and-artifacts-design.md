# Data Contract + Artifact Generation — Design

**Foundation #86, workstream 3.C.** Replaces the removed xlsx workbook with an AI-first,
on-demand artifact path built on a versioned, verifiable data contract.

**Status:** approved 2026-06-20 (tightened after vagueness review). Supersedes the §3.C
sketch in `docs/superpowers/specs/2026-06-19-public-ai-first-distribution-design.md`.

---

## 0. North star

The user asks for any artifact in their own words; the AI produces it from verified engine
data and **never invents or re-derives a number**. The legible proof the xlsx used to
carry — per-figure `inputs × formula = result` + source — is now a first-class, testable
output of the engine itself.

### 0.1 Locked decisions (2026-06-20)

1. **Engine emits provenance + a guard test enforces it.** The engine gains an additive
   audit trace; artifacts reference figures by contract path, never as typed literals; a
   static test fails if any figure in the sample audit artifact is not traceable to the
   contract.
2. **Two-layer split.** The *plugin* stays pure stdlib and never bundles a binary writer.
   The *host surface* (claude.ai / Claude Desktop / Claude Code's xlsx skill) produces
   `.xlsx` / `.pptx` / `.docx` / `.pdf` from an already-verified payload when available.
3. **Portable text floor:** `generate-artifact` always emits Markdown / CSV / HTML — pure
   stdlib, works on any surface. Binaries are an opportunistic hand-off, not a dependency.
4. `results.json` stays **byte-identical** (existing golden constraint). The trace is a new
   sidecar file; the contract version lives in the trace + the contract doc, never in
   `results.json`.

### 0.2 Why the surface owns binaries

Research (2026-06-20): claude.ai / Desktop / Mobile ship a file-creation capability
(genuine binary `.xlsx`/`.pptx`/`.docx`/`.pdf` via a code-execution sandbox, all tiers);
Claude Code ships an official xlsx skill (code execution + LibreOffice recalc validation).
Excel output is therefore a **surface** capability, not a plugin one. This keeps the
pure-stdlib guarantee and the clean-machine smoke test (#91) intact.

---

## 1. Components

Five units, each with one responsibility.

| Unit | Responsibility | Type |
|---|---|---|
| `model/trace.json` | Per-figure provenance for every computed value in `results.json`. Written by `run.py` on the same run. | Data artifact (new) |
| `engine/trace.py` | Pure-stdlib provenance builder. **Reads the values `compute.py` already returns** and formats them into provenance — it does not re-derive any number (see §3.2). | Engine module (new) |
| `docs/data-contract.md` | Public API reference: every key in `results.json` + `trace.json`, types, `contract_version`, and the compatibility policy. | Doc (new) |
| `engine/artifact_check.py` | Stdlib verifier: given an artifact's figure manifest + the contract, asserts every manifest figure matches the contract value (§4.2). Powers the guard test. | Engine module (new) |
| `skills/generate-artifact/` | Standalone skill: plain-language request → load contract → render referencing only contract figures → build manifest → run `artifact_check` → emit text floor or hand a verified payload to the surface. Ships the built-in CFO audit template. | Skill (new) |

**Unchanged by this work:** `results.json` bytes; `engine/compute.py` formulas; the
pure-stdlib guarantee; `using-methodology` / `system-prompt.md` (verbatim-sync guard);
`building-deliverable` (Phase 11's fixed HTML coexists — `generate-artifact` is the
on-demand any-format path; no merge in v1).

---

## 2. Contract paths & figure manifest

These two notations are the interface every other section depends on.

**2.1 Contract path (a figure's address).**

- **Result/trace path** — dotted from the `results.json` root, range endpoints as keys:
  `costs.OPP-001.total`, `value.OPP-001.high`, `wave1_aggregate.payback_years.low`.
- **Input source path** — `model/<file>.json#<key>`, where `<key>` is `<id>.<field>` for the
  id-keyed input files: `model/costs.json#OPP-001.labor_hours`,
  `model/baselines.json#PROC-003.volume`.

**2.2 Figure manifest (what an artifact declares).** A JSON list emitted beside every
artifact. Each entry:

```json
{"value": 754000.0, "path": "costs.OPP-001.total"}
```

`value` is the contract figure in its **stored numeric form** (a JSON number, not a display
string like `"$754,000"`). Display formatting lives only in the artifact prose; the skill
formats prose **from** manifest values, so prose and manifest cannot diverge by
construction. The verifier therefore never has to parse currency/percent strings (§4.2).

---

## 3. The audit trace

### 3.1 Data flow

```
model/*.json (inputs)
   │  engine/run.py
   ├─► engine/compute.py ─► results.json        (UNCHANGED — byte-identical)
   └─► engine/trace.py   ─► model/trace.json     (NEW, additive, same run)

User: "give me the CFO audit" / "a one-pager" / "this as a spreadsheet"
   │  skills/generate-artifact
   ├─ load results.json + trace.json
   ├─ render artifact referencing figures BY PATH (never a typed literal)
   ├─ emit figure-manifest  (every number → its contract path)
   ├─ run engine/artifact_check  → block emission on any mismatch
   ├─ TEXT FLOOR: write audit.md / .csv / .html               ◄── portable, any surface
   └─ BINARY (if surface supports): hand verified text payload + manifest to host
        file-creation → .xlsx / .pptx / .docx / .pdf  (rendered 1:1 from verified values)
```

### 3.2 How `trace.py` avoids a second source of formula truth

`compute.py` functions already return their intermediate values: `cost_structure` returns a
`CostBlock` exposing `labor`, `change_mgmt`, `subtotal`, `contingency`, `total`; the others
return their result(s) directly. `trace.py` reads those returned values and the known
inputs, and supplies only the presentational **step template** (the operator symbols and
layout, e.g. `"labor = {labor_hours} × {labor_rate} = {labor}"`). **Every number in a step
comes from `compute.py`'s output or its declared inputs — `trace.py` performs no
arithmetic.** A test evaluates each rendered step's embedded arithmetic and asserts it
equals the stated sub-result (§6, test 2), so a wrong template (`×` mistyped as `+`) fails.

### 3.3 Figure classes

Two classes; test 1 accepts both forms.

- **Computed** — `value.*`, `scores.*`, `costs.*` (incl. `rom.*`), `wave1_aggregate.*`. Full
  provenance: `formula`, ordered `inputs` (each with its `model/*.json` source path),
  `steps`, `result`.
- **Passthrough** — `baselines.*` (the engine copies these from `model/baselines.json`, it
  does not compute them). Provenance is `{"formula": "passthrough", "source":
  "model/baselines.json#<PROC>.<field>", "result": <value>}` — no steps.

Non-numeric fields (`costs.*.rom_label`, `baselines.*.source`) are labels, excluded from
trace numeric coverage and from manifests.

### 3.4 Formulas traced (Task-1 scope)

The eight `compute.py` functions, all traced: `value_range`, `score_composite`,
`cost_structure`, `initiative_rom`, `wave1_aggregate`, `wave1_point`, `payback`, plus the
`volume = base_volume × volume_fraction` derivation that `run.py` performs before
`value_range` (its provenance lists `base_volume` and `volume_fraction` as inputs with a
preceding step). `baselines.*` are passthrough per §3.3.

### 3.5 `trace.json` shape

```json
{
  "contract_version": "1.0",
  "costs": {
    "OPP-001": {
      "total": {
        "formula": "cost_structure",
        "result": 754000.0,
        "inputs": [
          {"name": "labor_hours", "value": 1400, "source": "model/costs.json#OPP-001.labor_hours"},
          {"name": "labor_rate",  "value": 200,  "source": "model/costs.json#OPP-001.labor_rate"}
        ],
        "steps": [
          "labor = 1400 × 200 = 280000",
          "change_mgmt = 280000 × 0.25 = 70000",
          "subtotal = 280000 + 80000 + 150000 + 70000 = 580000",
          "contingency = 580000 × 0.30 = 174000",
          "total = 580000 + 174000 = 754000"
        ]
      }
    }
  }
}
```

A `PENDING` figure in `results.json` is `PENDING` in `trace.json` — no fabricated inputs or
steps.

---

## 4. The CFO audit template + the verifier

### 4.1 CFO audit template (headline built-in)

A near-direct rendering of `trace.json`: one block per figure showing
`inputs × formula = result` + the source citation, with a `PENDING` figure rendered as
"Pending — awaiting `<input>`," never a number. It is the **one** built-in template v1
ships; every other format (deck, one-pager, CSV, the user's own layout) is freeform
generation under the same manifest + verifier discipline — not a pre-built gallery. The
template file lives in `skills/generate-artifact/`.

### 4.2 `artifact_check` (the guard)

For each manifest entry: resolve `path` in `results.json` → the contract value; compare to
the entry's `value` with **exact equality after rounding both to the figure's decimal
places** (money and scores 2 dp; fractions exact). Range endpoints (`.low`/`.high`) are
cited and checked as separate paths. A `value` with no resolvable path, or any mismatch, is
a **hard failure** — the artifact is rejected, not shipped.

### 4.3 The same guard runs at render time, for every artifact

`generate-artifact` builds a manifest and runs `artifact_check` before emitting **any**
artifact, audit or freeform — emission is blocked on failure. This is mechanical, not prose
discipline. CI can only execute it against the sample audit (test 4), but the mechanism is
identical for every artifact the skill produces.

### 4.4 Binary verification boundary

The verification boundary is the **text payload + manifest**. Where the surface supports
file creation, the binary is rendered **1:1 from the already-verified manifest values**, so
it inherits verification. The plugin does not introspect binaries (not portable across
surfaces); it never adds a binary writer of its own.

---

## 5. Versioning, lifecycle, staleness

- **`contract_version` (semver)** lives in `trace.json` + `docs/data-contract.md`, never in
  `results.json`. Policy: **patch** = doc-only clarification; **minor** = additive key
  (back-compatible; consumers ignore unknown keys); **major** = a removed / renamed /
  retyped key. v1 ships `1.0`.
- **Lifecycle / trigger.** `generate-artifact` is a standalone skill (like
  `building-deliverable`), invoked on a plain-language artifact request — not a numbered
  phase. It is gated on `results.json` + `trace.json` existing; if they are absent it runs
  the engine first. `conducting-engagement` registers it as a can-infer / should-confirm
  capability offered once the engine has run.
- **Freshness.** Before rendering, the skill **always regenerates** the contract by running
  the engine (`run.py`), then loads `results.json` + `trace.json`. The engine is cheap, pure
  stdlib, and idempotent — a re-run on unchanged inputs reproduces byte-identical outputs —
  so unconditional regeneration guarantees fresh numbers without any staleness comparison.
  This deliberately avoids mtime checks: the repo lives in an iCloud-synced folder where
  sync rewrites timestamps, which is exactly why `state/staleness.py` hashes content rather
  than trusting mtime.

---

## 6. Testing

All pure-stdlib; `results.json` golden stays byte-identical.

1. `test_trace_covers_results` — every numeric figure in `results.json` has a `trace.json`
   entry (computed **or** passthrough form per §3.3). Drift guard between `compute.py` and
   `trace.py`.
2. `test_trace_steps_are_arithmetically_sound` — each computed figure's rendered `steps`
   evaluate to its stated sub-results and final `result` (catches a wrong step template).
3. `test_trace_inputs_trace_to_model` — every cited input `source` path resolves to a real
   key in `model/*.json`.
4. `test_artifact_check_rejects_untraceable` — a manifest with an invented number (or
   unknown path) fails; a clean manifest passes.
5. `test_sample_audit_verifies` — the sample engagement's generated audit artifact passes
   `artifact_check`, and each manifest value's formatted form appears in the rendered audit
   text (ties prose to manifest for the structured template).
6. `test_contract_doc_lists_all_keys` — `docs/data-contract.md` documents every top-level
   key the engine emits (doc-drift guard).

---

## 7. Decomposition (one plan, ~5 tasks)

| Task | Deliverable |
|---|---|
| 1 | `engine/trace.py` (§3.2–3.5) + `run.py` emits `model/trace.json`; tests 1–3 |
| 2 | `docs/data-contract.md` (results + trace keys, paths §2.1, versioning policy); test 6 |
| 3 | `engine/artifact_check.py` + figure-manifest format (§2.2, §4.2); test 4 |
| 4 | `skills/generate-artifact/` + CFO audit template; sample audit artifact + manifest; test 5 |
| 5 | Wiring: `conducting-engagement` registers the on-demand artifact capability (§5);
       CHANGELOG `[Unreleased]`; methodology-graph guard updates for the new skill + artifact |

---

## 8. Out of v1 (YAGNI)

- Native binary writers in the plugin (`openpyxl`, `python-pptx`, etc.) — binaries are a
  surface capability.
- A formal machine-readable JSON Schema file — the self-describing trace + prose contract
  doc suffice for v1; revisit if external consumers need schema validation.
- Merging or reworking Phase 11 `building-deliverable` — coexists untouched. (A separate
  "standard deliverables" conversation, parked 2026-06-20, may later rework Phase 11 on top
  of this contract layer.)
- A template *library* — v1 ships the CFO audit template + freeform generation only.

---

## 9. Forward compatibility

The contract (`results.json` + `trace.json`), the `artifact_check` verifier, and the
figure-manifest discipline are reusable units. When standard deliverables / Phase 11 are
revisited, Phase 11 can be re-expressed *on top of* this contract layer rather than reworked
from scratch.
