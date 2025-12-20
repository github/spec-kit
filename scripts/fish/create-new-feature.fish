#!/usr/bin/env fish

set JSON_MODE false
set SHORT_NAME ""
set BRANCH_NUMBER ""
set ARGS

set i 1
while test $i -le (count $argv)
    set arg $argv[$i]
    switch $arg
        case --json
            set JSON_MODE true
        case --short-name
            if test (math $i + 1) -gt (count $argv)
                echo 'Error: --short-name requires a value' >&2
                exit 1
            end
            set i (math $i + 1)
            set next_arg $argv[$i]
            # Check if the next argument is another option
            if string match -q -- '--*' $next_arg
                echo 'Error: --short-name requires a value' >&2
                exit 1
            end
            set SHORT_NAME $next_arg
        case --number
            if test (math $i + 1) -gt (count $argv)
                echo 'Error: --number requires a value' >&2
                exit 1
            end
            set i (math $i + 1)
            set next_arg $argv[$i]
            if string match -q -- '--*' $next_arg
                echo 'Error: --number requires a value' >&2
                exit 1
            end
            set BRANCH_NUMBER $next_arg
        case --help -h
            echo "Usage: create-new-feature.fish [--json] [--short-name <name>] [--number N] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --short-name <name> Provide a custom short name (2-4 words) for the branch"
            echo "  --number N          Specify branch number manually (overrides auto-detection)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  create-new-feature.fish 'Add user authentication system' --short-name 'user-auth'"
            echo "  create-new-feature.fish 'Implement OAuth2 integration for API' --number 5"
            exit 0
        case '*'
            set -a ARGS $arg
    end
    set i (math $i + 1)
end

set FEATURE_DESCRIPTION (string join " " $ARGS)
if test -z "$FEATURE_DESCRIPTION"
    echo "Usage: create-new-feature.fish [--json] [--short-name <name>] [--number N] <feature_description>" >&2
    exit 1
end

# Function to find the repository root
function find_repo_root
    set dir $argv[1]
    while test "$dir" != "/"
        if test -d "$dir/.git"; or test -d "$dir/.specify"
            echo $dir
            return 0
        end
        set dir (dirname $dir)
    end
    return 1
end

# Function to get highest number from specs directory
function get_highest_from_specs
    set specs_dir $argv[1]
    set highest 0
    
    if test -d "$specs_dir"
        for dir in $specs_dir/*
            test -d "$dir"; or continue
            set dirname (basename $dir)
            set number (string match -r '^[0-9]+' $dirname; or echo "0")
            set number (math $number + 0)
            if test $number -gt $highest
                set highest $number
            end
        end
    end
    
    echo $highest
end

# Function to get highest number from git branches
function get_highest_from_branches
    set highest 0
    
    # Get all branches (local and remote)
    set branches (git branch -a 2>/dev/null; or echo "")
    
    if test -n "$branches"
        for branch in $branches
            # Clean branch name: remove leading markers and remote prefixes
            set clean_branch (echo $branch | sed 's/^[* ]*//; s|^remotes/[^/]*/||')
            
            # Extract feature number if branch matches pattern ###-*
            if string match -qr '^[0-9]{3}-' $clean_branch
                set number (string match -r '^[0-9]{3}' $clean_branch; or echo "0")
                set number (math $number + 0)
                if test $number -gt $highest
                    set highest $number
                end
            end
        end
    end
    
    echo $highest
end

# Function to check existing branches
function check_existing_branches
    set specs_dir $argv[1]

    # Fetch all remotes
    git fetch --all --prune 2>/dev/null; or true

    # Get highest number from ALL branches
    set highest_branch (get_highest_from_branches)

    # Get highest number from ALL specs
    set highest_spec (get_highest_from_specs $specs_dir)

    # Take the maximum of both
    set max_num $highest_branch
    if test $highest_spec -gt $max_num
        set max_num $highest_spec
    end

    # Return next number
    echo (math $max_num + 1)
end

# Function to clean and format a branch name
function clean_branch_name
    set name $argv[1]
    echo $name | string lower | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
end

# Resolve repository root
set SCRIPT_DIR (dirname (status --current-filename))

if git rev-parse --show-toplevel >/dev/null 2>&1
    set REPO_ROOT (git rev-parse --show-toplevel)
    set HAS_GIT true
else
    set REPO_ROOT (find_repo_root $SCRIPT_DIR)
    if test -z "$REPO_ROOT"
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    end
    set HAS_GIT false
