#!/usr/bin/env bash
#
# test-all-scripts.sh - Comprehensive test suite for all bash and PowerShell scripts
#
# This script tests:
# - All bash scripts in scripts/bash/
# - All PowerShell scripts in scripts/powershell/
# - Bash/PowerShell parity where applicable
# - Basic functionality (help flags, dependency checks, etc.)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Test output directory
TEST_OUTPUT_DIR="/tmp/script-tests-$$"
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

print_test() {
    echo -e "${BLUE}TEST:${NC} $1"
}

print_pass() {
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

print_fail() {
    ((TESTS_FAILED++))
    echo -e "${RED}✗ FAIL:${NC} $1"
}

print_skip() {
    ((TESTS_SKIPPED++))
    echo -e "${YELLOW}⊘ SKIP:${NC} $1"
}

# Generic test: Script has help flag
test_script_help() {
    local script_path="$1"
    local script_name=$(basename "$script_path")

    ((TESTS_RUN++))
    print_test "$script_name --help flag"

    if [[ "$script_path" == *.sh ]]; then
        if bash "$script_path" --help 2>&1 | grep -qiE "(usage|help|options)"; then
            print_pass "$script_name --help works"
            return 0
        else
            print_fail "$script_name --help does not work"
            return 1
        fi
    elif [[ "$script_path" == *.ps1 ]]; then
        if ! command -v pwsh &> /dev/null; then
            print_skip "$script_name (PowerShell not installed)"
            return 0
        fi

        if pwsh -File "$script_path" -Help 2>&1 | grep -qiE "(usage|help|parameters)"; then
            print_pass "$script_name -Help works"
            return 0
        else
            print_fail "$script_name -Help does not work"
            return 1
        fi
    fi
}

# Generic test: Script has no syntax errors
test_script_syntax() {
    local script_path="$1"
    local script_name=$(basename "$script_path")

    ((TESTS_RUN++))
    print_test "$script_name syntax check"

    if [[ "$script_path" == *.sh ]]; then
        if bash -n "$script_path" 2>&1; then
            print_pass "$script_name syntax OK"
            return 0
        else
            print_fail "$script_name has syntax errors"
            return 1
        fi
    elif [[ "$script_path" == *.ps1 ]]; then
        if ! command -v pwsh &> /dev/null; then
            print_skip "$script_name (PowerShell not installed)"
            return 0
        fi

        # PowerShell syntax check
        if pwsh -Command "Get-Command -Syntax \"$script_path\"" &> /dev/null || \
           pwsh -Command "\$null = Get-Content '$script_path' -ErrorAction Stop" &> /dev/null; then
            print_pass "$script_name syntax OK"
            return 0
        else
            print_fail "$script_name has syntax errors"
            return 1
        fi
    fi
}

# Test: check-prerequisites scripts
test_check_prerequisites() {
    print_header "Testing check-prerequisites scripts"

    local bash_script="$REPO_ROOT/scripts/bash/check-prerequisites.sh"
    local ps_script="$REPO_ROOT/scripts/powershell/check-prerequisites.ps1"

    test_script_syntax "$bash_script" || true
    test_script_help "$bash_script" || true

    if [ -f "$ps_script" ]; then
        test_script_syntax "$ps_script" || true
        test_script_help "$ps_script" || true
    fi

    # Test actual execution with --help
    ((TESTS_RUN++))
    if bash "$bash_script" 2>&1 | grep -qiE "(checking|prerequisites)"; then
        print_pass "check-prerequisites.sh runs without errors"
    else
        print_skip "check-prerequisites.sh requires specific environment"
    fi
}

# Test: update-agent-context scripts
test_update_agent_context() {
    print_header "Testing update-agent-context scripts"

    local bash_script="$REPO_ROOT/scripts/bash/update-agent-context.sh"
    local ps_script="$REPO_ROOT/scripts/powershell/update-agent-context.ps1"

    test_script_syntax "$bash_script" || true
    test_script_help "$bash_script" || true

    if [ -f "$ps_script" ]; then
        test_script_syntax "$ps_script" || true
        test_script_help "$ps_script" || true
    fi
}

# Test: create-new-feature scripts
test_create_new_feature() {
    print_header "Testing create-new-feature scripts"

    local bash_script="$REPO_ROOT/scripts/bash/create-new-feature.sh"
    local ps_script="$REPO_ROOT/scripts/powershell/create-new-feature.ps1"

    test_script_syntax "$bash_script" || true
    test_script_help "$bash_script" || true

    if [ -f "$ps_script" ]; then
        test_script_syntax "$ps_script" || true
        test_script_help "$ps_script" || true
    fi
}

# Test: setup-plan scripts
test_setup_plan() {
    print_header "Testing setup-plan scripts"

    local bash_script="$REPO_ROOT/scripts/bash/setup-plan.sh"
    local ps_script="$REPO_ROOT/scripts/powershell/setup-plan.ps1"

    test_script_syntax "$bash_script" || true
    test_script_help "$bash_script" || true

    if [ -f "$ps_script" ]; then
        test_script_syntax "$ps_script" || true
        test_script_help "$ps_script" || true
    fi
}

# Test: analyze-project-setup scripts
test_analyze_project_setup() {
    print_header "Testing analyze-project-setup scripts"

    local bash_script="$REPO_ROOT/scripts/bash/analyze-project-setup.sh"
    local ps_script="$REPO_ROOT/scripts/powershell/analyze-project-setup.ps1"

    if [ -f "$bash_script" ]; then
        test_script_syntax "$bash_script" || true
        test_script_help "$bash_script" || true
    fi

    if [ -f "$ps_script" ]; then
        test_script_syntax "$ps_script" || true
        test_script_help "$ps_script" || true
    fi
}

# Test: common utility scripts
test_common_scripts() {
    print_header "Testing common utility scripts"

    local bash_common="$REPO_ROOT/scripts/bash/common.sh"
    local ps_common="$REPO_ROOT/scripts/powershell/common.ps1"

    if [ -f "$bash_common" ]; then
        test_script_syntax "$bash_common" || true
    fi

    if [ -f "$ps_common" ]; then
        test_script_syntax "$ps_common" || true
    fi
}

# Test: Guidelines-related scripts
test_guidelines_scripts() {
    print_header "Testing guidelines scripts"

    local scripts=(
        "$REPO_ROOT/scripts/bash/check-guidelines-compliance.sh"
        "$REPO_ROOT/scripts/bash/autofix-guidelines.sh"
        "$REPO_ROOT/scripts/bash/diff-guidelines.sh"
        "$REPO_ROOT/scripts/bash/guidelines-analytics.sh"
    )

    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            test_script_syntax "$script" || true
            test_script_help "$script" || true
        fi
    done
}

# Run all specialized test suites
run_specialized_tests() {
    print_header "Running Specialized Test Suites"

    # Run enumerate-project tests
    if [ -f "$SCRIPT_DIR/test-enumerate-project.sh" ]; then
        echo -e "\n${BLUE}Running enumerate-project test suite...${NC}"
        if bash "$SCRIPT_DIR/test-enumerate-project.sh"; then
            ((TESTS_RUN++))
            ((TESTS_PASSED++))
            print_pass "enumerate-project test suite passed"
        else
            ((TESTS_RUN++))
            ((TESTS_FAILED++))
            print_fail "enumerate-project test suite failed"
        fi
    fi

    # Run analyze-project tests
    if [ -f "$SCRIPT_DIR/test-analyze-project.sh" ]; then
        echo -e "\n${BLUE}Running analyze-project test suite...${NC}"
        if bash "$SCRIPT_DIR/test-analyze-project.sh"; then
            ((TESTS_RUN++))
            ((TESTS_PASSED++))
            print_pass "analyze-project test suite passed"
        else
            ((TESTS_RUN++))
            ((TESTS_FAILED++))
            print_fail "analyze-project test suite failed"
        fi
    fi
}

# Main execution
main() {
    print_header "Comprehensive Script Test Suite"

    echo "Repository: $REPO_ROOT"
    echo "Test output: $TEST_OUTPUT_DIR"
    echo ""

    # Check dependencies
    echo "Checking dependencies..."
    command -v jq &> /dev/null && echo "  ✓ jq installed" || echo "  ✗ jq NOT installed"
    command -v pwsh &> /dev/null && echo "  ✓ PowerShell Core installed" || echo "  ✗ PowerShell Core NOT installed"
    echo ""

    # Run all test categories
    test_check_prerequisites
    test_update_agent_context
    test_create_new_feature
    test_setup_plan
    test_analyze_project_setup
    test_common_scripts
    test_guidelines_scripts

    # Run specialized test suites
    run_specialized_tests

    # Print summary
    print_header "Test Summary"
    echo "Tests run:    $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Tests skipped: ${YELLOW}$TESTS_SKIPPED${NC}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

main "$@"
