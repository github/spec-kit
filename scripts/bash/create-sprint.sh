#!/usr/bin/env bash

set -e

# Function to find the repository root by searching for existing project markers
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

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(unset CDPATH && cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
fi

# Source common functions
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
SPRINT_NAME=""
DURATION="2w"
SPRINT_GOAL=""
SUCCESS_CRITERIA=""
ARGS=()

# Parse arguments
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --duration)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --duration requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            DURATION="${!i}"
            ;;
        --goal)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --goal requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            SPRINT_GOAL="${!i}"
            ;;
        --criteria)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --criteria requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            SUCCESS_CRITERIA="${!i}"
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
    i=$((i + 1))
done

# Get sprint name from remaining args
SPRINT_NAME="${ARGS[*]}"

if [ -z "$SPRINT_NAME" ]; then
    echo "Error: Sprint name is required" >&2
    echo "Usage: create-sprint.sh [--json] [--duration 2w] [--goal \"Goal\"] [--criteria \"Crit1|Crit2\"] \"Sprint Name\"" >&2
    exit 1
fi

# Check if active sprint already exists
ACTIVE_DIR="$REPO_ROOT/.specify/sprints/active"
if [ -f "$ACTIVE_DIR/sprint.md" ]; then
    echo "Error: Active sprint already exists at $ACTIVE_DIR" >&2
    echo "Complete the current sprint with '/speckit.sprint complete' or '/speckit.archive' first" >&2
    exit 1
fi

# Determine next sprint number
ARCHIVE_DIR="$REPO_ROOT/.specify/sprints/archive"
SPRINT_NUMBER=1
if [ -d "$ARCHIVE_DIR" ]; then
    # Count existing sprint directories
    SPRINT_COUNT=$(find "$ARCHIVE_DIR" -maxdepth 1 -type d -name "sprint-*" | wc -l | tr -d ' ')
    SPRINT_NUMBER=$((SPRINT_COUNT + 1))
fi

# Format sprint number with leading zeros
SPRINT_NUM_FORMATTED=$(printf "%03d" "$SPRINT_NUMBER")

# Calculate dates
START_DATE=$(date +%Y-%m-%d)
case "$DURATION" in
    1w|1week)
        END_DATE=$(date -v+7d +%Y-%m-%d 2>/dev/null || date -d "+7 days" +%Y-%m-%d)
        DURATION_TEXT="1 week"
        NUM_WEEKS=1
        ;;
    2w|2weeks)
        END_DATE=$(date -v+14d +%Y-%m-%d 2>/dev/null || date -d "+14 days" +%Y-%m-%d)
        DURATION_TEXT="2 weeks"
        NUM_WEEKS=2
        ;;
    3w|3weeks)
        END_DATE=$(date -v+21d +%Y-%m-%d 2>/dev/null || date -d "+21 days" +%Y-%m-%d)
        DURATION_TEXT="3 weeks"
        NUM_WEEKS=3
        ;;
    4w|4weeks|1m|1month)
        END_DATE=$(date -v+28d +%Y-%m-%d 2>/dev/null || date -d "+28 days" +%Y-%m-%d)
        DURATION_TEXT="4 weeks"
        NUM_WEEKS=4
        ;;
    *)
        echo "Warning: Unknown duration format '$DURATION', defaulting to 2 weeks" >&2
        END_DATE=$(date -v+14d +%Y-%m-%d 2>/dev/null || date -d "+14 days" +%Y-%m-%d)
        DURATION_TEXT="2 weeks"
        NUM_WEEKS=2
        ;;
esac

CREATED_DATE=$(date +%Y-%m-%d)

# Generate sprint backlog weeks
BACKLOG_WEEKS=""
for ((i=1; i<=NUM_WEEKS; i++)); do
    BACKLOG_WEEKS+="### Week $i"$'\n'
    BACKLOG_WEEKS+="[Add tasks for week $i]"
    if [ $i -lt $NUM_WEEKS ]; then
        BACKLOG_WEEKS+=$'\n\n'
    fi
done

# Create active sprint directory
mkdir -p "$ACTIVE_DIR"

# Copy sprint template
TEMPLATE_FILE="$REPO_ROOT/.specify/templates/sprint-template.md"
SPRINT_FILE="$ACTIVE_DIR/sprint.md"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Sprint template not found at $TEMPLATE_FILE" >&2
    exit 1
