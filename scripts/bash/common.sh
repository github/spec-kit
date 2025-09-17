#!/usr/bin/env bash

# ==============================================================================
# Common Functions Library
# ==============================================================================
#
# DESCRIPTION:
#   Shared utility functions and path resolution logic used across all
#   Spec-Driven Development workflow scripts. This library provides consistent
#   behavior for git operations, feature branch validation, and file system
#   path management.
#
# FUNCTIONS:
#   get_repo_root()        - Returns the root directory of the git repository
#   get_current_branch()   - Returns the name of the current git branch
#   check_feature_branch() - Validates feature branch naming convention
#   get_feature_dir()      - Constructs feature directory path from repo root and branch
#   get_feature_paths()    - Generates all standard feature-related file paths
#   check_file()           - Displays file existence status with checkmark/X
#   check_dir()            - Displays directory existence status with contents check
#
# FEATURE BRANCH NAMING CONVENTION:
#   Feature branches must follow the pattern: XXX-feature-name
#   Where XXX is a 3-digit zero-padded number (001, 002, etc.)
#   Examples: 001-user-authentication, 042-payment-integration
#
# STANDARD FEATURE DIRECTORY STRUCTURE:
#   specs/XXX-feature-name/
#   ├── spec.md           # Feature specification (required)
#   ├── plan.md           # Implementation plan (required)
#   ├── tasks.md          # Task breakdown (optional)
#   ├── research.md       # Research notes (optional)
#   ├── data-model.md     # Data model documentation (optional)
#   ├── quickstart.md     # Quick start guide (optional)
#   └── contracts/        # API contracts and interfaces (optional)
#
# USAGE:
#   This file should be sourced by other scripts:
#   source "$SCRIPT_DIR/common.sh"
#   eval $(get_feature_paths)
#
# DEPENDENCIES:
#   - git (for repository operations)
#   - bash 4.0+ (for associative arrays and advanced features)
#
# ==============================================================================

get_repo_root() { git rev-parse --show-toplevel; }
get_current_branch() { git rev-parse --abbrev-ref HEAD; }

check_feature_branch() {
    local branch="$1"
    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    fi; return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local feature_dir=$(get_feature_dir "$repo_root" "$current_branch")
    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
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
