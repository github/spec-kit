#!/usr/bin/env bash
# check-task-prerequisites.sh
# Validates prerequisites for tasks generation command

set -euo pipefail

# Parse arguments
JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json]"; exit 0 ;;
        *) ;;
    esac
done

# Get script directory and source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get feature paths (now capability-aware)
eval $(get_feature_paths)

# Check if we're on a valid feature branch
if ! check_feature_branch "$CURRENT_BRANCH"; then
    if [[ "$JSON_MODE" == "true" ]]; then
        echo '{"error": "Not on a valid feature branch. Feature branches should be named like: username/proj-123.feature-name or username/proj-123.feature-name-cap-001"}'
    else
        echo "ERROR: Not on a valid feature branch"
        echo "Current branch: $CURRENT_BRANCH"
        echo "Expected format: username/proj-123.feature-name or username/proj-123.feature-name-cap-001"
    fi
    exit 1
fi

# Check for required files
MISSING_FILES=()
[[ ! -f "$IMPL_PLAN" ]] && MISSING_FILES+=("plan.md")

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    if [[ "$JSON_MODE" == "true" ]]; then
        printf '{"error": "Missing required files: %s. Run /plan command first"}\n' "${MISSING_FILES[*]}"
    else
        echo "ERROR: Missing required files: ${MISSING_FILES[*]}"
        echo "Run /plan command first"
        echo ""
        echo "Expected file:"
        echo "  - $IMPL_PLAN"
    fi
    exit 1
fi

# Build list of available design documents
AVAILABLE_DOCS=()
[[ -f "$FEATURE_SPEC" ]] && AVAILABLE_DOCS+=("spec.md")
[[ -f "$IMPL_PLAN" ]] && AVAILABLE_DOCS+=("plan.md")
[[ -f "$DATA_MODEL" ]] && AVAILABLE_DOCS+=("data-model.md")
[[ -f "$RESEARCH" ]] && AVAILABLE_DOCS+=("research.md")
[[ -f "$QUICKSTART" ]] && AVAILABLE_DOCS+=("quickstart.md")
[[ -d "$CONTRACTS_DIR" && -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]] && AVAILABLE_DOCS+=("contracts/")

# Output results
if [[ "$JSON_MODE" == "true" ]]; then
    cat <<EOF
{
    "repo_root": "$REPO_ROOT",
    "feature_dir": "$FEATURE_DIR",
    "plan_path": "$IMPL_PLAN",
    "branch": "$CURRENT_BRANCH",
    "capability_id": "$CAPABILITY_ID",
    "parent_feature_dir": "$PARENT_FEATURE_DIR",
    "feature_spec": "$FEATURE_SPEC",
    "data_model": "$DATA_MODEL",
    "contracts_dir": "$CONTRACTS_DIR",
    "research": "$RESEARCH",
    "quickstart": "$QUICKSTART",
    "available_docs": $(printf '%s\n' "${AVAILABLE_DOCS[@]}" | jq -R . | jq -s .)
}
EOF
else
    echo "Task Generation Prerequisites Check"
    echo "===================================="
    echo "Repository: $REPO_ROOT"
    echo "Feature Branch: $CURRENT_BRANCH "
    if [[ -n "$CAPABILITY_ID" ]]; then
        echo "Capability Mode: $CAPABILITY_ID (atomic PR workflow)"
        echo "Parent Feature: $PARENT_FEATURE_DIR"
    fi
    echo "Feature Directory: $FEATURE_DIR"
    echo ""
    echo "Required Files:"
    echo "   Plan: $IMPL_PLAN"
    echo ""
    echo "Optional Design Documents:"
    [[ -f "$FEATURE_SPEC" ]] && echo "   Specification: Found" || echo "   Specification: Not found"
    [[ -f "$DATA_MODEL" ]] && echo "   Data Model: Found" || echo "   Data Model: Not found"
    [[ -f "$RESEARCH" ]] && echo "   Research: Found" || echo "   Research: Not found"
    [[ -f "$QUICKSTART" ]] && echo "   Quickstart: Found" || echo "   Quickstart: Not found"
    [[ -d "$CONTRACTS_DIR" && -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]] && echo "   Contracts: Found" || echo "   Contracts: Not found"
    echo ""
    echo "=€ Ready to generate tasks!"
    echo ""
    echo "Available docs: ${AVAILABLE_DOCS[*]}"
fi
