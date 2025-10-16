#!/usr/bin/env bash
# Archon Task Auto-Sync - Silent Task Synchronization
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called in background by /speckit.tasks command

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
    exit 0  # No project ID, can't sync tasks
fi

# Load tasks.md
TASKS_FILE="$FEATURE_DIR/tasks.md"
if [[ ! -f "$TASKS_FILE" ]]; then
    exit 0  # No tasks file, nothing to sync
fi

# Parse tasks.md and extract tasks
# Format: - [ ] [TaskID] [P?] [Story?] Description
TASKS_JSON="["
FIRST=true

while IFS= read -r line; do
    # Match task lines: - [ ] or - [X] or - [x]
    if [[ "$line" =~ ^-[[:space:]]\[[[:space:]xX]\][[:space:]](.+)$ ]]; then
        task_content="${BASH_REMATCH[1]}"

        # Check if completed
        if [[ "$line" =~ ^-[[:space:]]\[[xX]\] ]]; then
            status="done"
        else
            status="todo"
        fi

        # Extract task ID if present: [T001] or [T002]
        task_id=""
        if [[ "$task_content" =~ ^\[T([0-9]+)\][[:space:]](.+)$ ]]; then
            task_id="T${BASH_REMATCH[1]}"
            task_content="${BASH_REMATCH[2]}"
        fi

        # Extract parallel marker [P] if present
        parallel="false"
        if [[ "$task_content" =~ ^\[P\][[:space:]](.+)$ ]]; then
            parallel="true"
            task_content="${BASH_REMATCH[1]}"
        fi

        # Extract story marker [US1], [US2], etc. if present
        story=""
        if [[ "$task_content" =~ ^\[US([0-9]+)\][[:space:]](.+)$ ]]; then
            story="US${BASH_REMATCH[1]}"
            task_content="${BASH_REMATCH[2]}"
        fi

        # The rest is the task title/description
        task_title="$task_content"

        # Build JSON entry
        if [[ "$FIRST" == "true" ]]; then
            FIRST=false
        else
            TASKS_JSON+=","
        fi

        # Escape quotes in title
        task_title="${task_title//\"/\\\"}"

        TASKS_JSON+="{\"task_id\":\"${task_id:-}\",\"title\":\"$task_title\",\"status\":\"$status\",\"parallel\":$parallel,\"story\":\"${story:-}\"}"
    fi
done < "$TASKS_FILE"

TASKS_JSON+="]"

# Create task sync request for AI agent
SYNC_REQUEST_FILE="$SCRIPT_DIR/.archon-state/${FEATURE_NAME}.task-sync-request"
mkdir -p "$SCRIPT_DIR/.archon-state" 2>/dev/null || true

cat > "$SYNC_REQUEST_FILE" 2>/dev/null <<EOF
{
    "feature_name": "$FEATURE_NAME",
    "project_id": "$PROJECT_ID",
    "tasks_file": "$TASKS_FILE",
    "tasks": $TASKS_JSON,
    "timestamp": "$(get_timestamp)",
    "status": "pending"
}
EOF

# Exit silently
exit 0
