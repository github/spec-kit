#!/usr/bin/env bash
# Component: workflow launcher; target: developer workstation; task: fork workflow.
set -e
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
    context) helper=workflow_context.py ;;
    progress) helper=code_progress.py ;;
    *) echo "Usage: workflow.sh context STAGE | progress ACTION [options]" >&2; exit 1 ;;
esac
shift
helper_path="$SCRIPT_DIR/../python/$helper"
# Git Bash may inherit MSYS_NO_PATHCONV; pass an explicit native filename.
if command -v cygpath >/dev/null 2>&1; then
    helper_path="$(cygpath -m "$helper_path")"
fi
python_candidates=("${SPECKIT_PYTHON_EXECUTABLE:-${SPECKIT_PYTHON:-}}" "$SCRIPT_DIR/../../../.venv/bin/python" "$SCRIPT_DIR/../../../.venv/Scripts/python.exe" python3 python)
for executable in "${python_candidates[@]}"; do
    if [[ -n "$executable" ]] && command -v "$executable" >/dev/null 2>&1 &&
        "$executable" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
        exec "$executable" "$helper_path" "$@"
    fi
done
echo "ERROR: Python 3.11+ is required; set SPECKIT_PYTHON_EXECUTABLE to its executable." >&2
exit 1
