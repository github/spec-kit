"""
Prompt generator for stage-specific workflow guidance.

Generates custom prompts for all 8 spec-driven workflow stages that inject
legacy context at the right time, referencing specific code locations and
extracted insights from the analysis.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Handle both relative and absolute imports
try:
    from .analysis_context import AnalysisContext
except ImportError:
    from analysis_context import AnalysisContext


@dataclass
class StagePromptContext:
    """Context information for generating stage-specific prompts."""

    project_name: str
    legacy_tech_stack: str
    proposed_tech_stack: str
    analysis_date: str
    code_references: Dict[str, str]  # area -> file:line reference
    key_findings: List[str]
    critical_constraints: List[str]


class PromptGenerator:
    """
    Generate stage-specific prompts for the spec-driven workflow.

    Creates 8 prompt files (one per workflow stage) that inject legacy
    context and provide guidance on using analysis artifacts.
    """

    STAGES = [
        "1-constitution",
        "2-specify",
        "3-clarify",
        "4-plan",
        "5-tasks",
        "6-analyze",
        "7-implement",
        "8-checklist"
    ]

    def __init__(self, context: AnalysisContext, output_dir: Path):
        """
        Initialize prompt generator.

        Args:
            context: Shared analysis context
            output_dir: Directory where prompts will be written
        """
        self.context = context
        self.output_dir = output_dir

        # Create stage-prompts directory
        self.prompts_dir = output_dir / "stage-prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_prompts(self) -> List[Path]:
        """
        Generate all 8 stage prompts.

        Returns:
            List of generated prompt file paths
        """
        generated_files = []

        # Build common context
        context = self._build_context()

        # Generate each stage prompt
        for stage in self.STAGES:
            prompt_path = self._generate_stage_prompt(stage, context)
            generated_files.append(prompt_path)

        # Generate README for stage-prompts directory
        readme_path = self._generate_readme()
        generated_files.append(readme_path)

        return generated_files

    def _build_context(self) -> StagePromptContext:
        """Build common context for all prompts."""
        # Build tech stack strings
        legacy_stack = self._format_legacy_stack()
        proposed_stack = self._format_proposed_stack()

        # Build code references
        code_refs = self._extract_code_references()

        # Build key findings
        findings = self._extract_key_findings()

        # Build critical constraints
        constraints = self._extract_critical_constraints()

        return StagePromptContext(
            project_name=self.context.project_name,
            legacy_tech_stack=legacy_stack,
            proposed_tech_stack=proposed_stack,
            analysis_date=self.context.analysis_date,
            code_references=code_refs,
            key_findings=findings,
            critical_constraints=constraints
        )

    def _format_legacy_stack(self) -> str:
        """Format legacy tech stack as readable string."""
        parts = [self.context.scan_result.tech_stack.primary_language.title()]

        if self.context.scan_result.tech_stack.runtime_version:
            parts[0] += f" {self.context.scan_result.tech_stack.runtime_version}"

        if self.context.scan_result.tech_stack.frameworks:
            parts.append(", ".join(self.context.scan_result.tech_stack.frameworks))

        if self.context.scan_result.tech_stack.package_manager:
            parts.append(self.context.scan_result.tech_stack.package_manager)

        return ", ".join(parts)

    def _format_proposed_stack(self) -> str:
        """Format proposed tech stack with LTS versions."""
        primary = self.context.scan_result.tech_stack.primary_language.lower()

        # Map to proposed LTS versions
        lts_mapping = {
            "python": "Python 3.12 (LTS until 2028)",
            "javascript": "Node.js 20 LTS (until 2026)",
            "typescript": "TypeScript 5.x + Node.js 20 LTS",
            "java": "Java 21 LTS (until 2029)",
            "csharp": ".NET 8 LTS (until 2026)",
            "ruby": "Ruby 3.3",
            "php": "PHP 8.3",
            "go": "Go 1.21+",
            "rust": "Rust 1.75+"
        }

        proposed = lts_mapping.get(primary, f"{primary.title()} (latest stable)")

        # Add framework suggestions if applicable
        if "react" in str(self.context.scan_result.tech_stack.frameworks).lower():
            proposed += ", React 18+"
        elif "vue" in str(self.context.scan_result.tech_stack.frameworks).lower():
            proposed += ", Vue 3+"
        elif "angular" in str(self.context.scan_result.tech_stack.frameworks).lower():
            proposed += ", Angular 17+"

        return proposed

    def _extract_code_references(self) -> Dict[str, str]:
        """Extract key code area references."""
        refs = {}

        # Add structure-based references
        if self.context.scan_result.structure.source_dirs:
            refs["Source Code"] = ", ".join(self.context.scan_result.structure.source_dirs)

        if self.context.scan_result.structure.test_dirs:
            refs["Tests"] = ", ".join(self.context.scan_result.structure.test_dirs)

        if self.context.scan_result.structure.config_files:
            refs["Configuration"] = ", ".join(self.context.scan_result.structure.config_files[:3])

        # Add package manager files
        if self.context.scan_result.tech_stack.package_manager:
            if "npm" in self.context.scan_result.tech_stack.package_manager.lower():
                refs["Dependencies"] = "package.json"
            elif "pip" in self.context.scan_result.tech_stack.package_manager.lower():
                refs["Dependencies"] = "requirements.txt, setup.py"
            elif "maven" in self.context.scan_result.tech_stack.package_manager.lower():
                refs["Dependencies"] = "pom.xml"
            elif "gradle" in self.context.scan_result.tech_stack.package_manager.lower():
                refs["Dependencies"] = "build.gradle"

        return refs

    def _extract_key_findings(self) -> List[str]:
        """Extract key findings from analysis."""
        findings = []

        # Test coverage finding
        if self.context.metrics.test_coverage < 60:
            findings.append(f"Low test coverage ({self.context.metrics.test_coverage:.0f}%) - Modernization should improve this")
        elif self.context.metrics.test_coverage >= 80:
            findings.append(f"Good test coverage ({self.context.metrics.test_coverage:.0f}%) - Preserve testing practices")

        # Technical debt finding
        if self.context.metrics.technical_debt_percentage > 40:
            findings.append(f"High technical debt ({self.context.metrics.technical_debt_percentage:.0f}%) - Major refactoring opportunity")

        # Security finding
        vulnerable_count = sum(r.vulnerable_count for r in self.context.dependency_reports)
        if vulnerable_count > 0:
            findings.append(f"{vulnerable_count} vulnerable dependencies - MUST be addressed in modernization")

        # CI/CD finding
        if self.context.scan_result.structure.has_ci_cd:
            findings.append("CI/CD pipeline exists - Preserve automation practices")
        else:
            findings.append("No CI/CD - Modernization should add automated deployment")

        # Documentation finding
        if self.context.scan_result.structure.has_documentation:
            findings.append("Documentation present - Extract domain knowledge")
        else:
            findings.append("Limited documentation - Reverse engineer domain rules from code")

        return findings

    def _extract_critical_constraints(self) -> List[str]:
        """Extract critical constraints to preserve."""
        constraints = []

        # Add size-based constraints
        if self.context.metrics.lines_of_code > 50000:
            constraints.append(f"Large codebase ({self.context.metrics.lines_of_code:,} LOC) - Incremental migration recommended")

        # Add dependency constraints
        if self.context.metrics.total_dependencies > 50:
            constraints.append(f"Many dependencies ({self.context.metrics.total_dependencies}) - Careful upgrade planning needed")

        # Add framework constraints
        if self.context.scan_result.tech_stack.frameworks:
            constraints.append(f"Existing framework patterns ({', '.join(self.context.scan_result.tech_stack.frameworks)}) - Study before changing")

        # Add architecture constraints
        if self.context.metrics.modularity_score < 5:
            constraints.append("Low modularity - May need significant restructuring")

        return constraints

    def _generate_stage_prompt(self, stage: str, context: StagePromptContext) -> Path:
        """Generate prompt file for a specific stage."""
        # Map stage to generator method
        generators = {
            "1-constitution": self._generate_constitution_prompt,
            "2-specify": self._generate_specify_prompt,
            "3-clarify": self._generate_clarify_prompt,
            "4-plan": self._generate_plan_prompt,
            "5-tasks": self._generate_tasks_prompt,
            "6-analyze": self._generate_analyze_prompt,
            "7-implement": self._generate_implement_prompt,
            "8-checklist": self._generate_checklist_prompt
        }

        generator = generators[stage]
        content = generator(context)

        # Write to file
        prompt_path = self.prompts_dir / f"{stage}-prompt.md"
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(content)

        return prompt_path

    def _generate_constitution_prompt(self, ctx: StagePromptContext) -> str:
        """Generate constitution stage prompt."""
        return f"""# Constitution Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Legacy Code References

