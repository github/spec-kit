#!/usr/bin/env bash
# Git-specific common functions for the git extension.
# Extracted from scripts/bash/common.sh — contains only git-specific
# branch validation and detection logic.

# Check if we have git available at the repo root
has_git() {
    local repo_root="${1:-$(pwd)}"
    [ -d "$repo_root/.git" ] || [ -f "$repo_root/.git" ] && \
        command -v git >/dev/null 2>&1 && \
        git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Validate that a branch name matches the expected feature branch pattern.
# Accepts sequential (###-* with >=3 digits) or timestamp (YYYYMMDD-HHMMSS-*) formats.
check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    # Reject malformed timestamps (7-digit date or no trailing slug)
    if [[ "$branch" =~ ^[0-9]{7}-[0-9]{6}- ]] || [[ "$branch" =~ ^[0-9]{8}-[0-9]{6}$ ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name or 20260319-143022-feature-name" >&2
        return 1
    fi

    # Accept sequential (>=3 digits followed by hyphen) or timestamp (YYYYMMDD-HHMMSS-*)
    if [[ "$branch" =~ ^[0-9]{3,}- ]] || [[ "$branch" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
        return 0
    fi

    echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
    echo "Feature branches should be named like: 001-feature-name or 20260319-143022-feature-name" >&2
    return 1
}
