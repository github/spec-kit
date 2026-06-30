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
# When `plan_path` is omitted, the script derives it from `.specify/feature.json`
# (written by /speckit-specify). Falls back to the most recently modified
# `specs/*/plan.md` only when feature.json is absent or its plan does not exist yet.

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
#
# NOTE (bash 3.2 / macOS portability): the embedded Python heredocs below run
# inside $(...) command substitution. bash 3.2 (the system /bin/bash on macOS)
# mis-parses a single-quote/apostrophe in a heredoc body nested in $(...),
# failing with "unexpected EOF while looking for matching `''". Keep these
# $(...)-nested heredoc bodies free of apostrophes (use double quotes in Python
# string literals and avoid contractions in comments).
if ! _raw_opts="$("$_python" - "$EXT_CONFIG" "$_case_insensitive_context_files" "$PROJECT_ROOT" <<'PY'
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
def add_context_file(value):
    if not isinstance(value, str):
        return
    candidate = value.strip()
    if not candidate:
        return
    key = candidate.casefold() if case_insensitive else candidate
    if key in seen_context_files:
        return
    context_files.append(candidate)
    seen_context_files.add(key)
raw_files = data.get("context_files")
if isinstance(raw_files, list):
    for value in raw_files:
        add_context_file(value)
if not context_files:
    add_context_file(get_str(data, "context_file"))
if not context_files:
    # Self-seed: the agent-context extension manages its own lifecycle, so when
    # its config declares no target, it derives one from the active integration
    # recorded in init-options.json, mapped through the bundled
    # agent-context-defaults.json file. This is independent of the Specify CLI
    # by design; nothing here imports specify_cli.
    project_root = sys.argv[3] if len(sys.argv) > 3 else "."
    integration_key = ""
    try:
        with open(
            f"{project_root}/.specify/init-options.json", "r", encoding="utf-8"
        ) as fh:
            opts = json.load(fh)
        if isinstance(opts, dict):
            value = opts.get("integration") or opts.get("ai") or ""
            integration_key = value if isinstance(value, str) else ""
    except Exception:
        integration_key = ""
    if integration_key:
        defaults_path = (
            f"{project_root}/.specify/extensions/agent-context/"
            "agent-context-defaults.json"
        )
        mapping = {}
        try:
            with open(defaults_path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            agents = loaded.get("agents", {}) if isinstance(loaded, dict) else {}
            mapping = agents if isinstance(agents, dict) else {}
        except Exception:
            print(
                "agent-context: unable to read %s; cannot self-seed the context "
                "file. Set context_file in the extension config." % defaults_path,
                file=sys.stderr,
            )
            mapping = {}
        add_context_file(mapping.get(integration_key, "") or "")
        if not context_files:
            print(
                "agent-context: no default context file is known for integration "
                "%s. Set context_file in the extension config to choose one."
                % integration_key,
                file=sys.stderr,
            )
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
  # Prefer .specify/feature.json (written by /speckit-specify) over mtime heuristic.
  _feature_json="$PROJECT_ROOT/.specify/feature.json"
  if [[ -f "$_feature_json" ]]; then
    _feature_dir="$("$_python" - "$_feature_json" <<'PY'
import sys, json
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        d = json.load(fh)
    val = d.get("feature_directory", "")
    print(val if isinstance(val, str) else "")
except Exception:
    print("")
PY
)"
    # Normalize backslashes (written by PS on Windows) to forward slashes before path ops.
    _feature_dir="$(printf '%s' "$_feature_dir" | tr '\\' '/')"
    _feature_dir="${_feature_dir%/}"
    if [[ -n "$_feature_dir" ]]; then
      # feature_directory may be relative or absolute (absolute paths outside PROJECT_ROOT
      # are preserved as-is by _persist_feature_json in common.sh).
      # Also match drive-qualified paths (C:/...) written by PowerShell on Windows.
      if [[ "$_feature_dir" == /* ]] || [[ "$_feature_dir" =~ ^[A-Za-z]:/ ]]; then
        _candidate="$_feature_dir/plan.md"
      else
        _candidate="$PROJECT_ROOT/$_feature_dir/plan.md"
      fi
      if [[ -f "$_candidate" ]]; then
        # Resolve symlinks before comparing so paths like /var/… vs /private/var/…
        # (macOS) are treated as equivalent. Mirrors the mtime-fallback approach.
        PLAN_PATH="$("$_python" - "$PROJECT_ROOT" "$_candidate" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
cand = Path(sys.argv[2]).resolve()
try:
    print(cand.relative_to(root).as_posix())
except ValueError:
    # Outside project root: emit the resolved path in POSIX form.
    # as_posix() converts backslashes correctly on native Windows Python.
    print(cand.as_posix())
PY
)"
      fi
    fi
  fi

  # Fall back to mtime only when feature.json is absent or its plan does not exist yet.
  # Python emits a project-relative POSIX path directly to avoid bash prefix-strip
  # issues with backslash paths on Windows (Git bash / MSYS2).
  if [[ -z "$PLAN_PATH" ]]; then
    _plan_rel="$("$_python" - "$PROJECT_ROOT" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
specs = root / "specs"
plans = sorted(
    specs.glob("*/plan.md"),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if plans:
    try:
        print(plans[0].relative_to(root).as_posix())
    except ValueError:
        print("")
else:
    print("")
PY
)"
    if [[ -n "$_plan_rel" ]]; then
      PLAN_PATH="$_plan_rel"
    fi
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
import os
import re
import sys

ctx_path, start, end, section_path = sys.argv[1:5]
with open(section_path, "r", encoding="utf-8") as fh:
    section = fh.read().rstrip("\n") + "\n"


def ensure_mdc_frontmatter(content):
    """Ensure ``.mdc`` content has YAML frontmatter with ``alwaysApply: true``.

    Cursor only auto-loads ``.mdc`` rule files that carry frontmatter with
    ``alwaysApply: true``. Prepend it when missing, or repair the value while
    preserving any existing frontmatter comments/formatting.
    """
    leading_ws = len(content) - len(content.lstrip())
    leading = content[:leading_ws]
    stripped = content[leading_ws:]

    if not stripped.startswith("---"):
        return "---\nalwaysApply: true\n---\n\n" + content

    match = re.match(
        r"^(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*)(\r?\n|$)(.*)",
        stripped,
        re.DOTALL,
    )
    if not match:
        return "---\nalwaysApply: true\n---\n\n" + content

    opening, fm_text, closing, sep, rest = match.groups()
    newline = "\r\n" if "\r\n" in opening else "\n"

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*(?:#.*)?$", fm_text):
        return content

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:", fm_text):
        fm_text = re.sub(
            r"(?m)^([ \t]*)alwaysApply[ \t]*:.*?([ \t]*(?:#.*)?)$",
            r"\1alwaysApply: true\2",
            fm_text,
            count=1,
        )
    elif fm_text.strip():
        fm_text = fm_text + newline + "alwaysApply: true"
    else:
        fm_text = "alwaysApply: true"

    return f"{leading}{opening}{fm_text}{closing}{sep}{rest}"


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
if ctx_path.casefold().endswith(".mdc"):
    new_content = ensure_mdc_frontmatter(new_content)
with open(ctx_path, "wb") as fh:
    fh.write(new_content.encode("utf-8"))
PY

  echo "agent-context: updated $CONTEXT_FILE"
done
