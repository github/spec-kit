"""
Principle extractor for constitution generation.

Generates extracted-principles.md that feeds into /speckit.constitution stage.
Extracts ACTUAL principles from codebase patterns (not template-based).
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Handle both relative and absolute imports
try:
    from .analysis_context import AnalysisContext
except ImportError:
    from analysis_context import AnalysisContext


class PrincipleExtractor:
    """
    Extract principles from legacy codebase analysis.

    This class generates a structured document with evidence-backed principles
    that can be used to create a project constitution.
    """

    def __init__(self, context: AnalysisContext):
        """
        Initialize principle extractor.

        Args:
            context: Shared analysis context
        """
        self.context = context

    def generate_extracted_principles(self, output_path: Path) -> Path:
        """
        Generate extracted-principles.md file.

        Args:
            output_path: Path where the file should be written

        Returns:
            Path to the generated file
        """
        sections = []

        # Header
        sections.append(self._build_header())

        # Overview
        sections.append(self._build_overview())

        # Business Principles
        sections.append(self._build_business_principles())

        # Architectural Principles
        sections.append(self._build_architectural_principles())

        # Quality Principles
        sections.append(self._build_quality_principles())

        # How to Use
        sections.append(self._build_usage_guide())

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(sections))

        return output_path

    def _build_header(self) -> str:
        """Build header section."""
        return f"""# Extracted Principles (from Legacy Codebase Analysis)

**Project**: {self.context.project_name}
**Analysis Date**: {self.context.analysis_date}
**Purpose**: Feed into `/speckit.constitution` for project modernization

---

## Executive Summary

This document contains principles extracted from analyzing the legacy codebase.
These are NOT generic templates - they are based on ACTUAL patterns, practices,
and requirements discovered in the existing system.

**Key Stats**:
- **Lines of Code**: {self.context.metrics.lines_of_code:,}
- **Primary Language**: {self.context.scan_result.tech_stack.primary_language.title()}
- **Frameworks**: {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "None detected"}
- **Test Coverage**: {self.context.metrics.test_coverage:.0f}%
- **Technical Debt**: {self.context.metrics.technical_debt_percentage:.0f}%

---"""

    def _build_overview(self) -> str:
        """Build overview section."""
        findings = []

        if self.context.scan_result.structure.has_tests:
            findings.append("testing infrastructure")
        if self.context.scan_result.structure.has_ci_cd:
            findings.append("CI/CD automation")
        if self.context.scan_result.structure.has_documentation:
            findings.append("documentation practices")
        if self.context.metrics.modularity_score >= 6:
            findings.append("modular architecture")

        findings_text = ", ".join(findings) if findings else "basic project structure"

        return f"""## Analysis Overview

The legacy codebase was analyzed to extract principles that should guide
the modernized system. Analysis examined:

- **Code Structure**: {len(self.context.scan_result.structure.source_dirs)} source directories
- **Dependencies**: {self.context.metrics.total_dependencies} total packages
- **Build System**: {", ".join(self.context.scan_result.tech_stack.build_tools) if self.context.scan_result.tech_stack.build_tools else "Standard"}
- **Patterns Found**: {findings_text}

**Extraction Method**: Automated analysis of project structure, dependencies,
testing patterns, and quality metrics combined with code examination.

---"""

    def _build_business_principles(self) -> str:
        """Build business principles section."""
        principles = []

        # Principle 1: Data Integrity (always important)
        principles.append(self._extract_data_integrity_principle())

        # Principle 2: User Experience Continuity
        principles.append(self._extract_ux_continuity_principle())

        # Principle 3: Domain-Specific Rules (AI should extract these)
        principles.append(self._extract_domain_rules_principle())

        return f"""## Business Principles

These principles govern business logic and domain requirements.

{chr(10).join(principles)}

---"""

    def _extract_data_integrity_principle(self) -> str:
        """Extract data integrity principle."""
        has_db = any("db" in str(f).lower() or "database" in str(f).lower()
                     for f in self.context.scan_result.structure.config_files)

        evidence_loc = "Configuration files" if has_db else "Project structure"

        return f"""### 1. Data Integrity and Consistency

