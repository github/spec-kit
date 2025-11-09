"""
Tech stack proposer with AI-driven LTS recommendations.

Generates proposed-tech-stack.md with guidance for AI to determine latest LTS
versions and detailed rationale for each technology choice.

Design Philosophy:
- Provide documentation URLs and guidance for AI agents
- AI determines latest LTS versions using its knowledge base
- No hardcoded version numbers that require maintenance
- Focus on rationale and migration complexity assessment
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Handle both relative and absolute imports
try:
    from .analysis_context import AnalysisContext
    from .constants import (
        LTSGuidance,
        ProjectSizeThresholds,
        MigrationComplexity,
        QuirkThresholds
    )
except ImportError:
    from analysis_context import AnalysisContext
    from constants import (
        LTSGuidance,
        ProjectSizeThresholds,
        MigrationComplexity,
        QuirkThresholds
    )


@dataclass
class TechRecommendation:
    """Recommendation for a specific technology component."""

    component_type: str  # "Language", "Framework", "Database", etc.
    current: str
    proposed_guidance: str  # AI guidance for determining version
    rationale: List[str]
    migration_complexity: str  # LOW, MEDIUM, HIGH
    documentation_url: str
    alternatives: List[Tuple[str, str]]  # [(name, reason), ...]


class TechStackProposer:
    """
    Propose modernized tech stack with AI-driven LTS recommendations.

    Uses AI knowledge base to determine latest LTS versions rather than
    maintaining hardcoded version data.
    """

    # Documentation URLs for AI to reference when determining LTS versions
    LANGUAGE_DOCS = {
        "python": "https://www.python.org/downloads/",
        "javascript": "https://nodejs.org/en/about/releases/",
        "node": "https://nodejs.org/en/about/releases/",
        "java": "https://www.oracle.com/java/technologies/java-se-support-roadmap.html",
        "csharp": "https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core",
        "dotnet": "https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core",
        "go": "https://go.dev/dl/",
        "ruby": "https://www.ruby-lang.org/en/downloads/",
        "php": "https://www.php.net/supported-versions.php",
        "rust": "https://www.rust-lang.org/",
    }

    FRAMEWORK_DOCS = {
        "react": "https://react.dev/",
        "vue": "https://vuejs.org/",
        "angular": "https://angular.io/",
        "express": "https://expressjs.com/",
        "fastapi": "https://fastapi.tiangolo.com/",
        "django": "https://www.djangoproject.com/",
        "flask": "https://flask.palletsprojects.com/",
        "spring-boot": "https://spring.io/projects/spring-boot",
        "rails": "https://rubyonrails.org/",
        "laravel": "https://laravel.com/",
        "aspnet": "https://dotnet.microsoft.com/apps/aspnet",
    }

    DATABASE_DOCS = {
        "postgresql": "https://www.postgresql.org/support/versioning/",
        "mysql": "https://www.mysql.com/support/",
        "mongodb": "https://www.mongodb.com/",
        "redis": "https://redis.io/",
        "mariadb": "https://mariadb.org/",
        "sqlite": "https://www.sqlite.org/",
    }

    def __init__(self, context: AnalysisContext):
        """
        Initialize tech stack proposer.

        Args:
            context: Shared analysis context with scan results and metrics
        """
        self.context = context

    def generate_proposed_stack(self, output_path: Path) -> Path:
        """
        Generate proposed-tech-stack.md file.

        Args:
            output_path: Path where the file should be written

        Returns:
            Path to the generated file
        """
        sections = []

        # Header
        sections.append(self._build_header())

        # Executive Summary
        sections.append(self._build_executive_summary())

        # Build recommendations
        recommendations = self._build_recommendations()

        # Language & Runtime
        if recommendations.get("language"):
            sections.append(self._format_recommendation(recommendations["language"]))

        # Framework
        if recommendations.get("framework"):
            sections.append(self._format_recommendation(recommendations["framework"]))

        # Database
        if recommendations.get("database"):
            sections.append(self._format_recommendation(recommendations["database"]))

        # Summary Table
        sections.append(self._build_summary_table(recommendations))

        # Migration Strategy
        sections.append(self._build_migration_strategy())

        # How to Use
        sections.append(self._build_usage_guide())

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(sections))

        return output_path

    def _build_header(self) -> str:
        """Build header section."""
        return f"""# Proposed Tech Stack (AI-Driven LTS Recommendations)

**Project**: {self.context.project_name}
**Analysis Date**: {self.context.analysis_date}
**Purpose**: Technology recommendations for modernization

