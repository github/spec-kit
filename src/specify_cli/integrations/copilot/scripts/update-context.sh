#!/usr/bin/env bash
# update-context.sh — Copilot integration: create/update .github/copilot-instructions.md
#
# This is the copilot-specific implementation that produces the GitHub
# Copilot instructions file. The shared dispatcher reads
# .specify/integration.json and calls this script.
#
# NOTE: This script is not yet active. It will be activated in Stage 7
# when the shared update-agent-context.sh replaces its case statement
# with integration.json-based dispatch. The shared script must also be
# refactored to support SPECKIT_SOURCE_ONLY (guard the main logic)
# before sourcing will work.
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

# Invoke shared update-agent-context script as a separate process.
# Sourcing is unsafe until that script guards its main logic.
exec "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh" copilot
