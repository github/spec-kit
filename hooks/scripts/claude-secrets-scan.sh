#!/usr/bin/env bash
# MiniSpec Hook: secrets-scan (Claude Code version)
# Scans for secrets before git add/commit
#
# Reads JSON from stdin, checks staged files for secrets,
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

# Only check commands that contain git add or git commit (handles chained commands)
if [[ ! "$COMMAND" =~ git[[:space:]]+(add|commit) ]]; then
    echo '{}'
    exit 0  # Allow non-git commands
fi

# Get staged files (or files being added)
if [[ "$COMMAND" =~ git[[:space:]]+add ]]; then
    # Extract args after 'git add'
    ARGS=$(echo "$COMMAND" | sed -E 's/^.*git[[:space:]]+add[[:space:]]*//')
    # Wildcards or flags-only: resolve via git diff
    if [[ "$ARGS" == "." ]] || [[ "$ARGS" == "-A" ]] || [[ "$ARGS" == "--all" ]] || [[ "$ARGS" =~ ^- ]]; then
        FILES=$(git diff --name-only 2>/dev/null || echo "")
    else
        # Explicit file list: convert space-delimited args to newline-delimited
        FILES=$(echo "$ARGS" | tr ' ' '\n')
    fi
else
    # For commit, check already staged files
    FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")
fi

if [[ -z "$FILES" ]]; then
    echo '{}'
    exit 0
fi

# Secret patterns (simplified for grep -E)
PATTERNS=(
    $'api[_-]?key[[:space:]]*[=:][[:space:]]*["\'][^"\']{6,}["\']'
    $'secret[_-]?key[[:space:]]*[=:][[:space:]]*["\'][^"\']{6,}["\']'
    $'password[[:space:]]*[=:][[:space:]]*["\'][^"\']{4,}["\']'
    'AKIA[0-9A-Z]{16}'
    '-----BEGIN .* PRIVATE KEY-----'
)

FOUND_SECRETS=""

# Scan each file (read line-by-line to handle spaces in filenames)
while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ ! -f "$file" ]]; then
        continue
    fi

    # Skip common non-secret files
    if [[ "$file" =~ \.(md|lock|sample|example)$ ]]; then
        continue
    fi

    for pattern in "${PATTERNS[@]}"; do
        match=$(grep -nEi "$pattern" "$file" 2>/dev/null | head -1 || true)
        if [[ -n "$match" ]]; then
            FOUND_SECRETS="$FOUND_SECRETS\n- $file: $match"
        fi
    done
done <<< "$FILES"

if [[ -n "$FOUND_SECRETS" ]]; then
    # Return deny decision as JSON
    jq -n --arg secrets "$FOUND_SECRETS" '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: ("Potential secrets detected in staged files:" + $secrets + "\n\nUse environment variables or .env files instead of hardcoding secrets.")
        }
    }'
    exit 0
fi

# Allow the command
echo '{}'
exit 0