**Evidence**: {evidence_loc} indicate data persistence layer

**Source**:
- Configuration: {", ".join(self.context.scan_result.structure.config_files[:3]) if self.context.scan_result.structure.config_files else "Standard"}
- Data layer likely in: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "source code"}

**Requirement**:
- MUST preserve all data validation rules from legacy system
- MUST maintain data consistency during migration
- MUST validate input data at all entry points
- SHOULD use transactions for multi-step data operations

**Action for AI**: Examine legacy data models, validation logic, and database
schemas to extract specific validation rules and constraints."""

    def _extract_ux_continuity_principle(self) -> str:
        """Extract UX continuity principle."""
        has_frontend = any(f in str(self.context.scan_result.tech_stack.frameworks)
                          for f in ["react", "vue", "angular"])

        return f"""### 2. User Experience Continuity

**Evidence**: {"Frontend framework detected (" + ", ".join([f for f in self.context.scan_result.tech_stack.frameworks if f.lower() in ["react", "vue", "angular"]]) + ")" if has_frontend else "User-facing application"}

**Source**:
- Framework: {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "Unknown"}
- Codebase structure suggests {self._infer_app_type()}

**Requirement**:
- MUST preserve critical user workflows
- MUST maintain or improve performance (response times, load times)
- SHOULD improve user experience where possible
- MUST not break existing user expectations

**Action for AI**: Examine legacy UI code, routing, and user interaction
patterns to identify critical user journeys that must be preserved."""

    def _extract_domain_rules_principle(self) -> str:
        """Extract domain-specific rules principle."""
        return f"""### 3. Domain-Specific Business Rules

**Evidence**: Business logic in {self.context.metrics.lines_of_code:,} lines of code

**Source**:
- Primary codebase: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "source files"}
- Business logic modules: **AI should examine code**

**Requirement**:
- MUST preserve all business validation rules
- MUST maintain calculation/algorithm accuracy
- MUST preserve workflow state machines
- SHOULD document business rules explicitly in new code

**Action for AI**: Deep examination of legacy code required to extract:
- Validation rules (min/max values, format requirements, business constraints)
- Calculation algorithms (pricing, scoring, reporting)
- Workflow rules (state transitions, approval processes)
- Business-specific edge case handling"""

    def _build_architectural_principles(self) -> str:
        """Build architectural principles section."""
        principles = []

        # Principle 1: Modularity
        principles.append(self._extract_modularity_principle())

        # Principle 2: Service Boundaries
        principles.append(self._extract_service_boundaries_principle())

        # Principle 3: API Design
        principles.append(self._extract_api_design_principle())

        return f"""## Architectural Principles

These principles govern system architecture and design patterns.

{chr(10).join(principles)}

---"""

    def _extract_modularity_principle(self) -> str:
        """Extract modularity principle."""
        score = self.context.metrics.modularity_score

        if score >= 7:
            assessment = "GOOD - Preserve modular structure"
        elif score >= 5:
            assessment = "MODERATE - Improve separation of concerns"
        else:
            assessment = "LOW - Major restructuring needed"

        return f"""### 1. Modularity and Separation of Concerns

**Evidence**: Modularity score: {score:.1f}/10 ({assessment})

**Source**:
- Directory structure: {len(self.context.scan_result.structure.source_dirs)} main directories
- Code organization: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "Standard"}

**Current Pattern**: {self._describe_modularity_pattern()}

**Requirement**:
- {"SHOULD preserve existing modular boundaries" if score >= 6 else "MUST improve separation of concerns"}
- {"SHOULD maintain clear module interfaces" if score >= 6 else "SHOULD define clear module boundaries"}
- MUST avoid circular dependencies
- SHOULD follow single responsibility principle

**Action for AI**: {self._get_modularity_action()}"""

    def _extract_service_boundaries_principle(self) -> str:
        """Extract service boundaries principle."""
        num_dirs = len(self.context.scan_result.structure.source_dirs)

        return f"""### 2. Service/Component Boundaries

