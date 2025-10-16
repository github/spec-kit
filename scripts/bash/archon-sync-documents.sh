#!/usr/bin/env bash
# Archon Document Sync - Silent Bidirectional Synchronization
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called by slash commands for pull-before/push-after operations

# NOTE: This script creates marker files for the AI agent to process
# Only the AI agent (Claude Code) can make actual MCP calls

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh" 2>/dev/null || exit 0

# Arguments: feature_dir, mode (pull|push)
FEATURE_DIR="${1:-}"
SYNC_MODE="${2:-pull}"

if [[ -z "$FEATURE_DIR" ]]; then
    exit 0  # Silent exit if no feature directory provided
fi

if [[ ! "$SYNC_MODE" =~ ^(pull|push)$ ]]; then
    exit 0  # Invalid mode, silent exit
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
    exit 0  # No project ID, can't sync
fi

# Document types to sync
DOCUMENT_TYPES=(
    "spec.md:spec"
    "plan.md:plan"
    "research.md:research"
    "data-model.md:data-model"
    "quickstart.md:quickstart"
    "tasks.md:tasks"
)

# Create sync request for AI agent
SYNC_REQUEST_FILE="$SCRIPT_DIR/.archon-state/${FEATURE_NAME}.sync-request"
mkdir -p "$SCRIPT_DIR/.archon-state" 2>/dev/null || true

# Build document list
DOCS_JSON="["
FIRST=true
for doc_entry in "${DOCUMENT_TYPES[@]}"; do
    IFS=':' read -r filename doc_type <<< "$doc_entry"
    filepath="$FEATURE_DIR/$filename"
    doc_id=$(load_document_mapping "$FEATURE_NAME" "$filename")

    if [[ "$FIRST" == "true" ]]; then
        FIRST=false
    else
        DOCS_JSON+=","
    fi

    DOCS_JSON+="{\"filename\":\"$filename\",\"doc_type\":\"$doc_type\",\"filepath\":\"$filepath\",\"doc_id\":\"${doc_id:-}\"}"
done
DOCS_JSON+="]"

cat > "$SYNC_REQUEST_FILE" 2>/dev/null <<EOF
{
    "feature_name": "$FEATURE_NAME",
    "project_id": "$PROJECT_ID",
    "feature_dir": "$FEATURE_DIR",
    "sync_mode": "$SYNC_MODE",
    "documents": $DOCS_JSON,
    "timestamp": "$(get_timestamp)",
    "status": "pending"
}
EOF

# Exit silently
exit 0
