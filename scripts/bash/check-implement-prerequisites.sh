#!/usr/bin/env bash
# Check that tasks.md exist and find optional design documents
# Usage: ./check-implement-prerequisites.sh [--json]

set -e

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json]"; exit 0 ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths
eval $(get_feature_paths)

# Check if on feature branch
check_feature_branch "$CURRENT_BRANCH" || exit 1

# Check if feature directory exists
if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR"
    echo "Run /specify first to create the feature structure."
    exit 1
fi

# Check for tasks (required)
if [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR"
    echo "Run /tasks first to create the tasks."
    exit 1
fi

if $JSON_MODE; then
    # Build JSON array of available docs that actually exist
    docs=()
    [[ -f "$IMPL_PLAN" ]] && docs+=("plan.md")
    [[ -f "$RESEARCH" ]] && docs+=("research.md")
    [[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")
    [[ -f "$TASKS" ]] && docs+=("tasks.md")
    ([[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]) && docs+=("contracts/")
    [[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")
    # join array into JSON
    json_docs=$(printf '"%s",' "${docs[@]}")
    json_docs="[${json_docs%,}]"
    printf '{"FEATURE_DIR":"%s", "AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
else
    # List available design documents (optional)
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"

    # Use common check functions
    check_file "$TASKS" "tasks.md"
    check_file "$IMPL_PLAN" "plan.md"
    check_file "$RESEARCH" "research.md"
    check_file "$DATA_MODEL" "data-model.md"
    check_dir "$CONTRACTS_DIR" "contracts/"
    check_file "$QUICKSTART" "quickstart.md"
fi
