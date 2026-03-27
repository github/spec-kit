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

# Strip common wrappers (sudo, 'command' builtin, env keyword, env VAR=val) from a subcommand
strip_wrappers() {
    local cmd="$1"
    # Strip leading whitespace
    cmd="${cmd#"${cmd%%[! ]*}"}"
    # Strip sudo/command/env prefixes (may repeat, e.g. sudo env git ...)
    while [[ "$cmd" =~ ^(sudo|command|env)[[:space:]] ]]; do
        cmd="${cmd#*[[:space:]]}"
        cmd="${cmd#"${cmd%%[! ]*}"}"
    done
    # Strip env var assignments at start (VAR=val ...) — handles 'env FOO=bar git ...'
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
        # Match: exact, pattern + space (extra args), or pattern + more flag chars
        # (e.g. 'git clean -fd' and 'git clean -fxd' must match pattern 'git clean -f')
        if [[ "$subcommand" == "$pattern" ]] || \
           [[ "$subcommand" == "$pattern "* ]] || \
           { [[ "$pattern" =~ [[:space:]]-[a-zA-Z]$ ]] && [[ "$subcommand" == "$pattern"[a-zA-Z]* ]]; }; then
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
done < <(printf '%s\n' "$COMMAND" | sed -E 's/(&&|\|\||;|\|)/\n/g')

# Allow the command
echo '{}'
exit 0
