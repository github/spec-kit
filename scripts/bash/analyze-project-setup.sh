#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
PROJECT_PATH=""
ANALYSIS_DEPTH="STANDARD"
FOCUS_AREAS="ALL"

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--project PATH] [--depth LEVEL] [--focus AREAS]"
            echo "  --json         Output results in JSON format"
            echo "  --project      Path to project to analyze (required)"
            echo "  --depth        Analysis depth: QUICK|STANDARD|COMPREHENSIVE (default: STANDARD)"
            echo "  --focus        Focus areas: ALL|SECURITY|PERFORMANCE|ARCHITECTURE|DEPENDENCIES (default: ALL)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        --project)
            shift
            PROJECT_PATH="$1"
            ;;
        --depth)
            shift
            ANALYSIS_DEPTH="$1"
            ;;
        --focus)
            shift
            FOCUS_AREAS="$1"
            ;;
    esac
    shift 2>/dev/null || true
done

# Get repository root (where this script is run from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Validate PROJECT_PATH
if [[ -z "$PROJECT_PATH" ]]; then
    echo "ERROR: --project PATH is required" >&2
    echo "Use --help for usage information" >&2
    exit 1
fi

# Convert to absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd || echo "$PROJECT_PATH")"

if [[ ! -d "$PROJECT_PATH" ]]; then
    echo "ERROR: Project path does not exist or is not accessible: $PROJECT_PATH" >&2
    exit 1
fi

# Validate ANALYSIS_DEPTH
if [[ ! "$ANALYSIS_DEPTH" =~ ^(QUICK|STANDARD|COMPREHENSIVE)$ ]]; then
    echo "ERROR: Invalid analysis depth: $ANALYSIS_DEPTH" >&2
    echo "Must be one of: QUICK, STANDARD, COMPREHENSIVE" >&2
    exit 1
fi

# Validate FOCUS_AREAS
if [[ ! "$FOCUS_AREAS" =~ ^(ALL|SECURITY|PERFORMANCE|ARCHITECTURE|DEPENDENCIES)$ ]]; then
    echo "ERROR: Invalid focus area: $FOCUS_AREAS" >&2
    echo "Must be one of: ALL, SECURITY, PERFORMANCE, ARCHITECTURE, DEPENDENCIES" >&2
    exit 1
fi

# Extract project name from path
PROJECT_NAME="$(basename "$PROJECT_PATH")"

# Create timestamp for this analysis
TIMESTAMP="$(date +%Y-%m-%d-%H%M%S)"

# Create analysis directory structure
ANALYSIS_ROOT="$REPO_ROOT/.analysis"
ANALYSIS_DIR="$ANALYSIS_ROOT/${PROJECT_NAME}-${TIMESTAMP}"

mkdir -p "$ANALYSIS_DIR"
mkdir -p "$ANALYSIS_DIR/checkpoints"

# Define output file paths
ANALYSIS_REPORT="$ANALYSIS_DIR/analysis-report.md"
UPGRADE_PLAN="$ANALYSIS_DIR/upgrade-plan.md"
RECOMMENDED_CONSTITUTION="$ANALYSIS_DIR/recommended-constitution.md"
RECOMMENDED_SPEC="$ANALYSIS_DIR/recommended-spec.md"
DEPENDENCY_AUDIT="$ANALYSIS_DIR/dependency-audit.json"
METRICS_SUMMARY="$ANALYSIS_DIR/metrics-summary.json"
DECISION_MATRIX="$ANALYSIS_DIR/decision-matrix.md"

# Copy templates to analysis directory (if they exist)
TEMPLATES_DIR="$REPO_ROOT/.specify/templates"

if [[ -f "$TEMPLATES_DIR/analysis-report-template.md" ]]; then
    cp "$TEMPLATES_DIR/analysis-report-template.md" "$ANALYSIS_REPORT"
fi

if [[ -f "$TEMPLATES_DIR/upgrade-plan-template.md" ]]; then
    cp "$TEMPLATES_DIR/upgrade-plan-template.md" "$UPGRADE_PLAN"
fi

if [[ -f "$TEMPLATES_DIR/reverse-engineering-constitution-template.md" ]]; then
    cp "$TEMPLATES_DIR/reverse-engineering-constitution-template.md" "$RECOMMENDED_CONSTITUTION"
fi

