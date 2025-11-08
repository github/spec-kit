#!/usr/bin/env bash

#
# analyze-project.sh - Main orchestration script for Reverse Engineering & Modernization
#
# Usage:
#   ./analyze-project.sh [PROJECT_PATH] [OPTIONS]
#
# Options:
#   --depth DEPTH       Analysis depth: QUICK, STANDARD, COMPREHENSIVE (default: STANDARD)
#   --focus AREAS       Focus areas: ALL, SECURITY, DEPENDENCIES, PERFORMANCE (default: ALL)
#   --output DIR        Output directory (default: .analysis/PROJECT_NAME-TIMESTAMP)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ANALYSIS_DEPTH="STANDARD"
FOCUS_AREAS="ALL"
OUTPUT_DIR=""
PROJECT_PATH=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANALYZER_DIR="$REPO_ROOT/scripts/python/analyzer"

# Functions

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

usage() {
    cat <<EOF
Usage: $0 [PROJECT_PATH] [OPTIONS]

Analyze an existing codebase for reverse engineering and modernization planning.

Arguments:
  PROJECT_PATH         Path to project root directory (default: current directory)

Options:
  --depth DEPTH        Analysis depth: QUICK, STANDARD, COMPREHENSIVE (default: STANDARD)
  --focus AREAS        Focus areas: ALL, SECURITY, DEPENDENCIES, PERFORMANCE (default: ALL)
  --output DIR         Output directory (default: .analysis/PROJECT_NAME-TIMESTAMP)
  -h, --help           Show this help message

Examples:
  # Analyze current directory with standard depth
  $0 .

  # Analyze specific project with comprehensive depth
  $0 /path/to/project --depth COMPREHENSIVE

  # Focus on security and dependencies only
  $0 /path/to/project --focus SECURITY,DEPENDENCIES

  # Custom output directory
  $0 /path/to/project --output /tmp/analysis-results

Analysis Depths:
  QUICK         - Basic scan (30 minutes)
  STANDARD      - Comprehensive analysis (2-4 hours) [RECOMMENDED]
  COMPREHENSIVE - Deep analysis with all features (1-2 days)

Focus Areas:
  ALL           - Analyze everything (default)
  SECURITY      - Security vulnerabilities and CVEs
  DEPENDENCIES  - Dependency health and outdated packages
  PERFORMANCE   - Performance bottlenecks
  ARCHITECTURE  - Architecture and code quality

Output:
  The script generates multiple markdown reports in the output directory:
  - analysis-report.md          Main comprehensive report
  - upgrade-plan.md             Step-by-step upgrade instructions (if inline upgrade)
  - recommended-constitution.md Suggested principles (if greenfield rewrite)
  - decision-matrix.md          Stakeholder-friendly comparison table

EOF
    exit 0
}

check_dependencies() {
    print_header "Checking Dependencies"

    local missing_deps=0

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        missing_deps=1
    else
        print_success "Python 3 found: $(python3 --version)"
    fi

    # Check optional tools
    if command -v npm &> /dev/null; then
        print_success "npm found: $(npm --version)"
    else
        print_warning "npm not found - Node.js project analysis will be limited"
    fi

    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        print_success "pip found"
    else
        print_warning "pip not found - Python project analysis will be limited"
    fi

    if command -v cloc &> /dev/null; then
        print_success "cloc found - will use for code metrics"
    elif command -v tokei &> /dev/null; then
        print_success "tokei found - will use for code metrics"
    else
        print_warning "cloc/tokei not found - code metrics will be estimated"
        print_info "Install cloc: sudo apt-get install cloc  OR  brew install cloc"
        print_info "Install tokei: cargo install tokei"
    fi

    if [ $missing_deps -eq 1 ]; then
        print_error "Missing required dependencies. Please install and try again."
        exit 1
    fi

    echo ""
}

validate_project_path() {
    print_header "Validating Project Path"

    if [ ! -d "$PROJECT_PATH" ]; then
        print_error "Project path does not exist: $PROJECT_PATH"
        exit 1
    fi

    PROJECT_PATH="$(cd "$PROJECT_PATH" && pwd)"
    print_success "Project path: $PROJECT_PATH"

    # Detect project name
    PROJECT_NAME=$(basename "$PROJECT_PATH")
    print_success "Project name: $PROJECT_NAME"

    echo ""
}

setup_output_directory() {
    print_header "Setting Up Output Directory"

    if [ -z "$OUTPUT_DIR" ]; then
        TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
        OUTPUT_DIR="$PROJECT_PATH/.analysis/$PROJECT_NAME-$TIMESTAMP"
    fi

    mkdir -p "$OUTPUT_DIR"
    print_success "Output directory: $OUTPUT_DIR"

    echo ""
}