{self._format_code_references(ctx)}

## Extracted Principles

The legacy codebase analysis revealed these patterns worth preserving:

{self._format_findings_as_bullets(ctx.key_findings)}

## Suggested Constitution Principles

Based on analysis, consider including these principles:

### 1. Testing Standards

**Evidence**: Current test coverage is {self.context.metrics.test_coverage:.0f}%

**Recommendation**:
- MUST maintain minimum 80% test coverage for all new code
- SHOULD write tests before implementation (TDD)
- MUST include integration tests for all APIs

### 2. Security First

**Evidence**: {sum(r.vulnerable_count for r in self.context.dependency_reports)} vulnerable dependencies found

**Recommendation**:
- MUST address security vulnerabilities within 48 hours
- MUST use automated dependency scanning
- MUST validate all user inputs

### 3. Code Quality

**Evidence**: Code quality score: {self.context.metrics.code_quality_score:.1f}/10

**Recommendation**:
- MUST follow consistent code quality standards
- MUST enforce linting in CI/CD
- MUST require code reviews for all changes

### 4. Documentation

**Evidence**: {"Documentation present" if self.context.scan_result.structure.has_documentation else "Limited documentation"}

**Recommendation**:
- MUST document all public APIs
- SHOULD include inline comments for complex logic
- MUST maintain up-to-date README

## Suggested Prompt

When running `/speckit.constitution`, use this guidance:

```
Create a project constitution for modernizing {ctx.project_name}.

Legacy System Context:
- Current stack: {ctx.legacy_tech_stack}
- Target stack: {ctx.proposed_tech_stack}
- Key challenges: {", ".join(ctx.critical_constraints[:2])}

Preserve these good practices:
{self._format_findings_as_bullets([f for f in ctx.key_findings if "Preserve" in f or "Good" in f])}

Address these gaps:
{self._format_findings_as_bullets([f for f in ctx.key_findings if "No " in f or "Low" in f or "Limited" in f])}

Include principles for: testing, security, code quality, documentation, and deployment automation.
```

## Next Steps

1. Review the `extracted-principles.md` file for detailed analysis
2. Run `/speckit.constitution` with the suggested prompt above
3. Adjust principles based on team discussion
4. Proceed to Specify stage with constitution in place
"""

    def _generate_specify_prompt(self, ctx: StagePromptContext) -> str:
        """Generate specify stage prompt."""
        return f"""# Specify Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Legacy Code References

{self._format_code_references(ctx)}

## Functional Requirements Context

The legacy system provides these capabilities (preserve in modernized version):

{self._format_findings_as_bullets(ctx.key_findings)}

## Feature Inventory

Based on codebase analysis:

- **Lines of Code**: {self.context.metrics.lines_of_code:,}
- **File Count**: {self.context.scan_result.metrics.file_count}
- **Languages**: {", ".join(self.context.scan_result.tech_stack.languages)}
- **Frameworks**: {", ".join(self.context.scan_result.tech_stack.frameworks) if self.context.scan_result.tech_stack.frameworks else "None detected"}

