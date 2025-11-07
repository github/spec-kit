---
description: Perform a comprehensive project analysis against all SpecKit specifications to verify whether the project meets all defined expectations, including optional code pattern and principles validation.
scripts:
  sh: scripts/bash/project-analysis.sh --json
  ps: scripts/powershell/project-analysis.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify `--check-patterns` or similar flags to enable optional code pattern analysis.

## Goal

Perform a comprehensive project-wide analysis to verify that:
1. All SpecKit specifications are complete and properly structured
2. The codebase implements the requirements defined in specifications
3. Code follows approved patterns and principles (when `--check-patterns` is enabled)
4. Generate a detailed Markdown report with findings, recommendations, and compliance status

This command provides a holistic view of project health and specification compliance across ALL features, not just the current branch.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured analysis report and generate a Markdown file summarizing findings.

**Constitution Authority**: The project constitution (`/memory/constitution.md`) is the highest authority for project principles. Any violations must be flagged as CRITICAL.

**Comprehensive Scope**: Unlike `/speckit.analyze` which focuses on a single feature, this command analyzes the ENTIRE project across all specifications.

## Execution Steps

### 1. Parse User Arguments

Check if the user requested pattern analysis:
- Look for `--check-patterns`, `check-patterns`, `patterns`, or similar keywords in `$ARGUMENTS`
- Set `PATTERN_CHECK_ENABLED` flag accordingly
- If enabled, the analysis will include Security, DRY, KISS, SOLID, and architectural pattern validation

### 2. Initialize Analysis Context

Run `{SCRIPT}` (with `--check-patterns` if requested) from repo root and parse JSON output:

```bash
# Example: scripts/bash/project-analysis.sh --json [--check-patterns]
```

Expected JSON structure:
```json
{
  "repo_root": "/path/to/repo",
  "specs_dir": "/path/to/repo/specs",
  "constitution_exists": true,
  "constitution_file": "/path/to/constitution.md",
  "pattern_check_enabled": false,
  "detected_languages": "Python,JavaScript/TypeScript",
  "source_dirs": "src,lib",
  "total_specs": 3,
  "specs": [
    {
      "name": "001-feature-name",
      "dir": "/path/to/specs/001-feature-name",
      "has_spec": true,
      "has_plan": true,
      "has_tasks": true,
      "has_research": false,
      "has_data_model": true,
      "has_quickstart": false,
      "has_contracts": true,
      "spec_lines": 250,
      "plan_lines": 180,
      "tasks_lines": 450
    }
  ]
}
```

### 3. Validate Constitution Presence

Load `/memory/constitution.md` if it exists. If missing:
- Flag as CRITICAL issue
- Recommend creating a constitution using `/speckit.constitution`
- Continue analysis with reduced constitutional checks

### 4. Load and Analyze Each Specification

For each specification in the `specs` array, progressively load and analyze:

#### A. Specification Completeness Check

