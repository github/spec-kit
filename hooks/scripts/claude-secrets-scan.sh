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

# Get files to scan.
# For 'git add': respect the pathspec from the command so that 'git add README.md'
# doesn't trigger false positives from unrelated untracked files.
#   - If the args are a wildcard/flag form (`.`, `-A`, `--all`, or any flag), ask git
#     for all modified tracked + all untracked files.
#   - Otherwise, pass the args as a pathspec to git so only the relevant files are
#     returned.  (Git handles glob expansion; we avoid complex shell parsing.)
# For 'git commit': scan the index blob (git show ":$file") so partially-staged
# files are checked for what is actually staged, not the on-disk version.
SCAN_FROM_INDEX=false
if [[ "$COMMAND" =~ git[[:space:]]+add ]]; then
    ARGS=$(printf '%s\n' "$COMMAND" | sed -E 's/.*git[[:space:]]+add[[:space:]]+(.*)/\1/' | head -1)
    if [[ "$ARGS" == "." ]] || [[ "$ARGS" == "-A" ]] || [[ "$ARGS" == "--all" ]] || \
       [[ "$ARGS" =~ ^- ]] || [[ -z "$ARGS" ]]; then
        # Wildcard/flag-only: scan all modified tracked + all untracked
        TRACKED=$(git diff --name-only 2>/dev/null || echo "")
        UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || echo "")
    else
        # Specific pathspec: let git resolve it (handles globs, paths, etc.)
        # shellcheck disable=SC2086
        TRACKED=$(git diff --name-only -- $ARGS 2>/dev/null || echo "")
        # shellcheck disable=SC2086
        UNTRACKED=$(git ls-files --others --exclude-standard -- $ARGS 2>/dev/null || echo "")
    fi
    FILES=$(printf '%s\n%s\n' "$TRACKED" "$UNTRACKED" | sed '/^$/d' | sort -u)
else
    # For commit, check already-staged files and scan from the index
    FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")
    SCAN_FROM_INDEX=true
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

# Message prefix depends on whether we're checking files-to-be-staged or already-staged content
if [[ "$SCAN_FROM_INDEX" == true ]]; then
    DENY_PREFIX="Potential secrets detected in staged files:"
else
    DENY_PREFIX="Potential secrets detected in files to be staged:"
fi

# Scan each file (read line-by-line to handle spaces in filenames)
while IFS= read -r file; do
    [[ -z "$file" ]] && continue

    # Skip common non-secret files
    if [[ "$file" =~ \.(md|lock|sample|example)$ ]]; then
        continue
    fi

    # Get content: from the index blob for commits (what is actually staged),
    # or from disk for git add (what will be staged).
    local_content=""
    if [[ "$SCAN_FROM_INDEX" == true ]]; then
        local_content=$(git show ":$file" 2>/dev/null || true)
        [[ -z "$local_content" ]] && continue
    else
        [[ ! -f "$file" ]] && continue
        local_content=$(cat "$file" 2>/dev/null || true)
    fi

    for pattern in "${PATTERNS[@]}"; do
        match=$(printf '%s\n' "$local_content" | grep -nEi "$pattern" | head -1 || true)
        if [[ -n "$match" ]]; then
            FOUND_SECRETS="$FOUND_SECRETS\n- $file: $match"
        fi
    done
done <<< "$FILES"

if [[ -n "$FOUND_SECRETS" ]]; then
    # Return deny decision as JSON
    jq -n --arg secrets "$FOUND_SECRETS" --arg prefix "$DENY_PREFIX" '{
        hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: ($prefix + $secrets + "\n\nUse environment variables or .env files instead of hardcoding secrets.")
        }
    }'
    exit 0
fi

# Allow the command
echo '{}'
exit 0
