#!/usr/bin/env bash
#
# Extract translatable strings from source code to POT template file
#
# Usage: ./scripts/i18n/extract-messages.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🌍 Extracting translatable messages..."

# Extract messages using Babel
pybabel extract \
    -F babel.cfg \
    -k _ \
    -k ngettext:1,2 \
    -o src/specify_cli/i18n/messages.pot \
    --add-location=file \
    --msgid-bugs-address="https://github.com/github/spec-kit/issues" \
    --copyright-holder="GitHub" \
    --project="Specify CLI" \
    --version="0.0.23" \
    src/

echo "✅ Extraction complete: src/specify_cli/i18n/messages.pot"
echo ""
echo "Next steps:"
echo "  1. Update existing catalogs: pybabel update -i src/specify_cli/i18n/messages.pot -d src/specify_cli/i18n"
echo "  2. Translate messages in PO files"
echo "  3. Compile: ./scripts/i18n/compile-translations.sh"