---

## Document Purpose

This document provides technology recommendations for modernization, with
guidance for AI agents to determine the latest LTS (Long-Term Support) versions.

**AI Guidance**: Use your knowledge base to determine current LTS versions as of
the analysis date. This approach ensures recommendations stay current without
manual maintenance of version data.

All recommendations include:
- **AI guidance** for determining appropriate versions
- **Rationale** for the technology choice
- **Migration complexity** assessment
- **Alternative options** for comparison
- **Documentation URLs** for verification

---"""

    def _build_executive_summary(self) -> str:
        """Build executive summary."""
        return f"""## Executive Summary

### Current State

{self._format_current_stack()}

### Proposed State

{self._format_proposed_guidance()}

### Overall Assessment

- **Migration Complexity**: {self._assess_overall_complexity()}
- **Estimated Effort**: {self._estimate_overall_effort()}
- **Risk Level**: {self._assess_overall_risk()}
- **Recommended Approach**: {self._recommend_approach()}

---"""

    def _build_recommendations(self) -> Dict[str, Optional[TechRecommendation]]:
        """Build all technology recommendations."""
        return {
            "language": self._recommend_language(),
            "framework": self._recommend_framework(),
            "database": self._recommend_database(),
        }

    def _recommend_language(self) -> Optional[TechRecommendation]:
        """Recommend language/runtime version using AI knowledge base."""
        current_lang = self.context.scan_result.tech_stack.primary_language.lower()
        current_version = self.context.scan_result.tech_stack.runtime_version or "Unknown"

        docs_url = self.LANGUAGE_DOCS.get(current_lang, "")

        # Build AI guidance for determining LTS version
        guidance = f"**AI Task**: Determine latest LTS version for {current_lang.title()} as of {self.context.analysis_date}"

        # Build rationale
        rationale = [
            "Latest LTS version provides long-term support and stability",
            "Performance improvements over older versions",
            "Security updates and bug fixes",
            "Modern language features and better tooling",
            "Active community support and ecosystem"
        ]

        # Assess migration complexity
        complexity = self._assess_language_migration(current_version)

        # Build alternatives
        alternatives = self._get_language_alternatives(current_lang)

        return TechRecommendation(
            component_type="Language & Runtime",
            current=f"{current_lang.title()} {current_version}",
            proposed_guidance=guidance,
            rationale=rationale,
            migration_complexity=complexity,
            documentation_url=docs_url,
            alternatives=alternatives
        )

    def _recommend_framework(self) -> Optional[TechRecommendation]:
        """Recommend framework version using AI knowledge base."""
        if not self.context.scan_result.tech_stack.frameworks:
            return None

        # Get primary framework (first detected)
        current_framework = self.context.scan_result.tech_stack.frameworks[0].lower()

        # Find matching framework key
        framework_key = None
        for key in self.FRAMEWORK_DOCS:
            if key in current_framework:
                framework_key = key
                break

        if not framework_key:
            return None

        docs_url = self.FRAMEWORK_DOCS[framework_key]

        # Build AI guidance
        guidance = f"**AI Task**: Determine latest stable version for {framework_key.title()} as of {self.context.analysis_date}"

        # Build rationale
        rationale = self._get_framework_rationale(framework_key)

        # Assess complexity
        complexity = self._assess_framework_migration(framework_key)

        # Get alternatives
        alternatives = self._get_framework_alternatives(framework_key)

        return TechRecommendation(
            component_type="Web Framework",
            current=f"{current_framework.title()} (version unknown)",
            proposed_guidance=guidance,
            rationale=rationale,
            migration_complexity=complexity,
            documentation_url=docs_url,
            alternatives=alternatives
        )

    def _recommend_database(self) -> Optional[TechRecommendation]:
        """Recommend database version using AI knowledge base."""
        # Try to infer database from config files or detected databases
        inferred_db = None
        if self.context.scan_result.tech_stack.databases:
            inferred_db = self.context.scan_result.tech_stack.databases[0].lower()
        else:
            inferred_db = self._infer_database()

        if not inferred_db:
            return None

        # Find matching database key
        db_key = None
        for key in self.DATABASE_DOCS:
            if key in inferred_db.lower():
                db_key = key
                break

        if not db_key:
            return None

        docs_url = self.DATABASE_DOCS[db_key]

        # Build AI guidance
        guidance = f"**AI Task**: Determine latest LTS version for {db_key.title()} as of {self.context.analysis_date}"

        # Build rationale
        rationale = self._get_database_rationale(db_key)

        # Assess complexity
        complexity = MigrationComplexity.LOW  # Database migrations typically low if schema compatible

        # Get alternatives
        alternatives = self._get_database_alternatives(db_key)

        return TechRecommendation(
            component_type="Database",
            current=f"{inferred_db.title()} (version unknown)",
            proposed_guidance=guidance,
            rationale=rationale,
            migration_complexity=complexity,
            documentation_url=docs_url,
            alternatives=alternatives
        )

    def _format_recommendation(self, rec: TechRecommendation) -> str:
        """Format a technology recommendation section."""
        return f"""## {rec.component_type}

