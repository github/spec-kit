#!/usr/bin/env bash
# (Moved to scripts/bash/) Create a new feature with branch, directory structure, and template
set -e

JSON_MODE=false
CAPABILITY_ID=""
MODE=""
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --capability=*) CAPABILITY_ID="${arg#*=}" ;;
        --mode=*) MODE="${arg#*=}" ;;
        --help|-h)
            echo "Usage: $0 [--json] [--capability=cap-XXX] [--mode=MODE] [jira-key] <hyphenated-feature-name>"
            echo ""
            echo "Options:"
            echo "  --capability=cap-XXX  Create capability within parent feature (e.g., cap-001)"
            echo "  --mode=MODE           Spec depth: quick|lightweight|full (default: full)"
            echo "  --json                Output in JSON format"
            echo ""
            echo "Modes:"
            echo "  quick               Minimal spec for <200 LOC (bug fixes, small changes)"
            echo "  lightweight         Compact spec for 200-800 LOC (simple features)"
            echo "  full                Complete spec for 800+ LOC (complex features, default)"
            echo ""
            echo "Note: Feature name must be provided as hyphenated-words (e.g., my-feature-name)"
            echo "      JIRA key is required for user 'hnimitanakit' or github.marqeta.com hosts"
            echo ""
            echo "Examples:"
            echo "  # With JIRA key (required for hnimitanakit or Marqeta):"
            echo "  $0 proj-123 my-feature-name           # Branch: hnimitanakit/proj-123.my-feature-name"
            echo ""
            echo "  # Without JIRA key (for user hcnimi):"
            echo "  $0 my-feature-name                    # Branch: my-feature-name (no prefix)"
            echo ""
            echo "  # Capability mode:"
            echo "  $0 --capability=cap-001 login-flow    # Create capability in current feature"
            echo ""
            echo "  # With mode selection:"
            echo "  $0 --mode=quick proj-123 bug-fix      # Use quick template for small changes"
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

# Detect GitHub host
GIT_REMOTE_URL=$(git config remote.origin.url 2>/dev/null || echo "")
IS_MARQETA_HOST=false
if [[ "$GIT_REMOTE_URL" == *"github.marqeta.com"* ]]; then
    IS_MARQETA_HOST=true
fi

# Determine if JIRA key and username prefix are required
REQUIRE_JIRA=false
USE_USERNAME_PREFIX=true
if [[ "$USERNAME" == "hnimitanakit" ]] || [[ "$IS_MARQETA_HOST" == true ]]; then
    REQUIRE_JIRA=true
    USE_USERNAME_PREFIX=true
elif [[ "$USERNAME" == "hcnimi" ]]; then
    REQUIRE_JIRA=false
    USE_USERNAME_PREFIX=false
fi

# Check if first arg is JIRA key format
JIRA_KEY=""
FEATURE_NAME=""
if [[ "${ARGS[0]}" =~ ^[a-z]+-[0-9]+$ ]]; then
    JIRA_KEY="${ARGS[0]}"
    FEATURE_NAME="${ARGS[1]}"
else
    if $REQUIRE_JIRA; then
        # Interactive prompt for JIRA key if not provided
        if [ -t 0 ]; then  # Only prompt if stdin is a terminal
            read -p "Enter JIRA issue key (e.g., proj-123): " JIRA_KEY
            FEATURE_NAME="${ARGS[0]}"
        else
            echo "ERROR: JIRA key required for user '$USERNAME'. Usage: $0 [--json] jira-key hyphenated-feature-name" >&2
            exit 1
        fi
    else
        FEATURE_NAME="${ARGS[0]}"
    fi
fi

# Validate feature name is provided
if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: $0 [--json] [jira-key] <hyphenated-feature-name>" >&2
    exit 1
fi

# Validate JIRA key format if provided
if [ -n "$JIRA_KEY" ] && [[ ! "$JIRA_KEY" =~ ^[a-z]+-[0-9]+$ ]]; then
    echo "ERROR: Invalid JIRA key format. Expected format: proj-123" >&2
    exit 1
fi

# Normalize feature name to lowercase with hyphens
FEATURE_NAME=$(echo "$FEATURE_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')

# Validate feature name contains hyphens (or is a single word, which is acceptable)
if [[ ! "$FEATURE_NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo "ERROR: Feature name must be hyphenated words (e.g., my-feature-name)" >&2
    echo "Received: $FEATURE_NAME" >&2
    exit 1
fi

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
    CAPABILITY_NAME="${CAPABILITY_ID}-${FEATURE_NAME}"
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
        # With JIRA key and username prefix
        if $USE_USERNAME_PREFIX; then
            BRANCH_NAME="${USERNAME}/${JIRA_KEY}.${FEATURE_NAME}"
        else
            BRANCH_NAME="${JIRA_KEY}.${FEATURE_NAME}"
        fi
        FEATURE_ID="${JIRA_KEY}.${FEATURE_NAME}"
    else
        # Without JIRA key
        if $USE_USERNAME_PREFIX; then
            BRANCH_NAME="${USERNAME}/${FEATURE_NAME}"
        else
            BRANCH_NAME="${FEATURE_NAME}"
        fi
        FEATURE_ID="${FEATURE_NAME}"
    fi

    FEATURE_DIR="$SPECS_DIR/$FEATURE_ID"

    # Create branch in current repo
    git checkout -b "$BRANCH_NAME"

    # Create feature directory
    mkdir -p "$FEATURE_DIR"

    # Determine template filename based on mode
    TEMPLATE_NAME="spec-template.md"
    if [[ "$MODE" == "quick" ]]; then
        TEMPLATE_NAME="spec-template-quick.md"
    elif [[ "$MODE" == "lightweight" ]]; then
        TEMPLATE_NAME="spec-template-lightweight.md"
    fi

    # Create spec file in feature directory
    TEMPLATE="$REPO_ROOT/.specify/templates/$TEMPLATE_NAME"
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
