---
name: ai-process-assessment:generate-artifact
description: On-demand artifact generation from the verified data contract. On a plain-language request ("give me the CFO audit", "a one-pager", "this as a spreadsheet"), regenerates the engine contract, renders the artifact referencing only contract figures, builds a figure manifest, and verifies it before emitting — never inventing or re-deriving a number. Ships the built-in CFO show-your-work audit template.
---

# Generating an Artifact

## Session Start

This skill runs as a standalone session. At session start:
1. Read `scope.md` — extract the `Engagement folder:` field. This is the canonical engagement path for all inputs and outputs. Do not ask the user for the path. Halt if `scope.md` is absent or the field is missing (return to Phase 1).
2. Read this engagement's `.conductor.md` (`read_conductor`) — extract `engine_root` (the absolute plugin root). Every engine command below uses this path.

## Render Loop

Execute these steps in order. Do not skip any step.

### Step 1 — Resolve the engagement folder

Extract the `Engagement folder:` field from `scope.md`. This is `<folder>` in all paths below.

### Step 2 — Regenerate the contract (always, no mtime check)

Run the engine unconditionally to guarantee fresh `results.json` + `trace.json`:

```bash
python3 <engine_root>/engine/run.py <folder>/
```

This is idempotent. Do NOT skip it based on file age, last-run time, or any other heuristic. The repo is sync-prone (iCloud/Dropbox) and stale contract figures cause audit failures.

### Step 3 — Load the contract

Read:
- `<folder>/model/results.json` — all computed figures
- `<folder>/model/trace.json` — provenance steps with source citations

### Step 4 — Render the artifact

Identify the artifact type from the user's request:

| Request | Template | Output file |
|---|---|---|
| "CFO audit", "show your work", "audit view" | `cfo-audit-template.md` (in this skill's directory) | `<folder>/artifacts/cfo-audit.md` |
| "one-pager", "executive summary sheet" | Prose summary: one page, all headline figures | `<folder>/artifacts/one-pager.md` |
| "CSV", "spreadsheet export" | Flat CSV: one row per figure (path, value, label) | `<folder>/artifacts/figures.csv` |
| Binary (`.xlsx`, `.pptx`, `.docx`, `.pdf`) | Render the verified text payload first, then hand it to the host surface's file-creation | `<folder>/artifacts/<name>.<ext>` |

**Canonical rule:** Reference every number by its contract path — never type a literal. For example, to include `costs.OPP-001.total`, resolve it from `results.json["costs"]["OPP-001"]["total"]` and format it. Do not copy-paste numbers from prior context.

For the CFO audit, follow `cfo-audit-template.md` exactly: one block per initiative, `inputs × formula = result` rows pulled from `trace.json` steps, money formatted as `$NNN,NNN`, `Source` citing each input's `source` path from the trace. PENDING figures are rendered as `Pending — awaiting \`<input path>\`` — see Step 6 for the block rule.

### Step 5 — Build the figure manifest

Construct the manifest: one entry per rendered number, in stored numeric form (not formatted strings):

```json
[
  {"value": <number from results.json>, "path": "<dotted results path>"}
]
```

Include every money figure, score, or aggregate that appears in the artifact. Do not include intermediate inputs (hours, rates, percentages) that are not themselves results-contract values.

### Step 6 — Verify the manifest (block on error)

Run:

```bash
PYTHONPATH="<engine_root>" python3 -c "
import json, sys
from pathlib import Path
from engine.artifact_check import check_manifest

results = json.loads(Path('<folder>/model/results.json').read_text())
manifest = json.loads(Path('<folder>/artifacts/<name>.manifest.json').read_text())
errors = check_manifest(manifest, results)
if errors:
    for e in errors:
        print('ERROR:', e, file=sys.stderr)
    sys.exit(1)
print('OK: manifest verified,', len(manifest), 'figures')
"
```

**If any errors are returned:** STOP. Do not emit the artifact. Report each error to the user and diagnose:
- `unknown path` — the path in the manifest does not exist in `results.json`; correct the path.
- `figure is PENDING` — a required input is missing from the model; do not emit the artifact until the input is provided and the engine is re-run.
- `value mismatch` — the manifest value does not match the contract; the artifact contains a stale or incorrect number.

A PENDING figure must never appear in an emitted artifact.

### Step 7 — Emit the artifact

Write:
- `<folder>/artifacts/<name>.md` (or `.csv`, `.html`) — the rendered text artifact
- `<folder>/artifacts/<name>.manifest.json` — the verified figure manifest

For binaries (`.xlsx`, `.pptx`, `.docx`, `.pdf`): the plugin adds no binary writer. Hand the verified text payload (already checked in Step 6) and the manifest to the host surface's file-creation. The binary is rendered 1:1 from the already-verified values — no new arithmetic.

Confirm the files written and their paths. Do NOT reproduce the full artifact content in the response — state the path only.

## CFO Audit (built-in template)

The CFO "show your work" audit is the canonical artifact for finance reviewers. It renders one block per initiative with cost data, showing the inputs × formula = result for every line item, with source citations to the trace. See `cfo-audit-template.md` in this skill's directory for the full render specification.

A sample rendered audit is at `sample-pso-delivery/artifacts/cfo-audit.md`. Use it as a reference for the expected format and figure density.

## Rationalization Table

| Rationalization / Shortcut | Correct Reframe |
|---|---|
| "The contract was just regenerated — skip Step 2." | The engine is cheap and the repo is sync-prone. Always regenerate. No mtime checks. |
| "I'll type the number from memory / context — it matches." | If it is not resolved from `results.json` at render time, it is not contract-verified. Typed literals are how stale figures enter audits. |
| "The manifest check is a formality — I can eyeball it." | The guard is mechanical for a reason. PENDING figures or mismatches that pass an eyeball check will fail a CFO review. Run the check. |
| "I'll fix the number in the artifact after the check fails." | No. Fix the contract path or the missing input, re-run the engine, re-render, re-verify. |
| "Binary output is fine to render directly — I can do the math." | Binaries are rendered from the verified text payload only. No new arithmetic in the binary layer. |

## Completion Confirmation

After writing both files, present to the user:
1. The artifact file path and type
2. The manifest file path and figure count
3. Confirmation that `artifact_check` returned no errors
4. Any PENDING figures encountered (if any inputs were missing — these blocked the artifact)
