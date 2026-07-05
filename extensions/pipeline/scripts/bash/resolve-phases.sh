#!/usr/bin/env bash
# Thin POSIX wrapper: resolve the Spec Kit pipeline phase plan.
# Delegates to the pure-Python resolver so there is one source of truth.
# Usage: resolve-phases.sh [--skip a,b] [--add x,y] [--json|--list]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${HERE}/../resolve_phases.py" "$@"