**Source Directories**: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "Not detected"}

**Recommendation**: Review each source directory to identify features and user workflows.

## Critical Behaviors to Preserve

{self._format_constraints_as_bullets(ctx.critical_constraints)}

## Suggested Prompt

When running `/speckit.specify`, use this guidance:

```
Create a functional specification for modernizing {ctx.project_name}.

Legacy System Overview:
- Current implementation: {ctx.legacy_tech_stack}
- Size: {self.context.metrics.lines_of_code:,} lines of code
- Structure: {", ".join(self.context.scan_result.structure.source_dirs[:3]) if self.context.scan_result.structure.source_dirs else "Standard layout"}

Requirements:
1. Preserve all existing functionality (see functional-spec.md for details)
2. Address these issues: {", ".join(ctx.critical_constraints[:2])}
3. Improve: {", ".join([f for f in ctx.key_findings if "should" in f.lower()][:2])}

Target: Modern, maintainable implementation with {ctx.proposed_tech_stack}
```

## Reference Documents

- **functional-spec.md**: Complete feature inventory from legacy system
- **analysis-report.md**: Technical details and metrics

## Next Steps

1. Review `functional-spec.md` for complete legacy feature list
2. Run `/speckit.specify` with suggested prompt
3. Ensure all critical legacy behaviors are captured
4. Proceed to Clarify stage for ambiguity resolution
"""

    def _generate_clarify_prompt(self, ctx: StagePromptContext) -> str:
        """Generate clarify stage prompt."""
        return f"""# Clarify Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Legacy Code References

{self._format_code_references(ctx)}

## Ambiguity Resolution Rules

When specifications are unclear, follow this decision tree:

### Step 1: Check Legacy Code

Before asking questions, examine the legacy implementation:

{self._format_code_references(ctx)}

### Step 2: Legacy as Source of Truth

The legacy codebase is the authoritative source for:

- **Business Logic**: How features actually work
- **Edge Cases**: How system handles unexpected inputs
- **Validation Rules**: What input constraints exist
- **Error Handling**: How errors are reported/handled
- **Performance Expectations**: Current throughput/latency

### Step 3: Document Findings

If legacy code clarifies the ambiguity:
- Document the discovered behavior in spec
- Reference legacy code location (file:line)
- Mark as "PRESERVE EXACTLY" if critical (security, payments, etc.)

### Step 4: Escalate Remaining Ambiguities

If still unclear after checking legacy code:
- ASK USER for clarification
- NEVER guess or assume behavior
- Provide options based on common patterns

## Critical Legacy Behaviors

These MUST be preserved exactly (check code before making changes):

{self._format_constraints_as_bullets(ctx.critical_constraints)}

## Common Ambiguity Patterns

### Pattern 1: Validation Rules

**If unclear**: Check legacy validation code in:
{self._get_validation_hint()}

### Pattern 2: Error Handling

**If unclear**: Check legacy error handling patterns in:
{self._get_error_handling_hint()}

### Pattern 3: Business Rules

**If unclear**: Check legacy business logic in:
{", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "source code"}

## Suggested Prompt

When running `/speckit.clarify`, use this guidance:

```
Clarify ambiguities in the specification for {ctx.project_name} modernization.

Legacy Code as Reference:
- Location: {", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "project root"}
- When unclear, refer to legacy implementation as source of truth
- Preserve critical behaviors: {", ".join(ctx.critical_constraints[:2])}

For each ambiguity:
1. Check corresponding legacy code first
2. If behavior is clear, document it with code reference
3. If still unclear after checking code, ask me (don't assume)

Mark as CRITICAL any behavior related to: security, payments, data integrity, user authentication.
```

## Next Steps

1. Review specification for ambiguities
2. Run `/speckit.clarify` with legacy code references
3. Ensure critical behaviors are explicitly documented
4. Proceed to Plan stage with clear requirements
"""

    def _generate_plan_prompt(self, ctx: StagePromptContext) -> str:
        """Generate plan stage prompt."""
        return f"""# Plan Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Legacy Architecture Context

**Current Structure**:
- **Source**: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "Standard layout"}
- **Tests**: {", ".join(self.context.scan_result.structure.test_dirs) if self.context.scan_result.structure.test_dirs else "No test directories"}
- **CI/CD**: {"Present" if self.context.scan_result.structure.has_ci_cd else "Not detected"}
- **Modularity Score**: {self.context.metrics.modularity_score:.1f}/10
- **Architecture Score**: {self.context.metrics.architecture_score:.1f}/10

## Proposed Tech Stack with LTS

See `proposed-tech-stack.md` for detailed recommendations:

**Summary**:
- **Target**: {ctx.proposed_tech_stack}
- **Migration Complexity**: {self._assess_migration_complexity()}
- **Estimated Effort**: {self._estimate_migration_effort()}

## Architecture Recommendations

### 1. Preserve Good Patterns

{self._format_good_patterns()}

### 2. Fix Anti-Patterns

{self._format_anti_patterns()}

### 3. Modernization Opportunities

{self._format_modernization_opportunities()}

## Critical Constraints

{self._format_constraints_as_bullets(ctx.critical_constraints)}

## Suggested Prompt

When running `/speckit.plan`, use this guidance:

```
Create technical plan for modernizing {ctx.project_name}.

Target Tech Stack:
{ctx.proposed_tech_stack}
(See proposed-tech-stack.md for detailed rationale)

Legacy Architecture:
- Current: {ctx.legacy_tech_stack}
- Modularity: {self.context.metrics.modularity_score:.1f}/10
- {"Preserve: " + ", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "Standard structure"}

Requirements:
1. {"Add CI/CD pipeline" if not self.context.scan_result.structure.has_ci_cd else "Enhance existing CI/CD"}
2. {"Improve test coverage from " + str(int(self.context.metrics.test_coverage)) + "% to 80%+" if self.context.metrics.test_coverage < 80 else "Maintain " + str(int(self.context.metrics.test_coverage)) + "% test coverage"}
3. Address: {", ".join(ctx.critical_constraints[:2])}
4. Migration approach: {self._recommend_migration_approach()}

Design for: maintainability, testability, security, and scalability.
```