For each spec directory, verify:
- **spec.md** exists (CRITICAL if missing)
- **plan.md** exists (HIGH if missing for specs with tasks)
- **tasks.md** exists (MEDIUM if missing, indicates incomplete workflow)
- **data-model.md** exists (LOW if missing, but recommended for data-intensive features)
- **contracts/** directory exists (LOW if missing, but recommended for API features)

#### B. Specification Quality Analysis

For each `spec.md` file:
1. **Ambiguity Detection**
   - Flag vague requirements (fast, scalable, secure, intuitive, robust) without measurable criteria
   - Detect placeholders (TODO, TKTK, ???, `<placeholder>`, TBD)
   - Identify incomplete user stories

2. **Completeness Assessment**
   - Verify presence of required sections:
     - User Scenarios & Testing
     - Functional Requirements
     - Non-Functional Requirements
     - Key Entities
     - Success Criteria
   - Check for empty or stub sections

3. **Testability Evaluation**
   - Requirements must have measurable acceptance criteria
   - User stories must be independently testable
   - Edge cases should be explicitly documented

#### C. Implementation Plan Analysis

For each `plan.md` file:
1. **Technical Alignment**
   - Verify technology choices align with detected languages
   - Check for architectural consistency across features
   - Validate project structure matches source directories

2. **Constitution Compliance**
   - Extract constitution principles from `/memory/constitution.md`
   - Verify plan sections explicitly address MUST principles
   - Flag any conflicts with constitutional requirements

3. **Complexity Tracking**
   - Identify complexity justifications
   - Validate that deviations are documented

#### D. Task Coverage Analysis

For each `tasks.md` file:
1. **Requirement-Task Mapping**
   - Build semantic model of requirements from spec.md
   - Map each task to requirements by keyword matching
   - Identify requirements with zero task coverage (HIGH severity)
   - Identify orphan tasks with no requirement mapping (MEDIUM severity)

2. **Dependency Validation**
   - Check task ordering for logical dependencies
   - Verify foundational tasks precede integration tasks
   - Validate parallel markers [P] are appropriate

#### E. Cross-Specification Consistency

Analyze consistency across ALL specifications:
1. **Terminology Consistency**
   - Build vocabulary of terms across all specs
   - Flag terminology drift (same concept, different names)
   - Identify potential naming conflicts

2. **Architectural Consistency**
   - Verify consistent technology stack choices
   - Check for conflicting architectural approaches
   - Validate shared infrastructure patterns

3. **Data Model Consistency**
   - If data-model.md exists, check for entity conflicts
   - Verify relationship consistency across features
   - Identify duplicate or overlapping entities

### 5. Code-Specification Compliance (Always Enabled)

For EVERY specification with a plan and tasks, verify code implementation:

#### A. File Existence Verification
- For tasks referencing specific file paths, check if files exist in codebase
- For planned components/modules, verify implementation exists
- Flag missing implementations as HIGH severity

#### B. Requirement Traceability
- Search codebase for evidence of requirement implementation
- Use file paths, module names, and component references from tasks
- Identify requirements with no code evidence (HIGH severity)

#### C. API Contract Validation
- If `contracts/` directory exists with API specifications:
  - Search for endpoint implementations
  - Verify HTTP methods match specifications
  - Check for request/response structure alignment

### 6. Code Pattern Analysis (When `--check-patterns` Enabled)

If pattern checking is enabled, perform additional analysis:

#### A. Security Best Practices

Scan for common security issues:
- **SQL Injection**: Look for string concatenation in database queries
- **XSS Vulnerabilities**: Check for unescaped user input in templates/HTML
- **Authentication Issues**: Verify proper authentication in API endpoints
- **Secrets in Code**: Search for hardcoded passwords, API keys, tokens
- **CORS Misconfigurations**: Check for overly permissive CORS settings
- **Input Validation**: Verify user input validation exists

Pattern searches (language-specific):
```python
# Python examples
# SQL Injection patterns
"execute(" + "string concatenation"
".format()" in SQL queries
f"SELECT * FROM {user_input}"

# Hardcoded secrets
"password = '..."
"api_key = '..."
"secret_key = '..."
```

```javascript
// JavaScript/TypeScript examples
// XSS patterns
innerHTML =
dangerouslySetInnerHTML
eval(

// Hardcoded secrets
const apiKey = "..."
const password = "..."
```

#### B. DRY (Don't Repeat Yourself) Analysis

Detect code duplication:
- Search for similar function names across files (e.g., `validate_email` in multiple files)
- Identify copied logic patterns
- Flag duplicate utility functions
- Recommend extraction to shared modules

Heuristics:
- Similar function names in different files (edit distance < 3)
- Long similar code blocks (>10 lines, >80% similarity)
- Duplicate string constants

#### C. KISS (Keep It Simple, Stupid) Evaluation

Identify overly complex code:
- **Function Length**: Flag functions >50 lines
- **Cyclomatic Complexity**: Identify deeply nested conditionals (>4 levels)
- **Parameter Count**: Flag functions with >5 parameters
- **Class Size**: Flag classes with >10 methods

Language-specific patterns:
```python
# Python: Count nested if/for/while
def complex_function():  # Flag if too many nested levels
    if condition1:
        for item in items:
            if condition2:
                while condition3:
                    if condition4:  # 4 levels deep - flag!
```

#### D. SOLID Principles Assessment

Validate SOLID adherence:

1. **Single Responsibility**
   - Check class/module names for "and", "or" (e.g., `UserAndOrderManager`)
   - Flag classes with >10 methods or multiple unrelated method groups
   - Identify "God classes" doing too much

2. **Open/Closed**
   - Look for hardcoded conditional chains that should use polymorphism
   - Identify switch statements on type that could be abstracted

3. **Liskov Substitution**
   - Check for child classes that override parent methods with empty implementations
   - Identify type checking before method calls

4. **Interface Segregation**
   - Flag large interfaces with >7 methods
   - Identify classes implementing interfaces but throwing "not implemented" errors

5. **Dependency Inversion**
   - Check for direct instantiation of concrete classes in business logic
   - Verify dependency injection patterns are used
   - Look for tight coupling to specific implementations

#### E. Architectural Pattern Compliance

Verify approved architectural approaches from constitution:

1. **Extract Approved Patterns** from constitution
   - Library-first approach
   - CLI interface requirements
   - Test-first development
   - Layered architecture
   - Microservices patterns
   - Other project-specific patterns

2. **Validate Code Structure**
   - Check if libraries are standalone and testable
   - Verify CLI entry points exist
   - Confirm test files exist for each module
   - Validate layer separation (if layered architecture)

3. **Flag Violations**
   - Code violating architectural patterns (CRITICAL)
   - Missing test files (HIGH)
   - Tight coupling between layers (MEDIUM)

### 7. Issue Severity Classification

Assign severity to all findings using this heuristic:

- **CRITICAL**:
  - Missing constitution
  - Missing spec.md for any feature
  - Constitution MUST principle violations
  - Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
  - Requirements with zero code implementation (for completed features)

- **HIGH**:
  - Missing plan.md for features with tasks
  - Architectural pattern violations
  - Duplicate or conflicting requirements across specs
  - Missing implementations for defined tasks
  - Ambiguous security or performance requirements
  - Significant code duplication (DRY violations)

- **MEDIUM**:
  - Missing tasks.md
  - Terminology drift across specifications
  - Missing non-functional requirement coverage in tasks
  - Code complexity violations (KISS)
  - SOLID principle violations
  - Missing or incomplete data models

- **LOW**:
  - Missing optional files (research.md, quickstart.md)
  - Style and wording improvements
  - Minor redundancy
  - Documentation gaps

### 8. Generate Comprehensive Markdown Report

Create a detailed report file: `project-analysis-report.md`

Report structure:

```markdown
# Project Analysis Report

**Generated**: [TIMESTAMP]
**Repository**: [REPO_ROOT]
**Total Specifications**: [COUNT]
**Pattern Check**: [Enabled/Disabled]

---

## Executive Summary

[Provide 3-5 sentence overview of project health]

**Overall Compliance**: [Excellent/Good/Fair/Poor]
**Critical Issues**: [COUNT]
**High Priority Issues**: [COUNT]
**Medium Priority Issues**: [COUNT]
**Low Priority Issues**: [COUNT]

**Key Findings**:
- [Top 3-5 most important findings]

---

## Specification Completeness

| Spec | spec.md | plan.md | tasks.md | data-model.md | Status |
|------|---------|---------|----------|---------------|--------|
| 001-feature-a | ✓ | ✓ | ✓ | ✓ | Complete |
| 002-feature-b | ✓ | ✓ | ✗ | ✗ | Incomplete |

**Summary**:
- X of Y specifications are complete
- Y specifications missing critical files

---

## Constitution Compliance

**Constitution Status**: [Found/Missing]

[If missing, add CRITICAL recommendation to create one]

[If found, list principle violations]

### Principle Violations

| Specification | Principle | Severity | Issue | Recommendation |
|---------------|-----------|----------|-------|----------------|
| 001-feature-a | Test-First | CRITICAL | No test files found | Implement TDD workflow |

---

## Issues by Severity

### CRITICAL Issues (Count: X)

| ID | Category | Specification | Location | Summary | Recommendation |
|----|----------|---------------|----------|---------|----------------|
| C1 | Security | 001-feature-a | src/api/auth.py:45 | SQL Injection vulnerability | Use parameterized queries |
| C2 | Constitution | ALL | - | Missing project constitution | Run /speckit.constitution |

[Repeat for each CRITICAL issue]

### HIGH Priority Issues (Count: X)

[Same table format]

### MEDIUM Priority Issues (Count: X)

[Same table format]

### LOW Priority Issues (Count: X)

[Same table format - limit to top 10, summarize remainder]

---

## Code-Specification Alignment

### Implementation Coverage

| Specification | Requirements | Tasks | Implemented | Coverage % | Status |
|---------------|--------------|-------|-------------|------------|--------|
| 001-feature-a | 15 | 42 | 38 | 90% | In Progress |
| 002-feature-b | 8 | 24 | 24 | 100% | Complete |

### Missing Implementations

[List requirements with defined tasks but no code evidence]

### Orphan Code

[List implemented code with no corresponding specification]

---

## Code Quality Analysis

[Include this section only if --check-patterns was enabled]

### Security Assessment

**Security Issues Found**: X

[List security findings with code locations]

### DRY (Don't Repeat Yourself)

**Duplication Instances**: X

[List significant code duplication with file locations]

### KISS (Keep It Simple, Stupid)

**Complexity Issues**: X

[List overly complex functions/classes]

### SOLID Principles

**SOLID Violations**: X

[List principle violations with examples]

### Architectural Patterns

**Pattern Compliance**: [X/Y patterns followed]

[List architectural deviations]

---

## Cross-Specification Consistency

### Terminology Analysis

**Terminology Drift Instances**: X

[List terms used inconsistently]

### Architectural Consistency

[List technology stack inconsistencies]

### Data Model Consistency

[List entity conflicts or duplications]

---

## Recommendations

### Immediate Actions (Critical/High)

1. [ACTION] - [JUSTIFICATION]
2. [ACTION] - [JUSTIFICATION]

### Short-term Improvements (Medium)

1. [ACTION] - [JUSTIFICATION]
2. [ACTION] - [JUSTIFICATION]

### Long-term Enhancements (Low)

1. [ACTION] - [JUSTIFICATION]
2. [ACTION] - [JUSTIFICATION]

---

## Metrics Summary

| Metric | Value |
|--------|-------|
| Total Specifications | X |
| Complete Specifications | X |
| Total Requirements | X |
| Total Tasks | X |
| Implementation Coverage | XX% |
| Average Spec Quality | Good/Fair/Poor |
| Critical Issues | X |
| High Priority Issues | X |
| Medium Priority Issues | X |
| Low Priority Issues | X |
| Overall Health Score | XX/100 |

---

## Next Steps

[Provide clear, actionable next steps based on findings]

1. **If CRITICAL issues exist**: MUST resolve before continuing development
   - [Specific command or action]
   - [Specific command or action]

2. **If only HIGH/MEDIUM issues**: May proceed with caution
   - [Improvement suggestions]
   - [Refactoring recommendations]

3. **Recommended Commands**:
   - `/speckit.constitution` - If constitution missing
   - `/speckit.specify` - To refine ambiguous specifications
   - `/speckit.plan` - To update architectural approach
   - `/speckit.tasks` - To add coverage for unmapped requirements

---

## Appendix

### Analysis Configuration

- Pattern Check: [Enabled/Disabled]
- Detected Languages: [LIST]
- Source Directories: [LIST]
- Analysis Timestamp: [TIMESTAMP]
- Report Version: 1.0

### Glossary

[Define key terms used in report]
```

### 9. Display Report Summary

After generating the report file, display a concise summary to the user:

```
Project Analysis Complete!

Report saved to: project-analysis-report.md

📊 Summary:
  • Total Specifications: X
  • Critical Issues: X
  • High Priority Issues: X
  • Medium Priority Issues: X
  • Low Priority Issues: X
  • Overall Health: [Excellent/Good/Fair/Poor]

🔍 Top Issues:
  1. [Issue summary]
  2. [Issue summary]
  3. [Issue summary]

📋 Next Actions:
  [Most important action to take]

To view the full report, open: project-analysis-report.md
```

### 10. Offer Detailed Issue Resolution

Ask the user:
> "Would you like me to create a detailed remediation plan for the top [N] CRITICAL/HIGH issues?"

If user agrees, create a separate document: `project-analysis-remediation.md` with:
- Detailed description of each issue
- Root cause analysis
- Step-by-step resolution guide
- Code examples (before/after if applicable)
- Testing recommendations

## Operating Principles

### Analysis Quality

- **Comprehensive Coverage**: Analyze ALL specifications, not just a sample
- **Evidence-Based**: Base findings on actual code and specification content
- **Actionable**: Every issue must have a clear recommendation
- **Prioritized**: Focus on high-impact issues first
- **Balanced**: Acknowledge what's working well, not just problems

### Context Efficiency

- **Progressive Disclosure**: Load specifications incrementally to manage tokens
- **Focused Scanning**: Use targeted searches for pattern analysis, not full file reads
- **Summarization**: Aggregate similar issues to avoid repetition
- **Smart Sampling**: For large codebases, sample representative files for pattern analysis

### Accuracy Standards

- **NEVER modify files** (this is read-only analysis)
- **NEVER hallucinate findings** (all issues must be verifiable)
- **NEVER skip constitution check** (always prioritize)
- **NEVER report false positives** (verify before flagging)
- **ALWAYS provide file locations** (specific line numbers when possible)

### Report Quality

- **Clear Structure**: Follow the report template exactly
- **Professional Tone**: Objective, constructive, solution-oriented
- **Specific Examples**: Cite actual code/specification locations
- **Measurable Metrics**: Provide concrete numbers and percentages
- **Actionable Recommendations**: Every finding needs a clear next step

## Pattern Analysis Guidelines

When `--check-patterns` is enabled, follow these guidelines:

### 1. Language-Specific Analysis

Adapt pattern checks to detected languages:
- Python: Check for PEP 8 violations, proper exception handling
- JavaScript/TypeScript: Check for async/await patterns, promise handling
- Go: Check for error handling, goroutine management
- Java: Check for exception handling, interface usage

### 2. Search Strategy

Use efficient code searching:
```
# Instead of reading entire files, use targeted searches:
# Security: Search for dangerous patterns
grep -r "eval(" src/
grep -r "innerHTML" src/
grep -r "execute(" src/

# DRY: Search for duplicate function names
grep -r "def function_name" src/ | sort | uniq -d

# Complexity: Count nested indentation
grep -E "^[\t ]{16,}" src/*.py  # 4+ levels of nesting
```

### 3. False Positive Management

Avoid false positives:
- Check context before flagging (e.g., `eval()` in safe sandbox)
- Verify security issues are actual vulnerabilities, not test code
- Distinguish between intentional complexity and unnecessary complexity
- Consider framework conventions (e.g., Rails "magic" is intentional)

### 4. Sampling for Large Codebases

For projects with >100 source files:
- Sample 20-30 representative files for pattern analysis
- Focus on critical paths (API endpoints, auth, data access)
- Extrapolate findings to estimate project-wide issues
- Note sampling methodology in report

## Error Handling

Handle common errors gracefully:

1. **Missing specs directory**: Report clearly and suggest running `/speckit.specify`
2. **Empty specification**: Flag as CRITICAL and recommend completion
3. **Malformed files**: Report parsing errors with file location
4. **Permission errors**: Note files that couldn't be accessed
5. **Large codebase timeouts**: Use sampling and note in report

## Validation Checklist

Before finalizing the report, verify:

- [ ] All specifications have been analyzed
- [ ] Constitution compliance has been checked
- [ ] Issue severity is correctly assigned
- [ ] Every issue has a recommendation
- [ ] File locations are specific and accurate
- [ ] Metrics are calculated correctly
- [ ] Report structure matches template
- [ ] Next actions are clear and actionable
- [ ] Report file has been generated successfully
- [ ] User has been notified of report location

## Context

{ARGS}
