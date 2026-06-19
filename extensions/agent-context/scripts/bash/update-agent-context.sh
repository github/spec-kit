#!/usr/bin/env bash
# update-agent-context.sh
#
# Refresh the managed Spec Kit section in the coding agent's context file(s)
# (e.g. CLAUDE.md, .github/copilot-instructions.md, AGENTS.md).
#
# Reads `context_files` or `context_file`, plus `context_markers.{start,end}`, from the
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

# Locate a Python 3 interpreter with PyYAML available.
_python=""
_python_candidates=()
[[ -n "${SPECKIT_PYTHON:-}" ]] && _python_candidates+=("$SPECKIT_PYTHON")
_python_candidates+=("python3" "python")
for _candidate in "${_python_candidates[@]}"; do
  if command -v "$_candidate" >/dev/null 2>&1 \
    && "$_candidate" - <<'PY' >/dev/null 2>&1
import sys
try:
    import yaml  # noqa: F401
except ImportError:
    sys.exit(1)
sys.exit(0 if sys.version_info[0] == 3 else 1)
PY
  then
    _python="$_candidate"
    break
  fi
done
unset _candidate _python_candidates

if [[ -z "$_python" ]]; then
  echo "agent-context: Python 3 with PyYAML not found on PATH; skipping update." >&2
  echo "  To resolve: pip install pyyaml (or install it into the environment used by python3)." >&2
  exit 0
fi
_case_insensitive_context_files=0
case "$(uname -s 2>/dev/null || true)" in
  MINGW*|MSYS*|CYGWIN*) _case_insensitive_context_files=1 ;;
esac

# Parse extension config once; emit context files as JSON, followed by marker strings.
if ! _raw_opts="$("$_python" - "$EXT_CONFIG" "$_case_insensitive_context_files" <<'PY'
import json
import sys
try:
    import yaml
except ImportError:
    print(
        "agent-context: PyYAML is required to parse extension config but is not available "
        "in the current Python environment.\n"
        "  To resolve: pip install pyyaml (or install it into the environment used by python3).\n"
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
context_files = []
seen_context_files = set()
case_insensitive = sys.argv[2] == "1" or sys.platform.startswith(("win32", "cygwin"))
raw_files = data.get("context_files")
if isinstance(raw_files, list):
    for value in raw_files:
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if not candidate:
            continue
        key = candidate.casefold() if case_insensitive else candidate
        if key in seen_context_files:
            continue
        context_files.append(candidate)
        seen_context_files.add(key)
if not context_files:
    raw_file = get_str(data, "context_file")
    candidate = raw_file.strip()
    if candidate:
        context_files.append(candidate)
print(json.dumps(context_files))
print(get_str(data, "context_markers", "start"))
print(get_str(data, "context_markers", "end"))
PY
)"; then
  echo "agent-context: skipping update (see above for details)." >&2
  exit 0
fi

_opts_lines=()
while IFS= read -r _line || [[ -n "$_line" ]]; do
  _opts_lines+=("$_line")
done < <(printf '%s\n' "$_raw_opts")
if (( ${#_opts_lines[@]} < 3 )); then
  echo "agent-context: malformed config parser output; expected 3 lines (context_files, marker_start, marker_end), got ${#_opts_lines[@]}; skipping update." >&2
  exit 0
fi
CONTEXT_FILES_JSON="${_opts_lines[0]}"
MARKER_START="${_opts_lines[1]}"
MARKER_END="${_opts_lines[2]}"

if ! _context_files_raw="$("$_python" - "$CONTEXT_FILES_JSON" <<'PY'
import json
import sys
try:
    data = json.loads(sys.argv[1])
except Exception:
    data = []
if not isinstance(data, list):
    data = []
for value in data:
    if isinstance(value, str) and value:
        print(value)
PY
)"; then
  echo "agent-context: malformed context_files parser output; skipping update." >&2
  exit 0
fi

CONTEXT_FILES=()
while IFS= read -r _line || [[ -n "$_line" ]]; do
  [[ -n "$_line" ]] && CONTEXT_FILES+=("$_line")
done < <(printf '%s\n' "$_context_files_raw")

if (( ${#CONTEXT_FILES[@]} == 0 )); then
  echo "agent-context: context_files/context_file not set in extension config; nothing to do." >&2
  exit 0
fi

for CONTEXT_FILE in "${CONTEXT_FILES[@]}"; do
  # Reject absolute paths, backslash separators, and '..' path segments in context files
  if [[ "$CONTEXT_FILE" == /* ]] || [[ "$CONTEXT_FILE" =~ ^[A-Za-z]: ]]; then
    echo "agent-context: context files must be project-relative paths; got '$CONTEXT_FILE'." >&2
    exit 1
  fi
  if [[ "$CONTEXT_FILE" == *\\* ]]; then
    echo "agent-context: context files must not contain backslash separators; got '$CONTEXT_FILE'." >&2
    exit 1
  fi
  IFS='/' read -ra _cf_parts <<< "$CONTEXT_FILE"
  for _seg in "${_cf_parts[@]}"; do
    if [[ "$_seg" == ".." ]]; then
      echo "agent-context: context files must not contain '..' path segments; got '$CONTEXT_FILE'." >&2
      exit 1
    fi
  done
  if ! "$_python" - "$PROJECT_ROOT" "$CONTEXT_FILE" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
target = (root / sys.argv[2]).resolve(strict=False)
try:
    target.relative_to(root)
except ValueError:
    sys.exit(1)
PY
  then
    echo "agent-context: context file path resolves outside the project root; got '$CONTEXT_FILE'." >&2
    exit 1
  fi
done
unset _cf_parts _seg

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

for CONTEXT_FILE in "${CONTEXT_FILES[@]}"; do
  CTX_PATH="$PROJECT_ROOT/$CONTEXT_FILE"
  mkdir -p "$(dirname "$CTX_PATH")"

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
done
