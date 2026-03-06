#!/usr/bin/env bash

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for MiniSpec workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for implementation phase)
#   --require-design    Require design.md to exist (for task creation phase)
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... etc.

set -e

# Parse command line arguments
JSON_MODE=false
REQUIRE_TASKS=false
REQUIRE_DESIGN=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            ;;
        --require-design)
            REQUIRE_DESIGN=true
            ;;
        --paths-only)
            PATHS_ONLY=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Consolidated prerequisite checking for MiniSpec workflow.

OPTIONS:
  --json              Output in JSON format
  --require-tasks     Require tasks.md to exist (for implementation phase)
  --require-design    Require design.md to exist (for task creation phase)
  --paths-only        Only output path variables (no prerequisite validation)
  --help, -h          Show this help message

EXAMPLES:
  # Check task prerequisites (design.md required)
  ./check-prerequisites.sh --json --require-design

  # Check implementation prerequisites (design.md + tasks.md required)
  ./check-prerequisites.sh --json --require-design --require-tasks

  # Get feature paths only (no validation)
  ./check-prerequisites.sh --paths-only

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
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths and validate branch
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# If paths-only mode, output paths and exit (support JSON + paths-only combined)
if $PATHS_ONLY; then
    if $JSON_MODE; then
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","FEATURE_DIR":"%s","DESIGN":"%s","TASKS":"%s","KNOWLEDGE_DIR":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$FEATURE_DIR" "$DESIGN" "$TASKS" "$KNOWLEDGE_DIR"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "DESIGN: $DESIGN"
        echo "TASKS: $TASKS"
        echo "KNOWLEDGE_DIR: $KNOWLEDGE_DIR"
    fi
    exit 0
fi

# Validate required directories and files
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /minispec.design first to create the feature structure." >&2
    exit 1
fi

# Check for design.md if required
if $REQUIRE_DESIGN && [[ ! -f "$DESIGN" ]]; then
    echo "ERROR: design.md not found in $FEATURE_DIR" >&2
    echo "Run /minispec.design first to create the feature design." >&2
    exit 1
fi

# Check for tasks.md if required
if $REQUIRE_TASKS && [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /minispec.tasks first to create the task list." >&2
    exit 1
fi

# Build list of available documents
docs=()

# Check design and tasks
[[ -f "$DESIGN" ]] && docs+=("design.md")
[[ -f "$TASKS" ]] && docs+=("tasks.md")

# Check checklists directory (only if it exists and has files)
if [[ -d "$CHECKLISTS_DIR" ]] && [[ -n "$(ls -A "$CHECKLISTS_DIR" 2>/dev/null)" ]]; then
    docs+=("checklists/")
fi

# Check knowledge base
[[ -d "$KNOWLEDGE_DIR" ]] && docs+=("knowledge/")

# Output results
if $JSON_MODE; then
    # Build JSON array of documents
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi

    printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
else
    # Text output
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"

    # Show status of each potential document
    check_file "$DESIGN" "design.md"
    check_file "$TASKS" "tasks.md"
    check_dir "$CHECKLISTS_DIR" "checklists/"
    check_dir "$KNOWLEDGE_DIR" "knowledge/"
fi
