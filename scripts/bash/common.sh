#!/usr/bin/env bash
# Common functions and variables for all scripts

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"
    local repo_root="${3:-$(get_repo_root)}"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    # Load branch template to build validation pattern
    local template
    template=$(load_branch_template "$repo_root")
    if [[ -z "$template" ]]; then
        template="{number}-{short_name}"
    fi

    # Build a regex pattern from template by replacing placeholders
    # {number} -> [0-9]{3}
    # {short_name} -> .+
    # {username}, {email_prefix} -> [a-z0-9-]+
    local pattern="$template"

    # First, replace placeholders with neutral tokens so we can safely escape
    pattern="${pattern//\{number\}/__NUMBER__}"
    pattern="${pattern//\{short_name\}/__SHORT_NAME__}"
    pattern="${pattern//\{username\}/__USERNAME__}"
    pattern="${pattern//\{email_prefix\}/__EMAIL_PREFIX__}"
    # Escape all regex metacharacters in the remaining literal text
    pattern=$(printf '%s' "$pattern" | sed 's/[][\\.^$*+?(){}|]/\\&/g')
    # Replace tokens with their intended regex fragments
    pattern="${pattern//__NUMBER__/[0-9]{3}}"
    pattern="${pattern//__SHORT_NAME__/.+}"
    pattern="${pattern//__USERNAME__/[a-z0-9-]+}"
    pattern="${pattern//__EMAIL_PREFIX__/[a-z0-9.-]+}"

    pattern="^${pattern}$"

    if [[ ! "$branch" =~ $pattern ]]; then
        # Build example from template
        local example="$template"
        example=$(echo "$example" | sed 's/{number}/001/g')
        example=$(echo "$example" | sed 's/{short_name}/feature-name/g')
        example=$(echo "$example" | sed 's/{username}/jdoe/g')
        example=$(echo "$example" | sed 's/{email_prefix}/jdoe/g')
        
        echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
        echo "Feature branches should match pattern: $template" >&2
        echo "Example: $example" >&2
        return 1
    fi

    return 0
}

