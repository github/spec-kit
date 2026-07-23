#!/usr/bin/env bash
# Git extension: auto-commit.sh
# Automatically commit changes after a Spec Kit command completes.
# Checks per-command config keys in git-config.yml before committing.
#
# Usage: auto-commit.sh <event_name> [generated_message]
#        auto-commit.sh <event_name> --message-file <path>
#   e.g.: auto-commit.sh after_specify
#   e.g.: auto-commit.sh after_specify --message-file /tmp/commit-msg.txt  (commit_style: conventional)
#
# --message-file is the preferred way to supply an agent-generated commit
# message: it reads the message from a file instead of a shell argument,
# so message content (which may contain quotes, `$(...)`, backticks, etc.)
# is never interpolated into a shell command line.

set -e

EVENT_NAME="${1:-}"
if [ -z "$EVENT_NAME" ]; then
    echo "Usage: $0 <event_name> [generated_message | --message-file <path>]" >&2
    exit 1
fi
shift || true

# Optional second argument: an agent-generated commit message (used when
# commit_style: conventional is configured). Prefer --message-file over
# passing the message directly as a shell argument.
GENERATED_MESSAGE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --message-file)
            _message_file="${2:-}"
            if [ -z "$_message_file" ]; then
                echo "[specify] Error: --message-file requires a path argument" >&2
                exit 1
            fi
            if [ ! -f "$_message_file" ]; then
                echo "[specify] Error: message file '$_message_file' not found" >&2
                exit 1
            fi
            GENERATED_MESSAGE="$(cat "$_message_file")"
            # The message file is a transport-only artifact: its content is
            # now captured above, so remove it immediately. Otherwise, if it
            # was written inside the worktree, it would be picked up as an
            # untracked change by both the "any changes?" check below and by
            # `git add .`, polluting the commit or defeating the no-changes
            # short-circuit even when nothing else changed.
            rm -f "$_message_file"
            shift 2
            ;;
        *)
            GENERATED_MESSAGE="$1"
            shift
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.specify" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

REPO_ROOT=$(_find_project_root "$SCRIPT_DIR") || REPO_ROOT="$(pwd)"
cd "$REPO_ROOT"

# Check if git is available
if ! command -v git >/dev/null 2>&1; then
    echo "[specify] Warning: Git not found; skipped auto-commit" >&2
    exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[specify] Warning: Not a Git repository; skipped auto-commit" >&2
    exit 0
fi

# Read per-command config from git-config.yml
_config_file="$REPO_ROOT/.specify/extensions/git/git-config.yml"
_enabled=false
_commit_msg=""
_commit_style="fixed"

