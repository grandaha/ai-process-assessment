# Checkpoint Outcome — <checkpoint id>

- **Checkpoint:** <id> (e.g., baseline — Process & Baseline Validation)
- **Date:** <YYYY-MM-DD>
- **Attendees / sign-off:** <names + roles — e.g., process owner(s), sponsor>
- **Status:** Confirmed | Changes Requested

## Changes requested

| What | Which PROC-NNN / metric | Raised by |
|---|---|---|
| <e.g., cycle time is 9 days, not 12> | PROC-003 · cycle time | <name> |

(Leave the table empty and write "None — confirmed as presented" if Status is Confirmed.)

## Routing

- On **Changes Requested**: route to <route-back phase — e.g., Phase 4 discovering-processes>; correct the source file(s); re-run `python -m engine.run <engagement>/` if any number changed; regenerate the checkpoint; append a new outcome record.
- On **Confirmed**: downstream phases may rely on the validated output; the terminal deliverable-gate and final deliverable may cite this sign-off.