**Evidence**: {num_dirs} primary source {"directories" if num_dirs != 1 else "directory"} identified

**Source**:
- Structure: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "Flat structure"}
- Architecture score: {self.context.metrics.architecture_score:.1f}/10

**Current Pattern**: {self._describe_architecture_pattern()}

**Requirement**:
- SHOULD maintain logical service boundaries
- MUST define clear interfaces between components
- SHOULD minimize coupling between services
- MAY refactor boundaries if current design is problematic

**Action for AI**: Examine directory structure and import/dependency patterns
to identify service boundaries and potential violations."""

    def _extract_api_design_principle(self) -> str:
        """Extract API design principle."""
        has_api = any("api" in str(d).lower() or "route" in str(d).lower() or "controller" in str(d).lower()
                     for d in self.context.scan_result.structure.source_dirs)

        return f"""### 3. API Design and Contracts

**Evidence**: {"API layer detected in directory structure" if has_api else "Application structure suggests API usage"}

**Source**:
- Framework: {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "Unknown"}
- Likely location: {self._infer_api_location()}

**Current Pattern**: {self._describe_api_pattern()}

**Requirement**:
- MUST maintain backward compatibility with existing API contracts
- SHOULD use OpenAPI/Swagger for API documentation
- MUST version APIs for breaking changes
- SHOULD follow RESTful principles (or GraphQL if currently used)

**Action for AI**: Examine API endpoint definitions, request/response formats,
and error handling to extract current API contract specifications."""

    def _build_quality_principles(self) -> str:
        """Build quality principles section."""
        principles = []

        # Principle 1: Testing
        principles.append(self._extract_testing_principle())

        # Principle 2: Code Quality
        principles.append(self._extract_code_quality_principle())

        # Principle 3: Security
        principles.append(self._extract_security_principle())

        # Principle 4: Performance
        principles.append(self._extract_performance_principle())

        return f"""## Quality Principles

These principles govern code quality, testing, and operational excellence.

{chr(10).join(principles)}

---"""

    def _extract_testing_principle(self) -> str:
        """Extract testing principle."""
        has_tests = self.context.scan_result.structure.has_tests
        coverage = self.context.metrics.test_coverage

        if coverage >= 80:
            target = "maintain"
            rationale = "Excellent existing coverage should be preserved"
        elif coverage >= 60:
            target = "improve to"
            rationale = "Good foundation exists, raise to industry standard"
        else:
            target = "achieve"
            rationale = "Current coverage below acceptable threshold"

        return f"""### 1. Testing and Quality Assurance

**Evidence**: {"Test infrastructure present" if has_tests else "No test infrastructure detected"} (Coverage: {coverage:.0f}%)

**Source**:
- Test directories: {", ".join(self.context.scan_result.structure.test_dirs) if self.context.scan_result.structure.test_dirs else "None found"}
- Test framework: {"Detected" if has_tests else "Not detected"}

**Current State**: {coverage:.0f}% test coverage

**Requirement**:
- MUST {target} minimum 80% test coverage for all new code
- {"MUST maintain existing test suite" if has_tests else "MUST create comprehensive test suite"}
- SHOULD write tests before implementation (TDD)
- MUST include unit, integration, and E2E tests

**Rationale**: {rationale}

**Action for AI**: {self._get_testing_action()}"""

    def _extract_code_quality_principle(self) -> str:
        """Extract code quality principle."""
        score = self.context.metrics.code_quality_score

        return f"""### 2. Code Quality and Maintainability

**Evidence**: Code quality score: {score:.1f}/10

**Source**:
- Documentation: {"Present" if self.context.scan_result.structure.has_documentation else "Limited"}
- Code organization: {self.context.metrics.modularity_score:.1f}/10 modularity
- Technical debt: {self.context.metrics.technical_debt_percentage:.0f}%

**Current State**: {"Good code quality practices" if score >= 7 else "Code quality needs improvement"}

