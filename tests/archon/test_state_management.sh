#!/usr/bin/env bash
# Test Suite: State Management
# Tests for project/document/task ID mapping functions

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
echo "Test Suite: State Management"
echo "========================================"
echo ""

# Setup test state directory
STATE_DIR="$(get_archon_state_dir)"
mkdir -p "$STATE_DIR" 2>/dev/null || true

# Test 1: Save and load project mapping
TEST_FEATURE="test-feature-001"
TEST_PROJECT_ID="proj-abc123def456"
save_project_mapping "$TEST_FEATURE" "$TEST_PROJECT_ID" 2>/dev/null
LOADED_ID=$(load_project_mapping "$TEST_FEATURE")
run_test "Project mapping save/load cycle" \
    "test \"$LOADED_ID\" = \"$TEST_PROJECT_ID\""

# Test 2: Save and load document mapping
TEST_DOC_FILENAME="spec.md"
TEST_DOC_ID="doc-xyz789"
save_document_mapping "$TEST_FEATURE" "$TEST_DOC_FILENAME" "$TEST_DOC_ID" 2>/dev/null
LOADED_DOC_ID=$(load_document_mapping "$TEST_FEATURE" "$TEST_DOC_FILENAME")
run_test "Document mapping save/load cycle" \
    "test \"$LOADED_DOC_ID\" = \"$TEST_DOC_ID\""

# Test 3: Save and load task mapping
TEST_TASK_LOCAL="T001"
TEST_TASK_ARCHON="task-uuid-12345"
save_task_mapping "$TEST_FEATURE" "$TEST_TASK_LOCAL" "$TEST_TASK_ARCHON" 2>/dev/null
LOADED_TASK_ID=$(load_task_mapping "$TEST_FEATURE" "$TEST_TASK_LOCAL")
run_test "Task mapping save/load cycle" \
    "test \"$LOADED_TASK_ID\" = \"$TEST_TASK_ARCHON\""

# Test 4: Save and load sync metadata with timestamp
TEST_FILENAME="plan.md"
TEST_TIMESTAMP="2025-10-16T01:30:00Z"
save_sync_metadata "$TEST_FEATURE" "$TEST_FILENAME" "$TEST_TIMESTAMP" 2>/dev/null
LOADED_TIMESTAMP=$(load_sync_metadata "$TEST_FEATURE" "$TEST_FILENAME")
run_test "Sync metadata save/load cycle (with colons in timestamp)" \
    "test \"$LOADED_TIMESTAMP\" = \"$TEST_TIMESTAMP\""

# Test 5: Load non-existent project returns empty
EMPTY_RESULT=$(load_project_mapping "non-existent-feature")
run_test "Loading non-existent project returns empty string" \
    "test -z \"$EMPTY_RESULT\""

# Test 6: Load non-existent document returns empty
EMPTY_DOC=$(load_document_mapping "$TEST_FEATURE" "non-existent.md")
run_test "Loading non-existent document returns empty string" \
    "test -z \"$EMPTY_DOC\""

# Test 7: Load non-existent task returns empty
EMPTY_TASK=$(load_task_mapping "$TEST_FEATURE" "T999")
run_test "Loading non-existent task returns empty string" \
    "test -z \"$EMPTY_TASK\""

# Test 8: State directory is created if missing
rm -rf "$STATE_DIR" 2>/dev/null || true
save_project_mapping "new-feature" "proj-test" 2>/dev/null
run_test "State directory auto-created on save" \
    "test -d \"$STATE_DIR\""

# Test 9: All save operations are silent (no stdout)
STDOUT_OUTPUT=$(save_project_mapping "silent-test" "proj-123" 2>/dev/null)
run_test "save_project_mapping() is silent (no stdout)" \
    "test -z \"$STDOUT_OUTPUT\""

# Test 10: All load operations produce only result (no stderr to stdout)
STDERR_LEAKED=$(load_project_mapping "non-existent" 2>&1 >/dev/null)
run_test "load_project_mapping() doesn't leak stderr" \
    "test -z \"$STDERR_LEAKED\""

# Cleanup test state
rm -rf "$STATE_DIR" 2>/dev/null || true

echo ""
echo "========================================"
echo "Results: $TESTS_PASSED/$TESTS_RUN passed"
echo "========================================"

if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
fi

exit 0
