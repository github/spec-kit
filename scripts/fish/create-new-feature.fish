#!/usr/bin/env fish

set -l JSON_MODE false
set -l FEATURE_DESCRIPTION

for arg in $argv
    switch $arg
        case --json
            set JSON_MODE true
        case --help -h
            echo "Usage: $argv[0] [--json] <feature_description>"
            exit 0
        case '*'
            # Concatenate all non-flag arguments as the feature description
            if test -z "$FEATURE_DESCRIPTION"
                set FEATURE_DESCRIPTION $arg
            else
                set FEATURE_DESCRIPTION "$FEATURE_DESCRIPTION $arg"
            end
    end
end

if test -z "$FEATURE_DESCRIPTION"
    echo "Usage: $argv[0] [--json] <feature_description>" >&2
    exit 1
end

# Function to find the repository root by searching for existing project markers
function find_repo_root
    set -l dir $argv[1]
    while test "$dir" != "/"
        if test -d "$dir/.git"; or test -d "$dir/.specify"
            echo $dir
            return 0
        end
        set dir (dirname "$dir")
    end
    return 1
end

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
set -l SCRIPT_DIR (dirname (status filename))
set -l REPO_ROOT
set -l HAS_GIT false

if git rev-parse --show-toplevel >/dev/null 2>&1
    set REPO_ROOT (git rev-parse --show-toplevel)
    set HAS_GIT true
else
    set REPO_ROOT (find_repo_root "$SCRIPT_DIR")
    if test -z "$REPO_ROOT"
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    end
end

cd "$REPO_ROOT"

set -l SPECS_DIR "$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

set -l HIGHEST 0
if test -d "$SPECS_DIR"
    for dir in $SPECS_DIR/*
        if not test -d "$dir"
            continue
        end
        set -l dirname (basename "$dir")
        # Extract leading numbers
        set -l number (string match -r '^[0-9]+' $dirname)
        if test -n "$number"
            # Convert to decimal (remove leading zeros)
            set number (math $number)
            if test $number -gt $HIGHEST
                set HIGHEST $number
            end
        end
    end
end

set -l NEXT (math $HIGHEST + 1)
set -l FEATURE_NUM (printf "%03d" $NEXT)

# Convert feature description to branch name
set -l BRANCH_NAME (echo "$FEATURE_DESCRIPTION" | string lower | string replace -ar '[^a-z0-9]' '-' | string replace -ar -- '-+' '-' | string trim -c '-')
# Get first 3 words
set -l WORDS (echo "$BRANCH_NAME" | string split '-' | head -3 | string join '-')
set BRANCH_NAME "$FEATURE_NUM-$WORDS"

if test "$HAS_GIT" = true
    git checkout -b "$BRANCH_NAME"
else
    echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME" >&2
end

set -l FEATURE_DIR "$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR"

set -l TEMPLATE "$REPO_ROOT/.specify/templates/spec-template.md"
set -l SPEC_FILE "$FEATURE_DIR/spec.md"
if test -f "$TEMPLATE"
    cp "$TEMPLATE" "$SPEC_FILE"
else
    touch "$SPEC_FILE"
end

# Set the SPECIFY_FEATURE environment variable for the current session
set -gx SPECIFY_FEATURE "$BRANCH_NAME"

if test $JSON_MODE = true
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
end
