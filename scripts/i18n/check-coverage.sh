#!/usr/bin/env bash
#
# Check translation coverage and completeness
#
# Usage: ./scripts/i18n/check-coverage.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "📊 Checking translation coverage..."
echo ""

EXIT_CODE=0

for po_file in src/specify_cli/i18n/*/LC_MESSAGES/specify.po; do
    if [ -f "$po_file" ]; then
        locale=$(basename $(dirname $(dirname "$po_file")))
        echo "Language: $locale"
        echo "File: $po_file"
        
        # Use msgfmt to check statistics
        if msgfmt --statistics --check "$po_file" 2>&1 | tee /tmp/msgfmt_output.txt; then
            # Check for untranslated messages
            if grep -q "untranslated" /tmp/msgfmt_output.txt; then
                echo "❌ FAIL: Translation incomplete"
                EXIT_CODE=1
            else
                echo "✅ PASS: Translation complete"
            fi
        else
            echo "❌ ERROR: Failed to validate PO file"
            EXIT_CODE=1
        fi
        echo ""
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All translations are complete!"
else
    echo "❌ Some translations are incomplete. Please complete them before release."
fi

exit $EXIT_CODE
