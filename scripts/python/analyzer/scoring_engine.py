"""
Feasibility scoring engine for reverse engineering analysis.

Calculates inline upgrade and greenfield rewrite feasibility scores (0-100)
based on multiple factors including code quality, test coverage, dependencies,
architecture, and business constraints.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ProjectMetrics:
    """Container for project metrics used in scoring."""

    # Code quality metrics
    code_quality_score: float = 0.0  # 0-10 scale
    test_coverage: float = 0.0  # 0-100 percentage
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0

    # Dependency health
    total_dependencies: int = 0
    outdated_dependencies: int = 0
    vulnerable_dependencies: int = 0
    deprecated_dependencies: int = 0

    # Architecture quality
    architecture_score: float = 0.0  # 0-10 scale
    modularity_score: float = 0.0  # 0-10 scale
    coupling_level: str = "medium"  # low, medium, high

    # Team factors
    team_familiarity: float = 0.0  # 0-10 scale
    documentation_quality: float = 0.0  # 0-10 scale

    # Upgrade complexity
    breaking_changes_count: int = 0
    migration_difficulty: str = "medium"  # easy, medium, hard

    # Business constraints
    requirements_clarity: float = 0.0  # 0-10 scale
    technical_debt_percentage: float = 0.0  # 0-100 percentage
    business_continuity_risk: str = "medium"  # low, medium, high
    team_capacity_score: float = 0.0  # 0-10 scale
    time_available_weeks: int = 0
    budget_available: bool = True


@dataclass
class FeasibilityResult:
    """Container for feasibility scoring results."""

    inline_upgrade_score: float
    greenfield_rewrite_score: float
    analysis_confidence: float
    recommendation_confidence: float
    recommendation: str  # "inline_upgrade", "greenfield_rewrite", "hybrid"
    breakdown: Dict[str, float]
    rationale: str


class FeasibilityScorer:
    """
    Calculate feasibility scores for inline upgrade vs greenfield rewrite.

    Implements scoring formulas from reverse-engineering.md documentation.
    """

    def __init__(self):
        # Load weights from configuration
        weights = DEFAULT_CONFIG.scoring_weights

        # Inline upgrade weights (must sum to 1.0)
        self.inline_weights = {
            "code_quality": weights.inline_code_quality,
            "test_coverage": weights.inline_test_coverage,
            "dependency_health": weights.inline_dependency_health,
            "architecture_quality": weights.inline_architecture_quality,
            "team_familiarity": weights.inline_team_familiarity,
            "documentation": weights.inline_documentation,
            "breaking_changes": weights.inline_breaking_changes,
        }

        # Greenfield rewrite weights (must sum to 1.0)
        self.greenfield_weights = {
            "requirements_clarity": weights.greenfield_requirements_clarity,
            "technical_debt_level": weights.greenfield_technical_debt,
            "business_continuity": weights.greenfield_business_continuity,
            "team_capacity": weights.greenfield_team_capacity,
            "time_available": weights.greenfield_time_available,
            "budget": weights.greenfield_budget,
        }

        logger.debug("Initialized FeasibilityScorer with configured weights")

    def calculate_inline_upgrade_score(self, metrics: ProjectMetrics) -> tuple[float, Dict[str, float]]:
        """
        Calculate inline upgrade feasibility score (0-100).

        Formula:
        Score = (Code_Quality × 0.20) +
                (Test_Coverage × 0.15) +
                (Dependency_Health × 0.20) +
                (Architecture_Quality × 0.15) +
                (Team_Familiarity × 0.10) +
                (Documentation × 0.10) +
                (Breaking_Changes × 0.10)

        Args:
            metrics: ProjectMetrics containing all necessary data

        Returns:
            Tuple of (score, breakdown_dict)
        """
        breakdown = {}

        # Code Quality (0-10 → 0-100)
        code_quality_normalized = self._normalize_10_to_100(metrics.code_quality_score)
        breakdown["code_quality"] = code_quality_normalized * self.inline_weights["code_quality"]

        # Test Coverage (already 0-100)
        breakdown["test_coverage"] = metrics.test_coverage * self.inline_weights["test_coverage"]

        # Dependency Health (0-100)
        dependency_health = self._calculate_dependency_health(metrics)
        breakdown["dependency_health"] = dependency_health * self.inline_weights["dependency_health"]

        # Architecture Quality (0-10 → 0-100)
        arch_normalized = self._normalize_10_to_100(metrics.architecture_score)
        breakdown["architecture_quality"] = arch_normalized * self.inline_weights["architecture_quality"]

        # Team Familiarity (0-10 → 0-100)
        team_normalized = self._normalize_10_to_100(metrics.team_familiarity)
        breakdown["team_familiarity"] = team_normalized * self.inline_weights["team_familiarity"]

        # Documentation (0-10 → 0-100)
        docs_normalized = self._normalize_10_to_100(metrics.documentation_quality)
        breakdown["documentation"] = docs_normalized * self.inline_weights["documentation"]

        # Breaking Changes (inverse - fewer is better)
        breaking_changes_score = self._calculate_breaking_changes_score(metrics)
        breakdown["breaking_changes"] = breaking_changes_score * self.inline_weights["breaking_changes"]

        total_score = sum(breakdown.values())
        return round(total_score, 2), breakdown

    def calculate_greenfield_score(self, metrics: ProjectMetrics) -> tuple[float, Dict[str, float]]:
        """
        Calculate greenfield rewrite feasibility score (0-100).

        Formula:
        Score = (Requirements_Clarity × 0.20) +
                (Technical_Debt_Level × 0.20) +
                (Business_Continuity × 0.15) +
                (Team_Capacity × 0.15) +
                (Time_Available × 0.15) +
                (Budget × 0.15)

        Args:
            metrics: ProjectMetrics containing all necessary data

        Returns:
            Tuple of (score, breakdown_dict)
        """
        breakdown = {}

        # Requirements Clarity (0-10 → 0-100)
        req_normalized = self._normalize_10_to_100(metrics.requirements_clarity)
        breakdown["requirements_clarity"] = req_normalized * self.greenfield_weights["requirements_clarity"]

        # Technical Debt Level (already 0-100, higher debt = higher greenfield score)
        breakdown["technical_debt_level"] = metrics.technical_debt_percentage * self.greenfield_weights["technical_debt_level"]

        # Business Continuity (risk level → score)
        business_continuity_score = self._risk_to_score(metrics.business_continuity_risk)
        breakdown["business_continuity"] = business_continuity_score * self.greenfield_weights["business_continuity"]

        # Team Capacity (0-10 → 0-100)
        capacity_normalized = self._normalize_10_to_100(metrics.team_capacity_score)
        breakdown["team_capacity"] = capacity_normalized * self.greenfield_weights["team_capacity"]

        # Time Available (weeks → score)
        time_score = self._time_to_score(metrics.time_available_weeks)
        breakdown["time_available"] = time_score * self.greenfield_weights["time_available"]

        # Budget (boolean → score)
        budget_score = 100.0 if metrics.budget_available else 0.0
        breakdown["budget"] = budget_score * self.greenfield_weights["budget"]

        total_score = sum(breakdown.values())
        return round(total_score, 2), breakdown

    def calculate_confidence_scores(self, metrics: ProjectMetrics) -> tuple[float, float]:
        """
        Calculate confidence scores for the analysis and recommendation.

        Args:
            metrics: ProjectMetrics

        Returns:
            Tuple of (analysis_confidence, recommendation_confidence)
        """
        # Analysis confidence based on data completeness
        data_completeness_factors = [
            1.0 if metrics.test_coverage > 0 else 0.0,
            1.0 if metrics.code_quality_score > 0 else 0.0,
            1.0 if metrics.total_dependencies > 0 else 0.0,
            1.0 if metrics.architecture_score > 0 else 0.0,
            1.0 if metrics.documentation_quality > 0 else 0.0,
        ]
        analysis_confidence = (sum(data_completeness_factors) / len(data_completeness_factors)) * 100

        # Recommendation confidence based on score separation and data quality
        # Higher confidence when scores are clearly separated and data is complete
        recommendation_confidence = min(analysis_confidence + 10, 95.0)  # Cap at 95%

        return round(analysis_confidence, 2), round(recommendation_confidence, 2)

    def analyze_feasibility(self, metrics: ProjectMetrics) -> FeasibilityResult:
        """
        Perform complete feasibility analysis.

        Args:
            metrics: ProjectMetrics

        Returns:
            FeasibilityResult with scores and recommendation
        """
        inline_score, inline_breakdown = self.calculate_inline_upgrade_score(metrics)
        greenfield_score, greenfield_breakdown = self.calculate_greenfield_score(metrics)
        analysis_conf, recommendation_conf = self.calculate_confidence_scores(metrics)

        # Determine recommendation based on scores
        recommendation, rationale = self._determine_recommendation(
            inline_score, greenfield_score, metrics
        )

        # Combine breakdowns
        full_breakdown = {
            "inline": inline_breakdown,
            "greenfield": greenfield_breakdown,
        }

        return FeasibilityResult(
            inline_upgrade_score=inline_score,
            greenfield_rewrite_score=greenfield_score,
            analysis_confidence=analysis_conf,
            recommendation_confidence=recommendation_conf,
            recommendation=recommendation,
            breakdown=full_breakdown,
            rationale=rationale,
        )

    # Helper methods

    def _normalize_10_to_100(self, value: float) -> float:
        """Normalize 0-10 scale to 0-100."""
        return min(max(value * 10, 0.0), 100.0)

    def _calculate_dependency_health(self, metrics: ProjectMetrics) -> float:
        """Calculate dependency health score (0-100)."""
        if metrics.total_dependencies == 0:
            return 50.0  # Neutral score if no dependencies detected

        outdated_ratio = metrics.outdated_dependencies / metrics.total_dependencies
        vulnerable_ratio = metrics.vulnerable_dependencies / metrics.total_dependencies
        deprecated_ratio = metrics.deprecated_dependencies / metrics.total_dependencies

        # Penalize heavily for vulnerabilities, moderately for outdated/deprecated
        health_score = 100.0
        health_score -= (vulnerable_ratio * 50)  # Vulnerabilities are critical
        health_score -= (outdated_ratio * 30)
        health_score -= (deprecated_ratio * 20)

        return max(health_score, 0.0)

    def _calculate_breaking_changes_score(self, metrics: ProjectMetrics) -> float:
        """Calculate breaking changes score (0-100). Fewer breaking changes = higher score."""
        if metrics.breaking_changes_count == 0:
            return 100.0
        elif metrics.breaking_changes_count <= 5:
            return 80.0
        elif metrics.breaking_changes_count <= 10:
            return 60.0
        elif metrics.breaking_changes_count <= 20:
            return 40.0
        else:
            return 20.0

    def _risk_to_score(self, risk_level: str) -> float:
        """Convert risk level to score (low risk = high score)."""
        risk_map = {
            "low": 100.0,
            "medium": 60.0,
            "high": 30.0,
        }
        return risk_map.get(risk_level.lower(), 50.0)

    def _time_to_score(self, weeks: int) -> float:
        """Convert time available to score. More time = higher score for greenfield."""
        if weeks >= 26:  # 6+ months
            return 100.0
        elif weeks >= 13:  # 3-6 months
            return 80.0
        elif weeks >= 8:  # 2-3 months
            return 60.0
        elif weeks >= 4:  # 1-2 months
            return 40.0
        else:
            return 20.0

    def _determine_recommendation(
        self, inline_score: float, greenfield_score: float, metrics: ProjectMetrics
    ) -> tuple[str, str]:
        """
        Determine recommendation based on scores.

        Returns:
            Tuple of (recommendation, rationale)
        """
        # Load thresholds from configuration
        thresholds = DEFAULT_CONFIG.score_thresholds

        INLINE_HIGHLY_FEASIBLE = thresholds.inline_highly_feasible
        INLINE_FEASIBLE = thresholds.inline_feasible
        INLINE_RISKY = thresholds.inline_risky

        GREENFIELD_STRONG = thresholds.greenfield_strong
        GREENFIELD_VIABLE = thresholds.greenfield_viable
        GREENFIELD_CHALLENGING = thresholds.greenfield_challenging

        # Decision logic
        if inline_score >= INLINE_HIGHLY_FEASIBLE and inline_score > greenfield_score:
            return "inline_upgrade", (
                f"Highly feasible inline upgrade (score: {inline_score}/100). "
                f"Code quality is acceptable, test coverage adequate, and upgrade path clear."
            )

        elif greenfield_score >= GREENFIELD_STRONG and greenfield_score > inline_score + 10:
            return "greenfield_rewrite", (
                f"Strong candidate for greenfield rewrite (score: {greenfield_score}/100). "
                f"High technical debt ({metrics.technical_debt_percentage}%) and inline upgrade "
                f"score too low ({inline_score}/100)."
            )

        elif inline_score >= INLINE_FEASIBLE and inline_score >= greenfield_score:
            return "inline_upgrade", (
                f"Feasible inline upgrade with caution (score: {inline_score}/100). "
                f"Assess risks carefully and plan for potential challenges."
            )

        elif (INLINE_RISKY <= inline_score < INLINE_FEASIBLE and
              GREENFIELD_CHALLENGING <= greenfield_score < GREENFIELD_VIABLE):
            return "hybrid", (
                f"Hybrid approach recommended (inline: {inline_score}/100, greenfield: {greenfield_score}/100). "
                f"Both options are moderately risky. Consider Strangler Fig pattern: "
                f"incrementally extract and modernize components while maintaining parallel systems."
            )

        elif greenfield_score >= GREENFIELD_VIABLE:
            return "greenfield_rewrite", (
                f"Greenfield rewrite recommended (score: {greenfield_score}/100). "
                f"Inline upgrade too risky ({inline_score}/100)."
            )

        else:
            return "inline_upgrade", (
                f"Default to inline upgrade (inline: {inline_score}/100, greenfield: {greenfield_score}/100). "
                f"Both options have challenges, but inline upgrade has lower risk and faster time to value."
            )


def main():
    """Example usage of FeasibilityScorer."""
    # Example: Legacy Node.js app
    metrics = ProjectMetrics(
        code_quality_score=6.0,
        test_coverage=38.0,
        lines_of_code=15000,
        total_dependencies=54,
        outdated_dependencies=47,
        vulnerable_dependencies=7,
        deprecated_dependencies=3,
        architecture_score=7.0,
        modularity_score=6.5,
        team_familiarity=8.0,
        documentation_quality=5.0,
        breaking_changes_count=12,
        requirements_clarity=7.0,
        technical_debt_percentage=35.0,
        team_capacity_score=7.0,
        time_available_weeks=8,
        budget_available=True,
    )

    scorer = FeasibilityScorer()
    result = scorer.analyze_feasibility(metrics)

    print(f"=== Feasibility Analysis Results ===")
    print(f"Inline Upgrade Score: {result.inline_upgrade_score}/100")
    print(f"Greenfield Rewrite Score: {result.greenfield_rewrite_score}/100")
    print(f"Analysis Confidence: {result.analysis_confidence}/100")
    print(f"Recommendation Confidence: {result.recommendation_confidence}/100")
    print(f"\nRecommendation: {result.recommendation.upper()}")
    print(f"Rationale: {result.rationale}")
    print(f"\nInline Breakdown:")
    for factor, score in result.breakdown["inline"].items():
        print(f"  {factor}: {score:.2f}")
    print(f"\nGreenfield Breakdown:")
    for factor, score in result.breakdown["greenfield"].items():
        print(f"  {factor}: {score:.2f}")


if __name__ == "__main__":
    main()
