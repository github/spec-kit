#!/usr/bin/env bash
set -euo pipefail

# create-phr.sh - Create Prompt History Record (PHR) - Spec Kit Native
# 
# Deterministic PHR location strategy:
# 1. Before feature exists (no specs/ or early-phase work):
#    → docs/prompts/
#    → stages: constitution, spec, general
#    → naming: 0001-title.constitution.prompt.md
#
# 2. After feature exists (working inside a feature):
#    → specs/<feature>/prompts/
#    → stages: architect, red, green, refactor, explainer, misc
#    → naming: 0001-title.architect.prompt.md
#
# Usage:
#   scripts/bash/create-phr.sh \
#     --title "Setup authentication" \
#     --stage architect \
#     --prompt "Design JWT authentication system" \
#     [--feature 001-auth] \
#     [--response "Created auth module..."] \
#     [--files "src/auth.py,tests/test_auth.py"] \
#     [--tests "test_auth.py::test_login"] \
#     [--labels "auth,security"] \
#     [--json]

JSON_MODE=false
TITLE=""
STAGE=""
PROMPT=""
RESPONSE=""
FILES=""
TESTS=""
LABELS=""
FEATURE=""
COMMAND="adhoc"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_MODE=true; shift ;;
    --title) TITLE=${2:-}; shift 2 ;;
    --stage) STAGE=${2:-}; shift 2 ;;
    --prompt) PROMPT=${2:-}; shift 2 ;;
    --response) RESPONSE=${2:-}; shift 2 ;;
    --files) FILES=${2:-}; shift 2 ;;
    --tests) TESTS=${2:-}; shift 2 ;;
    --labels) LABELS=${2:-}; shift 2 ;;
    --feature) FEATURE=${2:-}; shift 2 ;;
    --command) COMMAND=${2:-}; shift 2 ;;
    --help|-h)
      cat <<EOF
Usage: $0 --title <title> --stage <stage> --prompt <prompt> [options]

Required:
  --title <text>       Title for the PHR
  --stage <stage>      Pre-feature: constitution|spec|general
                       Feature work: architect|red|green|refactor|explainer|misc
  --prompt <text>      The prompt text

Optional:
  --feature <slug>     Feature slug (e.g., 001-auth). Auto-detected from branch if omitted.
  --response <text>    Response summary
  --files <list>       Comma-separated file list
  --tests <list>       Comma-separated test list
  --labels <list>      Comma-separated labels
  --command <name>     Command that produced this PHR (default: adhoc)
  --json               Output JSON with id and path

Stage Extensions:
  Pre-feature stages: .constitution.prompt.md, .spec.prompt.md, .general.prompt.md
  Feature stages: .architect.prompt.md, .red.prompt.md, .green.prompt.md, etc.

Examples:
  # Early-phase constitution work (no feature exists)
  $0 --title "Define quality standards" --stage constitution --prompt "Create constitution.md"

  # Feature-specific implementation work
  $0 --title "Implement login" --stage green --prompt "Add login endpoint" --feature 001-auth
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

if [[ -z "$PROMPT" ]]; then
  echo "Error: --prompt is required" >&2
  exit 1
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SPECS_DIR="$REPO_ROOT/specs"
TEMPLATE_PATH="$REPO_ROOT/.specify/templates/phr-template.prompt.md"

# Deterministic location logic
if [[ ! -d "$SPECS_DIR" ]]; then
  # Pre-feature: no specs/ directory exists
  PROMPTS_DIR="$REPO_ROOT/docs/prompts"
  VALID_STAGES=("constitution" "spec" "general")
  CONTEXT="pre-feature"
