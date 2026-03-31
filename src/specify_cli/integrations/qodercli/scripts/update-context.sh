#!/usr/bin/env bash
# update-context.sh — Qoder CLI integration: create/update QODER.md
#
# Thin wrapper that delegates to the shared update-agent-context script.
# Activated in Stage 7 when the shared script uses integration.json dispatch.
#
# Until then, this delegates to the shared script as a subprocess.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

exec "$REPO_ROOT/.specify/scripts/bash/update-agent-context.sh" qodercli
