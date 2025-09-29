#!/usr/bin/env bash
set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --help|-h) 
            echo "Usage: $0 [--json] --feature <path> --stage <stage> --title <title> [options]"
            echo "  --json       Output results in JSON format"
            echo "  --feature    Path to the feature directory (required)"
            echo "  --stage      Stage name (architect/red/green/refactor/explainer/ops/misc)"
            echo "  --title      Title for the prompt record"
            echo "  --command    Command that produced this record (default: adhoc)"
            echo "  --prompt     Prompt text (required)"
            echo "  --response   Response text (optional)"
            echo "  --files      Files touched (comma-separated, optional)"
            echo "  --tests      Tests executed (comma-separated, optional)"
            echo "  --labels     Labels (comma-separated, optional)"
            echo "  --help       Show this help message"
            exit 0 
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
done

# Parse arguments
FEATURE=""
STAGE="misc"
TITLE=""
COMMAND="adhoc"
PROMPT=""
RESPONSE=""
FILES=""
TESTS=""
LABELS=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --feature)
            FEATURE="$2"; shift 2 ;;
        --stage)
            STAGE="$2"; shift 2 ;;
        --title)
            TITLE="$2"; shift 2 ;;
        --command)
            COMMAND="$2"; shift 2 ;;
        --prompt)
            PROMPT="$2"; shift 2 ;;
        --response)
            RESPONSE="$2"; shift 2 ;;
        --files)
            FILES="$2"; shift 2 ;;
        --tests)
            TESTS="$2"; shift 2 ;;
        --labels)
            LABELS="$2"; shift 2 ;;
        *)
            shift ;;
    esac
done

# Validate required arguments
if [[ -z "$FEATURE" && ! -d "$REPO_ROOT/.specify" ]]; then
    # For standalone projects without Spec Kit, use a default feature name
    FEATURE="general"
fi

if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    exit 1
fi

# Get script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        (cd "$SCRIPT_DIR/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi
    
    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi
    
    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"
    
    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0
        
        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done
        
        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi
    
    echo "main"  # Final fallback
}

# Get repository root and current branch
REPO_ROOT=$(get_repo_root)
CURRENT_BRANCH=$(get_current_branch)

# Determine if we're in a Spec Kit project or standalone
if [[ -d "$REPO_ROOT/.specify" ]]; then
    # Spec Kit project: find the right feature directory
    SPECS_DIR="$REPO_ROOT/specs"
    
    if [[ -z "$FEATURE" ]]; then
        # No feature specified - find the right feature directory
        FEATURE=$(find_latest_feature "$SPECS_DIR" "$CURRENT_BRANCH")
        if [[ -z "$FEATURE" ]]; then
            echo "Error: No feature specified and no existing feature directories found in $SPECS_DIR" >&2
            echo "Please specify --feature or create a feature directory first" >&2
            echo "Current branch: $CURRENT_BRANCH" >&2
            exit 1
        fi
        echo "Auto-detected feature: $FEATURE" >&2
    fi
    
    FEATURE_DIR="$SPECS_DIR/$FEATURE"
    
    # Check if feature directory exists
    if [[ ! -d "$FEATURE_DIR" ]]; then
        echo "Error: Feature directory not found: $FEATURE_DIR" >&2
        echo "Available features:" >&2
        ls -1 "$SPECS_DIR" 2>/dev/null | head -5 | sed 's/^/  - /' >&2
        exit 1
    fi
    
    PROMPTS_DIR="$FEATURE_DIR/prompts"
    TEMPLATE_PATH="$REPO_ROOT/.specify/templates/phr-template.prompt.md"
else
    # Standalone project: use docs/prompts directory
    PROMPTS_DIR="$REPO_ROOT/docs/prompts"
    TEMPLATE_PATH="$REPO_ROOT/prompts/phr-template.prompt.md"
fi

