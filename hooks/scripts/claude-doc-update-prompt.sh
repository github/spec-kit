#!/usr/bin/env bash
# MiniSpec Hook: doc-update-prompt (PostToolUse)
# Reminds AI to update documentation after source code changes.
# Reads JSON from stdin (tool_name, tool_input with file_path).
# Outputs a brief reminder for source files; silently exits for non-source files.
# Always exits 0.

set -euo pipefail

# Read hook input from stdin
INPUT=$(cat)

# Extract file path from tool_input.file_path
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')

# If no file path found, exit silently
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip patterns - files that should NOT trigger documentation reminders
# Config/meta directories
case "$FILE_PATH" in
    *.minispec/*|*.claude/*|*.cursor/*|*.github/*|*.git/*|*.vscode/*) exit 0 ;;
esac

# Test files
case "$FILE_PATH" in
    *_test.go|*_test.py|*.test.js|*.test.ts|*.test.jsx|*.test.tsx|*.spec.js|*.spec.ts|*.spec.jsx|*.spec.tsx) exit 0 ;;
    */test/*|*/tests/*|*/__tests__/*|*/test_*) exit 0 ;;
esac

# Config and non-source files
case "$FILE_PATH" in
    *.md|*.txt|*.json|*.yaml|*.yml|*.toml|*.ini|*.cfg|*.conf|*.lock|*.sum) exit 0 ;;
    *.env*|*.gitignore|*.dockerignore|*.editorconfig) exit 0 ;;
    Makefile|Dockerfile*|docker-compose*) exit 0 ;;
esac

# Source code file - output reminder
echo "[MiniSpec] Source file modified: $FILE_PATH. If this change affects architecture, patterns, or module behavior, update the relevant docs in .minispec/knowledge/. Run /minispec.validate-docs to check freshness."

exit 0
