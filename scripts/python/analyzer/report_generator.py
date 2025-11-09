"""
Report generator for reverse engineering analysis.

Generates markdown reports (analysis-report.md, upgrade-plan.md,
recommended-constitution.md) from analysis data.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Handle both relative and absolute imports
try:
    from .dependency_analyzer import DependencyReport
    from .scanner import ScanResult
    from .scoring_engine import FeasibilityResult, ProjectMetrics
except ImportError:
    from dependency_analyzer import DependencyReport
    from scanner import ScanResult
    from scoring_engine import FeasibilityResult, ProjectMetrics


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    project_name: str
    project_path: Path
    output_dir: Path
    analysis_depth: str = "STANDARD"  # QUICK, STANDARD, COMPREHENSIVE
    focus_areas: List[str] = None  # ALL, SECURITY, PERFORMANCE, DEPENDENCIES, etc.

    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["ALL"]


class ReportGenerator:
    """
    Generate comprehensive markdown reports from analysis data.
    """

    def __init__(self, config: ReportConfig):
        """
        Initialize report generator.

        Args:
            config: ReportConfig with project details and output settings
        """
        self.config = config
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_only = datetime.now().strftime("%Y-%m-%d")

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(
        self,
        scan_result: ScanResult,
        dependency_reports: List[DependencyReport],
        feasibility_result: FeasibilityResult,
        metrics: ProjectMetrics,
    ) -> List[Path]:
        """
        Generate all applicable reports.

        Args:
            scan_result: Results from ProjectScanner
            dependency_reports: Results from DependencyAnalyzer
            feasibility_result: Results from FeasibilityScorer
            metrics: ProjectMetrics used in scoring

        Returns:
            List of generated report file paths
        """
        generated_files = []

        # Always generate main analysis report
        analysis_report_path = self.generate_analysis_report(
            scan_result, dependency_reports, feasibility_result, metrics
        )
        generated_files.append(analysis_report_path)

        # Generate upgrade plan if inline upgrade recommended
        if feasibility_result.recommendation in ["inline_upgrade", "hybrid"]:
            upgrade_plan_path = self.generate_upgrade_plan(
                scan_result, dependency_reports, feasibility_result
            )
            generated_files.append(upgrade_plan_path)

        # Generate constitution if greenfield rewrite recommended
        if feasibility_result.recommendation in ["greenfield_rewrite", "hybrid"]:
            constitution_path = self.generate_recommended_constitution(
                scan_result, metrics
            )
            generated_files.append(constitution_path)

        # Generate decision matrix (always useful)
        decision_matrix_path = self.generate_decision_matrix(
            feasibility_result, metrics
        )
        generated_files.append(decision_matrix_path)

        # Note: Phase 8 redesign moved to AI-driven interactive workflow
        # Analysis artifacts (functional-spec, technical-spec, stage-prompts)
        # are now generated interactively using templates in templates/analysis/
        # instead of Python generators

        return generated_files

    def generate_analysis_report(
        self,
        scan_result: ScanResult,
        dependency_reports: List[DependencyReport],
        feasibility_result: FeasibilityResult,
        metrics: ProjectMetrics,
    ) -> Path:
        """Generate main analysis report."""
        output_path = self.config.output_dir / "analysis-report.md"

        # Build report sections
        sections = []

        # Header
        sections.append(self._build_header())

        # Executive Summary
        sections.append(self._build_executive_summary(scan_result, feasibility_result))

        # Project Overview
        sections.append(self._build_project_overview(scan_result, metrics))

        # What's Good
        sections.append(self._build_whats_good(scan_result, metrics))

        # What's Bad
        sections.append(self._build_whats_bad(scan_result, metrics))

        # Dependency Analysis
        sections.append(self._build_dependency_analysis(dependency_reports))

        # Feasibility & Confidence Analysis
        sections.append(self._build_feasibility_analysis(feasibility_result))

        # Recommendations
        sections.append(self._build_recommendations(feasibility_result, scan_result))

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(sections))

        return output_path

    def generate_upgrade_plan(
        self,
        scan_result: ScanResult,
        dependency_reports: List[DependencyReport],
        feasibility_result: FeasibilityResult,
    ) -> Path:
        """Generate upgrade plan for inline upgrade approach."""
        output_path = self.config.output_dir / "upgrade-plan.md"

        sections = []

        # Header
        sections.append(f"# Upgrade Plan: {self.config.project_name}")
        sections.append(f"**Created**: {self.date_only}")
        sections.append(f"**Project**: {self.config.project_name}")
        sections.append(f"**Current State**: {scan_result.tech_stack.primary_language} project")
        sections.append(f"**Overall Risk Level**: {self._assess_upgrade_risk(feasibility_result)}")
        sections.append("---")

        # Executive Summary
        sections.append("## Executive Summary")
        sections.append(f"**Upgrade Strategy**: Inline upgrade (phased approach)")
        sections.append(f"**Feasibility Score**: {feasibility_result.inline_upgrade_score}/100")
        sections.append("\n**Key Objectives**:")
        sections.append("- Upgrade to latest LTS versions")
        sections.append("- Remove vulnerable dependencies")
        sections.append("- Modernize tooling and practices")
        sections.append("\n**Success Criteria**:")
        sections.append("- [ ] All tests passing")
        sections.append("- [ ] No critical vulnerabilities")
        sections.append("- [ ] Performance maintained or improved")

        # Prerequisites
        sections.append("\n---\n## Prerequisites")
        sections.append(self._build_upgrade_prerequisites(scan_result))

        # Phases
        sections.append("\n---\n## Upgrade Phases")
        sections.append(self._build_upgrade_phases(scan_result, dependency_reports))

        # Rollback Plan
        sections.append("\n---\n## Rollback Plan")
        sections.append(self._build_rollback_plan())

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        return output_path

    def generate_recommended_constitution(
        self, scan_result: ScanResult, metrics: ProjectMetrics
    ) -> Path:
        """Generate recommended constitution for greenfield rewrite."""
        output_path = self.config.output_dir / "recommended-constitution.md"

        sections = []

        # Header
        sections.append(f"# Project Constitution: {self.config.project_name}")
        sections.append(f"**Based on**: Reverse-engineered analysis")
        sections.append(f"**Analysis Date**: {self.date_only}")
        sections.append(f"**Constitution Version**: 1.0.0")
        sections.append("---")

        # Purpose
        sections.append("## Purpose")
        sections.append(
            f"This constitution establishes guiding principles for the modernized version of {self.config.project_name}. "
            "These principles were derived from analyzing the existing codebase to identify patterns worth preserving "
            "and anti-patterns to avoid."
        )

        # Derived Insights
        sections.append("\n---\n## Derived Insights")
        sections.append(self._build_derived_insights(scan_result, metrics))

        # Core Principles
        sections.append("\n---\n## Core Principles")
        sections.append(self._build_core_principles(scan_result, metrics))

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        return output_path

    def generate_decision_matrix(
        self, feasibility_result: FeasibilityResult, metrics: ProjectMetrics
    ) -> Path:
        """Generate decision matrix for stakeholders."""
        output_path = self.config.output_dir / "decision-matrix.md"

        content = f"""# Decision Matrix: {self.config.project_name}

