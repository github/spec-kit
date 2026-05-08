#!/usr/bin/env bash
# Git extension: initialize-repo.sh
# Initialize a Git repository with an initial commit.
# Customizable — replace this script to add .gitignore templates,
# default branch config, git-flow, LFS, signing, etc.

set -e

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find project root
_find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.specify" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

REPO_ROOT=$(_find_project_root "$SCRIPT_DIR") || REPO_ROOT="$(pwd)"
cd "$REPO_ROOT"

# Resolve commit message: env var set by caller (via config resolver) takes priority,
# then fall back to ad-hoc YAML read for backward compatibility, then hardcoded default.
#
# Callers should export GIT_CFG_INIT_COMMIT_MESSAGE before invoking this script:
#   eval "$(specify extension config resolve git --format env --prefix GIT_CFG_)"
COMMIT_MSG="${GIT_CFG_INIT_COMMIT_MESSAGE:-}"
if [ -z "$COMMIT_MSG" ]; then
    _config_file="$REPO_ROOT/.specify/extensions/git/git-config.yml"
    if [ -f "$_config_file" ]; then
        _msg=$(grep '^init_commit_message:' "$_config_file" 2>/dev/null | sed 's/^init_commit_message:[[:space:]]*//' | sed 's/^["'\'']//' | sed 's/["'\'']*$//')
        if [ -n "$_msg" ]; then
            COMMIT_MSG="$_msg"
        fi
    fi
fi
: "${COMMIT_MSG:=[Spec Kit] Initial commit}"

# Check if git is available
if ! command -v git >/dev/null 2>&1; then
    echo "[specify] Warning: Git not found; skipped repository initialization" >&2
    exit 0
fi

# Check if already a git repo
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[specify] Git repository already initialized; skipping" >&2
    exit 0
fi

# Initialize
_git_out=$(git init -q 2>&1) || { echo "[specify] Error: git init failed: $_git_out" >&2; exit 1; }
_git_out=$(git add . 2>&1) || { echo "[specify] Error: git add failed: $_git_out" >&2; exit 1; }
_git_out=$(git commit --allow-empty -q -m "$COMMIT_MSG" 2>&1) || { echo "[specify] Error: git commit failed: $_git_out" >&2; exit 1; }

echo "✓ Git repository initialized" >&2
