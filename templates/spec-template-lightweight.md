# Feature Specification (Lightweight Mode): [FEATURE NAME]

**Feature Branch**: `[username/jira-123.feature-name]` OR `[username/feature-name]`
**Created**: [DATE]
**Status**: Draft
**Mode**: Lightweight (200-800 LOC total)
**Input**: User description: "$ARGUMENTS"

<!-- Workspace Metadata (auto-populated in multi-repo workspaces) -->
**Workspace**: [WORKSPACE_NAME] (if workspace mode)
**Target Repository**: [REPO_NAME] (if workspace mode)

**Product Context**: docs/product-vision.md (if exists)
**System Architecture**: docs/system-architecture.md (if exists)

---

## Purpose

**What problem does this solve?**
[2-3 paragraphs describing the problem, who it affects, and why it matters]

**What is the proposed solution?**
[2-3 paragraphs describing the solution at a high level]

---

## User Scenarios & Testing

### Primary User Flow
**Actor**: [User type]
**Goal**: [What they want to accomplish]

#### Scenario: [SCENARIO NAME]
- GIVEN [initial context]
- WHEN [series of actions]
- THEN [expected outcomes]

<!-- Add 2-3 key scenarios -->

---

## Functional Requirements

### Requirement: [REQUIREMENT 1]
The system SHALL [requirement statement].

#### Scenario: [HAPPY PATH]
- GIVEN [context]
- WHEN [action]
- THEN [outcome]

#### Scenario: [ERROR CASE]
- GIVEN [context]
- WHEN [error condition]
- THEN [error handling]

<!-- Add 3-5 core requirements -->

---

## Non-Functional Requirements

### Performance
- [Specific measurable performance target]

### Security
- [Specific security requirements]

<!-- Add only critical NFRs -->

---

## Technical Constraints

**Must Integrate With**:
- [Existing system/API that must be used]

**Must Use**:
- [Technology/framework that must be used per system architecture]

<!-- Only list WHAT EXISTS, not implementation decisions -->

---

## Key Entities

### [Entity Name]
**Attributes**:
- [attribute]: [type/description]

<!-- Only if data modeling is relevant -->

---

## Acceptance Criteria

- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]
- [ ] [Performance targets met]
- [ ] [Security requirements satisfied]

---

## Out of Scope

- [Item 1 explicitly not included]
- [Item 2 explicitly not included]

---

## Review & Acceptance Checklist

- [ ] Every requirement is testable and unambiguous
- [ ] User scenarios cover all functional requirements
- [ ] Non-functional requirements are measurable
- [ ] Technical constraints documented (WHAT EXISTS)
- [ ] NO implementation details (architecture belongs in /plan)
- [ ] NO [NEEDS CLARIFICATION] markers for items that could be researched
- [ ] Acceptance criteria cover all requirements

---

**Next Step**: Run `/plan` with technology stack details to create implementation plan
