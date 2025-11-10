#!/usr/bin/env bash
#
# test-enumerate-project.sh - Test suite for enumerate-project scripts
#
# Tests both bash and PowerShell versions for:
# - Correct execution without errors
# - Valid JSON output
# - Proper handling of edge cases
# - Bash/PowerShell parity
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test output directory
TEST_OUTPUT_DIR="/tmp/enumerate-project-tests-$$"
mkdir -p "$TEST_OUTPUT_DIR"

# Cleanup on exit
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
    echo -e "${YELLOW}⊘ SKIP:${NC} $1"
}

# Test helper: Create test project
create_test_project() {
    local project_dir="$1"
    mkdir -p "$project_dir/src"

    # Create various test files
    echo "test" > "$project_dir/test.js"
    echo "test" > "$project_dir/test.py"
    echo "normal" > "$project_dir/normal.txt"
    echo "*.log" > "$project_dir/.gitignore"
    echo "app code" > "$project_dir/src/app.js"

    # File with spaces
    echo "test" > "$project_dir/file with spaces.txt"

    # File with quotes (tricky for JSON)
    echo "test" > "$project_dir/file\"with\"quotes.txt"

    # Binary file (contains null bytes)
    printf '\x00\x01\x02\x03' > "$project_dir/binary.dat"

    # Large file (oversized)
    dd if=/dev/zero of="$project_dir/large.bin" bs=1M count=15 2>/dev/null
}

# Test: Bash script runs without errors
test_bash_no_errors() {
    ((TESTS_RUN++))
    print_test "Bash script runs without errors"

    local test_project="$TEST_OUTPUT_DIR/test-project-bash"
    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    create_test_project "$test_project"

    # Run the script and check exit code and output file
    if "$REPO_ROOT/scripts/bash/enumerate-project.sh" \
        --project "$test_project" \
        --output "$output_file" >/dev/null 2>&1 && \
        [ -f "$output_file" ] && \
        [ -s "$output_file" ]; then
        print_pass "Bash script completed successfully"
        return 0
    else
        print_fail "Bash script failed to complete or output file missing"
        return 1
    fi
}

# Test: Bash output is valid JSON
test_bash_valid_json() {
    ((TESTS_RUN++))
    print_test "Bash output is valid JSON"

    local test_project="$TEST_OUTPUT_DIR/test-project-bash"
    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    if [ ! -f "$output_file" ]; then
        create_test_project "$test_project"
        "$REPO_ROOT/scripts/bash/enumerate-project.sh" \
            --project "$test_project" \
            --output "$output_file" 2>/dev/null
    fi

    if jq . "$output_file" > /dev/null 2>&1; then
        print_pass "Bash output is valid JSON"
        return 0
    else
        print_fail "Bash output is NOT valid JSON"
        cat "$output_file"
        return 1
    fi
}

# Test: Bash output has required fields
test_bash_required_fields() {
    ((TESTS_RUN++))
    print_test "Bash output has all required fields"

    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    local required_fields=(
        ".scan_info"
        ".scan_info.project_path"
        ".scan_info.scanner"
        ".scan_info.script_version"
        ".scan_info.scan_start"
        ".scan_info.scan_end"
        ".files"
        ".statistics"
        ".statistics.total_files"
        ".statistics.by_category"
        ".statistics.largest_files"
    )

    local all_present=true
    for field in "${required_fields[@]}"; do
        if ! jq -e "$field" "$output_file" > /dev/null 2>&1; then
            print_fail "Missing required field: $field"
            all_present=false
        fi
    done

    if $all_present; then
        print_pass "All required fields present"
        return 0
    else
        return 1
    fi
}

# Test: Bash handles special characters
test_bash_special_chars() {
    ((TESTS_RUN++))
    print_test "Bash handles special characters (spaces, quotes)"

    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    # Check if files with special characters are in output
    local has_spaces=$(jq -r '.files[] | select(.path == "file with spaces.txt") | .path' "$output_file")
    local has_quotes=$(jq -r '.files[] | select(.path | contains("quotes")) | .path' "$output_file")

    if [ -n "$has_spaces" ] && [ -n "$has_quotes" ]; then
        print_pass "Special characters handled correctly"
        return 0
    else
        print_fail "Special characters NOT handled correctly"
        echo "  Found spaces: '$has_spaces'"
        echo "  Found quotes: '$has_quotes'"
        return 1
    fi
}

# Test: Bash detects oversized files
test_bash_oversized_detection() {
    ((TESTS_RUN++))
    print_test "Bash detects oversized files"

    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    local oversized_count=$(jq -r '.statistics.oversized_files' "$output_file")
    local large_file=$(jq -r '.files[] | select(.path == "large.bin") | .skip_reason' "$output_file")

    if [ "$oversized_count" -gt 0 ] && [ "$large_file" = "exceeds_max_size" ]; then
        print_pass "Oversized files detected correctly (count: $oversized_count)"
        return 0
    else
        print_fail "Oversized detection failed (count: $oversized_count, reason: $large_file)"
        return 1
    fi
}

# Test: Bash detects binary files
test_bash_binary_detection() {
    ((TESTS_RUN++))
    print_test "Bash detects binary files"

    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    local binary_file=$(jq -r '.files[] | select(.path == "binary.dat") | .is_binary' "$output_file")

    if [ "$binary_file" = "true" ]; then
        print_pass "Binary files detected correctly"
        return 0
    else
        print_fail "Binary detection failed (is_binary: $binary_file)"
        return 1
    fi
}