run_analysis() {
    print_header "Running Analysis"

    print_info "This may take a while depending on project size..."
    print_info "Analysis depth: $ANALYSIS_DEPTH"
    print_info "Focus areas: $FOCUS_AREAS"

    # Create Python script to run the full analysis
    # Use single quotes to prevent variable expansion (security)
    cat > "$OUTPUT_DIR/run_analysis.py" <<'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Orchestration script for running complete project analysis.
"""

import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Parse arguments - analyzer_dir now passed as argument for security
    if len(sys.argv) < 5:
        print("Usage: run_analysis.py ANALYZER_DIR PROJECT_PATH OUTPUT_DIR PROJECT_NAME [DEPTH] [FOCUS]")
        sys.exit(1)

    analyzer_dir = Path(sys.argv[1])
    project_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])
    project_name = sys.argv[4]
    analysis_depth = sys.argv[5] if len(sys.argv) > 5 else "STANDARD"
    focus_areas = sys.argv[6].split(",") if len(sys.argv) > 6 else ["ALL"]

    # Add analyzer to path
    sys.path.insert(0, str(analyzer_dir))

    from scanner import ProjectScanner
    from dependency_analyzer import DependencyAnalyzer
    from scoring_engine import FeasibilityScorer, ProjectMetrics
    from report_generator import ReportGenerator, ReportConfig

    print(f"\n📊 Analyzing: {project_name}")
    print(f"📂 Path: {project_path}")
    print(f"📁 Output: {output_dir}\n")

    # Step 1: Scan project
    print("🔍 Step 1/4: Scanning project...")
    scanner = ProjectScanner(project_path)
    scan_result = scanner.scan_project()

    if not scan_result.scan_successful:
        print(f"❌ Scan failed: {scan_result.error_message}")
        sys.exit(1)

    print(f"   ✓ Detected: {scan_result.tech_stack.primary_language}")
    print(f"   ✓ Files: {scan_result.metrics.file_count}")
    print(f"   ✓ Lines of code: {scan_result.metrics.code_lines:,}")

    # Step 2: Analyze dependencies
    print("\n📦 Step 2/4: Analyzing dependencies...")
    dep_analyzer = DependencyAnalyzer(project_path)
    dependency_reports = dep_analyzer.analyze_dependencies()

    total_outdated = sum(r.outdated_count for r in dependency_reports)
    total_vulnerable = sum(r.vulnerable_count for r in dependency_reports)
    print(f"   ✓ Ecosystems analyzed: {len(dependency_reports)}")
    print(f"   ✓ Outdated dependencies: {total_outdated}")
    print(f"   ✓ Vulnerable dependencies: {total_vulnerable}")

    if total_vulnerable > 0:
        print(f"   ⚠️  {total_vulnerable} security vulnerabilities found!")

    # Step 3: Calculate feasibility scores
    print("\n📈 Step 3/4: Calculating feasibility scores...")

    # Build metrics from scan results
    total_deps = sum(r.total_dependencies for r in dependency_reports)
    outdated_deps = sum(r.outdated_count for r in dependency_reports)
    vulnerable_deps = sum(r.vulnerable_count for r in dependency_reports)
    deprecated_deps = sum(r.deprecated_count for r in dependency_reports)

    # Estimate metrics (these would ideally come from deeper analysis)
    code_quality = 7.0 if scan_result.structure.has_tests else 5.0
    test_coverage = 60.0 if scan_result.structure.has_tests else 0.0
    architecture_score = 7.0 if scan_result.structure.has_ci_cd else 5.0
    tech_debt_pct = 30.0 if code_quality >= 7 else 50.0

    metrics = ProjectMetrics(
        code_quality_score=code_quality,
        test_coverage=test_coverage,
        lines_of_code=scan_result.metrics.code_lines,
        total_dependencies=total_deps,
        outdated_dependencies=outdated_deps,
        vulnerable_dependencies=vulnerable_deps,
        deprecated_dependencies=deprecated_deps,
        architecture_score=architecture_score,
        modularity_score=6.5,
        team_familiarity=7.0,
        documentation_quality=7.0 if scan_result.structure.has_documentation else 4.0,
        breaking_changes_count=5,
        requirements_clarity=7.0,
        technical_debt_percentage=tech_debt_pct,
        team_capacity_score=7.0,
        time_available_weeks=12,
        budget_available=True,
    )

    scorer = FeasibilityScorer()
    feasibility_result = scorer.analyze_feasibility(metrics)

    print(f"   ✓ Inline upgrade score: {feasibility_result.inline_upgrade_score}/100")
    print(f"   ✓ Greenfield rewrite score: {feasibility_result.greenfield_rewrite_score}/100")
    print(f"   ✓ Recommendation: {feasibility_result.recommendation.upper().replace('_', ' ')}")
    print(f"   ✓ Confidence: {feasibility_result.recommendation_confidence:.0f}%")

    # Step 4: Generate reports
    print("\n📄 Step 4/4: Generating reports...")

    config = ReportConfig(
        project_name=project_name,
        project_path=project_path,
        output_dir=output_dir,
        analysis_depth=analysis_depth,
        focus_areas=focus_areas,
    )

    generator = ReportGenerator(config)
    generated_files = generator.generate_all_reports(
        scan_result, dependency_reports, feasibility_result, metrics
    )

    print(f"   ✓ Generated {len(generated_files)} report(s):")
    for file_path in generated_files:
        print(f"     - {file_path.name}")

    # Save metrics to JSON for tooling integration
    metrics_file = output_dir / "metrics-summary.json"
    with open(metrics_file, "w") as f:
        json.dump({
            "project_name": project_name,
            "analysis_date": str(Path(output_dir).name.split("-", 1)[1] if "-" in Path(output_dir).name else ""),
            "tech_stack": {
                "primary_language": scan_result.tech_stack.primary_language,
                "languages": scan_result.tech_stack.languages,
                "frameworks": scan_result.tech_stack.frameworks,
            },
            "metrics": {
                "total_lines": scan_result.metrics.total_lines,
                "code_lines": scan_result.metrics.code_lines,
                "file_count": scan_result.metrics.file_count,
                "test_coverage": metrics.test_coverage,
            },
            "dependencies": {
                "total": total_deps,
                "outdated": outdated_deps,
                "vulnerable": vulnerable_deps,
                "deprecated": deprecated_deps,
            },
            "feasibility": {
                "inline_upgrade_score": feasibility_result.inline_upgrade_score,
                "greenfield_rewrite_score": feasibility_result.greenfield_rewrite_score,
                "recommendation": feasibility_result.recommendation,
                "confidence": feasibility_result.recommendation_confidence,
            },
        }, f, indent=2)

    print(f"   ✓ Metrics saved to: metrics-summary.json")

    print("\n✅ Analysis complete!")
    print(f"\n📋 Results saved to: {output_dir}")
    print(f"\n📖 Next steps:")
    print(f"   1. Review analysis-report.md")
    if feasibility_result.recommendation == "inline_upgrade":
        print(f"   2. Review upgrade-plan.md for step-by-step instructions")
    elif feasibility_result.recommendation == "greenfield_rewrite":
        print(f"   2. Review recommended-constitution.md for principles")
    else:
        print(f"   2. Review both upgrade-plan.md and recommended-constitution.md")
    print(f"   3. Review decision-matrix.md with stakeholders")
    print(f"   4. Make final decision and execute plan")


if __name__ == "__main__":
    main()
PYTHON_SCRIPT

    # Make it executable
    chmod +x "$OUTPUT_DIR/run_analysis.py"

    # Run the analysis (pass analyzer_dir as first argument for security)
    python3 "$OUTPUT_DIR/run_analysis.py" \
        "$ANALYZER_DIR" \
        "$PROJECT_PATH" \
        "$OUTPUT_DIR" \
        "$PROJECT_NAME" \
        "$ANALYSIS_DEPTH" \
        "$FOCUS_AREAS" || {
        print_error "Analysis failed"
        exit 1
    }

    echo ""
}

show_summary() {
    print_header "Analysis Summary"

    if [ -f "$OUTPUT_DIR/metrics-summary.json" ]; then
        print_success "Analysis completed successfully!"
        echo ""
        print_info "Generated Reports:"
        ls -lh "$OUTPUT_DIR"/*.md 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
        echo ""
        print_info "Metrics Summary:"
        cat "$OUTPUT_DIR/metrics-summary.json" | python3 -m json.tool 2>/dev/null || cat "$OUTPUT_DIR/metrics-summary.json"
        echo ""
    else
        print_error "No summary file generated"
    fi

    echo ""
    print_success "🎉 All done! Review the reports in: $OUTPUT_DIR"
}

# Main script

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                ;;
            --depth)
                ANALYSIS_DEPTH="$2"
                shift 2
                ;;
            --focus)
                FOCUS_AREAS="$2"
                shift 2
                ;;
            --output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            *)
                if [ -z "$PROJECT_PATH" ]; then
                    PROJECT_PATH="$1"
                else
                    print_error "Unknown option: $1"
                    usage
                fi
                shift
                ;;
        esac
    done

    # Default project path to current directory
    if [ -z "$PROJECT_PATH" ]; then
        PROJECT_PATH="."
    fi

    # Validate depth
    if [[ ! "$ANALYSIS_DEPTH" =~ ^(QUICK|STANDARD|COMPREHENSIVE)$ ]]; then
        print_error "Invalid depth: $ANALYSIS_DEPTH"
        print_info "Valid options: QUICK, STANDARD, COMPREHENSIVE"
        exit 1
    fi

    # Welcome message
    print_header "Reverse Engineering & Modernization Analysis"
    echo ""

    # Run workflow
    check_dependencies
    validate_project_path
    setup_output_directory
    run_analysis
    show_summary

    exit 0
}

main "$@"
