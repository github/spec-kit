#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

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
            ARGS+=("$arg")
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

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Derive RFC path
RFC_FILE="$FEATURE_DIR/rfc.md"

# Copy RFC template if it exists
TEMPLATE=$(resolve_template "rfc-template" "$REPO_ROOT") || true
if [[ -n "$TEMPLATE" ]] && [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$RFC_FILE"
    echo "Copied RFC template to $RFC_FILE"
else
    echo "Warning: RFC template not found"
    touch "$RFC_FILE"
fi

# Output results
if $JSON_MODE; then
    if has_jq; then
        jq -cn \
            --arg feature_spec "$FEATURE_SPEC" \
            --arg rfc_file "$RFC_FILE" \
            --arg specs_dir "$FEATURE_DIR" \
            --arg branch "$CURRENT_BRANCH" \
            --arg has_git "$HAS_GIT" \
            '{FEATURE_SPEC:$feature_spec,RFC_FILE:$rfc_file,SPECS_DIR:$specs_dir,BRANCH:$branch,HAS_GIT:$has_git}'
    else
        printf '{"FEATURE_SPEC":"%s","RFC_FILE":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
            "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$RFC_FILE")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")" "$(json_escape "$HAS_GIT")"
    fi
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "RFC_FILE: $RFC_FILE"
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
