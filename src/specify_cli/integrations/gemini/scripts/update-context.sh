#!/usr/bin/env bash
# update-context.sh — Gemini CLI integration: create/update GEMINI.md
#
# Thin wrapper that delegates to the shared update-agent-context script.
# Activated in Stage 7 when the shared script uses integration.json dispatch.
#
# Until then, this delegates to the shared script as a subprocess.

set -euo pipefail

# Derive repo root from script location (walks up to find .specify/)
_script_dir="$(cd "$(dirname "$0")" && pwd)"
_root="$_script_dir"
while [ "$_root" != "/" ] && [ ! -d "$_root/.specify" ]; do _root="$(dirname "$_root")"; done
if [ -z "${REPO_ROOT:-}" ]; then
  if [ -d "$_root/.specify" ]; then
    REPO_ROOT="$_root"
  else
    git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -n "$git_root" ] && [ -d "$git_root/.specify" ]; then
      REPO_ROOT="$git_root"
    else
      REPO_ROOT="$_root"
    fi
  fi
fi

exec "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh" gemini
