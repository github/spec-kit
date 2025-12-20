#!/usr/bin/env fish

# Parse command line arguments
set JSON_MODE false
set ARGS

for arg in $argv
    switch $arg
        case --json
            set JSON_MODE true
        case --help -h
            echo "Usage: setup-plan.fish [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
        case '*'
            set -a ARGS $arg
    end
end

# Get script directory and load common functions
set SCRIPT_DIR (dirname (status --current-filename))
source "$SCRIPT_DIR/common.fish"

# Get all paths and variables from common functions
eval (get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch $CURRENT_BRANCH $HAS_GIT; or exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template if it exists
set TEMPLATE "$REPO_ROOT/.specify/templates/plan-template.md"
if test -f "$TEMPLATE"
    cp "$TEMPLATE" "$IMPL_PLAN"
    echo "Copied plan template to $IMPL_PLAN"
else
    echo "Warning: Plan template not found at $TEMPLATE"
    # Create a basic plan file if template doesn't exist
    touch "$IMPL_PLAN"
end

# Output results
if test $JSON_MODE = true
    printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
        $FEATURE_SPEC $IMPL_PLAN $FEATURE_DIR $CURRENT_BRANCH $HAS_GIT
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN"
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
end
