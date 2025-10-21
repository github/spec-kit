#!/usr/bin/env bash
set -euo pipefail

# validate-docs-sync.sh
# CI script to validate that documentation is in sync with AGENT_CONFIG
# This should be run in CI to catch documentation drift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "🔍 Validating documentation sync..."
echo "Repository: $REPO_ROOT"
echo ""

# Run the doc generator check
if ! python3 "$REPO_ROOT/scripts/generate-docs.py" --check; then
    echo ""
    echo "❌ Documentation is out of sync with AGENT_CONFIG"
    echo ""
    echo "To fix this issue, run:"
    echo "  python scripts/generate-docs.py --update"
    echo ""
    echo "Then commit the changes:"
    echo "  git add README.md .github/workflows/scripts/create-github-release.sh"
    echo "  git commit -m 'chore: sync documentation with AGENT_CONFIG'"
    exit 1
fi

# Run the release script check
echo ""
echo "🔍 Validating release script..."
if ! python3 "$REPO_ROOT/scripts/generate-release-script.py" --check; then
    echo ""
    echo "❌ Release script is out of sync with AGENT_CONFIG"
    echo ""
    echo "To fix this issue, run:"
    echo "  python scripts/generate-release-script.py --update"
    echo ""
    echo "Then commit the changes:"
    echo "  git add .github/workflows/scripts/create-github-release.sh"
    echo "  git commit -m 'chore: update release script from AGENT_CONFIG'"
    exit 1
fi

echo ""
echo "✅ All documentation is in sync!"
echo ""

# Show current agent count
AGENT_COUNT=$(python3 -c "
import ast
import sys

# Read the AGENT_CONFIG directly from the source file
with open('$REPO_ROOT/src/specify_cli/__init__.py', 'r') as f:
    content = f.read()

# Parse the AST to find AGENT_CONFIG
tree = ast.parse(content)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'AGENT_CONFIG':
                if isinstance(node.value, ast.Dict):
                    print(len(node.value.keys))
                    sys.exit(0)

print('0')  # fallback
")

echo "📊 Current status:"
echo "  - Supported agents: $AGENT_COUNT"
echo "  - Release assets: $((AGENT_COUNT * 2)) (2 per agent)"
echo ""

exit 0
