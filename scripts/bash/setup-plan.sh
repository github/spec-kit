#!/usr/bin/env bash
set -e
JSON_MODE=false
CAPABILITY_ID=""
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --capability=*) CAPABILITY_ID="${arg#*=}" ;;
    --help|-h)
      echo "Usage: $0 [--json] [--capability=cap-XXX]"
      echo ""
      echo "Options:"
      echo "  --capability=cap-XXX  Create capability branch and plan for atomic PR"
      echo "  --json                Output in JSON format"
      exit 0
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
check_feature_branch "$CURRENT_BRANCH" || exit 1

# Capability mode: create new branch for atomic PR
if [ -n "$CAPABILITY_ID" ]; then
  # Extract feature ID from current branch
  FEATURE_ID=$(get_feature_id "$CURRENT_BRANCH")
  PARENT_BRANCH="$CURRENT_BRANCH"

  # Verify capability directory exists
  CAPABILITY_DIR="$FEATURE_DIR/$CAPABILITY_ID"
  if [ ! -d "$CAPABILITY_DIR" ]; then
    echo "ERROR: Capability directory not found at $CAPABILITY_DIR" >&2
    echo "Run /decompose first to create capability structure" >&2
    exit 1
  fi

  # Create capability branch: username/jira-123.feature-cap-001
  USERNAME=$(echo "$CURRENT_BRANCH" | cut -d'/' -f1)
  CAPABILITY_BRANCH="${USERNAME}/${FEATURE_ID}-${CAPABILITY_ID}"

  # Check if capability branch already exists
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

  # Set paths for capability
  FEATURE_SPEC="$CAPABILITY_DIR/spec.md"
  IMPL_PLAN="$CAPABILITY_DIR/plan.md"
  SPECS_DIR="$CAPABILITY_DIR"
  CURRENT_BRANCH="$CAPABILITY_BRANCH"

  mkdir -p "$CAPABILITY_DIR"
else
  # Parent feature mode: use existing branch
  mkdir -p "$FEATURE_DIR"
  SPECS_DIR="$FEATURE_DIR"
fi

TEMPLATE="$REPO_ROOT/.specify/templates/plan-template.md"
[[ -f "$TEMPLATE" ]] && cp "$TEMPLATE" "$IMPL_PLAN"

if $JSON_MODE; then
  if [ -n "$CAPABILITY_ID" ]; then
    printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","CAPABILITY_ID":"%s","PARENT_BRANCH":"%s"}\n' \
      "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH" "$CAPABILITY_ID" "$PARENT_BRANCH"
  else
    printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s"}\n' \
      "$FEATURE_SPEC" "$IMPL_PLAN" "$SPECS_DIR" "$CURRENT_BRANCH"
  fi
else
  echo "FEATURE_SPEC: $FEATURE_SPEC"
  echo "IMPL_PLAN: $IMPL_PLAN"
  echo "SPECS_DIR: $SPECS_DIR"
  echo "BRANCH: $CURRENT_BRANCH"
  if [ -n "$CAPABILITY_ID" ]; then
    echo "CAPABILITY_ID: $CAPABILITY_ID"
    echo "PARENT_BRANCH: $PARENT_BRANCH"
    echo ""
    echo "Capability branch created for atomic PR workflow"
  fi
fi
