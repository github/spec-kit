#!/usr/bin/env bash

set -e

JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval $(get_feature_paths)

check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

FEATURE_BASENAME="$(basename "$FEATURE_DIR")"

KNOWLEDGE_ROOT="${SPECIFY_TEAM_DIRECTIVES:-}"
if [[ -z "$KNOWLEDGE_ROOT" ]]; then
    KNOWLEDGE_ROOT="$REPO_ROOT/.specify/memory/team-ai-directives"
fi

KNOWLEDGE_DRAFTS=""
if [[ -d "$KNOWLEDGE_ROOT" ]]; then
    KNOWLEDGE_DRAFTS="$KNOWLEDGE_ROOT/drafts"
    mkdir -p "$KNOWLEDGE_DRAFTS"
else
    KNOWLEDGE_ROOT=""
fi

if $JSON_MODE; then
    printf '{"FEATURE_DIR":"%s","BRANCH":"%s","SPEC_FILE":"%s","PLAN_FILE":"%s","TASKS_FILE":"%s","RESEARCH_FILE":"%s","QUICKSTART_FILE":"%s","KNOWLEDGE_ROOT":"%s","KNOWLEDGE_DRAFTS":"%s"}\n' \
        "$FEATURE_DIR" "$CURRENT_BRANCH" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS" "$RESEARCH" "$QUICKSTART" "$KNOWLEDGE_ROOT" "$KNOWLEDGE_DRAFTS"
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "SPEC_FILE: $FEATURE_SPEC"
    echo "PLAN_FILE: $IMPL_PLAN"
    echo "TASKS_FILE: $TASKS"
    echo "RESEARCH_FILE: $RESEARCH"
    echo "QUICKSTART_FILE: $QUICKSTART"
    if [[ -n "$KNOWLEDGE_ROOT" ]]; then
        echo "KNOWLEDGE_ROOT: $KNOWLEDGE_ROOT"
        echo "KNOWLEDGE_DRAFTS: $KNOWLEDGE_DRAFTS"
    else
        echo "KNOWLEDGE_ROOT: (missing)"
        echo "KNOWLEDGE_DRAFTS: (missing)"
    fi
fi
