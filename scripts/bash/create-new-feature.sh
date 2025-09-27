#!/usr/bin/env bash

set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] <feature_description>"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] <feature_description>" >&2
    exit 1
fi

# Function to find the repository root by searching for existing project markers
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specs" ] || [ -d "$dir/.specify" ]; then
            # If we stopped inside the .specs folder, return its parent
            if [ "$(basename "$dir")" = ".specs" ]; then
                dirname "$dir"
            else
                echo "$dir"
            fi
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

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

SPECS_ROOT="$REPO_ROOT/.specs"
SPECIFY_ROOT="$SPECS_ROOT/.specify"
# Load layout to determine feature location and filenames
if [ -x "$SCRIPT_DIR/read-layout.sh" ]; then
    eval $("$SCRIPT_DIR/read-layout.sh")
fi
# Determine parent folder for numbering using a dummy branch placeholder
DUMMY_BRANCH="000-placeholder"
DUMMY_PATH="$(get_feature_dir "$REPO_ROOT" "$DUMMY_BRANCH")"
FEATURE_PARENT_DIR="$(dirname "$DUMMY_PATH")"
mkdir -p "$FEATURE_PARENT_DIR"

HIGHEST=0
if [ -d "$FEATURE_PARENT_DIR" ]; then
    for dir in "$FEATURE_PARENT_DIR"/*; do
        [ -d "$dir" ] || continue
        dirname=$(basename "$dir")
        number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
        number=$((10#$number))
        if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
    done
fi

NEXT=$((HIGHEST + 1))
FEATURE_NUM=$(printf "%03d" "$NEXT")

BRANCH_NAME=$(echo "$FEATURE_DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
WORDS=$(echo "$BRANCH_NAME" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')
BRANCH_NAME="${FEATURE_NUM}-${WORDS}"

if [ "$HAS_GIT" = true ]; then
    git checkout -b "$BRANCH_NAME"
else
    >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

# Now compute final feature directory
FEATURE_DIR="$(get_feature_dir "$REPO_ROOT" "$BRANCH_NAME")"
mkdir -p "$FEATURE_DIR"

SPEC_FILE="$FEATURE_DIR/${LAYOUT_FILES_FPRD:-fprd.md}"
# Resolve content template via resolver (assets override if present)
RESOLVED_TEMPLATE="$SPECIFY_ROOT/templates/spec-template.md"
if [ -x "$SCRIPT_DIR/resolve-template.sh" ]; then
    if RES_JSON="$($SCRIPT_DIR/resolve-template.sh --json spec 2>/dev/null)"; then
        RESOLVED_TEMPLATE="$(printf '%s' "$RES_JSON" | sed -n 's/.*"TEMPLATE_PATH":"\([^"]*\)".*/\1/p')"
    fi
fi
if [ -f "$RESOLVED_TEMPLATE" ]; then cp "$RESOLVED_TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

# Optional legacy stub for spec.md if enabled
if [ "${LAYOUT_COMPAT_WRITE_STUB_SPEC:-$LAYOUT_COMPAT_WRITE_STUB_SPEC}" = "true" ]; then
    STUB_NAME="${LAYOUT_COMPAT_STUB_NAME:-spec.md}"
    if [ "$STUB_NAME" != "$(basename "$SPEC_FILE")" ]; then
        printf "# Legacy spec stub\n\nThis repository uses a declarative layout. The canonical feature PRD lives at: \n\n- %s\n" "$(basename "$SPEC_FILE")" > "$FEATURE_DIR/$STUB_NAME"
    fi
fi

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
