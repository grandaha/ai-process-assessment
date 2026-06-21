#!/usr/bin/env bash
# Path-agnostic conversational front door. Fires on every install (opt-in by
# installing the plugin) unless AI_ASSESSMENT_SILENT=1. Injects the one durable
# token every engine/state command needs — the absolute plugin root — plus the
# command forms and a warm, jargon-free greeting. The hook stays dumb: it does
# not detect whether an engagement exists; conducting-engagement resolves that.

if [ "${AI_ASSESSMENT_SILENT:-}" = "1" ]; then
  exit 0
fi

ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -z "$ROOT" ]; then
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

cat <<EOF
<EXTREMELY_IMPORTANT>
This session has the ai-process-assessment plugin installed. It turns plain-language
goals into audited AI/automation opportunity numbers via an 11-phase methodology.

Plugin root: ${ROOT}
Interpreter: ${PY}
Engine command form: ${PY} ${ROOT}/engine/run.py <engagement-folder>/
State command form:  ${PY} ${ROOT}/state/state.py <engagement-folder>/

If you're resuming an assessment I'll pick up where we left off; if you're starting fresh
I'll greet you with your options — start a new one, continue an existing one, or run a sample.
You don't need to know any commands or phase names.
</EXTREMELY_IMPORTANT>
EOF
