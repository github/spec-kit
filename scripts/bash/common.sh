#!/usr/bin/env bash
# Common functions and variables for MiniSpec workflow scripts

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if MINISPEC_FEATURE environment variable is set
    if [[ -n "${MINISPEC_FEATURE:-}" ]]; then
        echo "$MINISPEC_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/.minispec/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
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
        echo "[minispec] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    # Block work on protected branches
    case "$branch" in
        main|master|develop|production)
            echo "ERROR: Cannot run on protected branch '$branch'. Create a feature branch first." >&2
            return 1
            ;;
    esac

    return 0
}

get_feature_dir() { echo "$1/.minispec/specs/$2"; }

# Find feature directory by numeric prefix or exact branch match
# For numbered branches (e.g., 004-fix-bug), matches by prefix to allow multiple branches per spec
# For other branches (e.g., issue/25_get_product_details), sanitizes to a safe directory name
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/.minispec/specs"

    # If branch has numeric prefix (e.g., "004-whatever"), search by prefix
    if [[ "$branch_name" =~ ^([0-9]{3})- ]]; then
        local prefix="${BASH_REMATCH[1]}"

        local matches=()
        if [[ -d "$specs_dir" ]]; then
            for dir in "$specs_dir"/"$prefix"-*; do
                if [[ -d "$dir" ]]; then
                    matches+=("$(basename "$dir")")
                fi
            done
        fi

        if [[ ${#matches[@]} -eq 1 ]]; then
            echo "$specs_dir/${matches[0]}"
            return
        elif [[ ${#matches[@]} -gt 1 ]]; then
            echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
            echo "Please ensure only one spec directory exists per numeric prefix." >&2
            echo "$specs_dir/$branch_name"
            return
        fi
    fi

    # Sanitize branch name to a valid directory name (replace / with -)
    local safe_name="${branch_name//\//-}"
    echo "$specs_dir/$safe_name"
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
DESIGN='$feature_dir/design.md'
TASKS='$feature_dir/tasks.md'
CHECKLISTS_DIR='$feature_dir/checklists'
MINISPEC_DIR='$repo_root/.minispec'
MEMORY_DIR='$repo_root/.minispec/memory'
KNOWLEDGE_DIR='$repo_root/.minispec/knowledge'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

