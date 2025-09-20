#!/bin/bash

# Script to manage milestone-based branches
# Usage: ./scripts/manage-milestone-branches.sh <command> [options]

set -e

FEATURE_DIR="${1:-}"
COMMAND="${2:-}"
MILESTONE="${3:-}"

show_usage() {
    echo "Usage: $0 <feature-dir> <command> [milestone]"
    echo ""
    echo "Commands:"
    echo "  list                     List all milestone branches for feature"
    echo "  create <milestone>       Create milestone branch (milestone-1, milestone-2, etc.)"
    echo "  switch <milestone>       Switch to milestone branch"
    echo "  create-integration       Create integration branch"
    echo "  switch-integration       Switch to integration branch"
    echo "  status                   Show current branch and milestone status"
    echo "  check <task-id>         Check which branch a specific task should use"
    echo ""
    echo "Examples:"
    echo "  $0 specs/001-user-auth create milestone-1"
    echo "  $0 specs/001-user-auth switch milestone-2"
    echo "  $0 specs/001-user-auth check T008"
    echo "  $0 specs/001-user-auth status"
    exit 1
}

if [[ -z "$FEATURE_DIR" || -z "$COMMAND" ]]; then
    show_usage
fi

# Extract feature name from feature directory
FEATURE_NAME=$(basename "$FEATURE_DIR")

# Validate feature directory exists
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "Error: Feature directory '$FEATURE_DIR' not found"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

get_current_branch() {
    git branch --show-current
}

branch_exists() {
    git show-ref --verify --quiet "refs/heads/$1"
}

create_milestone_branch() {
    local milestone="$1"
    local branch_name="${FEATURE_NAME}/${milestone}"
    
    if branch_exists "$branch_name"; then
        echo "Branch '$branch_name' already exists"
        return 0
    fi
    
    echo "Creating milestone branch: $branch_name"
    git checkout -b "$branch_name"
    echo "✓ Created and switched to branch: $branch_name"
}

switch_to_branch() {
    local branch_name="$1"
    
    if ! branch_exists "$branch_name"; then
        echo "Error: Branch '$branch_name' does not exist"
        echo "Create it first with: $0 $FEATURE_DIR create $(basename $branch_name)"
        exit 1
    fi
    
    echo "Switching to branch: $branch_name"
    git checkout "$branch_name"
    echo "✓ Switched to branch: $branch_name"
}

list_milestone_branches() {
    echo "Milestone branches for feature '$FEATURE_NAME':"
    git branch --list "${FEATURE_NAME}/*" | sed 's/^../  /'
    echo ""
    echo "Current branch: $(get_current_branch)"
}

show_status() {
    local current_branch=$(get_current_branch)
    echo "Feature: $FEATURE_NAME"
    echo "Current branch: $current_branch"
    echo ""
    
    # Check if current branch is a milestone branch
    if [[ "$current_branch" =~ ^${FEATURE_NAME}/(milestone-[0-9]+|integration)$ ]]; then
        echo "✓ Working in milestone branch"
        
        # Extract milestone info
        local milestone_part=$(echo "$current_branch" | sed "s/^${FEATURE_NAME}\///")
        echo "✓ Milestone: $milestone_part"
    elif [[ "$current_branch" == "$FEATURE_NAME" ]]; then
        echo "ℹ Working in main feature branch"
    else
        echo "⚠ Not in a milestone branch for this feature"
    fi
    
    echo ""
    echo "Available milestone branches:"
    git branch --list "${FEATURE_NAME}/*" | sed 's/^../  /' || echo "  No milestone branches created yet"
}

check_task_branch() {
    local task_id="$1"
    local tasks_file="$FEATURE_DIR/tasks.md"
    
    if [[ ! -f "$tasks_file" ]]; then
        echo "Error: tasks.md not found at $tasks_file"
        exit 1
    fi
    
    # Search for task ID and extract branch assignment
    local branch_line=$(grep -A 10 "\\- \\[ \\] $task_id " "$tasks_file" | grep "Branch.*:" | head -1)
    
    if [[ -z "$branch_line" ]]; then
        echo "Task $task_id not found in tasks.md"
        exit 1
    fi
    
    # Extract branch name from the line
    local branch_name=$(echo "$branch_line" | sed 's/.*Branch.*: `\([^`]*\)`.*/\1/')
    
    echo "Task $task_id should be developed on branch: $branch_name"
    
    # Check if branch exists
    if branch_exists "$branch_name"; then
        echo "✓ Branch exists"
    else
        echo "⚠ Branch does not exist yet"
        echo "Create it with: $0 $FEATURE_DIR create $(basename $branch_name)"
    fi
    
    # Check if we're on the correct branch
    local current_branch=$(get_current_branch)
    if [[ "$current_branch" == "$branch_name" ]]; then
        echo "✓ You are on the correct branch"
    else
        echo "ℹ Current branch: $current_branch"
        echo "Switch to correct branch with: $0 $FEATURE_DIR switch $(basename $branch_name)"
    fi
}

case "$COMMAND" in
    "list")
        list_milestone_branches
        ;;
    "create")
        if [[ -z "$MILESTONE" ]]; then
            echo "Error: Milestone name required for create command"
            echo "Example: $0 $FEATURE_DIR create milestone-1"
            exit 1
        fi
        create_milestone_branch "$MILESTONE"
        ;;
    "switch")
        if [[ -z "$MILESTONE" ]]; then
            echo "Error: Milestone name required for switch command"
            exit 1
        fi
        switch_to_branch "${FEATURE_NAME}/${MILESTONE}"
        ;;
    "create-integration")
        create_milestone_branch "integration"
        ;;
    "switch-integration")
        switch_to_branch "${FEATURE_NAME}/integration"
        ;;
    "status")
        show_status
        ;;
    "check")
        if [[ -z "$MILESTONE" ]]; then
            echo "Error: Task ID required for check command"
            echo "Example: $0 $FEATURE_DIR check T008"
            exit 1
        fi
        check_task_branch "$MILESTONE"
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        show_usage
        ;;
esac