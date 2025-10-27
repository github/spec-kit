#!/usr/bin/env bash
# Workspace discovery and multi-repo support for spec-kit

# Detect if we're in a workspace (parent folder with multiple repos)
# or a single repo context
detect_workspace() {
    local current_dir="${1:-$(pwd)}"

    # Check if .specify/workspace.yml exists in current or parent directories
    local check_dir="$current_dir"
    while [[ "$check_dir" != "/" ]]; do
        if [[ -f "$check_dir/.specify/workspace.yml" ]]; then
            echo "$check_dir"
            return 0
        fi
        check_dir="$(dirname "$check_dir")"
    done

    # No workspace found
    return 1
}

# Get workspace root, or empty if not in workspace mode
get_workspace_root() {
    detect_workspace "${1:-$(pwd)}" 2>/dev/null || echo ""
}

# Check if current context is workspace mode
is_workspace_mode() {
    local workspace_root=$(get_workspace_root)
    [[ -n "$workspace_root" ]]
}

# Find all git repositories in a directory (non-recursive within repos)
# Usage: find_repos <search_path> [max_depth]
find_repos() {
    local search_path="${1:-.}"
    local max_depth="${2:-2}"

    # Find all .git directories, then get their parent directories
    find "$search_path" -maxdepth "$max_depth" -type d -name ".git" 2>/dev/null | while read -r git_dir; do
        dirname "$git_dir"
    done | sort
}

# Get repository name from path (basename of repo directory)
get_repo_name() {
    local repo_path="$1"
    basename "$repo_path"
}

# Parse workspace.yml to get repo configuration
# Usage: parse_workspace_config <workspace_root>
parse_workspace_config() {
    local workspace_root="$1"
    local config_file="$workspace_root/.specify/workspace.yml"

    if [[ ! -f "$config_file" ]]; then
        echo "ERROR: Workspace config not found: $config_file" >&2
        return 1
    fi

    # For now, just cat the file - in future could use yq or python for parsing
    cat "$config_file"
}

