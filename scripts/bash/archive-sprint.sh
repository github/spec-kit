#!/usr/bin/env bash

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(unset CDPATH && cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
CUSTOM_SUMMARY=""

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
        *)
            shift
            ;;
    esac
done

# Check if active sprint exists
ACTIVE_DIR="$REPO_ROOT/sprints/active"
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
ARCHIVE_DIR="$REPO_ROOT/sprints/archive"
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

# Create specs directory in archive
mkdir -p "$SPRINT_ARCHIVE_DIR/specs"

# Interactive check for near-complete features (if not in JSON mode)
NEAR_COMPLETE_FEATURES=()
if [ "$JSON_MODE" = false ] && [ -f "$ACTIVE_DIR/backlog.md" ]; then
    echo ""
    echo "Checking for near-complete features..."
    echo ""
    
    while IFS= read -r line; do
        # Look for In Progress, In Review, or Blocked features
        if echo "$line" | grep -qE '\| [0-9]+-[^|]+ \|.*\| (In Progress|In Review|Blocked)'; then
            FEATURE_ID=$(echo "$line" | sed 's/^| \([0-9]*-[^ |]*\) .*/\1/' | xargs)
            SPEC_DIR="$REPO_ROOT/specs/$FEATURE_ID"
            
            if [ -d "$SPEC_DIR" ]; then
                FEATURE_NAME=$(grep -m 1 "^# Feature Specification:" "$SPEC_DIR/spec.md" 2>/dev/null | sed 's/^# Feature Specification: //' || echo "Unknown")
                CURRENT_STATUS=$(echo "$line" | sed 's/.*| \([^|]*\) |[^|]*|[^|]*$/\1/' | xargs)
                
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "Feature: $FEATURE_ID"
                echo "Name: $FEATURE_NAME"
                echo "Current Status: $CURRENT_STATUS"
                echo ""
                
                # Check completion indicators
                HAS_SPEC=false
                HAS_PLAN=false
                HAS_TASKS=false
                
                [ -f "$SPEC_DIR/spec.md" ] && HAS_SPEC=true
                [ -f "$SPEC_DIR/plan.md" ] && HAS_PLAN=true
                [ -f "$SPEC_DIR/tasks.md" ] && HAS_TASKS=true
                
                echo "Completion indicators:"
                [ "$HAS_SPEC" = true ] && echo "  ✅ Spec exists" || echo "  ❌ Spec missing"
                [ "$HAS_PLAN" = true ] && echo "  ✅ Plan exists" || echo "  ❌ Plan missing"
                [ "$HAS_TASKS" = true ] && echo "  ✅ Tasks exist" || echo "  ❌ Tasks missing"
                
                # Check for common incomplete markers
                if [ -f "$SPEC_DIR/spec.md" ]; then
                    TODO_COUNT=$(grep -E "TODO|FIXME|XXX" "$SPEC_DIR/spec.md" 2>/dev/null | wc -l | xargs)
                    if [ "$TODO_COUNT" -gt 0 ]; then
                        echo "  ⚠️  $TODO_COUNT TODO/FIXME markers in spec"
                    fi
                fi
                
                echo ""
                read -p "Archive this feature as complete? (y/n/skip-all): " response
                
                case "$response" in
                    y|Y|yes|Yes)
                        NEAR_COMPLETE_FEATURES+=("$FEATURE_ID")
                        echo "  → Will archive $FEATURE_ID"
                        ;;
                    skip-all)
                        echo "  → Skipping all remaining near-complete checks"
                        break
                        ;;
                    *)
                        echo "  → Keeping $FEATURE_ID in active specs/"
                        ;;
                esac
                echo ""
            fi
        fi
    done < "$ACTIVE_DIR/backlog.md"
fi

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
    
    # Also move near-complete features that user approved
    for FEATURE_ID in "${NEAR_COMPLETE_FEATURES[@]}"; do
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
SUMMARY_TEMPLATE="$REPO_ROOT/templates/sprint-summary-template.md"
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
RETRO_TEMPLATE="$REPO_ROOT/templates/retrospective-template.md"
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