## Reference Documents

- **proposed-tech-stack.md**: Detailed tech stack recommendations with LTS versions
- **functional-spec.md**: Complete feature requirements
- **analysis-report.md**: Current state assessment

## Next Steps

1. Review `proposed-tech-stack.md` for technology choices
2. Run `/speckit.plan` with suggested prompt
3. Ensure plan addresses all critical constraints
4. Proceed to Tasks stage for breakdown
"""

    def _generate_tasks_prompt(self, ctx: StagePromptContext) -> str:
        """Generate tasks stage prompt."""
        return f"""# Tasks Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Complexity Hints from Analysis

**Project Size**: {self.context.metrics.lines_of_code:,} lines of code
**Estimated Effort**: {self._estimate_task_breakdown_effort()}
**Recommended Approach**: {self._recommend_task_breakdown_approach()}

## Task Breakdown Guidance

### Phase 0: Foundation (1-2 weeks)

**Effort Estimate**: {self._estimate_foundation_effort()}

Suggested tasks:
- [ ] Set up project structure with {ctx.proposed_tech_stack}
- [ ] {"Migrate existing CI/CD" if self.context.scan_result.structure.has_ci_cd else "Set up CI/CD pipeline"}
- [ ] Configure linting and code quality tools
- [ ] Set up test framework (target: 80%+ coverage)
- [ ] Create development/staging/production environments

### Phase 1: Core Migration (varies by size)

**Effort Estimate**: {self._estimate_core_migration_effort()}

Breakdown by complexity:
- **High Complexity**: {len([c for c in ctx.critical_constraints if "Large" in c or "Many" in c])} areas
- **Medium Complexity**: Standard business logic
- **Low Complexity**: Configuration, utilities

### Phase 2: Testing & Quality (2-4 weeks)

**Current Coverage**: {self.context.metrics.test_coverage:.0f}%
**Target Coverage**: 80%+

Suggested tasks:
- [ ] Write unit tests for all business logic
- [ ] Write integration tests for all APIs
- [ ] {"Migrate existing tests" if self.context.scan_result.structure.has_tests else "Create test suite from scratch"}
- [ ] Set up test automation in CI/CD
- [ ] Performance testing and optimization

### Phase 3: Deployment (1-2 weeks)

Suggested tasks:
- [ ] Deploy to staging environment
- [ ] Run acceptance testing
- [ ] Fix any deployment issues
- [ ] Deploy to production
- [ ] Monitor and validate

## Legacy Code Reference for Task Estimation

{self._format_code_references(ctx)}

**Use legacy code to estimate**:
- Complexity of each feature (lines of code, dependencies)
- Test coverage needs (examine existing tests)
- Integration points (external services, databases)

## Suggested Prompt

When running `/speckit.tasks`, use this guidance:

```
Break down modernization of {ctx.project_name} into concrete tasks.

Project Context:
- Size: {self.context.metrics.lines_of_code:,} lines of code
- Complexity: {self._assess_overall_complexity()}
- Recommended approach: {self._recommend_task_breakdown_approach()}

Task Breakdown:
- Phase 0: Foundation setup (1-2 weeks)
- Phase 1: Core migration ({self._estimate_core_migration_effort()})
- Phase 2: Testing & quality (2-4 weeks, target 80%+ coverage)
- Phase 3: Deployment (1-2 weeks)

Prioritize:
1. Critical business logic first (payments, auth, data integrity)
2. High-value user features
3. Nice-to-have enhancements last

Reference legacy code in: {", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "project root"}
```

## Next Steps

1. Run `/speckit.tasks` with suggested prompt
2. Review and adjust task estimates based on team capacity
3. Identify dependencies between tasks
4. Proceed to Analyze stage for validation
"""

    def _generate_analyze_prompt(self, ctx: StagePromptContext) -> str:
        """Generate analyze stage prompt."""
        return f"""# Analyze Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Consistency Checks Against Legacy

Use the legacy codebase as validation reference:

### 1. Feature Completeness

**Verify**: All legacy features are in the specification

