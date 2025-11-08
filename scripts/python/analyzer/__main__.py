#!/usr/bin/env python3
"""
Main entry point for project analyzer CLI.

Usage:
    python -m scripts.python.analyzer --project /path/to/project --output /path/to/output

This orchestrates the full analysis workflow:
1. Project scanning (tech stack, metrics, structure)
2. Dependency analysis (npm, pip, vulnerabilities)
3. Feasibility scoring (inline upgrade vs greenfield rewrite)
4. Report generation (markdown reports)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .scanner import ProjectScanner
from .dependency_analyzer import DependencyAnalyzer
from .scoring_engine import FeasibilityScorer, ProjectMetrics
from .report_generator import ReportGenerator, ReportConfig
from .config import DEFAULT_CONFIG
from .security import SecurityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze an existing project for modernization opportunities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python -m scripts.python.analyzer --project /path/to/project --output /path/to/output

  # With custom depth and focus
  python -m scripts.python.analyzer --project /path/to/project --output /path/to/output --depth COMPREHENSIVE --focus SECURITY

Analysis Depths:
  QUICK         - Surface-level scan (30 min)
  STANDARD      - Full codebase analysis (2-4 hours)
  COMPREHENSIVE - Deep dive with detailed profiling (1-2 days)

Focus Areas:
  ALL           - Complete analysis (default)
  SECURITY      - Focus on vulnerabilities and dependencies
  PERFORMANCE   - Focus on bottlenecks and optimization
  ARCHITECTURE  - Focus on design patterns and technical debt
  DEPENDENCIES  - Focus on package analysis and upgrades
        """
    )

    parser.add_argument(
        '--project',
        type=str,
        required=True,
        help='Path to project root directory'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output directory for reports'
    )

    parser.add_argument(
        '--depth',
        type=str,
        default='STANDARD',
        choices=['QUICK', 'STANDARD', 'COMPREHENSIVE'],
        help='Analysis depth (default: STANDARD)'
    )

    parser.add_argument(
        '--focus',
        type=str,
        default='ALL',
        choices=['ALL', 'SECURITY', 'PERFORMANCE', 'ARCHITECTURE', 'DEPENDENCIES'],
        help='Focus areas (default: ALL)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON summary to stdout'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def main():
    """Main entry point for analyzer CLI."""
    args = parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate and resolve paths
    try:
        project_path = Path(args.project).resolve()
        if not project_path.exists():
            logger.error(f"Project path does not exist: {args.project}")
            sys.exit(1)
        if not project_path.is_dir():
            logger.error(f"Project path is not a directory: {args.project}")
            sys.exit(1)
    except (OSError, RuntimeError) as e:
        logger.error(f"Cannot access project path: {e}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    try:
        output_path = Path(args.output).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create output directory: {e}")
        sys.exit(1)

    project_name = project_path.name

    logger.info(f"Starting analysis of: {project_path}")
    logger.info(f"Analysis depth: {args.depth}")
    logger.info(f"Focus areas: {args.focus}")
    logger.info(f"Output directory: {output_path}")

    try:
        # Phase 1: Project Scanning
        logger.info("Phase 1: Scanning project...")
        scanner = ProjectScanner(project_path)
        scan_result = scanner.scan_project()

        if not scan_result.scan_successful:
            logger.error(f"Project scan failed: {scan_result.error_message}")
            sys.exit(1)

        logger.info(f"✓ Detected {scan_result.tech_stack.primary_language} project")
        logger.info(f"✓ Found {scan_result.metrics.code_lines:,} lines of code")

        # Phase 2: Dependency Analysis
        logger.info("Phase 2: Analyzing dependencies...")
        dep_analyzer = DependencyAnalyzer(project_path)
        dependency_reports = dep_analyzer.analyze_dependencies()

        vulnerable_count = sum(r.vulnerable_count for r in dependency_reports)
        outdated_count = sum(r.outdated_count for r in dependency_reports)

        if vulnerable_count > 0:
            logger.warning(f"⚠ Found {vulnerable_count} vulnerable dependencies")
        if outdated_count > 0:
            logger.info(f"ℹ Found {outdated_count} outdated dependencies")

        # Phase 3: Calculate Metrics
        logger.info("Phase 3: Calculating project metrics...")

        # Build ProjectMetrics from scan results
        metrics = ProjectMetrics(
            lines_of_code=scan_result.metrics.code_lines,
            test_coverage=50.0 if scan_result.structure.has_tests else 0.0,  # Estimate
            code_quality_score=7.0 if scan_result.structure.has_documentation else 5.0,  # Estimate
            technical_debt_percentage=40.0 if not scan_result.structure.has_tests else 20.0,  # Estimate
            documentation_quality=8.0 if scan_result.structure.has_documentation else 3.0,
            modularity_score=7.0 if len(scan_result.structure.source_dirs) > 0 else 4.0,
            architecture_score=7.0 if scan_result.structure.has_documentation else 5.0,  # Estimate
            outdated_dependencies=outdated_count,
            vulnerable_dependencies=vulnerable_count,
            total_dependencies=sum(r.total_dependencies for r in dependency_reports),
            deprecated_dependencies=sum(r.deprecated_count for r in dependency_reports),
            team_familiarity=5.0,  # Default neutral score
            requirements_clarity=5.0,  # Default neutral score
            business_continuity_risk="medium",  # Default
            team_capacity_score=5.0,  # Default neutral score
            time_available_weeks=12,  # Default 3 months
            budget_available=True  # Assume budget available
        )

        # Phase 4: Feasibility Scoring
        logger.info("Phase 4: Calculating feasibility scores...")
        scorer = FeasibilityScorer()
        feasibility_result = scorer.analyze_feasibility(metrics)

        logger.info(f"✓ Inline upgrade score: {feasibility_result.inline_upgrade_score}/100")
        logger.info(f"✓ Greenfield rewrite score: {feasibility_result.greenfield_rewrite_score}/100")
        logger.info(f"✓ Recommendation: {feasibility_result.recommendation.upper()}")

        # Phase 5: Generate Reports
        logger.info("Phase 5: Generating reports...")

        report_config = ReportConfig(
            project_name=project_name,
            project_path=project_path,
            output_dir=output_path,
            analysis_depth=args.depth,
            focus_areas=[args.focus]
        )

        generator = ReportGenerator(report_config)
        generated_files = generator.generate_all_reports(
            scan_result=scan_result,
            dependency_reports=dependency_reports,
            feasibility_result=feasibility_result,
            metrics=metrics
        )

        logger.info(f"✓ Generated {len(generated_files)} reports")

        # Save JSON summaries
        dependency_audit_path = output_path / "dependency-audit.json"
        metrics_summary_path = output_path / "metrics-summary.json"

        try:
            with open(dependency_audit_path, 'w', encoding='utf-8') as f:
                dep_summary = {
                    "reports": [
                        {
                            "ecosystem": r.ecosystem,
                            "total": r.total_dependencies,
                            "outdated": r.outdated_count,
                            "vulnerable": r.vulnerable_count,
                            "deprecated": r.deprecated_count,
                            "issues": [
                                {
                                    "package": i.package_name,
                                    "current_version": i.current_version,
                                    "latest_version": i.latest_version,
                                    "severity": i.severity,
                                    "type": i.issue_type,
                                    "cve": i.cve
                                }
                                for i in r.issues[:10]  # Top 10 issues
                            ]
                        }
                        for r in dependency_reports
                    ]
                }
                json.dump(dep_summary, f, indent=2)
            logger.info(f"✓ Saved dependency audit to: {dependency_audit_path}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to save dependency audit: {e}")
            # Continue execution - this is not critical

        try:
            with open(metrics_summary_path, 'w', encoding='utf-8') as f:
                metrics_summary = {
                    "lines_of_code": metrics.lines_of_code,
                    "file_count": scan_result.metrics.file_count,
                    "test_coverage": metrics.test_coverage,
                    "code_quality_score": metrics.code_quality_score,
                    "technical_debt_percentage": metrics.technical_debt_percentage,
                    "modularity_score": metrics.modularity_score,
                    "architecture_score": metrics.architecture_score,
                    "has_ci_cd": scan_result.structure.has_ci_cd,
                    "has_tests": scan_result.structure.has_tests,
                    "total_dependencies": metrics.total_dependencies,
                    "outdated_dependencies": metrics.outdated_dependencies,
                    "vulnerable_dependencies": metrics.vulnerable_dependencies,
                    "deprecated_dependencies": metrics.deprecated_dependencies,
                    "tech_stack": {
                        "primary_language": scan_result.tech_stack.primary_language,
                        "languages": scan_result.tech_stack.languages,
                        "frameworks": scan_result.tech_stack.frameworks,
                        "build_tools": scan_result.tech_stack.build_tools,
                        "runtime_version": scan_result.tech_stack.runtime_version
                    }
                }
                json.dump(metrics_summary, f, indent=2)
            logger.info(f"✓ Saved metrics summary to: {metrics_summary_path}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to save metrics summary: {e}")
            # Continue execution - this is not critical

        # Output JSON summary if requested
        if args.json:
            summary = {
                "status": "success",
                "project_name": project_name,
                "project_path": str(project_path),
                "output_dir": str(output_path),
                "recommendation": feasibility_result.recommendation,
                "inline_upgrade_score": feasibility_result.inline_upgrade_score,
                "greenfield_rewrite_score": feasibility_result.greenfield_rewrite_score,
                "confidence": feasibility_result.recommendation_confidence,
                "generated_files": [str(f) for f in generated_files],
                "metrics": {
                    "lines_of_code": metrics.lines_of_code,
                    "vulnerable_dependencies": vulnerable_count,
                    "outdated_dependencies": outdated_count
                }
            }
            print(json.dumps(summary, indent=2))

        logger.info("=" * 60)
        logger.info("Analysis complete!")
        logger.info(f"Reports saved to: {output_path}")
        logger.info(f"Primary recommendation: {feasibility_result.recommendation.upper()}")
        logger.info("=" * 60)

        return 0

    except SecurityError as e:
        logger.error(f"Security error: {e}")
        sys.exit(2)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(3)

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        sys.exit(4)

    except Exception as e:
        logger.exception(f"Unexpected error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
