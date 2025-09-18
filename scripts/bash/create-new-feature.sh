#!/usr/bin/env bash
# (Moved to scripts/bash/) Create a new feature with branch, directory structure, and template
set -e

JSON_MODE=false
FEATURE_NUM_OVERRIDE=""
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_MODE=true; shift ;;
        --feature-num)
            if [[ -z "$2" || "$2" =~ ^- ]]; then
                echo "Error: --feature-num requires a number (1-999)" >&2
                exit 1
            fi
            if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                echo "Error: --feature-num must be a positive integer" >&2
                exit 1
            fi
            if [[ "$2" -lt 1 || "$2" -gt 999 ]]; then
                echo "Error: --feature-num must be between 1 and 999" >&2
                exit 1
            fi
            FEATURE_NUM_OVERRIDE="$2"
            shift 2 ;;
        --help|-h) echo "Usage: $0 [--json] [--feature-num NUMBER(1-999)] <feature_description>"; exit 0 ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] [--feature-num NUMBER(1-999)] <feature_description>" >&2
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Use override if provided, otherwise auto-increment
if [ -n "$FEATURE_NUM_OVERRIDE" ]; then
    FEATURE_NUM=$(printf "%03d" "$FEATURE_NUM_OVERRIDE")
else
    HIGHEST=0
    if [ -d "$SPECS_DIR" ]; then
        for dir in "$SPECS_DIR"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
            number=$((10#$number))
            if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
        done
    fi

    NEXT=$((HIGHEST + 1))
    FEATURE_NUM=$(printf "%03d" "$NEXT")
fi

BRANCH_NAME=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
WORDS=$(echo "$BRANCH_NAME" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')
BRANCH_NAME="${FEATURE_NUM}-${WORDS}"

git checkout -b "$BRANCH_NAME"

FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR"

TEMPLATE="$REPO_ROOT/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
fi
