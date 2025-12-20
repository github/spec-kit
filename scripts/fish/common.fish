#!/usr/bin/env fish
# Common functions and variables for all Fish shell scripts

# Get repository root, with fallback for non-git repositories
function get_repo_root
    if git rev-parse --show-toplevel 2>/dev/null
        return 0
    else
        # Fall back to script location for non-git repos
        set script_dir (dirname (status --current-filename))
        cd $script_dir/../../.. && pwd
    end
end

# Get current branch, with fallback for non-git repositories
function get_current_branch
    # First check if SPECIFY_FEATURE environment variable is set
    if set -q SPECIFY_FEATURE; and test -n "$SPECIFY_FEATURE"
        echo $SPECIFY_FEATURE
        return
    end

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD 2>/dev/null
        return
    end

    # For non-git repos, try to find the latest feature directory
    set repo_root (get_repo_root)
    set specs_dir "$repo_root/specs"

    if test -d "$specs_dir"
        set latest_feature ""
        set highest 0

        for dir in $specs_dir/*
            if test -d "$dir"
                set dirname (basename $dir)
                if string match -qr '^([0-9]{3})-' $dirname
                    set number (string sub -l 3 $dirname)
                    # Remove leading zeros
                    set number (math $number + 0)
                    if test $number -gt $highest
                        set highest $number
                        set latest_feature $dirname
                    end
                end
            end
        end

        if test -n "$latest_feature"
            echo $latest_feature
            return
        end
    end

    echo "main"  # Final fallback
end

# Check if we have git available
function has_git
    git rev-parse --show-toplevel 2>/dev/null >/dev/null
    return $status
end

function check_feature_branch
    set branch $argv[1]
    set has_git_repo $argv[2]

    # For non-git repos, we can't enforce branch naming but still provide output
    if test "$has_git_repo" != "true"
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    end

    if not string match -qr '^[0-9]{3}-' $branch
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should be named like: 001-feature-name" >&2
        return 1
    end

    return 0
end

function get_feature_dir
    echo "$argv[1]/specs/$argv[2]"
end

# Find feature directory by numeric prefix instead of exact branch match
function find_feature_dir_by_prefix
    set repo_root $argv[1]
    set branch_name $argv[2]
    set specs_dir "$repo_root/specs"

    # Extract numeric prefix from branch
    if not string match -qr '^([0-9]{3})-' $branch_name
        # If branch doesn't have numeric prefix, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    end

    set prefix (string sub -l 3 $branch_name)

    # Search for directories in specs/ that start with this prefix
    set matches

    if test -d "$specs_dir"
        for dir in $specs_dir/$prefix-*
            if test -d "$dir"
                set -a matches (basename $dir)
            end
        end
    end

    # Handle results
    if test (count $matches) -eq 0
        # No match found
        echo "$specs_dir/$branch_name"
    else if test (count $matches) -eq 1
        # Exactly one match - perfect!
        echo "$specs_dir/$matches[1]"
    else
        # Multiple matches - this shouldn't happen
        echo "ERROR: Multiple spec directories found with prefix '$prefix': $matches" >&2
        echo "Please ensure only one spec directory exists per numeric prefix." >&2
        echo "$specs_dir/$branch_name"
    end
end

function get_feature_paths
    set repo_root (get_repo_root)
    set current_branch (get_current_branch)
    set has_git_repo "false"

    if has_git
        set has_git_repo "true"
    end

    # Use prefix-based lookup to support multiple branches per spec
    set feature_dir (find_feature_dir_by_prefix $repo_root $current_branch)

    echo "set REPO_ROOT '$repo_root';"
    echo "set CURRENT_BRANCH '$current_branch';"
    echo "set HAS_GIT '$has_git_repo';"
    echo "set FEATURE_DIR '$feature_dir';"
    echo "set FEATURE_SPEC '$feature_dir/spec.md';"
    echo "set IMPL_PLAN '$feature_dir/plan.md';"
    echo "set TASKS '$feature_dir/tasks.md';"
    echo "set RESEARCH '$feature_dir/research.md';"
    echo "set DATA_MODEL '$feature_dir/data-model.md';"
    echo "set QUICKSTART '$feature_dir/quickstart.md';"
    echo "set CONTRACTS_DIR '$feature_dir/contracts';"
end

function check_file
    if test -f "$argv[1]"
        echo "  ✓ $argv[2]"
    else
        echo "  ✗ $argv[2]"
    end
end

function check_dir
    if test -d "$argv[1]"; and test -n (ls -A $argv[1] 2>/dev/null)
        echo "  ✓ $argv[2]"
    else
        echo "  ✗ $argv[2]"
    end
end