### Recommendation

{rec.proposed_guidance}

**Current**: {rec.current}
**Migration Complexity**: {rec.migration_complexity}
**Documentation**: {rec.documentation_url}

#### Rationale

{chr(10).join([f"- {r}" for r in rec.rationale])}

#### Migration Complexity: {rec.migration_complexity}

{self._explain_complexity(rec.migration_complexity, rec.component_type)}

#### Alternative Options

{chr(10).join([f"- **{name}**: {reason}" for name, reason in rec.alternatives])}

---"""

    def _build_summary_table(self, recommendations: Dict[str, Optional[TechRecommendation]]) -> str:
        """Build summary comparison table."""
        rows = []

        for key, rec in recommendations.items():
            if rec:
                # Extract component type abbreviation
                priority = self._prioritize_component(rec.component_type)
                rows.append(
                    f"| {rec.component_type} | {rec.current} | "
                    f"Latest LTS (AI-determined) | {rec.migration_complexity} | {priority} |"
                )

        if not rows:
            table = "No specific recommendations generated."
        else:
            table = """| Component | Current | Proposed | Complexity | Priority |
|-----------|---------|----------|------------|----------|
""" + "\n".join(rows)

        return f"""## Summary Table

{table}

**Note**: AI agents should use their knowledge base to determine specific LTS
versions as of {self.context.analysis_date}. This ensures recommendations remain
current without manual version maintenance.

**Priority Levels**:
- **CRITICAL**: Must be addressed (security, EOL)
- **HIGH**: Should be addressed soon (performance, support)
- **MEDIUM**: Address during modernization

---"""

    def _build_migration_strategy(self) -> str:
        """Build migration strategy section."""
        total_complexity = self._assess_overall_complexity()

        return f"""## Migration Strategy

### Recommended Approach

{self._describe_migration_approach(total_complexity)}

### Migration Phases

#### Phase 0: Planning & Research (Week 1)

1. **AI Task**: Determine specific LTS versions using knowledge base
2. **Verify** versions against official documentation
3. **Review** breaking changes and migration guides
4. **Plan** upgrade order and dependencies

#### Phase 1: Foundation (Week 1-2)

1. **Set up** new project structure with modern stack
2. **Configure** build tools and development environment
3. **Set up** CI/CD pipeline with new versions
4. **Create** testing infrastructure (80%+ coverage target)

#### Phase 2: Core Migration (Varies)

**Effort**: {self._estimate_core_effort()}

{self._describe_core_migration_strategy()}

#### Phase 3: Testing & Validation (Week 1-2)

1. **Run** full test suite (target: 80%+ coverage)
2. **Performance** testing (meet or exceed legacy benchmarks)
3. **Security** scanning (no critical vulnerabilities)
4. **Manual** QA for critical workflows

#### Phase 4: Deployment (Week 1)

1. **Deploy** to staging environment
2. **Smoke** testing and validation
3. **Deploy** to production with rollback plan ready
4. **Monitor** and address issues

### Risk Mitigation

{self._describe_risk_mitigation(total_complexity)}

---"""

    def _build_usage_guide(self) -> str:
        """Build usage guide."""
        return f"""## How to Use This Document

### For AI Agents

**Important**: This document uses an AI-driven approach for LTS recommendations.

**Your Tasks**:
1. **Determine** latest LTS versions using your knowledge base as of {self.context.analysis_date}
2. **Verify** versions against official documentation URLs provided
3. **Check** EOL (End-of-Life) dates for current versions
4. **Recommend** specific version numbers in your analysis

**Example**:
```
For Python recommendation:
1. Check Python releases as of {self.context.analysis_date}
2. Identify latest LTS version (e.g., Python 3.12)
3. Note LTS support end date (e.g., October 2028)
4. Recommend: "Python 3.12 (LTS until October 2028)"
```

