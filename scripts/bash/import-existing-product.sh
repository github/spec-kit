#!/usr/bin/env bash

set -e

JSON_MODE=false
VERSION_NAME=""
CREATE_BRANCH=true
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --version)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --version requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            if [[ "$next_arg" == --* ]]; then
                echo 'Error: --version requires a value' >&2
                exit 1
            fi
            VERSION_NAME="$next_arg"
            ;;
        --no-branch)
            CREATE_BRANCH=false
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--version <name>] [--no-branch] [version_identifier]"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --version <name>    Provide a custom version name for the import"
            echo "  --no-branch         Don't create/switch git branch (use current branch)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --json 'baseline'"
            echo "  $0 --version 'initial-import'"
            echo "  $0                  # Auto-generates as 001-import-baseline"
            exit 0
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
    i=$((i + 1))
done

# Use positional arg as version name if not set via --version
if [ -z "$VERSION_NAME" ] && [ ${#ARGS[@]} -gt 0 ]; then
    VERSION_NAME="${ARGS[0]}"
fi

# Function to find the repository root
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

# Function to get highest feature number from specs directory
get_highest_feature_number() {
    local specs_dir="$1"
    local highest=0

    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            # Match pattern ###-* (e.g., 001-feature-name)
            if echo "$dirname" | grep -qE '^[0-9]{3}-'; then
                number=$(echo "$dirname" | grep -oE '^[0-9]{3}' || echo "0")
                number=$((10#$number))
                if [ "$number" -gt "$highest" ]; then
                    highest=$number
                fi
            fi
        done
    fi

    echo "$highest"
}

# Function to get highest number from git branches
get_highest_from_branches() {
    local highest=0

    # Get all branches (local and remote)
    branches=$(git branch -a 2>/dev/null || echo "")

    if [ -n "$branches" ]; then
        while IFS= read -r branch; do
            # Clean branch name: remove leading markers and remote prefixes
            clean_branch=$(echo "$branch" | sed 's/^[* ]*//; s|^remotes/[^/]*/||')

            # Extract feature number if branch matches pattern ###-*
            if echo "$clean_branch" | grep -q '^[0-9]\{3\}-'; then
                number=$(echo "$clean_branch" | grep -o '^[0-9]\{3\}' || echo "0")
                number=$((10#$number))
                if [ "$number" -gt "$highest" ]; then
                    highest=$number
                fi
            fi
        done <<< "$branches"
    fi

    echo "$highest"
}

# Function to clean and format a name for filesystem/branch use
clean_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Resolve repository root
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Fetch latest branches if git is available
if [ "$HAS_GIT" = true ]; then
    git fetch --all --prune 2>/dev/null || true
fi

# Determine the next feature number
HIGHEST_SPEC=$(get_highest_feature_number "$SPECS_DIR")
HIGHEST_BRANCH=0
if [ "$HAS_GIT" = true ]; then
    HIGHEST_BRANCH=$(get_highest_from_branches)
fi

# Use the higher of the two
if [ "$HIGHEST_BRANCH" -gt "$HIGHEST_SPEC" ]; then
    HIGHEST=$HIGHEST_BRANCH
else
    HIGHEST=$HIGHEST_SPEC
fi

NEXT_NUM=$((HIGHEST + 1))
FEATURE_NUM=$(printf "%03d" "$NEXT_NUM")

# Determine the suffix for the import
if [ -z "$VERSION_NAME" ]; then
    # Default suffix for imports
    IMPORT_SUFFIX="import-baseline"
else
    # Clean the provided name
    IMPORT_SUFFIX="import-$(clean_name "$VERSION_NAME")"
fi

# Create the branch/directory name in standard ###-name format
BRANCH_NAME="${FEATURE_NUM}-${IMPORT_SUFFIX}"

# Create git branch if requested and git is available
if [ "$HAS_GIT" = true ] && [ "$CREATE_BRANCH" = true ]; then
    git checkout -b "$BRANCH_NAME"
else
    if [ "$HAS_GIT" = true ] && [ "$CREATE_BRANCH" = false ]; then
        >&2 echo "[specify] Skipping branch creation (--no-branch specified)"
    elif [ "$HAS_GIT" = false ]; then
        >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
    fi
fi

# Create directory structure
SPEC_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$SPEC_DIR"
mkdir -p "$SPEC_DIR/analysis"
mkdir -p "$SPEC_DIR/checklists"

# Create spec file from template or empty
TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
SPEC_FILE="$SPEC_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$SPEC_FILE"
else
    touch "$SPEC_FILE"
fi

# Create placeholder analysis files
touch "$SPEC_DIR/analysis/architecture.md"
touch "$SPEC_DIR/analysis/entities.md"
touch "$SPEC_DIR/analysis/features.md"

# Set environment variable
export SPECIFY_FEATURE="$BRANCH_NAME"

# Get current date
IMPORT_DATE=$(date +%Y-%m-%d)

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_DIR":"%s","SPEC_FILE":"%s","ANALYSIS_DIR":"%s","IMPORT_DATE":"%s","FEATURE_NUM":"%s"}\n' \
        "$BRANCH_NAME" "$SPEC_DIR" "$SPEC_FILE" "$SPEC_DIR/analysis" "$IMPORT_DATE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_DIR: $SPEC_DIR"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "ANALYSIS_DIR: $SPEC_DIR/analysis"
    echo "IMPORT_DATE: $IMPORT_DATE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
