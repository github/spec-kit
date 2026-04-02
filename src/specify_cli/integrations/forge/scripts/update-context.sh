#!/usr/bin/env bash
# update-context.sh — Forge integration: create/update AGENTS.md
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
# If the shared dispatcher already knows about "forge", delegate to it.
if grep -q 'forge)' "$shared_script" 2>/dev/null; then
  exec "$shared_script" forge
fi

# Forge-specific handling: update or create AGENTS.md directly until the shared
# dispatcher script supports "forge".
agents_file="$REPO_ROOT/AGENTS.md"
if [ -f "$agents_file" ]; then
  # Only add a Forge entry if one does not already exist.
  if ! grep -q '\bForge\b' "$agents_file"; then
    printf '\n## Forge\n- Forge integration agent context\n' >> "$agents_file"
  fi
else
  cat > "$agents_file" << 'EOF'
# Agents

## Forge
- Forge integration agent context
EOF
fi
exit 0
