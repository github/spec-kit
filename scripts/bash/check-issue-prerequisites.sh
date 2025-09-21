#!/usr/bin/env bash

# Issue prerequisite checking script
#
# This script provides prerequisite checking for issue-resolution flow.
# It checks for issue-specific files and directories.
#
# Usage: ./check-issue-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for resolution phase)
#   --include-tasks     Include tasks.md in AVAILABLE_DOCS list
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"ISSUE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: ISSUE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n ISSUE_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
        --include-tasks)
            INCLUDE_TASKS=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-issue-prerequisites.sh [OPTIONS]

Issue prerequisite checking for issue-resolution flow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for resolution phase)
  --include-tasks     Include tasks.md in AVAILABLE_DOCS list
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check issue prerequisites (issue.md required)
  ./check-issue-prerequisites.sh --json
  
  # Check resolution prerequisites (issue.md + tasks.md required)
  ./check-issue-prerequisites.sh --json --require-tasks --include-tasks
  
  # Get issue paths only (no validation)
  ./check-issue-prerequisites.sh --paths-only
  
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths and validate branch
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# For issue-resolution flow, we look in issues/ directory instead of specs/
ISSUES_DIR="$REPO_ROOT/issues"
ISSUE_DIR="$ISSUES_DIR/$CURRENT_BRANCH"
ISSUE_SPEC="$ISSUE_DIR/issue.md"
ISSUE_PLAN="$ISSUE_DIR/plan.md"
ISSUE_TASKS="$ISSUE_DIR/tasks.md"
ISSUE_RESEARCH="$ISSUE_DIR/research.md"
ISSUE_DATA_MODEL="$ISSUE_DIR/data-model.md"
ISSUE_CONTRACTS_DIR="$ISSUE_DIR/contracts"
ISSUE_QUICKSTART="$ISSUE_DIR/quickstart.md"

# If paths-only mode, output paths and exit
if $PATHS_ONLY; then
    echo "REPO_ROOT: $REPO_ROOT"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "ISSUE_DIR: $ISSUE_DIR"
    echo "ISSUE_SPEC: $ISSUE_SPEC"
    echo "ISSUE_PLAN: $ISSUE_PLAN"
    echo "ISSUE_TASKS: $ISSUE_TASKS"
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$ISSUE_DIR" ]]; then
    echo "ERROR: Issue directory not found: $ISSUE_DIR" >&2
    echo "Run /issue first to create the issue structure." >&2
    exit 1
fi

if [[ ! -f "$ISSUE_SPEC" ]]; then
    echo "ERROR: issue.md not found in $ISSUE_DIR" >&2
    echo "Run /issue first to create the issue specification." >&2
    exit 1
fi

# Check for tasks.md if required
if $REQUIRE_TASKS && [[ ! -f "$ISSUE_TASKS" ]]; then
    echo "ERROR: tasks.md not found in $ISSUE_DIR" >&2
    echo "Run /plan first to create the task list for this issue." >&2
    exit 1
fi

# Build list of available documents
docs=()

# Always check these optional docs
[[ -f "$ISSUE_RESEARCH" ]] && docs+=("research.md")
[[ -f "$ISSUE_DATA_MODEL" ]] && docs+=("data-model.md")

# Check contracts directory (only if it exists and has files)
if [[ -d "$ISSUE_CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$ISSUE_CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi

[[ -f "$ISSUE_QUICKSTART" ]] && docs+=("quickstart.md")

# Include tasks.md if requested and it exists
if $INCLUDE_TASKS && [[ -f "$ISSUE_TASKS" ]]; then
    docs+=("tasks.md")
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of documents
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi
    
    printf '{"ISSUE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$ISSUE_DIR" "$json_docs"
else
    # Text output
    echo "ISSUE_DIR:$ISSUE_DIR"
    echo "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    check_file "$ISSUE_RESEARCH" "research.md"
    check_file "$ISSUE_DATA_MODEL" "data-model.md"
    check_dir "$ISSUE_CONTRACTS_DIR" "contracts/"
    check_file "$ISSUE_QUICKSTART" "quickstart.md"
    
    if $INCLUDE_TASKS; then
        check_file "$ISSUE_TASKS" "tasks.md"
    fi
fi