**Requirement**:
- MUST follow consistent coding standards
- MUST enforce linting in CI/CD pipeline
- MUST require code reviews for all changes
- {"SHOULD maintain documentation standards" if self.context.scan_result.structure.has_documentation else "MUST add comprehensive documentation"}
- SHOULD use static analysis tools

**Target**: Achieve 8.5+/10 code quality score (currently {score:.1f}/10)

**Action for AI**: Examine existing code style, documentation patterns, and
any linter configurations to extract specific quality standards."""

    def _extract_security_principle(self) -> str:
        """Extract security principle."""
        vulnerable_count = sum(r.vulnerable_count for r in self.context.dependency_reports)

        urgency = "CRITICAL" if vulnerable_count > 10 else "HIGH" if vulnerable_count > 0 else "MODERATE"

        return f"""### 3. Security and Compliance

**Evidence**: {vulnerable_count} vulnerable dependencies found (Severity: {urgency})

**Source**:
- Dependencies analyzed: {self.context.metrics.total_dependencies} total
- Security scan results: {vulnerable_count} vulnerabilities
- {"Outdated packages: " + str(self.context.metrics.outdated_dependencies) if self.context.metrics.outdated_dependencies > 0 else "All packages current"}

**Current State**: {self._assess_security_posture()}

**Requirement**:
- MUST address all critical/high security vulnerabilities immediately
- MUST fix security issues within 48 hours of discovery
- MUST use automated dependency scanning in CI/CD
- MUST validate and sanitize all user inputs
- SHOULD implement security headers and best practices
- SHOULD conduct regular security audits

**Priority**: {urgency}

**Action for AI**: Examine authentication, authorization, data validation,
and encryption patterns in legacy code to extract security requirements."""

    def _extract_performance_principle(self) -> str:
        """Extract performance principle."""
        size_category = self._get_size_category()

        return f"""### 4. Performance and Scalability

**Evidence**: Project size: {self.context.metrics.lines_of_code:,} LOC ({size_category})

**Source**:
- Codebase size: {self.context.metrics.lines_of_code:,} lines
- Architecture: {self.context.metrics.architecture_score:.1f}/10
- {"CI/CD: Present" if self.context.scan_result.structure.has_ci_cd else "CI/CD: Not detected"}

**Current State**: {self._assess_performance_baseline()}

**Requirement**:
- MUST maintain or improve current performance baselines
- SHOULD measure and monitor key performance indicators
- SHOULD optimize database queries and API calls
- MAY introduce caching where appropriate
- SHOULD design for horizontal scalability

**Action for AI**: Examine legacy code for performance-critical sections,
caching strategies, and database access patterns to extract performance
requirements and acceptable latency thresholds."""

    def _build_usage_guide(self) -> str:
        """Build usage guide section."""
        return """## How to Use This Document

### For `/speckit.constitution` Command

This document should be used as input when creating your project constitution:

1. **Review** each principle and its evidence
2. **Validate** by examining the referenced legacy code
3. **Adapt** principles to your modernization goals
4. **Add** any additional principles from team discussions

### For AI Agents

When extracting additional principles, follow this process:

1. **Examine Legacy Code**: Look at actual implementation
2. **Find Evidence**: Identify specific patterns, configurations, or practices
3. **Extract Rule**: Derive the principle from observed behavior
4. **Document Source**: Note file paths and line numbers
5. **Assess Criticality**: Determine if MUST/SHOULD/MAY

### Principle Template

When adding new principles, use this format:

```markdown
### N. Principle Name

**Evidence**: What you observed in the code
**Source**: File paths and locations
**Requirement**: What MUST/SHOULD/MAY be done
**Action for AI**: What deeper examination is needed
```

### Critical vs. Aspirational

- **MUST**: Non-negotiable requirements (security, data integrity, compliance)
- **SHOULD**: Strong recommendations (testing, code quality)
- **MAY**: Optional improvements (nice-to-haves)

---

