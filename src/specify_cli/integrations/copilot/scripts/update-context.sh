#!/usr/bin/env bash
# update-context.sh — Copilot integration: update .github/copilot-instructions.md
#
# Sources the shared update-agent-context.sh (which defines parse_plan_data,
# update_agent_file, etc.) and calls update_agent_file with the copilot-
# specific target path.
#
# In the final architecture (Stage 7) the shared dispatcher reads
# .specify/integration.json and exec's this script. Until then, the
# shared script's case statement still works for copilot.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
COPILOT_FILE="$REPO_ROOT/.github/copilot-instructions.md"

# Source the shared script to get update_agent_file and friends.
# Use SPECKIT_SOURCE_ONLY=1 to load functions without running main().
export SPECKIT_SOURCE_ONLY=1
source "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh"

update_agent_file "$COPILOT_FILE" "GitHub Copilot" "$@"
