#!/bin/bash
# Spectrena Test Runner
#
# Usage:
#   ./run_tests.sh           # Run all tests
#   ./run_tests.sh -v        # Verbose output
#   ./run_tests.sh --cov     # With coverage
#   ./run_tests.sh unit      # Only unit tests
#   ./run_tests.sh workflow  # Only workflow tests

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Spectrena Test Runner${NC}"
echo "================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Please install uv first: https://docs.astral.sh/uv/${NC}"
    exit 1
fi

# Parse arguments
ARGS=()
TEST_SELECTION=""

for arg in "$@"; do
    case $arg in
        unit)
            TEST_SELECTION="tests/test_config.py tests/test_commands.py"
            ;;
        workflow)
            TEST_SELECTION="tests/test_workflow.py"
            ;;
        worktrees)
            TEST_SELECTION="tests/test_worktrees.py"
            ;;
        --cov)
            ARGS+=("--cov=src/spectrena" "--cov-report=term-missing" "--cov-report=html")
            ;;
        *)
            ARGS+=("$arg")
            ;;
    esac
done

# Run tests
echo ""
if [ -z "$TEST_SELECTION" ]; then
    echo "Running all tests..."
    uv run pytest "${ARGS[@]}"
else
    echo "Running selected tests: $TEST_SELECTION"
    uv run pytest $TEST_SELECTION "${ARGS[@]}"
fi

# Summary
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"

    # Check if coverage was generated
    if [ -d "htmlcov" ]; then
        echo ""
        echo "Coverage report: htmlcov/index.html"
    fi
else
    echo ""
    echo -e "${YELLOW}✗ Some tests failed${NC}"
    exit 1
fi
