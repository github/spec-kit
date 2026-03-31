#!/usr/bin/env bash
# update-context.sh — Copilot integration update-context script
#
# Thin wrapper that delegates to the shared update-agent-context.sh
# with the copilot agent type. Installed by the integration into
# .specify/integrations/copilot/scripts/ and referenced from
# .specify/agent.json so the shared dispatcher can find it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Delegate to the shared update-agent-context script
exec "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh" copilot "$@"
