#!/usr/bin/env bash
# Archon Auto-Init - Silent Project and Document Creation
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# Called in background by /speckit.specify command

# NOTE: This script creates a marker file that the AI agent will process
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

# Extract feature name from directory path
FEATURE_NAME=$(extract_feature_name "$FEATURE_DIR")

if [[ -z "$FEATURE_NAME" ]]; then
    exit 0  # Silent exit if feature name extraction fails
fi

# Check if Archon MCP available (completely silent)
if ! check_archon_available; then
    exit 0  # MCP not available, do nothing
fi

# Check if project already exists
EXISTING_PROJECT_ID=$(load_project_mapping "$FEATURE_NAME")
if [[ -n "$EXISTING_PROJECT_ID" ]]; then
    exit 0  # Project already exists, nothing to do
fi

# Load spec.md to extract title and description
SPEC_FILE="$FEATURE_DIR/spec.md"
if [[ ! -f "$SPEC_FILE" ]]; then
    exit 0  # No spec file, can't create project
fi

# Extract title from spec.md (first # heading)
PROJECT_TITLE=$(grep -m 1 "^# " "$SPEC_FILE" 2>/dev/null | sed 's/^# //' || echo "")
if [[ -z "$PROJECT_TITLE" ]]; then
    PROJECT_TITLE="Feature: $FEATURE_NAME"
fi

# Extract description from spec.md (content after first heading, before next ##)
PROJECT_DESC=$(sed -n '/^# /,/^## /p' "$SPEC_FILE" 2>/dev/null | sed '1d;$d' | head -n 3 | tr '\n' ' ' || echo "")
if [[ -z "$PROJECT_DESC" ]]; then
    PROJECT_DESC="Implementation of $FEATURE_NAME"
fi

# Create initialization request for AI agent to process
INIT_REQUEST_FILE="$SCRIPT_DIR/.archon-state/${FEATURE_NAME}.init-request"
mkdir -p "$SCRIPT_DIR/.archon-state" 2>/dev/null || true

cat > "$INIT_REQUEST_FILE" 2>/dev/null <<EOF
{
    "feature_name": "$FEATURE_NAME",
    "project_title": "$PROJECT_TITLE",
    "project_description": "$PROJECT_DESC",
    "spec_file": "$SPEC_FILE",
    "feature_dir": "$FEATURE_DIR",
    "timestamp": "$(get_timestamp)",
    "status": "pending"
}
EOF

# Exit silently
exit 0
