#!/bin/bash

# Script to help update task status and maintain task registry
# Usage: ./scripts/update-task-status.sh [feature-dir] [task-id] [new-status] [assignee]

set -e

FEATURE_DIR="${1:-}"
TASK_ID="${2:-}"
NEW_STATUS="${3:-}"
ASSIGNEE="${4:-Unassigned}"

if [[ -z "$FEATURE_DIR" || -z "$TASK_ID" || -z "$NEW_STATUS" ]]; then
    echo "Usage: $0 <feature-dir> <task-id> <new-status> [assignee]"
    echo ""
    echo "Examples:"
    echo "  $0 specs/001-user-auth T005 'In Progress' @john"
    echo "  $0 specs/001-user-auth T007 Completed"
    echo "  $0 specs/001-user-auth T010 Blocked @team"
    echo ""
    echo "Valid statuses: 'Not Started', 'In Progress', 'Testing', 'Completed', 'Blocked'"
    exit 1
fi

TASKS_FILE="$FEATURE_DIR/tasks.md"

if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Error: tasks.md not found at $TASKS_FILE"
    exit 1
fi

# Validate status
case "$NEW_STATUS" in
    "Not Started"|"In Progress"|"Testing"|"Completed"|"Blocked")
        ;;
    *)
        echo "Error: Invalid status '$NEW_STATUS'"
        echo "Valid statuses: 'Not Started', 'In Progress', 'Testing', 'Completed', 'Blocked'"
        exit 1
        ;;
esac

echo "Updating task $TASK_ID in $TASKS_FILE..."

# Create backup
cp "$TASKS_FILE" "$TASKS_FILE.bak"

# Update task status using sed
# Look for the task ID and update the status line that follows
sed -i.tmp "/- \[[ x]\] $TASK_ID /,/Status.*Detailed.*Assignee/ {
    s/Status\": [^|]*/Status\": $NEW_STATUS/
    s/Assignee\": [^}]*/Assignee\": $ASSIGNEE/
}" "$TASKS_FILE"

# If status is Completed, mark the checkbox
if [[ "$NEW_STATUS" == "Completed" ]]; then
    sed -i.tmp "s/- \[ \] $TASK_ID /- [x] $TASK_ID /" "$TASKS_FILE"
else
    sed -i.tmp "s/- \[x\] $TASK_ID /- [ ] $TASK_ID /" "$TASKS_FILE"
fi

# Update the Task Registry summary (basic counting)
echo "Updating Task Registry summary..."

# Count tasks by status
NOT_STARTED=$(grep -c "Status\": Not Started" "$TASKS_FILE" || echo "0")
IN_PROGRESS=$(grep -c "Status\": In Progress" "$TASKS_FILE" || echo "0")
TESTING=$(grep -c "Status\": Testing" "$TASKS_FILE" || echo "0")
COMPLETED=$(grep -c "Status\": Completed" "$TASKS_FILE" || echo "0")
BLOCKED=$(grep -c "Status\": Blocked" "$TASKS_FILE" || echo "0")
DETAILED=$(grep -c "Detailed\": Yes" "$TASKS_FILE" || echo "0")

# Update the summary section
sed -i.tmp "/### Task Status Summary/,/### / {
    /- \*\*Not Started\*\*:/ s/[0-9]* tasks/$NOT_STARTED tasks/
    /- \*\*In Progress\*\*:/ s/[0-9]* tasks/$IN_PROGRESS tasks/
    /- \*\*Testing\*\*:/ s/[0-9]* tasks/$TESTING tasks/
    /- \*\*Completed\*\*:/ s/[0-9]* tasks/$COMPLETED tasks/
    /- \*\*Blocked\*\*:/ s/[0-9]* tasks/$BLOCKED tasks/
    /- \*\*Detailed\*\*:/ s/[0-9]* tasks/$DETAILED tasks/
}" "$TASKS_FILE"

# Update timestamp
CURRENT_DATE=$(date +"%Y-%m-%d")
sed -i.tmp "s/Updated\**: \[DATE\]/Updated**: $CURRENT_DATE/" "$TASKS_FILE"

# Clean up temp files
rm -f "$TASKS_FILE.tmp"

echo "✓ Task $TASK_ID updated to '$NEW_STATUS' (assigned to $ASSIGNEE)"
echo "✓ Task Registry summary updated"
echo ""
echo "Current status summary:"
echo "  Not Started: $NOT_STARTED tasks"
echo "  In Progress: $IN_PROGRESS tasks"
echo "  Testing: $TESTING tasks"
echo "  Completed: $COMPLETED tasks"
echo "  Blocked: $BLOCKED tasks"
echo "  Detailed: $DETAILED tasks"

# Show the updated task
echo ""
echo "Updated task:"
grep -A 1 "- \[[ x]\] $TASK_ID " "$TASKS_FILE" || echo "Task not found in output"