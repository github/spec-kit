#!/usr/bin/env bash
set -euo pipefail

# simulate-release.sh
# Simulate the release process locally without pushing to GitHub
# Usage: simulate-release.sh [version]
#   If version is omitted, auto-increments patch version

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Simulating Release Process Locally${NC}"
echo "======================================"
echo ""

# Step 1: Determine version
if [[ -n "${1:-}" ]]; then
  VERSION="${1#v}"
  TAG="v$VERSION"
  echo -e "${GREEN}📝 Using manual version: $VERSION${NC}"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
  echo -e "${BLUE}Latest tag: $LATEST_TAG${NC}"
  
  VERSION=$(echo $LATEST_TAG | sed 's/v//')
  IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
  MAJOR=${VERSION_PARTS[0]:-0}
  MINOR=${VERSION_PARTS[1]:-0}
  PATCH=${VERSION_PARTS[2]:-0}
  
  PATCH=$((PATCH + 1))
  VERSION="$MAJOR.$MINOR.$PATCH"
  TAG="v$VERSION"
  echo -e "${GREEN}📝 Auto-incremented to: $VERSION${NC}"
fi

echo ""

# Step 2: Check if tag exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo -e "${RED}❌ Error: Tag $TAG already exists!${NC}"
  echo "   Please use a different version or delete the tag first."
  exit 1
fi
echo -e "${GREEN}✓ Tag $TAG is available${NC}"

# Step 3: Backup current state
echo ""
echo -e "${YELLOW}💾 Creating backup of current state...${NC}"
BACKUP_DIR=$(mktemp -d)
cp pyproject.toml "$BACKUP_DIR/pyproject.toml.bak"
cp CHANGELOG.md "$BACKUP_DIR/CHANGELOG.md.bak"
echo -e "${GREEN}✓ Backup created at: $BACKUP_DIR${NC}"

# Step 4: Update pyproject.toml
echo ""
echo -e "${YELLOW}📝 Updating pyproject.toml...${NC}"
sed -i.tmp "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm -f pyproject.toml.tmp
echo -e "${GREEN}✓ Updated pyproject.toml to version $VERSION${NC}"

# Step 5: Update CHANGELOG.md
echo ""
echo -e "${YELLOW}📝 Updating CHANGELOG.md...${NC}"
DATE=$(date +%Y-%m-%d)

# Get the previous tag to compare commits
PREVIOUS_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$PREVIOUS_TAG" ]]; then
  echo "   Generating changelog from commits since $PREVIOUS_TAG"
  # Get commits since last tag, format as bullet points
  COMMITS=$(git log --oneline "$PREVIOUS_TAG"..HEAD --no-merges --pretty=format:"- %s" 2>/dev/null || echo "- Initial release")
else
  echo "   No previous tag found - this is the first release"
  COMMITS="- Initial release"
fi

# Create temp file with new entry
{
  head -n 8 CHANGELOG.md
  echo ""
  echo "## [$VERSION] - $DATE"
  echo ""
  echo "### Changed"
  echo ""
  echo "$COMMITS"
  echo ""
  tail -n +9 CHANGELOG.md
} > CHANGELOG.md.tmp
mv CHANGELOG.md.tmp CHANGELOG.md
echo -e "${GREEN}✓ Updated CHANGELOG.md with commits since $PREVIOUS_TAG${NC}"

# Step 6: Show what would be committed
echo ""
echo -e "${YELLOW}📋 Changes that would be committed:${NC}"
git diff pyproject.toml CHANGELOG.md

# Step 7: Create temporary tag (no push)
echo ""
echo -e "${YELLOW}🏷️  Creating temporary local tag...${NC}"
git tag -a "$TAG" -m "Simulated release $TAG" 2>/dev/null || true
echo -e "${GREEN}✓ Tag $TAG created locally${NC}"

# Step 8: Simulate release artifact creation
echo ""
echo -e "${YELLOW}📦 Simulating release package creation...${NC}"
echo "   (Running create-release-packages.sh in dry-run mode)"
echo ""

# Check if script exists and is executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$SCRIPT_DIR/create-release-packages.sh" ]]; then
  # Just show what would be created, don't actually create
  echo -e "${BLUE}Packages that would be created:${NC}"
  echo "  - spec-kit-template-copilot-sh-$TAG.zip"
  echo "  - spec-kit-template-copilot-ps-$TAG.zip"
  echo "  - spec-kit-template-claude-sh-$TAG.zip"
  echo "  - spec-kit-template-claude-ps-$TAG.zip"
  echo "  - spec-kit-template-gemini-sh-$TAG.zip"
  echo "  - spec-kit-template-gemini-ps-$TAG.zip"
  echo "  - spec-kit-template-cursor-agent-sh-$TAG.zip"
  echo "  - spec-kit-template-cursor-agent-ps-$TAG.zip"
  echo "  ... (40 total packages)"
else
  echo -e "${RED}⚠️  create-release-packages.sh not found or not executable${NC}"
fi

# Step 9: Simulate release notes generation
echo ""
echo -e "${YELLOW}📄 Simulating release notes generation...${NC}"
echo ""
PREVIOUS_TAG=$(git describe --tags --abbrev=0 $TAG^ 2>/dev/null || echo "")
if [[ -n "$PREVIOUS_TAG" ]]; then
  echo -e "${BLUE}Changes since $PREVIOUS_TAG:${NC}"
  git log --oneline "$PREVIOUS_TAG".."$TAG" | head -n 10
  echo ""
else
  echo -e "${BLUE}No previous tag found - this would be the first release${NC}"
fi

# Step 10: Summary
echo ""
echo -e "${GREEN}🎉 Simulation Complete!${NC}"
echo "======================================"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Version: $VERSION"
echo "  Tag: $TAG"
echo "  Backup: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}⚠️  SIMULATION ONLY - NO CHANGES PUSHED${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Review the changes above"
echo "  2. To keep changes: git add pyproject.toml CHANGELOG.md && git commit"
echo "  3. To discard changes: git checkout pyproject.toml CHANGELOG.md && git tag -d $TAG"
echo "  4. To restore from backup: cp $BACKUP_DIR/* ."
echo ""
echo -e "${BLUE}To run the actual release:${NC}"
echo "  Go to: https://github.com/github/spec-kit/actions/workflows/release-trigger.yml"
echo "  Click 'Run workflow' and enter version: $VERSION"
echo ""
