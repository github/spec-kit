#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
PROJECT_PATH=""

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--project PATH]"
            echo "  --json         Output results in JSON format"
            echo "  --project      Path to project to analyze (required)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        --project)
            shift
            PROJECT_PATH="$1"
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
# Note: upgrade-plan.md and recommended-constitution.md removed in Phase 8
# Replaced by stage-prompts/ directory and new workflow artifacts
RECOMMENDED_SPEC="$ANALYSIS_DIR/recommended-spec.md"
DEPENDENCY_AUDIT="$ANALYSIS_DIR/dependency-audit.json"
METRICS_SUMMARY="$ANALYSIS_DIR/metrics-summary.json"
DECISION_MATRIX="$ANALYSIS_DIR/decision-matrix.md"

# Copy templates to analysis directory (if they exist)
TEMPLATES_DIR="$REPO_ROOT/.specify/templates"

if [[ -f "$TEMPLATES_DIR/analysis-report-template.md" ]]; then
    cp "$TEMPLATES_DIR/analysis-report-template.md" "$ANALYSIS_REPORT"
fi

# Phase 8: upgrade-plan and recommended-constitution templates removed
# These have been replaced by stage-prompts/ directory with 6 prompt files

# Check if we have git in the target project (optional)
TARGET_HAS_GIT="false"
if (cd "$PROJECT_PATH" && git rev-parse --show-toplevel >/dev/null 2>&1); then
    TARGET_HAS_GIT="true"
fi

# Output results
if $JSON_MODE; then
    printf '{"PROJECT_PATH":"%s","PROJECT_NAME":"%s","ANALYSIS_DIR":"%s","ANALYSIS_REPORT":"%s","RECOMMENDED_SPEC":"%s","DEPENDENCY_AUDIT":"%s","METRICS_SUMMARY":"%s","DECISION_MATRIX":"%s","TARGET_HAS_GIT":"%s","TIMESTAMP":"%s"}\n' \
        "$PROJECT_PATH" "$PROJECT_NAME" "$ANALYSIS_DIR" "$ANALYSIS_REPORT" "$RECOMMENDED_SPEC" "$DEPENDENCY_AUDIT" "$METRICS_SUMMARY" "$DECISION_MATRIX" "$TARGET_HAS_GIT" "$TIMESTAMP"
else
    echo "PROJECT_PATH: $PROJECT_PATH"
    echo "PROJECT_NAME: $PROJECT_NAME"
    echo "ANALYSIS_DIR: $ANALYSIS_DIR"
    echo "ANALYSIS_REPORT: $ANALYSIS_REPORT"
    echo "RECOMMENDED_SPEC: $RECOMMENDED_SPEC"
    echo "DEPENDENCY_AUDIT: $DEPENDENCY_AUDIT"
    echo "METRICS_SUMMARY: $METRICS_SUMMARY"
    echo "DECISION_MATRIX: $DECISION_MATRIX"
    echo "TARGET_HAS_GIT: $TARGET_HAS_GIT"
    echo "TIMESTAMP: $TIMESTAMP"
fi
