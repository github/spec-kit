# Issue Specification: [ISSUE NAME]

**Issue Number**: `[001-dashboard-loading]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: Issue description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse issue description from Input
   → If empty: ERROR "No issue description provided"
2. Extract key concepts from description
   → Identify: problem, impact, affected systems, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill Problem Statement & Impact section
   → If no clear problem: ERROR "Cannot determine issue scope"
5. Generate Issue Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Affected Systems (if applicable)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Issue has uncertainties"
   → If solution details found: ERROR "Remove solution details"
8. Return: SUCCESS (issue ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT is broken and WHY it matters
- ❌ Avoid HOW to fix (no implementation details, code changes, tech stack)
- 👥 Written for stakeholders and developers to understand the problem

### Section Requirements
- **Mandatory sections**: Must be completed for every issue
- **Optional sections**: Include only when relevant to the issue
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this issue from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login broken" without error details), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - Error conditions and symptoms
   - User impact and severity
   - Affected user types or systems
   - Reproduction steps
   - Expected vs actual behavior
   - Performance impact
   - Security implications

---

## Problem Statement & Impact *(mandatory)*

### Issue Summary
[Describe the problem in plain language - what is broken or not working as expected]

### Current Behavior
[Describe what is currently happening - the actual behavior]

### Expected Behavior
[Describe what should be happening - the desired behavior]

### Impact Assessment
- **User Impact**: [How does this affect users?]
- **Business Impact**: [How does this affect business operations?]
- **System Impact**: [How does this affect system performance/reliability?]

### Reproduction Steps
1. [Step 1 to reproduce the issue]
2. [Step 2 to reproduce the issue]
3. [Step 3 to reproduce the issue]
4. **Result**: [What actually happens]
5. **Expected**: [What should happen]

## Issue Requirements *(mandatory)*

### Functional Requirements
- **IR-001**: System MUST [specific behavior that should work, e.g., "allow users to login successfully"]
- **IR-002**: System MUST [specific behavior, e.g., "display error messages clearly"]  
- **IR-003**: System MUST [specific behavior, e.g., "handle invalid input gracefully"]
- **IR-004**: System MUST [specific behavior, e.g., "maintain data consistency"]
- **IR-005**: System MUST [specific behavior, e.g., "log errors appropriately"]

*Example of marking unclear requirements:*
- **IR-006**: System MUST handle [NEEDS CLARIFICATION: specific error condition not specified]
- **IR-007**: System MUST support [NEEDS CLARIFICATION: user type or scenario not specified]

### Affected Systems *(include if issue affects multiple systems)*
- **[System 1]**: [What system is affected, how it's impacted]
- **[System 2]**: [What system is affected, relationships to other systems]

### Constraints & Dependencies
- **Technical Constraints**: [Any technical limitations that affect the solution]
- **Business Constraints**: [Any business rules or policies that must be considered]
- **Dependencies**: [Other issues, features, or systems that this issue depends on]

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No solution details (implementation, code changes, tech stack)
- [ ] Focused on problem identification and impact
- [ ] Written for stakeholders and developers
- [ ] All mandatory sections completed

### Issue Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Problem scope is clearly defined
- [ ] Impact is measurable and specific
- [ ] Reproduction steps are clear and complete

---

## Execution Status
*Updated by main() during processing*

- [ ] Issue description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] Problem statement defined
- [ ] Requirements generated
- [ ] Affected systems identified
- [ ] Review checklist passed

---
