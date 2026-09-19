#!/usr/bin/env bash

# Resolve the active feature and its tasks.md for the github extension.
#
# Deliberately self-contained: the github extension owns this script so that
# `speckit.github.taskstoissues` keeps working when the core `taskstoissues`
# command (and its `check-prerequisites` helper invocation) is deprecated and
# removed. It is a trimmed twin of core `check-prerequisites.sh` — it resolves
# the project root and the active feature directory, requires tasks.md, and
# reports the optional design docs that sit next to it. It performs none of
# core's plan.md/spec.md gating and never writes .specify/feature.json.
#
# Usage: ./resolve-tasks.sh [--json]
#
# OPTIONS:
#   --json      Output in JSON format
#   --help, -h  Show help message
#
# OUTPUTS:
#   JSON mode: {"FEATURE_DIR":"...","TASKS":"...","AVAILABLE_DOCS":["..."]}
#   Text mode: FEATURE_DIR:... \n TASKS:... \n AVAILABLE_DOCS: \n ✓/✗ file.md

set -e

JSON_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            cat << 'HELP'
Usage: resolve-tasks.sh [OPTIONS]

Resolve the active feature and its tasks.md for the github extension.

OPTIONS:
  --json      Output in JSON format
  --help, -h  Show this help message

EXAMPLES:
  ./resolve-tasks.sh --json
HELP
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$1'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
    shift
done

# Escape a string for safe embedding in a JSON value (RFC 8259).
# Kept byte-for-byte in step with core's json_escape (scripts/bash/common.sh)
# rather than sourcing it, so this script stays self-contained.
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

# Find the project root by searching upward for the .specify marker directory.
find_specify_root() {
    local dir="${1:-$(pwd)}"
    dir="$(CDPATH="" cd -- "$dir" 2>/dev/null && pwd)" || return 1
    local prev_dir=""
    while true; do
        if [ -d "$dir/.specify" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
        if [ "$dir" = "/" ] || [ "$dir" = "$prev_dir" ]; then
            break
        fi
        prev_dir="$dir"
        dir="$(dirname "$dir")"
    done
    return 1
}

# Resolve the project root, honouring an explicit SPECIFY_INIT_DIR override.
# Mirrors core get_repo_root: strict on an invalid override, no silent fallback.
get_repo_root() {
    if [[ -n "${SPECIFY_INIT_DIR:-}" ]]; then
        local init_root
        if ! init_root="$(CDPATH="" cd -- "$SPECIFY_INIT_DIR" 2>/dev/null && pwd)"; then
            echo "ERROR: SPECIFY_INIT_DIR does not point to an existing directory: $SPECIFY_INIT_DIR" >&2
            return 1
        fi
        if [[ ! -d "$init_root/.specify" ]]; then
            echo "ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): $init_root" >&2
            return 1
        fi
        printf '%s\n' "$init_root"
        return 0
    fi

    local specify_root
    if specify_root=$(find_specify_root); then
        printf '%s\n' "$specify_root"
        return 0
    fi

    # Installed scripts live at .specify/extensions/github/scripts/bash/.
    local script_dir
    script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if specify_root=$(find_specify_root "$script_dir"); then
        printf '%s\n' "$specify_root"
        return 0
    fi

    echo "ERROR: Not inside a Spec Kit project (no .specify/ directory found)." >&2
    return 1
}

# Read .specify/feature.json's "feature_directory" value, or empty string.
# Parser order mirrors core common.sh (jq -> python3 -> grep/sed) and selects
# by parse success rather than availability, so a Windows python3 App Execution
# Alias stub cannot swallow the fallback (issue #3304).
read_feature_json_feature_directory() {
    local repo_root="$1"
    local fj="$repo_root/.specify/feature.json"
    [[ -f "$fj" ]] || { printf '%s' ''; return 0; }

    local _fd=''
    if command -v jq >/dev/null 2>&1; then
        if ! _fd=$(jq -r '.feature_directory // empty' "$fj" 2>/dev/null); then
            _fd=''
        fi
    fi
    if [[ -z "$_fd" ]] && command -v python3 >/dev/null 2>&1; then
        if ! _fd=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); v=d.get('feature_directory'); print(v if v else '')" "$fj" 2>/dev/null); then
            _fd=''
        fi
    fi
    if [[ -z "$_fd" ]]; then
        _fd=$( { grep -E '"feature_directory"[[:space:]]*:' "$fj" 2>/dev/null || true; } \
            | head -n 1 \
            | sed -E 's/^[^:]*:[[:space:]]*"([^"]*)".*$/\1/' )
    fi

    printf '%s' "$_fd"
    return 0
}

REPO_ROOT=$(get_repo_root) || exit 1

# Resolve the feature directory. Priority:
#   1. SPECIFY_FEATURE_DIRECTORY (explicit override)
#   2. .specify/feature.json "feature_directory"
# Read-only by design: unlike core, this never persists feature.json (#3025).
if [[ -n "${SPECIFY_FEATURE_DIRECTORY:-}" ]]; then
    FEATURE_DIR="$SPECIFY_FEATURE_DIRECTORY"
else
    FEATURE_DIR=$(read_feature_json_feature_directory "$REPO_ROOT")
    if [[ -z "$FEATURE_DIR" ]]; then
        echo "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or run the specify command to create .specify/feature.json." >&2
        exit 1
    fi
fi
[[ "$FEATURE_DIR" != /* ]] && FEATURE_DIR="$REPO_ROOT/$FEATURE_DIR"

if [[ ! -d "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory not found: $FEATURE_DIR" >&2
    echo "Run the Spec Kit specify command (e.g. /speckit.specify) first to create the feature structure." >&2
    exit 1
fi

TASKS="$FEATURE_DIR/tasks.md"
if [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found in $FEATURE_DIR" >&2
    echo "Run the Spec Kit tasks command (e.g. /speckit.tasks) first to create the task list." >&2
    exit 1
fi

RESEARCH="$FEATURE_DIR/research.md"
DATA_MODEL="$FEATURE_DIR/data-model.md"
QUICKSTART="$FEATURE_DIR/quickstart.md"
CONTRACTS_DIR="$FEATURE_DIR/contracts"

docs=()
[[ -f "$RESEARCH" ]] && docs+=("research.md")
[[ -f "$DATA_MODEL" ]] && docs+=("data-model.md")
if [[ -d "$CONTRACTS_DIR" ]] && [[ -n "$(ls -A "$CONTRACTS_DIR" 2>/dev/null)" ]]; then
    docs+=("contracts/")
fi
[[ -f "$QUICKSTART" ]] && docs+=("quickstart.md")
docs+=("tasks.md")

if $JSON_MODE; then
    json_docs=$(for d in "${docs[@]}"; do printf '"%s",' "$(json_escape "$d")"; done)
    json_docs="[${json_docs%,}]"
    printf '{"FEATURE_DIR":"%s","TASKS":"%s","AVAILABLE_DOCS":%s}\n' \
        "$(json_escape "$FEATURE_DIR")" "$(json_escape "$TASKS")" "$json_docs"
else
    echo "FEATURE_DIR:$FEATURE_DIR"
    echo "TASKS:$TASKS"
    echo "AVAILABLE_DOCS:"
    for d in "${docs[@]}"; do
        echo "  ✓ $d"
    done
fi