**Analysis Date**: {self.date_only}
**Recommendation**: {feasibility_result.recommendation.upper().replace('_', ' ')}

---

## Comparison Table

| Criteria | Inline Upgrade | Greenfield Rewrite | Hybrid Approach |
|----------|----------------|--------------------|--------------------|
| **Feasibility Score** | {feasibility_result.inline_upgrade_score}/100 | {feasibility_result.greenfield_rewrite_score}/100 | {(feasibility_result.inline_upgrade_score + feasibility_result.greenfield_rewrite_score) / 2:.1f}/100 |
| **Estimated Time** | {self._estimate_time_inline(metrics)} | {self._estimate_time_greenfield(metrics)} | {self._estimate_time_hybrid(metrics)} |
| **Estimated Cost** | {self._estimate_cost(metrics, "inline")} | {self._estimate_cost(metrics, "greenfield")} | {self._estimate_cost(metrics, "hybrid")} |
| **Risk Level** | {self._assess_risk(feasibility_result.inline_upgrade_score)} | {self._assess_risk(100 - feasibility_result.greenfield_rewrite_score)} | Medium |
| **Business Disruption** | Low | Medium-High | Low-Medium |
| **Technical Debt Reduction** | {40 if feasibility_result.inline_upgrade_score > 60 else 20}% | 100% | {60 if metrics.technical_debt_percentage > 50 else 50}% |
| **Team Learning Curve** | Low | Medium-High | Medium |
| **Reversibility** | High | Low | Medium |

---

## Recommendation Rationale

{feasibility_result.rationale}

---

## Key Considerations

