#!/usr/bin/env bash
set -e

# setup-ui.sh: Prepare UI blueprint files for the current feature.
# Outputs JSON with absolute paths so agents can write content deterministically.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Resolve paths and feature context
eval $(get_feature_paths)

# Validate branch context for git repos
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

UI_DIR="$FEATURE_DIR/ui"
mkdir -p "$UI_DIR"

fail() { echo "[speckit.ui] ERROR: $*" >&2; exit 1; }

# Resolve template root to work in both packaged projects and repo checkouts
if [[ -d "$REPO_ROOT/.specify/templates/ui" ]]; then
  TEMPLATE_ROOT="$REPO_ROOT/.specify/templates/ui"
elif [[ -d "$REPO_ROOT/templates/ui" ]]; then
  TEMPLATE_ROOT="$REPO_ROOT/templates/ui"
else
  fail "UI templates not found. Expected at either: \n  - $REPO_ROOT/.specify/templates/ui \n  - $REPO_ROOT/templates/ui \nPlease ensure the project was initialized via 'specify init' or that templates/ui exists."
fi

# Files to provision
TOKENS_FILE="$UI_DIR/tokens.json"
COMPONENTS_SPEC="$UI_DIR/components.md"
FLOWS_FILE="$UI_DIR/flows.mmd"
HTML_SKELETON="$UI_DIR/skeleton.html"
BDD_FILE="$UI_DIR/stories.feature"
TYPES_TS_FILE="$UI_DIR/types.ts"
TYPES_SCHEMA_FILE="$UI_DIR/types.schema.json"
README_FILE="$UI_DIR/README.md"

# Copy templates; if any is missing, fail-fast with guidance
copy_or_fail() {
  local src="$1"; local dest="$2"; local name="$3"
  [[ -f "$src" ]] || fail "Missing template: $name at $src"
  cp "$src" "$dest"
}

copy_or_fail "$TEMPLATE_ROOT/tokens.json" "$TOKENS_FILE" "tokens.json"
copy_or_fail "$TEMPLATE_ROOT/components.md" "$COMPONENTS_SPEC" "components.md"
copy_or_fail "$TEMPLATE_ROOT/flows.mmd" "$FLOWS_FILE" "flows.mmd"
copy_or_fail "$TEMPLATE_ROOT/skeleton.html" "$HTML_SKELETON" "skeleton.html"
copy_or_fail "$TEMPLATE_ROOT/stories.feature" "$BDD_FILE" "stories.feature"
copy_or_fail "$TEMPLATE_ROOT/types.ts" "$TYPES_TS_FILE" "types.ts"
# JSON Schema is optional but preferred; include if present
if [[ -f "$TEMPLATE_ROOT/types.schema.json" ]]; then
  cp "$TEMPLATE_ROOT/types.schema.json" "$TYPES_SCHEMA_FILE"
fi
copy_or_fail "$TEMPLATE_ROOT/README.md" "$README_FILE" "README.md"

# Print JSON for agent consumption
printf '{"UI_DIR":"%s","TOKENS_FILE":"%s","COMPONENTS_SPEC":"%s","FLOWS_FILE":"%s","HTML_SKELETON":"%s","BDD_FILE":"%s","TYPES_TS":"%s","TYPES_SCHEMA":"%s","README_FILE":"%s"}\n' \
  "$UI_DIR" "$TOKENS_FILE" "$COMPONENTS_SPEC" "$FLOWS_FILE" "$HTML_SKELETON" "$BDD_FILE" "$TYPES_TS_FILE" "${TYPES_SCHEMA_FILE:-}" "$README_FILE"
