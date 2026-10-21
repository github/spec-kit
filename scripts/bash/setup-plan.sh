#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'" >&2
            exit 1
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template if plan doesn't already exist
if [[ -f "$IMPL_PLAN" ]]; then
    if $JSON_MODE; then
        echo "Plan already exists at $IMPL_PLAN, skipping template copy" >&2
    else
        echo "Plan already exists at $IMPL_PLAN, skipping template copy"
    fi
else
    template_file=$(mktemp)
    trap 'rm -f "$template_file"' EXIT
    if resolve_template_content "plan-template" "$REPO_ROOT" > "$template_file"; then
        if ! file_has_non_whitespace_content "$template_file"; then
            echo "ERROR: Plan template is empty; no new plan.md was created." >&2
            echo "Restore a valid plan template and rerun plan setup." >&2
            exit 1
        fi
        cat "$template_file" > "$IMPL_PLAN"
        if $JSON_MODE; then
            echo "Copied plan template to $IMPL_PLAN" >&2
        else
            echo "Copied plan template to $IMPL_PLAN"
        fi
    else
        resolve_status=$?
        if [ "$resolve_status" -ne 1 ]; then
            exit "$resolve_status"
        fi
        echo "ERROR: Plan template not found; no new plan.md was created." >&2
        echo "Restore a valid plan template and rerun plan setup." >&2
        exit 1
    fi
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_spec "$FEATURE_SPEC" \
            --arg impl_plan "$IMPL_PLAN" \
            --arg feature_dir "$FEATURE_DIR" \
            --arg branch "$CURRENT_BRANCH" \
            '{FEATURE_SPEC:$feature_spec,IMPL_PLAN:$impl_plan,FEATURE_DIR:$feature_dir,BRANCH:$branch}'
    else
        printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","FEATURE_DIR":"%s","BRANCH":"%s"}\n' \
            "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")"
    fi
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
fi
