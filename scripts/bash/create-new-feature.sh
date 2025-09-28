#!/usr/bin/env bash

set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] <feature_description>"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [[ -z "$FEATURE_DESCRIPTION" ]]; then
    echo "Usage: $0 [--json] <feature_description>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)
WORKFLOW=$(read_workflow "$REPO_ROOT")
cd "$REPO_ROOT"

if has_git; then
    HAS_GIT=true
else
    HAS_GIT=false
fi

# Determine next feature number using git branches when available
HIGHEST=0
if [[ "$HAS_GIT" = true ]]; then
    while IFS= read -r branch; do
        if [[ "$branch" =~ ^([0-9]{3})- ]]; then
            number=${BASH_REMATCH[1]}
            number=$((10#$number))
            (( number > HIGHEST )) && HIGHEST=$number
        fi
    done < <(git for-each-ref --format='%(refname:short)' refs/heads)
fi

# Fallback: inspect workflow directories if git not available
if (( HIGHEST == 0 )); then
    for dir in "$REPO_ROOT/specs"/* "$REPO_ROOT/context-eng/prp"/* "$REPO_ROOT/context-eng/all-in-one"/*; do
        [[ -d "$dir" ]] || continue
        base=$(basename "$dir")
        if [[ "$base" =~ ^([0-9]{3})- ]]; then
            number=${BASH_REMATCH[1]}
            number=$((10#$number))
            (( number > HIGHEST )) && HIGHEST=$number
        fi
    done
fi

NEXT=$((HIGHEST + 1))
FEATURE_NUM=$(printf "%03d" "$NEXT")

SLUG=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
WORDS=$(echo "$SLUG" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')
BRANCH_NAME="${FEATURE_NUM}-${WORDS:-feature}"

if [[ "$HAS_GIT" = true ]]; then
    git checkout -b "$BRANCH_NAME"
else
    >&2 echo "[cek] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

CONTEXT_DIR="$REPO_ROOT/.context-eng"
CHECKLIST_TEMPLATE="$CONTEXT_DIR/checklists/full-implementation-checklist.md"

PRIMARY_TEMPLATE=""
PRIMARY_FILE=""
FEATURE_DIR=""
PLAN_FILE=""
RESEARCH_FILE=""
TASKS_FILE=""
PRP_FILE=""
INITIAL_FILE=""

case "$WORKFLOW" in
    free-style)
        FEATURE_DIR="$REPO_ROOT/specs/$BRANCH_NAME"
        mkdir -p "$FEATURE_DIR"
        PRIMARY_TEMPLATE="$CONTEXT_DIR/workflows/free-style/templates/context-spec-template.md"
        PRIMARY_FILE="$FEATURE_DIR/context-spec.md"
        PLAN_FILE="$FEATURE_DIR/plan.md"
        RESEARCH_FILE="$FEATURE_DIR/research.md"
        TASKS_FILE="$FEATURE_DIR/tasks.md"
        ;;
    prp)
        FEATURE_DIR="$REPO_ROOT/context-eng/prp/$BRANCH_NAME"
        mkdir -p "$FEATURE_DIR"
        PRIMARY_TEMPLATE="$CONTEXT_DIR/workflows/prp/templates/initial-template.md"
        PRIMARY_FILE="$REPO_ROOT/PRPs/INITIAL.md"
        PRP_FILE="$REPO_ROOT/PRPs/${BRANCH_NAME}.md"
        PLAN_FILE="$FEATURE_DIR/plan.md"
        RESEARCH_FILE="$FEATURE_DIR/research.md"
        TASKS_FILE="$FEATURE_DIR/tasks.md"
        INITIAL_FILE="$PRIMARY_FILE"
        PRP_TEMPLATE="$CONTEXT_DIR/workflows/prp/templates/prp-template.md"
        mkdir -p "$(dirname "$PRIMARY_FILE")"
        mkdir -p "$(dirname "$PRP_FILE")"
        if [[ ! -f "$PRP_FILE" && -f "$PRP_TEMPLATE" ]]; then
            cp "$PRP_TEMPLATE" "$PRP_FILE"
        fi
        ;;
    all-in-one)
        FEATURE_DIR="$REPO_ROOT/context-eng/all-in-one/$BRANCH_NAME"
        mkdir -p "$FEATURE_DIR"
        PRIMARY_TEMPLATE="$CONTEXT_DIR/workflows/all-in-one/templates/all-in-one-template.md"
        PRIMARY_FILE="$FEATURE_DIR/record.md"
        PLAN_FILE="$FEATURE_DIR/plan.md"
        RESEARCH_FILE="$FEATURE_DIR/research.md"
        TASKS_FILE="$FEATURE_DIR/tasks.md"
        ;;
    *)
        FEATURE_DIR="$REPO_ROOT/specs/$BRANCH_NAME"
        mkdir -p "$FEATURE_DIR"
        PRIMARY_TEMPLATE="$CONTEXT_DIR/workflows/free-style/templates/context-spec-template.md"
        PRIMARY_FILE="$FEATURE_DIR/context-spec.md"
        PLAN_FILE="$FEATURE_DIR/plan.md"
        RESEARCH_FILE="$FEATURE_DIR/research.md"
        TASKS_FILE="$FEATURE_DIR/tasks.md"
        ;;
esac

mkdir -p "$(dirname "$PRIMARY_FILE")"
mkdir -p "$(dirname "$PLAN_FILE")"
mkdir -p "$(dirname "$RESEARCH_FILE")"
mkdir -p "$(dirname "$TASKS_FILE")"
if [[ -f "$PRIMARY_TEMPLATE" && ! -f "$PRIMARY_FILE" ]]; then
    cp "$PRIMARY_TEMPLATE" "$PRIMARY_FILE"
else
    touch "$PRIMARY_FILE"
fi

export CONTEXT_FEATURE="$BRANCH_NAME"
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","FEATURE_NUM":"%s","WORKFLOW":"%s","PRIMARY_FILE":"%s","TEMPLATE_FILE":"%s","FEATURE_DIR":"%s","PLAN_FILE":"%s","RESEARCH_FILE":"%s","TASKS_FILE":"%s","PRP_FILE":"%s","INITIAL_FILE":"%s","CHECKLIST_TEMPLATE":"%s"}\n' \
        "$BRANCH_NAME" "$FEATURE_NUM" "$WORKFLOW" "$PRIMARY_FILE" "$PRIMARY_TEMPLATE" "$FEATURE_DIR" "$PLAN_FILE" "$RESEARCH_FILE" "$TASKS_FILE" "$PRP_FILE" "${INITIAL_FILE:-}" "$CHECKLIST_TEMPLATE"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "WORKFLOW: $WORKFLOW"
    echo "PRIMARY_FILE: $PRIMARY_FILE"
    echo "TEMPLATE_FILE: $PRIMARY_TEMPLATE"
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "PLAN_FILE: $PLAN_FILE"
    echo "RESEARCH_FILE: $RESEARCH_FILE"
    echo "TASKS_FILE: $TASKS_FILE"
    [[ -n "$PRP_FILE" ]] && echo "PRP_FILE: $PRP_FILE"
    echo "CONTEXT_FEATURE environment variable set to: $BRANCH_NAME"
fi
