#!/usr/bin/env bash
# update-context.sh — Copilot integration: create/update .github/copilot-instructions.md
#
# This is the copilot-specific implementation that produces the GitHub
# Copilot instructions file. The shared dispatcher reads
# .specify/integration.json and calls this script.
#
# NOTE: This script is not yet active. It will be activated in Stage 7
# when the shared update-agent-context.sh replaces its case statement
# with integration.json-based dispatch. The shared script must also be
# refactored to support SPECKIT_SOURCE_ONLY (guard the main logic)
# before sourcing will work.
#
# Sources common.sh and the shared update-agent-context functions,
# then calls update_agent_file with the copilot target path.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Source shared utilities
source "$REPO_ROOT/.specify/scripts/bash/common.sh"

# Source update-agent-context functions (parse_plan_data, update_agent_file, etc.)
# SPECKIT_SOURCE_ONLY prevents the shared script from running its own main().
export SPECKIT_SOURCE_ONLY=1
source "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh"

# Gather feature paths and parse plan data
_paths_output=$(get_feature_paths) || exit 1
eval "$_paths_output"
parse_plan_data "$IMPL_PLAN"

# Create or update the copilot instructions file
update_agent_file "$REPO_ROOT/.github/copilot-instructions.md" "GitHub Copilot"
