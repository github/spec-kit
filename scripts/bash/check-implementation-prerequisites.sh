#!/usr/bin/env bash
# check-implementation-prerequisites.sh
# Validates prerequisites for implementation command

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

# Get feature paths
eval $(get_feature_paths)

# Check if we're on a valid feature branch
if ! check_feature_branch "$CURRENT_BRANCH"; then
    if [[ "$JSON_MODE" == "true" ]]; then
        echo '{"error": "Not on a valid feature branch. Feature branches should be named like: username/proj-123.feature-name"}'
    else
        echo "ERROR: Not on a valid feature branch"
        echo "Current branch: $CURRENT_BRANCH"
        echo "Expected format: username/proj-123.feature-name"
    fi
    exit 1
fi

# Check for required files
MISSING_FILES=()
[[ ! -f "$IMPL_PLAN" ]] && MISSING_FILES+=("plan.md")
[[ ! -f "$TASKS" ]] && MISSING_FILES+=("tasks.md")

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    if [[ "$JSON_MODE" == "true" ]]; then
        printf '{"error": "Missing required files: %s"}\n' "${MISSING_FILES[*]}"
    else
        echo "ERROR: Missing required files: ${MISSING_FILES[*]}"
        echo "Run /plan and /tasks commands first"
        echo ""
        echo "Expected files:"
        echo "  - $IMPL_PLAN"
        echo "  - $TASKS"
    fi
    exit 1
fi

# Check for constitution
CONSTITUTION_PATH="$REPO_ROOT/memory/constitution.md"
[[ ! -f "$CONSTITUTION_PATH" ]] && CONSTITUTION_PATH=""

# Check for optional files (use variables from get_feature_paths)
AVAILABLE_DOCS=()
[[ -f "$FEATURE_SPEC" ]] && AVAILABLE_DOCS+=("spec.md")
[[ -f "$IMPL_PLAN" ]] && AVAILABLE_DOCS+=("plan.md")
[[ -f "$TASKS" ]] && AVAILABLE_DOCS+=("tasks.md")
[[ -f "$DATA_MODEL" ]] && AVAILABLE_DOCS+=("data-model.md")
[[ -f "$RESEARCH" ]] && AVAILABLE_DOCS+=("research.md")
[[ -f "$QUICKSTART" ]] && AVAILABLE_DOCS+=("quickstart.md")
[[ -d "$CONTRACTS_DIR" && -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]] && AVAILABLE_DOCS+=("contracts/")

# Check for recent validation
LAST_VALIDATION=""
if command -v git &>/dev/null; then
    LAST_VALIDATION=$(git log -1 --oneline --grep="validate" 2>/dev/null | head -1 || echo "")
fi

# Check git status for uncommitted changes
UNCOMMITTED_CHANGES=""
if command -v git &>/dev/null; then
    if ! git diff --quiet HEAD 2>/dev/null; then
        UNCOMMITTED_CHANGES="true"
    fi
fi

# Check if tests exist and are failing (TDD validation)
TEST_STATUS=""
if [[ -f "$REPO_ROOT/package.json" ]] && command -v npm &>/dev/null; then
    if npm test --silent >/dev/null 2>&1; then
        TEST_STATUS="passing"
    else
        TEST_STATUS="failing"
    fi
elif [[ -f "$REPO_ROOT/pyproject.toml" ]] || [[ -f "$REPO_ROOT/setup.py" ]] && command -v python &>/dev/null; then
    if python -m pytest --quiet >/dev/null 2>&1; then
        TEST_STATUS="passing"
    else
        TEST_STATUS="failing"
    fi
elif [[ -f "$REPO_ROOT/go.mod" ]] && command -v go &>/dev/null; then
    if go test ./... >/dev/null 2>&1; then
        TEST_STATUS="passing"
    else
        TEST_STATUS="failing"
    fi
fi

# Output results
if [[ "$JSON_MODE" == "true" ]]; then
    cat <<EOF
{
    "repo_root": "$REPO_ROOT",
    "feature_dir": "$FEATURE_DIR",
    "feature_spec": "$FEATURE_SPEC",
    "impl_plan": "$IMPL_PLAN",
    "tasks": "$TASKS",
    "branch": "$CURRENT_BRANCH",
    "constitution": "$CONSTITUTION_PATH",
    "data_model": "$DATA_MODEL",
    "contracts_dir": "$CONTRACTS_DIR",
    "research": "$RESEARCH",
    "quickstart": "$QUICKSTART",
    "available_docs": $(printf '%s\n' "${AVAILABLE_DOCS[@]}" | jq -R . | jq -s .),
    "last_validation": "$LAST_VALIDATION",
    "uncommitted_changes": "$UNCOMMITTED_CHANGES",
    "test_status": "$TEST_STATUS"
}
EOF
else
    echo "Implementation Prerequisites Check"
    echo "================================="
    echo "Repository: $REPO_ROOT"
    echo "Feature Branch: $CURRENT_BRANCH ✓"
    echo "Feature Directory: $FEATURE_DIR"
    echo ""
    echo "Required Files:"
    echo "  ✓ Plan: $IMPL_PLAN"
    echo "  ✓ Tasks: $TASKS"
    echo ""
    echo "Optional Files:"
    [[ -f "$FEATURE_SPEC" ]] && echo "  ✓ Specification: Found" || echo "  ✗ Specification: Not found"
    [[ -n "$CONSTITUTION_PATH" ]] && echo "  ✓ Constitution: Found" || echo "  ✗ Constitution: Not found"
    [[ -f "$DATA_MODEL" ]] && echo "  ✓ Data Model: Found" || echo "  ✗ Data Model: Not found"
    [[ -f "$RESEARCH" ]] && echo "  ✓ Research: Found" || echo "  ✗ Research: Not found"
    [[ -f "$QUICKSTART" ]] && echo "  ✓ Quickstart: Found" || echo "  ✗ Quickstart: Not found"
    [[ -d "$CONTRACTS_DIR" && -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]] && echo "  ✓ Contracts: Found" || echo "  ✗ Contracts: Not found"
    echo ""
    echo "Status Checks:"
    [[ -n "$LAST_VALIDATION" ]] && echo "  ✓ Recent validation: $LAST_VALIDATION" || echo "  ⚠ No recent validation found"
    [[ -n "$UNCOMMITTED_CHANGES" ]] && echo "  ⚠ Uncommitted changes detected" || echo "  ✓ Working directory clean"
    case "$TEST_STATUS" in
        "passing") echo "  ⚠ Tests passing (TDD expects failing tests initially)" ;;
        "failing") echo "  ✓ Tests failing (good for TDD red phase)" ;;
        "") echo "  ℹ No test framework detected" ;;
    esac
    echo ""
    echo "🚀 Ready to implement!"
    echo ""
    echo "Available docs: ${AVAILABLE_DOCS[*]}"
fi