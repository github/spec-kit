#!/usr/bin/env bash

# ==============================================================================
# Setup Implementation Plan Script
# ==============================================================================
#
# DESCRIPTION:
#   Creates the implementation plan (plan.md) for the current feature by copying
#   the plan template into the feature directory. This is the second step in the
#   Spec-Driven Development workflow, following the feature specification creation.
#   The plan.md file contains technical implementation details, architecture
#   decisions, and step-by-step implementation guidance.
#
# USAGE:
#   ./setup-plan.sh [OPTIONS]
#
# OPTIONS:
#   --json    Output results in JSON format for programmatic consumption
#   --help    Show usage information and exit
#   -h        Show usage information and exit
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a valid feature branch (format: XXX-feature-name)
#   - Feature directory should exist (created by create-new-feature.sh)
#
# TEMPLATE LOCATION:
#   The script looks for the plan template at:
#   $REPO_ROOT/.specify/templates/plan-template.md
#   If the template doesn't exist, the script will still create the target
#   directory structure but won't copy any template content.
#
# OUTPUT:
#   In default mode: Displays paths for feature spec, implementation plan,
#                   feature directory, and current branch
#   In JSON mode: Returns structured JSON with the same information
#
# EXIT CODES:
#   0 - Plan setup completed successfully
#   1 - Not on a valid feature branch or other error
#
# WORKFLOW INTEGRATION:
#   This script is typically called as part of the /plan command in AI coding
#   assistants, after the initial feature specification has been created but
#   before implementation begins.
#
# EXAMPLES:
#   ./setup-plan.sh
#   ./setup-plan.sh --json
#
# RELATED SCRIPTS:
#   - create-new-feature.sh: Previous step that creates the feature structure
#   - check-task-prerequisites.sh: Validates that plan.md exists before implementation
#   - common.sh: Provides shared path resolution functions
#
# ==============================================================================

set -e
JSON_MODE=false
for arg in "$@"; do case "$arg" in --json) JSON_MODE=true ;; --help|-h) echo "Usage: $0 [--json]"; exit 0 ;; esac; done
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" || exit 1
mkdir -p "$FEATURE_DIR"
TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
[[ -f "$TEMPLATE" ]] && cp "$TEMPLATE" "$IMPL_PLAN"
if $JSON_MODE; then
  printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
    "$FEATURE_SPEC" "$IMPL_PLAN" "$FEATURE_DIR" "$CURRENT_BRANCH"
else
  echo "FEATURE_SPEC: $FEATURE_SPEC"; echo "IMPL_PLAN: $IMPL_PLAN"; echo "SPECS_DIR: $FEATURE_DIR"; echo "BRANCH: $CURRENT_BRANCH"
fi
