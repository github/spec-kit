---
description: Validate design-task alignment and cross-artifact consistency before implementation begins.
---

## User Input

```text
$ARGUMENTS
```

You are performing a **pre-implementation validation** to catch issues before they become expensive to fix. This is a conversation about readiness, not just a report dump.

## Philosophy

The goal isn't to generate a lengthy report—it's to answer one question:
**"Are we ready to start implementing?"**

If yes, confirm and move on. If no, explain what needs attention and help fix it.

## Prerequisites

Verify these artifacts exist:

1. **Constitution** at `.minispec.minispec/memory/constitution.md`
2. **Design** at `.minispec/specs/[feature-name]/design.md`
3. **Tasks** at `.minispec/specs/[feature-name]/tasks.md`
4. **Decisions** in `.minispec/knowledge/decisions/`

If `$ARGUMENTS` specifies a feature, use that. Otherwise, detect the current feature or ask.

If any required artifact is missing:
> "I can't run a full analysis yet. Missing:
> - [x] Constitution ✓
> - [ ] Design - Run `/minispec.design` first
> - [ ] Tasks - Run `/minispec.tasks` first
>
> Want me to help with the missing piece?"

## Analysis Areas

### 1. Design ↔ Tasks Alignment

Check that every design element has corresponding tasks:

**Components:**
- Each component in design.md should have implementation tasks
- Flag components with no associated tasks

**Decisions:**
- Each decision in `.minispec/knowledge/decisions/` should be reflected in tasks
- Flag decisions that imply work but have no tasks

**Data Model:**
- Each entity should have model/migration tasks
- Flag entities missing from task list

**API/Interface:**
- Each endpoint/function should have implementation tasks
- Flag APIs without coverage

### 2. Task Completeness

Check that tasks are well-formed:

**Required elements:**
- Estimate (lines)
- Files affected
- Description
- Acceptance criteria

**Dependency validity:**
- No circular dependencies
- Dependencies reference existing tasks
- Order makes sense (can't integrate before building)

**Size appropriateness:**
- Compare estimates against constitution chunk size preference
- Flag tasks significantly over/under target size

### 3. Constitution Compliance

Check alignment with project principles:

**Core principles:**
- Do design decisions respect stated principles?
- Are there tasks that would violate principles?

**MiniSpec preferences:**
- Are tasks sized appropriately for review chunk preference?
- Is documentation approach consistent with doc review policy?

### 4. Knowledge Base Consistency

Check documentation coherence:

**Decisions:**
- All decisions have required frontmatter
- No contradictory decisions
- Referenced code paths exist or will be created by tasks

**Cross-references:**
- Design references correct decision IDs
- Tasks reference correct design components

### 5. Gap Detection

Look for missing pieces:

**Coverage gaps:**
- Requirements without tasks
- Tasks without clear requirements

**Edge cases:**
- Error handling mentioned but no tasks
- Edge cases in design but not covered

**Non-functional:**
- Performance requirements without tasks
- Security requirements without tasks

## Execution Flow

### Phase 1: Load and Parse

1. Read all artifacts quietly
2. Build internal model of:
   - Design components and requirements
   - Task list with dependencies
   - Decision records
   - Constitution rules and preferences

### Phase 2: Run Checks

Perform each analysis area. Track findings by severity:

- **CRITICAL**: Blocks implementation (missing core coverage, contradictions)
- **WARNING**: Should fix but can proceed (sizing issues, minor gaps)
- **INFO**: Suggestions for improvement (style, clarity)

### Phase 3: Report Findings

**If no issues found:**
> "✅ Analysis complete. Everything looks good!
>
> **Summary:**
> - [N] design components → [N] tasks covering them
> - [N] decisions documented
> - Tasks sized appropriately for your [size] preference
> - No constitution violations
>
> Ready to implement. Run `/minispec.next` when you're ready."

**If issues found:**
> "Analysis found [N] items to review before implementing:
>
> **Critical (must fix):**
> 1. [Issue description]
>    - Location: [file:section]
>    - Problem: [what's wrong]
>    - Suggestion: [how to fix]
>
> **Warnings (should fix):**
> 1. [Issue description]
>    ...
>
> **Info (optional):**
> 1. [Suggestion]
>    ...
>
> Want me to help resolve the critical issues?"

### Phase 4: Interactive Resolution

If engineer wants help fixing issues:

1. Start with critical issues
2. For each issue:
   - Explain the problem in context
   - Propose a specific fix
   - Ask for confirmation
   - Make the change (or guide them to make it)
3. Re-run affected checks after fixes
4. Confirm when ready

## Report Format (When Requested)

If the engineer wants a formal report, generate:

```markdown
# Pre-Implementation Analysis Report

**Feature:** [feature-name]
**Date:** [YYYY-MM-DD]
**Status:** [Ready | Blocked | Needs Review]

## Summary

| Metric | Value |
|--------|-------|
| Design Components | [N] |
| Tasks | [N] |
| Coverage | [N]% |
| Critical Issues | [N] |
| Warnings | [N] |

## Coverage Matrix

| Design Component | Tasks | Status |
|------------------|-------|--------|
| [Component 1] | T1, T3 | ✅ Covered |
| [Component 2] | T2 | ✅ Covered |
| [Component 3] | - | ❌ No tasks |

## Issues

### Critical

| ID | Location | Issue | Recommendation |
|----|----------|-------|----------------|
| C1 | design.md | [Description] | [Fix] |

### Warnings

| ID | Location | Issue | Recommendation |
|----|----------|-------|----------------|
| W1 | tasks.md | [Description] | [Fix] |

## Decision Alignment

| Decision | Tasks Reflecting It | Status |
|----------|---------------------|--------|
| 001-auth | T4, T5, T6 | ✅ Aligned |
| 002-db | T2 | ✅ Aligned |

## Recommendations

1. [Specific action]
2. [Specific action]

## Next Steps

- [ ] Resolve critical issues
- [ ] Review warnings
- [ ] Run `/minispec.next` to begin implementation
```

## Important Guidelines

- **Be concise**: Don't generate a report if a simple "looks good" suffices
- **Be actionable**: Every issue should have a clear fix
- **Be conversational**: This is a checkpoint, not an audit
- **Help fix issues**: Don't just report—offer to resolve
- **Respect time**: If only minor issues, let them proceed with a note

## Constitution Authority

The constitution is non-negotiable. If something violates a constitution principle:
- It's automatically CRITICAL
- The fix is to change the design/tasks, not the constitution
- If the principle itself needs to change, that's a separate conversation

## Output Artifacts

This command is primarily **read-only**, but may update:

1. `.minispec/specs/[feature-name]/design.md` - If fixes are applied
2. `.minispec/specs/[feature-name]/tasks.md` - If fixes are applied
3. `.minispec/knowledge/decisions/*.md` - If fixes are applied

Only with explicit engineer approval.
