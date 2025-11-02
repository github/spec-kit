#!/usr/bin/env bash
# Common functions and variables for all scripts

# Feature branch naming pattern (3 digits followed by hyphen)
readonly FEATURE_BRANCH_PATTERN='^[0-9]{3}-'

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                # Note: Cannot use FEATURE_BRANCH_PATTERN here as we need the capture group
                # to extract the numeric part for comparison
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi
    
    if [[ ! "$branch" =~ $FEATURE_BRANCH_PATTERN ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi

    return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/specs"

    # Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
        # If branch doesn't have numeric prefix, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    fi

    local prefix="${BASH_REMATCH[1]}"

    # Search for directories in specs/ that start with this prefix
    local matches=()
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$(basename "$dir")")
            fi
        done
    fi

    # Handle results
    if [[ ${#matches[@]} -eq 0 ]]; then
        # No match found - return the branch name path (will fail later with clear error)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # Exactly one match - perfect!
        echo "$specs_dir/${matches[0]}"
    else
        # Multiple matches - this shouldn't happen with proper naming convention
        echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
        echo "Please ensure only one spec directory exists per numeric prefix." >&2
        echo "$specs_dir/$branch_name"  # Return something to avoid breaking the script
    fi
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

# Check if current branch matches a spec directory, and offer to fix mismatches
#
# This function detects "orphaned" spec directories (directories with no matching git branch)
# and provides guidance to rename them to match the current branch.
#
# Returns:
#   0 - Success (no mismatch or check skipped)
#   1 - Mismatch detected, user action required
#
# Side effects:
#   Writes warning messages and remediation instructions to stderr
#
# Dependencies:
#   Requires git for orphan detection (gracefully skips if unavailable)
check_and_fix_spec_directory_mismatch() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)

    # Validate required variables
    if [[ -z "$repo_root" ]] || [[ -z "$current_branch" ]]; then
        return 0  # Skip check if we can't determine context
    fi

    local expected_dir="$repo_root/specs/$current_branch"

    # Skip check for non-git repos or main branch
    if [[ "$current_branch" == "main" ]] || ! has_git; then
        return 0
    fi

    # Skip check if branch doesn't follow feature branch naming convention
    if [[ ! "$current_branch" =~ $FEATURE_BRANCH_PATTERN ]]; then
        return 0
    fi

    # If expected directory exists, all good
    if [[ -d "$expected_dir" ]]; then
        return 0
    fi

    # Directory doesn't exist - look for orphaned spec directories
    local specs_dir="$repo_root/specs"
    local orphaned_dirs=()

    if [[ -d "$specs_dir" ]] && has_git; then
        # Get all existing branch names for efficient lookup (Bash 3.2 compatible)
        local existing_branches=$(git for-each-ref refs/heads/ --format='%(refname:short)' 2>/dev/null | tr '\n' '|')

        # Enable nullglob to handle empty directories gracefully
        local original_nullglob=$(shopt -p nullglob)
        shopt -s nullglob

        for dir in "$specs_dir"/*; do
            # Skip if not a directory or if it's a symlink
            if [[ -d "$dir" ]] && [[ ! -L "$dir" ]]; then
                local dirname=$(basename "$dir")

                # Skip hidden/special directories
                if [[ "$dirname" =~ ^\. ]]; then
                    continue
                fi

                # Check if this spec dir has no matching branch
                # Using grep for compatibility with older bash versions
                if ! echo "|${existing_branches}" | grep -q "|${dirname}|"; then
                    orphaned_dirs+=("$dirname")
                fi
            fi
        done

        # Restore original nullglob setting
        eval "$original_nullglob"
    fi

    # If we found exactly one orphaned directory, suggest renaming it
    if [[ ${#orphaned_dirs[@]} -eq 1 ]]; then
        local orphaned="${orphaned_dirs[0]}"
        echo "" >&2
        echo "WARNING: Branch '$current_branch' has no matching spec directory" >&2
        echo "   Found orphaned spec directory: specs/$orphaned" >&2
        echo "   This may be from a deleted or renamed branch." >&2
        echo "" >&2
        echo "   To fix this issue, run:" >&2
        echo "   git mv specs/$orphaned specs/$current_branch" >&2
        echo "" >&2
        return 1
    elif [[ ${#orphaned_dirs[@]} -gt 1 ]]; then
        echo "" >&2
        echo "WARNING: Branch '$current_branch' has no matching spec directory" >&2
        echo "   Found multiple orphaned spec directories:" >&2
        for dir in "${orphaned_dirs[@]}"; do
            echo "   - specs/$dir" >&2
        done
        echo "" >&2
        echo "   To fix this, manually rename the correct directory:" >&2
        echo "   git mv specs/<old-name> specs/$current_branch" >&2
        echo "" >&2
        return 1
    else
        # No spec directory exists at all - might be a new branch
        echo "" >&2
        echo "WARNING: No spec directory found for branch '$current_branch'" >&2
        echo "   Run /specify to create a new feature specification." >&2
        echo "" >&2
        return 1
    fi
}
