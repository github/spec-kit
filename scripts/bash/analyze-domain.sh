#!/usr/bin/env bash

set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

JSON_MODE=false
DATA_DIR=""
INTERACTIVE_MODE=false
SETUP_MODE=false
CONFIG_FILE=""
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --data-dir=*) DATA_DIR="${arg#*=}" ;;
        --interactive) INTERACTIVE_MODE=true ;;
        --setup) SETUP_MODE=true ;;
        --config=*) CONFIG_FILE="${arg#*=}" ;;
        --help|-h)
            echo "Usage: $0 [--json] [--data-dir=PATH] [--interactive] [--setup] [--config=FILE] [feature_description]"
            echo "  --json          Output results in JSON format"
            echo "  --data-dir      Specify data directory path (optional, auto-detected if not provided)"
            echo "  --interactive   Enable interactive mode for user validation and customization"
            echo "  --setup         Run setup wizard to configure domain analysis preferences"
            echo "  --config        Use configuration file with saved preferences"
            exit 0
            ;;
        *) ARGS+=("$arg") ;;
    esac
done

# Get repository paths
REPO_ROOT=$(get_repo_root)
CURRENT_BRANCH=$(get_current_branch)
HAS_GIT_REPO="false"
if has_git; then
    HAS_GIT_REPO="true"
fi

FEATURE_DIR="$REPO_ROOT/specs/$CURRENT_BRANCH"
SPEC_FILE="$FEATURE_DIR/spec.md"

# Check if we're on a valid feature branch and have a spec file
if ! check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT_REPO"; then
    if $JSON_MODE; then
        printf '{"error":"Not on a feature branch. Run /specify first."}\n'
    else
        echo "Error: Not on a feature branch. Run /specify first." >&2
    fi
    exit 1
fi

if [[ ! -f "$SPEC_FILE" ]]; then
    if $JSON_MODE; then
        printf '{"error":"Specification file not found. Run /specify first."}\n'
    else
        echo "Error: Specification file not found at $SPEC_FILE. Run /specify first." >&2
    fi
    exit 1
fi

# Auto-detect data directory if not provided
if [[ -z "$DATA_DIR" ]]; then
    # Look for common data directory patterns
    for candidate in "$REPO_ROOT/data" "$REPO_ROOT/src/data" "$REPO_ROOT/data/processed" "$REPO_ROOT/data/3_processed"; do
        if [[ -d "$candidate" ]]; then
            DATA_DIR="$candidate"
            break
        fi
    done

    # If still not found, check current working directory
    if [[ -z "$DATA_DIR" && -d "$(pwd)/data" ]]; then
        DATA_DIR="$(pwd)/data"
    fi

    # Final fallback - use repo root
    if [[ -z "$DATA_DIR" ]]; then
        DATA_DIR="$REPO_ROOT"
    fi
fi

# Verify data directory exists
if [[ ! -d "$DATA_DIR" ]]; then
    if $JSON_MODE; then
        printf '{"error":"Data directory not found: %s"}\n' "$DATA_DIR"
    else
        echo "Error: Data directory not found: $DATA_DIR" >&2
    fi
    exit 1
fi

# Scan for data files
JSON_FILES=()
CSV_FILES=()
DATA_DIRS=()

while IFS= read -r -d '' file; do
    if [[ "$file" == *.json ]]; then
        JSON_FILES+=("$file")
    elif [[ "$file" == *.csv ]]; then
        CSV_FILES+=("$file")
    fi
done < <(find "$DATA_DIR" -type f \( -name "*.json" -o -name "*.csv" \) -print0)

# Find data subdirectories
while IFS= read -r -d '' dir; do
    DATA_DIRS+=("$dir")
done < <(find "$DATA_DIR" -mindepth 1 -maxdepth 3 -type d -print0)

