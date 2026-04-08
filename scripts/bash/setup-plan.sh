#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
SCAN_DEPTH=""
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --scan-depth)
            # Next argument is the depth value — handled below
            SCAN_DEPTH="__NEXT__"
            ;;
        --help|-h) 
            echo "Usage: $0 [--json] [--scan-depth N]"
            echo "  --json         Output results in JSON format"
            echo "  --scan-depth N Max directory depth for nested repo discovery (default: 2)"
            echo "  --help         Show this help message"
            exit 0 
            ;;
        *) 
            if [ "$SCAN_DEPTH" = "__NEXT__" ]; then
                SCAN_DEPTH="$arg"
            else
                ARGS+=("$arg")
            fi
            ;;
    esac
done
# Validate --scan-depth argument
if [ "$SCAN_DEPTH" = "__NEXT__" ]; then
    echo "ERROR: --scan-depth requires a positive integer value" >&2
    exit 1
fi
if [ -n "$SCAN_DEPTH" ]; then
    case "$SCAN_DEPTH" in
        ''|*[!0-9]*|0)
            echo "ERROR: --scan-depth must be a positive integer, got '$SCAN_DEPTH'" >&2
            exit 1
            ;;
    esac
fi

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
_paths_output=$(get_feature_paths) || { echo "ERROR: Failed to resolve feature paths" >&2; exit 1; }
eval "$_paths_output"
unset _paths_output

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template if it exists
TEMPLATE=$(resolve_template "plan-template" "$REPO_ROOT") || true
if [[ -n "$TEMPLATE" ]] && [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$IMPL_PLAN"
    echo "Copied plan template to $IMPL_PLAN"
else
    echo "Warning: Plan template not found"
    # Create a basic plan file if template doesn't exist
    touch "$IMPL_PLAN"
fi

# Discover nested independent git repositories (for AI agent to analyze)
NESTED_REPOS_JSON="[]"
if [ "$HAS_GIT" = true ]; then
    scan_depth="${SCAN_DEPTH:-2}"
    nested_repos=$(find_nested_git_repos "$REPO_ROOT" "$scan_depth")
    if [ -n "$nested_repos" ]; then
        NESTED_REPOS_JSON="["
        first=true
        while IFS= read -r nested_path; do
            [ -z "$nested_path" ] && continue
            nested_path="${nested_path%/}"
            rel_path="${nested_path#"$REPO_ROOT/"}"
            rel_path="${rel_path%/}"
            if [ "$first" = true ]; then
                first=false
            else
                NESTED_REPOS_JSON+=","
            fi
            NESTED_REPOS_JSON+="{\"path\":\"$(json_escape "$rel_path")\"}"
        done <<< "$nested_repos"
        NESTED_REPOS_JSON+="]"
    fi
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_spec "$FEATURE_SPEC" \
            --arg impl_plan "$IMPL_PLAN" \
            --arg specs_dir "$FEATURE_DIR" \
            --arg branch "$CURRENT_BRANCH" \
            --arg has_git "$HAS_GIT" \
            --argjson nested_repos "$NESTED_REPOS_JSON" \
            '{FEATURE_SPEC:$feature_spec,IMPL_PLAN:$impl_plan,SPECS_DIR:$specs_dir,BRANCH:$branch,HAS_GIT:$has_git,NESTED_REPOS:$nested_repos}'
    else
        printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s","NESTED_REPOS":%s}\n' \
            "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")" "$(json_escape "$HAS_GIT")" "$NESTED_REPOS_JSON"
    fi
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
    if [ "$NESTED_REPOS_JSON" != "[]" ]; then
        echo "NESTED_REPOS: $NESTED_REPOS_JSON"
    fi
fi

