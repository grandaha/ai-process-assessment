# Injects the keystone skill into session context at startup.
# Runs via SessionStart hook — must complete before the first user turn.

$skillPath = Join-Path $PSScriptRoot "..\skills\using-methodology\SKILL.md"

if (Test-Path $skillPath) {
    Write-Output "<EXTREMELY_IMPORTANT>"
    Get-Content $skillPath -Raw
    Write-Output "</EXTREMELY_IMPORTANT>"
}
