#!/usr/bin/env bash
set -e
JSON_MODE=false
CAPABILITY_ID=""
TARGET_REPO=""
NEXT_IS_CAPABILITY=false

for arg in "$@"; do
  if $NEXT_IS_CAPABILITY; then
    CAPABILITY_ID="$arg"
    NEXT_IS_CAPABILITY=false
    continue
  fi

  case "$arg" in
    --json) JSON_MODE=true ;;
    --capability=*) CAPABILITY_ID="${arg#*=}" ;;
    --capability) NEXT_IS_CAPABILITY=true ;;
    --repo=*) TARGET_REPO="${arg#*=}" ;;
    --help|-h)
      echo "Usage: $0 [--json] [--capability cap-XXX] [--repo=repo-name]"
      echo ""
      echo "Options:"
      echo "  --capability cap-XXX  Create capability branch and plan for atomic PR"
      echo "  --repo=repo-name      Target repository for capability (workspace mode only)"
      echo "  --json                Output in JSON format"
      echo ""
      echo "Note: Capabilities are single-repo. In workspace mode, you must specify"
      echo "      which repo the capability targets if parent spec spans multiple repos."
      exit 0
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Detect workspace mode
WORKSPACE_ROOT=$(get_workspace_root)
IS_WORKSPACE_MODE=false
if [[ -n "$WORKSPACE_ROOT" ]]; then
    IS_WORKSPACE_MODE=true
fi

# Get feature paths using smart function if in workspace mode
if $IS_WORKSPACE_MODE && [[ -n "$TARGET_REPO" ]]; then
    eval $(get_feature_paths_smart "$TARGET_REPO")
else
    eval $(get_feature_paths)
fi

# Get current branch from appropriate repo
if $IS_WORKSPACE_MODE && [[ -n "$REPO_PATH" ]]; then
    CURRENT_BRANCH=$(get_current_branch "$REPO_PATH")
else
    CURRENT_BRANCH=$(get_current_branch)
fi

check_feature_branch "$CURRENT_BRANCH" || exit 1

# Capability mode: create new branch for atomic PR
if [ -n "$CAPABILITY_ID" ]; then
  # Extract feature ID from current branch
  FEATURE_ID=$(get_feature_id "$CURRENT_BRANCH")
  PARENT_BRANCH="$CURRENT_BRANCH"

  # Workspace mode: determine target repo for capability
  if $IS_WORKSPACE_MODE; then
    if [[ -z "$TARGET_REPO" ]]; then
      # Prompt user to select target repo if not specified
      echo "Capability '$CAPABILITY_ID' requires a target repository." >&2
      echo "Available repos:" >&2
      AVAILABLE_REPOS=($(list_workspace_repos "$WORKSPACE_ROOT"))

      for i in "${!AVAILABLE_REPOS[@]}"; do
        echo "  $((i+1))) ${AVAILABLE_REPOS[$i]}" >&2
      done

      if [ -t 0 ]; then
        read -p "Select target repository (1-${#AVAILABLE_REPOS[@]}): " selection
        TARGET_REPO="${AVAILABLE_REPOS[$((selection-1))]}"
      else
        echo "ERROR: --repo flag required in non-interactive mode" >&2
        exit 1
      fi
    fi

    # Re-evaluate paths with target repo
    eval $(get_feature_paths_smart "$TARGET_REPO")
    REPO_PATH=$(get_repo_path "$WORKSPACE_ROOT" "$TARGET_REPO")
  fi

  # Determine specs directory based on mode
  if $IS_WORKSPACE_MODE; then
    SPECS_DIR="$WORKSPACE_ROOT/specs"
    CAPABILITY_DIR="$SPECS_DIR/$FEATURE_ID/$CAPABILITY_ID"
  else
    CAPABILITY_DIR="$FEATURE_DIR/$CAPABILITY_ID"
  fi

  # Verify capability directory exists
  if [ ! -d "$CAPABILITY_DIR" ]; then
    echo "ERROR: Capability directory not found at $CAPABILITY_DIR" >&2
    echo "Run /decompose first to create capability structure" >&2
    exit 1
  fi

  # Create capability branch: username/jira-123.feature-cap-001
  USERNAME=$(echo "$CURRENT_BRANCH" | cut -d'/' -f1)
  CAPABILITY_BRANCH="${USERNAME}/${FEATURE_ID}-${CAPABILITY_ID}"

  # Check if capability branch already exists and create/checkout appropriately
  if $IS_WORKSPACE_MODE; then
    # Workspace mode: use git_exec for target repo
    if git_exec "$REPO_PATH" show-ref --verify --quiet "refs/heads/$CAPABILITY_BRANCH"; then
      echo "Checking out existing capability branch: $CAPABILITY_BRANCH in $TARGET_REPO"
      git_exec "$REPO_PATH" checkout "$CAPABILITY_BRANCH" 2>&1
      if [ $? -ne 0 ]; then
        echo "ERROR: Failed to checkout capability branch: $CAPABILITY_BRANCH" >&2
        exit 1
      fi
    else
      echo "Creating new capability branch: $CAPABILITY_BRANCH from $PARENT_BRANCH in $TARGET_REPO"
      git_exec "$REPO_PATH" checkout -b "$CAPABILITY_BRANCH" "$PARENT_BRANCH" 2>&1
      if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create capability branch: $CAPABILITY_BRANCH" >&2
        exit 1
      fi
    fi
  else
    # Single-repo mode: standard git commands
    if git show-ref --verify --quiet "refs/heads/$CAPABILITY_BRANCH"; then
      echo "Checking out existing capability branch: $CAPABILITY_BRANCH"
      git checkout "$CAPABILITY_BRANCH" 2>&1
      if [ $? -ne 0 ]; then
        echo "ERROR: Failed to checkout capability branch: $CAPABILITY_BRANCH" >&2
        exit 1
      fi
    else
      echo "Creating new capability branch: $CAPABILITY_BRANCH from $PARENT_BRANCH"
      git checkout -b "$CAPABILITY_BRANCH" "$PARENT_BRANCH" 2>&1
      if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create capability branch: $CAPABILITY_BRANCH" >&2
        exit 1
      fi
    fi
  fi

  # Set paths for capability
  FEATURE_SPEC="$CAPABILITY_DIR/spec.md"
  IMPL_PLAN="$CAPABILITY_DIR/plan.md"
  CURRENT_BRANCH="$CAPABILITY_BRANCH"

  mkdir -p "$CAPABILITY_DIR"
