#!/usr/bin/env bash
# Archon Status Pull - Silent Status Synchronization
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called before /speckit.implement to sync task statuses

# NOTE: This script creates marker files for the AI agent to process
# Only the AI agent (Claude Code) can make actual MCP calls

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh" 2>/dev/null || exit 0

# Feature directory passed as argument
FEATURE_DIR="${1:-}"

if [[ -z "$FEATURE_DIR" ]]; then
    exit 0  # Silent exit if no feature directory provided
fi

# Extract feature name
FEATURE_NAME=$(extract_feature_name "$FEATURE_DIR")

if [[ -z "$FEATURE_NAME" ]]; then
    exit 0  # Silent exit if feature name extraction fails
fi

# Check if Archon MCP available (completely silent)
if ! check_archon_available; then
    exit 0  # MCP not available, do nothing
fi

# Check if project exists
PROJECT_ID=$(load_project_mapping "$FEATURE_NAME")
if [[ -z "$PROJECT_ID" ]]; then
    exit 0  # No project ID, can't sync status
fi

# Load tasks.md path
TASKS_FILE="$FEATURE_DIR/tasks.md"
if [[ ! -f "$TASKS_FILE" ]]; then
    exit 0  # No tasks file, nothing to sync
fi

# Create status pull request for AI agent
# Conflict resolution strategy: "archon_wins"
# - Always trust Archon status over local checkboxes
# - Overwrite tasks.md without prompting (silent resolution)
# - No UI, no user interaction, no conflict markers
# - Advanced users can manually edit tasks.md if needed
STATUS_REQUEST_FILE="$SCRIPT_DIR/.archon-state/${FEATURE_NAME}.status-request"
mkdir -p "$SCRIPT_DIR/.archon-state" 2>/dev/null || true

cat > "$STATUS_REQUEST_FILE" 2>/dev/null <<EOF
{
    "feature_name": "$FEATURE_NAME",
    "project_id": "$PROJECT_ID",
    "tasks_file": "$TASKS_FILE",
    "timestamp": "$(get_timestamp)",
    "status": "pending",
    "conflict_strategy": "archon_wins"
}
EOF

# Exit silently
exit 0
