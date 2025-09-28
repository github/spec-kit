#!/usr/bin/env bash

set -e

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            cat <<'EOF'
Usage: context-plan-setup.sh [--json]

Ensure the workflow-specific plan file exists and report key artifact paths.
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

mkdir -p "$FEATURE_DIR"

if [[ ! -f "$PLAN_FILE" ]]; then
    mkdir -p "$(dirname "$PLAN_FILE")"
    case "$WORKFLOW" in
        free-style)
            cat <<'EOF' > "$PLAN_FILE"
# Implementation Plan (Free-Style Workflow)

## Summary

## Workstreams
- Frontend:
- Backend:
- Data & Storage:
- QA & Tooling:

## Sequencing

## Risks & Mitigations

## Validation Strategy

EOF
            ;;
        prp)
            cat <<'EOF' > "$PLAN_FILE"
# Execution Plan (PRP Workflow)

## PRP Alignment
- Reference PRP file:

## Objectives & Deliverables

## Task Breakdown

## Risks & Dependencies

## Validation Strategy

EOF
            ;;
        all-in-one)
            cat <<'EOF' > "$PLAN_FILE"
# Plan Notes (All-in-One Workflow)

Use this file to track any plan details that need to live outside the main all-in-one record.

## Focus Areas

## Risks & Blockers

## Follow-ups

EOF
            ;;
    esac

    if [[ -f "$CHECKLIST_TEMPLATE" ]]; then
        echo "## Full Implementation Checklist" >> "$PLAN_FILE"
        cat "$CHECKLIST_TEMPLATE" >> "$PLAN_FILE"
    fi
fi

if $JSON_MODE; then
    printf '{"WORKFLOW":"%s","PLAN_FILE":"%s","PRIMARY_FILE":"%s","RESEARCH_FILE":"%s","TASKS_FILE":"%s","CHECKLIST_TEMPLATE":"%s"}\n' \
        "$WORKFLOW" "$PLAN_FILE" "$PRIMARY_FILE" "$RESEARCH_FILE" "$TASKS_FILE" "$CHECKLIST_TEMPLATE"
else
    cat <<EOF
WORKFLOW: $WORKFLOW
PLAN_FILE: $PLAN_FILE
PRIMARY_FILE: $PRIMARY_FILE
RESEARCH_FILE: $RESEARCH_FILE
TASKS_FILE: $TASKS_FILE
CHECKLIST_TEMPLATE: $CHECKLIST_TEMPLATE
EOF
fi
