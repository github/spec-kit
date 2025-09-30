#!/usr/bin/env fish

# Parse command line arguments
set -l JSON_MODE false

for arg in $argv
    switch $arg
        case --json
            set JSON_MODE true
        case --help -h
            echo "Usage: $argv[0] [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0
        case '*'
            # Ignore other arguments
    end
end

# Get script directory and load common functions
set -l SCRIPT_DIR (dirname (status filename))
source "$SCRIPT_DIR/common.fish"

# Declare variables before eval to ensure proper scope
set REPO_ROOT ""
set CURRENT_BRANCH ""
set HAS_GIT ""
set FEATURE_DIR ""
set FEATURE_SPEC ""
set IMPL_PLAN ""
set TASKS ""
set RESEARCH ""
set DATA_MODEL ""
set QUICKSTART ""
set CONTRACTS_DIR ""

# Get all paths and variables from common functions
eval (get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT"; or exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template if it exists
set -l TEMPLATE "$REPO_ROOT/.specify/templates/plan-template.md"
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
        "$FEATURE_SPEC" "$IMPL_PLAN" "$FEATURE_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
end
