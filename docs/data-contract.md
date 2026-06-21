# Data Contract — `results.json` + `trace.json`

**contract_version: 1.0**

This document is the public API reference for the two files the engine writes into
`<engagement>/model/` after each run. Downstream consumers (reports, dashboards,
skill prose) MUST NOT depend on internal engine symbols — only on the shapes described
here.

---

## Contract versioning

`contract_version` is `1.0`. It lives in two places:

1. The top-level `contract_version` field of `trace.json`.
2. This document.

It does **not** appear in `results.json`, which is byte-stable: its schema changes
are governed by this contract, not by a runtime field.

### Semver policy

| Bump | Meaning |
|------|---------|
| **patch** (e.g. `1.0.1`) | Documentation clarification only — no file changes |
| **minor** (e.g. `1.1`) | Additive key added to `results.json` or `trace.json` — fully back-compatible |
| **major** (e.g. `2.0`) | Removed, renamed, or retyped key — breaking change |

---

## `results.json`

Produced by `engine.run.build_results`. Contains five top-level keys.

### Top-level keys

| Key | Type | Description |
|-----|------|-------------|
| `value` | object | Value range per opportunity (`{low, high}` or `"PENDING"`) |
| `scores` | object | Composite readiness score per opportunity (float or `"PENDING"`) |
| `costs` | object | Cost breakdown per opportunity (see below) |
| `baselines` | object | Process baseline metrics per process ID |
| `wave1_aggregate` | object | Rolled-up investment, value, and payback for Wave-1 initiatives |

### `value`

```json
{
  "OPP-001": { "low": 480000, "high": 720000 },
  "OPP-002": "PENDING"
}
```

Each entry is either `{ "low": <number>, "high": <number> }` or the sentinel
string `"PENDING"` when inputs are incomplete.

### `scores`

```json
{
  "OPP-001": 3.5,
  "OPP-002": "PENDING"
}
```

Each entry is a float (arithmetic mean of the six readiness dimensions, rounded
to one decimal) or `"PENDING"`.

### `costs`

Full entry (all inputs present):

```json
{
  "OPP-001": {
    "labor": 160000,
    "tech_cost": 40000,
    "integration_cost": 30000,
    "change_mgmt": 57500,
    "subtotal": 287500,
    "contingency": 43125,
    "total": 330625,
    "rom": { "low": 165312.5, "high": 495937.5 },
    "rom_label": "AACE Class 5"
  }
}
```

Sparse entry (any required input is `null`):

```json
{
  "OPP-002": { "total": "PENDING", "rom": "PENDING", "rom_label": "AACE Class 5" }
}
```

### `baselines`

```json
{
  "PROC-01": {
    "volume": 8000,
    "cycle_time_median": 6,
    "cycle_time_p90": 14,
    "error_rate": 0.04,
    "fte": 2.4,
    "source": "Lattice ops interview R2"
  }
}
```

Keyed by `process_id`. All numeric fields may be `null` when the baseline row
is not yet populated.

### `wave1_aggregate`

```json
{
  "investment": { "low": 247968.75, "high": 743906.25 },
  "investment_point": 495937.5,
  "value": { "low": 700000, "high": 1050000 },
  "payback_years": { "low": 0.24, "high": 1.06 }
}
```

Each subkey is either `{ "low": <number>, "high": <number> }`, a plain number,
or `"PENDING"`.

---

## `trace.json`

Produced by `engine.trace.build_trace`. Documents the provenance of every figure
in `results.json`. The `contract_version` field at the root records the schema
version this trace conforms to.

### Root structure

```json
{
  "contract_version": "1.0",
  "value": { ... },
  "scores": { ... },
  "costs": { ... },
  "baselines": { ... },
  "wave1_aggregate": { ... }
}
```

The five data keys mirror the structure of `results.json` exactly.

### Provenance entry shapes

Every leaf in `trace.json` is one of three shapes:

#### Computed entry

```json
{
  "formula": "value_range",
  "result": { "low": 480000, "high": 720000 },
  "inputs": [
    { "name": "improvement_low", "value": 0.1, "source": "model/value.json#OPP-001.improvement_low" },
    { "name": "base_volume",     "value": 8000, "source": "model/baselines.json#PROC-01.volume" }
  ],
  "steps": [
    "volume=8000 × 0.75 = 6000",
    "low=0.1 × 6000 × 800 = 480000",
    "high=0.15 × 6000 × 800 = 720000"
  ]
}
```

Fields:

| Field | Type | Description |
|-------|------|-------------|
| `formula` | string | Name of the `engine.compute` function used |
| `result` | number \| object \| string | Computed value, or `"PENDING"` |
| `inputs` | array | Each element: `{ "name", "value", "source" }` |
| `steps` | array | Human-readable arithmetic trace strings |

#### PENDING entry

```json
{
  "formula": "value_range",
  "result": "PENDING"
}
```

Emitted when at least one required input is `null`.

#### Passthrough entry

```json
{
  "formula": "passthrough",
  "result": 8000,
  "source": "model/baselines.json#PROC-01.volume"
}
```

Emitted for baseline fields that are read directly from `baselines.json` without
transformation.

---

## Path grammar

### Result / trace paths

Paths into `results.json` or `trace.json` are dotted strings from the document
root:

```
costs.OPP-001.total
wave1_aggregate.payback_years.low
```

### Input source paths

The `source` field of a computed `inputs` entry uses the form:

```
model/<file>.json#<id>.<field>
```

Examples:

```
model/value.json#OPP-001.improvement_low
model/baselines.json#PROC-01.volume
model/costs.json#OPP-001.labor_hours
```

The fragment (`#`) separates the file path from the dotted key within that file.

---

## Stability guarantees

- **`results.json`** — byte-stable for a given set of model inputs. The engine
  never writes unstable metadata (timestamps, run IDs) into this file.
- **`trace.json`** — stable for a given set of model inputs. The `contract_version`
  field records the schema version; consumers should check it before parsing.
- Neither file is committed to the repository; both are generated on demand.
