#!/usr/bin/env bash
set -euo pipefail

# create-phr.sh - Create Prompt History Record (PHR) - Spec Kit Native
# 
# Deterministic PHR location strategy:
# 1. Pre-feature stages (constitution, spec):
#    → docs/prompts/
#    → stages: constitution, spec
#    → naming: 0001-title.constitution.prompt.md
#
# 2. Feature stages (all other work):
#    → specs/<feature>/prompts/
#    → stages: architect, red, green, refactor, explainer, misc, general
#    → naming: 0001-title.architect.prompt.md
#
# 3. Special case - 'general' stage:
#    → If specs/ exists: goes to specs/<feature>/prompts/
#    → If no specs/: falls back to docs/prompts/ with warning
#
# This script ONLY:
#   1. Creates the correct directory structure
#   2. Copies the template with {{PLACEHOLDERS}} intact
#   3. Returns metadata (id, path, context) for AI to fill in
#
# The calling AI agent is responsible for filling {{PLACEHOLDERS}}
#
# Usage:
#   scripts/bash/create-phr.sh \
#     --title "Setup authentication" \
#     --stage architect \
#     [--feature 001-auth] \
#     [--json]

JSON_MODE=false
TITLE=""
STAGE=""
FEATURE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_MODE=true; shift ;;
    --title) TITLE=${2:-}; shift 2 ;;
    --stage) STAGE=${2:-}; shift 2 ;;
    --feature) FEATURE=${2:-}; shift 2 ;;
    --help|-h)
      cat <<EOF
Usage: $0 --title <title> --stage <stage> [options]

Required:
  --title <text>       Title for the PHR (used for filename)
  --stage <stage>      Pre-feature: constitution|spec
                       Feature work: architect|red|green|refactor|explainer|misc|general

Optional:
  --feature <slug>     Feature slug (e.g., 001-auth). Auto-detected from branch if omitted.
  --json               Output JSON with id, path, and context

Stage Extensions:
  Pre-feature stages: .constitution.prompt.md, .spec.prompt.md
  Feature stages: .architect.prompt.md, .red.prompt.md, .green.prompt.md, .general.prompt.md, etc.
  
Location Rules:
  - constitution, spec → always docs/prompts/
  - architect, red, green, refactor, explainer, misc → requires specs/<feature>/prompts/
  - general → specs/<feature>/prompts/ if exists, else docs/prompts/ with warning

Output:
  Creates PHR file with template placeholders ({{ID}}, {{TITLE}}, etc.)
  AI agent must fill these placeholders after creation

Examples:
  # Early-phase constitution work (no feature exists)
  $0 --title "Define quality standards" --stage constitution --json

  # Feature-specific implementation work
  $0 --title "Implement login" --stage green --feature 001-auth --json
EOF
      exit 0
      ;;
    *) shift ;;
  esac
done

# Validation
if [[ -z "$TITLE" ]]; then
  echo "Error: --title is required" >&2
  exit 1
fi

if [[ -z "$STAGE" ]]; then
  echo "Error: --stage is required" >&2
  exit 1
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SPECS_DIR="$REPO_ROOT/specs"

# Check for template (try both locations)
TEMPLATE_PATH=""
if [[ -f "$REPO_ROOT/.specify/templates/phr-template.prompt.md" ]]; then
  TEMPLATE_PATH="$REPO_ROOT/.specify/templates/phr-template.prompt.md"
elif [[ -f "$REPO_ROOT/templates/phr-template.prompt.md" ]]; then
  TEMPLATE_PATH="$REPO_ROOT/templates/phr-template.prompt.md"
else
  echo "Error: PHR template not found at .specify/templates/ or templates/" >&2
  exit 1
fi

# Deterministic location logic based on STAGE
PRE_FEATURE_STAGES=("constitution" "spec")
FEATURE_STAGES=("architect" "red" "green" "refactor" "explainer" "misc" "general")

# Check if this is a pre-feature stage (constitution or spec only)
IS_PRE_FEATURE=false
for pf_stage in "${PRE_FEATURE_STAGES[@]}"; do
  if [[ "$STAGE" == "$pf_stage" ]]; then
    IS_PRE_FEATURE=true
    break
  fi
done

if [[ "$IS_PRE_FEATURE" == "true" ]]; then
  # Pre-feature stage: always use docs/prompts/ (constitution, spec only)
  PROMPTS_DIR="$REPO_ROOT/docs/prompts"
  VALID_STAGES=("${PRE_FEATURE_STAGES[@]}")
  CONTEXT="pre-feature"
