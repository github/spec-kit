#!/usr/bin/env bash

set -e

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            cat <<'EOF'
Usage: context-feature-info.sh [--json]

Emit metadata about the active Context Engineering feature and workflow.

Outputs include workflow type, feature directory, key artifact paths, and checklist template hints.
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="${BASH_SOURCE[0]%/*}"
SCRIPT_DIR="$(cd "$SCRIPT_DIR"; pwd)"
source "$SCRIPT_DIR/common.sh"

eval $(get_feature_paths)

check_feature_branch "$FEATURE_NAME" "$HAS_GIT" || exit 1

if $JSON_MODE; then
    printf '{"REPO_ROOT":"%s","FEATURE":"%s","WORKFLOW":"%s","FEATURE_DIR":"%s","PRIMARY_FILE":"%s","PLAN_FILE":"%s","RESEARCH_FILE":"%s","TASKS_FILE":"%s","PRP_FILE":"%s","INITIAL_FILE":"%s","CHECKLIST_TEMPLATE":"%s"}\n' \
        "$REPO_ROOT" "$FEATURE_NAME" "$WORKFLOW" "$FEATURE_DIR" "$PRIMARY_FILE" "$PLAN_FILE" "$RESEARCH_FILE" "$TASKS_FILE" "$PRP_FILE" "$INITIAL_FILE" "$CHECKLIST_TEMPLATE"
else
    cat <<EOF
REPO_ROOT: $REPO_ROOT
FEATURE: $FEATURE_NAME
WORKFLOW: $WORKFLOW
FEATURE_DIR: $FEATURE_DIR
PRIMARY_FILE: $PRIMARY_FILE
PLAN_FILE: $PLAN_FILE
RESEARCH_FILE: $RESEARCH_FILE
TASKS_FILE: $TASKS_FILE
PRP_FILE: $PRP_FILE
INITIAL_FILE: $INITIAL_FILE
CHECKLIST_TEMPLATE: $CHECKLIST_TEMPLATE
EOF
fi
