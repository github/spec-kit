---
description: Analyze code quality, technical debt, and provide actionable improvement recommendations
semantic_anchors:
  - Code Smell Catalog    # Martin Fowler's refactoring patterns, detection heuristics
  - OWASP Top 10          # Security vulnerability classification
  - Technical Debt Quadrant  # Martin Fowler: Reckless/Prudent × Deliberate/Inadvertent
  - Cyclomatic Complexity # McCabe metric for code complexity
  - SOLID Principles      # Design quality indicators
  - Boy Scout Rule        # Leave code better than you found it
handoffs:
  - label: Deep Fix
    agent: speckit.fix
    prompt: Diagnose root causes and create a comprehensive correction plan
  - label: Implement Fixes
    agent: speckit.implement
    prompt: Execute the correction tasks from review
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

# Code Review & Technical Debt Analysis

> **Activated Frameworks**: Code Smell Catalog (Martin Fowler), OWASP Top 10, Technical Debt Quadrant, Cyclomatic Complexity, SOLID Principles.

You are a **Code Quality Analyst** applying Martin Fowler's Code Smell Catalog and Technical Debt Quadrant. Your job is to review code, identify technical debt (classify as Reckless/Prudent × Deliberate/Inadvertent), and provide actionable recommendations following the Boy Scout Rule.

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

First, detect if on a feature branch and get the appropriate diff:

```bash
# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)

# Check if this is a feature branch (pattern: ###-name or feature/*)
if [[ "$CURRENT_BRANCH" =~ ^[0-9]+-.*$ ]] || [[ "$CURRENT_BRANCH" =~ ^feature/.* ]]; then
    # Determine base branch (main, master, or develop)
    BASE_BRANCH=$(git remote show origin | grep 'HEAD branch' | cut -d' ' -f5)
    if [ -z "$BASE_BRANCH" ]; then
        BASE_BRANCH="main"
    fi

    # Diff against base branch - ALL changes in this feature branch
    git diff --name-only "$BASE_BRANCH"...HEAD
else
    # Not on feature branch - use last 5 commits
    git diff --name-only HEAD~5
fi
```

**IMPORTANT**: When on a feature branch, the review scope MUST include ALL changes since branching from main/master, not just recent commits. This ensures the review covers the complete feature implementation.

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
| **Magic Numbers** | Hardcoded values without constants | Low |
| **Deep Nesting** | > 3 levels of nesting | Medium |
| **God Object** | Class doing too many things | High |
| **Feature Envy** | Method using other class data excessively | Medium |
| **Primitive Obsession** | Using primitives instead of objects | Low |

### 2.2: Dead Code Detection

Identify code that is never executed, never called, or no longer reachable:

| Pattern | Detection Method | Severity |
|---------|-----------------|----------|
| **Unused exports** | Exported functions/classes with zero imports across the project | High |
| **Unused variables/params** | Declared but never read (beyond linter suppression `_var`) | Medium |
| **Unreachable code** | Code after unconditional `return`, `throw`, `break`, `continue` | Medium |
| **Dead branches** | Conditions that always evaluate to the same value | Medium |
| **Commented-out code** | Large blocks of commented code (> 5 lines) — not comments explaining why | High |
| **Orphaned files** | Source files not imported by any other file and not an entry point | High |
| **Unused dependencies** | Packages in package.json/requirements.txt not imported anywhere | Medium |
| **Stale feature flags** | Feature flags that are always on/off with no toggle path | Low |

