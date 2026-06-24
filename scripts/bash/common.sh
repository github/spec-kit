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

# Resolve an explicit SPECIFY_INIT_DIR project override (the directory that
# *contains* .specify/), for non-interactive / CI use — e.g. running a Spec Kit
# command against a member project from a monorepo root without cd.
#
# Precondition: SPECIFY_INIT_DIR is non-empty. Echoes the validated absolute
# project root, or prints an error and returns 1. Strict by design: the path
# must exist and contain .specify/, with no silent fallback to cwd or the
# script-location default (which would silently write to the wrong project).
#
# This is the single resolver: bundled extensions inherit it by sourcing core
# (e.g. the git extension's create-new-feature-branch) rather than duplicating it.
resolve_specify_init_dir() {
    local init_root
    # Normalize: relative paths resolve against $(pwd); a trailing slash collapses.
    # CDPATH="" so a relative value cannot be resolved against the caller's CDPATH
    # (which would also echo to stdout and corrupt the captured path).
    if ! init_root="$(CDPATH="" cd -- "$SPECIFY_INIT_DIR" 2>/dev/null && pwd)"; then
        echo "ERROR: SPECIFY_INIT_DIR does not point to an existing directory: $SPECIFY_INIT_DIR" >&2
        return 1
    fi
    if [[ ! -d "$init_root/.specify" ]]; then
        echo "ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): $init_root" >&2
        return 1
    fi
    printf '%s\n' "$init_root"
}

# Get repository root, prioritizing .specify directory
# This prevents using a parent repository when spec-kit is initialized in a subdirectory
get_repo_root() {
    # Explicit project override wins (see resolve_specify_init_dir).
    if [[ -n "${SPECIFY_INIT_DIR:-}" ]]; then
        resolve_specify_init_dir
        return
    fi

    # First, look for .specify directory (spec-kit's own marker)
    local specify_root
    if specify_root=$(find_specify_root); then
        echo "$specify_root"
        return
    fi

    # Final fallback to script location
    local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    (cd "$script_dir/../../.." && pwd)
}

# Get current feature name from explicit state only.
# Returns the feature identifier or empty string if none is set.
# Feature state is set by SPECIFY_FEATURE (from create-new-feature or
# the git extension) or implicitly via .specify/feature.json.
get_current_branch() {
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # No explicit feature set — caller must handle this via feature.json
    # in get_feature_paths(). Return empty to signal "unknown".
    echo ""
}

# Safely read .specify/feature.json's "feature_directory" value.
# Prints the raw value (possibly relative) to stdout, or empty string if the file
# is missing, unparseable, or does not contain the key. Always returns 0 so callers
# under `set -e` cannot be aborted by parser failure.
# Parser order mirrors the historical get_feature_paths behavior: jq -> python3 -> grep/sed.
read_feature_json_feature_directory() {
    local repo_root="$1"
    local fj="$repo_root/.specify/feature.json"
    [[ -f "$fj" ]] || { printf '%s' ''; return 0; }

    local _fd=''
    if command -v jq >/dev/null 2>&1; then
        if ! _fd=$(jq -r '.feature_directory // empty' "$fj" 2>/dev/null); then
            _fd=''
        fi
    elif command -v python3 >/dev/null 2>&1; then
        # Use Python so pretty-printed/multi-line JSON still parses correctly.
        if ! _fd=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get('feature_directory'); print(v if v else '')" "$fj" 2>/dev/null); then
            _fd=''
        fi
    else
        # Last-resort single-line grep/sed fallback. The `|| true` guards against
        # grep returning 1 (no match) aborting under `set -e` / `pipefail`.
        _fd=$( { grep -E '"feature_directory"[[:space:]]*:' "$fj" 2>/dev/null || true; } \
            | head -n 1 \
            | sed -E 's/^[^:]*:[[:space:]]*"([^"]*)".*$/\1/' )
    fi

    printf '%s' "$_fd"
    return 0
}

