#!/usr/bin/env bash
# (Moved to scripts/bash/) Create a new feature with branch, directory structure, and template
set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] [JIRA-key] <feature_description>"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

# Check if first arg is JIRA key format
if [[ "${ARGS[0]}" =~ ^[A-Z]+-[0-9]+$ ]]; then
    JIRA_KEY="${ARGS[0]}"
    FEATURE_DESCRIPTION="${ARGS[@]:1}"
else
    # Interactive prompt for JIRA key if not provided
    if [ -t 0 ]; then  # Only prompt if stdin is a terminal
        read -p "Enter JIRA issue key (e.g., PROJ-123): " JIRA_KEY
    else
        echo "ERROR: JIRA key required. Usage: $0 [--json] JIRA-key feature_description" >&2
        exit 1
    fi
    FEATURE_DESCRIPTION="${ARGS[*]}"
fi

if [ -z "$FEATURE_DESCRIPTION" ] || [ -z "$JIRA_KEY" ]; then
    echo "Usage: $0 [--json] [JIRA-key] <feature_description>" >&2
    exit 1
fi

# Validate JIRA key format
if [[ ! "$JIRA_KEY" =~ ^[A-Z]+-[0-9]+$ ]]; then
    echo "ERROR: Invalid JIRA key format. Expected format: PROJ-123" >&2
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Get username from git config (prefer email username over full name)
USERNAME=$(git config user.email 2>/dev/null | cut -d'@' -f1 || git config user.name 2>/dev/null)
if [ -z "$USERNAME" ]; then
    echo "ERROR: Unable to determine username from git config" >&2
    echo "Set git user.name: git config user.name 'Your Name'" >&2
    exit 1
fi

# Sanitize username for branch name (replace spaces/special chars with hyphens)
USERNAME=$(echo "$USERNAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')

# Sanitize feature description
FEATURE_NAME=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
WORDS=$(echo "$FEATURE_NAME" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')

# Create branch name: username/JIRA-123.feature-name
BRANCH_NAME="${USERNAME}/${JIRA_KEY}.${WORDS}"

# Feature directory uses just JIRA-123.feature-name
FEATURE_ID="${JIRA_KEY}.${WORDS}"

git checkout -b "$BRANCH_NAME"

FEATURE_DIR="$SPECS_DIR/$FEATURE_ID"
mkdir -p "$FEATURE_DIR"

TEMPLATE="$REPO_ROOT/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","JIRA_KEY":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$JIRA_KEY"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_ID: $FEATURE_ID"
    echo "JIRA_KEY: $JIRA_KEY"
fi
