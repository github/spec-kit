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

# Strip common wrappers (sudo, 'command' builtin, env keyword, env VAR=val) from a subcommand.
# Also handles option flags on wrappers (e.g. sudo -u root, env -i) by advancing past
# any option tokens that follow a stripped keyword, using '##* git' to locate 'git'.
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
    # If cmd still starts with option flags after keyword/assignment stripping
    # (e.g. 'sudo -u root git ...' leaves '-u root git ...'), advance greedily
    # to the last ' git' occurrence so wrapper options are skipped regardless of
    # whether they take arguments (sudo -E, sudo -u user, env -i, etc.).
    if [[ "$cmd" =~ ^- ]] && [[ "$cmd" =~ [[:space:]]git([[:space:]]|$) ]]; then
        cmd="git${cmd##* git}"
    fi
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
