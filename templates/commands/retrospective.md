---
description: Perform a post-implementation retrospective analysis measuring spec drift, implementation deviations, and generating lessons learned for future features.
handoffs: 
  - label: Update Constitution
    agent: speckit.constitution
    prompt: Update constitution based on retrospective learnings
    send: true
  - label: Create New Feature
    agent: speckit.specify
    prompt: Create a new feature incorporating learnings from retrospective
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create checklist based on retrospective findings
    send: true
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Goal

Analyze completed implementation against spec.md, plan.md, and tasks.md to measure **spec drift**. Generate actionable insights for future SDD cycles.

## Constraints

- **Output**: Generates and saves `retrospective.md` report to FEATURE_DIR
- **Post-Implementation**: Run after implementation complete; warn if <80% tasks done, abort if <50%

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root. Parse JSON for FEATURE_DIR. Derive paths: SPEC, PLAN, TASKS = FEATURE_DIR/{spec,plan,tasks}.md. Abort if missing.

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Validate Completeness

```bash
total_tasks=$(grep -c '^\- \[[ Xx]\]' "$TASKS")
completed_tasks=$(grep -c '^\- \[[Xx]\]' "$TASKS")
completion_rate=$((completed_tasks * 100 / total_tasks))
```

- **≥80%**: Full retrospective | **50-79%**: Warn, partial analysis | **<50%**: Confirm before proceeding

### 3. Load Artifacts

- **spec.md**: FR-XXX, NFR-XXX, SC-XXX, User Stories, Assumptions, Edge Cases
- **plan.md**: Architecture, data model, phases, constraints, dependencies
- **tasks.md**: All tasks with status, file paths, blockers
- **constitution**: `/memory/constitution.md` (if exists)

### 4. Discover Implementation

- Extract file paths from completed tasks + `git log --name-only HEAD~50..HEAD`
- Inventory: Models, APIs, Services, Tests, Config changes
- Audit: Libraries, frameworks, integrations actually used

### 5. Spec Drift Analysis

#### A. Requirement Coverage

| Status | Meaning | Example |
|--------|---------|--------|
| ✅ IMPLEMENTED | Fully satisfied | FR-001: User login works as specified |
| ⚠️ PARTIAL | Partially done | FR-002: Search works but no filters |
| ❌ NOT IMPLEMENTED | Not addressed | NFR-003: No rate limiting added |
| 🔄 MODIFIED | Differs from spec | FR-004: REST instead of GraphQL |
| ➕ UNSPECIFIED | Added without spec | Admin dashboard not in requirements |

#### B. Success Criteria - Validate each SC-XXX against measured values
#### C. Architecture Drift - Data model, API, stack, structure changes vs plan.md
#### D. Task Fidelity - Tasks completed/modified/added/dropped
#### E. Timeline (if available) - Phase delays, scope changes, blockers

### 6. Severity Classification

| Severity | Criteria | Example |
|----------|----------|--------|
| **CRITICAL** | Core functionality, constitution violations | Missing payment validation |
| **SIGNIFICANT** | Notable deviation affecting UX/performance | Changed auth method |
| **MINOR** | Small variations, cosmetic | Button color differs |
| **POSITIVE** | Improvements over spec | Added response caching |

### 7. Innovation Opportunities

For positive deviations: What improved, why better, reusability, constitution candidate?

### 8. Root Cause Analysis

- **Discovery Point**: Planning/Implementation/Testing/Review
- **Cause**: Spec Gap, Tech Constraint, Scope Evolution, Misunderstanding, Improvement, Process Skip
- **Prevention**: How to avoid in future

### 9. Constitution Compliance

Check each article against implementation. All violations = CRITICAL.

| Article | Title | Status | Notes |
|---------|-------|--------|-------|

### 10. Generate Report

```markdown
## 📊 Feature Retrospective Report
**Feature**: [Name] | **Branch**: [branch] | **Date**: [date] | **Completion**: [X]%

### Executive Summary
[2-3 sentences] | **Spec Adherence**: [X]%

| Metric | Value |
|--------|-------|
| Total/Implemented/Modified/Not Implemented/Unspecified | X |

### Requirement Coverage Matrix
| Req ID | Description | Status | Notes |

### Success Criteria Assessment
| Criterion | Target | Actual | Met? |

### Architecture Drift
| Entity/Component | Specified | Actual | Change Type/Reason |

### Significant Deviations
For each: Severity, Requirements Affected, Specified vs Implemented, Discovery, Root Cause, Impact, Lesson

**Example:**
> #### Auth Method Changed
> - **Severity**: SIGNIFICANT | **Affected**: FR-003, SC-002
> - **Specified**: Email/password with bcrypt | **Implemented**: OAuth2 SSO
> - **Discovery**: Phase 1 | **Cause**: Tech Constraint (email service unavailable)
> - **Impact**: Better UX, added third-party dependency
> - **Lesson**: Specify auth dependencies in planning phase

### Innovations & Best Practices
| Innovation | Description | Benefit | Reusability | Constitution Candidate? |

**Example:**
| Response caching | Redis cache for frequent queries | 85% less DB load, 60% faster | All read-heavy endpoints | Yes - "Cache-First" principle |

### Constitution Compliance
| Article | Title | Status | Notes |
**Violations**: [None / List with justifications]

### Unspecified Implementations
| Addition | Description | Justification | Should Have Been Specified? |

### Task Execution Analysis
| Phase | Planned | Completed | Added | Dropped |

### Lessons Learned
- Specification/Planning/Process/Technical improvements

### Recommendations
- For this feature / For future features / Constitution updates

### Appendix: File Traceability
| File | Created/Modified | Requirements |
```

### 11. Save Report

1. Write to `FEATURE_DIR/retrospective.md` with YAML frontmatter (feature, branch, date, rates, counts)
2. Commit: `Add retrospective analysis - Spec adherence: X% | Completion: X%`
3. Confirm: `✅ Retrospective saved | 📊 Adherence: X% | ⚠️ Critical: X`

### 12. Follow-up Actions

**By Priority:**
1. **CRITICAL**: Constitution violations, breaking changes, security issues
2. **HIGH**: Significant drift, process improvements, template updates
3. **MEDIUM**: Best practices, constitution candidates
4. **LOW**: Minor optimizations

**Commands:**
- `/speckit.constitution` for violations
- `/speckit.specify` for spec updates
- `/speckit.checklist` for new checklists

**Example output:**
```
🚨 CRITICAL: 2 actions required
   1. /speckit.constitution Review Article II violation in auth module
   2. Update spec.md to document OAuth2 implementation
⚠️  HIGH: 2 improvements
   1. /speckit.checklist Create security checklist with OAuth2 validation
   2. Document caching pattern in /memory/patterns/
✅ MEDIUM: 1 best practice
   1. /speckit.constitution Consider "Cache-First" principle
```

## Guidelines

### Count as Drift
Features differing from spec, dropped requirements, scope creep, tech approach changes

### NOT Drift
Implementation details, optimizations within boundaries, bug fixes, refactoring, test improvements

### Principles
- Facts over judgments, process over blame, positive deviations = learning
- Progressive disclosure, max 50 detailed deviations, compact tables
- Executive summary <500 words, report <2000 lines
