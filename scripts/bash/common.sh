#!/usr/bin/env bash
# (Moved to scripts/bash/) Common functions and variables for all scripts

get_repo_root() { git rev-parse --show-toplevel; }
get_current_branch() { git rev-parse --abbrev-ref HEAD; }

check_feature_branch() {
    local branch="$1"
    if [[ ! "$branch" =~ ^[a-zA-Z0-9_-]+/[a-zA-Z]+-[0-9]+\. ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: username/JIRA-123.anything" >&2
        return 1
    fi; return 0
}

get_feature_id() {
    local branch="$1"
    echo "$branch" | sed 's|.*/||'  # Extract JIRA-123.feature-name part
}

get_feature_dir() {
    local feature_id=$(get_feature_id "$2")
    echo "$1/specs/$feature_id"
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local feature_id=$(get_feature_id "$current_branch")
    local specs_dir="$repo_root/specs"

    # Convert PROJ-123.feature-name to PROJ-123-feature-name for flat file structure
    local file_prefix=$(echo "$feature_id" | sed 's/\./-/')

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
FEATURE_DIR='$specs_dir'
FEATURE_SPEC='$specs_dir/${file_prefix}.md'
IMPL_PLAN='$specs_dir/${file_prefix}-plan.md'
TASKS='$specs_dir/${file_prefix}-tasks.md'
RESEARCH='$specs_dir/${file_prefix}-research.md'
DATA_MODEL='$specs_dir/${file_prefix}-data-model.md'
QUICKSTART='$specs_dir/${file_prefix}-quickstart.md'
CONTRACTS_DIR='$specs_dir/${file_prefix}-contracts'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
