#!/usr/bin/env bash
# Prepare fork for upstream sync by checking status and creating backup
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== Spec-Kit Fork Sync Preparation ===${NC}\n"

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

cd "$REPO_ROOT"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}❌ Uncommitted changes detected${NC}"
    echo -e "${YELLOW}Please commit or stash your changes before syncing:${NC}"
    git status -s
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  git add ."
    echo "  git commit -m 'your message'"
    echo "  # OR"
    echo "  git stash push -m 'before sync'"
    exit 1
fi

# Check if upstream remote exists
if ! git remote | grep -q "^upstream$"; then
    echo -e "${YELLOW}⚠️  Upstream remote not configured${NC}"
    echo -e "${CYAN}Adding upstream remote:${NC}"
    git remote add upstream https://github.com/github/spec-kit.git
    echo -e "${GREEN}✅ Upstream remote added${NC}\n"
fi

# Fetch upstream
echo -e "${BLUE}📡 Fetching upstream changes...${NC}"
git fetch upstream --quiet

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}Current branch:${NC} $CURRENT_BRANCH\n"

# Check if we're behind upstream
BEHIND=$(git rev-list --count ${CURRENT_BRANCH}..upstream/main 2>/dev/null || echo "0")
AHEAD=$(git rev-list --count upstream/main..${CURRENT_BRANCH} 2>/dev/null || echo "0")

echo -e "${CYAN}=== Sync Status ===${NC}"
if [ "$BEHIND" -eq 0 ]; then
    echo -e "${GREEN}✅ Up to date with upstream${NC}"
else
    echo -e "${YELLOW}⚠️  Behind upstream by $BEHIND commits${NC}"
fi

if [ "$AHEAD" -gt 0 ]; then
    echo -e "${BLUE}ℹ️  Ahead of upstream by $AHEAD commits (custom changes)${NC}"
fi
echo ""

# Show files modified in both repos
echo -e "${CYAN}=== Files Modified in Both Fork and Upstream ===${NC}"
MODIFIED_FILES=$(git diff upstream/main...${CURRENT_BRANCH} --name-only 2>/dev/null | sort | uniq)
if [ -z "$MODIFIED_FILES" ]; then
    echo -e "${GREEN}No conflicts expected${NC}"
else
    echo -e "${YELLOW}The following files may need manual merge:${NC}"
    echo "$MODIFIED_FILES" | while read -r file; do
        echo "  • $file"
    done
fi
echo ""

# Show upstream commits since last sync
echo -e "${CYAN}=== New Upstream Commits ===${NC}"
LAST_SYNC=$(git log --grep="sync: Merge upstream" --format="%H" -n 1 2>/dev/null)
if [[ -n "$LAST_SYNC" ]]; then
    echo -e "${BLUE}Since last sync ($LAST_SYNC):${NC}"
    git log --oneline --no-merges ${LAST_SYNC}..upstream/main 2>/dev/null || echo "No new commits"
else
    echo -e "${YELLOW}No previous sync found. Showing recent upstream commits:${NC}"
    git log --oneline --no-merges upstream/main -10 2>/dev/null || echo "Unable to retrieve commits"
fi
echo ""

# Create backup branch
BACKUP_BRANCH="backup-${CURRENT_BRANCH}-$(date +%Y%m%d-%H%M%S)"
echo -e "${BLUE}💾 Creating backup branch:${NC} $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✅ Backup created${NC}\n"

# Check protected files that should use --ours during merge
echo -e "${CYAN}=== Protected Custom Files (will use --ours) ===${NC}"
PROTECTED_FILES=(
    ".claude/CLAUDE.md"
    "FORK_CUSTOMIZATIONS.md"
    "scripts/prepare-sync.sh"
)

for file in "${PROTECTED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  • $file"
    fi
done
echo ""

# Show recommended next steps
echo -e "${GREEN}✅ Ready to sync${NC}\n"
echo -e "${CYAN}=== Next Steps ===${NC}"
echo ""
echo -e "${YELLOW}1. Create sync branch:${NC}"
echo "   git checkout -b sync-upstream-$(date +%Y%m%d)"
echo ""
echo -e "${YELLOW}2. Merge upstream (don't commit yet):${NC}"
echo "   git merge upstream/main --no-commit --no-ff"
echo ""
echo -e "${YELLOW}3. Protect custom files:${NC}"
for file in "${PROTECTED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   git checkout --ours $file"
    fi
done
echo ""
echo -e "${YELLOW}4. Review conflicts:${NC}"
echo "   git status | grep 'both modified'"
echo ""
echo -e "${YELLOW}5. Test the merge:${NC}"
echo "   bash scripts/bash/check-prerequisites.sh --json"
echo "   uvx --from . specify init test-sync --ai claude"
echo ""
echo -e "${YELLOW}6. Complete the merge:${NC}"
echo "   git add ."
echo "   git commit -m \"sync: Merge upstream changes from github/spec-kit (\$(git rev-parse --short upstream/main))\""
echo ""
echo -e "${YELLOW}7. Merge into main branch:${NC}"
echo "   git checkout ${CURRENT_BRANCH}"
echo "   git merge sync-upstream-$(date +%Y%m%d) --no-ff"
echo ""
echo -e "${YELLOW}8. Push to origin:${NC}"
echo "   git push origin ${CURRENT_BRANCH}"
echo ""
echo -e "${YELLOW}9. Update FORK_CUSTOMIZATIONS.md with sync details${NC}"
echo ""
echo -e "${CYAN}=== Emergency Recovery ===${NC}"
echo -e "${RED}If sync goes wrong:${NC}"
echo "   git merge --abort  # or git rebase --abort"
echo "   git checkout ${CURRENT_BRANCH}"
echo "   git reset --hard ${BACKUP_BRANCH}"
echo ""
