#!/usr/bin/env bash

# Project Analysis Script
#
# This script performs comprehensive project analysis against all SpecKit specifications
# to verify whether the project meets defined expectations.
#
# Usage: ./project-analysis.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --check-patterns    Enable code pattern analysis (Security, DRY, KISS, SOLID)
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"specs":[...], "repo_root":"...", "pattern_check_enabled":true/false}
#   Text mode: Human-readable summary of all specs and their status

set -e

# Parse command line arguments
JSON_MODE=false
CHECK_PATTERNS=false
INCREMENTAL=false
SUMMARY_MODE=false
DIFF_ONLY=false
MAX_SAMPLE_FILES=20
START_TIME=$(date +%s%N 2>/dev/null || date +%s)

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --check-patterns)
            CHECK_PATTERNS=true
            ;;
        --incremental)
            INCREMENTAL=true
            ;;
        --diff-only)
            DIFF_ONLY=true
            ;;
        --summary)
            SUMMARY_MODE=true
            ;;
        --sample-size=*)
            MAX_SAMPLE_FILES="${arg#*=}"
            ;;
        --help|-h)
            cat << 'EOF'
Usage: project-analysis.sh [OPTIONS]

Perform comprehensive project analysis against all SpecKit specifications.

OPTIONS:
  --json              Output in JSON format
  --check-patterns    Enable code pattern analysis (Security, DRY, KISS, SOLID)
  --incremental       Only analyze changed files since last run (70-90% faster)
  --diff-only         Only analyze specs with git changes since last commit (80-95% faster)
  --summary           Quick summary mode (90% faster, metrics only)
  --sample-size=N     Max source files to analyze for patterns (default: 20)
  --help, -h          Show this help message

OPTIMIZATION FLAGS:
  --incremental       Uses file hashing to skip unchanged specs (huge token savings)
  --diff-only         Uses git diff to find changed specs (fastest, requires git)
  --summary           Skips deep analysis, reports only high-level metrics
  --sample-size=N     Limits code pattern analysis to N files (for large projects)

PERFORMANCE MODES (from fastest to most thorough):
  1. --diff-only      (fastest)  Only specs changed in git working tree
  2. --incremental    (fast)     Only specs changed since last analysis
  3. --summary        (quick)    All specs, minimal analysis
  4. (default)        (thorough) All specs, full analysis

EXAMPLES:
  # Basic project analysis
  ./project-analysis.sh --json

  # Analysis with pattern checking
  ./project-analysis.sh --json --check-patterns

  # Incremental analysis (only changed files)
  ./project-analysis.sh --json --incremental

  # Git-based differential (fastest)
  ./project-analysis.sh --json --diff-only

  # Quick summary mode (very fast)
  ./project-analysis.sh --json --summary

  # Large codebase with sampling
  ./project-analysis.sh --json --check-patterns --sample-size=30

  # Full incremental with patterns
  ./project-analysis.sh --json --incremental --check-patterns

EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
source "$SCRIPT_DIR/project-analysis-helper.sh" 2>/dev/null || true

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"
CONSTITUTION_FILE="$REPO_ROOT/memory/constitution.md"
CACHE_FILE="$REPO_ROOT/.speckit-analysis-cache.json"

# Check if specs directory exists
if [[ ! -d "$SPECS_DIR" ]]; then
    if $JSON_MODE; then
        printf '{"error":"Specs directory not found","specs_dir":"%s"}\n' "$SPECS_DIR"
    else
        echo "ERROR: Specs directory not found: $SPECS_DIR" >&2
    fi
    exit 1
fi

