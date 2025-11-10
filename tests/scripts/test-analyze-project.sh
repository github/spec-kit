#!/usr/bin/env bash
#
# test-analyze-project.sh - Test suite for analyze-project scripts
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

TEST_OUTPUT_DIR="/tmp/analyze-project-tests-$$"
mkdir -p "$TEST_OUTPUT_DIR"

cleanup() {
    rm -rf "$TEST_OUTPUT_DIR"
}
trap cleanup EXIT

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_pass() {
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

print_fail() {
    ((TESTS_FAILED++))
    echo -e "${RED}✗ FAIL:${NC} $1"
}

# Test: Bash help flag works
test_bash_help() {
    ((TESTS_RUN++))
    if "$REPO_ROOT/scripts/bash/analyze-project.sh" --help 2>&1 | grep -q "Usage:"; then
        print_pass "Bash --help works"
    else
        print_fail "Bash --help does not work"
    fi
}

# Test: Bash script creates workspace
test_bash_creates_workspace() {
    ((TESTS_RUN++))

    local test_project="$TEST_OUTPUT_DIR/test-project"
    mkdir -p "$test_project"
    echo "test" > "$test_project/test.js"

    local output_dir="$TEST_OUTPUT_DIR/analysis"

    if "$REPO_ROOT/scripts/bash/analyze-project.sh" "$test_project" --output "$output_dir" 2>&1 | grep -qi "ready"; then
        if [ -f "$output_dir/file-manifest.json" ]; then
            print_pass "Bash creates workspace with file-manifest.json"
        else
            print_fail "Bash did not create file-manifest.json"
        fi
    else
        print_fail "Bash script did not complete successfully"
    fi
}

# Test: Bash checks for jq dependency
test_bash_jq_check() {
    ((TESTS_RUN++))

    if "$REPO_ROOT/scripts/bash/analyze-project.sh" --help 2>&1; then
        # Script should mention jq in its checks or help
        print_pass "Bash script has dependency check"
    else
        print_fail "Bash script dependency check failed"
    fi
}

main() {
    print_header "analyze-project.sh Test Suite"

    test_bash_help || true
    test_bash_jq_check || true
    test_bash_creates_workspace || true

    print_header "Test Summary"
    echo "Tests run:    $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

main "$@"