# Test: Bash populates largest_files
test_bash_largest_files() {
    ((TESTS_RUN++))
    print_test "Bash populates largest_files array"

    local output_file="$TEST_OUTPUT_DIR/bash-output.json"

    local largest_count=$(jq -r '.statistics.largest_files | length' "$output_file")

    if [ "$largest_count" -gt 0 ]; then
        print_pass "largest_files populated (count: $largest_count)"
        return 0
    else
        print_fail "largest_files is empty"
        return 1
    fi
}

# Test: PowerShell script runs without errors (if pwsh available)
test_powershell_no_errors() {
    ((TESTS_RUN++))
    print_test "PowerShell script runs without errors"

    if ! command -v pwsh &> /dev/null; then
        print_skip "PowerShell Core not installed"
        return 0
    fi

    local test_project="$TEST_OUTPUT_DIR/test-project-ps"
    local output_file="$TEST_OUTPUT_DIR/ps-output.json"

    create_test_project "$test_project"

    # Run the script and check exit code and output file
    if pwsh -File "$REPO_ROOT/scripts/powershell/enumerate-project.ps1" \
        -Project "$test_project" \
        -Output "$output_file" >/dev/null 2>&1 && \
        [ -f "$output_file" ] && \
        [ -s "$output_file" ]; then
        print_pass "PowerShell script completed successfully"
        return 0
    else
        print_fail "PowerShell script failed to complete or output file missing"
        return 1
    fi
}

# Test: PowerShell output is valid JSON
test_powershell_valid_json() {
    ((TESTS_RUN++))
    print_test "PowerShell output is valid JSON"

    if ! command -v pwsh &> /dev/null; then
        print_skip "PowerShell Core not installed"
        return 0
    fi

    local output_file="$TEST_OUTPUT_DIR/ps-output.json"

    if [ ! -f "$output_file" ]; then
        local test_project="$TEST_OUTPUT_DIR/test-project-ps"
        create_test_project "$test_project"
        pwsh -File "$REPO_ROOT/scripts/powershell/enumerate-project.ps1" \
            -Project "$test_project" \
            -Output "$output_file" 2>/dev/null || true
    fi

    if jq . "$output_file" > /dev/null 2>&1; then
        print_pass "PowerShell output is valid JSON"
        return 0
    else
        print_fail "PowerShell output is NOT valid JSON"
        return 1
    fi
}

# Test: Bash and PowerShell parity
test_bash_powershell_parity() {
    ((TESTS_RUN++))
    print_test "Bash and PowerShell output parity"

    if ! command -v pwsh &> /dev/null; then
        print_skip "PowerShell Core not installed"
        return 0
    fi

    local bash_output="$TEST_OUTPUT_DIR/bash-output.json"
    local ps_output="$TEST_OUTPUT_DIR/ps-output.json"

    if [ ! -f "$ps_output" ]; then
        print_skip "PowerShell output not available"
        return 0
    fi

    # Compare key statistics
    local bash_files=$(jq -r '.statistics.total_files' "$bash_output")
    local ps_files=$(jq -r '.statistics.total_files' "$ps_output")

    local bash_oversized=$(jq -r '.statistics.oversized_files' "$bash_output")
    local ps_oversized=$(jq -r '.statistics.oversized_files' "$ps_output")

    if [ "$bash_files" = "$ps_files" ] && [ "$bash_oversized" = "$ps_oversized" ]; then
        print_pass "Bash/PowerShell parity verified (files: $bash_files, oversized: $bash_oversized)"
        return 0
    else
        print_fail "Bash/PowerShell parity MISMATCH"
        echo "  Bash: files=$bash_files, oversized=$bash_oversized"
        echo "  PS:   files=$ps_files, oversized=$ps_oversized"
        return 1
    fi
}

# Test: Empty directory handling
test_empty_directory() {
    ((TESTS_RUN++))
    print_test "Bash handles empty directory"

    local empty_dir="$TEST_OUTPUT_DIR/empty-project"
    local output_file="$TEST_OUTPUT_DIR/empty-output.json"

    mkdir -p "$empty_dir"

    if "$REPO_ROOT/scripts/bash/enumerate-project.sh" \
        --project "$empty_dir" \
        --output "$output_file" 2>/dev/null; then

        local file_count=$(jq -r '.statistics.total_files' "$output_file")

        if [ "$file_count" = "0" ]; then
            print_pass "Empty directory handled correctly"
            return 0
        else
            print_fail "Empty directory returned $file_count files (expected 0)"
            return 1
        fi
    else
        print_fail "Script failed on empty directory"
        return 1
    fi
}

# Test: Help flag works
test_help_flag() {
    ((TESTS_RUN++))
    print_test "Bash --help flag works"

    if "$REPO_ROOT/scripts/bash/enumerate-project.sh" --help 2>&1 | grep -q "Usage:"; then
        print_pass "--help flag works"
        return 0
    else
        print_fail "--help flag does not work"
        return 1
    fi
}

# Main test execution
main() {
    print_header "enumerate-project.sh Test Suite"

    echo "Test output directory: $TEST_OUTPUT_DIR"
    echo "Repository root: $REPO_ROOT"
    echo ""

    # Check dependencies
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}ERROR: jq is required for tests${NC}"
        exit 1
    fi

    # Run all tests
    test_help_flag || true
    test_bash_no_errors || true
    test_bash_valid_json || true
    test_bash_required_fields || true
    test_bash_special_chars || true
    test_bash_oversized_detection || true
    test_bash_binary_detection || true
    test_bash_largest_files || true
    test_empty_directory || true
    test_powershell_no_errors || true
    test_powershell_valid_json || true
    test_bash_powershell_parity || true

    # Print summary
    print_header "Test Summary"
    echo "Tests run:    $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
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
