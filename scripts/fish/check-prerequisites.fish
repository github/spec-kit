#!/usr/bin/env fish

# Consolidated prerequisite checking script
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.fish [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --require-tasks     Require tasks.md to exist (for implementation phase)
#   --include-tasks     Include tasks.md in AVAILABLE_DOCS list
#   --paths-only        Only output path variables (no validation)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...", "AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n AVAILABLE_DOCS: \n ✓/✗ file.md
#   Paths only: REPO_ROOT: ... \n BRANCH: ... \n FEATURE_DIR: ... etc.

# Parse command line arguments
set JSON_MODE false
set REQUIRE_TASKS false
set INCLUDE_TASKS false
set PATHS_ONLY false

for arg in $argv
    switch $arg
        case --json
            set JSON_MODE true
        case --require-tasks
            set REQUIRE_TASKS true
        case --include-tasks
            set INCLUDE_TASKS true
        case --paths-only
            set PATHS_ONLY true
        case --help -h
            echo "Usage: check-prerequisites.fish [OPTIONS]"
            echo ""
            echo "Consolidated prerequisite checking for Spec-Driven Development workflow."
            echo ""
            echo "OPTIONS:"
            echo "  --json              Output in JSON format"
            echo "  --require-tasks     Require tasks.md to exist (for implementation phase)"
            echo "  --include-tasks     Include tasks.md in AVAILABLE_DOCS list"
            echo "  --paths-only        Only output path variables (no prerequisite validation)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "EXAMPLES:"
            echo "  # Check task prerequisites (plan.md required)"
            echo "  ./check-prerequisites.fish --json"
            echo "  "
            echo "  # Check implementation prerequisites (plan.md + tasks.md required)"
            echo "  ./check-prerequisites.fish --json --require-tasks --include-tasks"
            echo "  "
            echo "  # Get feature paths only (no validation)"
            echo "  ./check-prerequisites.fish --paths-only"
            exit 0
        case '*'
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
    end
end

# Source common functions
set SCRIPT_DIR (dirname (status --current-filename))
source "$SCRIPT_DIR/common.fish"

# Get feature paths and validate branch
eval (get_feature_paths)
check_feature_branch $CURRENT_BRANCH $HAS_GIT; or exit 1

# If paths-only mode, output paths and exit
if test $PATHS_ONLY = true
    if test $JSON_MODE = true
        # Minimal JSON paths payload (no validation performed)
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","FEATURE_DIR":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s"}\n' \
            $REPO_ROOT $CURRENT_BRANCH $FEATURE_DIR $FEATURE_SPEC $IMPL_PLAN $TASKS
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "FEATURE_DIR: $FEATURE_DIR"
        echo "FEATURE_SPEC: $FEATURE_SPEC"
        echo "IMPL_PLAN: $IMPL_PLAN"
        echo "TASKS: $TASKS"
    end
    exit 0
end

# Validate required directories and files
if not test -d "$FEATURE_DIR"
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run /speckit.specify first to create the feature structure." >&2
    exit 1
end

if not test -f "$IMPL_PLAN"
    echo "ERROR: plan.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit.plan first to create the implementation plan." >&2
    exit 1
end

# Check for tasks.md if required
if test $REQUIRE_TASKS = true; and not test -f "$TASKS"
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run /speckit.tasks first to create the task list." >&2
    exit 1
end

# Build list of available documents
set docs

# Always check these optional docs
test -f "$RESEARCH"; and set -a docs "research.md"
test -f "$DATA_MODEL"; and set -a docs "data-model.md"

# Check contracts directory (only if it exists and has files)
if test -d "$CONTRACTS_DIR"; and test -n (ls -A "$CONTRACTS_DIR" 2>/dev/null)
    set -a docs "contracts/"
end

test -f "$QUICKSTART"; and set -a docs "quickstart.md"

# Include tasks.md if requested and it exists
if test $INCLUDE_TASKS = true; and test -f "$TASKS"
    set -a docs "tasks.md"
end

# Output results
if test $JSON_MODE = true
    # Build JSON array of documents
    if test (count $docs) -eq 0
        set json_docs "[]"
    else
        set json_parts
        for doc in $docs
            set -a json_parts "\"$doc\""
        end
        set json_docs "["(string join "," $json_parts)"]"
    end
    
    printf '{"FEATURE_DIR":"%s","AVAILABLE_DOCS":%s}\n' $FEATURE_DIR $json_docs
else
    # Text output
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    check_file $RESEARCH "research.md"
    check_file $DATA_MODEL "data-model.md"
    check_dir $CONTRACTS_DIR "contracts/"
    check_file $QUICKSTART "quickstart.md"
    
    if test $INCLUDE_TASKS = true
        check_file $TASKS "tasks.md"
    end
end
