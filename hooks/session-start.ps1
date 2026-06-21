# Path-agnostic conversational front door (PowerShell twin of session-start.sh).
# Fires on every install unless AI_ASSESSMENT_SILENT=1. Injects the absolute
# plugin root, the engine/state command forms, and a warm, jargon-free greeting.

if ($env:AI_ASSESSMENT_SILENT -eq "1") { exit 0 }

$root = $env:CLAUDE_PLUGIN_ROOT
if ([string]::IsNullOrEmpty($root)) { exit 0 }

if (Get-Command python3 -ErrorAction SilentlyContinue) { $py = "python3" } else { $py = "python" }

@"
<EXTREMELY_IMPORTANT>
This session has the ai-process-assessment plugin installed. It turns plain-language
goals into audited AI/automation opportunity numbers via an 11-phase methodology.

Plugin root: $root
Interpreter: $py
Engine command form: $py $root/engine/run.py <engagement-folder>/
State command form:  $py $root/state/state.py <engagement-folder>/

If you're resuming an assessment I'll pick up where we left off; if you're starting fresh
I'll greet you with your options — start a new one, continue an existing one, or run a sample.
You don't need to know any commands or phase names.
</EXTREMELY_IMPORTANT>
"@
