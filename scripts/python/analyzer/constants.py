"""
Constants and thresholds for analyzer modules.

Centralizes magic numbers to improve code clarity and enable easy tuning.
"""


class QuirkThresholds:
    """Thresholds for identifying legacy quirks and issues."""

    # Dependency thresholds
    OUTDATED_DEPENDENCIES_MANY = 10  # Threshold for "many" outdated packages
    VULNERABLE_DEPENDENCIES_CRITICAL = 10  # Threshold for critical security concern
    TOTAL_DEPENDENCIES_MANY = 50  # Threshold for "many" total dependencies

    # Code quality thresholds
    LOW_TEST_COVERAGE = 60  # Below this is considered low coverage
    EXCELLENT_TEST_COVERAGE = 80  # At or above is excellent
    HIGH_TECH_DEBT = 40  # Above this percentage is high technical debt

    # Code quality scoring
    CODE_QUALITY_GOOD = 7.0  # Score threshold for "good" quality
    CODE_QUALITY_EXCELLENT = 8.5  # Score threshold for "excellent" quality

    # Modularity and architecture
    LOW_MODULARITY = 5  # Below this score indicates low modularity
    GOOD_MODULARITY = 6  # At or above indicates good separation
    EXCELLENT_MODULARITY = 7  # At or above indicates excellent structure


class ProjectSizeThresholds:
    """Thresholds for project size categorization."""

    # Lines of code thresholds
    SMALL_PROJECT_LOC = 10_000  # Less than this is small
    MEDIUM_PROJECT_LOC = 50_000  # Less than this is medium (up to this)
    LARGE_PROJECT_LOC = 100_000  # Less than this is large (up to this)
    # Above LARGE is "very large"

    # For complexity assessment
    LARGE_CODEBASE_INCREMENTAL = 50_000  # Above this, recommend incremental migration


class ComplexityScoreWeights:
    """Weights for calculating overall complexity scores."""

    # Complexity calculation weights (should sum to 1.0)
    LINES_OF_CODE_WEIGHT = 0.3  # Impact of project size
    TECHNICAL_DEBT_WEIGHT = 0.3  # Impact of technical debt
    MODULARITY_WEIGHT = 0.2  # Impact of modularity (inverted)
    DEPENDENCY_WEIGHT = 0.2  # Impact of dependency count

    # Complexity score thresholds
    HIGH_COMPLEXITY_THRESHOLD = 7  # Above this is high complexity
    MEDIUM_COMPLEXITY_THRESHOLD = 4  # Above this is medium complexity


class MigrationComplexity:
    """Migration complexity assessment levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MEDIUM_HIGH = "MEDIUM-HIGH"  # For border cases


class MigrationEffortEstimates:
    """Time estimates for various migration scenarios."""

    # Small projects (< 10K LOC)
    SMALL_INLINE_WEEKS = "2-4 weeks"
    SMALL_GREENFIELD_MONTHS = "2-3 months"
    SMALL_HYBRID_MONTHS = "3-4 months"

    # Medium projects (10K-50K LOC)
    MEDIUM_INLINE_MONTHS = "2-3 months"
    MEDIUM_GREENFIELD_MONTHS = "4-6 months"
    MEDIUM_HYBRID_MONTHS = "5-8 months"

    # Large projects (50K+ LOC)
    LARGE_INLINE_MONTHS = "4-6 months"
    LARGE_GREENFIELD_MONTHS = "6-12 months"
    LARGE_HYBRID_MONTHS = "8-18 months"

    # Foundation setup
    FOUNDATION_WITH_CI_WEEKS = "1 week"
    FOUNDATION_WITHOUT_CI_WEEKS = "1-2 weeks"

    # Testing and QA
    TESTING_PHASE_WEEKS = "2-4 weeks"


class FeatureCriticality:
    """Feature criticality levels for modernization."""

    CRITICAL = "CRITICAL"  # Must preserve exactly
    STANDARD = "STANDARD"  # Can modernize implementation
    LEGACY_QUIRKS = "LEGACY QUIRKS"  # Decide preserve vs. fix


class SecurityPriority:
    """Security issue priority levels."""

    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"  # Address soon
    MODERATE = "MODERATE"  # Address during modernization


class DocumentationQuality:
    """Documentation quality thresholds."""

    POOR = 3.0  # Below this is poor documentation
    ACCEPTABLE = 6.0  # At or above is acceptable
    GOOD = 8.0  # At or above is good documentation


class PerformanceConstants:
    """Constants related to performance optimization."""

    # Parallelization thresholds
    MIN_FILES_FOR_PARALLEL = 100  # Below this, parallel processing not worth it
    PARALLEL_WORKER_COUNT = 4  # Default worker count for parallel processing

    # Memory thresholds
    MAX_FILE_SIZE_MEMORY_MB = 100  # Above this, consider streaming
    MAX_TOTAL_OUTPUT_SIZE_MB = 100  # Above this, use streaming writes


class LTSGuidance:
    """
    Guidance for LTS version recommendations.

    Note: Actual version numbers should come from AI knowledge base.
    This class provides guidance on how to present LTS information.
    """

    # Standard phrasing for AI-driven recommendations
    RECOMMEND_LATEST_LTS = "Recommend latest LTS version available as of analysis date"
    RECOMMEND_LATEST_STABLE = "Recommend latest stable version (no formal LTS)"
    CHECK_OFFICIAL_DOCS = "Verify current LTS status from official documentation"

    # Common LTS support durations (for context)
    PYTHON_SUPPORT_YEARS = 5  # Python LTS support duration
    NODE_LTS_SUPPORT_YEARS = 3  # Node.js LTS support duration
    JAVA_LTS_SUPPORT_YEARS = 8  # Java LTS support duration
    DOTNET_LTS_SUPPORT_YEARS = 3  # .NET LTS support duration


def main():
    """Example usage of constants."""
    print("Constants module loaded successfully")
    print(f"Low test coverage threshold: {QuirkThresholds.LOW_TEST_COVERAGE}%")
    print(f"Small project size: < {ProjectSizeThresholds.SMALL_PROJECT_LOC:,} LOC")


if __name__ == "__main__":
    main()
