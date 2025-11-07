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

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --check-patterns)
            CHECK_PATTERNS=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: project-analysis.sh [OPTIONS]

Perform comprehensive project analysis against all SpecKit specifications.

OPTIONS:
  --json              Output in JSON format
  --check-patterns    Enable code pattern analysis (Security, DRY, KISS, SOLID)
  --help, -h          Show this help message

EXAMPLES:
  # Basic project analysis
  ./project-analysis.sh --json

  # Analysis with pattern checking
  ./project-analysis.sh --json --check-patterns

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

# Get repository root
REPO_ROOT=$(get_repo_root)
SPECS_DIR="$REPO_ROOT/specs"
CONSTITUTION_FILE="$REPO_ROOT/memory/constitution.md"

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

# Output in JSON format
if $JSON_MODE; then
    printf '{'
    printf '"repo_root":"%s",' "$REPO_ROOT"
    printf '"specs_dir":"%s",' "$SPECS_DIR"
    printf '"constitution_exists":%s,' "$CONSTITUTION_EXISTS"
    printf '"constitution_file":"%s",' "$CONSTITUTION_FILE"
    printf '"pattern_check_enabled":%s,' "$CHECK_PATTERNS"
    printf '"detected_languages":"%s",' "$DETECTED_LANGUAGES"
    printf '"source_dirs":"%s",' "$SOURCE_DIRS"
    printf '"total_specs":%d,' "${#SORTED_SPECS[@]}"
    printf '"specs":['

    first=true
    for spec_name in "${SORTED_SPECS[@]}"; do
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

        printf '{'
        printf '"name":"%s",' "$spec_name"
        printf '"dir":"%s",' "$spec_dir"
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
    echo "Total Specifications: ${#SORTED_SPECS[@]}"
    echo ""

    for spec_name in "${SORTED_SPECS[@]}"; do
        spec_dir="$SPECS_DIR/$spec_name"
        echo "[$spec_name]"
        echo "  spec.md:       $(check_spec_file "$spec_dir" "spec.md")"
        echo "  plan.md:       $(check_spec_file "$spec_dir" "plan.md")"
        echo "  tasks.md:      $(check_spec_file "$spec_dir" "tasks.md")"
        echo "  research.md:   $(check_spec_file "$spec_dir" "research.md")"
        echo "  data-model.md: $(check_spec_file "$spec_dir" "data-model.md")"
        echo ""
    done
fi
