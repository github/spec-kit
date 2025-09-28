#!/usr/bin/env bash

# Context Engineering Kit prerequisite checker

set -e

JSON_MODE=false
REQUIRE_TASKS=false
INCLUDE_TASKS=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --require-tasks) REQUIRE_TASKS=true ;;
        --include-tasks) INCLUDE_TASKS=true ;;
        --paths-only) PATHS_ONLY=true ;;
        --help|-h)
            cat <<'EOF'
Usage: check-prerequisites.sh [OPTIONS]

Ensure required artifacts exist for the active context engineering workflow.

OPTIONS:
  --json              Return JSON output
  --require-tasks     Fail when tasks.md is missing
  --include-tasks     Include tasks.md in AVAILABLE_DOCS (if present)
  --paths-only        Emit paths only, skip validation
  --help, -h          Show this help message
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="${BASH_SOURCE[0]%/*}"
SCRIPT_DIR="$(cd "$SCRIPT_DIR"; pwd)"
source "$SCRIPT_DIR/common.sh"

eval $(get_feature_paths)
check_feature_branch "$FEATURE_NAME" "$HAS_GIT" || exit 1

if $PATHS_ONLY; then
    if $JSON_MODE; then
        printf '{"REPO_ROOT":"%s","FEATURE":"%s","WORKFLOW":"%s","FEATURE_DIR":"%s","PRIMARY_FILE":"%s","PLAN_FILE":"%s","RESEARCH_FILE":"%s","TASKS_FILE":"%s","PRP_FILE":"%s"}\n' \
            "$REPO_ROOT" "$FEATURE_NAME" "$WORKFLOW" "$FEATURE_DIR" "$PRIMARY_FILE" "$PLAN_FILE" "$RESEARCH_FILE" "$TASKS_FILE" "$PRP_FILE"
    else
        cat <<EOF
REPO_ROOT: $REPO_ROOT
FEATURE: $FEATURE_NAME
WORKFLOW: $WORKFLOW
FEATURE_DIR: $FEATURE_DIR
PRIMARY_FILE: $PRIMARY_FILE
PLAN_FILE: $PLAN_FILE
RESEARCH_FILE: $RESEARCH_FILE
TASKS_FILE: $TASKS_FILE
EOF
        [[ -n "$PRP_FILE" ]] && echo "PRP_FILE: $PRP_FILE"
    fi
    exit 0
fi

if [[ -n "$FEATURE_DIR" && ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /specify to bootstrap the workflow artifacts." >&2
    exit 1
fi

if [[ ! -f "$PRIMARY_FILE" ]]; then
    echo "ERROR: Primary context file missing at $PRIMARY_FILE" >&2
    echo "Run /specify to regenerate the initial artifact." >&2
    exit 1
fi

if [[ ! -f "$PLAN_FILE" ]]; then
    case "$WORKFLOW" in
        free-style)
            echo "ERROR: Plan file missing at $PLAN_FILE" >&2
            echo "Run /create-plan before continuing." >&2
            ;;
        prp)
            echo "ERROR: Plan file missing at $PLAN_FILE" >&2
            echo "Run /execute-prp to derive the execution plan." >&2
            ;;
        all-in-one)
            echo "ERROR: Plan file missing at $PLAN_FILE" >&2
            echo "Run /context-engineer to update the plan section." >&2
            ;;
    esac
    exit 1
fi

if $REQUIRE_TASKS && [[ ! -f "$TASKS_FILE" ]]; then
    echo "ERROR: tasks.md missing for $FEATURE_NAME" >&2
    echo "Capture tasks from your plan or PRP before implementation." >&2
    exit 1
fi

docs=()
[[ -f "$PRIMARY_FILE" ]] && docs+=("$(basename "$PRIMARY_FILE")")
[[ -f "$PLAN_FILE" ]] && docs+=("$(basename "$PLAN_FILE")")
[[ -f "$RESEARCH_FILE" ]] && docs+=("$(basename "$RESEARCH_FILE")")
if [[ -n "$PRP_FILE" && -f "$PRP_FILE" ]]; then
    docs+=("$(basename "$PRP_FILE")")
fi
if $INCLUDE_TASKS && [[ -f "$TASKS_FILE" ]]; then
    docs+=("tasks.md")
fi

if $JSON_MODE; then
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi
    printf '{"FEATURE_DIR":"%s","WORKFLOW":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$WORKFLOW" "$json_docs"
else
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "WORKFLOW:$WORKFLOW"
    echo "AVAILABLE_DOCS:"
    for doc in "${docs[@]}"; do
        echo "  ✓ $doc"
    done
    if $INCLUDE_TASKS && [[ ! -f "$TASKS_FILE" ]]; then
        echo "  ✗ tasks.md"
    fi
fi