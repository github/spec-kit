#!/usr/bin/env bash
# MiniSpec Hook: protect-main (Claude Code version)
# Blocks git commits to protected branches
#
# Reads JSON from stdin, checks if command is a git commit on protected branch,
# returns JSON decision to Claude Code

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract the command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check commands that contain git commit (handles chained commands like "git add && git commit")
if [[ ! "$COMMAND" =~ git[[:space:]]+commit ]]; then
    exit 0  # Allow non-commit commands
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# Protected branches
PROTECTED_BRANCHES=("main" "master" "develop" "production")

# Check if current branch is protected
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [[ "$CURRENT_BRANCH" == "$branch" ]]; then
        # Return deny decision as JSON
        jq -n '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: "Direct commits to '"$CURRENT_BRANCH"' are blocked. Create a feature branch instead: git checkout -b feature/your-feature"
            }
        }'
        exit 0
    fi
done

# Allow the command
exit 0
