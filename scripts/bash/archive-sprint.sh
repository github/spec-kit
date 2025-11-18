#!/usr/bin/env bash

set -e

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
SCRIPT_DIR="$(unset CDPATH && cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
fi

# Source common functions
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
CUSTOM_SUMMARY=""
ADDITIONAL_FEATURES=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --summary)
            CUSTOM_SUMMARY="$2"
            shift 2
            ;;
        --archive-features)
            ADDITIONAL_FEATURES="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Check if active sprint exists
ACTIVE_DIR="$REPO_ROOT/.specify/sprints/active"
if [ ! -f "$ACTIVE_DIR/sprint.md" ]; then
    echo "Error: No active sprint found at $ACTIVE_DIR" >&2
    echo "Create a sprint with '/speckit.sprint start' first" >&2
    exit 1
fi

# Extract sprint number and name from sprint.md
SPRINT_NUMBER=$(grep -m 1 "^# Sprint" "$ACTIVE_DIR/sprint.md" | sed 's/^# Sprint \([0-9]*\):.*/\1/')
SPRINT_NAME=$(grep -m 1 "^# Sprint" "$ACTIVE_DIR/sprint.md" | sed 's/^# Sprint [0-9]*: \(.*\)/\1/')

if [ -z "$SPRINT_NUMBER" ] || [ -z "$SPRINT_NAME" ]; then
    echo "Error: Could not extract sprint number or name from sprint.md" >&2
    exit 1
fi

