#!/usr/bin/env bash
# Decompose parent feature spec into capabilities
set -e

JSON_MODE=false
SPEC_PATH=""

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json] [path/to/parent/spec.md]"
            echo "Decomposes a parent feature spec into capability-based breakdown"
            exit 0
            ;;
        *) SPEC_PATH="$arg" ;;
    esac
done

# Determine spec path
if [ -z "$SPEC_PATH" ]; then
    # Try to find spec.md in current branch's specs directory
    REPO_ROOT=$(git rev-parse --show-toplevel)
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

    # Extract feature ID from branch name (username/jira-123.feature-name -> jira-123.feature-name)
    FEATURE_ID=$(echo "$BRANCH_NAME" | sed 's/^[^/]*\///')

    SPEC_PATH="$REPO_ROOT/specs/$FEATURE_ID/spec.md"
fi

# Validate spec exists
if [ ! -f "$SPEC_PATH" ]; then
    echo "ERROR: Spec file not found at $SPEC_PATH" >&2
    echo "Usage: $0 [path/to/parent/spec.md]" >&2
    exit 1
fi

SPEC_DIR=$(dirname "$SPEC_PATH")
REPO_ROOT=$(git rev-parse --show-toplevel)

# Create capabilities.md from template
DECOMPOSE_TEMPLATE="$REPO_ROOT/.specify/templates/decompose-template.md"
CAPABILITIES_FILE="$SPEC_DIR/capabilities.md"

if [ ! -f "$DECOMPOSE_TEMPLATE" ]; then
    echo "ERROR: Decompose template not found at $DECOMPOSE_TEMPLATE" >&2
    exit 1
fi

# Copy template to capabilities.md
cp "$DECOMPOSE_TEMPLATE" "$CAPABILITIES_FILE"

# Output results
if $JSON_MODE; then
    printf '{"SPEC_PATH":"%s","CAPABILITIES_FILE":"%s","SPEC_DIR":"%s"}\n' \
        "$SPEC_PATH" "$CAPABILITIES_FILE" "$SPEC_DIR"
else
    echo "SPEC_PATH: $SPEC_PATH"
    echo "CAPABILITIES_FILE: $CAPABILITIES_FILE"
    echo "SPEC_DIR: $SPEC_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Edit $CAPABILITIES_FILE to define capabilities"
    echo "2. AI will create capability subdirectories (cap-001/, cap-002/, ...)"
    echo "3. AI will generate scoped spec.md in each capability directory"
fi