else
  # Parent feature mode: use existing branch
  mkdir -p "$FEATURE_DIR"
  SPECS_DIR="$FEATURE_DIR"
fi

# Find template (workspace or repo)
if $IS_WORKSPACE_MODE; then
  TEMPLATE="$WORKSPACE_ROOT/.specify/templates/plan-template.md"
  if [[ ! -f "$TEMPLATE" && -n "$REPO_PATH" ]]; then
    TEMPLATE="$REPO_PATH/.specify/templates/plan-template.md"
  fi
else
  TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
fi

[[ -f "$TEMPLATE" ]] && cp "$TEMPLATE" "$IMPL_PLAN"

if $JSON_MODE; then
  if $IS_WORKSPACE_MODE; then
    if [ -n "$CAPABILITY_ID" ]; then
      printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","CAPABILITY_ID":"%s","PARENT_BRANCH":"%s","WORKSPACE_ROOT":"%s","TARGET_REPO":"%s","REPO_PATH":"%s"}\n' \
        "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH" "$CAPABILITY_ID" "$PARENT_BRANCH" "$WORKSPACE_ROOT" "$TARGET_REPO" "$REPO_PATH"
    else
      printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","WORKSPACE_ROOT":"%s","TARGET_REPO":"%s","REPO_PATH":"%s"}\n' \
        "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH" "$WORKSPACE_ROOT" "$TARGET_REPO" "$REPO_PATH"
    fi
  else
    if [ -n "$CAPABILITY_ID" ]; then
      printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","CAPABILITY_ID":"%s","PARENT_BRANCH":"%s"}\n' \
        "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH" "$CAPABILITY_ID" "$PARENT_BRANCH"
    else
      printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
        "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH"
    fi
  fi
else
  echo "FEATURE_SPEC: $FEATURE_SPEC"
  echo "IMPL_PLAN: $IMPL_PLAN"
  echo "SPECS_DIR: $SPECS_DIR"
  echo "BRANCH: $CURRENT_BRANCH"
  if [ -n "$CAPABILITY_ID" ]; then
    echo "CAPABILITY_ID: $CAPABILITY_ID"
    echo "PARENT_BRANCH: $PARENT_BRANCH"
  fi
  if $IS_WORKSPACE_MODE; then
    echo "WORKSPACE_ROOT: $WORKSPACE_ROOT"
    echo "TARGET_REPO: $TARGET_REPO"
    echo "REPO_PATH: $REPO_PATH"
  fi
  if [ -n "$CAPABILITY_ID" ]; then
    echo ""
    echo "Capability branch created for atomic PR workflow"
    if $IS_WORKSPACE_MODE; then
      echo "Target repository: $TARGET_REPO"
    fi
  fi
fi
