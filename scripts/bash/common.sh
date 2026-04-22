#!/usr/bin/env bash
# Common functions and variables for all scripts

# Find repository root by searching upward for .specify directory
# This is the primary marker for spec-kit projects
find_specify_root() {
    local dir="${1:-$(pwd)}"
    # Normalize to absolute path to prevent infinite loop with relative paths
    # Use -- to handle paths starting with - (e.g., -P, -L)
    dir="$(cd -- "$dir" 2>/dev/null && pwd)" || return 1
    local prev_dir=""
    while true; do
        if [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        # Stop if we've reached filesystem root or dirname stops changing
        if [ "$dir" = "/" ] || [ "$dir" = "$prev_dir" ]; then
            break
        fi
        prev_dir="$dir"
        dir="$(dirname "$dir")"
    done
    return 1
}

# Get repository root, prioritizing .specify directory over git
# This prevents using a parent git repo when spec-kit is initialized in a subdirectory
get_repo_root() {
    # First, look for .specify directory (spec-kit's own marker)
    local specify_root
    if specify_root=$(find_specify_root); then
        echo "$specify_root"
        return
    fi

    # Fallback to git if no .specify found
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
        return
    fi

    # Final fallback to script location for non-git repos
    local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    (cd "$script_dir/../../.." && pwd)
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available at the spec-kit root (not parent)
    local repo_root=$(get_repo_root)
    if has_git; then
        git -C "$repo_root" rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0
        local latest_timestamp=""

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{8}-[0-9]{6})- ]]; then
                    # Timestamp-based branch: compare lexicographically
                    local ts="${BASH_REMATCH[1]}"
                    if [[ "$ts" > "$latest_timestamp" ]]; then
                        latest_timestamp="$ts"
                        latest_feature=$dirname
                    fi
                elif [[ "$dirname" =~ ^([0-9]{3,})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        # Only update if no timestamp branch found yet
                        if [[ -z "$latest_timestamp" ]]; then
                            latest_feature=$dirname
                        fi
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

# Check if we have git available at the spec-kit root level
# Returns true only if git is installed and the repo root is inside a git work tree
# Handles both regular repos (.git directory) and worktrees/submodules (.git file)
has_git() {
    # First check if git command is available (before calling get_repo_root which may use git)
    command -v git >/dev/null 2>&1 || return 1
    local repo_root=$(get_repo_root)
    # Check if .git exists (directory or file for worktrees/submodules)
    [ -e "$repo_root/.git" ] || return 1
    # Verify it's actually a valid git work tree
    git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Strip a single optional path segment (e.g. gitflow "feat/004-name" -> "004-name").
# Only when the full name is exactly two slash-free segments; otherwise returns the raw name.
spec_kit_effective_branch_name() {
    local raw="$1"
    if [[ "$raw" =~ ^([^/]+)/([^/]+)$ ]]; then
        printf '%s\n' "${BASH_REMATCH[2]}"
    else
        printf '%s\n' "$raw"
    fi
}

check_feature_branch() {
    local raw="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    local branch
    branch=$(spec_kit_effective_branch_name "$raw")

    # Accept sequential prefix (3+ digits) but exclude malformed timestamps
    # Malformed: 7-or-8 digit date + 6-digit time with no trailing slug (e.g. "2026031-143022" or "20260319-143022")
    local is_sequential=false
    if [[ "$branch" =~ ^[0-9]{3,}- ]] && [[ ! "$branch" =~ ^[0-9]{7}-[0-9]{6}- ]] && [[ ! "$branch" =~ ^[0-9]{7,8}-[0-9]{6}$ ]]; then
        is_sequential=true
    fi
    if [[ "$is_sequential" != "true" ]] && [[ ! "$branch" =~ ^[0-9]{8}-[0-9]{6}- ]]; then
        echo "ERROR: Not on a feature branch. Current branch: $raw" >&2
        echo "Feature branches should be named like: 001-feature-name, 1234-feature-name, or 20260319-143022-feature-name" >&2
        return 1
    fi

    return 0
}

# Find feature directory by numeric prefix instead of exact branch match
# This allows multiple branches to work on the same spec (e.g., 004-fix-bug, 004-add-feature)
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name
    branch_name=$(spec_kit_effective_branch_name "$2")
    local specs_dir="$repo_root/specs"

    # Extract prefix from branch (e.g., "004" from "004-whatever" or "20260319-143022" from timestamp branches)
    local prefix=""
    if [[ "$branch_name" =~ ^([0-9]{8}-[0-9]{6})- ]]; then
        prefix="${BASH_REMATCH[1]}"
    elif [[ "$branch_name" =~ ^([0-9]{3,})- ]]; then
        prefix="${BASH_REMATCH[1]}"
    else
        # If branch doesn't have a recognized prefix, fall back to exact match
        echo "$specs_dir/$branch_name"
        return
    fi

    # Search for directories in specs/ that start with this prefix
    local matches=()
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            if [[ -d "$dir" ]]; then
                matches+=("$(basename "$dir")")
            fi
        done
    fi

    # Handle results
    if [[ ${#matches[@]} -eq 0 ]]; then
        # No match found - return the branch name path (will fail later with clear error)
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        # Exactly one match - perfect!
        echo "$specs_dir/${matches[0]}"
    else
        # Multiple matches - this shouldn't happen with proper naming convention
        echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
        echo "Please ensure only one spec directory exists per prefix." >&2
        return 1
    fi
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Resolve feature directory.  Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY env var (explicit override)
    #   2. .specify/feature.json "feature_directory" key (persisted by /speckit.specify)
    #   3. Branch-name-based prefix lookup (legacy fallback)
    local feature_dir
    if [[ -n "${SPECIFY_FEATURE_DIRECTORY:-}" ]]; then
        feature_dir="$SPECIFY_FEATURE_DIRECTORY"
        # Normalize relative paths to absolute under repo root
        [[ "$feature_dir" != /* ]] && feature_dir="$repo_root/$feature_dir"
    elif [[ -f "$repo_root/.specify/feature.json" ]]; then
        local _fd
        if command -v jq >/dev/null 2>&1; then
            _fd=$(jq -r '.feature_directory // empty' "$repo_root/.specify/feature.json" 2>/dev/null)
        elif command -v python3 >/dev/null 2>&1; then
            # Fallback: use Python to parse JSON so pretty-printed/multi-line files work
            _fd=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('feature_directory',''))" "$repo_root/.specify/feature.json" 2>/dev/null)
        else
            # Last resort: single-line grep fallback (won't work on multi-line JSON)
            _fd=$(grep -o '"feature_directory"[[:space:]]*:[[:space:]]*"[^"]*"' "$repo_root/.specify/feature.json" 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')
        fi
        if [[ -n "$_fd" ]]; then
            feature_dir="$_fd"
            # Normalize relative paths to absolute under repo root
            [[ "$feature_dir" != /* ]] && feature_dir="$repo_root/$feature_dir"
        elif ! feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch"); then
            echo "ERROR: Failed to resolve feature directory" >&2
            return 1
        fi
    elif ! feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch"); then
        echo "ERROR: Failed to resolve feature directory" >&2
        return 1
    fi

    # Use printf '%q' to safely quote values, preventing shell injection
    # via crafted branch names or paths containing special characters
    printf 'REPO_ROOT=%q\n' "$repo_root"
    printf 'CURRENT_BRANCH=%q\n' "$current_branch"
    printf 'HAS_GIT=%q\n' "$has_git_repo"
    printf 'FEATURE_DIR=%q\n' "$feature_dir"
    printf 'FEATURE_SPEC=%q\n' "$feature_dir/spec.md"
    printf 'IMPL_PLAN=%q\n' "$feature_dir/plan.md"
    printf 'TASKS=%q\n' "$feature_dir/tasks.md"
    printf 'RESEARCH=%q\n' "$feature_dir/research.md"
    printf 'DATA_MODEL=%q\n' "$feature_dir/data-model.md"
    printf 'QUICKSTART=%q\n' "$feature_dir/quickstart.md"
    printf 'CONTRACTS_DIR=%q\n' "$feature_dir/contracts"
}

# Check if jq is available for safe JSON construction
has_jq() {
    command -v jq >/dev/null 2>&1
}

# Escape a string for safe embedding in a JSON value (fallback when jq is unavailable).
# Handles backslash, double-quote, and JSON-required control character escapes (RFC 8259).
json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\t'/\\t}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\b'/\\b}"
    s="${s//$'\f'/\\f}"
    # Escape any remaining U+0001-U+001F control characters as \uXXXX.
    # (U+0000/NUL cannot appear in bash strings and is excluded.)
    # LC_ALL=C ensures ${#s} counts bytes and ${s:$i:1} yields single bytes,
    # so multi-byte UTF-8 sequences (first byte >= 0xC0) pass through intact.
    local LC_ALL=C
    local i char code
    for (( i=0; i<${#s}; i++ )); do
        char="${s:$i:1}"
        printf -v code '%d' "'$char" 2>/dev/null || code=256
        if (( code >= 1 && code <= 31 )); then
            printf '\\u%04x' "$code"
        else
            printf '%s' "$char"
        fi
    done
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

# Resolve a template name to a file path using the priority stack:
#   1. .specify/templates/overrides/
#   2. .specify/presets/<preset-id>/templates/ (sorted by priority from .registry)
#   3. .specify/extensions/<ext-id>/templates/
#   4. .specify/templates/ (core)
resolve_template() {
    local template_name="$1"
    local repo_root="$2"
    local base="$repo_root/.specify/templates"

    # Priority 1: Project overrides
    local override="$base/overrides/${template_name}.md"
    [ -f "$override" ] && echo "$override" && return 0

    # Priority 2: Installed presets (sorted by priority from .registry)
    local presets_dir="$repo_root/.specify/presets"
    if [ -d "$presets_dir" ]; then
        local registry_file="$presets_dir/.registry"
        if [ -f "$registry_file" ] && command -v python3 >/dev/null 2>&1; then
            # Read preset IDs sorted by priority (lower number = higher precedence).
            # The python3 call is wrapped in an if-condition so that set -e does not
            # abort the function when python3 exits non-zero (e.g. invalid JSON).
            local sorted_presets=""
            if sorted_presets=$(SPECKIT_REGISTRY="$registry_file" python3 -c "
import json, sys, os
try:
    with open(os.environ['SPECKIT_REGISTRY']) as f:
        data = json.load(f)
    presets = data.get('presets', {})
    for pid, meta in sorted(presets.items(), key=lambda x: x[1].get('priority', 10)):
        if meta.get('enabled', True) is not False:
            print(pid)
except Exception:
    sys.exit(1)
" 2>/dev/null); then
                if [ -n "$sorted_presets" ]; then
                    # python3 succeeded and returned preset IDs — search in priority order
                    while IFS= read -r preset_id; do
                        local candidate="$presets_dir/$preset_id/templates/${template_name}.md"
                        [ -f "$candidate" ] && echo "$candidate" && return 0
                    done <<< "$sorted_presets"
                fi
                # python3 succeeded but registry has no presets — nothing to search
            else
                # python3 failed (missing, or registry parse error) — fall back to unordered directory scan
                for preset in "$presets_dir"/*/; do
                    [ -d "$preset" ] || continue
                    local candidate="$preset/templates/${template_name}.md"
                    [ -f "$candidate" ] && echo "$candidate" && return 0
                done
            fi
        else
            # Fallback: alphabetical directory order (no python3 available)
            for preset in "$presets_dir"/*/; do
                [ -d "$preset" ] || continue
                local candidate="$preset/templates/${template_name}.md"
                [ -f "$candidate" ] && echo "$candidate" && return 0
            done
        fi
    fi

    # Priority 3: Extension-provided templates
    local ext_dir="$repo_root/.specify/extensions"
    if [ -d "$ext_dir" ]; then
        for ext in "$ext_dir"/*/; do
            [ -d "$ext" ] || continue
            # Skip hidden directories (e.g. .backup, .cache)
            case "$(basename "$ext")" in .*) continue;; esac
            local candidate="$ext/templates/${template_name}.md"
            [ -f "$candidate" ] && echo "$candidate" && return 0
        done
    fi

    # Priority 4: Core templates
    local core="$base/${template_name}.md"
    [ -f "$core" ] && echo "$core" && return 0

    # Template not found in any location.
    # Return 1 so callers can distinguish "not found" from "found".
    # Callers running under set -e should use: TEMPLATE=$(resolve_template ...) || true
    return 1
}

# Resolve a template name to composed content using composition strategies.
# Reads strategy metadata from preset manifests and composes content
# from multiple layers using prepend, append, or wrap strategies.
#
# Usage: CONTENT=$(resolve_template_content "template-name" "$REPO_ROOT")
# Returns composed content string on stdout; exit code 1 if not found.
resolve_template_content() {
    local template_name="$1"
    local repo_root="$2"
    local base="$repo_root/.specify/templates"

    # Collect all layers (highest priority first)
    local -a layer_paths=()
    local -a layer_strategies=()

    # Priority 1: Project overrides (always "replace")
    local override="$base/overrides/${template_name}.md"
    if [ -f "$override" ]; then
        layer_paths+=("$override")
        layer_strategies+=("replace")
    fi

    # Priority 2: Installed presets (sorted by priority from .registry)
    local presets_dir="$repo_root/.specify/presets"
    if [ -d "$presets_dir" ]; then
        local registry_file="$presets_dir/.registry"
        local sorted_presets=""
        if [ -f "$registry_file" ] && command -v python3 >/dev/null 2>&1; then
            if sorted_presets=$(SPECKIT_REGISTRY="$registry_file" python3 -c "
import json, sys, os
try:
    with open(os.environ['SPECKIT_REGISTRY']) as f:
        data = json.load(f)
    presets = data.get('presets', {})
    for pid, meta in sorted(presets.items(), key=lambda x: x[1].get('priority', 10)):
        if meta.get('enabled', True) is not False:
            print(pid)
except Exception:
    sys.exit(1)
" 2>/dev/null); then
                if [ -n "$sorted_presets" ]; then
                    while IFS= read -r preset_id; do
                        # Read strategy and file path from preset manifest
                        local strategy="replace"
                        local manifest_file=""
                        local manifest="$presets_dir/$preset_id/preset.yml"
                        if [ -f "$manifest" ] && command -v python3 >/dev/null 2>&1; then
                            # Requires PyYAML; falls back to replace/convention if unavailable
                            local result
                            local py_stderr
                            py_stderr=$(mktemp)
                            result=$(SPECKIT_MANIFEST="$manifest" SPECKIT_TMPL="$template_name" python3 -c "
import sys, os
try:
    import yaml
except ImportError:
    print('yaml_missing', file=sys.stderr)
    print('replace\t')
    sys.exit(0)
try:
    with open(os.environ['SPECKIT_MANIFEST']) as f:
        data = yaml.safe_load(f)
    for t in data.get('provides', {}).get('templates', []):
        if t.get('name') == os.environ['SPECKIT_TMPL'] and t.get('type', 'template') == 'template':
            print(t.get('strategy', 'replace') + '\t' + t.get('file', ''))
            sys.exit(0)
    print('replace\t')
except Exception:
    print('replace\t')
" 2>"$py_stderr")
                            local parse_status=$?
                            if [ $parse_status -eq 0 ] && [ -n "$result" ]; then
                                IFS=$'\t' read -r strategy manifest_file <<< "$result"
                                strategy=$(printf '%s' "$strategy" | tr '[:upper:]' '[:lower:]')
                            fi
                            # Warn only when PyYAML is explicitly missing
                            if grep -q 'yaml_missing' "$py_stderr" 2>/dev/null; then
                                echo "Warning: PyYAML not available; composition strategies in $manifest may be ignored" >&2
                            fi
                            rm -f "$py_stderr"
                        fi
                        # Try manifest file path first, then convention path
                        local candidate=""
                        if [ -n "$manifest_file" ]; then
                            local mf="$presets_dir/$preset_id/$manifest_file"
                            [ -f "$mf" ] && candidate="$mf"
                        fi
                        if [ -z "$candidate" ]; then
                            local cf="$presets_dir/$preset_id/templates/${template_name}.md"
                            [ -f "$cf" ] && candidate="$cf"
                        fi
                        if [ -n "$candidate" ]; then
                            layer_paths+=("$candidate")
                            layer_strategies+=("$strategy")
                        fi
                    done <<< "$sorted_presets"
                fi
            else
                # python3 failed — fall back to unordered directory scan (replace only)
                for preset in "$presets_dir"/*/; do
                    [ -d "$preset" ] || continue
                    local candidate="$preset/templates/${template_name}.md"
                    if [ -f "$candidate" ]; then
                        layer_paths+=("$candidate")
                        layer_strategies+=("replace")
                    fi
                done
            fi
        else
            # No python3 or registry — fall back to unordered directory scan (replace only)
            for preset in "$presets_dir"/*/; do
                [ -d "$preset" ] || continue
                local candidate="$preset/templates/${template_name}.md"
                if [ -f "$candidate" ]; then
                    layer_paths+=("$candidate")
                    layer_strategies+=("replace")
                fi
            done
        fi
    fi

    # Priority 3: Extension-provided templates (always "replace")
    local ext_dir="$repo_root/.specify/extensions"
    if [ -d "$ext_dir" ]; then
        for ext in "$ext_dir"/*/; do
            [ -d "$ext" ] || continue
            case "$(basename "$ext")" in .*) continue;; esac
            local candidate="$ext/templates/${template_name}.md"
            if [ -f "$candidate" ]; then
                layer_paths+=("$candidate")
                layer_strategies+=("replace")
            fi
        done
    fi

    # Priority 4: Core templates (always "replace")
    local core="$base/${template_name}.md"
    if [ -f "$core" ]; then
        layer_paths+=("$core")
        layer_strategies+=("replace")
    fi

    local count=${#layer_paths[@]}
    [ "$count" -eq 0 ] && return 1

    # Check if any layer uses a non-replace strategy
    local has_composition=false
    for s in "${layer_strategies[@]}"; do
        [ "$s" != "replace" ] && has_composition=true && break
    done

    # If the top (highest-priority) layer is replace, it wins entirely —
    # lower layers are irrelevant regardless of their strategies.
    if [ "${layer_strategies[0]}" = "replace" ]; then
        cat "${layer_paths[0]}"
        return 0
    fi

    if [ "$has_composition" = false ]; then
        cat "${layer_paths[0]}"
        return 0
    fi

    # Compose bottom-up: start from lowest priority
    local content=""
    local has_base=false
    local started=false
    local i
    for (( i=count-1; i>=0; i-- )); do
        local path="${layer_paths[$i]}"
        local strat="${layer_strategies[$i]}"
        local layer_content
        # Preserve trailing newlines: append sentinel, then strip it
        layer_content=$(cat "$path"; printf x)
        layer_content="${layer_content%x}"

        if [ "$started" = false ]; then
            if [ "$strat" = "replace" ]; then
                content="$layer_content"
                has_base=true
            fi
            # Keep consuming replace layers from the bottom until we hit a non-replace
            if [ "$strat" != "replace" ]; then
                # No base content to compose onto
                [ "$has_base" = false ] && return 1
                started=true
                case "$strat" in
                    prepend) content="$(printf '%s\n\n%s' "$layer_content" "$content")" ;;
                    append)  content="$(printf '%s\n\n%s' "$content" "$layer_content")" ;;
                    wrap)
                        # Validate placeholder exists
                        case "$layer_content" in
                            *'{CORE_TEMPLATE}'*) ;;
                            *) echo "Error: wrap strategy missing {CORE_TEMPLATE} placeholder" >&2; return 1 ;;
                        esac
                        # Replace all occurrences to match Python/PowerShell behavior
                        while [[ "$layer_content" == *'{CORE_TEMPLATE}'* ]]; do
                            local before="${layer_content%%\{CORE_TEMPLATE\}*}"
                            local after="${layer_content#*\{CORE_TEMPLATE\}}"
                            layer_content="${before}${content}${after}"
                        done
                        content="$layer_content"
                        ;;
                    *) echo "Error: unknown strategy '$strat'" >&2; return 1 ;;
                esac
            fi
        else
            case "$strat" in
                replace) content="$layer_content" ;;
                prepend) content="$(printf '%s\n\n%s' "$layer_content" "$content")" ;;
                append)  content="$(printf '%s\n\n%s' "$content" "$layer_content")" ;;
                wrap)
                    case "$layer_content" in
                        *'{CORE_TEMPLATE}'*) ;;
                        *) echo "Error: wrap strategy missing {CORE_TEMPLATE} placeholder" >&2; return 1 ;;
                    esac
                    while [[ "$layer_content" == *'{CORE_TEMPLATE}'* ]]; do
                        local before="${layer_content%%\{CORE_TEMPLATE\}*}"
                        local after="${layer_content#*\{CORE_TEMPLATE\}}"
                        layer_content="${before}${content}${after}"
                    done
                    content="$layer_content"
                    ;;
                *) echo "Error: unknown strategy '$strat'" >&2; return 1 ;;
            esac
        fi
    done

    printf '%s' "$content"
    return 0
}

