#!/usr/bin/env bash

# Project status discovery script for /speckit.status command
#
# This script discovers project structure and artifact existence.
# It does NOT parse file contents - that's left to the AI agent.
#
# Usage: ./get-project-status.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format (default: text)
#   --feature <name>    Focus on specific feature (name, number, or path)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: Full project status object
#   Text mode: Human-readable status lines

set -e

# Parse command line arguments
JSON_MODE=false
TARGET_FEATURE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --feature)
            if [ -z "$2" ] || [[ "$2" == --* ]]; then
                echo "Error: --feature requires a value" >&2
                exit 1
            fi
            TARGET_FEATURE="$2"
            shift 2
            ;;
        --help|-h)
            cat << 'EOF'
Usage: get-project-status.sh [OPTIONS]

Discover project structure and artifact existence for /speckit.status.

OPTIONS:
  --json              Output in JSON format (default: text)
  --feature <name>    Focus on specific feature (by name, number prefix, or path)
  --help, -h          Show this help message

EXAMPLES:
  # Get full project status in JSON
  ./get-project-status.sh --json

  # Get status for specific feature
  ./get-project-status.sh --json --feature 002-dashboard

  # Get status by feature number
  ./get-project-status.sh --json --feature 002

EOF
            exit 0
            ;;
        *)
            # Treat positional arg as feature identifier
            if [ -z "$TARGET_FEATURE" ]; then
                TARGET_FEATURE="$1"
            fi
            shift
            ;;
    esac
done

# Function to find repository root
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

# Function to get project name from directory or package.json
get_project_name() {
    local repo_root="$1"

    # Try package.json first
    if [ -f "$repo_root/package.json" ]; then
        local name=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$repo_root/package.json" 2>/dev/null | head -1 | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
        if [ -n "$name" ]; then
            echo "$name"
            return
        fi
    fi

    # Try pyproject.toml
    if [ -f "$repo_root/pyproject.toml" ]; then
        local name=$(grep -E '^name\s*=' "$repo_root/pyproject.toml" 2>/dev/null | head -1 | sed 's/^name[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/')
        if [ -n "$name" ] && [ "$name" != "$(grep -E '^name\s*=' "$repo_root/pyproject.toml" 2>/dev/null | head -1)" ]; then
            echo "$name"
            return
        fi
    fi

    # Fall back to directory name
    basename "$repo_root"
}

