#!/usr/bin/env bash

set -e

JSON_MODE=false
FEATURE_NAME=""
ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --feature-name=*)
            FEATURE_NAME="${1#*=}"
            shift
            ;;
        --feature-name)
            if [[ -n "$2" && "$2" != --* ]]; then
                FEATURE_NAME="$2"
                shift 2
            else
                echo "Error: --feature-name requires a value" >&2
                exit 1
            fi
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--feature-name=<name>] <feature_description>"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] [--feature-name=<name>] <feature_description>" >&2
    exit 1
fi

# Function to find the repository root by searching for existing project markers
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Normalise AI-provided feature or description text into a kebab-case slug limited by an optional word cap.
# Assumes input contains valid alphanumeric characters. WordLimit of 0 removes the cap.
get_feature_slug() {
    local raw="$1"
    local word_limit="${2:-3}"
    
    # Convert to lowercase and replace non-alphanumeric with dashes
    local slug=$(echo "$raw" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
    
    # Split into words and apply word limit
    if [ "$word_limit" -le 0 ]; then
        echo "$slug"
    else
        local words=()
        IFS='-' read -ra ADDR <<< "$slug"
        local count=0
        for word in "${ADDR[@]}"; do
            [ -n "$word" ] || continue
            words+=("$word")
            count=$((count + 1))
            if [ "$count" -ge "$word_limit" ]; then
                break
            fi
        done
        IFS='-'; echo "${words[*]}"
    fi
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

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

# Generate slug for branch naming from AI-provided text: prioritize explicit feature name over description
if [ -n "$FEATURE_NAME" ]; then
    SELECTED_SLUG=$(get_feature_slug "$FEATURE_NAME" 0)
else
    SELECTED_SLUG=$(get_feature_slug "$FEATURE_DESCRIPTION" 3)
fi

BRANCH_NAME="${FEATURE_NUM}-${SELECTED_SLUG}"

if [ "$HAS_GIT" = true ]; then
    git checkout -b "$BRANCH_NAME"
else
    >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR"

TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s","HAS_GIT":%s}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM" "$([ "$HAS_GIT" = true ] && echo 'true' || echo 'false')"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "HAS_GIT: $HAS_GIT"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
