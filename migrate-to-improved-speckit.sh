#!/usr/bin/env bash
#
# Spec-Kit Migration Script
# Upgrades existing spec-kit project to include Phases 1-5 improvements
#
# Usage: ./migrate-to-improved-speckit.sh [SOURCE_SPECKIT_DIR]
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Spec-Kit Migration to Improved Version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if we're in a spec-kit project
if [ ! -d "specs" ] || [ ! -d "templates" ]; then
    echo -e "${RED}Error: This doesn't appear to be a spec-kit project${NC}"
    echo "Please run this script from your spec-kit project root directory."
    exit 1
fi

# Get source spec-kit directory
SOURCE_DIR="$1"

if [ -z "$SOURCE_DIR" ]; then
    echo -e "${YELLOW}No source directory provided.${NC}"
    echo ""
    echo "Options:"
    echo "  1. Clone improved spec-kit to /tmp and use it"
    echo "  2. Provide path to existing improved spec-kit clone"
    echo ""
    read -p "Enter option [1 or 2]: " option

    if [ "$option" = "1" ]; then
        echo ""
        echo -e "${BLUE}Cloning improved spec-kit...${NC}"
        SOURCE_DIR="/tmp/spec-kit-improved-$$"
        git clone https://github.com/guisantossi/spec-kit.git "$SOURCE_DIR"
        cd "$SOURCE_DIR"
        git checkout claude/improve-s-feature-011CUtKowzjCGGTB49vfnCEm
        cd - > /dev/null
        echo -e "${GREEN}✓ Cloned to $SOURCE_DIR${NC}"
    else
        read -p "Enter path to improved spec-kit: " SOURCE_DIR
    fi
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}Error: Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

if [ ! -f "$SOURCE_DIR/scripts/bash/token-budget.sh" ]; then
    echo -e "${RED}Error: Source doesn't appear to be improved spec-kit${NC}"
    echo "Missing: scripts/bash/token-budget.sh"
    exit 1
fi

PROJECT_DIR="$(pwd)"
BACKUP_DIR="$PROJECT_DIR/.speckit-backup-$(date +%Y%m%d-%H%M%S)"

echo ""
echo "Source: $SOURCE_DIR"
echo "Target: $PROJECT_DIR"
echo "Backup: $BACKUP_DIR"
echo ""

read -p "Proceed with migration? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Creating backup...${NC}"
mkdir -p "$BACKUP_DIR"

# Backup critical files
[ -f "memory/constitution.md" ] && cp "memory/constitution.md" "$BACKUP_DIR/"
[ -d "templates/commands" ] && cp -r "templates/commands" "$BACKUP_DIR/"
[ -f ".gitignore" ] && cp ".gitignore" "$BACKUP_DIR/"

echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"

echo ""
echo -e "${BLUE}Step 2: Copying new bash scripts...${NC}"
mkdir -p scripts/bash

# Copy all Phase 1-5 bash scripts
cp "$SOURCE_DIR/scripts/bash/token-budget.sh" scripts/bash/
cp "$SOURCE_DIR/scripts/bash/validate-spec.sh" scripts/bash/
cp "$SOURCE_DIR/scripts/bash/semantic-search.sh" scripts/bash/
cp "$SOURCE_DIR/scripts/bash/session-prune.sh" scripts/bash/
cp "$SOURCE_DIR/scripts/bash/error-analysis.sh" scripts/bash/
cp "$SOURCE_DIR/scripts/bash/clarify-history.sh" scripts/bash/

# Update existing scripts if they exist
[ -f "$SOURCE_DIR/scripts/bash/setup-ai-doc.sh" ] && cp "$SOURCE_DIR/scripts/bash/setup-ai-doc.sh" scripts/bash/
[ -f "$SOURCE_DIR/scripts/bash/project-analysis.sh" ] && cp "$SOURCE_DIR/scripts/bash/project-analysis.sh" scripts/bash/