# Count files and directories
JSON_COUNT=${#JSON_FILES[@]}
CSV_COUNT=${#CSV_FILES[@]}
TOTAL_FILES=$((JSON_COUNT + CSV_COUNT))

# Create analysis summary
ANALYSIS_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ENTITIES_DISCOVERED=0
BUSINESS_RULES_COUNT=0
INTEGRATION_POINTS=0

# Basic entity detection from file paths
ENTITIES_LIST=""
ENTITIES_DISCOVERED=0

for file in "${JSON_FILES[@]}"; do
    basename_file=$(basename "$file" .json | tr '[:upper:]' '[:lower:]')
    # Extract potential entity names from filenames
    if [[ "$basename_file" =~ invoice ]] && [[ ! "$ENTITIES_LIST" =~ "Invoice" ]]; then
        ENTITIES_LIST="$ENTITIES_LIST Invoice"
        ((ENTITIES_DISCOVERED++))
    fi
    if [[ "$basename_file" =~ (payment|unallocated) ]] && [[ ! "$ENTITIES_LIST" =~ "Payment" ]]; then
        ENTITIES_LIST="$ENTITIES_LIST Payment"
        ((ENTITIES_DISCOVERED++))
    fi
    if [[ "$basename_file" =~ supplier ]] && [[ ! "$ENTITIES_LIST" =~ "Supplier" ]]; then
        ENTITIES_LIST="$ENTITIES_LIST Supplier"
        ((ENTITIES_DISCOVERED++))
    fi
    if [[ "$basename_file" =~ reconcil ]] && [[ ! "$ENTITIES_LIST" =~ "ReconciliationRun" ]]; then
        ENTITIES_LIST="$ENTITIES_LIST ReconciliationRun"
        ((ENTITIES_DISCOVERED++))
    fi
done

# Convert space-separated list to array for output
IFS=' ' read -ra ENTITIES_ARRAY <<< "$ENTITIES_LIST"

# Estimate business rules based on data patterns
BUSINESS_RULES_COUNT=$((ENTITIES_DISCOVERED * 2 + 3))  # Basic heuristic

# Count integration points from directory structure
for dir in "${DATA_DIRS[@]}"; do
    if [[ "$dir" =~ (processed|reports|sage|mcp) ]]; then
        ((INTEGRATION_POINTS++))
    fi
done

# Ensure at least some integration points
if [[ $INTEGRATION_POINTS -eq 0 ]]; then
    INTEGRATION_POINTS=2  # File System + MCP Server minimum
fi

# Generate output
if $JSON_MODE; then
    cat <<EOF
{
    "DATA_DIR": "$DATA_DIR",
    "FEATURE_DIR": "$FEATURE_DIR",
    "SPEC_FILE": "$SPEC_FILE",
    "interactive_mode": $INTERACTIVE_MODE,
    "setup_mode": $SETUP_MODE,
    "config_file": "$CONFIG_FILE",
    "analysis": {
        "timestamp": "$ANALYSIS_TIMESTAMP",
        "files_scanned": {
            "json_files": $JSON_COUNT,
            "csv_files": $CSV_COUNT,
            "total_files": $TOTAL_FILES
        },
        "entities_discovered": $ENTITIES_DISCOVERED,
        "business_rules_estimated": $BUSINESS_RULES_COUNT,
        "integration_points": $INTEGRATION_POINTS,
        "data_directories": $(printf '%s\n' "${DATA_DIRS[@]}" | jq -R . | jq -s .),
        "sample_json_files": $(printf '%s\n' "${JSON_FILES[@]:0:5}" | jq -R . | jq -s .),
        "entities": $(printf '%s\n' "${ENTITIES_ARRAY[@]}" | jq -R . | jq -s .)
    },
    "status": "ready_for_analysis"
}
EOF
else
    echo "DATA_DIR: $DATA_DIR"
    echo "FEATURE_DIR: $FEATURE_DIR"
    echo "SPEC_FILE: $SPEC_FILE"
    echo ""
    echo "Domain Analysis Summary:"
    echo "  JSON files found: $JSON_COUNT"
    echo "  CSV files found: $CSV_COUNT"
    echo "  Data directories: ${#DATA_DIRS[@]}"
    echo "  Entities discovered: $ENTITIES_DISCOVERED"
    echo "  Business rules estimated: $BUSINESS_RULES_COUNT"
    echo "  Integration points: $INTEGRATION_POINTS"
    echo ""
    echo "Entities detected:"
    for entity in "${ENTITIES_ARRAY[@]}"; do
        echo "  - $entity"
    done
    echo ""
    echo "Sample data files:"
    for ((i=0; i<5 && i<${#JSON_FILES[@]}; i++)); do
        echo "  - ${JSON_FILES[i]}"
    done
fi