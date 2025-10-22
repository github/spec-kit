#!/bin/bash
# Run Bicep Generator tests with various options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
PARALLEL=false
MARKERS=""

# Help function
show_help() {
    cat << EOF
Usage: ${0##*/} [OPTIONS]

Run Bicep Generator tests with various configurations.

OPTIONS:
    -h, --help              Show this help message
    -t, --type TYPE         Test type to run: all, unit, integration, e2e (default: all)
    -m, --markers MARKERS   Run tests matching given mark expression
    -c, --no-coverage       Disable coverage reporting
    -v, --verbose           Verbose output
    -p, --parallel          Run tests in parallel
    -f, --failed            Run only previously failed tests
    -s, --slow              Include slow tests
    -a, --azure             Include Azure integration tests (requires credentials)
    -q, --quick             Quick test run (unit tests only, no coverage)

EXAMPLES:
    ${0##*/}                                   # Run all tests with coverage
    ${0##*/} -t unit                          # Run only unit tests
    ${0##*/} -t integration -v                # Run integration tests with verbose output
    ${0##*/} -m "not slow"                    # Run tests excluding slow tests
    ${0##*/} -a                                # Run all tests including Azure tests
    ${0##*/} -q                                # Quick unit tests (no coverage)
    ${0##*/} -t e2e -s                        # Run E2E tests including slow ones

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -f|--failed)
            MARKERS="${MARKERS} --lf"
            shift
            ;;
        -s|--slow)
            MARKERS="${MARKERS} or slow"
            shift
            ;;
        -a|--azure)
            MARKERS="${MARKERS} or azure"
            shift
            ;;
        -q|--quick)
            TEST_TYPE="unit"
            COVERAGE=false
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

# Add test type marker
case $TEST_TYPE in
    unit)
        PYTEST_CMD="$PYTEST_CMD -m unit"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD -m integration"
        ;;
    e2e)
        PYTEST_CMD="$PYTEST_CMD -m e2e"
        ;;
    all)
        # Run all tests except azure by default
        if [[ ! "$MARKERS" =~ "azure" ]]; then
            PYTEST_CMD="$PYTEST_CMD -m 'not azure'"
        fi
        ;;
    *)
        echo -e "${RED}Error: Invalid test type: $TEST_TYPE${NC}"
        echo "Valid types: all, unit, integration, e2e"
        exit 1
        ;;
esac

# Add additional markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/specify_cli/bicep --cov-report=term-missing --cov-report=html"
else
    PYTEST_CMD="$PYTEST_CMD --no-cov"
fi

# Add verbose option
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add parallel option
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Print configuration
echo -e "${GREEN}=== Bicep Generator Test Runner ===${NC}"
echo "Test Type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo "Verbose: $VERBOSE"
echo "Parallel: $PARALLEL"
echo "Markers: $MARKERS"
echo ""
echo -e "${YELLOW}Running command:${NC} $PYTEST_CMD"
echo ""

# Run tests
if $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    
    # Show coverage report location if enabled
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
