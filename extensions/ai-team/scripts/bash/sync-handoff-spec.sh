#!/usr/bin/env bash
# AI Team extension: fetch handoff requirement URL and build spec.override.md
#
# Usage: sync-handoff-spec.sh [--json] [argument text...]

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

if ! url=$(resolve_handoff_requirement_url "$REPO_ROOT" "$ARGS_TEXT"); then
    if $JSON_MODE; then
        emit_handoff_json true "$FEATURE_DIR" "$SPEC_FILE" "$EFFECTIVE_SPEC" "" false
    else
        echo "SKIPPED: no handoff_requirement_url found"
    fi
    exit 0
fi

bootstrapped=false
if [[ ! -f "$SPEC_FILE" ]]; then
    write_spec_pointer "$SPEC_FILE" "$url"
    bootstrapped=true
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
fetched="$tmpdir/fetched.md"

if ! fetch_remote_requirement "$url" "$fetched"; then
    echo "ERROR: Failed to fetch handoff requirement URL: $url" >&2
    exit 1
fi

write_merged_override "$OVERRIDE_FILE" "$url" "$SPEC_FILE" "$fetched"
ensure_gitignore_pattern "$REPO_ROOT" "**/$OVERRIDE_NAME"

EFFECTIVE_SPEC="$(resolve_effective_spec "$FEATURE_DIR" "$OVERRIDE_NAME")"

bootstrapped_json=false
if [[ "$bootstrapped" == true ]]; then
    bootstrapped_json=true
fi

if $JSON_MODE; then
    emit_handoff_json false "$FEATURE_DIR" "$SPEC_FILE" "$EFFECTIVE_SPEC" "$url" "$bootstrapped_json"
else
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "FEATURE_SPEC: $SPEC_FILE"
    echo "EFFECTIVE_SPEC: $EFFECTIVE_SPEC"
    echo "HANDOFF_REQUIREMENT_URL: $url"
    echo "SPEC_BOOTSTRAPPED: $bootstrapped"
fi
