"""
Shared context for Phase 7 analysis generators.

Centralizes common state to reduce parameter passing and improve maintainability.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

# Handle both relative and absolute imports
try:
    from .scanner import ScanResult
    from .dependency_analyzer import DependencyReport
    from .scoring_engine import ProjectMetrics
except ImportError:
    from scanner import ScanResult
    from dependency_analyzer import DependencyReport
    from scoring_engine import ProjectMetrics


@dataclass
class AnalysisContext:
    """
    Shared context for all Phase 7 generators.

    Centralizes common data to reduce parameter passing across generators
    and provide single source of truth for analysis metadata.

    Attributes:
        scan_result: Results from ProjectScanner
        dependency_reports: Results from DependencyAnalyzer
        metrics: ProjectMetrics from scoring engine
        project_name: Name of the project being analyzed
        analysis_date: ISO 8601 formatted date (YYYY-MM-DD)
    """

    scan_result: ScanResult
    dependency_reports: List[DependencyReport]
    metrics: ProjectMetrics
    project_name: str
    analysis_date: str

    @classmethod
    def create(
        cls,
        scan_result: ScanResult,
        dependency_reports: List[DependencyReport],
        metrics: ProjectMetrics,
        project_name: str
    ) -> "AnalysisContext":
        """
        Factory method to create AnalysisContext with auto-generated date.

        Args:
            scan_result: Results from ProjectScanner
            dependency_reports: Results from DependencyAnalyzer
            metrics: ProjectMetrics from scoring engine
            project_name: Name of the project

        Returns:
            AnalysisContext instance with current date
        """
        return cls(
            scan_result=scan_result,
            dependency_reports=dependency_reports,
            metrics=metrics,
            project_name=project_name,
            analysis_date=datetime.now().strftime("%Y-%m-%d")
        )


def main():
    """Example usage of AnalysisContext."""
    print("AnalysisContext module loaded successfully")
    print("This module provides shared context for Phase 7 generators")


if __name__ == "__main__":
    main()