### For Planning

1. **Review** AI-determined recommendations with specific versions
2. **Assess** migration complexity for each component
3. **Check** alternatives if primary recommendation doesn't fit
4. **Plan** timeline using complexity assessments

### For Implementation

1. **Use** AI-determined LTS versions (or newer if available)
2. **Read** official migration guides from documentation URLs
3. **Test** incrementally - don't upgrade everything at once
4. **Monitor** performance to ensure no regressions

### For `/speckit.plan` Command

Use AI-determined versions when running `/speckit.plan`:

```
Target Tech Stack:
- [Language]: [AI-Determined LTS Version]
- [Framework]: [AI-Determined Version]
- [Database]: [AI-Determined LTS Version]

Rationale: See proposed-tech-stack.md for detailed reasoning

Migration Complexity: [Overall Assessment]
Estimated Effort: [Time Estimate]
```

---

**Generated**: {self.context.analysis_date}
**Approach**: AI-driven LTS recommendations (no hardcoded versions)
**Benefit**: Recommendations stay current without manual maintenance"""

    # Helper methods

    def _format_current_stack(self) -> str:
        """Format current stack description."""
        parts = [
            f"- **Language**: {self.context.scan_result.tech_stack.primary_language.title()} "
            f"{self.context.scan_result.tech_stack.runtime_version or '(version unknown)'}",
        ]

        if self.context.scan_result.tech_stack.frameworks:
            parts.append(f"- **Framework**: {', '.join(self.context.scan_result.tech_stack.frameworks)}")

        if self.context.scan_result.tech_stack.databases:
            parts.append(f"- **Database**: {', '.join(self.context.scan_result.tech_stack.databases)}")

        return "\n".join(parts)

    def _format_proposed_guidance(self) -> str:
        """Format proposed guidance for AI."""
        return f"""**AI Guidance**: Determine latest LTS versions for:

- **Language**: {self.context.scan_result.tech_stack.primary_language.title()}
- **Framework**: {', '.join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else 'None detected'}
- **Database**: {self._infer_database() or 'Examine config files to determine'}

