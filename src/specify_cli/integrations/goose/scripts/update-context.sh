#!/usr/bin/env bash
# update-context.sh — Goose integration: create/update AGENTS.md
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

shared_script="$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh"

# Always delegate to the shared updater; fail clearly if it is unavailable.
if [ ! -x "$shared_script" ]; then
  echo "Error: shared agent context updater not found or not executable:" >&2
  echo "  $shared_script" >&2
  echo "Goose integration requires support in scripts/bash/update-agent-context.sh." >&2
  exit 1
fi

exec "$shared_script" goose
