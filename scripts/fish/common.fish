#!/usr/bin/env fish
# Common functions and variables for all fish scripts

# Get repository root, with fallback for non-git repositories
function get_repo_root
    if git rev-parse --show-toplevel >/dev/null 2>&1
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        set -l script_dir (dirname (status filename))
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
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1
        git rev-parse --abbrev-ref HEAD
        return
    end
    
    # For non-git repos, try to find the latest feature directory
    set -l repo_root (get_repo_root)
    set -l specs_dir "$repo_root/specs"
    
    if test -d "$specs_dir"
        set -l latest_feature ""
        set -l highest 0
        
        for dir in $specs_dir/*
            if test -d "$dir"
                set -l dirname (basename "$dir")
                # Check if dirname matches pattern XXX-
                set -l matches (string match -r '^([0-9]{3})-' $dirname)
                if test (count $matches) -gt 0
                    set -l number (string sub -s 1 -l 3 $dirname)
                    # Convert to decimal (remove leading zeros)
                    set -l number (math $number)
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
    git rev-parse --show-toplevel >/dev/null 2>&1
end

function check_feature_branch
    set -l branch $argv[1]
    set -l has_git_repo $argv[2]
    
    # For non-git repos, we can't enforce branch naming but still provide output
    if test "$has_git_repo" != "true"
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    end
    
    # Check if branch matches pattern XXX-
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

function get_feature_paths
    set -l repo_root (get_repo_root)
    set -l current_branch (get_current_branch)
    set -l has_git_repo "false"
    
    if has_git
        set has_git_repo "true"
    end
    
    set -l feature_dir (get_feature_dir "$repo_root" "$current_branch")
    
    # Output the paths in a format that can be eval'd in fish
    # Use semicolons to ensure commands execute in sequence
    echo "set REPO_ROOT '$repo_root'; set CURRENT_BRANCH '$current_branch'; set HAS_GIT '$has_git_repo'; set FEATURE_DIR '$feature_dir'; set FEATURE_SPEC '$feature_dir/spec.md'; set IMPL_PLAN '$feature_dir/plan.md'; set TASKS '$feature_dir/tasks.md'; set RESEARCH '$feature_dir/research.md'; set DATA_MODEL '$feature_dir/data-model.md'; set QUICKSTART '$feature_dir/quickstart.md'; set CONTRACTS_DIR '$feature_dir/contracts'"
end

function check_file
    if test -f "$argv[1]"
        echo "  ✓ $argv[2]"
    else
        echo "  ✗ $argv[2]"
    end
end

function check_dir
    if test -d "$argv[1]"; and test -n "(ls -A "$argv[1]" 2>/dev/null)"
        echo "  ✓ $argv[2]"
    else
        echo "  ✗ $argv[2]"
    end
end
