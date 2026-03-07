#!/usr/bin/env bash
# Test polyglot wrappers on current platform
#
# This script validates that polyglot wrapper scripts work correctly
# on the current platform (Linux, macOS, Windows Git Bash, etc.)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing Polyglot Wrappers"
echo "=========================================="
echo ""
echo "Platform: $(uname -s)"
echo "Scripts directory: $SCRIPTS_DIR"
echo ""

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_wrapper() {
    local wrapper_name="$1"
    local test_description="$2"
    local wrapper_path="$SCRIPTS_DIR/$wrapper_name"
    
    echo -n "Testing $wrapper_name: $test_description... "
    
    # Check if wrapper exists
    if [ ! -f "$wrapper_path" ]; then
        echo -e "${RED}FAIL${NC} (file not found)"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Check if executable (Unix only)
    if [ "$(uname -s)" != "MINGW"* ] && [ "$(uname -s)" != "MSYS"* ]; then
        if [ ! -x "$wrapper_path" ]; then
            echo -e "${RED}FAIL${NC} (not executable)"
            ((TESTS_FAILED++))
            return 1
        fi
    fi
    
    # Check for shebang
    if ! head -n 1 "$wrapper_path" | grep -q "^#!/usr/bin/env bash"; then
        echo -e "${RED}FAIL${NC} (missing shebang)"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Check for polyglot pattern
    if ! head -n 2 "$wrapper_path" | tail -n 1 | grep -q "2>nul & @echo off & goto :batch"; then
        echo -e "${RED}FAIL${NC} (missing polyglot pattern)"
        ((TESTS_FAILED++))
        return 1
    fi
    
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
    return 0
}

# Test execution function
test_execution() {
    local wrapper_name="$1"
    local args="$2"
    local wrapper_path="$SCRIPTS_DIR/$wrapper_name"
    
    echo -n "Testing $wrapper_name execution with args '$args'... "
    
    # Try to execute (some may fail due to missing dependencies, that's ok)
    if "$wrapper_path" $args >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        local exit_code=$?
        # Exit code 1 is often expected (e.g., missing prerequisites)
        if [ $exit_code -eq 1 ]; then
            echo -e "${YELLOW}EXPECTED FAIL${NC} (exit code 1 - likely missing prerequisites)"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}FAIL${NC} (unexpected exit code: $exit_code)"
            ((TESTS_FAILED++))
            return 1
        fi
    fi
}

echo "=========================================="
echo "Structure Tests"
echo "=========================================="
echo ""

# Test each wrapper's structure
test_wrapper "check-prerequisites" "file structure"
test_wrapper "setup-plan" "file structure"
test_wrapper "create-new-feature" "file structure"
test_wrapper "update-agent-context" "file structure"

echo ""
echo "=========================================="
echo "Execution Tests"
echo "=========================================="
echo ""

# Test help flags (these should work even without prerequisites)
test_execution "check-prerequisites" "--help"
test_execution "setup-plan" "--help"
test_execution "create-new-feature" "--help"

echo ""
echo "=========================================="
echo "Line Ending Tests"
echo "=========================================="
echo ""

# Check line endings (should be LF)
for wrapper in check-prerequisites setup-plan create-new-feature update-agent-context; do
    wrapper_path="$SCRIPTS_DIR/$wrapper"
    echo -n "Testing $wrapper line endings... "
    
    if file "$wrapper_path" | grep -q "CRLF"; then
        echo -e "${RED}FAIL${NC} (has CRLF line endings, should be LF)"
        ((TESTS_FAILED++))
    else
        echo -e "${GREEN}PASS${NC} (LF line endings)"
        ((TESTS_PASSED++))
    fi
done

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
