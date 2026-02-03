#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/check-prerequisites.sh"

if [[ ! -x "$CHECK_SCRIPT" ]]; then
    echo "ERROR: check-prerequisites.sh not found or not executable" >&2
    exit 1
fi

CHECK_OUTPUT="$($CHECK_SCRIPT --json --require-tasks --include-tasks 2>/tmp/taskstoepic-prereq.err || true)"
CHECK_STATUS=$?
if [[ $CHECK_STATUS -ne 0 ]]; then
    if grep -q "tasks.md not found" /tmp/taskstoepic-prereq.err; then
        echo "ERROR: tasks.md not found in feature directory. Run /speckit.tasks first." >&2
        exit 1
    fi
    cat /tmp/taskstoepic-prereq.err >&2
    exit 1
fi

FEATURE_DIR=$(python - <<'PY'
import json
import sys
payload = sys.stdin.read()
data = json.loads(payload)
print(data.get("FEATURE_DIR", ""))
PY
<<<"$CHECK_OUTPUT")

if [[ -z "$FEATURE_DIR" ]]; then
    echo "ERROR: Feature directory could not be determined." >&2
    exit 1
fi

TASKS="$FEATURE_DIR/tasks.md"
if [[ ! -f "$TASKS" ]]; then
    echo "ERROR: tasks.md not found at $TASKS" >&2
    exit 1
fi

if [[ ! -d "$REPO_ROOT/.beads" ]]; then
    echo "ERROR: Beads not initialized. Run 'bd init' to initialize beads in this repository." >&2
    exit 2
fi

if ! command -v bd >/dev/null 2>&1; then
    echo "ERROR: bd CLI not found in PATH. Install from https://github.com/steveyegge/beads" >&2
    exit 3
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
"$PYTHON_BIN" "$REPO_ROOT/.specify/lib/task_parser.py" "$FEATURE_DIR" "$TASKS" "$REPO_ROOT" "$@"
exit $?
