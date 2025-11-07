#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
FEATURE_IDENTIFIER=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [feature_identifier]"
            echo ""
            echo "Options:"
            echo "  --json                  Output in JSON format"
            echo "  feature_identifier      Feature name, number, or branch name (optional)"
            echo "                          If not provided, uses current branch"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Use current branch"
            echo "  $0 user-auth            # Use feature by name"
            echo "  $0 5                    # Use feature by number"
            echo "  $0 5-user-auth          # Use feature by full branch name"
            echo "  $0 --json user-auth     # JSON output"
            exit 0
            ;;
        *)
            FEATURE_IDENTIFIER="$1"
            shift
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"

# Determine feature directory
if [ -z "$FEATURE_IDENTIFIER" ]; then
    # No identifier provided - use current branch
    CURRENT_BRANCH=$(get_current_branch)
    FEATURE_DIR=$(find_feature_dir_by_prefix "$REPO_ROOT" "$CURRENT_BRANCH")

    if [[ ! "$CURRENT_BRANCH" =~ ^[0-9]{3}- ]]; then
        if [ "$JSON_MODE" = true ]; then
            echo '{"error": "Not on a feature branch. Please specify feature identifier or switch to a feature branch."}'
        else
            echo "ERROR: Not on a feature branch (current: $CURRENT_BRANCH)" >&2
            echo "Please specify feature name/number or switch to a feature branch." >&2
        fi
        exit 1
    fi
else
    # Identifier provided - find the feature directory
    # Try different interpretations of the identifier

    # Case 1: Full branch name (e.g., "5-user-auth")
    if [[ "$FEATURE_IDENTIFIER" =~ ^[0-9]{1,3}-[a-z0-9-]+$ ]]; then
        # Normalize to 3-digit prefix
        if [[ "$FEATURE_IDENTIFIER" =~ ^([0-9]+)- ]]; then
            NUM="${BASH_REMATCH[1]}"
            NORMALIZED=$(printf "%03d" "$NUM")
            REST="${FEATURE_IDENTIFIER#*-}"
            FEATURE_DIR="$SPECS_DIR/$NORMALIZED-$REST"
        else
            FEATURE_DIR="$SPECS_DIR/$FEATURE_IDENTIFIER"
        fi

    # Case 2: Just a number (e.g., "5")
    elif [[ "$FEATURE_IDENTIFIER" =~ ^[0-9]+$ ]]; then
        NUM="$FEATURE_IDENTIFIER"
        NORMALIZED=$(printf "%03d" "$NUM")
        # Find directory starting with this number
        MATCHES=( "$SPECS_DIR/$NORMALIZED"-* )
        if [ -d "${MATCHES[0]}" ]; then
            FEATURE_DIR="${MATCHES[0]}"
        else
            if [ "$JSON_MODE" = true ]; then
                echo "{\"error\": \"No feature directory found for number: $NUM\"}"
            else
                echo "ERROR: No feature directory found for number: $NUM" >&2
                echo "Looked in: $SPECS_DIR/" >&2
            fi
            exit 1
        fi

    # Case 3: Feature name (e.g., "user-auth")
    else
        # Search for directory ending with this name
        MATCHES=( "$SPECS_DIR/"*-"$FEATURE_IDENTIFIER" )
        if [ -d "${MATCHES[0]}" ]; then
            FEATURE_DIR="${MATCHES[0]}"
        else
            # Try exact match
            if [ -d "$SPECS_DIR/$FEATURE_IDENTIFIER" ]; then
                FEATURE_DIR="$SPECS_DIR/$FEATURE_IDENTIFIER"
            else
                if [ "$JSON_MODE" = true ]; then
                    echo "{\"error\": \"No feature directory found for: $FEATURE_IDENTIFIER\"}"
                else
                    echo "ERROR: No feature directory found for: $FEATURE_IDENTIFIER" >&2
                    echo "Looked in: $SPECS_DIR/" >&2
                fi
                exit 1
            fi
        fi
    fi
fi

# Verify feature directory exists
if [ ! -d "$FEATURE_DIR" ]; then
    if [ "$JSON_MODE" = true ]; then
        echo "{\"error\": \"Feature directory not found: $FEATURE_DIR\"}"
    else
        echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
        echo "Please ensure the feature exists in .specify/specs/" >&2
    fi
    exit 1
fi

# Verify spec.md exists
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ ! -f "$SPEC_FILE" ]; then
    if [ "$JSON_MODE" = true ]; then
        echo "{\"error\": \"Spec file not found: $SPEC_FILE\", \"warning\": \"Feature directory exists but spec.md is missing\"}"
    else
        echo "ERROR: Spec file not found: $SPEC_FILE" >&2
        echo "The feature directory exists but spec.md is missing." >&2
    fi
    exit 1
fi

# Define AI doc file path
AI_DOC_FILE="$FEATURE_DIR/ai-doc.md"

# Get template path
TEMPLATE_FILE="$REPO_ROOT/templates/ai-doc-template.md"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    # Fall back to .specify/templates if repo root doesn't have templates
    TEMPLATE_FILE="$REPO_ROOT/.specify/templates/ai-doc-template.md"

    if [ ! -f "$TEMPLATE_FILE" ]; then
        if [ "$JSON_MODE" = true ]; then
            echo "{\"error\": \"Template file not found: ai-doc-template.md\"}"
        else
            echo "ERROR: Template file not found" >&2
            echo "Expected at: $REPO_ROOT/templates/ai-doc-template.md" >&2
            echo "Or at: $REPO_ROOT/.specify/templates/ai-doc-template.md" >&2
        fi
        exit 1
    fi
fi

# Extract feature name from directory
FEATURE_NAME=$(basename "$FEATURE_DIR")

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Create ai-doc.md from template if it doesn't exist
if [ ! -f "$AI_DOC_FILE" ]; then
    # Copy template and do basic replacements
    sed -e "s/\[FEATURE NAME\]/$FEATURE_NAME/g" \
        -e "s/\[###-feature-name\]/$FEATURE_NAME/g" \
        -e "s/\[DATE\]/$CURRENT_DATE/g" \
        -e "s/\[Draft\/Complete\]/Draft/g" \
        "$TEMPLATE_FILE" > "$AI_DOC_FILE"

    STATUS="created"
else
    STATUS="exists"
fi

# Get additional file paths for reference
PLAN_FILE="$FEATURE_DIR/plan.md"
TASKS_FILE="$FEATURE_DIR/tasks.md"

# Output results
if [ "$JSON_MODE" = true ]; then
    cat <<EOF
{
  "AI_DOC_FILE": "$AI_DOC_FILE",
  "FEATURE_DIR": "$FEATURE_DIR",
  "FEATURE_NAME": "$FEATURE_NAME",
  "SPEC_FILE": "$SPEC_FILE",
  "PLAN_FILE": "$PLAN_FILE",
  "TASKS_FILE": "$TASKS_FILE",
  "STATUS": "$STATUS",
  "TEMPLATE_USED": "$TEMPLATE_FILE"
}
EOF
else
    echo "AI Documentation Setup Complete"
    echo ""
    echo "Feature: $FEATURE_NAME"
    echo "Documentation file: $AI_DOC_FILE"
    echo "Status: $STATUS"
    echo ""
    echo "Related files:"
    echo "  - Spec: $SPEC_FILE"
    [ -f "$PLAN_FILE" ] && echo "  - Plan: $PLAN_FILE"
    [ -f "$TASKS_FILE" ] && echo "  - Tasks: $TASKS_FILE"
fi
