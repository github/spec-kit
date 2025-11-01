#!/usr/bin/env bash
# (Moved to scripts/bash/) Common functions and variables for all scripts

# Source workspace discovery functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/workspace-discovery.sh"

# Get repo root (workspace-aware and worktree-aware)
# Returns parent repo root if in worktree, else repo toplevel
# Use this for convention matching - must use parent repo name, not worktree dir name
get_repo_root() {
    local git_dir=$(git rev-parse --git-dir 2>/dev/null)
    local git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)

    if [[ -n "$git_dir" ]] && [[ "$git_dir" != "$git_common_dir" ]]; then
        # In worktree, return parent repo root
        dirname "$git_common_dir"
    else
        # In parent repo or not in git repo
        git rev-parse --show-toplevel 2>/dev/null || echo ""
    fi
}

# Get current branch for a specific repo
# Usage: get_current_branch [repo_path]
get_current_branch() {
    local repo_path="${1:-.}"
    if [[ "$repo_path" == "." ]]; then
        git rev-parse --abbrev-ref HEAD 2>/dev/null
    else
        git_exec "$repo_path" rev-parse --abbrev-ref HEAD 2>/dev/null
    fi
}

check_feature_branch() {
    local branch="$1"
    # Support three patterns:
    # 1. username/jira-123.feature-name (with JIRA key and prefix)
    # 2. username/feature-name (with prefix, no JIRA)
    # 3. feature-name (no prefix, for hcnimi)
    # 4. jira-123.feature-name (with JIRA key, no prefix)
    if [[ "$branch" =~ ^[a-zA-Z0-9_-]+/([a-z]+-[0-9]+\.)?[a-z0-9._-]+$ ]] || \
       [[ "$branch" =~ ^([a-z]+-[0-9]+\.)?[a-z0-9._-]+$ ]]; then
        return 0
    else
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like:" >&2
        echo "  username/jira-123.feature-name (with JIRA key and prefix)" >&2
        echo "  username/feature-name (with prefix, no JIRA)" >&2
        echo "  feature-name (no prefix, for hcnimi)" >&2
        echo "  jira-123.feature-name (with JIRA key, no prefix)" >&2
        return 1
    fi
}

get_feature_id() {
    local branch="$1"
    # Extract feature ID from branch name
    # With prefix: username/jira-123.feature-name → jira-123.feature-name
    # With prefix: username/feature-name → feature-name
    # No prefix: feature-name → feature-name
    # No prefix: jira-123.feature-name → jira-123.feature-name
    if [[ "$branch" == *"/"* ]]; then
        # Has prefix - extract part after slash
        echo "$branch" | sed 's|.*/||'
    else
        # No prefix - use entire branch name
        echo "$branch"
    fi
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

# Get feature paths in workspace mode
# Usage: get_feature_paths_workspace <workspace_root> <feature_id> <target_repo>
get_feature_paths_workspace() {
    local workspace_root="$1"
    local feature_id="$2"
    local target_repo="$3"
    local current_branch="$4"

    local specs_dir="$workspace_root/specs"
    local capability_id=$(get_capability_id_from_branch "$current_branch")
    local repo_path=$(get_repo_path "$workspace_root" "$target_repo")

    # Capability mode
    if [[ -n "$capability_id" ]]; then
        local parent_feature_id=$(get_parent_feature_id "$current_branch")
        local parent_feature_dir="$specs_dir/$parent_feature_id"

        # Find capability directory matching pattern cap-XXX-*/
        local capability_dir=""
        if [[ -d "$parent_feature_dir" ]]; then
            for dir in "$parent_feature_dir/$capability_id"-*/; do
                if [[ -d "$dir" ]]; then
                    capability_dir="${dir%/}"
                    break
                fi
            done
        fi

        if [[ -z "$capability_dir" ]]; then
            capability_dir="$parent_feature_dir/$capability_id"
        fi

        cat <<EOF
WORKSPACE_ROOT='$workspace_root'
TARGET_REPO='$target_repo'
REPO_PATH='$repo_path'
REPO_ROOT='$repo_path'
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
        # Parent feature mode
        local feature_dir="$specs_dir/$feature_id"

        cat <<EOF
WORKSPACE_ROOT='$workspace_root'
TARGET_REPO='$target_repo'
REPO_PATH='$repo_path'
REPO_ROOT='$repo_path'
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

# Smart get_feature_paths that handles both workspace and single-repo modes
# Usage: get_feature_paths_smart [target_repo]
get_feature_paths_smart() {
    local target_repo="$1"
    local workspace_root=$(get_workspace_root)

    if [[ -n "$workspace_root" ]]; then
        # Workspace mode
        local current_branch=$(get_current_branch)
        local feature_id=$(get_feature_id "$current_branch")

        # If no target repo specified, try to infer from spec name
        if [[ -z "$target_repo" ]]; then
            local repos=($(get_target_repos_for_spec "$workspace_root" "$feature_id"))
            if [[ ${#repos[@]} -eq 1 ]]; then
                target_repo="${repos[0]}"
            elif [[ ${#repos[@]} -gt 1 ]]; then
                # Multiple repos - use first one as default
                target_repo="${repos[0]}"
                echo "WARNING: Multiple target repos found, using $target_repo" >&2
            else
                echo "ERROR: No target repo found for spec: $feature_id" >&2
                return 1
            fi
        fi

        get_feature_paths_workspace "$workspace_root" "$feature_id" "$target_repo" "$current_branch"
    else
        # Single-repo mode - use existing function
        get_feature_paths
    fi
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
