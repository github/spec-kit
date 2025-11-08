"""
Configuration management for reverse engineering analyzer.

Centralizes all magic numbers, thresholds, and weights for easy tuning.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoringWeights:
    """Weights for feasibility scoring (must sum to 1.0)."""

    # Inline upgrade weights
    inline_code_quality: float = 0.20
    inline_test_coverage: float = 0.15
    inline_dependency_health: float = 0.20
    inline_architecture_quality: float = 0.15
    inline_team_familiarity: float = 0.10
    inline_documentation: float = 0.10
    inline_breaking_changes: float = 0.10

    # Greenfield rewrite weights
    greenfield_requirements_clarity: float = 0.20
    greenfield_technical_debt: float = 0.20
    greenfield_business_continuity: float = 0.15
    greenfield_team_capacity: float = 0.15
    greenfield_time_available: float = 0.15
    greenfield_budget: float = 0.15


@dataclass
class ScoreThresholds:
    """Thresholds for interpreting feasibility scores."""

    # Inline upgrade thresholds
    inline_highly_feasible: int = 80
    inline_feasible: int = 60
    inline_risky: int = 40

    # Greenfield rewrite thresholds
    greenfield_strong: int = 80
    greenfield_viable: int = 60
    greenfield_challenging: int = 40

    # Test coverage thresholds
    test_coverage_good: int = 60
    test_coverage_excellent: int = 80

    # Code quality thresholds
    code_quality_good: float = 7.0
    code_quality_excellent: float = 8.5


@dataclass
class SecurityConfig:
    """Security configuration for safe analysis."""

    # Maximum timeout for subprocess calls (seconds)
    subprocess_timeout_default: int = 60
    subprocess_timeout_long: int = 120
    subprocess_timeout_quick: int = 10

    # Forbidden paths that should never be analyzed
    forbidden_paths: tuple = (
        '/bin', '/sbin', '/usr/bin', '/usr/sbin',
        '/etc', '/var', '/sys', '/proc', '/dev',
        '/boot', '/root', '/tmp', '/System', '/Windows'
    )

    # Maximum project size (lines of code)
    max_project_size_lines: int = 10_000_000  # 10M LOC

    # Maximum file size to read (bytes)
    max_file_size_bytes: int = 10_000_000  # 10MB


@dataclass
class AnalyzerConfig:
    """Main analyzer configuration."""

    scoring_weights: ScoringWeights
    score_thresholds: ScoreThresholds
    security: SecurityConfig

    @classmethod
    def default(cls) -> "AnalyzerConfig":
        """Create default configuration."""
        return cls(
            scoring_weights=ScoringWeights(),
            score_thresholds=ScoreThresholds(),
            security=SecurityConfig(),
        )


# Global default configuration
DEFAULT_CONFIG = AnalyzerConfig.default()
