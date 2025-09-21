#!/usr/bin/env bash
# Project State Analyzer - Compare constitution against implementation
set -e

JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) 
            echo "Usage: $0 [--json]"
            echo "Analyzes project state by comparing constitution.md against implementation"
            exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ERROR: Not in a git repository. Run this script from within a git repository." >&2
    exit 1
fi

CONSTITUTION_FILE="$REPO_ROOT/.specify/memory/constitution.md"
SRC_DIR="$REPO_ROOT/src"
TESTS_DIR="$REPO_ROOT/tests"
DOCS_DIR="$REPO_ROOT/docs"
SPECS_DIR="$REPO_ROOT/specs"

# Check if this is a brownfield project
IS_BROWNFIELD=false
PROJECT_TYPE="greenfield"

if [ -d "$SRC_DIR" ] || [ -d "$TESTS_DIR" ] || [ -d "$DOCS_DIR" ]; then
    IS_BROWNFIELD=true
    PROJECT_TYPE="brownfield"
fi

# Analyze existing specs and their completion status
EXISTING_SPECS=()
COMPLETED_FEATURES=()
INCOMPLETE_FEATURES=()
MISSING_IMPLEMENTATIONS=()

if [ -d "$SPECS_DIR" ]; then
    for spec_dir in "$SPECS_DIR"/*; do
        if [ -d "$spec_dir" ]; then
            SPEC_NAME=$(basename "$spec_dir")
            EXISTING_SPECS+=("$SPEC_NAME")
            
            # Check if tasks.md exists and analyze completion
            TASKS_FILE="$spec_dir/tasks.md"
            if [ -f "$TASKS_FILE" ]; then
                # Count completed vs total tasks
                TOTAL_TASKS=$(grep -c "^- \[ \]" "$TASKS_FILE" 2>/dev/null || echo "0")
                COMPLETED_TASKS=$(grep -c "^- \[x\]" "$TASKS_FILE" 2>/dev/null || echo "0")
                
                if [ "$TOTAL_TASKS" -eq "$COMPLETED_TASKS" ] && [ "$TOTAL_TASKS" -gt 0 ]; then
                    COMPLETED_FEATURES+=("$SPEC_NAME")
                elif [ "$COMPLETED_TASKS" -gt 0 ]; then
                    INCOMPLETE_FEATURES+=("$SPEC_NAME:$COMPLETED_TASKS/$TOTAL_TASKS")
                else
                    MISSING_IMPLEMENTATIONS+=("$SPEC_NAME")
                fi
            else
                MISSING_IMPLEMENTATIONS+=("$SPEC_NAME")
            fi
        fi
    done
fi

# Analyze implementation folders
IMPLEMENTATION_STATUS=""
SRC_FILES_COUNT=0
TEST_FILES_COUNT=0
DOC_FILES_COUNT=0

if [ -d "$SRC_DIR" ]; then
    SRC_FILES_COUNT=$(find "$SRC_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.cs" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | wc -l)
fi

if [ -d "$TESTS_DIR" ]; then
    TEST_FILES_COUNT=$(find "$TESTS_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.cs" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | wc -l)
fi

if [ -d "$DOCS_DIR" ]; then
    DOC_FILES_COUNT=$(find "$DOCS_DIR" -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) 2>/dev/null | wc -l)
fi

# Constitution analysis
CONSTITUTION_PRINCIPLES=()
CONSTITUTION_REQUIREMENTS=()

if [ -f "$CONSTITUTION_FILE" ]; then
    # Extract principle names (lines starting with ###)
    while IFS= read -r line; do
        if [[ "$line" =~ ^###[[:space:]]*(.+) ]]; then
            PRINCIPLE_NAME="${BASH_REMATCH[1]}"
            CONSTITUTION_PRINCIPLES+=("$PRINCIPLE_NAME")
        fi
    done < "$CONSTITUTION_FILE"
    
    # Extract key requirements from constitution
    if grep -q "Library-First\|library" "$CONSTITUTION_FILE"; then
        CONSTITUTION_REQUIREMENTS+=("Library-First Architecture")
    fi
    if grep -q "CLI Interface\|CLI" "$CONSTITUTION_FILE"; then
        CONSTITUTION_REQUIREMENTS+=("CLI Interface")
    fi
    if grep -q "Test-First\|TDD\|NON-NEGOTIABLE" "$CONSTITUTION_FILE"; then
        CONSTITUTION_REQUIREMENTS+=("Test-First Development")
    fi
    if grep -q "Integration Testing" "$CONSTITUTION_FILE"; then
        CONSTITUTION_REQUIREMENTS+=("Integration Testing")
    fi
    if grep -q "Observability\|logging" "$CONSTITUTION_FILE"; then
        CONSTITUTION_REQUIREMENTS+=("Observability")
    fi
fi

# Gap analysis
CONSTITUTIONAL_GAPS=()
IMPLEMENTATION_GAPS=()

# Check for constitutional compliance
if [[ " ${CONSTITUTION_REQUIREMENTS[*]} " =~ " Test-First Development " ]] && [ "$TEST_FILES_COUNT" -eq 0 ]; then
    CONSTITUTIONAL_GAPS+=("Missing test implementation - Constitution requires Test-First")
fi

if [[ " ${CONSTITUTION_REQUIREMENTS[*]} " =~ " CLI Interface " ]] && [ "$SRC_FILES_COUNT" -gt 0 ]; then
    # Check if CLI files exist
    CLI_FILES=$(find "$SRC_DIR" -type f -name "*cli*" -o -name "*command*" 2>/dev/null | wc -l)
    if [ "$CLI_FILES" -eq 0 ]; then
        CONSTITUTIONAL_GAPS+=("Missing CLI interface - Constitution requires CLI for all libraries")
    fi
fi

# Generate analysis summary
ANALYSIS_DATE=$(date +"%Y-%m-%d %H:%M:%S")

if $JSON_MODE; then
    printf '{"project_type":"%s","analysis_date":"%s","existing_specs":%s,"completed_features":%s,"incomplete_features":%s,"missing_implementations":%s,"src_files":%d,"test_files":%d,"doc_files":%d,"constitution_principles":%s,"constitution_requirements":%s,"constitutional_gaps":%s,"implementation_gaps":%s}\n' \
        "$PROJECT_TYPE" \
        "$ANALYSIS_DATE" \
        "$(printf '%s\n' "${EXISTING_SPECS[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${COMPLETED_FEATURES[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${INCOMPLETE_FEATURES[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${MISSING_IMPLEMENTATIONS[@]}" | jq -R . | jq -s .)" \
        "$SRC_FILES_COUNT" \
        "$TEST_FILES_COUNT" \
        "$DOC_FILES_COUNT" \
        "$(printf '%s\n' "${CONSTITUTION_PRINCIPLES[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${CONSTITUTION_REQUIREMENTS[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${CONSTITUTIONAL_GAPS[@]}" | jq -R . | jq -s .)" \
        "$(printf '%s\n' "${IMPLEMENTATION_GAPS[@]}" | jq -R . | jq -s .)"
else
    echo "PROJECT TYPE: $PROJECT_TYPE"
    echo "ANALYSIS DATE: $ANALYSIS_DATE"
    echo ""
    echo "=== EXISTING SPECS ==="
    printf '%s\n' "${EXISTING_SPECS[@]}"
    echo ""
    echo "=== COMPLETED FEATURES ==="
    printf '%s\n' "${COMPLETED_FEATURES[@]}"
    echo ""
    echo "=== INCOMPLETE FEATURES ==="
    printf '%s\n' "${INCOMPLETE_FEATURES[@]}"
    echo ""
    echo "=== MISSING IMPLEMENTATIONS ==="
    printf '%s\n' "${MISSING_IMPLEMENTATIONS[@]}"
    echo ""
    echo "=== IMPLEMENTATION STATUS ==="
    echo "Source files: $SRC_FILES_COUNT"
    echo "Test files: $TEST_FILES_COUNT"
    echo "Doc files: $DOC_FILES_COUNT"
    echo ""
    echo "=== CONSTITUTION ANALYSIS ==="
    echo "Principles:"
    printf '  - %s\n' "${CONSTITUTION_PRINCIPLES[@]}"
    echo "Requirements:"
    printf '  - %s\n' "${CONSTITUTION_REQUIREMENTS[@]}"
    echo ""
    echo "=== GAPS IDENTIFIED ==="
    echo "Constitutional gaps:"
    printf '  - %s\n' "${CONSTITUTIONAL_GAPS[@]}"
    echo "Implementation gaps:"
    printf '  - %s\n' "${IMPLEMENTATION_GAPS[@]}"
fi