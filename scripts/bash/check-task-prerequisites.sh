#!/usr/bin/env bash

# ==============================================================================
# Check Task Prerequisites Script
# ==============================================================================
#
# DESCRIPTION:
#   Validates that all required prerequisites are in place before starting
#   implementation tasks in the Spec-Driven Development workflow. This script
#   ensures that the current branch is a valid feature branch, that the feature
#   directory structure exists, and that essential planning documents are present.
#
# USAGE:
#   ./check-task-prerequisites.sh [OPTIONS]
#
# OPTIONS:
#   --json    Output results in JSON format for programmatic consumption
#   --help    Show usage information and exit
#   -h        Show usage information and exit
#
# PREREQUISITES:
#   - Must be run from within a git repository
#   - Must be on a feature branch (format: XXX-feature-name)
#   - Feature directory must exist in specs/
#   - plan.md must exist in the feature directory
#
# OUTPUT:
#   In default mode: Displays feature directory path and available documentation files
#   In JSON mode: Returns structured JSON with FEATURE_DIR and AVAILABLE_DOCS array
#
# EXIT CODES:
#   0 - All prerequisites met successfully
#   1 - Missing prerequisites or invalid branch/directory structure
#
# EXAMPLES:
#   ./check-task-prerequisites.sh
#   ./check-task-prerequisites.sh --json
#
# RELATED SCRIPTS:
#   - common.sh: Provides shared functions for path resolution and validation
#   - create-new-feature.sh: Creates the feature structure that this script validates
#   - setup-plan.sh: Creates the plan.md file that this script requires
#
# ==============================================================================

set -e
JSON_MODE=false
for arg in "$@"; do case "$arg" in --json) JSON_MODE=true ;; --help|-h) echo "Usage: $0 [--json]"; exit 0 ;; esac; done
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" || exit 1
if [[ ! -d "$FEATURE_DIR" ]]; then echo "ERROR: Feature directory not found: $FEATURE_DIR"; echo "Run /specify first."; exit 1; fi
if [[ ! -f "$IMPL_PLAN" ]]; then echo "ERROR: plan.md not found in $FEATURE_DIR"; echo "Run /plan first."; exit 1; fi
if $JSON_MODE; then
  docs=(); [[ -f "$RESEARCH" ]] && docs+=("research.md"); [[ -f "$DATA_MODEL" ]] && docs+=("data-model.md"); ([[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]) && docs+=("contracts/"); [[ -f "$QUICKSTART" ]] && docs+=("quickstart.md");
  json_docs=$(printf '"%s",' "${docs[@]}"); json_docs="[${json_docs%,}]"; printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$FEATURE_DIR" "$json_docs"
else
  echo "FEATURE_DIR:$FEATURE_DIR"; echo "AVAILABLE_DOCS:"; check_file "$RESEARCH" "research.md"; check_file "$DATA_MODEL" "data-model.md"; check_dir "$CONTRACTS_DIR" "contracts/"; check_file "$QUICKSTART" "quickstart.md"; fi
