#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" || exit 1
echo "REPO_ROOT: $REPO_ROOT"; echo "BRANCH: $CURRENT_BRANCH"; echo "FEATURE_DIR: $FEATURE_DIR"; echo "FEATURE_SPEC: $FEATURE_SPEC"; echo "IMPL_PLAN: $IMPL_PLAN"; echo "TASKS: $TASKS"
