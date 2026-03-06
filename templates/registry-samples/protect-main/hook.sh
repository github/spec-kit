#!/usr/bin/env bash
set -euo pipefail

# protect-main - Prevents direct commits to main/master branches
# Installed by MiniSpec registry package
#
# This hook runs on PreToolUse for Bash commands. It reads the
# tool input JSON from stdin and checks if the command would
# commit directly to main or master.

# Read tool input from stdin
INPUT=$(cat)

# Extract the command being run
COMMAND=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' || true)

# Skip if no command found
if [ -z "$COMMAND" ]; then
  exit 0
fi

# Only check git commit commands
if ! echo "$COMMAND" | grep -q "git commit"; then
  exit 0
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Block commits on main or master
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "Blocked: direct commits to '$BRANCH' are not allowed." >&2
  echo "Create a feature branch first: git checkout -b feature/my-change" >&2
  exit 2
fi

exit 0