# Make executable
chmod +x scripts/bash/*.sh

echo -e "${GREEN}✓ Bash scripts copied and made executable${NC}"

echo ""
echo -e "${BLUE}Step 3: Copying PowerShell scripts...${NC}"
mkdir -p scripts/powershell

# Copy all PowerShell scripts
cp "$SOURCE_DIR/scripts/powershell"/*.ps1 scripts/powershell/ 2>/dev/null || echo "  (Some PowerShell scripts may not exist in source)"

echo -e "${GREEN}✓ PowerShell scripts copied${NC}"

echo ""
echo -e "${BLUE}Step 4: Copying new command templates...${NC}"
mkdir -p templates/commands

# Copy new command templates
cp "$SOURCE_DIR/templates/commands/budget.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/validate.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/find.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/prune.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/error-context.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/clarify-history.md" templates/commands/
cp "$SOURCE_DIR/templates/commands/resume.md" templates/commands/

# Update existing templates if they changed
[ -f "$SOURCE_DIR/templates/commands/document.md" ] && cp "$SOURCE_DIR/templates/commands/document.md" templates/commands/

# Copy quick-ref template
cp "$SOURCE_DIR/templates/quick-ref-template.md" templates/

echo -e "${GREEN}✓ Command templates copied${NC}"

echo ""
echo -e "${BLUE}Step 5: Copying Git hooks...${NC}"
mkdir -p hooks

cp -r "$SOURCE_DIR/hooks"/* hooks/
chmod +x hooks/pre-commit 2>/dev/null || true

echo -e "${GREEN}✓ Git hooks copied${NC}"

echo ""
echo -e "${BLUE}Step 6: Copying documentation...${NC}"

cp "$SOURCE_DIR/PLATFORM-COMPATIBILITY.md" .
[ -f "$SOURCE_DIR/IMPROVED-WORKFLOW.md" ] && cp "$SOURCE_DIR/IMPROVED-WORKFLOW.md" .

echo -e "${GREEN}✓ Documentation copied${NC}"

echo ""
echo -e "${BLUE}Step 7: Updating .gitignore...${NC}"

# Check if gitignore already has spec-kit entries
if ! grep -q ".speckit-cache" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# Spec-kit Phase 1-5 additions
.speckit-cache/
.speckit-analysis-cache.json
.speckit-progress.json
.speckit/memory/session-summary-*.md
.speckit.config.json
EOF
    echo -e "${GREEN}✓ .gitignore updated${NC}"
else
    echo -e "${YELLOW}  .gitignore already contains spec-kit entries (skipped)${NC}"
fi

echo ""
echo -e "${BLUE}Step 8: Creating sample config...${NC}"

if [ ! -f ".speckit.config.json" ]; then
    [ -f "$SOURCE_DIR/.speckit.config.json.example" ] && cp "$SOURCE_DIR/.speckit.config.json.example" .
    echo -e "${GREEN}✓ Sample config created (.speckit.config.json.example)${NC}"
else
    echo -e "${YELLOW}  .speckit.config.json already exists (skipped)${NC}"
fi

echo ""
echo -e "${BLUE}Step 9: Installing Git pre-commit hook...${NC}"

if [ -d ".git" ]; then
    read -p "Install Git pre-commit hook? [y/N]: " install_hook
    if [[ "$install_hook" =~ ^[Yy]$ ]]; then
        if [ -f ".git/hooks/pre-commit" ]; then
            echo -e "${YELLOW}  Backing up existing pre-commit hook${NC}"
            cp .git/hooks/pre-commit "$BACKUP_DIR/pre-commit.old"
        fi

        # Try symlink first
        if ln -sf ../../hooks/pre-commit .git/hooks/pre-commit 2>/dev/null; then
            echo -e "${GREEN}✓ Pre-commit hook installed (symlink)${NC}"
        else
            # Fallback to copy
            cp hooks/pre-commit .git/hooks/pre-commit
            chmod +x .git/hooks/pre-commit
            echo -e "${GREEN}✓ Pre-commit hook installed (copy)${NC}"
        fi
    else
        echo -e "${YELLOW}  Skipped (you can install later with: ln -s ../../hooks/pre-commit .git/hooks/pre-commit)${NC}"
    fi
else
    echo -e "${YELLOW}  Not a git repository (skipped)${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Migration Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "New features available:"
echo "  /speckit.budget              - Track token usage"
echo "  /speckit.validate --all      - Validate all specs"
echo "  /speckit.find \"query\"        - Semantic code search"
echo "  /speckit.prune               - Compress session context"
echo "  /speckit.error-context       - AI-assisted error debugging"
echo "  /speckit.clarify-history     - View clarification decisions"
echo ""
echo "Enhanced features:"
echo "  /speckit.project-analysis --diff-only      - 80-95% faster"
echo "  /speckit.project-analysis --incremental    - 70-90% faster"
echo "  /speckit.document                          - Now generates quick-ref.md"
echo ""
echo "Quick verification:"
echo "  ./scripts/bash/token-budget.sh"
echo "  ./scripts/bash/validate-spec.sh --all"
echo ""
echo "Documentation:"
echo "  cat PLATFORM-COMPATIBILITY.md    - Cross-platform usage guide"
echo "  cat IMPROVED-WORKFLOW.md          - New workflow examples"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test new features: ./scripts/bash/token-budget.sh"
echo "  2. Validate your specs: ./scripts/bash/validate-spec.sh --all"
echo "  3. Review documentation: cat PLATFORM-COMPATIBILITY.md"
echo "  4. Commit changes: git add -A && git commit -m 'Upgrade to improved spec-kit'"
echo ""
echo "Happy coding! 🚀"