if [ -f "$_config_file" ]; then
    # Top-level scalar key: commit_style (fixed | conventional)
    _style_val=$(grep -m1 '^commit_style:' "$_config_file" 2>/dev/null | sed 's/^commit_style:[[:space:]]*//' | sed 's/[[:space:]]\{1,\}#.*$//' | sed 's/[[:space:]]*$//' | sed 's/^["'\'']//' | sed 's/["'\'']*$//' | tr '[:upper:]' '[:lower:]')
    if [ -n "$_style_val" ]; then
        case "$_style_val" in
            fixed|conventional)
                _commit_style="$_style_val"
                ;;
            *)
                echo "[specify] Warning: unknown commit_style '$_style_val' in git-config.yml (expected 'fixed' or 'conventional'); defaulting to 'fixed'" >&2
                ;;
        esac
    fi

    # Parse the auto_commit section for this event.
    # Look for auto_commit.<event_name>.enabled and .message
    # Also check auto_commit.default as fallback.
    _in_auto_commit=false
    _in_event=false
    _default_enabled=false

    while IFS= read -r _line; do
        # Detect auto_commit: section
        if echo "$_line" | grep -q '^auto_commit:'; then
            _in_auto_commit=true
            _in_event=false
            continue
        fi

        # Exit auto_commit section on next top-level key
        if $_in_auto_commit && echo "$_line" | grep -Eq '^[a-z]'; then
            break
        fi

        if $_in_auto_commit; then
            # Check default key
            if echo "$_line" | grep -Eq "^[[:space:]]+default:[[:space:]]"; then
                _val=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
                [ "$_val" = "true" ] && _default_enabled=true
            fi

            # Detect our event subsection
            if echo "$_line" | grep -Eq "^[[:space:]]+${EVENT_NAME}:"; then
                _in_event=true
                continue
            fi

            # Inside our event subsection
            if $_in_event; then
                # Exit on next sibling key (same indent level as event name)
                if echo "$_line" | grep -Eq '^[[:space:]]{2}[a-z]' && ! echo "$_line" | grep -Eq '^[[:space:]]{4}'; then
                    _in_event=false
                    continue
                fi
                if echo "$_line" | grep -Eq '[[:space:]]+enabled:'; then
                    _val=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
                    [ "$_val" = "true" ] && _enabled=true
                    [ "$_val" = "false" ] && _enabled=false
                fi
                if echo "$_line" | grep -Eq '[[:space:]]+message:'; then
                    # Trim trailing whitespace before stripping the closing quote:
                    # a value like `message: "Done"  ` (trailing spaces after the
                    # quote) would otherwise leave the quote dangling (`Done"  `),
                    # since the closing-quote strip is anchored to end-of-string.
                    # The PowerShell twin .Trim()s first; match it for parity.
                    _commit_msg=$(echo "$_line" | sed 's/^[^:]*:[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed 's/^["'\'']//' | sed 's/["'\'']*$//')
                fi
            fi
        fi
    done < "$_config_file"

    # If event-specific key not found, use default
    if [ "$_enabled" = "false" ] && [ "$_default_enabled" = "true" ]; then
        # Only use default if the event wasn't explicitly set to false
        # Check if event section existed at all
        if ! grep -q "^[[:space:]]*${EVENT_NAME}:" "$_config_file" 2>/dev/null; then
            _enabled=true
        fi
    fi
else
    # No config file — auto-commit disabled by default
    exit 0
fi

if [ "$_enabled" != "true" ]; then
    exit 0
fi

# Check if there are changes to commit
if git diff --quiet HEAD 2>/dev/null && git diff --cached --quiet 2>/dev/null && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    echo "[specify] No changes to commit after $EVENT_NAME" >&2
    exit 0
fi

# In conventional mode, the commit message must be supplied by the agent
# (via the generated_message argument); never fall back to the fixed message.
if [ "$_commit_style" = "conventional" ]; then
    if [ -n "$GENERATED_MESSAGE" ]; then
        _commit_msg="$GENERATED_MESSAGE"
    else
        echo "[specify] Error: commit_style is 'conventional' but no generated commit message was supplied; aborting auto-commit (pass --message-file <path>, or a raw message as arg 2, or set commit_style: fixed)" >&2
        exit 1
    fi
fi

# Derive a human-readable command name from the event
# e.g., after_specify -> specify, before_plan -> plan
_command_name=$(echo "$EVENT_NAME" | sed 's/^after_//' | sed 's/^before_//')
_phase=$(echo "$EVENT_NAME" | grep -q '^before_' && echo 'before' || echo 'after')

# Use custom message if configured, otherwise default
if [ -z "$_commit_msg" ]; then
    _commit_msg="[Spec Kit] Auto-commit ${_phase} ${_command_name}"
fi

# Stage and commit
_git_out=$(git add . 2>&1) || { echo "[specify] Error: git add failed: $_git_out" >&2; exit 1; }
_git_out=$(git commit -q -m "$_commit_msg" 2>&1) || { echo "[specify] Error: git commit failed: $_git_out" >&2; exit 1; }

echo "[OK] Changes committed ${_phase} ${_command_name}" >&2
