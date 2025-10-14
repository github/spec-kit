#!/usr/bin/env bash
# (Moved to scripts/bash/) Common functions and variables for all scripts

get_repo_root() { git rev-parse --show-toplevel; }
get_current_branch() { git rev-parse --abbrev-ref HEAD; }

check_feature_branch() {
    local branch="$1"
    # Support both patterns:
    # 1. username/jira-123.feature-name (with JIRA key)
    # 2. username/feature-name (without JIRA key)
    if [[ ! "$branch" =~ ^[a-zA-Z0-9_-]+/([a-z]+-[0-9]+\.)?[a-z0-9._-]+$ ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like:" >&2
        echo "  username/jira-123.feature-name (with JIRA key)" >&2
        echo "  username/feature-name (without JIRA key)" >&2
        return 1
    fi; return 0
}

get_feature_id() {
    local branch="$1"
    # Extract feature ID from branch name (everything after username/)
    # Examples: username/jira-123.feature-name → jira-123.feature-name
    #           username/feature-name → feature-name
    echo "$branch" | sed 's|.*/||'
}

get_feature_dir() {
    local feature_id=$(get_feature_id "$2")
    echo "$1/specs/$feature_id"
}

# Extract capability ID from branch name if present
# Example: username/jira-123.feature-cap-001 → cap-001
get_capability_id_from_branch() {
    local branch="$1"
    if [[ "$branch" =~ -cap-[0-9]{3}[a-z]?$ ]]; then
        echo "$branch" | sed -E 's/.*-(cap-[0-9]{3}[a-z]?)$/\1/'
    else
        echo ""
    fi
}

# Extract parent feature ID from capability branch
# Example: username/jira-123.feature-name-cap-001 → jira-123.feature-name
get_parent_feature_id() {
    local branch="$1"
    local feature_id=$(get_feature_id "$branch")
    # Remove -cap-XXX suffix if present
    echo "$feature_id" | sed -E 's/-cap-[0-9]{3}[a-z]?$//'
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local capability_id=$(get_capability_id_from_branch "$current_branch")
    local specs_dir="$repo_root/specs"

    # Capability mode: branch pattern username/jira-123.feature-name-cap-001
    if [[ -n "$capability_id" ]]; then
        local parent_feature_id=$(get_parent_feature_id "$current_branch")
        local parent_feature_dir="$specs_dir/$parent_feature_id"

        # Find capability directory matching pattern cap-XXX-*/
        local capability_dir=""
        if [[ -d "$parent_feature_dir" ]]; then
            # Look for directory matching cap-XXX-*
            for dir in "$parent_feature_dir/$capability_id"-*/; do
                if [[ -d "$dir" ]]; then
                    capability_dir="${dir%/}"  # Remove trailing slash
                    break
                fi
            done
        fi

        # Fallback to generic path if directory not found yet
        if [[ -z "$capability_dir" ]]; then
            capability_dir="$parent_feature_dir/$capability_id"
        fi

        cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
CAPABILITY_ID='$capability_id'
PARENT_FEATURE_ID='$parent_feature_id'
PARENT_FEATURE_DIR='$parent_feature_dir'
FEATURE_DIR='$capability_dir'
FEATURE_SPEC='$capability_dir/spec.md'
IMPL_PLAN='$capability_dir/plan.md'
TASKS='$capability_dir/tasks.md'
RESEARCH='$capability_dir/research.md'
DATA_MODEL='$capability_dir/data-model.md'
QUICKSTART='$capability_dir/quickstart.md'
CONTRACTS_DIR='$capability_dir/contracts'
EOF
    else
        # Parent feature mode: standard branch pattern
        local feature_id=$(get_feature_id "$current_branch")
        local feature_dir="$specs_dir/$feature_id"

        cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
CAPABILITY_ID=''
PARENT_FEATURE_ID=''
PARENT_FEATURE_DIR=''
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
EOF
    fi
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
