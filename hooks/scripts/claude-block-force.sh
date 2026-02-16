#!/usr/bin/env bash
# MiniSpec Hook: block-force (Claude Code version)
# Blocks destructive git operations
#
# Reads JSON from stdin, checks for dangerous commands,
# returns JSON decision to Claude Code

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract the command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Dangerous patterns
DANGEROUS_PATTERNS=(
    "git reset --hard"
    "git push --force"
    "git push -f"
    "git clean -f"
    "git checkout ."
    "git restore ."
)

# Check if command matches any dangerous pattern
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if [[ "$COMMAND" == *"$pattern"* ]]; then
        # Return deny decision as JSON
        jq -n --arg cmd "$COMMAND" --arg pattern "$pattern" '{
            hookSpecificOutput: {
                hookEventName: "PreToolUse",
                permissionDecision: "deny",
                permissionDecisionReason: ("Destructive command blocked: " + $pattern + ". This can cause irreversible data loss. If you really need to run this, ask the user to run it manually.")
            }
        }'
        exit 0
    fi
done

# Allow the command
exit 0