# Check if we have git in the target project (optional)
TARGET_HAS_GIT="false"
if (cd "$PROJECT_PATH" && git rev-parse --show-toplevel >/dev/null 2>&1); then
    TARGET_HAS_GIT="true"
fi

# Run Python analyzer if available
PYTHON_ANALYZER_AVAILABLE="false"
PYTHON_ANALYSIS_STATUS="not_run"
PYTHON_ANALYSIS_ERROR=""

# Check if python3 is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON_ANALYZER_AVAILABLE="true"

    # Try to run the Python analyzer
    echo "Running Python analyzer..." >&2

    if python3 -m scripts.python.analyzer \
        --project "$PROJECT_PATH" \
        --output "$ANALYSIS_DIR" \
        --depth "$ANALYSIS_DEPTH" \
        --focus "$FOCUS_AREAS" \
        --json 2>&1 | tee "$ANALYSIS_DIR/analyzer-log.txt" | tail -n 20; then

        PYTHON_ANALYSIS_STATUS="success"
        echo "✓ Python analyzer completed successfully" >&2
    else
        PYTHON_ANALYSIS_STATUS="failed"
        PYTHON_ANALYSIS_ERROR="Python analyzer failed - see analyzer-log.txt"
        echo "⚠ Python analyzer failed - will use AI-guided analysis fallback" >&2
    fi
else
    echo "⚠ Python3 not available - will use AI-guided analysis" >&2
fi

# Output results
if $JSON_MODE; then
    printf '{"PROJECT_PATH":"%s","PROJECT_NAME":"%s","ANALYSIS_DIR":"%s","ANALYSIS_REPORT":"%s","UPGRADE_PLAN":"%s","RECOMMENDED_CONSTITUTION":"%s","RECOMMENDED_SPEC":"%s","DEPENDENCY_AUDIT":"%s","METRICS_SUMMARY":"%s","DECISION_MATRIX":"%s","ANALYSIS_DEPTH":"%s","FOCUS_AREAS":"%s","TARGET_HAS_GIT":"%s","TIMESTAMP":"%s","PYTHON_ANALYZER_AVAILABLE":"%s","PYTHON_ANALYSIS_STATUS":"%s","PYTHON_ANALYSIS_ERROR":"%s"}\n' \
        "$PROJECT_PATH" "$PROJECT_NAME" "$ANALYSIS_DIR" "$ANALYSIS_REPORT" "$UPGRADE_PLAN" "$RECOMMENDED_CONSTITUTION" "$RECOMMENDED_SPEC" "$DEPENDENCY_AUDIT" "$METRICS_SUMMARY" "$DECISION_MATRIX" "$ANALYSIS_DEPTH" "$FOCUS_AREAS" "$TARGET_HAS_GIT" "$TIMESTAMP" "$PYTHON_ANALYZER_AVAILABLE" "$PYTHON_ANALYSIS_STATUS" "$PYTHON_ANALYSIS_ERROR"
else
    echo "PROJECT_PATH: $PROJECT_PATH"
    echo "PROJECT_NAME: $PROJECT_NAME"
    echo "ANALYSIS_DIR: $ANALYSIS_DIR"
    echo "ANALYSIS_REPORT: $ANALYSIS_REPORT"
    echo "UPGRADE_PLAN: $UPGRADE_PLAN"
    echo "RECOMMENDED_CONSTITUTION: $RECOMMENDED_CONSTITUTION"
    echo "RECOMMENDED_SPEC: $RECOMMENDED_SPEC"
    echo "DEPENDENCY_AUDIT: $DEPENDENCY_AUDIT"
    echo "METRICS_SUMMARY: $METRICS_SUMMARY"
    echo "DECISION_MATRIX: $DECISION_MATRIX"
    echo "ANALYSIS_DEPTH: $ANALYSIS_DEPTH"
    echo "FOCUS_AREAS: $FOCUS_AREAS"
    echo "TARGET_HAS_GIT: $TARGET_HAS_GIT"
    echo "TIMESTAMP: $TIMESTAMP"
    echo "PYTHON_ANALYZER_AVAILABLE: $PYTHON_ANALYZER_AVAILABLE"
    echo "PYTHON_ANALYSIS_STATUS: $PYTHON_ANALYSIS_STATUS"
    echo "PYTHON_ANALYSIS_ERROR: $PYTHON_ANALYSIS_ERROR"
fi
