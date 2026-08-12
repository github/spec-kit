# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Status**: Draft

**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- What happens when [boundary condition]?
- How does system handle [error scenario]?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.

  ID NUMBERING — SPARSE AND PERMANENT: FR identifiers are references, not labels. Plans,
  tasks, checklists, commits, and review comments cite them, so a renumber silently
  invalidates every citation. Allocate them with room to grow:
    - Group requirements by category. Each category starts at the next multiple of 1000
      (FR-1000, FR-2000, FR-3000...) and requirements step by 10 within it.
    - Insert using the gap: a requirement belonging between FR-1010 and FR-1020 becomes
      FR-1015. Nothing after it shifts.
    - Append at the next free multiple of 10; open a new category at the next unused
      multiple of 1000.
    - Removing a requirement leaves a permanent hole. Delete the line and stop — do not
      close the gap, do not renumber, and never re-issue a retired number. Gaps are the
      expected steady state, not damage to repair.
-->

### Functional Requirements

**[Category 1, e.g. Accounts]**

- **FR-1000**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-1010**: System MUST [specific capability, e.g., "validate email addresses"]
- **FR-1020**: Users MUST be able to [key interaction, e.g., "reset their password"]

**[Category 2, e.g. Data and audit]**

- **FR-2000**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-2010**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*

- **FR-2020**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-2030**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.

  ID NUMBERING: SC identifiers follow the same sparse, permanent scheme as FR identifiers
  above — step by 10 (SC-1000, SC-1010, ...), insert into the gap (SC-1015), append at the
  next free multiple of 10, and leave a permanent hole when a criterion is removed. Never
  renumber, never re-issue a retired number. If the criteria are grouped by category, each
  category starts at the next multiple of 1000.
-->

### Measurable Outcomes

- **SC-1000**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-1010**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-1020**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-1030**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- [Assumption about target users, e.g., "Users have stable internet connectivity"]
- [Assumption about scope boundaries, e.g., "Mobile support is out of scope for v1"]
- [Assumption about data/environment, e.g., "Existing authentication system will be reused"]
- [Dependency on existing system/service, e.g., "Requires access to the existing user profile API"]