# Function to find the right feature directory
find_latest_feature() {
    local specs_dir="$1"
    local current_branch="$2"
    local latest_feature=""
    local highest=0
    
    if [[ -d "$specs_dir" ]]; then
        # Strategy 1: Try to match current branch name
        if [[ -n "$current_branch" && "$current_branch" != "main" && "$current_branch" != "master" ]]; then
            for dir in "$specs_dir"/*; do
                if [[ -d "$dir" ]]; then
                    local dirname=$(basename "$dir")
                    if [[ "$dirname" == "$current_branch" ]]; then
                        echo "$dirname"
                        return
                    fi
                fi
            done
        fi
        
        # Strategy 2: Find the highest numbered feature
        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                # Look for numbered features (001-, 002-, etc.)
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done
    fi
    
    echo "$latest_feature"
}

# Ensure prompts directory exists
mkdir -p "$PROMPTS_DIR"

# Check if template exists
if [[ ! -f "$TEMPLATE_PATH" ]]; then
    echo "Warning: Template not found at $TEMPLATE_PATH" >&2
    echo "Creating a basic PHR without template..." >&2
    USE_TEMPLATE=false
else
    USE_TEMPLATE=true
fi

# Generate next PHR ID
get_next_phr_id() {
    local prompts_dir="$1"
    local max_id=0
    
    if [[ -d "$prompts_dir" ]]; then
        for file in "$prompts_dir"/[0-9][0-9][0-9][0-9]-*.prompt.md; do
            [[ -e "$file" ]] || continue
            local base=$(basename "$file")
            if [[ "$base" == "phr-template.prompt.md" ]]; then
                continue
            fi
            local num=${base%%-*}
            if [[ "$num" =~ ^[0-9]{4}$ ]]; then
                local value=$((10#$num))
                if (( value > max_id )); then
                    max_id=$value
                fi
            fi
        done
    fi
    
    local next_id=$((max_id + 1))
    printf '%04d' "$next_id"
}

# Slugify text for filenames
slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Format comma-separated list as YAML
format_yaml_list() {
    if [[ -z "$1" ]]; then
        echo "  - none"
        return
    fi
    IFS=',' read -ra ITEMS <<< "$1"
    local printed=0
    for item in "${ITEMS[@]}"; do
        item=$(echo "$item" | xargs)  # trim whitespace
        if [[ -n "$item" ]]; then
            echo "  - $item"
            printed=1
        fi
    done
    if [[ $printed -eq 0 ]]; then
        echo "  - none"
    fi
}

# Format comma-separated list as inline JSON array
format_inline_list() {
    if [[ -z "$1" ]]; then
        echo "\"phr\""
        return
    fi
    IFS=',' read -ra ITEMS <<< "$1"
    local result=""
    for item in "${ITEMS[@]}"; do
        item=$(echo "$item" | xargs)  # trim whitespace
        if [[ -n "$item" ]]; then
            if [[ -n "$result" ]]; then
                result="$result, "
            fi
            # Escape quotes in the item
            item=$(echo "$item" | sed 's/"/\\"/g')
            result="$result\"$item\""
        fi
    done
    if [[ -z "$result" ]]; then
        result="\"phr\""
    fi
    echo "$result"
}

PHR_ID=$(get_next_phr_id "$PROMPTS_DIR")

# Generate title slug
if [[ -z "$TITLE" ]]; then
    TITLE="Prompt $PHR_ID"
fi

TITLE_SLUG=$(slugify "$TITLE")
STAGE_SLUG=$(slugify "$STAGE")

# Create output filename
OUTFILE="$PROMPTS_DIR/${PHR_ID}-${TITLE_SLUG}.${STAGE_SLUG}.prompt.md"

# Get git metadata
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
USER_NAME=$(git config user.name 2>/dev/null || echo "unknown")
DATE_ISO=$(date -u +%Y-%m-%d)

# Format lists
FILES_YAML=$(format_yaml_list "$FILES")
TESTS_YAML=$(format_yaml_list "$TESTS")
LABELS_INLINE=$(format_inline_list "$LABELS")

# Create PHR content
if [[ "$USE_TEMPLATE" == "true" ]]; then
    # Use template if available
    cp "$TEMPLATE_PATH" "$OUTFILE"
    
    # Replace template variables (using a single sed command to avoid multiple .bak files)
    sed -i.tmp \
        -e "s/{{ID}}/$PHR_ID/g" \
        -e "s/{{TITLE}}/$TITLE/g" \
        -e "s/{{STAGE}}/$STAGE/g" \
        -e "s/{{DATE_ISO}}/$DATE_ISO/g" \
        -e "s/{{SURFACE}}/gemini-slash/g" \
        -e "s/{{MODEL}}/unspecified/g" \
        -e "s|{{FEATURE}}|$FEATURE_DIR|g" \
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
    
    # Clean up temporary file
    rm -f "$OUTFILE.tmp"
else
    # Create basic PHR without template
    cat > "$OUTFILE" << EOF
---
id: $PHR_ID
title: $TITLE
stage: $STAGE
date: $DATE_ISO
surface: gemini-slash
model: unspecified
feature: $FEATURE
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
if $JSON_MODE; then
    printf '{"PHR_ID":"%s","OUTFILE":"%s","FEATURE":"%s","STAGE":"%s"}\n' \
        "$PHR_ID" "$OUTFILE" "$FEATURE" "$STAGE"
else
    echo "✅ Prompt recorded → $OUTFILE"
fi
