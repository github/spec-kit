#!/usr/bin/env bash
# Verification script for SpecKit Memory installation
# Usage: bash scripts/memory/verify_install.sh

set -e

echo "=== SpecKit Memory Installation Verification ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Global home
GLOBAL_HOME="$HOME/.claude"
SPECKIT_LINK="$GLOBAL_HOME/spec-kit"
MEMORY_DIR="$GLOBAL_HOME/memory/projects"

# Check results
CHECKS_PASSED=0
CHECKS_TOTAL=0

check_item() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

echo "Checking installation..."
echo ""

# 1. Global home directory
if [ -d "$GLOBAL_HOME" ]; then
    check_item 0 "Global home exists: $GLOBAL_HOME"
else
    check_item 1 "Global home missing: $GLOBAL_HOME"
fi

# 2. SpecKit link
if [ -e "$SPECKIT_LINK" ]; then
    # Check if it's a symlink or junction
    if [ -L "$SPECKIT_LINK" ] || [ -d "$SPECKIT_LINK" ]; then
        check_item 0 "SpecKit link exists: $SPECKIT_LINK"
    else
        check_item 1 "SpecKit link broken: $SPECKIT_LINK"
    fi
else
    check_item 1 "SpecKit link missing: $SPECKIT_LINK"
fi

# 3. Memory directories
if [ -d "$MEMORY_DIR" ]; then
    check_item 0 "Memory directory exists: $MEMORY_DIR"
else
    check_item 1 "Memory directory missing: $MEMORY_DIR"
fi

# 4. Templates
if [ -f "$GLOBAL_HOME/spec-kit/templates/memory/lessons.md" ]; then
    check_item 0 "Templates installed (lessons.md found)"
else
    check_item 1 "Templates missing (lessons.md not found)"
fi

# 5. Config system
if [ -f "$GLOBAL_HOME/spec-kit/config/.version" ] || \
   [ -d "$GLOBAL_HOME/spec-kit/config" ]; then
    check_item 0 "Config system initialized"
else
    check_item 1 "Config system not initialized"
fi

echo ""
echo "=== Verification Summary ==="
echo "Passed: $CHECKS_PASSED/$CHECKS_TOTAL checks"

if [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo -e "${GREEN}Installation verified successfully!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some checks failed. See details above.${NC}"
    exit 1
fi
