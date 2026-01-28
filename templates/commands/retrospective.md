---
description: Perform a post-implementation retrospective analysis measuring spec drift, implementation deviations, and generating lessons learned for future features.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Analyze the **completed implementation** against the original specification (`spec.md`), plan (`plan.md`), and tasks (`tasks.md`) to measure **spec drift** - the deviation between what was specified and what was actually built. Generate actionable insights and lessons learned to improve future Spec-Driven Development cycles.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Output a structured retrospective report. All findings are for team learning and process improvement, not for immediate remediation.

**Post-Implementation Only**: This command should run AFTER implementation is complete (or at a significant milestone). If tasks.md shows many incomplete tasks, warn the user and offer to proceed with partial analysis or abort.

## Execution Steps

### 1. Initialize Retrospective Context

Run `{SCRIPT}` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

If any required file is missing, abort with instructions to ensure the feature was developed using the full Spec-Driven Development workflow.

### 2. Validate Implementation Completeness

**Before proceeding, verify implementation readiness:**

1. Parse tasks.md and calculate completion percentage:
   - Count total tasks: Lines matching `- [ ]` or `- [X]` or `- [x]`
   - Count completed tasks: Lines matching `- [X]` or `- [x]`
   - Calculate: `completion_rate = completed / total * 100`

2. **Completeness Gate:**
   - **≥80% complete**: Proceed with full retrospective
   - **50-79% complete**: Warn user, proceed with partial analysis, note incomplete areas
   - **<50% complete**: Ask user to confirm proceeding (analysis may be premature)

### 3. Load Artifacts (Progressive Disclosure)

Load relevant sections from each artifact:

**From spec.md:**

- Feature Overview/Context
- Functional Requirements (FR-XXX)
- Non-Functional Requirements (NFR-XXX)
- User Stories with priorities
- Success Criteria (SC-XXX)
- Assumptions
- Edge Cases

**From plan.md:**

- Architecture/stack choices
- Data Model specifications
- Phase breakdown
- Technical constraints
- Dependencies

**From tasks.md:**

- All tasks with completion status
- Phase grouping
- Referenced file paths
- Any notes or blockers

**From constitution (if exists):**

- Load `/memory/constitution.md` for principle validation

### 4. Discover Implementation Reality

**Scan the actual codebase** to understand what was built:

1. **File Discovery**: Identify all files created/modified as part of this feature:
   - Extract file paths from completed tasks in tasks.md
   - Cross-reference with git history if available: `git log --name-only --oneline HEAD~50..HEAD`
   - List actual project structure in relevant directories

2. **Implementation Inventory**:
   - Entities/Models actually created (vs data-model.md)
   - Endpoints/APIs actually implemented (vs contracts/)
   - Services/Components actually built
   - Tests actually written
   - Configuration changes made

3. **Technology Audit**:
   - Libraries/dependencies actually installed
   - Frameworks actually used
   - Third-party integrations actually connected

### 5. Spec Drift Analysis

Compare specification artifacts against implementation reality across these dimensions:

#### A. Requirement Coverage Analysis

For each Functional Requirement (FR-XXX) and Non-Functional Requirement (NFR-XXX):

| Status | Meaning |
|--------|---------|
| ✅ IMPLEMENTED | Requirement fully satisfied in code |
| ⚠️ PARTIAL | Requirement partially implemented, missing aspects |
| ❌ NOT IMPLEMENTED | Requirement not addressed in code |
| 🔄 MODIFIED | Implementation differs from specification |
| ➕ UNSPECIFIED | Implemented but not in original spec (scope creep or evolution) |

Track:

- Which requirements (FR and NFR) were implemented as specified
- Which requirements were modified during implementation
- Which requirements were dropped or deferred
- Which capabilities were added without specification

#### B. Success Criteria Validation

For each Success Criterion (SC-XXX):

- Is the criterion measurable in the current implementation?
- What is the actual measured value (if available)?
- Does it meet the specified target?

#### C. Architecture Drift

Compare plan.md architecture against actual implementation:

- Data model changes (entities added/removed/modified)
- API contract changes (endpoints, request/response shapes)
- Technology stack changes (libraries, frameworks)
- Structural changes (file organization, module boundaries)

#### D. Task Execution Fidelity

Analyze how closely implementation followed the task plan:

- Tasks completed as specified
- Tasks modified during execution
- Tasks added during implementation
- Tasks that proved unnecessary
- Parallel execution opportunities used/missed

#### E. Timeline & Scope Analysis (if data available)

- Phases that took longer than expected
- Scope changes during implementation
- Blockers encountered
- Dependencies that caused delays

### 6. Drift Severity Classification

Classify each deviation by impact:

| Severity | Criteria | Action |
|----------|----------|--------|
| **CRITICAL** | Changes core functionality, breaks user stories, violates constitution | Must document for stakeholders |
| **SIGNIFICANT** | Notable deviation from spec, may affect user experience or performance | Document and analyze cause |
| **MINOR** | Small implementation variations, cosmetic differences | Note for completeness |
| **POSITIVE** | Improvements over specification (better UX, performance, security) | Capture as best practice |

### 7. Root Cause Analysis

For each significant deviation, analyze:

1. **Discovery Point**: When was the deviation identified?
   - During planning (spec was unclear)
   - During implementation (technical constraint)
   - During testing (requirement was wrong)
   - During review (stakeholder feedback)

2. **Cause Category**:
   - **Spec Gap**: Original specification was incomplete or ambiguous
   - **Tech Constraint**: Technical limitation prevented specified approach
   - **Scope Evolution**: Requirements changed during development
   - **Misunderstanding**: Requirement was misinterpreted
   - **Improvement**: Deviation represents a better solution
   - **Process Skip**: Spec/plan step was bypassed

