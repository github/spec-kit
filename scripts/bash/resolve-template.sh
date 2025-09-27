#!/usr/bin/env bash

set -e

# Resolve a template path with optional JSON output.
# Usage: resolve-template.sh [--json] <key>
#   key: spec | plan | tasks | pprd | <custom>
# Behavior:
#   - Prefer assets override at .specs/.specify/templates/assets/<key>-template.md (case-insensitive)
#   - Fallback to .specs/.specify/templates/<key>-template.md
# Output:
#   - JSON: {"TEMPLATE_PATH":"/abs/path"}
#   - Plain: /abs/path

JSON_MODE=false
KEY=""

for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h)
      echo "Usage: $0 [--json] <key>"; exit 0 ;;
    *) KEY="$arg" ;;
  esac
done

if [[ -z "$KEY" ]]; then
  echo "Error: missing <key>. Usage: $0 [--json] <key>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
TEMPLATES_DIR="$REPO_ROOT/.specs/.specify/templates"
ASSETS_DIR="$TEMPLATES_DIR/assets"

# Try assets override (case-insensitive match)
ASSET_CANDIDATE=""
if [[ -d "$ASSETS_DIR" ]]; then
  ASSET_CANDIDATE=$(find "$ASSETS_DIR" -maxdepth 1 -type f -iname "${KEY}-template.md" -print -quit || true)
fi

if [[ -n "$ASSET_CANDIDATE" ]]; then
  PATH_OUT="$ASSET_CANDIDATE"
else
  # Fallback to default location
  DEFAULT_PATH="$TEMPLATES_DIR/${KEY}-template.md"
  if [[ -f "$DEFAULT_PATH" ]]; then
    PATH_OUT="$DEFAULT_PATH"
  else
    echo "Error: No template found for key '$KEY'. Looked for: $ASSETS_DIR/[${KEY}-template.md] and $DEFAULT_PATH" >&2
    exit 1
  fi
fi

if $JSON_MODE; then
  printf '{"TEMPLATE_PATH":"%s"}\n' "$PATH_OUT"
else
  printf '%s\n' "$PATH_OUT"
fi