### Inline Upgrade
**Pros**:
- Faster time to value (weeks vs months)
- Lower risk of introducing new bugs
- Team knows the codebase
- Can maintain business operations

**Cons**:
- Technical debt only partially addressed ({metrics.technical_debt_percentage:.0f}% remains)
- May need another upgrade cycle soon
- Limited architectural improvements

### Greenfield Rewrite
**Pros**:
- Clean slate - modern architecture
- 100% technical debt elimination
- Latest best practices
- Better long-term maintainability

**Cons**:
- Longer timeline (months)
- Higher risk of scope creep
- Requires clear requirements
- Potential business disruption

### Hybrid Approach (Strangler Fig)
**Pros**:
- Gradual migration reduces risk
- Can maintain business operations
- Flexibility to adjust strategy
- Learn as you go

**Cons**:
- Longest overall timeline
- Complexity of maintaining two systems
- Requires careful planning
- Higher coordination overhead

---

## Next Steps

Based on the **{feasibility_result.recommendation.upper().replace('_', ' ')}** recommendation:

1. Review this decision matrix with stakeholders
2. Discuss timeline and budget constraints
3. Assess team capacity and skills
4. {"Review upgrade-plan.md for detailed steps" if feasibility_result.recommendation == "inline_upgrade" else "Review recommended-constitution.md for principles"}
5. Make final decision and commit to approach
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    # Helper methods for building report sections

    def _build_header(self) -> str:
        return f"""# Project Analysis Report: {self.config.project_name}

**Analysis Date**: {self.timestamp}
**Analysis Depth**: {self.config.analysis_depth}
**Focus Areas**: {', '.join(self.config.focus_areas)}
**Report Version**: 1.0

---"""

    def _build_executive_summary(
        self, scan_result: ScanResult, feasibility_result: FeasibilityResult
    ) -> str:
        return f"""## Executive Summary

**Project Type**: Web Application
**Primary Language**: {scan_result.tech_stack.primary_language.upper()}
**Frameworks**: {', '.join(scan_result.tech_stack.frameworks) if scan_result.tech_stack.frameworks else 'None detected'}
**Lines of Code**: {scan_result.metrics.code_lines:,}

**Key Findings**:

- {len(scan_result.tech_stack.languages)} programming language(s) detected
- {scan_result.metrics.file_count} files analyzed
- {"CI/CD pipeline detected" if scan_result.structure.has_ci_cd else "No CI/CD pipeline found"}
- {"Tests present" if scan_result.structure.has_tests else "No tests detected"}
- {"Documentation present" if scan_result.structure.has_documentation else "Limited documentation"}

**Recommendation**: **{feasibility_result.recommendation.upper().replace('_', ' ')}**

**Confidence**: {feasibility_result.recommendation_confidence:.0f}%

---"""

    def _build_project_overview(self, scan_result: ScanResult, metrics: ProjectMetrics) -> str:
        langs_breakdown = "\n".join([
            f"- {lang}: {lines:,} lines"
            for lang, lines in sorted(
                scan_result.metrics.languages_breakdown.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]) if scan_result.metrics.languages_breakdown else "- Not available"

        return f"""## 1. Project Overview

### 1.1 Technology Stack

**Languages**: {', '.join(scan_result.tech_stack.languages)}
**Frameworks**: {', '.join(scan_result.tech_stack.frameworks) if scan_result.tech_stack.frameworks else 'None detected'}
**Build Tools**: {', '.join(scan_result.tech_stack.build_tools) if scan_result.tech_stack.build_tools else 'None detected'}
**Package Manager**: {scan_result.tech_stack.package_manager or 'Not detected'}
**Runtime Version**: {scan_result.tech_stack.runtime_version or 'Not detected'}

### 1.2 Codebase Metrics

- **Total Lines**: {scan_result.metrics.total_lines:,}
- **Code Lines**: {scan_result.metrics.code_lines:,}
- **Comment Lines**: {scan_result.metrics.comment_lines:,}
- **Blank Lines**: {scan_result.metrics.blank_lines:,}
- **File Count**: {scan_result.metrics.file_count}
- **Test Coverage**: {metrics.test_coverage:.1f}%

**Languages Breakdown**:
{langs_breakdown}

### 1.3 Project Structure

- **Source Directories**: {', '.join(scan_result.structure.source_dirs) if scan_result.structure.source_dirs else 'None found'}
- **Test Directories**: {', '.join(scan_result.structure.test_dirs) if scan_result.structure.test_dirs else 'None found'}
- **Has CI/CD**: {scan_result.structure.has_ci_cd}
- **Has Tests**: {scan_result.structure.has_tests}
- **Has Documentation**: {scan_result.structure.has_documentation}

---"""

    def _build_whats_good(self, scan_result: ScanResult, metrics: ProjectMetrics) -> str:
        strengths = []

        if scan_result.structure.has_ci_cd:
            strengths.append("- **CI/CD Pipeline**: Automated build and deployment processes in place")

        if scan_result.structure.has_tests:
            strengths.append("- **Testing Infrastructure**: Test directories and frameworks detected")

        if metrics.test_coverage >= 60:
            strengths.append(f"- **Good Test Coverage**: {metrics.test_coverage:.0f}% coverage meets recommended threshold")

        if scan_result.structure.has_documentation:
            strengths.append("- **Documentation Present**: README and documentation files found")

        if metrics.code_quality_score >= 7:
            strengths.append(f"- **Code Quality**: Score of {metrics.code_quality_score:.1f}/10 indicates well-maintained code")

        if not strengths:
            strengths.append("- Analysis in progress - refer to detailed sections below")

        return f"""## 2. What's Good ✅

### 2.1 Strengths Identified

{chr(10).join(strengths)}

### 2.2 Best Practices Observed

- Project structure follows common conventions
- Version control in use
- {f"Modular architecture with score {metrics.modularity_score:.1f}/10" if metrics.modularity_score > 0 else "Standard project organization"}

---"""

    def _build_whats_bad(self, scan_result: ScanResult, metrics: ProjectMetrics) -> str:
        issues = []

        if not scan_result.structure.has_tests:
            issues.append("| No test infrastructure | HIGH | Entire codebase | Weeks | Add test framework and write tests |")

        if metrics.test_coverage < 60:
            issues.append(f"| Low test coverage ({metrics.test_coverage:.0f}%) | HIGH | Entire codebase | Weeks | Increase coverage to 80%+ |")

        if not scan_result.structure.has_ci_cd:
            issues.append("| No CI/CD pipeline | MEDIUM | DevOps | Days | Set up GitHub Actions/GitLab CI |")

        if metrics.code_quality_score < 6:
            issues.append(f"| Code quality issues (score: {metrics.code_quality_score:.1f}/10) | MEDIUM | Various files | Weeks | Refactor and apply linting |")

        if metrics.technical_debt_percentage > 40:
            issues.append(f"| High technical debt ({metrics.technical_debt_percentage:.0f}%) | HIGH | Entire codebase | Months | Systematic refactoring needed |")

        issues_table = "\n".join(issues) if issues else "| None identified during automated scan | LOW | N/A | N/A | Manual review recommended |"

        return f"""## 3. What's Bad ❌

### 3.1 Technical Debt

**Technical Debt Level**: {metrics.technical_debt_percentage:.0f}%

| Issue | Impact | Location | Effort to Fix | Recommendation |
|-------|--------|----------|---------------|----------------|
{issues_table}

### 3.2 Security Issues

See Dependency Analysis section below for security vulnerabilities.

---"""

    def _build_dependency_analysis(self, dependency_reports: List[DependencyReport]) -> str:
        if not dependency_reports:
            return """## 4. Dependency Analysis

No dependency files detected or analysis tools unavailable.

---"""

        sections = ["## 4. Dependency Analysis"]

        for report in dependency_reports:
            if not report.analysis_successful:
                sections.append(f"\n### {report.ecosystem.upper()}: Analysis Failed")
                sections.append(f"**Error**: {report.error_message}")
                continue

            sections.append(f"\n### {report.ecosystem.upper()} Dependencies")
            sections.append(f"- **Total**: {report.total_dependencies}")
            sections.append(f"- **Outdated**: {report.outdated_count}")
            sections.append(f"- **Vulnerable**: {report.vulnerable_count}")
            sections.append(f"- **Deprecated**: {report.deprecated_count}")

            if report.vulnerable_count > 0:
                sections.append(f"\n⚠️ **{report.vulnerable_count} security vulnerabilities detected** - Review and patch immediately!")

                # Show top vulnerable packages
                vulnerable = [i for i in report.issues if i.issue_type == "vulnerable"][:5]
                if vulnerable:
                    sections.append("\n**Top Vulnerable Packages**:")
                    for issue in vulnerable:
                        sections.append(f"- {issue.package_name} ({issue.current_version}) - Severity: {issue.severity.upper()}")
                        if issue.cve:
                            sections.append(f"  - CVE: {issue.cve}")

        sections.append("\n---")
        return "\n".join(sections)

    def _build_feasibility_analysis(self, feasibility_result: FeasibilityResult) -> str:
        inline_breakdown = "\n".join([
            f"- {factor.replace('_', ' ').title()}: {score:.2f}"
            for factor, score in feasibility_result.breakdown["inline"].items()
        ])

        greenfield_breakdown = "\n".join([
            f"- {factor.replace('_', ' ').title()}: {score:.2f}"
            for factor, score in feasibility_result.breakdown["greenfield"].items()
        ])

        return f"""## 5. Feasibility & Confidence Analysis

### 5.1 Inline Upgrade Feasibility

**Score**: {feasibility_result.inline_upgrade_score}/100

**Interpretation**: {self._interpret_score(feasibility_result.inline_upgrade_score)}

**Breakdown**:
{inline_breakdown}

### 5.2 Greenfield Rewrite Feasibility

**Score**: {feasibility_result.greenfield_rewrite_score}/100

**Interpretation**: {self._interpret_score(feasibility_result.greenfield_rewrite_score)}

**Breakdown**:
{greenfield_breakdown}

### 5.3 Confidence Scores

- **Analysis Confidence**: {feasibility_result.analysis_confidence:.0f}/100
- **Recommendation Confidence**: {feasibility_result.recommendation_confidence:.0f}/100

---"""

    def _build_recommendations(self, feasibility_result: FeasibilityResult, scan_result: ScanResult) -> str:
        return f"""## 6. Recommendations

### 6.1 Primary Recommendation

**{feasibility_result.recommendation.upper().replace('_', ' ')}**

{feasibility_result.rationale}

### 6.2 Immediate Actions (Next 2 Weeks)

{"- Review and apply security patches for vulnerable dependencies" if any(r.vulnerable_count > 0 for r in []) else "- Review upgrade-plan.md or recommended-constitution.md"}
- Set up monitoring and baseline metrics
- Create feature branch for changes
- Review this report with team and stakeholders

### 6.3 Short-term Roadmap (1-3 Months)

- {"Follow phased upgrade plan" if feasibility_result.recommendation == "inline_upgrade" else "Begin greenfield development with recommended constitution"}
- Increase test coverage to 80%+
- Modernize build tooling
- Address critical technical debt

### 6.4 Long-term Roadmap (3-12 Months)

- Achieve full modernization
- Establish sustainable maintenance practices
- Implement continuous improvement processes

---"""

    def _build_upgrade_prerequisites(self, scan_result: ScanResult) -> str:
        return """### Required Before Starting

- [ ] **Full test suite passing** in current state
- [ ] **Code committed** to version control
- [ ] **Backup created** (database, code, configuration)
- [ ] **Development environment ready**
- [ ] **Rollback plan documented**
- [ ] **Team alignment** and stakeholder approval

### Recommended Tools

```bash
# Install recommended tooling based on tech stack
# See analysis report for specific recommendations
```"""

    def _build_upgrade_phases(self, scan_result: ScanResult, dependency_reports: List[DependencyReport]) -> str:
        return """### Phase 0: Preparation & Baseline (Effort: 1-2 days)

1. Create feature branch
2. Capture current metrics
3. Document current behavior
4. Set up monitoring

### Phase 1: Critical Security Patches (Effort: 2-3 days)

1. Fix critical vulnerabilities
2. Update vulnerable dependencies
3. Run security audit
4. Verify no regressions

### Phase 2: Dependency Updates (Effort: 1 week)

1. Update patch versions
2. Update minor versions
3. Test thoroughly
4. Update major versions (if needed)

### Phase 3: Runtime/Framework Upgrade (Effort: 1-2 weeks)

1. Upgrade runtime version
2. Update framework versions
3. Resolve breaking changes
4. Update tooling

### Phase 4: Testing & Quality Assurance (Effort: 1 week)

1. Run full test suite
2. Manual QA for critical flows
3. Performance testing
4. Security scanning

### Phase 5: Documentation & Deployment (Effort: 2-3 days)

1. Update documentation
2. Deploy to staging
3. Deploy to production
4. Monitor post-deployment"""

    def _build_rollback_plan(self) -> str:
        return """### Rollback Procedures

**If upgrade fails**:

1. Revert to previous git commit
2. Restore database from backup (if schema changed)
3. Redeploy previous version
4. Notify stakeholders
5. Document what went wrong

**Rollback command**:

```bash
git revert HEAD~1  # Or specific commit
# Deploy previous version
```

**Recovery time objective**: < 1 hour"""

    def _build_derived_insights(self, scan_result: ScanResult, metrics: ProjectMetrics) -> str:
        good_patterns = []
        if scan_result.structure.has_ci_cd:
            good_patterns.append("- Automated CI/CD pipeline exists")
        if scan_result.structure.has_tests:
            good_patterns.append("- Testing infrastructure present")
        if scan_result.structure.has_documentation:
            good_patterns.append("- Documentation maintained")

        anti_patterns = []
        if not scan_result.structure.has_tests:
            anti_patterns.append("- No automated testing")
        if metrics.test_coverage < 60:
            anti_patterns.append(f"- Low test coverage ({metrics.test_coverage:.0f}%)")
        if not scan_result.structure.has_ci_cd:
            anti_patterns.append("- No CI/CD automation")

        gaps = []
        if metrics.technical_debt_percentage > 40:
            gaps.append(f"- High technical debt ({metrics.technical_debt_percentage:.0f}%)")
        if metrics.documentation_quality < 6:
            gaps.append("- Insufficient documentation")

        return f"""**Good Patterns Observed** (to preserve):
{chr(10).join(good_patterns) if good_patterns else "- Manual analysis recommended"}

**Anti-Patterns Found** (to eliminate):
{chr(10).join(anti_patterns) if anti_patterns else "- None identified in automated scan"}

**Critical Gaps** (to address):
{chr(10).join(gaps) if gaps else "- None identified in automated scan"}"""

    def _build_core_principles(self, scan_result: ScanResult, metrics: ProjectMetrics) -> str:
        return """### Principle 1: Test Coverage

**Statement**: MUST maintain minimum 80% test coverage for all new code

**Rationale**: Current coverage below threshold - new system must be testable from day one

**Implementation**:
- Write tests before implementation (TDD)
- Unit tests for all business logic
- Integration tests for all APIs
- E2E tests for critical paths

### Principle 2: Code Quality

**Statement**: MUST follow consistent code quality standards

**Implementation**:
- Linting enforced in CI/CD
- Code reviews mandatory
- Automated quality checks
- Documentation required for public APIs

### Principle 3: Security

**Statement**: MUST address security vulnerabilities within 48 hours of discovery

**Implementation**:
- Automated dependency scanning
- Regular security audits
- Input validation mandatory
- Secure coding standards enforced"""

    def _interpret_score(self, score: float) -> str:
        if score >= 80:
            return "✅ Highly feasible"
        elif score >= 60:
            return "⚠️ Feasible with caution"
        elif score >= 40:
            return "🟡 Moderately risky"
        else:
            return "🔴 High risk"

    def _assess_upgrade_risk(self, feasibility_result: FeasibilityResult) -> str:
        score = feasibility_result.inline_upgrade_score
        if score >= 70:
            return "LOW"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "HIGH"

    def _assess_risk(self, score: float) -> str:
        if score >= 70:
            return "Low"
        elif score >= 50:
            return "Medium"
        else:
            return "High"

    def _estimate_time_inline(self, metrics: ProjectMetrics) -> str:
        if metrics.lines_of_code < 10000:
            return "2-4 weeks"
        elif metrics.lines_of_code < 50000:
            return "1-2 months"
        else:
            return "2-3 months"

    def _estimate_time_greenfield(self, metrics: ProjectMetrics) -> str:
        if metrics.lines_of_code < 10000:
            return "2-3 months"
        elif metrics.lines_of_code < 50000:
            return "4-6 months"
        else:
            return "6-12 months"

    def _estimate_time_hybrid(self, metrics: ProjectMetrics) -> str:
        if metrics.lines_of_code < 10000:
            return "3-4 months"
        elif metrics.lines_of_code < 50000:
            return "5-8 months"
        else:
            return "8-18 months"

    def _estimate_cost(self, metrics: ProjectMetrics, approach: str) -> str:
        if approach == "inline":
            return "$"
        elif approach == "greenfield":
            return "$$$"
        else:  # hybrid
            return "$$-$$$"


def main():
    """Example usage of ReportGenerator."""
    from pathlib import Path

    # This would normally come from running the analysis
    # For demo purposes, we'll create minimal test data

    print("ReportGenerator module loaded successfully")
    print("Run the main analyze-project.sh script to generate reports")


if __name__ == "__main__":
    main()