# Function to check if path/file exists and is non-empty (for directories)
check_exists() {
    local path="$1"
    if [ -f "$path" ]; then
        echo "true"
    elif [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to list files in a directory (for checklists)
list_files() {
    local dir="$1"
    local extension="$2"

    if [ -d "$dir" ]; then
        find "$dir" -maxdepth 1 -name "*$extension" -type f -exec basename {} \; 2>/dev/null | sort
    fi
}

# Function to escape string for JSON
json_escape() {
    local str="$1"
    # Escape backslashes, quotes, and control characters
    printf '%s' "$str" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g' | tr -d '\n'
}

# Resolve repository root
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root." >&2
        exit 1
    fi
    HAS_GIT=false
    CURRENT_BRANCH=""
fi

# Determine specs directory (.specify/specs or specs/)
if [ -d "$REPO_ROOT/.specify/specs" ]; then
    SPECS_DIR="$REPO_ROOT/.specify/specs"
elif [ -d "$REPO_ROOT/specs" ]; then
    SPECS_DIR="$REPO_ROOT/specs"
else
    SPECS_DIR="$REPO_ROOT/.specify/specs"  # Default even if doesn't exist
fi

# Determine memory directory (.specify/memory or memory/)
if [ -d "$REPO_ROOT/.specify/memory" ]; then
    MEMORY_DIR="$REPO_ROOT/.specify/memory"
elif [ -d "$REPO_ROOT/memory" ]; then
    MEMORY_DIR="$REPO_ROOT/memory"
else
    MEMORY_DIR="$REPO_ROOT/.specify/memory"  # Default even if doesn't exist
fi

# Check constitution
CONSTITUTION_PATH="$MEMORY_DIR/constitution.md"
CONSTITUTION_EXISTS=$(check_exists "$CONSTITUTION_PATH")

# Get project name
PROJECT_NAME=$(get_project_name "$REPO_ROOT")

# Check if on feature branch (matches NNN-* pattern)
IS_FEATURE_BRANCH=false
if [[ "$CURRENT_BRANCH" =~ ^[0-9]{3}- ]]; then
    IS_FEATURE_BRANCH=true
fi

# Collect all features
declare -a FEATURES=()
if [ -d "$SPECS_DIR" ]; then
    for dir in "$SPECS_DIR"/[0-9][0-9][0-9]-*; do
        if [ -d "$dir" ]; then
            FEATURES+=("$(basename "$dir")")
        fi
    done
fi

# Sort features by number
IFS=$'\n' FEATURES=($(sort <<<"${FEATURES[*]}")); unset IFS

# Function to get feature info
get_feature_info() {
    local feature_name="$1"
    local feature_dir="$SPECS_DIR/$feature_name"

    local has_spec=$(check_exists "$feature_dir/spec.md")
    local has_plan=$(check_exists "$feature_dir/plan.md")
    local has_tasks=$(check_exists "$feature_dir/tasks.md")
    local has_research=$(check_exists "$feature_dir/research.md")
    local has_data_model=$(check_exists "$feature_dir/data-model.md")
    local has_quickstart=$(check_exists "$feature_dir/quickstart.md")
    local has_contracts=$(check_exists "$feature_dir/contracts")
    local has_checklists=$(check_exists "$feature_dir/checklists")

    # Get checklist files if they exist
    local checklist_files=""
    if [ "$has_checklists" = "true" ]; then
        checklist_files=$(list_files "$feature_dir/checklists" ".md" | tr '\n' ',' | sed 's/,$//')
    fi

    # Determine if this is the current feature
    local is_current=false
    if [ "$IS_FEATURE_BRANCH" = "true" ]; then
        # Extract prefix from current branch
        local current_prefix=$(echo "$CURRENT_BRANCH" | grep -o '^[0-9]\{3\}')
        local feature_prefix=$(echo "$feature_name" | grep -o '^[0-9]\{3\}')
        if [ "$current_prefix" = "$feature_prefix" ]; then
            is_current=true
        fi
    fi

    if $JSON_MODE; then
        printf '{"name":"%s","path":"%s","is_current":%s,"has_spec":%s,"has_plan":%s,"has_tasks":%s,"has_research":%s,"has_data_model":%s,"has_quickstart":%s,"has_contracts":%s,"has_checklists":%s,"checklist_files":[%s]}' \
            "$(json_escape "$feature_name")" \
            "$(json_escape "$feature_dir")" \
            "$is_current" \
            "$has_spec" \
            "$has_plan" \
            "$has_tasks" \
            "$has_research" \
            "$has_data_model" \
            "$has_quickstart" \
            "$has_contracts" \
            "$has_checklists" \
            "$(echo "$checklist_files" | sed 's/\([^,]*\)/"\1"/g')"
    else
        echo "  Name: $feature_name"
        echo "  Path: $feature_dir"
        echo "  Current: $is_current"
        echo "  Artifacts:"
        echo "    spec.md: $has_spec"
        echo "    plan.md: $has_plan"
        echo "    tasks.md: $has_tasks"
        echo "    research.md: $has_research"
        echo "    data-model.md: $has_data_model"
        echo "    quickstart.md: $has_quickstart"
        echo "    contracts/: $has_contracts"
        echo "    checklists/: $has_checklists"
        if [ -n "$checklist_files" ]; then
            echo "    checklist_files: $checklist_files"
        fi
        echo ""
    fi
}

# Resolve target feature if specified
RESOLVED_TARGET=""
if [ -n "$TARGET_FEATURE" ]; then
    # Try exact match first
    if [ -d "$SPECS_DIR/$TARGET_FEATURE" ]; then
        RESOLVED_TARGET="$TARGET_FEATURE"
    # Try as path
    elif [ -d "$TARGET_FEATURE" ]; then
        RESOLVED_TARGET=$(basename "$TARGET_FEATURE")
    # Try as number prefix
    elif [[ "$TARGET_FEATURE" =~ ^[0-9]+$ ]]; then
        PREFIX=$(printf "%03d" "$TARGET_FEATURE")
        for f in "${FEATURES[@]}"; do
            if [[ "$f" == "$PREFIX"-* ]]; then
                RESOLVED_TARGET="$f"
                break
            fi
        done
    # Try partial match
    else
        for f in "${FEATURES[@]}"; do
            if [[ "$f" == *"$TARGET_FEATURE"* ]]; then
                RESOLVED_TARGET="$f"
                break
            fi
        done
    fi

    if [ -z "$RESOLVED_TARGET" ]; then
        echo "Error: Feature not found: $TARGET_FEATURE" >&2
        exit 1
    fi
fi

# Output results
if $JSON_MODE; then
    # Build features array
    features_json=""
    for feature in "${FEATURES[@]}"; do
        if [ -n "$features_json" ]; then
            features_json="$features_json,"
        fi
        features_json="$features_json$(get_feature_info "$feature")"
    done

    # Build main JSON object
    printf '{'
    printf '"project":"%s",' "$(json_escape "$PROJECT_NAME")"
    printf '"repo_root":"%s",' "$(json_escape "$REPO_ROOT")"
    printf '"specs_dir":"%s",' "$(json_escape "$SPECS_DIR")"
    printf '"has_git":%s,' "$HAS_GIT"
    printf '"branch":"%s",' "$(json_escape "$CURRENT_BRANCH")"
    printf '"is_feature_branch":%s,' "$IS_FEATURE_BRANCH"
    printf '"constitution":{"exists":%s,"path":"%s"},' "$CONSTITUTION_EXISTS" "$(json_escape "$CONSTITUTION_PATH")"
    printf '"feature_count":%d,' "${#FEATURES[@]}"

    if [ -n "$RESOLVED_TARGET" ]; then
        printf '"target_feature":"%s",' "$(json_escape "$RESOLVED_TARGET")"
    else
        printf '"target_feature":null,'
    fi

    printf '"features":[%s]' "$features_json"
    printf '}\n'
else
    echo "Project Status Discovery"
    echo "========================"
    echo ""
    echo "Project: $PROJECT_NAME"
    echo "Root: $REPO_ROOT"
    echo "Specs: $SPECS_DIR"
    echo "Git: $HAS_GIT"
    echo "Branch: $CURRENT_BRANCH"
    echo "Feature Branch: $IS_FEATURE_BRANCH"
    echo "Constitution: $CONSTITUTION_EXISTS ($CONSTITUTION_PATH)"
    echo ""

    if [ -n "$RESOLVED_TARGET" ]; then
        echo "Target Feature: $RESOLVED_TARGET"
        echo ""
    fi

    echo "Features (${#FEATURES[@]}):"
    echo ""

    if [ ${#FEATURES[@]} -eq 0 ]; then
        echo "  (none)"
    else
        for feature in "${FEATURES[@]}"; do
            get_feature_info "$feature"
        done
    fi
fi
