#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo ""
            echo "Creates a session summary to help AI agents compress context."
            echo "This script gathers current project state for the AI to use"
            echo "when creating a compressed session summary."
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)
MEMORY_DIR="$REPO_ROOT/.speckit/memory"
mkdir -p "$MEMORY_DIR"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)
CURRENT_TIME=$(date +%H:%M)

# Detect current feature
CURRENT_BRANCH=$(get_current_branch 2>/dev/null || echo "unknown")
FEATURE_DIR=$(find_feature_dir_by_prefix "$REPO_ROOT" "$CURRENT_BRANCH" 2>/dev/null || echo "")

# Collect project state
FEATURE_NAME=""
SPEC_STATUS="not_found"
PLAN_STATUS="not_found"
TASKS_STATUS="not_found"

if [ -n "$FEATURE_DIR" ] && [ -d "$FEATURE_DIR" ]; then
    FEATURE_NAME=$(basename "$FEATURE_DIR")
    [ -f "$FEATURE_DIR/spec.md" ] && SPEC_STATUS="exists"
    [ -f "$FEATURE_DIR/plan.md" ] && PLAN_STATUS="exists"
    [ -f "$FEATURE_DIR/tasks.md" ] && TASKS_STATUS="exists"
fi

# Count total features
TOTAL_FEATURES=0
if [ -d "$REPO_ROOT/specs" ]; then
    TOTAL_FEATURES=$(find "$REPO_ROOT/specs" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
fi

# Check constitution
CONSTITUTION_EXISTS=false
[ -f "$REPO_ROOT/memory/constitution.md" ] && CONSTITUTION_EXISTS=true

# Estimate token savings (heuristic: assume typical session is at 80-100K)
# Pruning typically saves 40-60K tokens
ESTIMATED_SAVINGS=50000

# Output results
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "timestamp": "$CURRENT_DATE $CURRENT_TIME",
  "current_feature": "$FEATURE_NAME",
  "current_branch": "$CURRENT_BRANCH",
  "spec_status": "$SPEC_STATUS",
  "plan_status": "$PLAN_STATUS",
  "tasks_status": "$TASKS_STATUS",
  "total_features": $TOTAL_FEATURES,
  "constitution_exists": $CONSTITUTION_EXISTS,
  "memory_dir": "$MEMORY_DIR",
  "summary_file": "$MEMORY_DIR/session-summary-$CURRENT_DATE.md",
  "estimated_token_savings": $ESTIMATED_SAVINGS
}
EOF
else
    cat <<EOF
Session Prune - Data Collection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current State:
  Feature: $FEATURE_NAME
  Branch: $CURRENT_BRANCH
  Total Features: $TOTAL_FEATURES
  Constitution: $CONSTITUTION_EXISTS

Specification Status:
  spec.md: $SPEC_STATUS
  plan.md: $PLAN_STATUS
  tasks.md: $TASKS_STATUS

Next Steps:
  The AI agent will now create a compressed session summary
  based on the conversation history and this project state.

  Summary will be saved to:
  $MEMORY_DIR/session-summary-$CURRENT_DATE.md

  Expected token savings: ~$ESTIMATED_SAVINGS tokens
EOF
fi
