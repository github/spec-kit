#!/bin/bash
# init-researchkit.sh - Initialize ResearchKit in current directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCHKIT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔬 Initializing ResearchKit..."
echo ""

# Check if we're already initialized
if [ -d "projects" ]; then
    echo "⚠️  ResearchKit appears to already be initialized (projects/ directory exists)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

# Create projects directory
echo "📁 Creating projects directory..."
mkdir -p projects

# Create a .researchkit marker file
echo "📝 Creating .researchkit configuration..."
cat > .researchkit <<EOF
# ResearchKit Configuration
# This file marks this directory as a ResearchKit workspace

researchkit_version=1.0.0
initialized=$(date +%Y-%m-%d)
EOF

# Create .gitignore for projects if it doesn't exist
if [ ! -f "projects/.gitignore" ]; then
    echo "🔒 Creating projects/.gitignore..."
    cat > projects/.gitignore <<EOF
# ResearchKit - Ignore downloaded documents by default
# (they're often large PDFs and may have licensing restrictions)

*/documents/foundational/*.pdf
*/documents/recent-reviews/*.pdf
*/documents/supplementary/*.pdf

# But keep the download queue tracking file
!*/documents/download-queue.md

# Keep directory structure
!*/documents/foundational/.gitkeep
!*/documents/recent-reviews/.gitkeep
!*/documents/supplementary/.gitkeep

# Allow markdown exports of PDFs
!*.md
!*.txt

# You can override these in specific projects by:
# 1. Using git add -f path/to/specific.pdf
# 2. Or modifying this .gitignore
EOF
fi

echo ""
echo "✅ ResearchKit initialized!"
echo ""
echo "Next steps:"
echo "  1. Create your first project: ./researchkit/scripts/new-project.sh 'project-name'"
echo "  2. Or use: /rk.constitution to start defining research principles"
echo ""
echo "Available commands:"
echo "  /rk.constitution       - Create/update research constitution"
echo "  /rk.question          - Define research question"
echo "  /rk.capture-story     - Capture vivid story/anecdote"
echo ""
echo "Documentation: researchkit/docs/"
echo ""
