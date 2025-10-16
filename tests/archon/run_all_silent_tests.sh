#!/usr/bin/env bash
# Archon Silent Integration - Test Runner
# Runs all test suites and reports overall results

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test suites to run
TEST_SUITES=(
    "test_mcp_detection.sh"
    "test_state_management.sh"
    "test_silent_integration.sh"
)

# Counters
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

echo "========================================"
echo "Archon Silent Integration Test Runner"
echo "========================================"
echo ""

# Run each test suite
for suite in "${TEST_SUITES[@]}"; do
    TOTAL_SUITES=$((TOTAL_SUITES + 1))

    suite_path="$SCRIPT_DIR/$suite"

    if [[ ! -f "$suite_path" ]]; then
        echo "❌ SKIP: $suite (not found)"
        FAILED_SUITES=$((FAILED_SUITES + 1))
        continue
    fi

    if [[ ! -x "$suite_path" ]]; then
        chmod +x "$suite_path" 2>/dev/null || true
    fi

    echo "Running: $suite"
    echo "----------------------------------------"

    if bash "$suite_path"; then
        PASSED_SUITES=$((PASSED_SUITES + 1))
    else
        FAILED_SUITES=$((FAILED_SUITES + 1))
    fi

    echo ""
done

# Overall results
echo "========================================"
echo "OVERALL TEST RESULTS"
echo "========================================"
echo "Test Suites: $TOTAL_SUITES"
echo "Passed: $PASSED_SUITES"
echo "Failed: $FAILED_SUITES"
echo "========================================"

if [[ $FAILED_SUITES -gt 0 ]]; then
    echo ""
    echo "❌ FAIL: $FAILED_SUITES test suite(s) failed"
    exit 1
else
    echo ""
    echo "✅ PASS: All test suites passed"
    exit 0
fi
