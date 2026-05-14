#!/usr/bin/env bash
# update-agent-context.sh
#
# Refresh the managed Spec Kit section in the coding agent's context file
# (e.g. CLAUDE.md, .github/copilot-instructions.md, AGENTS.md).
#
# Reads `context_file` and `context_markers.{start,end}` from the
# agent-context extension config:
#   .specify/extensions/agent-context/agent-context-config.yml
#
# Usage: update-agent-context.sh [plan_path]
#
# When `plan_path` is omitted, the script picks the most recently modified
# `specs/*/plan.md` if any exist, otherwise emits the section without a
# concrete plan path.

set -euo pipefail

PROJECT_ROOT="$(pwd)"
EXT_CONFIG="$PROJECT_ROOT/.specify/extensions/agent-context/agent-context-config.yml"
DEFAULT_START="<!-- SPECKIT START -->"
DEFAULT_END="<!-- SPECKIT END -->"

if [[ ! -f "$EXT_CONFIG" ]]; then
  echo "agent-context: $EXT_CONFIG not found; nothing to do." >&2
  exit 0
fi

# Locate a suitable Python interpreter (python3, then python).
_python=""
if command -v python3 >/dev/null 2>&1; then
  _python="python3"
elif command -v python >/dev/null 2>&1 && python --version 2>&1 | grep -q "^Python 3"; then
  _python="python"
fi

if [[ -z "$_python" ]]; then
  echo "agent-context: Python 3 not found on PATH; skipping update." >&2
  exit 0
fi

# Parse extension config once; emit three newline-separated fields:
# context_file, context_markers.start, context_markers.end
if ! _raw_opts="$("$_python" - "$EXT_CONFIG" <<'PY'
import sys
try:
    import yaml
except ImportError:
    print(
        "agent-context: PyYAML is required to parse extension config but is not available "
        "in the current Python environment.\n"
        "  To resolve: pip install pyyaml  (or install it into the environment used by python3).\n"
        "  Context file will not be updated until PyYAML is importable.",
        file=sys.stderr,
    )
    sys.exit(2)
try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
except Exception as exc:
    print(
        f"agent-context: unable to parse {sys.argv[1]} ({exc}); cannot update context.",
        file=sys.stderr,
    )
    sys.exit(2)
if not isinstance(data, dict):
    data = {}
def get_str(obj, *keys):
    node = obj
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return ""
    return node if isinstance(node, str) else ""
print(get_str(data, "context_file"))
print(get_str(data, "context_markers", "start"))
print(get_str(data, "context_markers", "end"))
PY
)"; then
  echo "agent-context: skipping update (see above for details)." >&2
  exit 0
fi

{
  IFS= read -r CONTEXT_FILE
  IFS= read -r MARKER_START
  IFS= read -r MARKER_END
} <<< "$_raw_opts"

if [[ -z "$CONTEXT_FILE" ]]; then
  echo "agent-context: context_file not set in extension config; nothing to do." >&2
  exit 0
fi

[[ -z "$MARKER_START" ]] && MARKER_START="$DEFAULT_START"
[[ -z "$MARKER_END"   ]] && MARKER_END="$DEFAULT_END"

PLAN_PATH="${1:-}"
if [[ -z "$PLAN_PATH" ]]; then
  # Pick the most recently modified plan.md one level deep (specs/<feature>/plan.md).
  # Use find + sort by modification time to avoid ls/head fragility with
  # spaces in paths or SIGPIPE from pipefail.
  _plan_abs="$("$_python" - "$PROJECT_ROOT" <<'PY'
import sys, os
from pathlib import Path
specs = Path(sys.argv[1]) / "specs"
plans = sorted(
    specs.glob("*/plan.md"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
print(plans[0] if plans else "")
PY
)"
  if [[ -n "$_plan_abs" ]]; then
    PLAN_PATH="${_plan_abs#"$PROJECT_ROOT/"}"
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

"$_python" - "$CTX_PATH" "$MARKER_START" "$MARKER_END" "$TMP_SECTION" <<'PY'
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
