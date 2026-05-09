#!/usr/bin/env bash
# Injects the methodology keystone into sessions started from the ai-cockpit project.

if [ "$CLAUDE_PROJECT_DIR" != "/Users/daveraffaele/Desktop/ai-cockpit" ]; then
  exit 0
fi

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-/Users/daveraffaele/Desktop/plugins/ai-usecase-methodology}"
SKILL_PATH="${PLUGIN_ROOT}/skills/using-methodology/SKILL.md"

if [ -f "$SKILL_PATH" ]; then
  echo "<EXTREMELY_IMPORTANT>"
  cat "$SKILL_PATH"
  echo "</EXTREMELY_IMPORTANT>"
fi
