#!/usr/bin/env bash
# Common helpers shared across Context Engineering Kit scripts

get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

read_workflow() {
    local repo_root="$1"
    local config_path="$repo_root/.context-eng/workflow.json"
    local workflow="free-style"
    if [[ -f "$config_path" ]]; then
        workflow=$(grep -E '"workflow"' "$config_path" | sed -E 's/.*"workflow"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' | tr -d '\r')
        if [[ -z "$workflow" ]]; then
            workflow="free-style"
        fi
    fi
    echo "$workflow"
}

get_current_feature() {
    if [[ -n "${CONTEXT_FEATURE:-}" ]]; then
        echo "$CONTEXT_FEATURE"
        return
    fi
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        local branch=$(git rev-parse --abbrev-ref HEAD)
        if [[ "$branch" != "HEAD" ]]; then
            echo "$branch"
            return
        fi
    fi
    # Fallback to most recent specs directory entry
    local repo_root=$(get_repo_root)
    local candidate_dir=""
    local highest=0
    for search_dir in "$repo_root/specs" "$repo_root/context-eng/prp" "$repo_root/context-eng/all-in-one"; do
        [[ -d "$search_dir" ]] || continue
        for dir in "$search_dir"/*; do
            [[ -d "$dir" ]] || continue
            local base=$(basename "$dir")
            if [[ "$base" =~ ^([0-9]{3})- ]]; then
                local number=${BASH_REMATCH[1]}
                number=$((10#$number))
                if (( number > highest )); then
                    highest=$number
                    candidate_dir="$base"
                fi
            fi
        done
    done
    if [[ -n "$candidate_dir" ]]; then
        echo "$candidate_dir"
    else
        echo "000-unspecified"
    fi
}

has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[cek] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi
    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a context feature branch. Current branch: $branch" >&2
        echo "Use branches like 001-feature-name." >&2
        return 1
    fi
    return 0
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local workflow=$(read_workflow "$repo_root")
    local feature_name=$(get_current_feature)
    local has_git_repo="false"
    [[ -n "${CONTEXT_FEATURE:-}" ]] && feature_name="$CONTEXT_FEATURE"
    if has_git; then
        has_git_repo="true"
    fi

    local context_dir="$repo_root/.context-eng"
    local checklist_template="$context_dir/checklists/full-implementation-checklist.md"

    local feature_dir=""
    local primary_file=""
    local plan_file=""
    local research_file=""
    local tasks_file=""
    local prp_file=""
    local initial_file=""

    case "$workflow" in
        free-style)
            feature_dir="$repo_root/specs/$feature_name"
            primary_file="$feature_dir/context-spec.md"
            plan_file="$feature_dir/plan.md"
            research_file="$feature_dir/research.md"
            tasks_file="$feature_dir/tasks.md"
            ;;
        prp)
            feature_dir="$repo_root/context-eng/prp/$feature_name"
            primary_file="$repo_root/PRPs/INITIAL.md"
            prp_file="$repo_root/PRPs/${feature_name}.md"
            plan_file="$feature_dir/plan.md"
            research_file="$feature_dir/research.md"
            tasks_file="$feature_dir/tasks.md"
            initial_file="$primary_file"
            ;;
        all-in-one)
            feature_dir="$repo_root/context-eng/all-in-one/$feature_name"
            primary_file="$feature_dir/record.md"
            plan_file="$feature_dir/plan.md"
            research_file="$feature_dir/research.md"
            tasks_file="$feature_dir/tasks.md"
            ;;
        *)
            feature_dir="$repo_root/specs/$feature_name"
            primary_file="$feature_dir/context-spec.md"
            plan_file="$feature_dir/plan.md"
            research_file="$feature_dir/research.md"
            tasks_file="$feature_dir/tasks.md"
            ;;
    esac

    cat <<EOF
REPO_ROOT='$repo_root'
WORKFLOW='$workflow'
FEATURE_NAME='$feature_name'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
PRIMARY_FILE='$primary_file'
PLAN_FILE='$plan_file'
RESEARCH_FILE='$research_file'
TASKS_FILE='$tasks_file'
PRP_FILE='$prp_file'
INITIAL_FILE='$initial_file'
CHECKLIST_TEMPLATE='$checklist_template'
CURRENT_BRANCH='$feature_name'
IMPL_PLAN='$plan_file'
TASKS='$tasks_file'
FEATURE_SPEC='$primary_file'
RESEARCH='$research_file'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
