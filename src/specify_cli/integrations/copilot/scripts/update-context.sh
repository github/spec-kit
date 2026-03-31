#!/usr/bin/env bash
# update-context.sh — Copilot integration: update .github/copilot-instructions.md
#
# Called by the shared dispatcher after it has sourced common functions
# (parse_plan_data, update_agent_file, etc.). This script only contains
# the copilot-specific target path and agent name.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

update_agent_file "$REPO_ROOT/.github/copilot-instructions.md" "GitHub Copilot"
