#!/usr/bin/env bash
# Common functions and variables for all scripts

# Find repository root by searching upward for .specify directory
# This is the primary marker for spec-kit projects
find_specify_root() {
    local dir="${1:-$(pwd)}"
    # Normalize to absolute path to prevent infinite loop with relative paths
    # Use -- to handle paths starting with - (e.g., -P, -L)
    dir="$(cd -- "$dir" 2>/dev/null && pwd)" || return 1
    local prev_dir=""
    while true; do
        if [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        # Stop if we've reached filesystem root or dirname stops changing
        if [ "$dir" = "/" ] || [ "$dir" = "$prev_dir" ]; then
            break
        fi
        prev_dir="$dir"
        dir="$(dirname "$dir")"
    done
    return 1
}

# Get repository root, prioritizing .specify directory over git
# This prevents using a parent git repo when spec-kit is initialized in a subdirectory
get_repo_root() {
    # First, look for .specify directory (spec-kit's own marker)
    local specify_root
    if specify_root=$(find_specify_root); then
        echo "$specify_root"
        return
    fi

    # Fallback to git if no .specify found
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
        return
    fi

    # Final fallback to script location for non-git repos
    local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    (cd "$script_dir/../../.." && pwd)
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available at the spec-kit root (not parent)
    local repo_root=$(get_repo_root)
    if has_git; then
        git -C "$repo_root" rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local specs_dir="$repo_root/specs"

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

# Check if we have git available at the spec-kit root level
# Returns true only if git is installed and the repo root is inside a git work tree
# Handles both regular repos (.git directory) and worktrees/submodules (.git file)
has_git() {
    # First check if git command is available (before calling get_repo_root which may use git)
    command -v git >/dev/null 2>&1 || return 1
    local repo_root=$(get_repo_root)
    # Check if .git exists (directory or file for worktrees/submodules)
    [ -e "$repo_root/.git" ] || return 1
    # Verify it's actually a valid git work tree
    git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi

    return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

# Resolve formal workflow artifacts (PRD/AR/SEC), preferring feature-local files
# and falling back to docs/<TYPE>/<prefix>-*.md when present.
resolve_formal_doc_path() {
    local repo_root="$1"
    local feature_dir="$2"
    local local_filename="$3" # prd.md | ar.md | sec.md
    local docs_subdir="$4"    # PRD | AR | SEC
    local feature_basename
    feature_basename="$(basename "$feature_dir")"

    local local_path="$feature_dir/$local_filename"
    if [[ -f "$local_path" ]]; then
        echo "$local_path"
        return
    fi

    if [[ "$feature_basename" =~ ^([0-9]{3})- ]]; then
        local prefix="${BASH_REMATCH[1]}"
        local docs_dir="$repo_root/docs/$docs_subdir"
        if [[ -d "$docs_dir" ]]; then
            local matches=()
            local doc
            shopt -s nullglob
            for doc in "$docs_dir"/"$prefix"-*.md; do
                [[ -f "$doc" ]] && matches+=("$doc")
            done
            shopt -u nullglob

            if [[ ${#matches[@]} -gt 0 ]]; then
                printf '%s\n' "${matches[@]}" | sort | head -n 1
                return
            fi
        fi
    fi

    # Return feature-local default even when missing; callers may still test existence.
    echo "$local_path"
}

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
    local _repo_root
    local _current_branch
    local _has_git_repo
    local _feature_dir
    local _prd_path
    local _ard_path
    local _sec_path
    _repo_root=$(get_repo_root)
    _current_branch=$(get_current_branch)
    _has_git_repo="false"

    if has_git; then
        _has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    _feature_dir=$(find_feature_dir_by_prefix "$_repo_root" "$_current_branch")

    _prd_path="$(resolve_formal_doc_path "$_repo_root" "$_feature_dir" "prd.md" "PRD")"
    _ard_path="$(resolve_formal_doc_path "$_repo_root" "$_feature_dir" "ar.md" "AR")"
    _sec_path="$(resolve_formal_doc_path "$_repo_root" "$_feature_dir" "sec.md" "SEC")"

    # Assign directly to the calling scope (no eval needed)
    REPO_ROOT="$_repo_root"
    CURRENT_BRANCH="$_current_branch"
    HAS_GIT="$_has_git_repo"
    FEATURE_DIR="$_feature_dir"
    FEATURE_SPEC="$_feature_dir/spec.md"
    IMPL_PLAN="$_feature_dir/plan.md"
    TASKS="$_feature_dir/tasks.md"
    RESEARCH="$_feature_dir/research.md"
    DATA_MODEL="$_feature_dir/data-model.md"
    QUICKSTART="$_feature_dir/quickstart.md"
    CONTRACTS_DIR="$_feature_dir/contracts"
    PRD="$_prd_path"
    ARD="$_ard_path"
    SEC="$_sec_path"
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

# Read a value from .specify/config.json
# Usage: read_config_value "git_mode" [default_value] [config_file_path]
# Returns the value or default if not found
read_config_value() {
    local key="$1"
    local default_value="${2:-}"
    local config_file="${3:-}"

    if [[ -z "$config_file" ]]; then
        local repo_root
        repo_root=$(get_repo_root)
        config_file="$repo_root/.specify/config.json"
    fi

    if [[ ! -f "$config_file" ]]; then
        echo "$default_value"
        return
    fi

    local value=""
    if command -v jq &>/dev/null; then
        # Use jq if available (preferred)
        value=$(jq -r ".$key // empty" "$config_file" 2>/dev/null)
    else
        # Fallback: simple grep/sed for JSON values
        # Try quoted string first: "key": "value"
        value=$(grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$config_file" 2>/dev/null | \
            sed 's/.*:[[:space:]]*"\([^"]*\)".*/\1/' | head -1)

        # If no quoted value found, try unquoted (booleans/numbers): "key": true/false/123
        if [[ -z "$value" ]]; then
            value=$(grep -o "\"$key\"[[:space:]]*:[[:space:]]*[^,}\"]*" "$config_file" 2>/dev/null | \
                sed 's/.*:[[:space:]]*\([^,}]*\).*/\1/' | tr -d ' ' | head -1)
        fi
    fi

    if [[ -n "$value" ]]; then
        echo "$value"
    else
        echo "$default_value"
    fi
}

# Read a value from a feature-level .feature-config.json
# Usage: read_feature_config_value <key> [feature_dir] [default]
# Returns the value or default if file/key absent
read_feature_config_value() {
    local key="$1"
    local feature_dir="${2:-}"
    local default_value="${3:-}"

    if [[ -z "$feature_dir" ]]; then
        local repo_root
        repo_root=$(get_repo_root)
        local current_branch
        current_branch=$(get_current_branch)
        feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")
    fi

    local config_file="$feature_dir/.feature-config.json"
    read_config_value "$key" "$default_value" "$config_file"
}

# Scan spec file for risk-indicating keywords from the v1 catalog
# Usage: detect_risk_triggers <spec_file_path>
# Returns: space-separated list of matched trigger tokens (empty string if none)
# Exit code: 0 always (detection failure is non-fatal)
detect_risk_triggers() {
    local spec_file="$1"

    if [[ ! -f "$spec_file" ]]; then
        echo ""
        return 0
    fi

    local keywords=(
        "auth"
        "authentication"
        "authorization"
        "payment"
        "billing"
        "pii"
        "personal data"
        "personal information"
        "external api"
        "third-party"
        "third party"
        "delete"
        "destroy"
        "drop"
        "admin"
        "compliance"
        "regulation"
        "gdpr"
        "hipaa"
        "encryption"
        "secret"
        "credential"
        "token"
        "password"
    )

    local matched=()
    local content
    content=$(cat "$spec_file" 2>/dev/null) || { echo ""; return 0; }

    for keyword in "${keywords[@]}"; do
        if [[ "$keyword" =~ [[:space:]-] ]]; then
            # Multi-word or hyphenated: use plain case-insensitive match
            if echo "$content" | grep -q -i "$keyword" 2>/dev/null; then
                # Canonicalize multi-word/hyphenated keywords by replacing spaces with hyphens
                local canonical="${keyword// /-}"
                local exists=0
                for m in "${matched[@]}"; do
                    if [[ "$m" == "$canonical" ]]; then
                        exists=1
                        break
                    fi
                done
                if [[ $exists -eq 0 ]]; then
                    matched+=("$canonical")
                fi
            fi
        else
            # Single word: use word-boundary match
            if echo "$content" | grep -q -i -w "$keyword" 2>/dev/null; then
                local canonical="$keyword"
                local exists=0
                for m in "${matched[@]}"; do
                    if [[ "$m" == "$canonical" ]]; then
                        exists=1
                        break
                    fi
                done
                if [[ $exists -eq 0 ]]; then
                    matched+=("$canonical")
                fi
            fi
        fi
    done

    # Return space-separated deduplicated, canonicalized keywords
    local result=""
    for m in "${matched[@]}"; do
        if [[ -z "$result" ]]; then
            result="$m"
        else
            result="$result $m"
        fi
    done
    echo "$result"
    return 0
}

# Read execution mode from .feature-config.json, falling back to config default then "balanced"
# Usage: get_execution_mode [feature_dir]
# Returns: one of fast|balanced|detailed
get_execution_mode() {
    local feature_dir="${1:-}"

    # Try feature-level config first
    local mode
    mode=$(read_feature_config_value "mode" "$feature_dir" "")

    # Fall back to project default
    if [[ -z "$mode" ]]; then
        mode=$(read_config_value "defaultMode" "")
    fi

    # Final fallback
    if [[ -z "$mode" ]]; then
        mode="balanced"
    fi

    # Validate
    case "$mode" in
        fast|balanced|detailed)
            echo "$mode"
            ;;
        *)
            echo "ERROR: Unknown execution mode '$mode'. Valid values: fast, balanced, detailed. Re-run /speckit.specify to reset." >&2
            echo "balanced"
            return 1
            ;;
    esac
}
