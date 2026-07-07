#!/usr/bin/env bash
# AI Team extension: resolve effective spec path for downstream SDD commands
#
# Usage: resolve-handoff-spec.sh [--json] [argument text...]

set -e

JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json] [arguments...]"
            exit 0
            ;;
        *) ARGS+=("$arg") ;;
    esac
done

ARGS_TEXT="${ARGS[*]}"

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=handoff-spec-common.sh
source "$SCRIPT_DIR/handoff-spec-common.sh"

REPO_ROOT="$(handoff_spec_repo_root)"
cd "$REPO_ROOT"

handoff_spec_load_core
_paths_output=$(get_feature_paths --no-persist) || {
    echo "ERROR: Failed to resolve feature paths" >&2
    exit 1
}
eval "$_paths_output"

OVERRIDE_NAME="$(_override_file_name "$REPO_ROOT")"
OVERRIDE_FILE="$FEATURE_DIR/$OVERRIDE_NAME"
SPEC_FILE="$FEATURE_SPEC"
EFFECTIVE_SPEC="$(resolve_effective_spec "$FEATURE_DIR" "$OVERRIDE_NAME")"

if [[ ! -f "$OVERRIDE_FILE" ]]; then
    if url=$(_read_url_from_spec_frontmatter "$SPEC_FILE" 2>/dev/null); then
        echo "ERROR: spec.override.md missing but handoff URL present in spec.md. Re-run speckit.plan or speckit.ai-team.handoff-spec-sync." >&2
        exit 1
    fi
    if resolve_handoff_requirement_url "$REPO_ROOT" "$ARGS_TEXT" >/dev/null 2>&1; then
        echo "ERROR: handoff URL configured but spec.override.md missing. Re-run speckit.ai-team.handoff-spec-sync." >&2
        exit 1
    fi
fi

if $JSON_MODE; then
    emit_handoff_json false "$FEATURE_DIR" "$SPEC_FILE" "$EFFECTIVE_SPEC" "" false
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "FEATURE_SPEC: $SPEC_FILE"
    echo "EFFECTIVE_SPEC: $EFFECTIVE_SPEC"
fi