else
  # Feature work: specs/ exists
  
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
      local max_num=0
      local latest_feature=""
      for dir in "$SPECS_DIR"/*; do
        if [[ -d "$dir" ]]; then
          local dirname=$(basename "$dir")
          if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
            local num=$((10#${BASH_REMATCH[1]}))
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
  VALID_STAGES=("architect" "red" "green" "refactor" "explainer" "misc")
  CONTEXT="feature"
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

# Helper functions
slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

format_yaml_list() {
  if [[ -z "$1" ]]; then
    echo "  - none"
    return
  fi
  IFS=',' read -ra ITEMS <<< "$1"
  local printed=0
  for item in "${ITEMS[@]}"; do
    item=$(echo "$item" | xargs)
    if [[ -n "$item" ]]; then
      echo "  - $item"
      printed=1
    fi
  done
  if [[ $printed -eq 0 ]]; then
    echo "  - none"
  fi
}

format_inline_list() {
  if [[ -z "$1" ]]; then
    echo "\"phr\""
    return
  fi
  IFS=',' read -ra ITEMS <<< "$1"
  local result=""
  for item in "${ITEMS[@]}"; do
    item=$(echo "$item" | xargs)
    if [[ -n "$item" ]]; then
      if [[ -n "$result" ]]; then
        result="$result, "
      fi
      item=$(echo "$item" | sed 's/"/\\"/g')
      result="$result\"$item\""
    fi
  done
  if [[ -z "$result" ]]; then
    result="\"phr\""
  fi
  echo "$result"
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

# Get metadata
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
USER_NAME=$(git config user.name 2>/dev/null || echo "unknown")
DATE_ISO=$(date -u +%Y-%m-%d)

# Format lists
FILES_YAML=$(format_yaml_list "$FILES")
TESTS_YAML=$(format_yaml_list "$TESTS")
LABELS_INLINE=$(format_inline_list "$LABELS")

# Create PHR content
if [[ -f "$TEMPLATE_PATH" ]]; then
  # Use template
  cp "$TEMPLATE_PATH" "$OUTFILE"
  
  # Replace placeholders
  sed -i.tmp \
    -e "s/{{ID}}/$PHR_ID/g" \
    -e "s/{{TITLE}}/$TITLE/g" \
    -e "s/{{STAGE}}/$STAGE/g" \
    -e "s/{{DATE_ISO}}/$DATE_ISO/g" \
    -e "s/{{SURFACE}}/agent/g" \
    -e "s/{{MODEL}}/unspecified/g" \
    -e "s|{{FEATURE}}|${FEATURE:-"$CONTEXT"}|g" \
    -e "s/{{BRANCH}}/$BRANCH/g" \
    -e "s/{{USER}}/$USER_NAME/g" \
    -e "s/{{COMMAND}}/$COMMAND/g" \
    -e "s/{{LABELS}}/$LABELS_INLINE/g" \
    -e "s/{{LINKS_SPEC}}/null/g" \
    -e "s/{{LINKS_TICKET}}/null/g" \
    -e "s/{{LINKS_ADR}}/null/g" \
    -e "s/{{LINKS_PR}}/null/g" \
    -e "s|{{FILES_YAML}}|$FILES_YAML|g" \
    -e "s|{{TESTS_YAML}}|$TESTS_YAML|g" \
    -e "s|{{PROMPT_TEXT}}|$PROMPT|g" \
    -e "s|{{RESPONSE_TEXT}}|${RESPONSE:-"(response recorded elsewhere)"}|g" \
    -e "s/{{OUTCOME_IMPACT}}/Prompt recorded for traceability/g" \
    -e "s/{{TESTS_SUMMARY}}/${TESTS:-"(not run)"}/g" \
    -e "s/{{FILES_SUMMARY}}/${FILES:-"(not captured)"}/g" \
    -e "s/{{NEXT_PROMPTS}}/none logged/g" \
    -e "s/{{REFLECTION_NOTE}}/One insight to revisit tomorrow/g" \
    "$OUTFILE"
  
  rm -f "$OUTFILE.tmp"
else
  # Create basic PHR without template
  cat > "$OUTFILE" << EOF
---
id: $PHR_ID
title: $TITLE
stage: $STAGE
date: $DATE_ISO
surface: agent
model: unspecified
feature: ${FEATURE:-"$CONTEXT"}
branch: $BRANCH
user: $USER_NAME
command: $COMMAND
labels: [$LABELS_INLINE]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
$FILES_YAML
tests:
$TESTS_YAML
---

## Prompt

$PROMPT

## Response snapshot

${RESPONSE:-"(response recorded elsewhere)"}

## Outcome

- ✅ Impact: Prompt recorded for traceability
- 🧪 Tests: ${TESTS:-"(not run)"}
- 📁 Files: ${FILES:-"(not captured)"}
- 🔁 Next prompts: none logged
- 🧠 Reflection: One insight to revisit tomorrow
EOF
fi

# Output results
ABS_PATH=$(cd "$(dirname "$OUTFILE")" && pwd)/$(basename "$OUTFILE")
if $JSON_MODE; then
  printf '{"id":"%s","path":"%s","context":"%s","stage":"%s"}\n' \
    "$PHR_ID" "$ABS_PATH" "$CONTEXT" "$STAGE"
else
  echo "✅ PHR recorded → $ABS_PATH"
fi