else
  # Feature stage: architect, red, green, refactor, explainer, misc, general
  # These require specs/ directory and feature context
  
  if [[ ! -d "$SPECS_DIR" ]]; then
    # Special case: 'general' can fall back to docs/prompts/ if no specs exist
    if [[ "$STAGE" == "general" ]]; then
      echo "Warning: No specs/ directory found. Using docs/prompts/ for general stage." >&2
      echo "Consider using 'constitution' or 'spec' stages, or create a feature first with /specify" >&2
      PROMPTS_DIR="$REPO_ROOT/docs/prompts"
      VALID_STAGES=("general")
      CONTEXT="pre-feature-fallback"
    else
      echo "Error: Feature stage '$STAGE' requires specs/ directory and feature context" >&2
      echo "Use pre-feature stages (constitution, spec) or create a feature first with /specify" >&2
      exit 1
    fi
  else
    # specs/ exists - proceed with feature context
    # Auto-detect feature if not specified
  if [[ -z "$FEATURE" ]]; then
    # Try to get from SPECIFY_FEATURE environment variable
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
      FEATURE="$SPECIFY_FEATURE"
    # Try to match current branch
    elif git rev-parse --show-toplevel >/dev/null 2>&1; then
      BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
      if [[ -n "$BRANCH" && "$BRANCH" != "main" && "$BRANCH" != "master" ]]; then
        # Check if branch name matches a feature directory
        if [[ -d "$SPECS_DIR/$BRANCH" ]]; then
          FEATURE="$BRANCH"
        fi
      fi
    fi
    
    # If still no feature, find the highest numbered feature
    if [[ -z "$FEATURE" ]]; then
      max_num=0
      latest_feature=""
      for dir in "$SPECS_DIR"/*; do
        if [[ -d "$dir" ]]; then
          dirname=$(basename "$dir")
          if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
            num=$((10#${BASH_REMATCH[1]}))
            if (( num > max_num )); then
              max_num=$num
              latest_feature="$dirname"
            fi
          fi
        fi
      done
      
      if [[ -n "$latest_feature" ]]; then
        FEATURE="$latest_feature"
      else
        echo "Error: No feature specified and no numbered features found in $SPECS_DIR" >&2
        echo "Please specify --feature or create a feature directory first" >&2
        exit 1
      fi
    fi
  fi
  
  # Validate feature exists
  if [[ ! -d "$SPECS_DIR/$FEATURE" ]]; then
    echo "Error: Feature directory not found: $SPECS_DIR/$FEATURE" >&2
    echo "Available features:" >&2
    ls -1 "$SPECS_DIR" 2>/dev/null | head -5 | sed 's/^/  - /' >&2
    exit 1
  fi
  
    PROMPTS_DIR="$SPECS_DIR/$FEATURE/prompts"
    VALID_STAGES=("architect" "red" "green" "refactor" "explainer" "misc" "general")
    CONTEXT="feature"
  fi
fi

# Validate stage
stage_valid=false
for valid_stage in "${VALID_STAGES[@]}"; do
  if [[ "$STAGE" == "$valid_stage" ]]; then
    stage_valid=true
    break
  fi
done

if [[ "$stage_valid" == "false" ]]; then
  echo "Error: Invalid stage '$STAGE' for $CONTEXT context" >&2
  echo "Valid stages for $CONTEXT: ${VALID_STAGES[*]}" >&2
  exit 1
fi

# Ensure prompts directory exists
mkdir -p "$PROMPTS_DIR"

# Helper: slugify
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Get next ID (local to this directory)
get_next_id() {
  local max_id=0
  for file in "$PROMPTS_DIR"/[0-9][0-9][0-9][0-9]-*.prompt.md; do
    [[ -e "$file" ]] || continue
    local base=$(basename "$file")
    local num=${base%%-*}
    if [[ "$num" =~ ^[0-9]{4}$ ]]; then
      local value=$((10#$num))
      if (( value > max_id )); then
        max_id=$value
      fi
    fi
  done
  printf '%04d' $((max_id + 1))
}

PHR_ID=$(get_next_id)
TITLE_SLUG=$(slugify "$TITLE")
STAGE_SLUG=$(slugify "$STAGE")

# Create filename with stage extension
OUTFILE="$PROMPTS_DIR/${PHR_ID}-${TITLE_SLUG}.${STAGE_SLUG}.prompt.md"

# Simply copy the template (AI will fill placeholders)
cp "$TEMPLATE_PATH" "$OUTFILE"

# Output results
ABS_PATH=$(cd "$(dirname "$OUTFILE")" && pwd)/$(basename "$OUTFILE")
if $JSON_MODE; then
  printf '{"id":"%s","path":"%s","context":"%s","stage":"%s","feature":"%s","template":"%s"}\n' \
    "$PHR_ID" "$ABS_PATH" "$CONTEXT" "$STAGE" "${FEATURE:-none}" "$(basename "$TEMPLATE_PATH")"
else
  echo "✅ PHR template copied → $ABS_PATH"
  echo "Note: AI agent should now fill in {{PLACEHOLDERS}}"
fi
