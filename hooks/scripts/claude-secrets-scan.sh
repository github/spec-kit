#!/usr/bin/env bash
# MiniSpec Hook: secrets-scan (Claude Code version)
# Scans for secrets before git add/commit
#
# Reads JSON from stdin, checks staged files for secrets,
# returns JSON decision to Claude Code

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract the command from tool_input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only check commands that contain git add or git commit (handles chained commands)
if [[ ! "$COMMAND" =~ git[[:space:]]+(add|commit) ]]; then
    exit 0  # Allow non-git commands
fi

# Get staged files (or files being added)
if [[ "$COMMAND" =~ git[[:space:]]+add ]]; then
    # Extract files from the add command
    FILES=$(echo "$COMMAND" | sed 's/^git add //')
    # If adding all, get staged files
    if [[ "$FILES" == "." ]] || [[ "$FILES" == "-A" ]] || [[ "$FILES" == "--all" ]]; then
        FILES=$(git diff --name-only 2>/dev/null || echo "")
    fi
else
    # For commit, check already staged files
    FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")
fi

if [[ -z "$FILES" ]]; then
    exit 0
fi

# Secret patterns (simplified for grep -E)
PATTERNS=(
    'api[_-]?key\s*[=:]\s*["\x27][^"\x27]{6,}["\x27]'
    'secret[_-]?key\s*[=:]\s*["\x27][^"\x27]{6,}["\x27]'
    'password\s*[=:]\s*["\x27][^"\x27]{4,}["\x27]'
    'AKIA[0-9A-Z]{16}'
    '-----BEGIN .* PRIVATE KEY-----'
)

FOUND_SECRETS=""

# Scan each file
for file in $FILES; do
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
done

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
exit 0
