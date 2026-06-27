#!/usr/bin/env bash
# Spec Kit plugin lifecycle hook.
#
# Fires (via the Claude hooks.json UserPromptExpansion matcher "speckit") just
# before a `/speckit:*` command expands. When the speckit skills are installed
# globally as a plugin, the per-project `.specify/` runtime state may be absent —
# this hook provisions it on first use so the command's scripts and templates
# resolve. Idempotent, never blocks the command.
#
# Cross-agent routing is adg's responsibility: adg references this same file for
# each runtime it supports (and lints events a target can't fire). We author one
# base hook in Claude's native format and leave platform mapping to adg.

set -u

INPUT="$(cat 2>/dev/null || true)"

# `cwd` is provided in the hook payload; fall back to the process cwd.
CWD=""
if command -v jq >/dev/null 2>&1; then
    CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)"
fi
[ -z "$CWD" ] && CWD="$PWD"

# Idempotent: an initialized speckit project has this sentinel.
if [ -f "$CWD/.specify/init-options.json" ]; then
    exit 0
fi

cd "$CWD" 2>/dev/null || exit 0

if command -v specify >/dev/null 2>&1; then
    if ! specify init --here --plugin --force >/dev/null 2>&1; then
        echo "Spec Kit: could not provision .specify/. Run: specify init --here --plugin" >&2
    fi
else
    echo "Spec Kit: '.specify/' is missing and the 'specify' CLI was not found." >&2
    echo "Install spec-kit, then run: specify init --here --plugin" >&2
fi

# Always allow the command to proceed; the hook only prepares the environment.
exit 0
