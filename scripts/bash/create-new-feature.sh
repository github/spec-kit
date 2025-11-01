#!/usr/bin/env bash
# (Moved to scripts/bash/) Create a new feature with branch, directory structure, and template
set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
CAPABILITY_ID=""
MODE=""
TARGET_REPO=""
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --capability=*) CAPABILITY_ID="${arg#*=}" ;;
        --mode=*) MODE="${arg#*=}" ;;
        --repo=*) TARGET_REPO="${arg#*=}" ;;
        --help|-h)
            echo "Usage: $0 [--json] [--capability=cap-XXX] [--mode=MODE] [--repo=repo-name] [jira-key] <hyphenated-feature-name>"
            echo ""
            echo "Options:"
            echo "  --capability=cap-XXX  Create capability within parent feature (e.g., cap-001)"
            echo "  --mode=MODE           Spec depth: quick|lightweight|full (default: full)"
            echo "  --repo=repo-name      Target repository (workspace mode only)"
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
            echo "  # Single-repo mode:"
            echo "  $0 proj-123 my-feature-name           # Branch: hnimitanakit/proj-123.my-feature-name"
            echo ""
            echo "  # Workspace mode with convention-based targeting:"
            echo "  $0 backend-api-auth                   # Infers target from spec name"
            echo ""
            echo "  # Workspace mode with explicit repo:"
            echo "  $0 --repo=attun-backend api-auth      # Explicit target repo"
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

# Detect workspace mode
WORKSPACE_ROOT=$(get_workspace_root)
IS_WORKSPACE_MODE=false
if [[ -n "$WORKSPACE_ROOT" ]]; then
    IS_WORKSPACE_MODE=true
    SPECS_DIR="$WORKSPACE_ROOT/specs"
    mkdir -p "$SPECS_DIR"
else
    # Single-repo mode
    REPO_ROOT=$(git rev-parse --show-toplevel)
    SPECS_DIR="$REPO_ROOT/specs"
    mkdir -p "$SPECS_DIR"
fi

# Get username from git config (prefer email username over full name)
USERNAME=$(git config user.email 2>/dev/null | cut -d'@' -f1 || git config user.name 2>/dev/null)
if [ -z "$USERNAME" ]; then
    echo "ERROR: Unable to determine username from git config" >&2
    echo "Set git user.name: git config user.name 'Your Name'" >&2
    exit 1
fi