# Create slug from sprint name
SPRINT_SLUG=$(echo "$SPRINT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')

# Create archive directory
ARCHIVE_DIR="$REPO_ROOT/.specify/sprints/archive"
SPRINT_ARCHIVE_DIR="$ARCHIVE_DIR/sprint-$SPRINT_NUMBER-$SPRINT_SLUG"

if [ -d "$SPRINT_ARCHIVE_DIR" ]; then
    echo "Error: Archive directory already exists: $SPRINT_ARCHIVE_DIR" >&2
    exit 1
fi

mkdir -p "$SPRINT_ARCHIVE_DIR"

# Move active sprint files to archive
cp "$ACTIVE_DIR/sprint.md" "$SPRINT_ARCHIVE_DIR/"
cp "$ACTIVE_DIR/backlog.md" "$SPRINT_ARCHIVE_DIR/" 2>/dev/null || true
cp "$ACTIVE_DIR/decisions.md" "$SPRINT_ARCHIVE_DIR/" 2>/dev/null || true

# Extract dates from sprint.md
START_DATE=$(grep "^\*\*Duration\*\*:" "$ACTIVE_DIR/sprint.md" | sed 's/.*: \([0-9-]*\) -.*/\1/')
END_DATE=$(grep "^\*\*Duration\*\*:" "$ACTIVE_DIR/sprint.md" | sed 's/.* - \([0-9-]*\) .*/\1/')
ARCHIVED_DATE=$(date +%Y-%m-%d)

# Parse additional features to archive (comma or space separated)
ADDITIONAL_FEATURES_ARRAY=()
if [ -n "$ADDITIONAL_FEATURES" ]; then
    # Convert comma-separated or space-separated list to array
    IFS=', ' read -ra ADDITIONAL_FEATURES_ARRAY <<< "$ADDITIONAL_FEATURES"
fi

# Create specs directory in archive
mkdir -p "$SPRINT_ARCHIVE_DIR/specs"

# Move completed features from specs directory to archive
COMPLETED_FEATURES=0
FEATURE_LIST=""
if [ -d "$REPO_ROOT/specs" ] && [ -f "$ACTIVE_DIR/backlog.md" ]; then
    # Extract completed feature IDs from backlog (status: Done, Completed, or ✅)
    while IFS= read -r line; do
        if echo "$line" | grep -qE '\| [0-9]+-[^|]+ \|.*\| (Done|Completed|✅)'; then
            FEATURE_ID=$(echo "$line" | sed 's/^| \([0-9]*-[^ |]*\) .*/\1/' | xargs)
            SPEC_DIR="$REPO_ROOT/specs/$FEATURE_ID"
            
            if [ -d "$SPEC_DIR" ]; then
                # Move spec to archive
                mv "$SPEC_DIR" "$SPRINT_ARCHIVE_DIR/specs/"
                
                # Extract feature name
                FEATURE_NAME=$(grep -m 1 "^# Feature Specification:" "$SPRINT_ARCHIVE_DIR/specs/$FEATURE_ID/spec.md" 2>/dev/null | sed 's/^# Feature Specification: //' || echo "Unknown")
                
                # Add to feature list with relative link
                FEATURE_LIST="${FEATURE_LIST}| $FEATURE_ID | $FEATURE_NAME | ✅ Complete | [spec](./specs/$FEATURE_ID/spec.md) |\n"
                COMPLETED_FEATURES=$((COMPLETED_FEATURES + 1))
            fi
        fi
    done < "$ACTIVE_DIR/backlog.md"
    
    # Also move additional features specified via --archive-features
    for FEATURE_ID in "${ADDITIONAL_FEATURES_ARRAY[@]}"; do
        SPEC_DIR="$REPO_ROOT/specs/$FEATURE_ID"
        if [ -d "$SPEC_DIR" ]; then
            mv "$SPEC_DIR" "$SPRINT_ARCHIVE_DIR/specs/"
            FEATURE_NAME=$(grep -m 1 "^# Feature Specification:" "$SPRINT_ARCHIVE_DIR/specs/$FEATURE_ID/spec.md" 2>/dev/null | sed 's/^# Feature Specification: //' || echo "Unknown")
            FEATURE_LIST="${FEATURE_LIST}| $FEATURE_ID | $FEATURE_NAME | ✅ Complete | [spec](./specs/$FEATURE_ID/spec.md) |\n"
            COMPLETED_FEATURES=$((COMPLETED_FEATURES + 1))
        fi
    done
fi

# Create features.md
cat > "$SPRINT_ARCHIVE_DIR/features.md" << FEATURES
# Sprint $SPRINT_NUMBER Features

## Completed Features

| Feature ID | Feature Name | Status | Spec |
|------------|--------------|--------|------|
$(echo -e "$FEATURE_LIST")

## Notes

[Add any additional notes about features]
FEATURES

# Create summary.md from template
SUMMARY_TEMPLATE="$REPO_ROOT/.specify/templates/sprint-summary-template.md"
SUMMARY_FILE="$SPRINT_ARCHIVE_DIR/summary.md"

if [ -f "$SUMMARY_TEMPLATE" ]; then
    sed -e "s/\[NUMBER\]/$SPRINT_NUMBER/g" \
        -e "s/\[NAME\]/$SPRINT_NAME/g" \
        -e "s/\[DURATION\]/$DURATION_TEXT/g" \
        -e "s/\[START_DATE\]/$START_DATE/g" \
        -e "s/\[END_DATE\]/$END_DATE/g" \
        -e "s/\[DATE\]/$ARCHIVED_DATE/g" \
        "$SUMMARY_TEMPLATE" > "$SUMMARY_FILE"
    
    # Add custom summary if provided
    if [ -n "$CUSTOM_SUMMARY" ]; then
        sed -i.bak "s/\[Paragraph 1: What was the sprint goal and was it achieved?\]/$CUSTOM_SUMMARY/" "$SUMMARY_FILE"
        rm "$SUMMARY_FILE.bak"
    fi
else
    # Create basic summary if template doesn't exist
    cat > "$SUMMARY_FILE" << SUMMARY
# Sprint $SPRINT_NUMBER Summary: $SPRINT_NAME

**Duration**: $START_DATE - $END_DATE  
**Status**: Completed  
**Archived**: $ARCHIVED_DATE

## Executive Summary

$CUSTOM_SUMMARY

## Completed Features

$COMPLETED_FEATURES features completed.

See [features.md](./features.md) for details.
SUMMARY
fi

# Create decisions.md (copy from active or create new)
if [ -f "$ACTIVE_DIR/decisions.md" ] && [ -s "$ACTIVE_DIR/decisions.md" ]; then
    cp "$ACTIVE_DIR/decisions.md" "$SPRINT_ARCHIVE_DIR/decisions.md"
else
    cat > "$SPRINT_ARCHIVE_DIR/decisions.md" << DECISIONS
# Sprint $SPRINT_NUMBER Decisions

## Key Decisions

[Extract key decisions from feature specs]

## Pivots & Course Corrections

[Document any pivots that occurred during the sprint]
DECISIONS
fi

# Create retrospective template
RETRO_TEMPLATE="$REPO_ROOT/.specify/templates/retrospective-template.md"
RETRO_FILE="$SPRINT_ARCHIVE_DIR/retrospective.md"

if [ -f "$RETRO_TEMPLATE" ]; then
    sed -e "s/\[NUMBER\]/$SPRINT_NUMBER/g" \
        -e "s/\[NAME\]/$SPRINT_NAME/g" \
        -e "s/\[START_DATE\]/$START_DATE/g" \
        -e "s/\[END_DATE\]/$END_DATE/g" \
        -e "s/\[DATE\]/$ARCHIVED_DATE/g" \
        "$RETRO_TEMPLATE" > "$RETRO_FILE"
else
    cat > "$RETRO_FILE" << RETRO
# Sprint $SPRINT_NUMBER Retrospective

**Sprint**: $SPRINT_NAME  
**Date**: $ARCHIVED_DATE  
**Duration**: $START_DATE - $END_DATE

Run \`/speckit.retrospective\` to conduct the retrospective.
RETRO
fi

# Clean up active directory
rm -rf "$ACTIVE_DIR"/*

# Output result
if [ "$JSON_MODE" = true ]; then
    cat << JSON
{
  "success": true,
  "sprint_number": "$SPRINT_NUMBER",
  "sprint_name": "$SPRINT_NAME",
  "archive_dir": "$SPRINT_ARCHIVE_DIR",
  "completed_features": $COMPLETED_FEATURES,
  "files_created": [
    "$SUMMARY_FILE",
    "$SPRINT_ARCHIVE_DIR/decisions.md",
    "$SPRINT_ARCHIVE_DIR/features.md",
    "$RETRO_FILE"
  ]
}
JSON
else
    echo "✅ Sprint $SPRINT_NUMBER archived successfully!"
    echo ""
    echo "Location: $SPRINT_ARCHIVE_DIR"
    echo ""
    echo "Summary:"
    echo "  - Features completed: $COMPLETED_FEATURES"
    echo ""
    echo "Files created:"
    echo "  - summary.md - High-level sprint summary"
    echo "  - decisions.md - Key decisions and pivots"
    echo "  - features.md - Feature list with links"
    echo "  - retrospective.md - Retrospective template"
    echo ""
    echo "Next steps:"
    echo "  1. Review summary.md for accuracy"
    echo "  2. Run '/speckit.retrospective' to conduct retrospective"
    echo "  3. Run '/speckit.sprint start' to begin next sprint"
fi