**Legacy Features**: Review code in:
{", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "source directories"}

**Check**:
- [ ] All API endpoints documented?
- [ ] All user workflows captured?
- [ ] All configuration options included?
- [ ] All business rules specified?

### 2. Behavior Preservation

**Verify**: Critical behaviors are preserved exactly

**Critical Areas**:
{self._format_constraints_as_bullets(ctx.critical_constraints)}

**Check**:
- [ ] Security mechanisms maintained?
- [ ] Data validation rules documented?
- [ ] Error handling specified?
- [ ] Performance requirements defined?

### 3. Technical Feasibility

**Verify**: Plan is technically sound

**Legacy Constraints**:
- Current architecture score: {self.context.metrics.architecture_score:.1f}/10
- Current modularity: {self.context.metrics.modularity_score:.1f}/10
- Current technical debt: {self.context.metrics.technical_debt_percentage:.0f}%

**Check**:
- [ ] Migration approach matches project size?
- [ ] Tech stack choices justified?
- [ ] Dependencies properly analyzed?
- [ ] Testing strategy adequate?

### 4. Gap Analysis

**Verify**: All improvements are addressed

**Known Gaps from Legacy**:
{self._format_legacy_gaps()}

**Check**:
- [ ] {"CI/CD pipeline added?" if not self.context.scan_result.structure.has_ci_cd else "CI/CD enhancements included?"}
- [ ] {"Test coverage improvements planned?" if self.context.metrics.test_coverage < 80 else "Test coverage maintained?"}
- [ ] Security vulnerabilities addressed? ({sum(r.vulnerable_count for r in self.context.dependency_reports)} found)
- [ ] Technical debt reduction planned? ({self.context.metrics.technical_debt_percentage:.0f}% current)

## Suggested Prompt

When running `/speckit.analyze`, use this guidance:

```
Analyze the specification, plan, and tasks for {ctx.project_name} modernization.

Validate against legacy system:
- Legacy location: {", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "project root"}
- Reference: functional-spec.md for complete feature list

Consistency Checks:
1. Feature completeness - All legacy features in spec?
2. Behavior preservation - Critical behaviors preserved?
3. Technical feasibility - Plan matches project constraints?
4. Gap analysis - All improvements addressed?

Flag any:
- Missing features from legacy
- Unclear specifications (reference legacy code)
- Technical risks or concerns
- Gaps in testing/deployment strategy
```

## Reference Documents

- **functional-spec.md**: Complete legacy feature inventory
- **analysis-report.md**: Technical metrics and assessment
- **proposed-tech-stack.md**: Technology decisions rationale

## Next Steps

1. Run `/speckit.analyze` with validation criteria
2. Address any gaps or inconsistencies found
3. Ensure all critical behaviors are verified
4. Proceed to Implement stage with confidence
"""

    def _generate_implement_prompt(self, ctx: StagePromptContext) -> str:
        """Generate implement stage prompt."""
        return f"""# Implement Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Legacy Code References for Implementation

When implementing features, reference legacy code for behavior details:

{self._format_code_references(ctx)}

## Implementation Guidelines

### 1. Preserve Critical Behaviors

**CRITICAL** - Implement exactly as in legacy:

{self._format_critical_behaviors()}

**How to verify**:
1. Review legacy code implementation
2. Extract exact business rules
3. Implement with same logic (modernized syntax)
4. Test against legacy behavior

### 2. Modernize Implementation

**OK to change** - Implementation details (not behavior):

- Code style and formatting (use modern conventions)
- Error handling (use modern patterns like try/catch)
- Logging (use structured logging)
- Configuration (use environment variables)
- {"Testing (add comprehensive tests - currently " + str(int(self.context.metrics.test_coverage)) + "%)" if self.context.metrics.test_coverage < 80 else "Testing (maintain " + str(int(self.context.metrics.test_coverage)) + "% coverage)"}

### 3. Reference Legacy for Edge Cases

When handling edge cases:

1. Check how legacy code handles it
2. Preserve behavior if part of contract
3. Fix if clearly a bug (document decision)
4. Ask if unclear

**Example areas to check**:
- Null/undefined handling
- Empty string/array handling
- Boundary conditions (max/min values)
- Concurrent access patterns
- Error recovery

### 4. Test Against Legacy Behavior

**Test Strategy**:

1. **Unit Tests**: Test same inputs/outputs as legacy
2. **Integration Tests**: Test same workflows as legacy
3. **Acceptance Tests**: Verify same user experience
4. **Performance Tests**: Match or exceed legacy performance

**Current Legacy Metrics**:
- Lines of code: {self.context.metrics.lines_of_code:,}
- Test coverage: {self.context.metrics.test_coverage:.0f}%
- File count: {self.context.scan_result.metrics.file_count}

## Code Quality Standards

**Target Improvements**:

- **Test Coverage**: {self.context.metrics.test_coverage:.0f}% → 80%+
- **Code Quality**: {self.context.metrics.code_quality_score:.1f}/10 → 8.5+/10
- **Documentation**: {self.context.metrics.documentation_quality:.1f}/10 → 8.0+/10
- **Technical Debt**: {self.context.metrics.technical_debt_percentage:.0f}% → <20%

## Suggested Prompt

When running `/speckit.implement`, use this guidance:

```
Implement modernization of {ctx.project_name} according to spec and plan.

Legacy Code Reference:
- Location: {", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "project root"}
- Use for: Business logic, edge cases, validation rules
- Preserve: Critical behaviors (security, payments, data integrity)
- Modernize: Code style, error handling, testing, logging

Implementation Standards:
- Test coverage: 80%+ (currently {self.context.metrics.test_coverage:.0f}%)
- Code quality: 8.5+/10 (currently {self.context.metrics.code_quality_score:.1f}/10)
- Follow plan.md architecture decisions
- Reference spec.md for requirements

For each feature:
1. Review legacy implementation
2. Extract business rules
3. Implement with modern patterns
4. Test against legacy behavior
5. Document any deviations
```

## Critical Constraints

{self._format_constraints_as_bullets(ctx.critical_constraints)}

## Next Steps

1. Run `/speckit.implement` following guidelines above
2. Reference legacy code for each feature
3. Ensure all tests pass (80%+ coverage target)
4. Proceed to Checklist stage for final validation
"""

    def _generate_checklist_prompt(self, ctx: StagePromptContext) -> str:
        """Generate checklist stage prompt."""
        return f"""# Checklist Stage Guidance (from Legacy Analysis)

## Quick Reference

**Project**: {ctx.project_name}
**Legacy Tech Stack**: {ctx.legacy_tech_stack}
**Proposed Tech Stack**: {ctx.proposed_tech_stack}
**Analysis Date**: {ctx.analysis_date}

## Quality Validation Checklist

### 1. Feature Completeness

Compare against legacy system:

**Legacy Baseline**:
- Source: {", ".join(self.context.scan_result.structure.source_dirs) if self.context.scan_result.structure.source_dirs else "project root"}
- Files: {self.context.scan_result.metrics.file_count}
- Lines: {self.context.metrics.lines_of_code:,}

**Validation**:
- [ ] All legacy features implemented?
- [ ] All API endpoints migrated?
- [ ] All user workflows working?
- [ ] All configuration options supported?

### 2. Behavior Validation

Verify critical behaviors match legacy:

{self._format_critical_behaviors()}

**Validation**:
- [ ] Security mechanisms working?
- [ ] Data validation correct?
- [ ] Error handling appropriate?
- [ ] Performance acceptable?

### 3. Quality Improvements

Verify modernization goals achieved:

**Targets vs Legacy**:
- Test coverage: 80%+ target (legacy: {self.context.metrics.test_coverage:.0f}%)
- Code quality: 8.5+/10 target (legacy: {self.context.metrics.code_quality_score:.1f}/10)
- Technical debt: <20% target (legacy: {self.context.metrics.technical_debt_percentage:.0f}%)
- CI/CD: {"Enhance" if self.context.scan_result.structure.has_ci_cd else "Add new"} pipeline

**Validation**:
- [ ] Test coverage ≥ 80%?
- [ ] All tests passing?
- [ ] Code quality score ≥ 8.5?
- [ ] {"CI/CD pipeline working?" if not self.context.scan_result.structure.has_ci_cd else "CI/CD enhancements deployed?"}
- [ ] Documentation complete?
- [ ] Security vulnerabilities fixed? (legacy had {sum(r.vulnerable_count for r in self.context.dependency_reports)})

### 4. Deployment Readiness

**Legacy System Context**:
- {"CI/CD: Present" if self.context.scan_result.structure.has_ci_cd else "CI/CD: Not detected"}
- {"Tests: Present" if self.context.scan_result.structure.has_tests else "Tests: Not detected"}
- Vulnerabilities: {sum(r.vulnerable_count for r in self.context.dependency_reports)}

**Validation**:
- [ ] All environments configured (dev/staging/prod)?
- [ ] Deployment automation working?
- [ ] Rollback plan tested?
- [ ] Monitoring/logging set up?
- [ ] Performance benchmarks met?
- [ ] Security scan passed?

### 5. Documentation

**Validation**:
- [ ] README updated?
- [ ] API documentation complete?
- [ ] Deployment guide created?
- [ ] Architecture documented?
- [ ] Constitution followed?

## Suggested Prompt

When running `/speckit.checklist`, use this guidance:

```
Create final validation checklist for {ctx.project_name} modernization.

Legacy Baseline:
- Location: {", ".join(self.context.scan_result.structure.source_dirs[:2]) if self.context.scan_result.structure.source_dirs else "project root"}
- Metrics: {self.context.metrics.lines_of_code:,} LOC, {self.context.metrics.test_coverage:.0f}% coverage
- Issues: {sum(r.vulnerable_count for r in self.context.dependency_reports)} vulnerabilities, {self.context.metrics.technical_debt_percentage:.0f}% tech debt

Validation Categories:
1. Feature completeness (all legacy features working)
2. Behavior validation (critical behaviors preserved)
3. Quality improvements (test coverage, code quality, tech debt)
4. Deployment readiness (CI/CD, monitoring, security)
5. Documentation (complete and accurate)

Success Criteria:
- All legacy features working
- Test coverage ≥ 80%
- Code quality ≥ 8.5/10
- 0 critical vulnerabilities
- All acceptance tests passing
```

## Final Validation

Before marking complete:

1. **Smoke Test**: Run through all major user workflows
2. **Performance Test**: Compare against legacy benchmarks
3. **Security Scan**: Verify no critical vulnerabilities
4. **Stakeholder Review**: Demo to stakeholders
5. **Go/No-Go Decision**: All critical items checked?

## Next Steps

1. Run `/speckit.checklist` with validation criteria
2. Complete all checklist items
3. Fix any issues found
4. Get stakeholder approval
5. Deploy to production
6. Monitor and iterate

---

**Congratulations!** You've completed the analysis-driven modernization workflow.
"""

    def _generate_readme(self) -> Path:
        """Generate README for stage-prompts directory."""
        content = f"""# Stage Prompts for {self.context.project_name}

**Generated**: {self.context.analysis_date}
**Purpose**: Guide spec-driven workflow with legacy code context

---

## Overview

This directory contains 8 stage-specific prompts that inject legacy codebase context into each phase of the modernization workflow. Each prompt provides:

- Legacy code references (file paths and locations)
- Critical behaviors to preserve
- Recommended approach based on analysis
- Ready-to-use prompts for each stage command

## Usage

### Quick Start

1. **Review** the prompt file for your current stage
2. **Copy** the "Suggested Prompt" section
3. **Run** the corresponding `/speckit.[stage]` command
4. **Reference** legacy code locations as needed

### Stage-by-Stage Guide

#### Stage 1: Constitution

**File**: `1-constitution-prompt.md`
**Purpose**: Extract principles from legacy codebase
**Key Content**: Testing standards, security principles, quality guidelines

**Usage**:
```bash
# Read the prompt
cat stage-prompts/1-constitution-prompt.md

# Use suggested prompt with /speckit.constitution
```

#### Stage 2: Specify

**File**: `2-specify-prompt.md`
**Purpose**: Document functional requirements based on legacy features
**Key Content**: Feature inventory, critical behaviors, functional scope

**Usage**: Run `/speckit.specify` with context from functional-spec.md

#### Stage 3: Clarify

**File**: `3-clarify-prompt.md`
**Purpose**: Resolve ambiguities using legacy code as source of truth
**Key Content**: Ambiguity resolution rules, code references, decision tree

**Usage**: When unclear, check legacy code FIRST, then ask if still unclear

#### Stage 4: Plan

**File**: `4-plan-prompt.md`
**Purpose**: Design architecture with legacy context and LTS recommendations
**Key Content**: Proposed tech stack, migration approach, architecture guidance

**Usage**: Reference proposed-tech-stack.md for technology decisions

#### Stage 5: Tasks

**File**: `5-tasks-prompt.md`
**Purpose**: Break down work with complexity hints from analysis
**Key Content**: Effort estimates, phase breakdown, complexity indicators

**Usage**: Use legacy code size/complexity for task estimation

#### Stage 6: Analyze

**File**: `6-analyze-prompt.md`
**Purpose**: Validate consistency against legacy system
**Key Content**: Validation checklist, gap analysis, completeness checks

**Usage**: Verify all legacy features are in spec before implementing

#### Stage 7: Implement

**File**: `7-implement-prompt.md`
**Purpose**: Guide implementation with legacy behavior references
**Key Content**: Code references, critical behaviors, testing guidance

**Usage**: Reference legacy code for business logic and edge cases

#### Stage 8: Checklist

**File**: `8-checklist-prompt.md`
**Purpose**: Final validation against legacy baseline
**Key Content**: Quality checklist, deployment readiness, acceptance criteria

**Usage**: Verify all modernization goals achieved before release

---

## Best Practices

### 1. Legacy Code as Source of Truth

When specifications are unclear:
1. ✅ **First**: Check corresponding legacy code
2. ✅ **Then**: Document discovered behavior in spec
3. ✅ **Finally**: Ask user if still unclear
4. ❌ **Never**: Guess or assume behavior

### 2. Preserve Critical Behaviors

Some behaviors MUST be preserved exactly:
- Security mechanisms (authentication, encryption, audit)
- Payment processing (retries, idempotency, validation)
- Data integrity rules (validation, constraints, relationships)
- Regulatory compliance (GDPR, SOX, HIPAA, etc.)

**How to identify**: Look for keywords in legacy code like "security", "payment", "audit", "compliance"

### 3. Modernize Implementation, Not Behavior

**Preserve** (what it does):
- Business logic and rules
- Validation constraints
- Error handling behavior
- API contracts

**Modernize** (how it does it):
- Code style and formatting
- Testing approach and coverage
- Logging and monitoring
- Configuration management
- Error reporting

---

## Reference Documents

This directory works with other analysis artifacts:

- **analysis-report.md**: Complete technical analysis
- **functional-spec.md**: Legacy feature inventory
- **extracted-principles.md**: Principles from codebase patterns
- **proposed-tech-stack.md**: Technology recommendations with LTS
- **upgrade-plan.md**: Phased upgrade approach (if inline)
- **recommended-constitution.md**: Constitution template (if greenfield)

---

## Troubleshooting

### Problem: Prompt is too generic

**Solution**: Review the corresponding reference document (functional-spec.md, proposed-tech-stack.md) for specific details

### Problem: Legacy code references are unclear

**Solution**: Examine the actual source directories listed in the prompt - they contain the implementation details

### Problem: Critical behaviors not specified

**Solution**: Review functional-spec.md "CRITICAL Features" section and add to specification

### Problem: Tech stack choices unclear

**Solution**: Review proposed-tech-stack.md for detailed rationale and alternatives

---

## Workflow Summary

```
1. Constitution  → Extract principles from legacy patterns
2. Specify       → Document features from legacy system
3. Clarify       → Use legacy code to resolve ambiguities
4. Plan          → Design with legacy constraints + LTS tech
5. Tasks         → Break down using legacy complexity hints
6. Analyze       → Validate against legacy completeness
7. Implement     → Reference legacy for business logic
8. Checklist     → Final validation against legacy baseline
```

Each stage builds on analysis artifacts to ensure modernization preserves what works while fixing what doesn't.

---

**Generated by**: Spec Kit Analyzer Phase 7 (Analysis-to-Spec Workflow Integration)
**Analysis Date**: {self.context.analysis_date}
**Project**: {self.context.project_name}
"""

        readme_path = self.prompts_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

        return readme_path

    # Helper methods for formatting

    def _format_code_references(self, ctx: StagePromptContext) -> str:
        """Format code references as bullet list."""
        if not ctx.code_references:
            return "- No specific code references available (examine source directories)"

        return "\n".join([
            f"- **{area}**: `{ref}`"
            for area, ref in ctx.code_references.items()
        ])

    def _format_findings_as_bullets(self, findings: List[str]) -> str:
        """Format findings as bullet list."""
        if not findings:
            return "- None identified in automated analysis"
        return "\n".join([f"- {finding}" for finding in findings])

    def _format_constraints_as_bullets(self, constraints: List[str]) -> str:
        """Format constraints as bullet list."""
        if not constraints:
            return "- No critical constraints identified"
        return "\n".join([f"- {constraint}" for constraint in constraints])

    def _assess_migration_complexity(self) -> str:
        """Assess migration complexity."""
        if self.context.metrics.lines_of_code > 100000:
            return "HIGH"
        elif self.context.metrics.lines_of_code > 20000:
            return "MEDIUM"
        else:
            return "LOW"

    def _estimate_migration_effort(self) -> str:
        """Estimate migration effort."""
        loc = self.context.metrics.lines_of_code
        if loc < 10000:
            return "2-4 weeks"
        elif loc < 50000:
            return "2-3 months"
        else:
            return "4-6 months"

    def _recommend_migration_approach(self) -> str:
        """Recommend migration approach."""
        if self.context.metrics.lines_of_code > 50000 or self.context.metrics.technical_debt_percentage > 60:
            return "Incremental (Strangler Fig pattern)"
        elif self.context.metrics.technical_debt_percentage < 30 and self.context.scan_result.structure.has_tests:
            return "Big Bang (high test coverage supports full migration)"
        else:
            return "Phased (module by module)"

    def _format_good_patterns(self) -> str:
        """Format good patterns from legacy."""
        patterns = []

        if self.context.scan_result.structure.has_ci_cd:
            patterns.append("- CI/CD automation exists - preserve and enhance")

        if self.context.metrics.test_coverage >= 60:
            patterns.append(f"- Good test coverage ({self.context.metrics.test_coverage:.0f}%) - maintain or improve")

        if self.context.scan_result.structure.has_documentation:
            patterns.append("- Documentation maintained - continue practice")

        if not patterns:
            patterns.append("- Review legacy code for domain-specific patterns to preserve")

        return "\n".join(patterns)

    def _format_anti_patterns(self) -> str:
        """Format anti-patterns from legacy."""
        patterns = []

        if not self.context.scan_result.structure.has_tests:
            patterns.append("- No automated testing - add comprehensive test suite")

        if self.context.metrics.test_coverage < 60:
            patterns.append(f"- Low test coverage ({self.context.metrics.test_coverage:.0f}%) - increase to 80%+")

        if not self.context.scan_result.structure.has_ci_cd:
            patterns.append("- No CI/CD pipeline - add automated deployment")

        if self.context.metrics.modularity_score < 5:
            patterns.append(f"- Low modularity ({self.context.metrics.modularity_score:.1f}/10) - improve separation of concerns")

        if not patterns:
            patterns.append("- None identified in automated analysis - manual code review recommended")

        return "\n".join(patterns)

    def _format_modernization_opportunities(self) -> str:
        """Format modernization opportunities."""
        opportunities = []

        vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)
        if vulnerable > 0:
            opportunities.append(f"- Security: Fix {vulnerable} vulnerable dependencies")

        outdated = sum(r.outdated_count for r in self.context.dependency_reports)
        if outdated > 0:
            opportunities.append(f"- Dependencies: Update {outdated} outdated packages")

        if self.context.metrics.technical_debt_percentage > 40:
            opportunities.append(f"- Technical Debt: Reduce from {self.context.metrics.technical_debt_percentage:.0f}% to <20%")

        if self.context.metrics.code_quality_score < 7:
            opportunities.append(f"- Code Quality: Improve from {self.context.metrics.code_quality_score:.1f} to 8.5+")

        if not opportunities:
            opportunities.append("- General modernization: Latest LTS versions, modern patterns, best practices")

        return "\n".join(opportunities)

    def _estimate_task_breakdown_effort(self) -> str:
        """Estimate effort for task breakdown."""
        if self.context.metrics.lines_of_code < 10000:
            return "Small project - 20-40 tasks"
        elif self.context.metrics.lines_of_code < 50000:
            return "Medium project - 40-80 tasks"
        else:
            return "Large project - 80-150 tasks"

    def _recommend_task_breakdown_approach(self) -> str:
        """Recommend task breakdown approach."""
        if self.context.metrics.modularity_score >= 7:
            return "Module-based (high modularity supports clean breakdown)"
        elif self.context.scan_result.structure.source_dirs:
            return f"Directory-based (organize by: {', '.join(self.context.scan_result.structure.source_dirs[:3])})"
        else:
            return "Feature-based (break down by user-facing functionality)"

    def _estimate_foundation_effort(self) -> str:
        """Estimate foundation setup effort."""
        if self.context.scan_result.structure.has_ci_cd:
            return "1 week (migrate existing CI/CD)"
        else:
            return "1-2 weeks (create CI/CD from scratch)"

    def _estimate_core_migration_effort(self) -> str:
        """Estimate core migration effort."""
        return self._estimate_migration_effort()

    def _assess_overall_complexity(self) -> str:
        """Assess overall project complexity."""
        complexity_score = (
            (self.context.metrics.lines_of_code / 10000) * 0.3 +
            (self.context.metrics.technical_debt_percentage / 10) * 0.3 +
            (10 - self.context.metrics.modularity_score) * 0.2 +
            (self.context.metrics.total_dependencies / 50) * 0.2
        )

        if complexity_score > 7:
            return "High complexity"
        elif complexity_score > 4:
            return "Medium complexity"
        else:
            return "Low complexity"

    def _format_critical_behaviors(self) -> str:
        """Format critical behaviors to preserve."""
        behaviors = []

        # Check for security indicators
        if any("auth" in str(d).lower() or "security" in str(d).lower()
               for d in self.context.scan_result.structure.config_files):
            behaviors.append("- **Authentication/Authorization**: Preserve exact security mechanisms")

        # Check for database/data indicators
        if any("db" in str(d).lower() or "database" in str(d).lower()
               for d in self.context.scan_result.structure.config_files):
            behaviors.append("- **Data Integrity**: Preserve validation rules and constraints")

        # Check for payment/financial indicators
        if self.context.scan_result.tech_stack.frameworks:
            behaviors.append("- **Business Logic**: Preserve core business rules and workflows")

        # Add test-based critical behaviors
        if self.context.scan_result.structure.has_tests:
            behaviors.append("- **Tested Behaviors**: All existing test cases must still pass")

        if not behaviors:
            behaviors.append("- Review legacy code to identify critical business logic")

        return "\n".join(behaviors)

    def _format_legacy_gaps(self) -> str:
        """Format legacy gaps that need addressing."""
        gaps = []

        if not self.context.scan_result.structure.has_ci_cd:
            gaps.append("- No CI/CD pipeline")

        if self.context.metrics.test_coverage < 60:
            gaps.append(f"- Low test coverage ({self.context.metrics.test_coverage:.0f}%)")

        vulnerable = sum(r.vulnerable_count for r in self.context.dependency_reports)
        if vulnerable > 0:
            gaps.append(f"- {vulnerable} security vulnerabilities")

        if self.context.metrics.technical_debt_percentage > 40:
            gaps.append(f"- High technical debt ({self.context.metrics.technical_debt_percentage:.0f}%)")

        if not gaps:
            gaps.append("- None identified in automated analysis")

        return "\n".join(gaps)

    def _get_validation_hint(self) -> str:
        """Get hint for where to find validation code."""
        if self.context.scan_result.structure.source_dirs:
            return f"{self.context.scan_result.structure.source_dirs[0]} (look for validation, schema, or model files)"
        return "source code (look for validation, schema, or model files)"

    def _get_error_handling_hint(self) -> str:
        """Get hint for where to find error handling code."""
        if self.context.scan_result.structure.source_dirs:
            return f"{self.context.scan_result.structure.source_dirs[0]} (look for error, exception, or handler files)"
        return "source code (look for error, exception, or handler files)"


def main():
    """Example usage of PromptGenerator."""
    print("PromptGenerator module loaded successfully")
    print("This module is called by ReportGenerator during analysis")


if __name__ == "__main__":
    main()
