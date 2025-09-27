#!/usr/bin/env bash
# Common functions and variables for all scripts

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        local cand
        cand=$(cd "$script_dir/../../.." && pwd)
        # If we resolved inside the .specs folder, return its parent
        if [[ "$(basename "$cand")" == ".specs" ]]; then
            dirname "$cand"
        else
            echo "$cand"
        fi
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
    
    # For non-git repos, try to find the latest feature directory (search nested)
    local repo_root=$(get_repo_root)
    local roots=("$repo_root/.specs/.specify/specs" "$repo_root/specs")
    # include configured roots if available
    if [[ -x "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh" ]]; then
        eval "$($(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh)"
        IFS=',' read -r -a cfg_roots <<< "${LAYOUT_SPEC_ROOTS:-}"
        for r in "${cfg_roots[@]}"; do roots+=("$repo_root/$r"); done
    fi
    local latest_feature=""; local highest=0
    for base in "${roots[@]}"; do
        [[ -d "$base" ]] || continue
        while IFS= read -r -d '' d; do
            local name="$(basename "$d")"
            if [[ "$name" =~ ^([0-9]{3})- ]]; then
                local n=$((10#${BASH_REMATCH[1]}))
                if (( n > highest )); then highest=$n; latest_feature="$name"; fi
            fi
        done < <(find "$base" -type d -maxdepth 4 -mindepth 1 -print0 2>/dev/null)
    done
    if [[ -n "$latest_feature" ]]; then echo "$latest_feature"; return; fi
    
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
    
    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi
    
    return 0
}

get_feature_dir() {
    local repo_root="$1"
    local branch="$2"

    # Load layout config (env assignments)
    if [[ -x "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh" ]]; then
        eval "$($(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh)"
    fi

    # Helper: first existing spec root or default to first configured
    IFS=',' read -r -a ROOTS_ARR <<< "${LAYOUT_SPEC_ROOTS:-.specs/.specify/specs,specs}"
    local chosen_root=""
    for r in "${ROOTS_ARR[@]}"; do
        local candidate="$repo_root/${r}"
        if [[ -d "$candidate" ]]; then
            chosen_root="$candidate"; break
        fi
    done
    if [[ -z "$chosen_root" ]]; then
        chosen_root="$repo_root/${ROOTS_ARR[0]}"
    fi

    # If an existing folder already matches the branch anywhere (search), honor it
    local found=$(find "$chosen_root" -type d -name "$branch" -print -quit 2>/dev/null || true)
    if [[ -n "$found" ]]; then
        echo "$found"; return
    fi

    # Build new path based on folder strategy. Allow override via SPECIFY_PRODUCT/SPECIFY_EPIC env.
    local epic="${SPECIFY_EPIC:-uncategorized}"
    local product="${SPECIFY_PRODUCT:-default}"
    # slugify
    epic=$(echo "$epic" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/-\+/-/g; s/^-//; s/-$//')
    product=$(echo "$product" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/-\+/-/g; s/^-//; s/-$//')

    case "${LAYOUT_FOLDER_STRATEGY:-epic}" in
        product)
            echo "$chosen_root/products/$product/epics/$epic/$branch" ;;
        epic)
            echo "$chosen_root/epics/$epic/$branch" ;;
        flat|*)
            echo "$chosen_root/$branch" ;;
    esac
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"
    
    if has_git; then
        has_git_repo="true"
    fi
    
    local specs_root="$repo_root/.specs"
    mkdir -p "$specs_root/.specify"
    # Load layout
    if [[ -x "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh" ]]; then
        eval "$($(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/read-layout.sh)"
    fi
    local feature_dir=$(get_feature_dir "$repo_root" "$current_branch")
    
    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/'"${LAYOUT_FILES_FPRD:-fprd.md}"
IMPL_PLAN='$feature_dir/'"${LAYOUT_FILES_DESIGN:-design.md}"
TASKS='$feature_dir/'"${LAYOUT_FILES_TASKS:-tasks.md}"
RESEARCH='$feature_dir/'"${LAYOUT_FILES_RESEARCH:-research.md}"
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/'"${LAYOUT_FILES_QUICKSTART:-quickstart.md}"
CONTRACTS_DIR='$feature_dir/'"${LAYOUT_FILES_CONTRACTS_DIR:-contracts}"
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
