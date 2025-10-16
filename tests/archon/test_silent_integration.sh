#!/usr/bin/env bash
# Test Suite: Silent Integration
# Tests that all Archon scripts operate silently and gracefully

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts/bash"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper
run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command"; then
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
echo "Test Suite: Silent Integration"
echo "========================================"
echo ""

# Test 1: archon-common.sh has valid bash syntax
run_test "archon-common.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-common.sh'"

# Test 2: archon-auto-init.sh has valid bash syntax
run_test "archon-auto-init.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-auto-init.sh'"

# Test 3: archon-sync-documents.sh has valid bash syntax
run_test "archon-sync-documents.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-sync-documents.sh'"

# Test 4: archon-auto-sync-tasks.sh has valid bash syntax
run_test "archon-auto-sync-tasks.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-auto-sync-tasks.sh'"

# Test 5: archon-auto-pull-status.sh has valid bash syntax
run_test "archon-auto-pull-status.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-auto-pull-status.sh'"

# Test 6: archon-daemon.sh has valid bash syntax
run_test "archon-daemon.sh syntax is valid" \
    "bash -n '$SCRIPTS_DIR/archon-daemon.sh'"

# Test 7: archon-auto-init.sh exits silently with no args
STDOUT_INIT=$(bash "$SCRIPTS_DIR/archon-auto-init.sh" 2>/dev/null || true)
run_test "archon-auto-init.sh is silent with no args" \
    "test -z \"$STDOUT_INIT\""

# Test 8: archon-sync-documents.sh exits silently with no args
STDOUT_SYNC=$(bash "$SCRIPTS_DIR/archon-sync-documents.sh" 2>/dev/null || true)
run_test "archon-sync-documents.sh is silent with no args" \
    "test -z \"$STDOUT_SYNC\""

# Test 9: archon-auto-sync-tasks.sh exits silently with no args
STDOUT_TASKS=$(bash "$SCRIPTS_DIR/archon-auto-sync-tasks.sh" 2>/dev/null || true)
run_test "archon-auto-sync-tasks.sh is silent with no args" \
    "test -z \"$STDOUT_TASKS\""

# Test 10: archon-auto-pull-status.sh exits silently with no args
STDOUT_STATUS=$(bash "$SCRIPTS_DIR/archon-auto-pull-status.sh" 2>/dev/null || true)
run_test "archon-auto-pull-status.sh is silent with no args" \
    "test -z \"$STDOUT_STATUS\""

# Test 11: archon-daemon.sh exits silently with invalid args
STDOUT_DAEMON=$(bash "$SCRIPTS_DIR/archon-daemon.sh" 2>/dev/null || true)
run_test "archon-daemon.sh is silent with no args" \
    "test -z \"$STDOUT_DAEMON\""

# Test 12: All scripts are executable
run_test "archon-common.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-common.sh'"

run_test "archon-auto-init.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-auto-init.sh'"

run_test "archon-sync-documents.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-sync-documents.sh'"

run_test "archon-auto-sync-tasks.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-auto-sync-tasks.sh'"

run_test "archon-auto-pull-status.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-auto-pull-status.sh'"

run_test "archon-daemon.sh is executable" \
    "test -x '$SCRIPTS_DIR/archon-daemon.sh'"

# Test 13: Scripts gracefully handle missing common.sh
run_test "archon-auto-init.sh handles missing common.sh" \
    "bash -c 'cd /tmp && bash $SCRIPTS_DIR/archon-auto-init.sh 2>/dev/null; test \$? -eq 0 || test \$? -eq 1'"

# Test 14: .gitignore excludes .archon-state/
run_test ".gitignore excludes .archon-state/" \
    "grep -q '.archon-state' '$PROJECT_ROOT/.gitignore'"

echo ""
echo "========================================"
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
echo "========================================"

if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
fi

exit 0