end

cd $REPO_ROOT

set SPECS_DIR "$REPO_ROOT/specs"
mkdir -p $SPECS_DIR

# Function to generate branch name with stop word filtering
function generate_branch_name
    set description $argv[1]
    
    # Common stop words to filter out
    set stop_words '^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$'
    
    # Convert to lowercase and split into words
    set clean_name (echo $description | string lower | sed 's/[^a-z0-9]/ /g')
    
    # Filter words
    set meaningful_words
    for word in $clean_name
        # Skip empty words
        test -z "$word"; and continue
        
        # Keep words that are NOT stop words AND (length >= 3 OR are potential acronyms)
        if not echo $word | string match -qir $stop_words
            if test (string length $word) -ge 3
                set -a meaningful_words $word
            else if echo $description | string match -q "*"(string upper $word)"*"
                # Keep short words if they appear as uppercase in original
                set -a meaningful_words $word
            end
        end
    end
    
    # If we have meaningful words, use first 3-4 of them
    if test (count $meaningful_words) -gt 0
        set max_words 3
        if test (count $meaningful_words) -eq 4
            set max_words 4
        end
        
        set result ""
        set count 0
        for word in $meaningful_words
            if test $count -ge $max_words
                break
            end
            if test -n "$result"
                set result "$result-"
            end
            set result "$result$word"
            set count (math $count + 1)
        end
        echo $result
    else
        # Fallback to original logic
        set cleaned (clean_branch_name $description)
        echo $cleaned | string split '-' | string match -v '' | head -3 | string join '-'
    end
end

# Generate branch name
if test -n "$SHORT_NAME"
    # Use provided short name, just clean it up
    set BRANCH_SUFFIX (clean_branch_name $SHORT_NAME)
else
    # Generate from description with smart filtering
    set BRANCH_SUFFIX (generate_branch_name $FEATURE_DESCRIPTION)
end

# Determine branch number
if test -z "$BRANCH_NUMBER"
    if test $HAS_GIT = true
        # Check existing branches on remotes
        set BRANCH_NUMBER (check_existing_branches $SPECS_DIR)
    else
        # Fall back to local directory check
        set HIGHEST (get_highest_from_specs $SPECS_DIR)
        set BRANCH_NUMBER (math $HIGHEST + 1)
    end
end

# Force base-10 interpretation
set FEATURE_NUM (printf "%03d" (math $BRANCH_NUMBER + 0))
set BRANCH_NAME "$FEATURE_NUM-$BRANCH_SUFFIX"

# GitHub enforces a 244-byte limit on branch names
set MAX_BRANCH_LENGTH 244
if test (string length $BRANCH_NAME) -gt $MAX_BRANCH_LENGTH
    # Calculate how much we need to trim from suffix
    set MAX_SUFFIX_LENGTH (math $MAX_BRANCH_LENGTH - 4)
    
    # Truncate suffix
    set TRUNCATED_SUFFIX (string sub -l $MAX_SUFFIX_LENGTH $BRANCH_SUFFIX)
    # Remove trailing hyphen if truncation created one
    set TRUNCATED_SUFFIX (echo $TRUNCATED_SUFFIX | sed 's/-$//')
    
    set ORIGINAL_BRANCH_NAME $BRANCH_NAME
    set BRANCH_NAME "$FEATURE_NUM-$TRUNCATED_SUFFIX"
    
    echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit" >&2
    echo "[specify] Original: $ORIGINAL_BRANCH_NAME ("(string length $ORIGINAL_BRANCH_NAME)" bytes)" >&2
    echo "[specify] Truncated to: $BRANCH_NAME ("(string length $BRANCH_NAME)" bytes)" >&2
end

if test $HAS_GIT = true
    git checkout -b $BRANCH_NAME
else
    echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME" >&2
end

set FEATURE_DIR "$SPECS_DIR/$BRANCH_NAME"
mkdir -p $FEATURE_DIR

set TEMPLATE "$REPO_ROOT/.specify/templates/spec-template.md"
set SPEC_FILE "$FEATURE_DIR/spec.md"
if test -f "$TEMPLATE"
    cp $TEMPLATE $SPEC_FILE
else
    touch $SPEC_FILE
end

# Set the SPECIFY_FEATURE environment variable for the current session
set -gx SPECIFY_FEATURE $BRANCH_NAME

if test $JSON_MODE = true
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' $BRANCH_NAME $SPEC_FILE $FEATURE_NUM
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
end