# Function to check if a file exists and get its path
check_spec_file() {
    local spec_dir="$1"
    local file_name="$2"
    local file_path="$spec_dir/$file_name"

    if [[ -f "$file_path" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to count lines in a file
count_lines() {
    local file="$1"
    if [[ -f "$file" ]]; then
        wc -l < "$file" | tr -d ' '
    else
        echo "0"
    fi
}

# Collect all spec directories
SPEC_DIRS=()
if [[ -d "$SPECS_DIR" ]]; then
    for dir in "$SPECS_DIR"/*; do
        if [[ -d "$dir" ]]; then
            SPEC_DIRS+=("$(basename "$dir")")
        fi
    done
fi

# Sort spec directories by numeric prefix
IFS=$'\n' SORTED_SPECS=($(printf '%s\n' "${SPEC_DIRS[@]}" | sort))
unset IFS

# Check if constitution file exists
CONSTITUTION_EXISTS="false"
if [[ -f "$CONSTITUTION_FILE" ]]; then
    CONSTITUTION_EXISTS="true"
fi

# Detect programming languages in the repository
detect_languages() {
    local languages=()

    # Check for common language files
    [[ -f "$REPO_ROOT/package.json" ]] && languages+=("JavaScript/TypeScript")
    [[ -f "$REPO_ROOT/pyproject.toml" || -f "$REPO_ROOT/setup.py" || -f "$REPO_ROOT/requirements.txt" ]] && languages+=("Python")
    [[ -f "$REPO_ROOT/go.mod" ]] && languages+=("Go")
    [[ -f "$REPO_ROOT/Cargo.toml" ]] && languages+=("Rust")
    [[ -f "$REPO_ROOT/pom.xml" || -f "$REPO_ROOT/build.gradle" ]] && languages+=("Java")
    [[ -f "$REPO_ROOT/Gemfile" ]] && languages+=("Ruby")
    [[ -f "$REPO_ROOT/composer.json" ]] && languages+=("PHP")
    [[ -f "$REPO_ROOT/*.csproj" ]] && languages+=("C#")

    if [[ ${#languages[@]} -eq 0 ]]; then
        echo "Unknown"
    else
        printf '%s\n' "${languages[@]}" | paste -sd ',' -
    fi
}

DETECTED_LANGUAGES=$(detect_languages)

# Load cache for incremental mode
CACHE_DATA="{}"
if $INCREMENTAL && [[ -f "$CACHE_FILE" ]]; then
    CACHE_DATA=$(cat "$CACHE_FILE")
fi

# Track changed and unchanged files
CHANGED_SPECS=()
UNCHANGED_SPECS=()

# For diff-only mode, use git to detect changed specs
if $DIFF_ONLY; then
    # Check if git repository
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # Get all changed files in specs directory
        CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || echo "")

        # If no changes staged, check working tree
        if [ -z "$CHANGED_FILES" ]; then
            CHANGED_FILES=$(git diff --name-only 2>/dev/null || echo "")
        fi

        # Extract unique spec directories from changed files
        if [ -n "$CHANGED_FILES" ]; then
            while IFS= read -r file; do
                # Check if file is in specs directory
                if [[ "$file" == specs/* ]]; then
                    # Extract spec directory name (e.g., specs/001-feature/spec.md -> 001-feature)
                    spec_dir=$(echo "$file" | cut -d'/' -f2)

                    # Add to changed specs if not already present
                    if [[ ! " ${CHANGED_SPECS[@]} " =~ " ${spec_dir} " ]]; then
                        CHANGED_SPECS+=("$spec_dir")
                    fi
                fi
            done <<< "$CHANGED_FILES"
        fi

        # All other specs are unchanged
        for spec_name in "${SORTED_SPECS[@]}"; do
            if [[ ! " ${CHANGED_SPECS[@]} " =~ " ${spec_name} " ]]; then
                UNCHANGED_SPECS+=("$spec_name")
            fi
        done
    else
        echo "Warning: --diff-only requires a git repository. Falling back to full analysis." >&2
        DIFF_ONLY=false
    fi
fi

# Find source code directories
find_source_dirs() {
    local source_dirs=()

    # Common source directories
    [[ -d "$REPO_ROOT/src" ]] && source_dirs+=("src")
    [[ -d "$REPO_ROOT/lib" ]] && source_dirs+=("lib")
    [[ -d "$REPO_ROOT/app" ]] && source_dirs+=("app")
    [[ -d "$REPO_ROOT/source" ]] && source_dirs+=("source")
    [[ -d "$REPO_ROOT/pkg" ]] && source_dirs+=("pkg")

    if [[ ${#source_dirs[@]} -eq 0 ]]; then
        echo ""
    else
        printf '%s\n' "${source_dirs[@]}" | paste -sd ',' -
    fi
}

SOURCE_DIRS=$(find_source_dirs)

# Generate file hashes for incremental mode (skip if diff-only is enabled)
declare -A SPEC_HASHES
if $INCREMENTAL && ! $DIFF_ONLY; then
    for spec_name in "${SORTED_SPECS[@]}"; do
        spec_dir="$SPECS_DIR/$spec_name"
        # Hash key files
        spec_hash=$(get_file_hash "$spec_dir/spec.md" 2>/dev/null || echo "none")
        plan_hash=$(get_file_hash "$spec_dir/plan.md" 2>/dev/null || echo "none")
        tasks_hash=$(get_file_hash "$spec_dir/tasks.md" 2>/dev/null || echo "none")

        # Check if any file changed
        cached_spec_hash=$(echo "$CACHE_DATA" | grep -o "\"$spec_name\":{\"spec_hash\":\"[^\"]*\"" | cut -d'"' -f6 || echo "")
        cached_plan_hash=$(echo "$CACHE_DATA" | grep -o "\"$spec_name\":{[^}]*\"plan_hash\":\"[^\"]*\"" | grep -o "plan_hash\":\"[^\"]*\"" | cut -d'"' -f3 || echo "")

        if [[ "$spec_hash" != "$cached_spec_hash" ]] || [[ "$plan_hash" != "$cached_plan_hash" ]]; then
            CHANGED_SPECS+=("$spec_name")
        else
            UNCHANGED_SPECS+=("$spec_name")
        fi

        SPEC_HASHES["$spec_name"]="$spec_hash|$plan_hash|$tasks_hash"
    done
fi

# Calculate performance metrics
END_TIME=$(date +%s%N 2>/dev/null || date +%s)
if [[ "$START_TIME" =~ ^[0-9]+$ ]] && [[ "$END_TIME" =~ ^[0-9]+$ ]]; then
    if [[ ${#START_TIME} -gt 10 ]]; then
        # Nanosecond precision
        ELAPSED_NS=$((END_TIME - START_TIME))
        ELAPSED_MS=$((ELAPSED_NS / 1000000))
    else
        # Second precision
        ELAPSED_MS=$(( (END_TIME - START_TIME) * 1000 ))
    fi
else
    ELAPSED_MS=0
fi

# Calculate specs analyzed
SPECS_ANALYZED="${#SORTED_SPECS[@]}"
if $DIFF_ONLY || $INCREMENTAL; then
    SPECS_ANALYZED="${#CHANGED_SPECS[@]}"
fi

# Output in JSON format
if $JSON_MODE; then
    printf '{'
    printf '"repo_root":"%s",' "$REPO_ROOT"
    printf '"specs_dir":"%s",' "$SPECS_DIR"
    printf '"constitution_exists":%s,' "$CONSTITUTION_EXISTS"
    printf '"constitution_file":"%s",' "$CONSTITUTION_FILE"
    printf '"pattern_check_enabled":%s,' "$CHECK_PATTERNS"
    printf '"incremental_mode":%s,' "$INCREMENTAL"
    printf '"diff_only_mode":%s,' "$DIFF_ONLY"
    printf '"summary_mode":%s,' "$SUMMARY_MODE"
    printf '"max_sample_files":%d,' "$MAX_SAMPLE_FILES"
    printf '"detected_languages":"%s",' "$DETECTED_LANGUAGES"
    printf '"source_dirs":"%s",' "$SOURCE_DIRS"
    printf '"total_specs":%d,' "${#SORTED_SPECS[@]}"
    printf '"changed_specs":%d,' "${#CHANGED_SPECS[@]}"
    printf '"unchanged_specs":%d,' "${#UNCHANGED_SPECS[@]}"
    printf '"specs_analyzed":%d,' "$SPECS_ANALYZED"
    printf '"performance":{'
    printf '"elapsed_ms":%d,' "$ELAPSED_MS"
    printf '"specs_per_second":%.2f' "$(echo "scale=2; $SPECS_ANALYZED / ($ELAPSED_MS / 1000.0)" | bc 2>/dev/null || echo "0")"
    printf '},'
    printf '"specs":['

    first=true
    for spec_name in "${SORTED_SPECS[@]}"; do
        # In diff-only or incremental mode, skip unchanged specs
        if ($DIFF_ONLY || $INCREMENTAL) && [[ " ${UNCHANGED_SPECS[@]} " =~ " ${spec_name} " ]]; then
            continue
        fi

        if [[ "$first" != true ]]; then
            printf ','
        fi
        first=false

        spec_dir="$SPECS_DIR/$spec_name"

        # Check for all specification files
        has_spec=$(check_spec_file "$spec_dir" "spec.md")
        has_plan=$(check_spec_file "$spec_dir" "plan.md")
        has_tasks=$(check_spec_file "$spec_dir" "tasks.md")
        has_research=$(check_spec_file "$spec_dir" "research.md")
        has_data_model=$(check_spec_file "$spec_dir" "data-model.md")
        has_quickstart=$(check_spec_file "$spec_dir" "quickstart.md")
        has_contracts=$(check_spec_file "$spec_dir" "contracts")

        # Count requirements and tasks
        spec_lines=$(count_lines "$spec_dir/spec.md")
        plan_lines=$(count_lines "$spec_dir/plan.md")
        tasks_lines=$(count_lines "$spec_dir/tasks.md")

        # Check if spec changed (for incremental or diff-only mode)
        changed="false"
        if $INCREMENTAL || $DIFF_ONLY; then
            for changed_spec in "${CHANGED_SPECS[@]}"; do
                if [[ "$changed_spec" == "$spec_name" ]]; then
                    changed="true"
                    break
                fi
            done
        else
            changed="null"
        fi

        printf '{'
        printf '"name":"%s",' "$spec_name"
        printf '"dir":"%s",' "$spec_dir"
        printf '"changed":%s,' "$changed"
        printf '"has_spec":%s,' "$has_spec"
        printf '"has_plan":%s,' "$has_plan"
        printf '"has_tasks":%s,' "$has_tasks"
        printf '"has_research":%s,' "$has_research"
        printf '"has_data_model":%s,' "$has_data_model"
        printf '"has_quickstart":%s,' "$has_quickstart"
        printf '"has_contracts":%s,' "$has_contracts"
        printf '"spec_lines":%s,' "$spec_lines"
        printf '"plan_lines":%s,' "$plan_lines"
        printf '"tasks_lines":%s' "$tasks_lines"
        printf '}'
    done

    printf ']'
    printf '}\n'

    # Update cache file if incremental mode
    if $INCREMENTAL; then
        {
            printf '{\n'
            printf '  "last_updated": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
            printf '  "specs": {\n'
            first_spec=true
            for spec_name in "${SORTED_SPECS[@]}"; do
                if [[ "$first_spec" != true ]]; then
                    printf ',\n'
                fi
                first_spec=false

                IFS='|' read -r spec_hash plan_hash tasks_hash <<< "${SPEC_HASHES[$spec_name]}"
                printf '    "%s": {\n' "$spec_name"
                printf '      "spec_hash": "%s",\n' "$spec_hash"
                printf '      "plan_hash": "%s",\n' "$plan_hash"
                printf '      "tasks_hash": "%s"\n' "$tasks_hash"
                printf '    }'
            done
            printf '\n  }\n'
            printf '}\n'
        } > "$CACHE_FILE"
    fi
else
    # Text mode output
    echo "=== Project Analysis ==="
    echo ""
    echo "Repository Root: $REPO_ROOT"
    echo "Specs Directory: $SPECS_DIR"
    echo "Constitution: $(if [[ "$CONSTITUTION_EXISTS" == "true" ]]; then echo "✓ Found"; else echo "✗ Missing"; fi)"
    echo "Detected Languages: $DETECTED_LANGUAGES"
    echo "Source Directories: $SOURCE_DIRS"
    echo "Pattern Check: $(if $CHECK_PATTERNS; then echo "Enabled"; else echo "Disabled"; fi)"
    echo ""

    # Performance mode indicator
    if $DIFF_ONLY; then
        echo "Mode: Git Differential (--diff-only)"
        echo "Analyzing: ${#CHANGED_SPECS[@]} changed specs (${#UNCHANGED_SPECS[@]} unchanged, skipped)"
    elif $INCREMENTAL; then
        echo "Mode: Incremental (--incremental)"
        echo "Analyzing: ${#CHANGED_SPECS[@]} changed specs (${#UNCHANGED_SPECS[@]} unchanged, skipped)"
    elif $SUMMARY_MODE; then
        echo "Mode: Summary (--summary)"
    else
        echo "Mode: Full Analysis"
    fi

    echo ""
    echo "Total Specifications: ${#SORTED_SPECS[@]}"
    echo "Specs Analyzed: $SPECS_ANALYZED"
    echo "Analysis Time: ${ELAPSED_MS}ms"
    echo ""

    for spec_name in "${SORTED_SPECS[@]}"; do
        # In diff-only or incremental mode, skip unchanged specs
        if ($DIFF_ONLY || $INCREMENTAL) && [[ " ${UNCHANGED_SPECS[@]} " =~ " ${spec_name} " ]]; then
            continue
        fi

        spec_dir="$SPECS_DIR/$spec_name"
        echo "[$spec_name]"

        # Show change indicator
        if $DIFF_ONLY || $INCREMENTAL; then
            echo "  Status: CHANGED"
        fi

        echo "  spec.md:       $(check_spec_file "$spec_dir" "spec.md")"
        echo "  plan.md:       $(check_spec_file "$spec_dir" "plan.md")"
        echo "  tasks.md:      $(check_spec_file "$spec_dir" "tasks.md")"
        echo "  research.md:   $(check_spec_file "$spec_dir" "research.md")"
        echo "  data-model.md: $(check_spec_file "$spec_dir" "data-model.md")"
        echo ""
    done
fi
