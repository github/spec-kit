#!/usr/bin/env bash
# (Moved to scripts/bash/) Create a new feature with branch, directory structure, and template
set -e

JSON_MODE=false
CAPABILITY_ID=""
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --capability=*) CAPABILITY_ID="${arg#*=}" ;;
        --help|-h)
            echo "Usage: $0 [--json] [--capability=cap-XXX] [jira-key] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --capability=cap-XXX  Create capability within parent feature (e.g., cap-001)"
            echo "  --json                Output in JSON format"
            echo ""
            echo "Note: JIRA key is required only for user 'hnimitanakit'"
            echo "      Other users can omit JIRA key and use: username/feature-name"
            echo ""
            echo "Examples:"
            echo "  # With JIRA key (required for hnimitanakit):"
            echo "  $0 proj-123 \"User authentication\"           # Branch: username/proj-123.user-authentication"
            echo ""
            echo "  # Without JIRA key (allowed for other users):"
            echo "  $0 \"User authentication\"                    # Branch: username/user-authentication"
            echo ""
            echo "  # Capability mode:"
            echo "  $0 --capability=cap-001 \"Login flow\"        # Create capability in current feature"
            exit 0
            ;;
        *) ARGS+=("$arg") ;;
    esac
done

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

# Determine if JIRA key is required based on username
REQUIRE_JIRA=false
if [[ "$USERNAME" == "hnimitanakit" ]]; then
    REQUIRE_JIRA=true
fi

# Check if first arg is JIRA key format
JIRA_KEY=""
if [[ "${ARGS[0]}" =~ ^[a-z]+-[0-9]+$ ]]; then
    JIRA_KEY="${ARGS[0]}"
    FEATURE_DESCRIPTION="${ARGS[@]:1}"
else
    if $REQUIRE_JIRA; then
        # Interactive prompt for JIRA key if not provided
        if [ -t 0 ]; then  # Only prompt if stdin is a terminal
            read -p "Enter JIRA issue key (e.g., proj-123): " JIRA_KEY
        else
            echo "ERROR: JIRA key required for user '$USERNAME'. Usage: $0 [--json] jira-key feature_description" >&2
            exit 1
        fi
    fi
    FEATURE_DESCRIPTION="${ARGS[*]}"
fi

if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] [jira-key] <feature_description>" >&2
    exit 1
fi

# Validate JIRA key format if provided
if [ -n "$JIRA_KEY" ] && [[ ! "$JIRA_KEY" =~ ^[a-z]+-[0-9]+$ ]]; then
    echo "ERROR: Invalid JIRA key format. Expected format: proj-123" >&2
    exit 1
fi

# Sanitize feature description
FEATURE_NAME=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
WORDS=$(echo "$FEATURE_NAME" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')

# Handle capability mode
if [ -n "$CAPABILITY_ID" ]; then
    # Capability mode: create within existing feature directory
    # Get current feature directory from current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    FEATURE_ID=$(echo "$CURRENT_BRANCH" | sed 's/^[^/]*\///')
    PARENT_DIR="$SPECS_DIR/$FEATURE_ID"

    if [ ! -d "$PARENT_DIR" ]; then
        echo "ERROR: Parent feature directory not found at $PARENT_DIR" >&2
        echo "Make sure you're on the parent feature branch" >&2
        exit 1
    fi

    # Create capability directory: cap-001-feature-name
    CAPABILITY_NAME="${CAPABILITY_ID}-${WORDS}"
    CAPABILITY_DIR="$PARENT_DIR/$CAPABILITY_NAME"

    # No new branch in capability mode - use current branch
    BRANCH_NAME="$CURRENT_BRANCH"

    # Create capability directory
    mkdir -p "$CAPABILITY_DIR"

    # Create spec file in capability directory using capability template
    TEMPLATE="$REPO_ROOT/.specify/templates/capability-spec-template.md"
    SPEC_FILE="$CAPABILITY_DIR/spec.md"

    if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

    # Output for capability mode
    if $JSON_MODE; then
        printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","CAPABILITY_ID":"%s","CAPABILITY_DIR":"%s"}\n' \
            "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$CAPABILITY_ID" "$CAPABILITY_DIR"
    else
        echo "BRANCH_NAME: $BRANCH_NAME (existing)"
        echo "SPEC_FILE: $SPEC_FILE"
        echo "FEATURE_ID: $FEATURE_ID"
        echo "CAPABILITY_ID: $CAPABILITY_ID"
        echo "CAPABILITY_DIR: $CAPABILITY_DIR"
    fi
else
    # Parent feature mode: create new feature branch and directory
    if [ -n "$JIRA_KEY" ]; then
        # With JIRA key: username/jira-123.feature-name
        BRANCH_NAME="${USERNAME}/${JIRA_KEY}.${WORDS}"
        FEATURE_ID="${JIRA_KEY}.${WORDS}"
    else
        # Without JIRA key: username/feature-name
        BRANCH_NAME="${USERNAME}/${WORDS}"
        FEATURE_ID="${USERNAME}.${WORDS}"
    fi

    FEATURE_DIR="$SPECS_DIR/$FEATURE_ID"

    git checkout -b "$BRANCH_NAME"

    # Create feature directory
    mkdir -p "$FEATURE_DIR"

    # Create spec file in feature directory
    TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
    SPEC_FILE="$FEATURE_DIR/spec.md"

    if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

    # Output for parent feature mode
    if $JSON_MODE; then
        if [ -n "$JIRA_KEY" ]; then
            printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","JIRA_KEY":"%s"}\n' \
                "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$JIRA_KEY"
        else
            printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s"}\n' \
                "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID"
        fi
    else
        echo "BRANCH_NAME: $BRANCH_NAME"
        echo "SPEC_FILE: $SPEC_FILE"
        echo "FEATURE_ID: $FEATURE_ID"
        if [ -n "$JIRA_KEY" ]; then
            echo "JIRA_KEY: $JIRA_KEY"
        fi
    fi
fi
