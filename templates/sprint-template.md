# Sprint [NUMBER]: [NAME]

**Duration**: [START_DATE] - [END_DATE] ([DURATION])  
**Status**: Active  
**Created**: [DATE]  
**Input**: User description: "$ARGUMENTS"

## Sprint Goal

<!--
Defined during sprint creation via /speckit.sprint start
Prompt: "What is the high-level goal for this sprint? What are you trying to achieve?"

Example: "Enable users to authenticate and access personalized dashboards with role-based permissions"
-->

[To be defined - use /speckit.sprint start to set sprint goal]

## Success Criteria

<!--
Defined during sprint creation via /speckit.sprint start
Prompt: "What are 3-5 measurable outcomes that indicate sprint success?"

Examples:
- [ ] Users can authenticate via OIDC with <2s login time
- [ ] API response time < 200ms for all endpoints
- [ ] Zero critical security vulnerabilities in security scan
- [ ] 90% code coverage on new features
- [ ] All acceptance tests passing in staging environment
-->

- [ ] [To be defined - use /speckit.sprint start to set success criteria]

## Capacity & Velocity

<!--
Example:
- **Team Size**: 3 developers
- **Sprint Duration**: 10 working days
- **Estimated Capacity**: 8 features
- **Previous Sprint Velocity**: 7 features (if available)
-->

- **Team Size**: [NUMBER] developers
- **Sprint Duration**: [NUMBER] working days
- **Estimated Capacity**: [NUMBER] story points / features (if tracked)
- **Previous Sprint Velocity**: [NUMBER] (if available)

## Features in Sprint

<!--
List all features planned for this sprint.
Features should be prioritized (P1 = must have, P2 = should have, P3 = nice to have)

Example:
| 001-user-auth | User Authentication | P1 | In Progress | @alice | OIDC integration |
| 002-dashboard-ui | Dashboard UI | P2 | Not Started | @bob | Depends on 001 |
-->

| Feature ID | Feature Name | Priority | Status | Owner | Notes |
|------------|--------------|----------|--------|-------|-------|

**Status Legend**: Not Started | In Progress | Blocked | In Review | Complete

## Dependencies

<!--
Document dependencies between features and external dependencies.
This helps identify potential blockers early.

Examples:
### Internal Dependencies
- [Feature 003-api] depends on [Feature 001-auth] - API needs auth middleware
- [Feature 004-ui] depends on [Feature 002-design] - UI needs design system

### External Dependencies
- AWS Cognito setup - Required for auth implementation (ETA: Week 1)
- Design system approval - Needed before UI components (Blocked)
-->

### Internal Dependencies
[Document internal dependencies here]

### External Dependencies
[Document external dependencies here]

## Risks & Mitigation

<!--
Identify potential risks and how to mitigate them.
Update this section as new risks emerge during the sprint.

Example:
| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| OIDC integration complexity | Medium | High | Spike task in first 2 days, fallback to simpler auth |
| Design system delays | Low | Medium | Use placeholder components, refactor later |
| Third-party API downtime | Low | High | Implement circuit breaker, cache responses |
-->

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|

## Sprint Backlog

<!--
Detailed breakdown of work items for the sprint.
This is more granular than the features table above.
Weeks are auto-generated based on sprint duration.

Example:
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
-->

[SPRINT_BACKLOG_WEEKS]

## Daily Progress

<!--
Track daily progress, blockers, and next steps.
This provides a historical record of the sprint.

Example:
### 2025-01-15 - Day 1
**Completed**:
- Setup OIDC provider configuration
- Created authentication middleware skeleton

**Blocked**:
- Waiting on AWS Cognito credentials

**Next**:
- Complete authentication middleware
- Start login UI components

**Notes**:
- Team decided to use JWT tokens instead of sessions
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

[Continue for each day of the sprint]

## Decisions Made During Sprint

<!--
Document key decisions made during the sprint.
This will be extracted during sprint archival.
Format: Decision title, context, options, choice, rationale

Example:
### Decision 1: Use JWT for Authentication
**Date**: 2025-01-15
**Context**: Need to choose authentication token format
**Options Considered**:
1. Session cookies - Simple but requires server state
2. JWT tokens - Stateless but larger payload

**Decision**: JWT tokens
**Rationale**: Better scalability, works with mobile apps
**Impact**: Need to implement token refresh logic
**Related Features**: 001-auth, 003-api
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

[Continue for additional decisions]

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
