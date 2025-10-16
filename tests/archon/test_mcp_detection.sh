#!/usr/bin/env bash
# Test Suite: MCP Detection
# Tests for check_archon_available() and MCP availability detection

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source the utilities
source "$PROJECT_ROOT/scripts/bash/archon-common.sh" 2>/dev/null || {
    echo "❌ FAIL: Cannot source archon-common.sh"
    exit 1
}

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper
run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command" >/dev/null 2>&1; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo "❌ FAIL: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "========================================"
echo "Test Suite: MCP Detection"
echo "========================================"
echo ""

# Test 1: check_archon_available returns boolean (0 or 1)
run_test "check_archon_available() returns exit code 0 or 1" \
    "check_archon_available; test \$? -eq 0 || test \$? -eq 1"

# Test 2: check_archon_available is silent (no stdout)
run_test "check_archon_available() produces no stdout" \
    "test -z \"\$(check_archon_available 2>/dev/null)\""

# Test 3: check_archon_available is silent (no stderr)
run_test "check_archon_available() produces no stderr" \
    "test -z \"\$(check_archon_available 2>&1 >/dev/null)\""

# Test 4: Function exists and is callable
run_test "check_archon_available() function exists" \
    "type check_archon_available >/dev/null 2>&1"

# Test 5: get_archon_state_dir returns valid path
run_test "get_archon_state_dir() returns valid path" \
    "test -n \"\$(get_archon_state_dir)\""

# Test 6: get_timestamp returns ISO 8601 format
run_test "get_timestamp() returns ISO 8601 timestamp" \
    "get_timestamp | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$' >/dev/null"

# Test 7: extract_feature_name extracts correctly
TEST_DIR="/path/to/specs/001-test-feature"
run_test "extract_feature_name() extracts feature name" \
    "test \"\$(extract_feature_name '$TEST_DIR')\" = '001-test-feature'"

echo ""
echo "========================================"
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
echo "========================================"

if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
fi

exit 0
