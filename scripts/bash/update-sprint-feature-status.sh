#!/usr/bin/env bash

set -e

# Function to find repository root
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Get repo root
SCRIPT_DIR="$(unset CDPATH && cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root." >&2
        exit 1
    fi
fi

# Get feature ID from current branch or SPECIFY_FEATURE env var
FEATURE_ID=""
if [ -n "$SPECIFY_FEATURE" ]; then
    FEATURE_ID="$SPECIFY_FEATURE"
elif git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [[ "$BRANCH" =~ ^[0-9]{3}- ]]; then
        FEATURE_ID="$BRANCH"
    fi
fi

if [ -z "$FEATURE_ID" ]; then
    echo "Error: Could not determine feature ID from branch or SPECIFY_FEATURE env var" >&2
    exit 1
fi

# Parse arguments
NEW_STATUS="$1"
if [ -z "$NEW_STATUS" ]; then
    echo "Usage: $0 <status>" >&2
    echo "Status options: Not Started | In Progress | Blocked | In Review | Complete" >&2
    exit 1
fi

# Update status in active sprint files
ACTIVE_SPRINT="$REPO_ROOT/.specify/sprints/active/sprint.md"
BACKLOG_FILE="$REPO_ROOT/.specify/sprints/active/backlog.md"

if [ -f "$ACTIVE_SPRINT" ]; then
    # Update sprint.md
    sed -i.bak "s/^\(| $FEATURE_ID |[^|]*|[^|]*|\) [^|]* \(|.*\)$/\1 $NEW_STATUS \2/" "$ACTIVE_SPRINT"
    rm -f "$ACTIVE_SPRINT.bak"
fi

if [ -f "$BACKLOG_FILE" ]; then
    # Update backlog.md
    sed -i.bak "s/^\(| $FEATURE_ID |[^|]*|[^|]*|\) [^|]* \(|.*\)$/\1 $NEW_STATUS \2/" "$BACKLOG_FILE"
    rm -f "$BACKLOG_FILE.bak"
fi

echo "✅ Updated $FEATURE_ID status to: $NEW_STATUS"
