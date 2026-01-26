#!/usr/bin/env bash
#
# Compile PO translation files to MO binary files
#
# Usage: ./scripts/i18n/compile-translations.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🔨 Compiling translations..."

# Compile all PO files to MO files
pybabel compile \
    -d src/specify_cli/i18n \
    --statistics

echo ""
echo "✅ Compilation complete"
echo ""
echo "Test translations:"
echo "  SPECIFY_LANG=zh_CN python -m specify_cli --help"