# Get target repos for a spec based on conventions
# Usage: get_target_repos_for_spec <workspace_root> <spec_id>
# Note: Strips Jira key prefix (e.g., proj-123.) for convention matching
get_target_repos_for_spec() {
    local workspace_root="$1"
    local spec_id="$2"
    local config_file="$workspace_root/.specify/workspace.yml"

    if [[ ! -f "$config_file" ]]; then
        echo "ERROR: Workspace config not found: $config_file" >&2
        return 1
    fi

    # Extract repos from config using grep/awk for simplicity
    # Looking for lines like:  "    - name: repo-name" under "repos:" section
    local all_repos=$(awk '/^repos:/,/^[a-z]/ {if (/^  - name:/) print $3}' "$config_file")

    # Strip Jira key prefix for convention matching
    # Example: proj-123.backend-api → backend-api
    local feature_name="$spec_id"
    if [[ "$spec_id" =~ ^[a-z]+-[0-9]+\.(.+)$ ]]; then
        feature_name="${BASH_REMATCH[1]}"
    fi

    # Apply convention-based matching using feature_name (without Jira key)
    local matched_repos=()

    # Read prefix rules from config
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]+([^:]+):.*\[([^\]]+)\] ]]; then
            local pattern="${BASH_REMATCH[1]}"
            local targets="${BASH_REMATCH[2]}"

            # Check if feature_name matches pattern (using stripped name)
            if [[ "$feature_name" == $pattern* ]]; then
                # Split targets by comma and add to matched_repos
                IFS=',' read -ra REPOS <<< "$targets"
                for repo in "${REPOS[@]}"; do
                    # Trim whitespace
                    repo=$(echo "$repo" | xargs)
                    matched_repos+=("$repo")
                done
            fi
        fi
    done < <(awk '/^  prefix_rules:/,/^  [a-z]/ {print}' "$config_file")

    # Read suffix rules from config
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]+([^:]+):.*\[([^\]]+)\] ]]; then
            local pattern="${BASH_REMATCH[1]}"
            local targets="${BASH_REMATCH[2]}"

            # Check if feature_name matches pattern (suffix, using stripped name)
            if [[ "$feature_name" == *"$pattern" ]]; then
                IFS=',' read -ra REPOS <<< "$targets"
                for repo in "${REPOS[@]}"; do
                    repo=$(echo "$repo" | xargs)
                    matched_repos+=("$repo")
                done
            fi
        fi
    done < <(awk '/^  suffix_rules:/,/^  [a-z]/ {print}' "$config_file")

    # Remove duplicates and output
    if [[ ${#matched_repos[@]} -gt 0 ]]; then
        printf '%s\n' "${matched_repos[@]}" | sort -u
        return 0
    else
        # Default: return all repos if no match
        echo "$all_repos"
        return 0
    fi
}

# Get repo path from workspace config
# Usage: get_repo_path <workspace_root> <repo_name>
get_repo_path() {
    local workspace_root="$1"
    local repo_name="$2"
    local config_file="$workspace_root/.specify/workspace.yml"

    if [[ ! -f "$config_file" ]]; then
        echo "ERROR: Workspace config not found: $config_file" >&2
        return 1
    fi

    # Extract path for specific repo
    local in_repo_section=0
    local current_repo=""

    while IFS= read -r line; do
        if [[ "$line" =~ ^repos: ]]; then
            in_repo_section=1
            continue
        fi

        if [[ $in_repo_section -eq 1 ]]; then
            # Check for end of repos section
            if [[ "$line" =~ ^[a-z] ]]; then
                break
            fi

            # Check for repo name
            if [[ "$line" =~ ^[[:space:]]+-[[:space:]]+name:[[:space:]]+(.+)$ ]]; then
                current_repo="${BASH_REMATCH[1]}"
            fi

            # Check for path when we're in the right repo
            if [[ "$current_repo" == "$repo_name" && "$line" =~ ^[[:space:]]+path:[[:space:]]+(.+)$ ]]; then
                local repo_path="${BASH_REMATCH[1]}"
                # Resolve relative paths
                if [[ "$repo_path" == ./* ]]; then
                    echo "$workspace_root/${repo_path#./}"
                else
                    echo "$repo_path"
                fi
                return 0
            fi
        fi
    done < "$config_file"

    echo "ERROR: Repo not found in workspace config: $repo_name" >&2
    return 1
}

# Get require_jira setting for a repo from workspace config
# Usage: get_repo_require_jira <workspace_root> <repo_name>
# Returns: "true" or "false"
get_repo_require_jira() {
    local workspace_root="$1"
    local repo_name="$2"
    local config_file="$workspace_root/.specify/workspace.yml"

    if [[ ! -f "$config_file" ]]; then
        # No workspace config, default to false
        echo "false"
        return 0
    fi

    # Extract require_jira for specific repo
    local in_repo_section=0
    local current_repo=""

    while IFS= read -r line; do
        if [[ "$line" =~ ^repos: ]]; then
            in_repo_section=1
            continue
        fi

        if [[ $in_repo_section -eq 1 ]]; then
            # Check for end of repos section
            if [[ "$line" =~ ^[a-z] ]]; then
                break
            fi

            # Check for repo name
            if [[ "$line" =~ ^[[:space:]]+-[[:space:]]+name:[[:space:]]+(.+)$ ]]; then
                current_repo="${BASH_REMATCH[1]}"
            fi

            # Check for require_jira when we're in the right repo
            if [[ "$current_repo" == "$repo_name" && "$line" =~ ^[[:space:]]+require_jira:[[:space:]]+(.+)$ ]]; then
                echo "${BASH_REMATCH[1]}"
                return 0
            fi
        fi
    done < "$config_file"

    # Default to false if not found
    echo "false"
    return 0
}

# Execute git command in specific repo
# Usage: git_exec <repo_path> <git_command> [args...]
git_exec() {
    local repo_path="$1"
    shift
    git -C "$repo_path" "$@"
}

# Extract GitHub host from git remote URL
# Usage: get_github_host <repo_path>
# Returns: github.com, github.marqeta.com, etc., or "unknown" if not GitHub
get_github_host() {
    local repo_path="$1"
    local remote_url=$(git -C "$repo_path" config remote.origin.url 2>/dev/null || echo "")

    if [[ -z "$remote_url" ]]; then
        echo "unknown"
        return 0
    fi

    # Extract host from various git URL formats:
    # - https://github.marqeta.com/org/repo.git
    # - git@github.marqeta.com:org/repo.git
    # - ssh://git@github.marqeta.com/org/repo.git
    if [[ "$remote_url" =~ github\.([a-zA-Z0-9.-]+)\.(com|net|org|io) ]]; then
        # Match github.marqeta.com, github.enterprise.com, etc.
        echo "github.${BASH_REMATCH[1]}.${BASH_REMATCH[2]}"
    elif [[ "$remote_url" =~ github\.(com|net|org|io) ]]; then
        # Match standard github.com
        echo "github.${BASH_REMATCH[1]}"
    else
        echo "unknown"
    fi
}

# Determine if Jira keys are required based on GitHub host
# Usage: requires_jira_key <github_host>
# Returns: "true" or "false"
requires_jira_key() {
    local github_host="$1"

    # Jira keys required for:
    # - github.marqeta.com (enterprise GitHub)
    # - Any non-standard GitHub host (not github.com)
    if [[ "$github_host" == "github.marqeta.com" ]] || \
       [[ "$github_host" != "github.com" && "$github_host" != "unknown" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Build workspace configuration from discovered repos
# Usage: build_workspace_config <workspace_root>
build_workspace_config() {
    local workspace_root="$1"
    local config_file="$workspace_root/.specify/workspace.yml"

    # Create .specify directory if it doesn't exist
    mkdir -p "$workspace_root/.specify"

    # Find all repos
    local repos=($(find_repos "$workspace_root" 2))

    if [[ ${#repos[@]} -eq 0 ]]; then
        echo "ERROR: No git repositories found in $workspace_root" >&2
        return 1
    fi

    # Generate workspace.yml
    cat > "$config_file" <<EOF
workspace:
  name: $(basename "$workspace_root")
  root: $workspace_root
  version: 1.0.0

repos:
EOF

    # Add each repo
    for repo_path in "${repos[@]}"; do
        local repo_name=$(get_repo_name "$repo_path")
        local relative_path="./${repo_path#$workspace_root/}"

        # Infer aliases from repo name
        local base_name="${repo_name%-*}"  # Remove suffix like -backend, -frontend
        local suffix="${repo_name##*-}"    # Get suffix

        # Detect GitHub host and Jira requirement
        local github_host=$(get_github_host "$repo_path")
        local require_jira=$(requires_jira_key "$github_host")

        cat >> "$config_file" <<EOF
  - name: $repo_name
    path: $relative_path
    aliases: [$base_name, $suffix]
    github_host: $github_host
    require_jira: $require_jira
EOF
    done

    # Add default conventions
    cat >> "$config_file" <<'EOF'

conventions:
  prefix_rules:
    backend-: [attun-backend]
    frontend-: [attun-frontend]
    fullstack-: [attun-backend, attun-frontend]

  suffix_rules:
    -api: [attun-backend]
    -ui: [attun-frontend]

  defaults:
    ambiguous_prompt: true
    default_repo: null
EOF

    echo "$config_file"
}

# Get specs directory (workspace or repo)
get_specs_dir() {
    local workspace_root=$(get_workspace_root)

    if [[ -n "$workspace_root" ]]; then
        # Workspace mode: specs in workspace root
        echo "$workspace_root/specs"
    else
        # Single-repo mode: specs in repo root
        local repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
        if [[ -n "$repo_root" ]]; then
            echo "$repo_root/specs"
        else
            echo "ERROR: Not in a git repository and no workspace found" >&2
            return 1
        fi
    fi
}

# List all repos in workspace
# Usage: list_workspace_repos <workspace_root>
list_workspace_repos() {
    local workspace_root="$1"
    local config_file="$workspace_root/.specify/workspace.yml"

    if [[ ! -f "$config_file" ]]; then
        echo "ERROR: Workspace config not found: $config_file" >&2
        return 1
    fi

    # Extract repo names
    awk '/^repos:/,/^[a-z]/ {if (/^  - name:/) print $3}' "$config_file"
}