**Detection approach**:
```bash
# Unused exports (TypeScript/JavaScript example)
# For each exported symbol, check if it's imported anywhere else
grep -r "export " {scope}/ --include="*.ts" --include="*.tsx" | while read export_line; do
  symbol=$(echo "$export_line" | grep -oP '(?:export\s+(?:default\s+)?(?:function|class|const|let|var|type|interface|enum)\s+)\K\w+')
  if [ -n "$symbol" ]; then
    import_count=$(grep -r "$symbol" {scope}/ --include="*.ts" --include="*.tsx" -l | wc -l)
    if [ "$import_count" -le 1 ]; then
      echo "UNUSED: $symbol in $export_line"
    fi
  fi
done

# Commented-out code blocks
grep -n "^\s*//.*[;{}()=]" {scope}/ -r --include="*.ts" --include="*.tsx" | head -20
grep -n "^\s*/\*" {scope}/ -r --include="*.ts" | head -20

# Orphaned files (no imports found)
for file in $(find {scope}/ -name "*.ts" -not -name "*.test.*" -not -name "*.spec.*"); do
  basename=$(basename "$file" .ts)
  import_count=$(grep -r "$basename" {scope}/ --include="*.ts" -l | grep -v "$file" | wc -l)
  if [ "$import_count" -eq 0 ]; then
    echo "ORPHAN: $file"
  fi
done
```

**Report format**:

| File | Line | Dead Code Type | Evidence | Recommendation |
|------|------|---------------|----------|----------------|
| {file} | {line} | Unused export / Orphaned file / etc. | {why it's dead} | Remove / Archive / Investigate |

### 2.3: Fake Implementations & Incomplete Code

> **Critical**: Detect code that appears implemented but is actually a placeholder, mock, stub, or incomplete implementation left in production code. These are the most dangerous form of technical debt because they pass superficial review.

**Scan for these patterns**:

| Pattern | Detection Method | Severity |
|---------|-----------------|----------|
| **TODO/FIXME/HACK/XXX** | Comments containing `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, `TEMPORARY` | High |
| **Placeholder returns** | Functions returning hardcoded values (`return []`, `return {}`, `return null`, `return "placeholder"`) | Critical |
| **Empty implementations** | Functions with empty body or only a `pass`/`return` statement | Critical |
| **Mock data in production** | Hardcoded test data, fake emails, "test@test.com", "lorem ipsum", dummy IDs | Critical |
| **Stubbed error handling** | `catch(e) {}`, `catch(e) { console.log(e) }`, silently swallowed errors | High |
| **Disabled validations** | Validation functions that always return `true` or skip checks | Critical |
| **Hardcoded feature bypasses** | `if (true)`, `if (false)`, `// skip for now`, `// disabled` | High |
| **Console.log/print left behind** | Debug output in production code | Medium |
| **NotImplementedError stubs** | `raise NotImplementedError`, `throw new Error("not implemented")` | Critical |
| **Fake async operations** | `setTimeout` or `sleep` simulating real operations | High |

**Detection approach**:
```bash
# TODO/FIXME/HACK markers
grep -rn "TODO\|FIXME\|HACK\|XXX\|TEMP\b\|TEMPORARY\|PLACEHOLDER" {scope}/ \
  --include="*.ts" --include="*.tsx" --include="*.py" --include="*.go" --include="*.rs" \
  --exclude-dir=node_modules --exclude-dir=.git

# Placeholder returns
grep -rn "return \[\]\|return {}\|return null\|return None\|return ''\|return \"\"" {scope}/ \
  --include="*.ts" --include="*.py" --include="*.go"

# Empty function bodies
grep -rn -A1 "function\|def \|fn " {scope}/ --include="*.ts" --include="*.py" --include="*.rs" | \
  grep -B1 "^\s*[}]\|^\s*pass\|^\s*return;"

# Mock data patterns
grep -rn "test@test\|example@\|lorem ipsum\|foo\|bar\|baz\|dummy\|fake\|mock" {scope}/ \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  --exclude-dir=__tests__ --exclude-dir=tests --exclude-dir=test --exclude-dir=*.test.* --exclude-dir=*.spec.*

# Not implemented stubs
grep -rn "NotImplementedError\|not implemented\|throw.*Error.*implement\|todo.*implement\|stub" {scope}/ \
  --include="*.ts" --include="*.py" --include="*.go" --include="*.rs"

# Swallowed errors
grep -rn "catch.*{}\|catch.*{\s*}\|except.*pass\|except.*:\s*$" {scope}/ \
  --include="*.ts" --include="*.py"
```

**Report format**:

| File | Line | Fake Pattern | Code Snippet | Impact | Recommendation |
|------|------|-------------|--------------|--------|----------------|
| {file} | {line} | TODO / Placeholder / Mock data / etc. | `{snippet}` | {what breaks} | {what to implement} |

**Classification**:
- **Blocker**: Placeholder returns, empty implementations, disabled validations, NotImplementedError in production paths → MUST fix before merge
- **High**: TODOs in critical paths, mock data, swallowed errors → Fix in current iteration
- **Medium**: TODOs in non-critical paths, debug logs → Track for next iteration

### 2.4: Spec Deviation Detection

> **Purpose**: Compare the actual implementation against the feature specification to detect functional drift — where code does something different from what the spec requires.

**Prerequisites**: Requires `specs/{feature}/` with at least `spec.md` and ideally `plan.md`, `contracts/`, `data-model.md`.

#### Step 2.4.1: Load Spec Artifacts

For the feature being reviewed:
1. Read `spec.md` → Extract functional requirements (FR-xxx), acceptance criteria (Given/When/Then), success criteria
2. Read `plan.md` → Extract file-to-requirement mapping, architecture decisions
3. Read `contracts/` → Extract API contracts (endpoints, request/response schemas)
4. Read `data-model.md` → Extract entity definitions, fields, relationships, constraints
5. Read `task-results/` → Extract what was actually implemented per task, deviations already noted

#### Step 2.4.2: Requirement Coverage Analysis

For each functional requirement (FR-xxx) in `spec.md`:

| Requirement | Expected Behavior | Implementation File(s) | Actual Behavior | Status |
|-------------|-------------------|----------------------|-----------------|--------|
| FR-001 | {from spec} | {from plan/task-results} | {from code analysis} | MATCH / DRIFT / MISSING / PARTIAL |

**Status definitions**:
- **MATCH**: Implementation aligns with spec requirement
- **DRIFT**: Implementation exists but behavior differs from spec (most dangerous)
- **MISSING**: No implementation found for this requirement
- **PARTIAL**: Implementation exists but is incomplete (some scenarios not handled)

#### Step 2.4.3: Contract Compliance

For each API contract in `contracts/`:

```bash
# Compare contract definition with actual implementation
# For each endpoint defined in contracts/:

# 1. Check route exists
grep -rn "{method} {path}\|{path}" {scope}/ --include="*.ts" --include="*.py"

# 2. Check request validation matches contract schema
# 3. Check response shape matches contract schema
# 4. Check error responses match contract error definitions
# 5. Check HTTP status codes match
```

| Contract | Endpoint | Contract Says | Code Does | Status |
|----------|----------|--------------|-----------|--------|
| {contract_file} | POST /api/users | Returns `{id, email, role}` | Returns `{id, email}` (missing `role`) | DRIFT |
| {contract_file} | GET /api/users/:id | 404 if not found | 500 (unhandled null) | DRIFT |

#### Step 2.4.4: Data Model Compliance

For each entity in `data-model.md`:

| Entity | Field | Spec Says | Code Says | Status |
|--------|-------|-----------|-----------|--------|
| User | email | UNIQUE, NOT NULL, format: RFC 5322 | UNIQUE, NOT NULL (no format validation) | DRIFT |
| Order | status | enum: draft, pending, confirmed, shipped | enum: draft, pending, confirmed (missing shipped) | DRIFT |

Check:
- All fields defined in spec exist in code (models, schemas, migrations)
- Field constraints match (unique, not null, types, formats)
- Relationships match (foreign keys, cardinality)
- Enum values match spec definitions

#### Step 2.4.5: Acceptance Criteria Verification

For each acceptance scenario (Given/When/Then) in `spec.md`:

| Scenario | Given | When | Then (Expected) | Code Path | Status |
|----------|-------|------|-----------------|-----------|--------|
| SC-001 | Valid credentials | POST /auth/login | Return JWT + 200 | auth.controller:45 | MATCH |
| SC-002 | Expired token | GET /api/data | Return 401 + refresh hint | middleware:22 | DRIFT (returns 403) |
| SC-003 | 5 failed attempts | POST /auth/login | Lock account 15min | — | MISSING |

**Detection approach**: For each scenario, trace the code path and verify:
1. The trigger (When) is handled by a route/function
2. The precondition (Given) is checked
3. The outcome (Then) matches what the code actually does
4. Error scenarios are handled as specified

#### Step 2.4.6: Spec Deviation Report

```markdown
## Spec Deviation Report

**Feature**: {feature_name}
**Spec**: specs/{feature}/spec.md
**Files Analyzed**: {count}

### Deviation Summary

| Category | Match | Drift | Missing | Partial | Total |
|----------|-------|-------|---------|---------|-------|
| Functional Requirements | X | X | X | X | X |
| API Contracts | X | X | X | X | X |
| Data Model | X | X | X | X | X |
| Acceptance Criteria | X | X | X | X | X |
| **Total** | **X** | **X** | **X** | **X** | **X** |

### Compliance Score: {matched / total * 100}%

### Critical Deviations (DRIFT)

| ID | What Spec Says | What Code Does | File:Line | Impact |
|----|---------------|----------------|-----------|--------|
| {id} | {spec_requirement} | {actual_behavior} | {file:line} | {user_impact} |

### Missing Implementations

| ID | Requirement | Expected In | Priority | Blocking? |
|----|------------|-------------|----------|-----------|
| {id} | {requirement} | {expected_file} | {P1/P2/P3} | {yes/no} |

### Partial Implementations

| ID | Requirement | What's Done | What's Missing | File:Line |
|----|------------|-------------|----------------|-----------|
| {id} | {requirement} | {done_part} | {missing_part} | {file:line} |
```

### 2.5: Security Vulnerabilities

Check for security issues (OWASP Top 10):

| Issue | Pattern | Severity |
|-------|---------|----------|
| **Hardcoded Secrets** | API keys, passwords in code | Critical |
| **SQL Injection** | String concatenation in queries | Critical |
| **XSS Vulnerabilities** | Unescaped user input in HTML | High |
| **Insecure Dependencies** | Known vulnerable packages | High |
| **Missing Auth Checks** | Unprotected endpoints | High |
| **Sensitive Data Exposure** | Logging PII/secrets | Medium |

### 2.6: Performance Issues

Check for performance problems:

| Issue | Pattern | Impact |
|-------|---------|--------|
| **N+1 Queries** | Loop with DB calls | High |
| **Missing Indexes** | Queries on unindexed fields | Medium |
| **Memory Leaks** | Unclosed resources | High |
| **Blocking Operations** | Sync calls in async context | Medium |
| **Unnecessary Computation** | Repeated calculations | Low |

### 2.7: Maintainability Issues

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
| **Dead Code Debt** | Unreachable or unused code | Orphaned files, unused exports, commented blocks |
| **Fake Implementation Debt** | Placeholders left in production | TODOs, stubs, mock data, empty catch, hardcoded returns |
| **Spec Deviation Debt** | Code doesn't match specification | Missing requirements, contract drift, incomplete scenarios |
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
- **Spec Compliance**: {compliance_score}% ({matched}/{total} requirements)
- **Fake Implementations Found**: {count} (blockers: {blocker_count})
- **Dead Code Items**: {count}
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

## Spec Deviation Summary

| Category | Match | Drift | Missing | Partial |
|----------|-------|-------|---------|---------|
| Functional Requirements | X | X | X | X |
| API Contracts | X | X | X | X |
| Data Model | X | X | X | X |
| Acceptance Criteria | X | X | X | X |

**Compliance Score**: {score}%

### Critical Deviations
| Requirement | Spec Says | Code Does | File:Line |
|-------------|-----------|-----------|-----------|
| ... | ... | ... | ... |

## Fake Implementations Found

| File | Line | Type | Snippet | Severity |
|------|------|------|---------|----------|
| ... | ... | TODO/Placeholder/Mock/Stub | ... | Blocker/High/Medium |

## Dead Code Found

| File | Line | Type | Evidence |
|------|------|------|----------|
| ... | ... | Orphaned/Unused export/Commented block | ... |

## Technical Debt Summary

| Category | Items | Estimated Effort | Priority |
|----------|-------|------------------|----------|
| Spec Deviation Debt | X | Y hours | Critical |
| Fake Implementation Debt | X | Y hours | Critical |
| Dead Code Debt | X | Y hours | Medium |
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

For high-priority issues, create actionable tasks with proper IDs:

```markdown
## Review Action Items

### Spec Deviations (fix first — these are functional drift)
- [ ] [DRIFT] FR-003: Password reset returns 200 instead of 204 (spec says no body)
- [ ] [MISSING] FR-007: Account locking after 5 failed attempts — not implemented
- [ ] [DRIFT] Contract: GET /api/users/:id returns 500 on not found, spec says 404

### Fake Implementations (blockers — code appears done but isn't)
- [ ] [FAKE] src/services/email.ts:23 — sendEmail() returns hardcoded `true`
- [ ] [FAKE] src/validators/payment.ts:15 — validateAmount() always returns `true`
- [ ] [FAKE] src/api/reports.ts:42 — TODO: implement actual report generation

### Dead Code (cleanup)
- [ ] [DEAD] src/utils/legacy-auth.ts — orphaned file, zero imports
- [ ] [DEAD] src/services/old-payment.ts — 45 lines commented-out code

### Code Quality
- [ ] [CRITICAL] Fix SQL injection in user_controller.py:45
- [ ] [HIGH] Add authentication to /api/admin endpoints
- [ ] [HIGH] Add tests for PaymentService
- [ ] [MEDIUM] Refactor OrderProcessor (God Object)
- [ ] [LOW] Update deprecated lodash methods
```

### 5.2: Update tasks.md (Smart Insertion)

If `tasks.md` exists in the feature directory, **DO NOT append at the end**. Instead, use smart insertion:

#### Step 5.2.1: Analyze Task Progress

```markdown
Parse tasks.md to identify:
1. All completed tasks: lines matching `- [x]` or `- [X]`
2. All pending tasks: lines matching `- [ ]`
3. The LAST completed task (by position in file)
4. The current phase/section being worked on
```

#### Step 5.2.2: Determine Insertion Point

The insertion point for review tasks depends on implementation progress:

| Scenario | Insertion Point |
|----------|-----------------|
| **No tasks completed** | After Phase 2 (Foundational) header, before first task |
| **Some tasks completed** | Immediately AFTER the last completed task `[x]` |
| **All tasks completed** | Append new "Review & Polish" section at the end |

**CRITICAL**: Review correction tasks must be addressed BEFORE continuing with pending tasks. Inserting them after the last completed task ensures proper execution order.

#### Step 5.2.3: Generate Task IDs

Find the highest existing task ID (e.g., T047) and continue numbering:

```bash
# Find highest task number
grep -oE 'T[0-9]+' tasks.md | sort -t'T' -k2 -n | tail -1
# If T047, new tasks start at T048
```

#### Step 5.2.4: Insert Review Tasks

Insert a review block after the last completed task:

```markdown
### 🔍 Review Corrections (Added {date})

> **Source**: Code review on branch `{branch_name}` vs `{base_branch}`
> **Must complete before**: Continuing with pending tasks

#### Spec Deviations
- [ ] T048 [DRIFT] [US1] Fix POST /auth/login response to match contract (returns 200, spec says 204)
- [ ] T049 [MISSING] [US2] Implement account locking after 5 failed attempts (FR-007)

#### Fake Implementations
- [ ] T050 [FAKE] [US1] Replace stub in email.ts:23 — sendEmail() returns hardcoded true
- [ ] T051 [FAKE] [US3] Implement real report generation in reports.ts:42 (currently TODO)

#### Dead Code
- [ ] T052 [DEAD] Remove orphaned file src/utils/legacy-auth.ts (zero imports)

#### Code Quality
- [ ] T053 [CRITICAL] [US1] Fix SQL injection in user_controller.py:45
- [ ] T054 [HIGH] [US1] Add input validation to createUser endpoint

---
```

### 5.3: Impact Analysis on Pending Tasks

**IMPORTANT**: Review findings may affect tasks not yet completed. Analyze and amend if necessary.

#### Step 5.3.1: Map Issues to Pending Tasks

For each review finding, check if it relates to a pending task:

| Review Finding | Related Pending Task | Impact |
|----------------|---------------------|--------|
| Missing auth check in `/api/orders` | T052: Implement order endpoint | Task must include auth |
| SQL injection pattern in models | T055: Create Report model | Must use parameterized queries |
| Missing error handling | T058: Add API error responses | Already planned, no change |

#### Step 5.3.2: Amend Affected Pending Tasks

If a pending task is impacted by a review finding:

1. **Add a note** to the task description:
   ```markdown
   - [ ] T052 [US2] Implement order endpoint in src/api/orders.py
     > ⚠️ **Review Note**: Must include authentication check (see T048)
   ```

2. **Add dependency** if the review task must complete first:
   ```markdown
   - [ ] T052 [US2] Implement order endpoint (depends on T048: auth fix)
   ```

3. **Modify the task scope** if needed:
   ```markdown
   # Before
   - [ ] T055 [US3] Create Report model in src/models/report.py

   # After (amended)
   - [ ] T055 [US3] Create Report model in src/models/report.py (use parameterized queries per review)
   ```

#### Step 5.3.3: Document Impact Summary

Add an impact summary after the review corrections block:

```markdown
### Impact on Pending Tasks

| Task | Amendment | Reason |
|------|-----------|--------|
| T052 | Added auth requirement | Review finding: missing auth check |
| T055 | Added query safety note | Review finding: SQL injection pattern |
| T060 | No change | Not affected by review findings |

**Blocking dependencies created**: T048 → T052, T049 → T055
```

### 5.4: Validation

Before saving the updated tasks.md:

1. ✅ Review tasks inserted after last completed task (not at end)
2. ✅ Task IDs are sequential and unique
3. ✅ All affected pending tasks have been amended
4. ✅ Dependencies are clearly marked
5. ✅ No duplicate findings (check if issue already has a task)

---

## Output

Present findings to user with:

1. **Summary**: Overall health score, critical issues count, spec compliance score
2. **Spec Deviations**: DRIFT/MISSING/PARTIAL requirements with file:line references
3. **Fake Implementations**: Blockers (stubs, placeholders, mock data in production code)
4. **Dead Code**: Orphaned files, unused exports, commented-out blocks
5. **Diff Scope**: Show base branch and number of files changed
6. **Top 5 Issues**: Most important findings with recommendations
7. **Quick Wins**: Easy fixes that improve quality immediately
8. **Tasks Created**: List of new review tasks with IDs (tagged: DRIFT/FAKE/DEAD/CRITICAL/HIGH/etc.)
9. **Tasks Amended**: List of pending tasks that were modified
10. **Report Location**: Path to full report file

Ask if user wants to:
- Generate detailed report file
- Apply the task updates to tasks.md
- Deep-dive into specific issues
- Run focused review on specific files
