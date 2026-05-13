#!/usr/bin/env bash
# update-agent-context.sh
#
# Refresh the managed Spec Kit section in the coding agent's context file
# (e.g. CLAUDE.md, .github/copilot-instructions.md, AGENTS.md).
#
# Reads `context_file` and `context_markers.{start,end}` from
# `.specify/init-options.json`. Falls back to the default markers when
# `context_markers` is absent.
#
# Usage: update-agent-context.sh [plan_path]
#
# When `plan_path` is omitted, the script picks the most recently modified
# `specs/*/plan.md` if any exist, otherwise emits the section without a
# concrete plan path.

set -euo pipefail

PROJECT_ROOT="$(pwd)"
INIT_OPTIONS="$PROJECT_ROOT/.specify/init-options.json"
DEFAULT_START="<!-- SPECKIT START -->"
DEFAULT_END="<!-- SPECKIT END -->"

if [[ ! -f "$INIT_OPTIONS" ]]; then
  echo "agent-context: $INIT_OPTIONS not found; nothing to do." >&2
  exit 0
fi

# Use python for JSON parsing (always available in spec-kit projects).
read_json_field() {
  # $1 = jq-style dotted path, e.g. "context_markers.start"
  python3 - "$INIT_OPTIONS" "$1" <<'PY'
import json, sys
path = sys.argv[1]
key = sys.argv[2]
try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    sys.exit(0)
node = data
for part in key.split("."):
    if isinstance(node, dict) and part in node:
        node = node[part]
    else:
        sys.exit(0)
if isinstance(node, str):
    sys.stdout.write(node)
PY
}

CONTEXT_FILE="$(read_json_field 'context_file' || true)"
if [[ -z "$CONTEXT_FILE" ]]; then
  echo "agent-context: context_file not set in init-options.json; nothing to do." >&2
  exit 0
fi

MARKER_START="$(read_json_field 'context_markers.start' || true)"
MARKER_END="$(read_json_field 'context_markers.end' || true)"
[[ -z "$MARKER_START" ]] && MARKER_START="$DEFAULT_START"
[[ -z "$MARKER_END"   ]] && MARKER_END="$DEFAULT_END"

PLAN_PATH="${1:-}"
if [[ -z "$PLAN_PATH" ]]; then
  if compgen -G "$PROJECT_ROOT/specs/*/plan.md" > /dev/null; then
    # Pick the most recently modified plan.md
    PLAN_PATH="$(ls -1t "$PROJECT_ROOT"/specs/*/plan.md 2>/dev/null | head -1 | sed "s|$PROJECT_ROOT/||")"
  fi
fi

CTX_PATH="$PROJECT_ROOT/$CONTEXT_FILE"
mkdir -p "$(dirname "$CTX_PATH")"

# Build the managed section
TMP_SECTION="$(mktemp)"
trap 'rm -f "$TMP_SECTION"' EXIT
{
  echo "$MARKER_START"
  echo "For additional context about technologies to be used, project structure,"
  echo "shell commands, and other important information, read the current plan"
  if [[ -n "$PLAN_PATH" ]]; then
    echo "at $PLAN_PATH"
  fi
  echo "$MARKER_END"
} > "$TMP_SECTION"

python3 - "$CTX_PATH" "$MARKER_START" "$MARKER_END" "$TMP_SECTION" <<'PY'
import sys, os
ctx_path, start, end, section_path = sys.argv[1:5]
with open(section_path, "r", encoding="utf-8") as fh:
    section = fh.read().rstrip("\n") + "\n"

if os.path.exists(ctx_path):
    with open(ctx_path, "r", encoding="utf-8-sig") as fh:
        content = fh.read()
    s = content.find(start)
    e = content.find(end, s if s != -1 else 0)
    if s != -1 and e != -1 and e > s:
        end_of_marker = e + len(end)
        if end_of_marker < len(content) and content[end_of_marker] == "\r":
            end_of_marker += 1
        if end_of_marker < len(content) and content[end_of_marker] == "\n":
            end_of_marker += 1
        new_content = content[:s] + section + content[end_of_marker:]
    elif s != -1:
        new_content = content[:s] + section
    elif e != -1:
        end_of_marker = e + len(end)
        if end_of_marker < len(content) and content[end_of_marker] == "\r":
            end_of_marker += 1
        if end_of_marker < len(content) and content[end_of_marker] == "\n":
            end_of_marker += 1
        new_content = section + content[end_of_marker:]
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = (content + "\n" + section) if content else section
else:
    new_content = section

new_content = new_content.replace("\r\n", "\n").replace("\r", "\n")
with open(ctx_path, "wb") as fh:
    fh.write(new_content.encode("utf-8"))
PY

echo "agent-context: updated $CONTEXT_FILE"