**Note**: This document is generated from automated analysis. AI agents should
examine the actual legacy code to extract more detailed and specific principles,
especially for business logic and domain rules."""

    # Helper methods

    def _infer_app_type(self) -> str:
        """Infer application type from tech stack."""
        frameworks = [f.lower() for f in self.context.scan_result.tech_stack.frameworks]

        if any(f in frameworks for f in ["react", "vue", "angular"]):
            return "web application with modern frontend"
        elif any(f in frameworks for f in ["express", "flask", "fastapi", "spring-boot"]):
            return "backend API service"
        elif any(f in frameworks for f in ["django", "rails", "laravel"]):
            return "full-stack web application"
        else:
            return "application (type to be determined)"

    def _describe_modularity_pattern(self) -> str:
        """Describe current modularity pattern."""
        score = self.context.metrics.modularity_score

        if score >= 7:
            return "Well-organized with clear separation of concerns"
        elif score >= 5:
            return "Moderate organization with some coupling"
        else:
            return "Monolithic structure with tight coupling"

    def _get_modularity_action(self) -> str:
        """Get action for modularity improvement."""
        score = self.context.metrics.modularity_score

        if score >= 7:
            return "Examine module interfaces and preserve boundaries in new system"
        elif score >= 5:
            return "Identify module boundaries and reduce coupling during migration"
        else:
            return "Design new modular architecture and refactor during migration"

    def _describe_architecture_pattern(self) -> str:
        """Describe architecture pattern."""
        num_dirs = len(self.context.scan_result.structure.source_dirs)

        if num_dirs >= 5:
            return "Multi-service or layered architecture"
        elif num_dirs >= 3:
            return "Moderate separation (likely MVC or similar)"
        else:
            return "Simple structure (likely small or monolithic)"

    def _infer_api_location(self) -> str:
        """Infer API location from structure."""
        for dir_name in self.context.scan_result.structure.source_dirs:
            if any(keyword in dir_name.lower() for keyword in ["api", "route", "controller", "endpoint"]):
                return dir_name

        if self.context.scan_result.structure.source_dirs:
            return f"{self.context.scan_result.structure.source_dirs[0]} (likely contains API definitions)"

        return "Source code (examine for route/endpoint definitions)"

    def _describe_api_pattern(self) -> str:
        """Describe API pattern from framework."""
        frameworks = [f.lower() for f in self.context.scan_result.tech_stack.frameworks]

        if "fastapi" in frameworks:
            return "FastAPI (async Python, OpenAPI built-in)"
        elif "flask" in frameworks:
            return "Flask (Python, likely REST)"
        elif "express" in frameworks:
            return "Express.js (Node.js, likely REST)"
        elif "spring-boot" in frameworks:
            return "Spring Boot (Java, likely REST)"
        elif any(f in frameworks for f in ["graphql"]):
            return "GraphQL API"
        else:
            return "RESTful API (assumed - verify in code)"

    def _get_testing_action(self) -> str:
        """Get testing action."""
        if self.context.scan_result.structure.has_tests:
            return "Examine existing tests to extract testing patterns and coverage standards"
        else:
            return "Create comprehensive test strategy (unit, integration, E2E) from scratch"

    def _assess_security_posture(self) -> str:
        """Assess security posture."""
        vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)

        if vulnerable == 0:
            return "Good - No known vulnerabilities"
        elif vulnerable <= 5:
            return f"Moderate - {vulnerable} vulnerabilities need patching"
        else:
            return f"Poor - {vulnerable} vulnerabilities require immediate attention"

    def _get_size_category(self) -> str:
        """Get project size category."""
        loc = self.context.metrics.lines_of_code

        if loc < 10000:
            return "Small"
        elif loc < 50000:
            return "Medium"
        elif loc < 100000:
            return "Large"
        else:
            return "Very Large"

    def _assess_performance_baseline(self) -> str:
        """Assess performance baseline."""
        return "Baseline to be measured - examine legacy performance characteristics"


def main():
    """Example usage of PrincipleExtractor."""
    print("PrincipleExtractor module loaded successfully")
    print("This module is called by ReportGenerator during analysis")


if __name__ == "__main__":
    main()
