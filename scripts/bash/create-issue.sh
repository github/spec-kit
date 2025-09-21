#!/usr/bin/env bash

set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] <issue_description>"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

ISSUE_DESCRIPTION="${ARGS[*]}"
if [ -z "$ISSUE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] <issue_description>" >&2
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

ISSUES_DIR="$REPO_ROOT/issues"
mkdir -p "$ISSUES_DIR"

HIGHEST=0
if [ -d "$ISSUES_DIR" ]; then
    for dir in "$ISSUES_DIR"/*; do
        [ -d "$dir" ] || continue
        dirname=$(basename "$dir")
        number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
        number=$((10#$number))
        if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
    done
fi

NEXT=$((HIGHEST + 1))
ISSUE_NUM=$(printf "%03d" "$NEXT")

# Normalize the issue description to create a slug
ISSUE_SLUG=$(echo "$ISSUE_DESCRIPTION" | tr '[:upper:]' '[:lower:]')
ISSUE_SLUG=$(echo "$ISSUE_SLUG" | sed 's/[^a-z0-9]/-/g')
ISSUE_SLUG=$(echo "$ISSUE_SLUG" | sed 's/-\+/-/g')
ISSUE_SLUG=$(echo "$ISSUE_SLUG" | sed 's/^-//')
ISSUE_SLUG=$(echo "$ISSUE_SLUG" | sed 's/-$//')

# Split the slug into words, filter empty, take first 3, join with dashes
ISSUE_WORDS=$(echo "$ISSUE_SLUG" | tr '-' '\n' | grep -v '^$')
ISSUE_WORDS=$(echo "$ISSUE_WORDS" | head -3)
ISSUE_WORDS=$(echo "$ISSUE_WORDS" | tr '\n' '-' | sed 's/-$//')

# If no words found, fallback to 'issue'
if [ -z "$ISSUE_WORDS" ]; then
    ISSUE_WORDS="issue"
fi

ISSUE_NAME="${ISSUE_NUM}-${ISSUE_WORDS}"

if [ "$HAS_GIT" = true ]; then
    git checkout -b "$ISSUE_NAME"
else
    >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $ISSUE_NAME"
fi

ISSUE_DIR="$ISSUES_DIR/$ISSUE_NAME"
mkdir -p "$ISSUE_DIR"

TEMPLATE="$REPO_ROOT/templates/issue-template.md"
ISSUE_SPEC="$ISSUE_DIR/issue.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$ISSUE_SPEC"; else touch "$ISSUE_SPEC"; fi

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$ISSUE_NAME"

if $JSON_MODE; then
    printf '{"ISSUE_NUM":"%s","ISSUE_DIR":"%s","ISSUE_SPEC":"%s"}\n' "$ISSUE_NUM" "$ISSUE_DIR" "$ISSUE_SPEC"
else
    echo "ISSUE_NUM: $ISSUE_NUM"
    echo "ISSUE_DIR: $ISSUE_DIR"
    echo "ISSUE_SPEC: $ISSUE_SPEC"
    echo "SPECIFY_FEATURE environment variable set to: $ISSUE_NAME"
fi
