#!/usr/bin/env bash

# ==============================================================================
# Get Feature Paths Script
# ==============================================================================
#
# DESCRIPTION:
#   Displays all relevant file and directory paths for the current feature branch
#   in the Spec-Driven Development workflow. This utility script helps developers
#   quickly identify where feature-related files are located and provides a
#   convenient way to inspect the current workspace configuration.
#
# USAGE:
#   ./get-feature-paths.sh
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a valid feature branch (format: XXX-feature-name)
#
# OUTPUT:
#   Displays the following paths:
#   - REPO_ROOT: Git repository root directory
#   - BRANCH: Current git branch name
#   - FEATURE_DIR: Feature-specific directory in specs/
#   - FEATURE_SPEC: Path to spec.md file
#   - IMPL_PLAN: Path to plan.md file
#   - TASKS: Path to tasks.md file
#
# EXIT CODES:
#   0 - Successfully displayed paths
#   1 - Not on a valid feature branch or other error
#
# EXAMPLES:
#   ./get-feature-paths.sh
#
#   Example output:
#   REPO_ROOT: /home/user/my-project
#   BRANCH: 001-user-authentication
#   FEATURE_DIR: /home/user/my-project/specs/001-user-authentication
#   FEATURE_SPEC: /home/user/my-project/specs/001-user-authentication/spec.md
#   IMPL_PLAN: /home/user/my-project/specs/001-user-authentication/plan.md
#   TASKS: /home/user/my-project/specs/001-user-authentication/tasks.md
#
# USE CASES:
#   - Debugging workflow scripts
#   - Setting up IDE workspace paths
#   - Creating custom automation scripts
#   - Troubleshooting missing files or directories
#
# RELATED SCRIPTS:
#   - common.sh: Provides the path generation functions
#   - check-task-prerequisites.sh: Uses these paths for validation
#
# ==============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" || exit 1
echo "REPO_ROOT: $REPO_ROOT"; echo "BRANCH: $CURRENT_BRANCH"; echo "FEATURE_DIR: $FEATURE_DIR"; echo "FEATURE_SPEC: $FEATURE_SPEC"; echo "IMPL_PLAN: $IMPL_PLAN"; echo "TASKS: $TASKS"