# Persist a feature_directory value to .specify/feature.json.
# Writes only when the file is missing or the value differs from what's stored.
# Accepts the raw (possibly relative) path — callers should pass the original
# user-supplied value, not the normalized absolute path.
_persist_feature_json() {
    local repo_root="$1"
    local feature_dir_value="$2"
    local fj="$repo_root/.specify/feature.json"

    # Strip repo_root prefix if the value is absolute and under repo_root
    if [[ "$feature_dir_value" == "$repo_root/"* ]]; then
        feature_dir_value="${feature_dir_value#"$repo_root/"}"
    fi

    # Read current value (if any) and skip write when unchanged
    local current_val
    current_val=$(read_feature_json_feature_directory "$repo_root")
    if [[ "$current_val" == "$feature_dir_value" ]]; then
        return 0
    fi

    # Ensure .specify/ directory exists
    mkdir -p "$repo_root/.specify"

    # Write feature.json — prefer jq for safe JSON, fall back to printf
    if command -v jq >/dev/null 2>&1; then
        jq -cn --arg fd "$feature_dir_value" '{feature_directory:$fd}' > "$fj"
    else
        printf '{"feature_directory":"%s"}\n' "$(json_escape "$feature_dir_value")" > "$fj"
    fi
}

get_feature_paths() {
    # Split decl/assignment so a SPECIFY_INIT_DIR validation failure in
    # get_repo_root propagates as a hard error instead of being masked by `local`.
    local repo_root
    repo_root=$(get_repo_root) || return 1
    local current_branch
    current_branch=$(get_current_branch)

    # Resolve feature directory.  Priority:
    #   1. SPECIFY_FEATURE_DIRECTORY env var (explicit override)
    #   2. .specify/feature.json "feature_directory" key (persisted by specify command)
    #   3. Error — no feature context available
    local feature_dir
    if [[ -n "${SPECIFY_FEATURE_DIRECTORY:-}" ]]; then
        feature_dir="$SPECIFY_FEATURE_DIRECTORY"
        # Normalize relative paths to absolute under repo root
        [[ "$feature_dir" != /* ]] && feature_dir="$repo_root/$feature_dir"
        # Persist to feature.json so future sessions without the env var still work
        _persist_feature_json "$repo_root" "$SPECIFY_FEATURE_DIRECTORY"
    elif [[ -f "$repo_root/.specify/feature.json" ]]; then
        local _fd
        _fd=$(read_feature_json_feature_directory "$repo_root")
        if [[ -n "$_fd" ]]; then
            feature_dir="$_fd"
            # Normalize relative paths to absolute under repo root
            [[ "$feature_dir" != /* ]] && feature_dir="$repo_root/$feature_dir"
        else
            echo "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or ensure .specify/feature.json contains feature_directory." >&2
            return 1
        fi
    else
        echo "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or run the specify command to create .specify/feature.json." >&2
        return 1
    fi

    # Use printf '%q' to safely quote values, preventing shell injection
    # via crafted branch names or paths containing special characters
    printf 'REPO_ROOT=%q\n' "$repo_root"
    printf 'CURRENT_BRANCH=%q\n' "$current_branch"
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

get_invoke_separator() {
    local repo_root="${1:-$(get_repo_root)}"
    if [[ "${_SPECIFY_INVOKE_SEPARATOR_CACHE_REPO_ROOT:-}" == "$repo_root" && -n "${_SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE:-}" ]]; then
        printf '%s\n' "$_SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE"
        return 0
    fi

    local integration_json="$repo_root/.specify/integration.json"
    local separator="."
    local parsed_with_jq=0

    if [[ -f "$integration_json" ]]; then
        if command -v jq >/dev/null 2>&1; then
            local jq_separator
            if jq_separator=$(jq -r '(.default_integration // .integration // "") as $k | if $k == "" then "." else (.integration_settings[$k].invoke_separator // ".") end' "$integration_json" 2>/dev/null); then
                parsed_with_jq=1
                case "$jq_separator" in
                    "."|"-") separator="$jq_separator" ;;
                esac
            fi
        fi

        if [[ "$parsed_with_jq" -eq 0 ]] && command -v python3 >/dev/null 2>&1; then
            if separator=$(python3 - "$integration_json" <<'PY' 2>/dev/null
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        state = json.load(fh)
    key = state.get("default_integration") or state.get("integration") or ""
    settings = state.get("integration_settings")
    separator = "."
    if isinstance(key, str) and isinstance(settings, dict):
        entry = settings.get(key)
        if isinstance(entry, dict) and entry.get("invoke_separator") in {".", "-"}:
            separator = entry["invoke_separator"]
    print(separator)
except Exception:
    print(".")
PY
); then
                case "$separator" in
                    "."|"-") ;;
                    *) separator="." ;;
                esac
            else
                separator="."
            fi
        fi
    fi

    _SPECIFY_INVOKE_SEPARATOR_CACHE_REPO_ROOT="$repo_root"
    _SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE="$separator"
    printf '%s\n' "$separator"
}

format_speckit_command() {
    local command_name="$1"
    local repo_root="${2:-$(get_repo_root)}"
    local separator
    if [[ "${_SPECIFY_INVOKE_SEPARATOR_CACHE_REPO_ROOT:-}" == "$repo_root" && -n "${_SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE:-}" ]]; then
        separator="$_SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE"
    else
        separator=$(get_invoke_separator "$repo_root")
        _SPECIFY_INVOKE_SEPARATOR_CACHE_REPO_ROOT="$repo_root"
        _SPECIFY_INVOKE_SEPARATOR_CACHE_VALUE="$separator"
    fi

    command_name="${command_name#/}"
    command_name="${command_name#speckit.}"
    command_name="${command_name#speckit-}"
    command_name="${command_name//./$separator}"

    printf '/speckit%s%s\n' "$separator" "$command_name"
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
    for pid, meta in sorted(presets.items(), key=lambda x: x[1].get('priority', 10) if isinstance(x[1], dict) else 10):
        if isinstance(meta, dict) and meta.get('enabled', True) is not False:
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
    for pid, meta in sorted(presets.items(), key=lambda x: x[1].get('priority', 10) if isinstance(x[1], dict) else 10):
        if isinstance(meta, dict) and meta.get('enabled', True) is not False:
            print(pid)
except Exception:
    sys.exit(1)
" 2>/dev/null); then
                if [ -n "$sorted_presets" ]; then
                    local yaml_warned=false
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
                            if [ "$yaml_warned" = false ] && grep -q 'yaml_missing' "$py_stderr" 2>/dev/null; then
                                echo "Warning: PyYAML not available; composition strategies may be ignored" >&2
                                yaml_warned=true
                            fi
                            rm -f "$py_stderr"
                        fi
                        # Try manifest file path first, then convention path
                        local candidate=""
                        if [ -n "$manifest_file" ]; then
                            # Reject absolute paths and parent traversal
                            case "$manifest_file" in
                                /*|*../*|../*) manifest_file="" ;;
                            esac
                        fi
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

    # Find the effective base: scan from highest priority (index 0) downward
    # to find the nearest replace layer. Only compose layers above that base.
    local base_idx=-1
    local i
    for (( i=0; i<count; i++ )); do
        if [ "${layer_strategies[$i]}" = "replace" ]; then
            base_idx=$i
            break
        fi
    done

    if [ $base_idx -lt 0 ]; then
        return 1  # no base layer found
    fi

    # Read the base content; compose layers above the base (higher priority)
    local content
    content=$(cat "${layer_paths[$base_idx]}"; printf x)
    content="${content%x}"

    for (( i=base_idx-1; i>=0; i-- )); do
        local path="${layer_paths[$i]}"
        local strat="${layer_strategies[$i]}"
        local layer_content
        # Preserve trailing newlines
        layer_content=$(cat "$path"; printf x)
        layer_content="${layer_content%x}"

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
    done

    printf '%s' "$content"
    return 0
}
