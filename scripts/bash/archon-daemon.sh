#!/usr/bin/env bash
# Archon Background Sync Daemon - Optional Periodic Synchronization
# CRITICAL: This script is for ADVANCED USERS ONLY
# CRITICAL: This script MUST be completely silent (no stdout/stderr)
# CRITICAL: NOT started automatically, NOT documented for regular users

# Usage: bash archon-daemon.sh <feature-dir> [interval-seconds]
# Example: bash archon-daemon.sh /path/to/specs/001-feature 300

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh" 2>/dev/null || exit 0

# Feature directory passed as argument
FEATURE_DIR="${1:-}"
SYNC_INTERVAL="${2:-300}"  # Default: 5 minutes (300 seconds)

if [[ -z "$FEATURE_DIR" ]]; then
    exit 1  # Require feature directory
fi

# Validate interval (must be positive integer)
if ! [[ "$SYNC_INTERVAL" =~ ^[0-9]+$ ]] || [[ "$SYNC_INTERVAL" -lt 60 ]]; then
    exit 1  # Minimum 60 seconds to avoid hammering
fi

# Extract feature name
FEATURE_NAME=$(extract_feature_name "$FEATURE_DIR")

if [[ -z "$FEATURE_NAME" ]]; then
    exit 1  # Feature name required
fi

# Check if Archon MCP available
if ! check_archon_available; then
    exit 0  # MCP not available, exit gracefully
fi

# Check if project exists
PROJECT_ID=$(load_project_mapping "$FEATURE_NAME")
if [[ -z "$PROJECT_ID" ]]; then
    exit 0  # No project, nothing to sync
fi

# Create PID file to prevent multiple daemons
PID_FILE="$SCRIPT_DIR/.archon-state/${FEATURE_NAME}.daemon.pid"
mkdir -p "$SCRIPT_DIR/.archon-state" 2>/dev/null || true

# Check if daemon already running
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
        # Daemon already running, exit silently
        exit 0
    fi
fi

# Write current PID
echo "$$" > "$PID_FILE" 2>/dev/null || exit 1

# Cleanup function to remove PID file on exit
cleanup() {
    rm -f "$PID_FILE" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Background sync loop (completely silent)
while true; do
    # Pull status from Archon (silent)
    bash "$SCRIPT_DIR/archon-auto-pull-status.sh" "$FEATURE_DIR" 2>/dev/null || true

    # Sync documents if they exist (silent)
    if [[ -d "$FEATURE_DIR" ]]; then
        bash "$SCRIPT_DIR/archon-sync-documents.sh" "$FEATURE_DIR" "pull" 2>/dev/null || true
    fi

    # Sleep for interval
    sleep "$SYNC_INTERVAL" 2>/dev/null || break
done

# Exit silently
exit 0