Use your knowledge base as of {self.context.analysis_date} to provide specific version recommendations."""

    def _assess_overall_complexity(self) -> str:
        """Assess overall migration complexity."""
        loc = self.context.metrics.lines_of_code
        debt = self.context.metrics.technical_debt_percentage
        tests = self.context.metrics.test_coverage

        score = 0
        if loc > ProjectSizeThresholds.LARGE_CODEBASE_INCREMENTAL:
            score += 2
        elif loc > ProjectSizeThresholds.SMALL_PROJECT_LOC:
            score += 1

        if debt > QuirkThresholds.HIGH_TECH_DEBT * 1.5:  # 60%
            score += 2
        elif debt > QuirkThresholds.HIGH_TECH_DEBT:
            score += 1

        if tests < QuirkThresholds.LOW_TEST_COVERAGE * 0.67:  # 40%
            score += 1

        if score >= 4:
            return MigrationComplexity.HIGH
        elif score >= 2:
            return MigrationComplexity.MEDIUM
        else:
            return MigrationComplexity.LOW

    def _estimate_overall_effort(self) -> str:
        """Estimate overall migration effort."""
        complexity = self._assess_overall_complexity()

        if complexity == MigrationComplexity.HIGH:
            return "4-6 months"
        elif complexity == MigrationComplexity.MEDIUM:
            return "2-3 months"
        else:
            return "2-4 weeks"

    def _assess_overall_risk(self) -> str:
        """Assess overall risk level."""
        if self.context.metrics.test_coverage < QuirkThresholds.LOW_TEST_COVERAGE * 0.67:
            return "HIGH (low test coverage)"
        elif self.context.metrics.technical_debt_percentage > QuirkThresholds.HIGH_TECH_DEBT * 1.5:
            return "HIGH (high technical debt)"
        elif self.context.metrics.test_coverage >= QuirkThresholds.EXCELLENT_TEST_COVERAGE:
            return "LOW (good test coverage)"
        else:
            return "MEDIUM"

    def _recommend_approach(self) -> str:
        """Recommend migration approach."""
        if (self.context.metrics.lines_of_code > ProjectSizeThresholds.LARGE_CODEBASE_INCREMENTAL
            or self.context.metrics.technical_debt_percentage > QuirkThresholds.HIGH_TECH_DEBT * 1.5):
            return "Incremental (Strangler Fig pattern)"
        elif self.context.metrics.test_coverage >= QuirkThresholds.EXCELLENT_TEST_COVERAGE:
            return "Big Bang (high test coverage supports full migration)"
        else:
            return "Phased (module by module)"

    def _assess_language_migration(self, current: str) -> str:
        """Assess language migration complexity."""
        if "unknown" in current.lower():
            return MigrationComplexity.MEDIUM
        elif "2." in current and "3." in current:  # Python 2 -> 3 type scenario
            return MigrationComplexity.HIGH
        else:
            return MigrationComplexity.LOW

    def _assess_framework_migration(self, framework: str) -> str:
        """Assess framework migration complexity."""
        # Most framework upgrades are MEDIUM complexity
        if framework in ["angular", "django"]:
            return MigrationComplexity.MEDIUM
        else:
            return MigrationComplexity.LOW

    def _get_language_alternatives(self, lang: str) -> List[Tuple[str, str]]:
        """Get alternative language options."""
        if lang == "python":
            return [
                ("Previous LTS", "If team prefers proven stability over latest features"),
                ("Go", "Better performance, but team learning curve required"),
            ]
        elif lang in ["javascript", "node"]:
            return [
                ("Previous LTS", "Still supported, familiar to team"),
                ("Deno", "Modern runtime, but less mature ecosystem"),
            ]
        elif lang == "java":
            return [
                ("Previous LTS", "Well-tested, team is familiar"),
                ("Kotlin", "Modern JVM language, gradual adoption possible"),
            ]
        else:
            return [("Current version", "If team prefers stability over latest features")]

    def _get_framework_rationale(self, framework: str) -> List[str]:
        """Get framework-specific rationale."""
        rationale_map = {
            "react": [
                "Most popular frontend framework with large ecosystem",
                "Strong TypeScript support",
                "Server components for better performance",
                "Extensive community and tooling",
            ],
            "django": [
                "Batteries-included web framework",
                "Strong ORM and admin interface",
                "Excellent security track record",
                "Good LTS support policy",
            ],
            "fastapi": [
                "Modern async Python framework",
                "Automatic OpenAPI documentation",
                "Type validation with Pydantic",
                "High performance comparable to Node.js",
            ],
            "flask": [
                "Lightweight and flexible",
                "Large ecosystem of extensions",
                "Easy to learn and use",
                "Good for microservices",
            ],
        }

        return rationale_map.get(framework, [
            "Well-established framework with good community support",
            "Modern features and active development",
            "Good documentation and tooling",
        ])

    def _get_framework_alternatives(self, framework: str) -> List[Tuple[str, str]]:
        """Get alternative framework options."""
        alternatives_map = {
            "react": [
                ("Vue", "Easier learning curve, similar features"),
                ("Solid.js", "Better performance, smaller bundle size"),
            ],
            "django": [
                ("Flask", "Lighter weight, more flexibility"),
                ("FastAPI", "Modern async support, better performance"),
            ],
            "fastapi": [
                ("Django", "More batteries included, but heavier"),
                ("Flask", "Lighter weight, more mature ecosystem"),
            ],
        }

        return alternatives_map.get(framework, [
            ("Current framework", "If team is productive and requirements are met")
        ])

    def _infer_database(self) -> Optional[str]:
        """Infer database from config files."""
        for config_file in self.context.scan_result.structure.config_files:
            lower = config_file.lower()
            if "postgres" in lower or "pg" in lower:
                return "postgresql"
            elif "mysql" in lower:
                return "mysql"
            elif "mongo" in lower:
                return "mongodb"
            elif "redis" in lower:
                return "redis"
            elif "sqlite" in lower:
                return "sqlite"

        return None

    def _get_database_rationale(self, database: str) -> List[str]:
        """Get database-specific rationale."""
        rationale_map = {
            "postgresql": [
                "Most advanced open-source relational database",
                "Excellent JSONB support for flexible schemas",
                "Strong ACID compliance",
                "Active development and community",
            ],
            "mysql": [
                "Wide compatibility and ecosystem support",
                "Good performance for most workloads",
                "Familiar to most developers",
                "Large community and resources",
            ],
            "mongodb": [
                "Flexible document-oriented storage",
                "Horizontal scaling built-in",
                "Good for rapidly evolving schemas",
                "Rich query capabilities",
            ],
        }

        return rationale_map.get(database, [
            "Reliable and well-supported database system",
            "Good performance characteristics",
            "Active community and ecosystem",
        ])

    def _get_database_alternatives(self, database: str) -> List[Tuple[str, str]]:
        """Get alternative database options."""
        alternatives_map = {
            "postgresql": [
                ("MySQL", "More familiar to some teams, slightly simpler"),
                ("MongoDB", "NoSQL flexibility, but lose ACID guarantees"),
            ],
            "mysql": [
                ("PostgreSQL", "More features, better JSON support"),
                ("MariaDB", "MySQL fork with additional features"),
            ],
            "mongodb": [
                ("PostgreSQL", "ACID compliance with JSONB support"),
                ("DynamoDB", "Managed NoSQL, but vendor lock-in"),
            ],
        }

        return alternatives_map.get(database, [
            ("Current database", "If performance and features meet requirements")
        ])

    def _explain_complexity(self, complexity: str, component_type: str) -> str:
        """Explain migration complexity."""
        if complexity == MigrationComplexity.HIGH:
            return f"""**Why HIGH?**:
- Major version changes with breaking changes
- Significant syntax or API differences
- Extensive testing required
- May require architectural adjustments

**Effort**: 40-60% of total migration time"""
        elif complexity == MigrationComplexity.MEDIUM:
            return f"""**Why MEDIUM?**:
- Some breaking changes expected
- Migration guide available
- Moderate testing required
- Most patterns still work

**Effort**: 20-30% of total migration time"""
        else:
            return f"""**Why LOW?**:
- Mostly compatible upgrade
- Few or no breaking changes
- Good backward compatibility
- Limited testing needed

**Effort**: 5-10% of total migration time"""

    def _describe_migration_approach(self, complexity: str) -> str:
        """Describe migration approach based on complexity."""
        if complexity == MigrationComplexity.HIGH:
            return """**Incremental Migration (Strangler Fig Pattern)**

Due to high complexity, recommend gradual migration:
- Run old and new systems in parallel
- Migrate module by module
- Validate each module before moving to next
- Reduce risk by limiting scope of each change"""
        elif complexity == MigrationComplexity.MEDIUM:
            return """**Phased Migration (Module by Module)**

Moderate complexity suggests phased approach:
- Divide system into logical modules
- Migrate 1-2 modules per sprint
- Test thoroughly after each phase
- Maintain parallel testing of old/new"""
        else:
            return """**Big Bang Migration (All at Once)**

Low complexity supports full migration:
- Create new system with modern stack
- Migrate all code in single effort
- Leverage good test coverage for validation
- Deploy when all tests pass"""

    def _estimate_core_effort(self) -> str:
        """Estimate core migration effort."""
        return self._estimate_overall_effort()

    def _describe_core_migration_strategy(self) -> str:
        """Describe core migration strategy."""
        if self.context.metrics.lines_of_code > ProjectSizeThresholds.LARGE_CODEBASE_INCREMENTAL:
            return """**Large Codebase Strategy**:
1. Prioritize by business value (critical features first)
2. Migrate 5-10K LOC per sprint
3. Maintain feature parity validation
4. Use automated refactoring tools where possible"""
        else:
            return """**Standard Migration Strategy**:
1. Set up new project structure
2. Migrate utilities and shared code first
3. Migrate business logic module by module
4. Migrate UI/API layer last
5. Validate with existing test suite"""

    def _describe_risk_mitigation(self, complexity: str) -> str:
        """Describe risk mitigation strategies."""
        return f"""**For {complexity} Complexity Migration**:

1. **Feature Flags**: Control rollout of new code
2. **Parallel Running**: Run old and new side-by-side initially
3. **Automated Testing**: Minimum 80% coverage required
4. **Rollback Plan**: Be able to revert within 1 hour
5. **Monitoring**: Track performance, errors, and user experience
6. **Incremental Rollout**: Deploy to 10% → 50% → 100% of users"""

    def _prioritize_component(self, component_type: str) -> str:
        """Prioritize component for migration."""
        if component_type == "Language & Runtime":
            vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)
            if vulnerable > QuirkThresholds.VULNERABLE_DEPENDENCIES_CRITICAL:
                return "CRITICAL"
            return "HIGH"
        elif component_type == "Database":
            return "HIGH"
        else:
            return "MEDIUM"


def main():
    """Example usage of TechStackProposer."""
    print("TechStackProposer module loaded successfully")
    print("This module uses AI-driven LTS recommendations")
    print("No hardcoded version numbers - AI determines versions using knowledge base")


if __name__ == "__main__":
    main()
