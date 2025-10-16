#!/usr/bin/env bash
# Archon MCP Silent Integration - Validation Test Suite
# Tests all critical paths for the silent integration implementation

set -e

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/scripts/bash"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Print test header
print_header() {
    echo ""
    echo "======================================"
    echo "$1"
    echo "======================================"
}

# Print test result
print_result() {
    local test_name="$1"
    local result="$2"
    local message="${3:-}"

    TESTS_RUN=$((TESTS_RUN + 1))

    if [[ "$result" == "PASS" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name"
        if [[ -n "$message" ]]; then
            echo "  Error: $message"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Create temporary test environment
setup_test_env() {
    TEST_WORKSPACE="/tmp/archon-integration-test-$$"
    mkdir -p "$TEST_WORKSPACE"

    # Create mock feature directory
    MOCK_FEATURE_DIR="$TEST_WORKSPACE/specs/001-test-feature"
    mkdir -p "$MOCK_FEATURE_DIR"

    # Create mock spec.md
    cat > "$MOCK_FEATURE_DIR/spec.md" <<'EOF'
# Test Feature

This is a test feature for validation.

## User Stories

### US1: Test Story
As a user, I want to test this feature.
EOF

    # Create mock tasks.md
    cat > "$MOCK_FEATURE_DIR/tasks.md" <<'EOF'
# Tasks for Test Feature

## Phase 1: Setup
- [ ] [T001] [US1] Setup test environment
- [ ] [T002] [P] [US1] Configure test data
- [X] [T003] [US1] Initialize test project

## Phase 2: Implementation
- [ ] [T004] Implement core functionality
EOF

    echo "$TEST_WORKSPACE"
}

# Cleanup test environment
cleanup_test_env() {
    if [[ -n "${TEST_WORKSPACE:-}" ]] && [[ -d "$TEST_WORKSPACE" ]]; then
        rm -rf "$TEST_WORKSPACE"
    fi
}

# Test 1: Script Syntax Validation
test_script_syntax() {
    print_header "Test 1: Script Syntax Validation"

    local scripts=(
        "archon-common.sh"
        "archon-auto-init.sh"
        "archon-sync-documents.sh"
        "archon-auto-sync-tasks.sh"
        "archon-auto-pull-status.sh"
    )

    for script in "${scripts[@]}"; do
        local script_path="$SCRIPTS_DIR/$script"
        if bash -n "$script_path" 2>/dev/null; then
            print_result "$script: Syntax check" "PASS"
        else
            print_result "$script: Syntax check" "FAIL" "Syntax error detected"
        fi
    done
}

# Test 2: Script Executability
test_script_permissions() {
    print_header "Test 2: Script Executability"

    local scripts=(
        "archon-common.sh"
        "archon-auto-init.sh"
        "archon-sync-documents.sh"
        "archon-auto-sync-tasks.sh"
        "archon-auto-pull-status.sh"
    )

    for script in "${scripts[@]}"; do
        local script_path="$SCRIPTS_DIR/$script"
        if [[ -x "$script_path" ]]; then
            print_result "$script: Execute permission" "PASS"
        else
            print_result "$script: Execute permission" "FAIL" "Not executable"
        fi
    done
}

# Test 3: Silent Operation Guarantee
test_silent_operation() {
    print_header "Test 3: Silent Operation Guarantee"

    # Source archon-common.sh and test functions
    source "$SCRIPTS_DIR/archon-common.sh"

    # Test check_archon_available (should produce no output)
    local output
    output=$(check_archon_available 2>&1 || true)
    if [[ -z "$output" ]]; then
        print_result "check_archon_available(): No output" "PASS"
    else
        print_result "check_archon_available(): No output" "FAIL" "Produced output: $output"
    fi

    # Test get_archon_state_dir (should produce stdout only)
    output=$(get_archon_state_dir 2>&1)
    if [[ -n "$output" ]]; then
        print_result "get_archon_state_dir(): Returns path" "PASS"
    else
        print_result "get_archon_state_dir(): Returns path" "FAIL" "No output"
    fi

    # Test extract_feature_name
    output=$(extract_feature_name "/path/to/specs/001-test-feature" 2>&1)
    if [[ "$output" == "001-test-feature" ]]; then
        print_result "extract_feature_name(): Correct extraction" "PASS"
    else
        print_result "extract_feature_name(): Correct extraction" "FAIL" "Got: $output"
    fi

    # Test get_timestamp
    output=$(get_timestamp 2>&1)
    if [[ "$output" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
        print_result "get_timestamp(): ISO 8601 format" "PASS"
    else
        print_result "get_timestamp(): ISO 8601 format" "FAIL" "Got: $output"
    fi
}

# Test 4: State Management Functions
test_state_management() {
    print_header "Test 4: State Management Functions"

    source "$SCRIPTS_DIR/archon-common.sh"

    local test_workspace=$(setup_test_env)

    # Override get_archon_state_dir to use test workspace
    get_archon_state_dir() {
        echo "$test_workspace/.archon-state"
    }

    local feature_name="001-test-feature"
    local state_dir="$test_workspace/.archon-state"
    mkdir -p "$state_dir"

    # Test project mapping
    if save_project_mapping "$feature_name" "proj-123" 2>/dev/null; then
        print_result "save_project_mapping(): Save successful" "PASS"
    else
        print_result "save_project_mapping(): Save successful" "FAIL"
    fi

    local loaded_pid
    loaded_pid=$(load_project_mapping "$feature_name")
    if [[ "$loaded_pid" == "proj-123" ]]; then
        print_result "load_project_mapping(): Load correct" "PASS"
    else
        print_result "load_project_mapping(): Load correct" "FAIL" "Got: $loaded_pid"
    fi

    # Test document mapping
    if save_document_mapping "$feature_name" "spec.md" "doc-abc" 2>/dev/null; then
        print_result "save_document_mapping(): Save successful" "PASS"
    else
        print_result "save_document_mapping(): Save successful" "FAIL"
    fi

    local loaded_doc
    loaded_doc=$(load_document_mapping "$feature_name" "spec.md")
    if [[ "$loaded_doc" == "doc-abc" ]]; then
        print_result "load_document_mapping(): Load correct" "PASS"
    else
        print_result "load_document_mapping(): Load correct" "FAIL" "Got: $loaded_doc"
    fi

    # Test task mapping
    if save_task_mapping "$feature_name" "T001" "task-xyz" 2>/dev/null; then
        print_result "save_task_mapping(): Save successful" "PASS"
    else
        print_result "save_task_mapping(): Save successful" "FAIL"
    fi

    local loaded_task
    loaded_task=$(load_task_mapping "$feature_name" "T001")
    if [[ "$loaded_task" == "task-xyz" ]]; then
        print_result "load_task_mapping(): Load correct" "PASS"
    else
        print_result "load_task_mapping(): Load correct" "FAIL" "Got: $loaded_task"
    fi

    # Test sync metadata
    local timestamp="2025-10-15T12:00:00Z"
    if save_sync_metadata "$feature_name" "spec.md" "$timestamp" 2>/dev/null; then
        print_result "save_sync_metadata(): Save successful" "PASS"
    else
        print_result "save_sync_metadata(): Save successful" "FAIL"
    fi

    local loaded_meta
    loaded_meta=$(load_sync_metadata "$feature_name" "spec.md")
    if [[ "$loaded_meta" == "$timestamp" ]]; then
        print_result "load_sync_metadata(): Load correct" "PASS"
    else
        print_result "load_sync_metadata(): Load correct" "FAIL" "Got: $loaded_meta"
    fi

    cleanup_test_env
}

# Test 5: Marker File Creation
test_marker_files() {
    print_header "Test 5: Marker File Creation"

    local test_workspace=$(setup_test_env)

    # Test archon-auto-init.sh
    local output
    output=$("$SCRIPTS_DIR/archon-auto-init.sh" "$test_workspace/specs/001-test-feature" 2>&1)
    if [[ -z "$output" ]]; then
        print_result "archon-auto-init.sh: Silent execution" "PASS"
    else
        print_result "archon-auto-init.sh: Silent execution" "FAIL" "Output: $output"
    fi

    # Check if marker file created
    local marker_file="$SCRIPTS_DIR/.archon-state/001-test-feature.init-request"
    if [[ -f "$marker_file" ]]; then
        print_result "archon-auto-init.sh: Marker file created" "PASS"

        # Validate JSON structure
        if command -v jq >/dev/null 2>&1 && jq empty "$marker_file" 2>/dev/null; then
            print_result "archon-auto-init.sh: Valid JSON marker" "PASS"
        else
            if command -v jq >/dev/null 2>&1; then
                print_result "archon-auto-init.sh: Valid JSON marker" "FAIL" "Invalid JSON"
            else
                print_result "archon-auto-init.sh: Valid JSON marker" "SKIP" "jq not available"
                TESTS_RUN=$((TESTS_RUN - 1))  # Don't count skipped test
            fi
        fi
    else
        print_result "archon-auto-init.sh: Marker file created" "FAIL" "File not found"
    fi

    # Test archon-sync-documents.sh (will exit early, no project ID - expected behavior)
    output=$("$SCRIPTS_DIR/archon-sync-documents.sh" "$test_workspace/specs/001-test-feature" "pull" 2>&1)
    if [[ -z "$output" ]]; then
        print_result "archon-sync-documents.sh: Silent execution" "PASS"
    else
        print_result "archon-sync-documents.sh: Silent execution" "FAIL" "Output: $output"
    fi

    # Test archon-auto-sync-tasks.sh (will exit early, no project ID - expected behavior)
    output=$("$SCRIPTS_DIR/archon-auto-sync-tasks.sh" "$test_workspace/specs/001-test-feature" 2>&1)
    if [[ -z "$output" ]]; then
        print_result "archon-auto-sync-tasks.sh: Silent execution" "PASS"
    else
        print_result "archon-auto-sync-tasks.sh: Silent execution" "FAIL" "Output: $output"
    fi

    # Test archon-auto-pull-status.sh (will exit early, no project ID - expected behavior)
    output=$("$SCRIPTS_DIR/archon-auto-pull-status.sh" "$test_workspace/specs/001-test-feature" 2>&1)
    if [[ -z "$output" ]]; then
        print_result "archon-auto-pull-status.sh: Silent execution" "PASS"
    else
        print_result "archon-auto-pull-status.sh: Silent execution" "FAIL" "Output: $output"
    fi

    cleanup_test_env
}

# Test 6: Task Parsing Logic (with project setup)
test_task_parsing() {
    print_header "Test 6: Task Parsing Logic"

    # Create a feature directory in the repo (so state management works)
    local test_feature_dir="$REPO_ROOT/specs/test-archon-validation"
    mkdir -p "$test_feature_dir"

    # Create tasks.md
    cat > "$test_feature_dir/tasks.md" <<'EOF'
# Tasks for Test Feature

## Phase 1: Setup
- [ ] [T001] [US1] Setup test environment
- [ ] [T002] [P] [US1] Configure test data
- [X] [T003] [US1] Initialize test project

## Phase 2: Implementation
- [ ] [T004] Implement core functionality
EOF

    # Set up project mapping
    mkdir -p "$SCRIPTS_DIR/.archon-state"
    source "$SCRIPTS_DIR/archon-common.sh"
    save_project_mapping "test-archon-validation" "proj-test-123" >/dev/null 2>&1

    # Run task sync
    "$SCRIPTS_DIR/archon-auto-sync-tasks.sh" "$test_feature_dir" >/dev/null 2>&1

    local task_marker="$SCRIPTS_DIR/.archon-state/test-archon-validation.task-sync-request"

    if [[ -f "$task_marker" ]]; then
        print_result "Task sync: Marker file created" "PASS"

        if command -v jq >/dev/null 2>&1; then
            # Check task T001
            local t001_title
            t001_title=$(jq -r '.tasks[] | select(.task_id == "T001") | .title' "$task_marker" 2>/dev/null || echo "ERROR")
            if [[ "$t001_title" == "Setup test environment" ]]; then
                print_result "Task T001: Title parsed correctly" "PASS"
            else
                print_result "Task T001: Title parsed correctly" "FAIL" "Got: $t001_title"
            fi

            local t001_status
            t001_status=$(jq -r '.tasks[] | select(.task_id == "T001") | .status' "$task_marker" 2>/dev/null || echo "ERROR")
            if [[ "$t001_status" == "todo" ]]; then
                print_result "Task T001: Status parsed correctly" "PASS"
            else
                print_result "Task T001: Status parsed correctly" "FAIL" "Got: $t001_status"
            fi

            local t001_story
            t001_story=$(jq -r '.tasks[] | select(.task_id == "T001") | .story' "$task_marker" 2>/dev/null || echo "ERROR")
            if [[ "$t001_story" == "US1" ]]; then
                print_result "Task T001: Story parsed correctly" "PASS"
            else
                print_result "Task T001: Story parsed correctly" "FAIL" "Got: $t001_story"
            fi

            # Check task T002 (parallel)
            local t002_parallel
            t002_parallel=$(jq -r '.tasks[] | select(.task_id == "T002") | .parallel' "$task_marker" 2>/dev/null || echo "ERROR")
            if [[ "$t002_parallel" == "true" ]]; then
                print_result "Task T002: Parallel marker parsed" "PASS"
            else
                print_result "Task T002: Parallel marker parsed" "FAIL" "Got: $t002_parallel"
            fi

            # Check task T003 (completed)
            local t003_status
            t003_status=$(jq -r '.tasks[] | select(.task_id == "T003") | .status' "$task_marker" 2>/dev/null || echo "ERROR")
            if [[ "$t003_status" == "done" ]]; then
                print_result "Task T003: Completed status parsed" "PASS"
            else
                print_result "Task T003: Completed status parsed" "FAIL" "Got: $t003_status"
            fi

            # Check task T004 (no ID)
            local t004_count
            t004_count=$(jq '[.tasks[] | select(.task_id == "")] | length' "$task_marker" 2>/dev/null || echo "0")
            if [[ "$t004_count" -ge 1 ]]; then
                print_result "Task T004: Tasks without IDs handled" "PASS"
            else
                print_result "Task T004: Tasks without IDs handled" "FAIL"
            fi
        else
            print_result "Task parsing tests: Skipped (jq not available)" "SKIP"
            TESTS_RUN=$((TESTS_RUN - 6))  # Don't count skipped tests
        fi
    else
        print_result "Task sync: Marker file created" "FAIL" "File not found"
    fi

    # Cleanup
    rm -rf "$test_feature_dir" 2>/dev/null || true
}

# Test 7: Gitignore Configuration
test_gitignore() {
    print_header "Test 7: Gitignore Configuration"

    local gitignore="$REPO_ROOT/.gitignore"

    if grep -q "\.archon-state/" "$gitignore"; then
        print_result ".gitignore: .archon-state/ excluded" "PASS"
    else
        print_result ".gitignore: .archon-state/ excluded" "FAIL" "Pattern not found"
    fi

    if grep -q "scripts/bash/\.archon-state/" "$gitignore"; then
        print_result ".gitignore: scripts/bash/.archon-state/ excluded" "PASS"
    else
        print_result ".gitignore: scripts/bash/.archon-state/ excluded" "FAIL" "Pattern not found"
    fi
}

# Test 8: Integration with common.sh
test_common_integration() {
    print_header "Test 8: Integration with common.sh"

    # Source common.sh and check if archon functions are available
    source "$SCRIPTS_DIR/common.sh"

    if declare -f check_archon_available >/dev/null; then
        print_result "common.sh: check_archon_available() available" "PASS"
    else
        print_result "common.sh: check_archon_available() available" "FAIL"
    fi

    if declare -f save_project_mapping >/dev/null; then
        print_result "common.sh: save_project_mapping() available" "PASS"
    else
        print_result "common.sh: save_project_mapping() available" "FAIL"
    fi

    if declare -f extract_feature_name >/dev/null; then
        print_result "common.sh: extract_feature_name() available" "PASS"
    else
        print_result "common.sh: extract_feature_name() available" "FAIL"
    fi
}

# Test 9: Error Handling and Graceful Degradation
test_error_handling() {
    print_header "Test 9: Error Handling & Graceful Degradation"

    # Test with missing feature directory
    local output
    output=$("$SCRIPTS_DIR/archon-auto-init.sh" "" 2>&1 || true)
    local exit_code=$?

    if [[ $exit_code -eq 0 ]] && [[ -z "$output" ]]; then
        print_result "archon-auto-init.sh: Handles missing directory" "PASS"
    else
        print_result "archon-auto-init.sh: Handles missing directory" "FAIL" "Exit: $exit_code, Output: $output"
    fi

    # Test with non-existent feature directory
    output=$("$SCRIPTS_DIR/archon-auto-init.sh" "/nonexistent/path" 2>&1 || true)
    exit_code=$?

    if [[ $exit_code -eq 0 ]] && [[ -z "$output" ]]; then
        print_result "archon-auto-init.sh: Handles invalid path" "PASS"
    else
        print_result "archon-auto-init.sh: Handles invalid path" "FAIL" "Exit: $exit_code"
    fi

    # Test sync with invalid mode
    output=$("$SCRIPTS_DIR/archon-sync-documents.sh" "/tmp" "invalid" 2>&1 || true)
    exit_code=$?

    if [[ $exit_code -eq 0 ]] && [[ -z "$output" ]]; then
        print_result "archon-sync-documents.sh: Handles invalid mode" "PASS"
    else
        print_result "archon-sync-documents.sh: Handles invalid mode" "FAIL" "Exit: $exit_code"
    fi
}

# Main test execution
main() {
    echo "Archon MCP Silent Integration - Validation Test Suite"
    echo "======================================================"

    # Check if jq is available for JSON tests
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: jq not found. JSON validation tests will be skipped.${NC}"
    fi

    test_script_syntax
    test_script_permissions
    test_silent_operation
    test_state_management
    test_marker_files
    test_task_parsing
    test_gitignore
    test_common_integration
    test_error_handling

    # Clean up any leftover marker files and test directories
    rm -rf "$SCRIPTS_DIR/.archon-state" 2>/dev/null || true
    rm -rf "$REPO_ROOT/specs/test-archon-validation" 2>/dev/null || true

    # Print summary
    print_header "Test Summary"
    echo "Total tests run: $TESTS_RUN"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Failed: $TESTS_FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Run tests
main