# Sanitize username for branch name (replace spaces/special chars with hyphens)
USERNAME=$(echo "$USERNAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')

# Detect GitHub host (for single-repo mode)
GIT_REMOTE_URL=$(git config remote.origin.url 2>/dev/null || echo "")
IS_MARQETA_HOST=false
if [[ "$GIT_REMOTE_URL" == *"github.marqeta.com"* ]]; then
    IS_MARQETA_HOST=true
fi

# Determine if JIRA key and username prefix are required
# In workspace mode, this will be refined after target repo is determined
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

    # Workspace mode: determine target repo and create branch there
    if $IS_WORKSPACE_MODE; then
        # Determine target repo
        if [[ -z "$TARGET_REPO" ]]; then
            # Use convention-based targeting
            TARGET_REPOS=($(get_target_repos_for_spec "$WORKSPACE_ROOT" "$FEATURE_ID"))

            if [[ ${#TARGET_REPOS[@]} -eq 0 ]]; then
                echo "ERROR: No target repository found for spec: $FEATURE_ID" >&2
                echo "Available repos:" >&2
                list_workspace_repos "$WORKSPACE_ROOT" >&2
                exit 1
            elif [[ ${#TARGET_REPOS[@]} -eq 1 ]]; then
                TARGET_REPO="${TARGET_REPOS[0]}"
            else
                # Multiple repos matched - prompt user
                echo "Multiple target repositories matched for '$FEATURE_ID':" >&2
                for i in "${!TARGET_REPOS[@]}"; do
                    echo "  $((i+1))) ${TARGET_REPOS[$i]}" >&2
                done

                if [ -t 0 ]; then
                    read -p "Select target repository (1-${#TARGET_REPOS[@]}): " selection
                    TARGET_REPO="${TARGET_REPOS[$((selection-1))]}"
                else
                    # Non-interactive: use first match
                    TARGET_REPO="${TARGET_REPOS[0]}"
                    echo "WARNING: Using first match: $TARGET_REPO" >&2
                fi
            fi
        fi

        # Get execution path (worktree-aware)
        # If in worktree of target repo, operations execute in worktree
        # Otherwise, operations execute in parent repo
        REPO_PATH=$(get_execution_path "$WORKSPACE_ROOT" "$TARGET_REPO")
        if [[ -z "$REPO_PATH" ]]; then
            echo "ERROR: Repository not found: $TARGET_REPO" >&2
            exit 1
        fi

        # Check if target repo requires Jira keys (workspace mode)
        REPO_REQUIRE_JIRA=$(get_repo_require_jira "$WORKSPACE_ROOT" "$TARGET_REPO")
        if [[ "$REPO_REQUIRE_JIRA" == "true" ]] && [[ -z "$JIRA_KEY" ]]; then
            # Target repo requires Jira key but none was provided
            if [ -t 0 ]; then
                read -p "Target repo '$TARGET_REPO' requires JIRA key. Enter JIRA issue key (e.g., proj-123): " JIRA_KEY
                if [[ -z "$JIRA_KEY" ]]; then
                    echo "ERROR: JIRA key is required for repo: $TARGET_REPO" >&2
                    exit 1
                fi
                # Validate JIRA key format
                if [[ ! "$JIRA_KEY" =~ ^[a-z]+-[0-9]+$ ]]; then
                    echo "ERROR: Invalid JIRA key format. Expected format: proj-123" >&2
                    exit 1
                fi
                # Rebuild feature ID and branch name with Jira key
                if $USE_USERNAME_PREFIX; then
                    BRANCH_NAME="${USERNAME}/${JIRA_KEY}.${FEATURE_NAME}"
                else
                    BRANCH_NAME="${JIRA_KEY}.${FEATURE_NAME}"
                fi
                FEATURE_ID="${JIRA_KEY}.${FEATURE_NAME}"
                FEATURE_DIR="$SPECS_DIR/$FEATURE_ID"
            else
                echo "ERROR: JIRA key required for repo '$TARGET_REPO' but not provided. Use: $0 jira-key feature-name" >&2
                exit 1
            fi
        fi

        # Check if spec already exists
        if [[ -f "$FEATURE_DIR/spec.md" ]]; then
            echo "WARN: Spec already exists at $FEATURE_DIR/spec.md"
            read -p "Continue with existing spec? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Aborted. Use --force to overwrite existing spec."
                exit 1
            fi
        fi

        # Check if branch already exists and checkout if so
        if git_exec "$REPO_PATH" show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
            echo "Branch $BRANCH_NAME already exists. Checking out existing branch..."
            git_exec "$REPO_PATH" checkout "$BRANCH_NAME"
        else
            # Create branch in target repo
            git_exec "$REPO_PATH" checkout -b "$BRANCH_NAME"
        fi

        # Find template (try workspace first, then target repo)
        TEMPLATE="$WORKSPACE_ROOT/.specify/templates/spec-template.md"
        if [[ ! -f "$TEMPLATE" ]]; then
            TEMPLATE="$REPO_PATH/.specify/templates/spec-template.md"
        fi
    else
        # Single-repo mode
        # Check if spec already exists
        if [[ -f "$FEATURE_DIR/spec.md" ]]; then
            echo "WARN: Spec already exists at $FEATURE_DIR/spec.md"
            read -p "Continue with existing spec? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Aborted. Use --force to overwrite existing spec."
                exit 1
            fi
        fi

        # Check if branch already exists and checkout if so
        if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
            echo "Branch $BRANCH_NAME already exists. Checking out existing branch..."
            git checkout "$BRANCH_NAME"
        else
            # Create branch in current repo
            git checkout -b "$BRANCH_NAME"
        fi

        TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
        REPO_PATH="$REPO_ROOT"
    fi

    # Create feature directory
    mkdir -p "$FEATURE_DIR"

    # Determine template filename based on mode
    TEMPLATE_NAME="spec-template.md"
    if [[ "$MODE" == "quick" ]]; then
        TEMPLATE_NAME="spec-template-quick.md"
    elif [[ "$MODE" == "lightweight" ]]; then
        TEMPLATE_NAME="spec-template-lightweight.md"
    fi

    # Update template path to use the mode-specific template name
    # (TEMPLATE was already set in the workspace/single-repo branch logic above)
    if $IS_WORKSPACE_MODE; then
        # Replace the base template name with the mode-specific one
        TEMPLATE="${TEMPLATE%/*}/$TEMPLATE_NAME"
        # Fallback if mode-specific template doesn't exist
        if [[ ! -f "$TEMPLATE" ]]; then
            TEMPLATE="$WORKSPACE_ROOT/.specify/templates/spec-template.md"
        fi
        if [[ ! -f "$TEMPLATE" ]]; then
            TEMPLATE="$REPO_PATH/.specify/templates/spec-template.md"
        fi
    else
        TEMPLATE="$REPO_ROOT/.specify/templates/$TEMPLATE_NAME"
    fi

    # Create spec file in feature directory
    SPEC_FILE="$FEATURE_DIR/spec.md"
    if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

    # Output for parent feature mode
    if $JSON_MODE; then
        if $IS_WORKSPACE_MODE; then
            if [ -n "$JIRA_KEY" ]; then
                printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","JIRA_KEY":"%s","WORKSPACE_ROOT":"%s","TARGET_REPO":"%s","REPO_PATH":"%s"}\n' \
                    "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$JIRA_KEY" "$WORKSPACE_ROOT" "$TARGET_REPO" "$REPO_PATH"
            else
                printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","WORKSPACE_ROOT":"%s","TARGET_REPO":"%s","REPO_PATH":"%s"}\n' \
                    "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$WORKSPACE_ROOT" "$TARGET_REPO" "$REPO_PATH"
            fi
        else
            if [ -n "$JIRA_KEY" ]; then
                printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s","JIRA_KEY":"%s"}\n' \
                    "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID" "$JIRA_KEY"
            else
                printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_ID":"%s"}\n' \
                    "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_ID"
            fi
        fi
    else
        echo "BRANCH_NAME: $BRANCH_NAME"
        echo "SPEC_FILE: $SPEC_FILE"
        echo "FEATURE_ID: $FEATURE_ID"
        if [ -n "$JIRA_KEY" ]; then
            echo "JIRA_KEY: $JIRA_KEY"
        fi
        if $IS_WORKSPACE_MODE; then
            echo "WORKSPACE_ROOT: $WORKSPACE_ROOT"
            echo "TARGET_REPO: $TARGET_REPO"
            echo "REPO_PATH: $REPO_PATH"
        fi
    fi
fi