3. **Prevention Strategy**: How could this be avoided in future features?

### 8. Generate Retrospective Report

Output a comprehensive Markdown report with the following structure:

---

## 📊 Feature Retrospective Report

**Feature**: [Feature Name from spec.md]
**Branch**: [Branch name]
**Analysis Date**: [Current date]
**Implementation Completion**: [X]%

---

### Executive Summary

[2-3 sentence summary of overall spec adherence and key findings]

**Spec Adherence Score**: [Calculate as percentage: implemented_as_specified / total_requirements * 100]

| Metric | Value |
|--------|-------|
| Total Requirements | X |
| Implemented as Specified | X |
| Modified During Implementation | X |
| Not Implemented | X |
| Unspecified Additions | X |
| Spec Adherence Score | X% |

---

### Requirement Coverage Matrix

| Req ID | Description | Status | Deviation Notes |
|--------|-------------|--------|-----------------|
| FR-001 | [Brief desc] | ✅/⚠️/❌/🔄 | [If applicable] |
| NFR-001 | [Brief desc] | ✅/⚠️/❌/🔄 | [If applicable] |
| ... | ... | ... | ... |

---

### Success Criteria Assessment

| Criterion | Target | Actual | Met? | Notes |
|-----------|--------|--------|------|-------|
| SC-001 | [Target value] | [Measured/Estimated] | ✅/❌/⚠️ | [Notes] |
| ... | ... | ... | ... | ... |

---

### Architecture Drift Summary

#### Data Model Changes

| Entity | Specified | Actual | Change Type |
|--------|-----------|--------|-------------|
| [Entity] | [Spec version] | [Impl version] | Added/Modified/Removed |

#### Technology Stack Changes

| Component | Planned | Actual | Reason |
|-----------|---------|--------|--------|
| [Database/Framework/Library] | [Planned] | [Used] | [Why changed] |

---

### Significant Deviations

#### Deviation 1: [Title]

- **Severity**: [CRITICAL/SIGNIFICANT/MINOR/POSITIVE]
- **Requirement(s) Affected**: [FR-XXX, SC-XXX]
- **What was specified**: [Original spec]
- **What was implemented**: [Actual implementation]
- **Discovery Point**: [When identified]
- **Root Cause**: [Cause category]
- **Impact**: [Effect on feature/user]
- **Lesson Learned**: [Preventive insight]

[Repeat for each significant deviation]

---

### Unspecified Implementations

| Addition | Description | Justification | Should Have Been Specified? |
|----------|-------------|---------------|---------------------------|
| [What was added] | [Brief desc] | [Why added] | Yes/No - [Reason] |

---

### Task Execution Analysis

| Phase | Planned Tasks | Completed | Added | Dropped | Notes |
|-------|---------------|-----------|-------|---------|-------|
| Setup | X | X | X | X | [Notes] |
| [Phase N] | X | X | X | X | [Notes] |
| ... | ... | ... | ... | ... | ... |

---

### Lessons Learned

#### Specification Improvements

- [ ] [Lesson 1: What to improve in future specs]
- [ ] [Lesson 2: ...]

#### Planning Improvements

- [ ] [Lesson 1: What to improve in future plans]
- [ ] [Lesson 2: ...]

#### Process Improvements

- [ ] [Lesson 1: What to improve in the SDD workflow]
- [ ] [Lesson 2: ...]

#### Technical Insights

- [ ] [Lesson 1: Technical knowledge gained]
- [ ] [Lesson 2: ...]

---

### Recommendations

#### For This Feature

1. [Recommendation for addressing any gaps]
2. [Recommendation for documentation updates]

#### For Future Features

1. [Process improvement recommendation]
2. [Template/checklist improvement recommendation]

#### Constitution Updates (if applicable)

- [ ] [Principle to add/modify based on learnings]

---

### Appendix: File-Level Traceability

| File | Created/Modified | Related Requirements | Notes |
|------|------------------|---------------------|-------|
| [path/to/file.ext] | Created | FR-001, FR-002 | [Notes] |
| ... | ... | ... | ... |

---

## 9. Save Retrospective (Optional)

Ask user: "Would you like me to save this retrospective report to `FEATURE_DIR/retrospective.md`?"

If yes, write the report file.

## 10. Offer Follow-up Actions

Based on findings, suggest next steps:

- If significant gaps exist: "Consider running `/speckit.specify` to update the spec with actual implementation"
- If constitution violations found: "Review constitution principles that may need updating"
- If process issues identified: "Consider updating team's SDD workflow documentation"
- If positive deviations found: "Document these improvements as best practices"

## Analysis Guidelines

### What to Count as Spec Drift

**Count as drift:**

- Features implemented differently than specified
- Requirements dropped without documentation
- Unplanned features added (scope creep)
- Technical approach changed from plan
- Data model evolved from specification
- API contracts modified

**Do NOT count as drift:**

- Implementation details not specified in functional requirements
- Technology-specific optimizations within spec boundaries
- Bug fixes discovered during development
- Refactoring that maintains functionality
- Test coverage improvements

### Objectivity Principles

- Report facts, not judgments about team performance
- Focus on process improvement, not blame
- Treat positive deviations as valuable learning
- Acknowledge that some drift is normal and expected
- Prioritize actionable insights over exhaustive documentation

### Token Efficiency

- Limit deviation details to top 10 most significant
- Aggregate minor deviations in summary counts
- Use tables for structured data
- Keep recommendations actionable and specific
- Cap total report at ~2000 lines
