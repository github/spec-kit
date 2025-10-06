#!/usr/bin/env bash
# Analyze current feature alignment with all existing features using systems thinking
set -e

# Platform detection is done inline where sed is used for better portability

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] [analysis_focus]"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

ANALYSIS_FOCUS="${ARGS[*]}"
if [ -z "$ANALYSIS_FOCUS" ]; then
    ANALYSIS_FOCUS="Comprehensive Analysis"
fi

# Resolve repository root. Prefer git information when available, but fall back
# to the script location so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FALLBACK_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$FALLBACK_ROOT"
    HAS_GIT=false
fi

cd "$REPO_ROOT"

# Get current branch name and find current spec
if [ "$HAS_GIT" = true ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
else
    # If no git, try to determine current feature from specs directory
    # This is a fallback - in practice, alignment analysis should run on active feature branch
    CURRENT_BRANCH=$(ls -t specs/ | head -n 1 2>/dev/null || echo "")
fi

if [ -z "$CURRENT_BRANCH" ] || [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo "Error: Alignment analysis must be run from a feature branch (created by /specify)" >&2
    exit 1
fi

CURRENT_SPEC="$REPO_ROOT/specs/$CURRENT_BRANCH/spec.md"
if [ ! -f "$CURRENT_SPEC" ]; then
    echo "Error: Current specification not found at $CURRENT_SPEC" >&2
    exit 1
fi

# Find all existing specifications
ALL_SPECS=()
SPECS_DIR="$REPO_ROOT/specs"
if [ -d "$SPECS_DIR" ]; then
    for dir in "$SPECS_DIR"/*; do
        [ -d "$dir" ] || continue
        spec_file="$dir/spec.md"
        if [ -f "$spec_file" ] && [ "$spec_file" != "$CURRENT_SPEC" ]; then
            ALL_SPECS+=("$spec_file")
        fi
    done
fi

# Create analysis file in current feature directory
FEATURE_DIR="$(dirname "$CURRENT_SPEC")"
ANALYSIS_FILE="$FEATURE_DIR/cross-feature-analysis.md"

# Create analysis file from template
TEMPLATE="$REPO_ROOT/templates/cross-feature-analysis-template.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$ANALYSIS_FILE"
else
    touch "$ANALYSIS_FILE"
fi

# Extract clarification line from template to avoid duplication
COMMAND_TEMPLATE="$REPO_ROOT/templates/commands/cross-feature.md"
if [ -f "$COMMAND_TEMPLATE" ]; then
    # Extract the clarification message from the template (handles both quotes and backticks)
    CLARIFICATION_LINE=$(grep -A 1 "Add:" "$COMMAND_TEMPLATE" | grep "NEEDS CLARIFICATION" | sed 's/.*["'\''`]\(.*NEEDS CLARIFICATION.*\)["'\''`].*/\1/')
fi

# Fallback if extraction fails
# NOTE: This fallback must match the clarification line in templates/commands/cross-feature.md
# The template is the source of truth - update there first if changing this message
if [ -z "$CLARIFICATION_LINE" ]; then
    CLARIFICATION_LINE="- [NEEDS CLARIFICATION: Review cross-feature alignment analysis in cross-feature-analysis.md - potential conflicts identified that may require spec adjustments]"
fi

# Find the Requirements section and add the clarification line
if [ -f "$CURRENT_SPEC" ]; then
    # Check if the clarification line already exists to avoid duplicates
    if ! grep -q "cross-feature-analysis.md" "$CURRENT_SPEC"; then
        # Find the line with "### Functional Requirements" and add our clarification after it
        if grep -q "### Functional Requirements" "$CURRENT_SPEC"; then
            # Use portable sed in-place editing for macOS and GNU/Linux
            if sed --version >/dev/null 2>&1; then
                # GNU sed
                sed -i "/### Functional Requirements/a\\$CLARIFICATION_LINE" "$CURRENT_SPEC"
            else
                # BSD/macOS sed
                sed -i.bak "/### Functional Requirements/a\\
$CLARIFICATION_LINE" "$CURRENT_SPEC" && rm -f "$CURRENT_SPEC.bak"
            fi
        else
            # If no Functional Requirements section, add to end of file
            echo "" >> "$CURRENT_SPEC"
            echo "$CLARIFICATION_LINE" >> "$CURRENT_SPEC"
        fi
    fi
fi

# Build JSON output with all specs array
if $JSON_MODE; then
    printf '{"CURRENT_SPEC":"%s","ALL_SPECS":[' "$CURRENT_SPEC"

    # Add all specs as JSON array
    first=true
    for spec in "${ALL_SPECS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            printf ','
        fi
        printf '"%s"' "$spec"
    done

    printf '],"ANALYSIS_FILE":"%s","ANALYSIS_FOCUS":"%s"}\n' "$ANALYSIS_FILE" "$ANALYSIS_FOCUS"
else
    echo "CURRENT_SPEC: $CURRENT_SPEC"
    echo "ALL_SPECS: ${ALL_SPECS[*]}"
    echo "ANALYSIS_FILE: $ANALYSIS_FILE"
    echo "ANALYSIS_FOCUS: $ANALYSIS_FOCUS"
fi