get_feature_dir() { echo "$1/specs/$2"; }

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
# Supports template-based branch names like "jdoe/001-feature" where number appears after prefix
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir="$repo_root/specs"

    # Load branch template to understand where {number} appears
    local template
    template=$(load_branch_template "$repo_root")
    if [[ -z "$template" ]]; then
        template="{number}-{short_name}"
    fi

    # Build regex to extract the numeric portion based on template structure
    # Replace {number} with capture group, other placeholders with matchers
    local extract_pattern="$template"
    extract_pattern=$(echo "$extract_pattern" | sed 's/{number}/([0-9]\{3\})/g')
    extract_pattern=$(echo "$extract_pattern" | sed 's/{short_name}/.\+/g')
    extract_pattern=$(echo "$extract_pattern" | sed 's/{username}/[a-z0-9-]\+/g')
    extract_pattern=$(echo "$extract_pattern" | sed 's/{email_prefix}/[a-z0-9.-]\+/g')
    extract_pattern="^${extract_pattern}$"

    # Extract numeric prefix from branch based on template pattern
    if [[ ! "$branch_name" =~ $extract_pattern ]]; then
        # If branch doesn't match template, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    fi

    local prefix="${BASH_REMATCH[1]}"
    
    # Determine the search path based on template structure (prefix before {number})
    local template_prefix=""
    if [[ "$template" =~ ^(.*)\{number\} ]]; then
        template_prefix="${BASH_REMATCH[1]}"
    fi
    
    local search_dir="$specs_dir"
    if [[ -n "$template_prefix" && "$template_prefix" == *"/"* ]]; then
        # Template has path prefix (e.g., "{username}/") - extract from branch
        local branch_prefix=""
        if [[ "$branch_name" =~ ^(.*/)${prefix}- ]]; then
            branch_prefix="${BASH_REMATCH[1]}"
        fi
        # Remove trailing slash and join with specs dir
        search_dir="$specs_dir/${branch_prefix%/}"
    fi

    # Search for directories starting with this prefix number
    local matches=()
    if [[ -d "$search_dir" ]]; then
        for dir in "$search_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$dir")
            fi
        done
    fi

    # Handle results
    if [[ ${#matches[@]} -eq 0 ]]; then
        # No match found - return the branch name path (will fail later with clear error)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # Exactly one match - perfect!
        echo "${matches[0]}"
    else
        # Multiple matches - this shouldn't happen with proper naming convention
        local match_names=""
        for m in "${matches[@]}"; do
            match_names="$match_names $(basename "$m")"
        done
        echo "ERROR: Multiple spec directories found with prefix '$prefix':$match_names" >&2
        echo "Please ensure only one spec directory exists per numeric prefix." >&2
        echo "$specs_dir/$branch_name"  # Return something to avoid breaking the script
    fi
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

# =============================================================================
# TOML Settings Functions (for branch template customization)
# =============================================================================

# Parse a single key from a TOML file
# Usage: get_toml_value "file.toml" "branch.template"
# Supports dotted keys by searching within [section] blocks
get_toml_value() {
    local file="$1"
    local key="$2"
    
    [[ ! -f "$file" ]] && return 1
    
    # Handle dotted keys like "branch.template"
    if [[ "$key" == *.* ]]; then
        local section="${key%%.*}"
        local subkey="${key#*.}"
        # Find the section and extract the key value
        awk -v section="$section" -v key="$subkey" '
            BEGIN { in_section = 0 }
            /^\[/ { 
                gsub(/[\[\]]/, "")
                in_section = ($0 == section)
            }
            in_section && $0 ~ "^"key"[[:space:]]*=" {
                sub(/^[^=]*=[[:space:]]*/, "")
                gsub(/^"|"$/, "")  # Remove surrounding quotes
                print
                exit
            }
        ' "$file"
    else
        # Simple key without section
        grep -E "^${key}[[:space:]]*=" "$file" 2>/dev/null | \
            sed 's/.*=[[:space:]]*"\([^"]*\)".*/\1/' | head -1
    fi
}

# Load branch template from settings file
# Returns: template string or empty if not found
load_branch_template() {
    local repo_root="${1:-$(get_repo_root)}"
    local settings_file="$repo_root/.specify/settings.toml"
    
    if [[ -f "$settings_file" ]]; then
        get_toml_value "$settings_file" "branch.template"
    fi
}

# =============================================================================
# Username and Email Resolution Functions
# =============================================================================

# Resolve {username} variable from Git config or OS fallback
# Returns: normalized username (lowercase, hyphens for special chars)
resolve_username() {
    local username
    username=$(git config user.name 2>/dev/null || echo "")
    
    if [[ -z "$username" ]]; then
        # Fallback to OS username
        username="${USER:-${USERNAME:-unknown}}"
    fi
    
    # Normalize: lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens
    echo "$username" | tr '[:upper:]' '[:lower:]' | \
        sed 's/[^a-z0-9]/-/g' | \
        sed 's/-\+/-/g' | \
        sed 's/^-//' | \
        sed 's/-$//'
}

# Resolve {email_prefix} variable from Git config
# Returns: email prefix (portion before @) or empty string
resolve_email_prefix() {
    local email
    email=$(git config user.email 2>/dev/null || echo "")
    
    if [[ -n "$email" && "$email" == *@* ]]; then
        echo "${email%%@*}" | tr '[:upper:]' '[:lower:]'
    fi
    # Returns empty string if no email configured (per FR-002 clarification)
}

# =============================================================================
# Branch Name Validation Functions
# =============================================================================

# Validate branch name against Git rules
# Args: $1 = branch name
# Returns: 0 if valid, 1 if invalid (prints error to stderr)
validate_branch_name() {
    local name="$1"
    
    # Cannot be empty
    if [[ -z "$name" ]]; then
        echo "Error: Branch name cannot be empty" >&2
        return 1
    fi
    
    # Cannot start with hyphen
    if [[ "$name" == -* ]]; then
        echo "Error: Branch name cannot start with hyphen: $name" >&2
        return 1
    fi
    
    # Cannot contain ..
    if [[ "$name" == *..* ]]; then
        echo "Error: Branch name cannot contain '..': $name" >&2
        return 1
    fi
    
    # Cannot contain forbidden characters: ~ ^ : ? * [ \
    if [[ "$name" =~ [~\^:\?\*\[\\] ]]; then
        echo "Error: Branch name contains invalid characters (~^:?*[\\): $name" >&2
        return 1
    fi
    
    # Cannot end with .lock
    if [[ "$name" == *.lock ]]; then
        echo "Error: Branch name cannot end with '.lock': $name" >&2
        return 1
    fi
    
    # Cannot end with /
    if [[ "$name" == */ ]]; then
        echo "Error: Branch name cannot end with '/': $name" >&2
        return 1
    fi
    
    # Cannot contain //
    if [[ "$name" == *//* ]]; then
        echo "Error: Branch name cannot contain '//': $name" >&2
        return 1
    fi
    
    # Check max length (244 bytes for GitHub)
    if [[ ${#name} -gt 244 ]]; then
        echo "Warning: Branch name exceeds 244 bytes (GitHub limit): $name" >&2
        # Return success but warn - truncation handled elsewhere
    fi
    
    return 0
}

# =============================================================================
# Per-User Number Scoping Functions
# =============================================================================

# Get highest feature number for a specific prefix pattern
# Args: $1 = prefix (e.g., "johndoe/" or "feature/johndoe/")
# Returns: highest number found (0 if none)
get_highest_for_prefix() {
    local prefix="$1"
    local repo_root="${2:-$(get_repo_root)}"
    local specs_dir="$repo_root/specs"
    local highest=0
    
    # Escape special regex characters in prefix for branch matching
    local escaped_prefix
    escaped_prefix=$(printf '%s' "$prefix" | sed 's/[.[\*^$()+?{|\\]/\\&/g')
    
    # Check specs directory for matching directories
    # For slashed prefixes (e.g., "johndoe/"), the structure is specs/johndoe/001-feature/
    # We need to navigate into the prefix path and match numbered directories there
    if [[ -d "$specs_dir" ]]; then
        # Check if prefix contains or ends with slash (indicating nested structure)
        # e.g., "johndoe/" or "feature/johndoe/" both indicate nested directories
        if [[ "$prefix" == *"/"* ]]; then
            # Slashed prefix: navigate to the nested directory and look for numbered dirs
            # Remove trailing slash for path joining
            local prefix_path="${prefix%/}"
            local prefix_dir="$specs_dir/$prefix_path"
            if [[ -d "$prefix_dir" ]]; then
                for dir in "$prefix_dir"/*; do
                    [[ -d "$dir" ]] || continue
                    local dirname
                    dirname=$(basename "$dir")
                    # Match directories starting with 3-digit number
                    if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                        local num=$((10#${BASH_REMATCH[1]}))
                        if [[ "$num" -gt "$highest" ]]; then
                            highest=$num
                        fi
                    fi
                done
            fi
        else
            # Non-slashed prefix: look at immediate children with prefix pattern
            for dir in "$specs_dir"/"${prefix}"*; do
                [[ -d "$dir" ]] || continue
                local dirname
                dirname=$(basename "$dir")
                # Extract number after prefix: prefix + 3-digit number
                if [[ "$dirname" =~ ^${escaped_prefix}([0-9]{3})- ]]; then
                    local num=$((10#${BASH_REMATCH[1]}))
                    if [[ "$num" -gt "$highest" ]]; then
                        highest=$num
                    fi
                fi
            done
        fi
    fi
    
    # Also check git branches if available
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        local branches
        branches=$(git branch -a 2>/dev/null || echo "")
        if [[ -n "$branches" ]]; then
            while IFS= read -r branch; do
                # Clean branch name
                local clean_branch
                clean_branch=$(echo "$branch" | sed 's/^[* ]*//; s|^remotes/[^/]*/||')
                
                # Check if branch matches prefix pattern
                if [[ "$clean_branch" =~ ^${escaped_prefix}([0-9]{3})- ]]; then
                    local num=$((10#${BASH_REMATCH[1]}))
                    if [[ "$num" -gt "$highest" ]]; then
                        highest=$num
                    fi
                fi
            done <<< "$branches"
        fi
    fi
    
    echo "$highest"
}

