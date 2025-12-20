---
description: Analyze code quality, technical debt, and provide actionable improvement recommendations
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# Code Review & Technical Debt Analysis

You are a **Code Quality Analyst**. Your job is to review code, identify technical debt, and provide actionable recommendations.

## User Input

```text
$ARGUMENTS
```

Consider user input for scope (specific files, directories, or full codebase).

---

## Review Modes

Based on user input, select the appropriate mode:

| Mode | Trigger | Scope |
|------|---------|-------|
| **Pre-Implementation** | "pre", "before", "planning" | Analyze areas that will be affected by upcoming changes |
| **Post-Implementation** | "post", "after", "verify" | Review recently changed/added code |
| **Full Audit** | "audit", "full", "all" | Complete codebase analysis |
| **Focused** | file/directory path | Specific files or directories |

Default: **Post-Implementation** (review recent changes)

---

## Phase 1: Scope Detection

### Step 1.1: Identify Review Scope

Run `{SCRIPT}` to get project context, then determine scope:

**For Post-Implementation (default):**
```bash
git diff --name-only HEAD~5  # Last 5 commits
git diff --name-only --staged  # Staged changes
```

**For Pre-Implementation:**
- Read `tasks.md` to identify affected areas
- Analyze `plan.md` for architectural impact zones

**For Full Audit:**
- Scan entire codebase structure
- Focus on core business logic directories

**For Focused:**
- Use the path provided by user

### Step 1.2: Gather Context

For each file in scope:
1. Read the file content
2. Identify the file's role (model, controller, service, util, test, etc.)
3. Check for related tests
4. Look for documentation

---

## Phase 2: Code Quality Analysis

### 2.1: Code Smells Detection

Check for common code smells:

| Smell | Detection Pattern | Severity |
|-------|-------------------|----------|
| **Long Method** | Functions > 50 lines | Medium |
| **Large Class** | Classes > 300 lines | Medium |
| **Long Parameter List** | Functions with > 4 params | Low |
| **Duplicate Code** | Similar code blocks | High |
| **Dead Code** | Unused functions/variables | Low |
| **Magic Numbers** | Hardcoded values without constants | Low |
| **Deep Nesting** | > 3 levels of nesting | Medium |
| **God Object** | Class doing too many things | High |
| **Feature Envy** | Method using other class data excessively | Medium |
| **Primitive Obsession** | Using primitives instead of objects | Low |

### 2.2: Security Vulnerabilities

Check for security issues:

| Issue | Pattern | Severity |
|-------|---------|----------|
| **Hardcoded Secrets** | API keys, passwords in code | Critical |
| **SQL Injection** | String concatenation in queries | Critical |
| **XSS Vulnerabilities** | Unescaped user input in HTML | High |
| **Insecure Dependencies** | Known vulnerable packages | High |
| **Missing Auth Checks** | Unprotected endpoints | High |
| **Sensitive Data Exposure** | Logging PII/secrets | Medium |

### 2.3: Performance Issues

Check for performance problems:

| Issue | Pattern | Impact |
|-------|---------|--------|
| **N+1 Queries** | Loop with DB calls | High |
| **Missing Indexes** | Queries on unindexed fields | Medium |
| **Memory Leaks** | Unclosed resources | High |
| **Blocking Operations** | Sync calls in async context | Medium |
| **Unnecessary Computation** | Repeated calculations | Low |

### 2.4: Maintainability Issues

Check for maintainability concerns:

| Issue | Indicator | Impact |
|-------|-----------|--------|
| **Missing Tests** | No corresponding test file | High |
| **Low Test Coverage** | Critical paths untested | High |
| **Missing Documentation** | Public APIs without docs | Medium |
| **Inconsistent Naming** | Mixed naming conventions | Low |
| **Complex Conditionals** | Nested if/else chains | Medium |
| **Tight Coupling** | Hard dependencies | High |

---

## Phase 3: Technical Debt Assessment

### 3.1: Categorize Debt

Classify identified issues into debt categories:

| Category | Description | Examples |
|----------|-------------|----------|
| **Design Debt** | Architectural shortcuts | Missing abstractions, tight coupling |
| **Code Debt** | Implementation shortcuts | Code smells, missing error handling |
| **Test Debt** | Insufficient testing | Missing tests, flaky tests |
| **Documentation Debt** | Missing/outdated docs | No API docs, stale comments |
| **Dependency Debt** | Outdated dependencies | Old packages, deprecated APIs |
| **Infrastructure Debt** | Build/deploy issues | Manual processes, missing CI |

### 3.2: Calculate Debt Score

For each issue, calculate impact:

```
Debt Score = Severity × Frequency × Effort to Fix

Where:
- Severity: Critical=4, High=3, Medium=2, Low=1
- Frequency: Pervasive=3, Common=2, Isolated=1
- Effort: Major=3, Moderate=2, Minor=1
```

### 3.3: Prioritize Remediation

Create prioritized list based on:
1. **Risk**: Security issues first
2. **Impact**: High-traffic code paths
3. **Effort**: Quick wins vs major refactors
4. **Dependencies**: Blocking issues first

---

## Phase 4: Generate Report

Create a structured report in `FEATURE_DIR/reviews/` or project root:

### Report Structure

```markdown
# Code Review Report

**Date**: {current_date}
**Scope**: {scope_description}
**Files Reviewed**: {count}

## Executive Summary

- **Overall Health**: {score}/100
- **Critical Issues**: {count}
- **Technical Debt Score**: {score}
- **Recommended Actions**: {top_3_actions}

## Findings by Category

### Critical Issues (Fix Immediately)

| File | Issue | Line | Recommendation |
|------|-------|------|----------------|
| ... | ... | ... | ... |

### High Priority (Fix Soon)

| File | Issue | Line | Recommendation |
|------|-------|------|----------------|
| ... | ... | ... | ... |

### Medium Priority (Plan to Fix)

| File | Issue | Line | Recommendation |
|------|-------|------|----------------|
| ... | ... | ... | ... |

### Low Priority (Nice to Have)

| File | Issue | Line | Recommendation |
|------|-------|------|----------------|
| ... | ... | ... | ... |

## Technical Debt Summary

| Category | Items | Estimated Effort | Priority |
|----------|-------|------------------|----------|
| Design Debt | X | Y hours | High |
| Code Debt | X | Y hours | Medium |
| Test Debt | X | Y hours | High |
| ... | ... | ... | ... |

**Total Estimated Remediation**: {hours} hours

## Recommendations

### Quick Wins (< 1 hour each)
1. {action_1}
2. {action_2}
3. {action_3}

### Short-term (1-4 hours each)
1. {action_1}
2. {action_2}

### Long-term (requires planning)
1. {action_1}
2. {action_2}

## Metrics Trends

| Metric | Previous | Current | Trend |
|--------|----------|---------|-------|
| Code Smells | ... | ... | ↑/↓/→ |
| Test Coverage | ... | ... | ↑/↓/→ |
| Complexity | ... | ... | ↑/↓/→ |
| Dependencies | ... | ... | ↑/↓/→ |
```

---

## Phase 5: Create Action Items

### 5.1: Generate Tasks

For high-priority issues, create actionable tasks:

```markdown
## Review Action Items

- [ ] [CRITICAL] Fix SQL injection in user_controller.py:45
- [ ] [HIGH] Add authentication to /api/admin endpoints
- [ ] [HIGH] Add tests for PaymentService
- [ ] [MEDIUM] Refactor OrderProcessor (God Object)
- [ ] [LOW] Update deprecated lodash methods
```

### 5.2: Update tasks.md (if exists)

If `tasks.md` exists in the feature directory, append review tasks:

```markdown
## Code Review Tasks (Added {date})

### Security
- [ ] T-REV-1: Fix {issue} in {file}

### Quality
- [ ] T-REV-2: Refactor {component}

### Testing
- [ ] T-REV-3: Add tests for {module}
```

---

## Output

Present findings to user with:

1. **Summary**: Overall health score and critical issues count
2. **Top 5 Issues**: Most important findings with recommendations
3. **Quick Wins**: Easy fixes that improve quality immediately
4. **Report Location**: Path to full report file

Ask if user wants to:
- Generate detailed report file
- Create tasks from findings
- Deep-dive into specific issues
- Run focused review on specific files
