# Sprint [NUMBER]: [NAME]

**Duration**: [START_DATE] - [END_DATE] ([DURATION])  
**Status**: Active  
**Created**: [DATE]  
**Input**: User description: "$ARGUMENTS"

## Sprint Goal

[High-level goal for this sprint - what are we trying to achieve? This should be a clear, measurable objective that the team can rally around.]

## Success Criteria

<!--
Define 3-5 measurable outcomes that indicate sprint success.
These should be specific, testable, and aligned with the sprint goal.
-->

- [ ] [Measurable outcome 1 - e.g., "Users can authenticate via OIDC"]
- [ ] [Measurable outcome 2 - e.g., "API response time < 200ms"]
- [ ] [Measurable outcome 3 - e.g., "Zero critical security vulnerabilities"]

## Capacity & Velocity

- **Team Size**: [NUMBER] developers
- **Sprint Duration**: [NUMBER] working days
- **Estimated Capacity**: [NUMBER] story points / features (if tracked)
- **Previous Sprint Velocity**: [NUMBER] (if available)

## Features in Sprint

<!--
List all features planned for this sprint.
Features should be prioritized (P1 = must have, P2 = should have, P3 = nice to have)
-->

| Feature ID | Feature Name | Priority | Status | Owner | Notes |
|------------|--------------|----------|--------|-------|-------|
| | | | | | |

**Status Legend**: Not Started | In Progress | Blocked | In Review | Complete

## Dependencies

<!--
Document dependencies between features and external dependencies.
This helps identify potential blockers early.
-->

### Internal Dependencies
- [Feature 003-api] depends on [Feature 001-auth] - API needs auth middleware
- [Feature X] depends on [Feature Y] - [Reason]

### External Dependencies
- AWS Cognito setup - Required for auth implementation
- Design system approval - Needed before UI components
- [External dependency] - [Description and status]

## Risks & Mitigation

<!--
Identify potential risks and how to mitigate them.
Update this section as new risks emerge during the sprint.
-->

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| OIDC integration complexity | Medium | High | Spike task in first 2 days, fallback to simpler auth |
| Design system delays | Low | Medium | Use placeholder components, refactor later |
| [Risk description] | [H/M/L] | [H/M/L] | [Strategy] |

## Sprint Backlog

<!--
Detailed breakdown of work items for the sprint.
This is more granular than the features table above.
-->

### Week 1
- [ ] Setup OIDC provider configuration
- [ ] Implement authentication middleware
- [ ] Create login/logout UI components
- [ ] Write authentication tests

### Week 2
- [ ] Integrate auth with API layer
- [ ] Add role-based access control
- [ ] Complete security review
- [ ] Deploy to staging

## Daily Progress

<!--
Track daily progress, blockers, and next steps.
This provides a historical record of the sprint.
-->

### [DATE] - Day 1
**Completed**:
- [What was finished today]

**Blocked**:
- [Any blockers encountered]

**Next**:
- [What's planned for tomorrow]

**Notes**:
- [Any important observations or decisions]

---

### [DATE] - Day 2
**Completed**:
- [What was finished today]

**Blocked**:
- [Any blockers encountered]

**Next**:
- [What's planned for tomorrow]

---

[Continue for each day of the sprint]

## Decisions Made During Sprint

<!--
Document key decisions made during the sprint.
This will be extracted during sprint archival.
Format: Decision title, context, options, choice, rationale
-->

### Decision 1: [Title]
**Date**: [DATE]  
**Context**: [Why this decision was needed]  
**Options Considered**:
1. [Option A] - [Pros/Cons]
2. [Option B] - [Pros/Cons]

**Decision**: [What was chosen]  
**Rationale**: [Why this was chosen]  
**Impact**: [How this affects the project]  
**Related Features**: [Feature IDs affected]

---

### Decision 2: [Title]
[Same structure as above]

---

## Pivots & Course Corrections

<!--
Document any significant changes from the original plan.
This helps understand why the sprint evolved.
-->

### Pivot 1: [Title]
**Date**: [DATE]  
**Original Plan**: [What was originally planned]  
**Change**: [What actually happened]  
**Reason**: [Why the pivot occurred - new information, blocker, priority shift]  
**Outcome**: [Result of the pivot]  
**Lessons**: [What we learned]

---

## Sprint Metrics

<!--
Track quantitative metrics throughout the sprint.
Update these daily or as features complete.
-->

- **Features Planned**: [NUMBER]
- **Features Completed**: [NUMBER]
- **Features In Progress**: [NUMBER]
- **Features Blocked**: [NUMBER]
- **Features Carried Over**: [NUMBER]
- **Velocity**: [NUMBER] (if tracked)
- **Bugs Found**: [NUMBER]
- **Bugs Fixed**: [NUMBER]

## Notes & Observations

<!--
Capture any additional context, learnings, or observations
that don't fit in other sections.
-->

- [Observation 1]
- [Observation 2]

## Sprint Review Preparation

<!--
Prepare for sprint review/demo.
What will we show? Who needs to attend?
-->

**Demo Date**: [DATE]  
**Attendees**: [List of stakeholders]  
**Demo Script**:
1. [Feature 1] - [What to demonstrate]
2. [Feature 2] - [What to demonstrate]

**Key Messages**:
- [Message 1 for stakeholders]
- [Message 2 for stakeholders]