fi

# Copy and replace placeholders
sed -e "s/\[NUMBER\]/$SPRINT_NUM_FORMATTED/g" \
    -e "s/\[NAME\]/$SPRINT_NAME/g" \
    -e "s/\[DURATION\]/$DURATION_TEXT/g" \
    -e "s/\[START_DATE\]/$START_DATE/g" \
    -e "s/\[END_DATE\]/$END_DATE/g" \
    -e "s/\[DATE\]/$CREATED_DATE/g" \
    -e "s/\$ARGUMENTS/$SPRINT_NAME/g" \
    "$TEMPLATE_FILE" > "$SPRINT_FILE.tmp"

# Replace goal and success criteria if provided
if [ -n "$SPRINT_GOAL" ]; then
    sed -i.bak "s/\[To be defined - use \/speckit.clarify to set sprint goal\]/$SPRINT_GOAL/" "$SPRINT_FILE.tmp"
    rm -f "$SPRINT_FILE.tmp.bak"
fi

if [ -n "$SUCCESS_CRITERIA" ]; then
    # Convert pipe-separated criteria to markdown list
    FORMATTED_CRITERIA=""
    IFS='|' read -ra CRITERIA_ARRAY <<< "$SUCCESS_CRITERIA"
    for criterion in "${CRITERIA_ARRAY[@]}"; do
        if [ -n "$FORMATTED_CRITERIA" ]; then
            FORMATTED_CRITERIA+=$'\n'
        fi
        FORMATTED_CRITERIA+="- [ ] $criterion"
    done
    
    # Escape special characters for sed
    ESCAPED_CRITERIA=$(echo "$FORMATTED_CRITERIA" | sed 's/[&/\]/\\&/g')
    sed -i.bak "s/- \[ \] \[To be defined - use \/speckit.clarify to set success criteria\]/$ESCAPED_CRITERIA/" "$SPRINT_FILE.tmp"
    rm -f "$SPRINT_FILE.tmp.bak"
fi

# Replace SPRINT_BACKLOG_WEEKS placeholder
# Write backlog weeks to temp file
echo "$BACKLOG_WEEKS" > "$SPRINT_FILE.weeks"
# Use sed to read and replace
sed -e "/\[SPRINT_BACKLOG_WEEKS\]/ {
    r $SPRINT_FILE.weeks
    d
}" "$SPRINT_FILE.tmp" > "$SPRINT_FILE"
rm -f "$SPRINT_FILE.tmp" "$SPRINT_FILE.weeks"

# Create backlog.md
cat > "$ACTIVE_DIR/backlog.md" << BACKLOG
# Sprint $SPRINT_NUM_FORMATTED Backlog

## Features

No features added yet. Use \`/speckit.sprint add <feature-id>\` to add features.

## Notes

[Sprint planning notes]
BACKLOG

# Create decisions.md
cat > "$ACTIVE_DIR/decisions.md" << DECISIONS
# Sprint $SPRINT_NUM_FORMATTED Decisions

Document key decisions made during this sprint.

## Decision Log

No decisions recorded yet.
DECISIONS

# Output result
if [ "$JSON_MODE" = true ]; then
    cat << JSON
{
  "success": true,
  "sprint_number": "$SPRINT_NUM_FORMATTED",
  "sprint_name": "$SPRINT_NAME",
  "duration": "$DURATION_TEXT",
  "start_date": "$START_DATE",
  "end_date": "$END_DATE",
  "active_dir": "$ACTIVE_DIR",
  "files_created": [
    "$SPRINT_FILE",
    "$ACTIVE_DIR/backlog.md",
    "$ACTIVE_DIR/decisions.md"
  ]
}
JSON
else
    echo "✅ Sprint $SPRINT_NUM_FORMATTED created successfully!"
    echo ""
    echo "Sprint: $SPRINT_NAME"
    echo "Duration: $DURATION_TEXT ($START_DATE - $END_DATE)"
    echo "Location: $ACTIVE_DIR"
    echo ""
    echo "Files created:"
    echo "  - sprint.md"
    echo "  - backlog.md"
    echo "  - decisions.md"
    echo ""
    echo "Next steps:"
    echo "  1. Add features: /speckit.sprint add <feature-id>"
    echo "  2. Define sprint goals in sprint.md"
    echo "  3. Start working on features"
fi
