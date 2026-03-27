#!/usr/bin/env bash
# MiniSpec Hook: block-force (Claude Code version)
# Blocks destructive git operations
#
# Reads JSON from stdin, checks for dangerous commands,
# returns JSON decision to Claude Code

set -euo pipefail

# Require jq; fail open (allow) if unavailable rather than breaking the hook chain
if ! command -v jq &>/dev/null; then
    echo '{}'
    exit 0
fi

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

# Strip common wrappers (sudo, 'command' builtin, env VAR=val) from a subcommand
strip_wrappers() {
    local cmd="$1"
    # Strip leading whitespace
    cmd="${cmd#"${cmd%%[! ]*}"}"
    # Strip sudo/command prefixes (may repeat, e.g. sudo command git ...)
    while [[ "$cmd" =~ ^(sudo|command)[[:space:]] ]]; do
        cmd="${cmd#*[[:space:]]}"
        cmd="${cmd#"${cmd%%[! ]*}"}"
    done
    # Strip env var assignments at start (VAR=val ...)
    while [[ "$cmd" =~ ^[A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]] ]]; do
        cmd="${cmd#*[[:space:]]}"
        cmd="${cmd#"${cmd%%[! ]*}"}"
    done
    printf '%s' "$cmd"
}

# Split COMMAND on shell separators (&&, ||, ;, |) and check each subcommand
# using literal string matching to avoid regex metacharacter false positives.
while IFS= read -r subcommand; do
    subcommand=$(strip_wrappers "$subcommand")
    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        # Match exactly the pattern or pattern followed by a space (e.g. with extra flags)
        if [[ "$subcommand" == "$pattern" ]] || [[ "$subcommand" == "$pattern "* ]]; then
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
done < <(echo "$COMMAND" | sed -E 's/(&&|\|\||;|\|)/\n/g')

# Allow the command
echo '{}'
exit 0
