# Blueprint: [FEATURE NAME]

**Short Name**: `[short-name]`
**Date**: [YYYY-MM-DD]
**Status**: Draft | In Review | Approved | Implementing | Done
**Source Idea**: > [Quote the user's original problem statement here, verbatim]

---

## 1. Constitutional Gates

These principles are binding for this feature. Each is a checkbox the implementer verifies as they go. If a gate cannot be passed, document the violation in §13 Complexity Tracking.

- [ ] **Library-First**: Every feature begins as a standalone library with a clear purpose, self-contained and independently testable.
- [ ] **CLI Interface**: Every library exposes its functionality via a text-in/text-out CLI with JSON support.
- [ ] **Test-First (NON-NEGOTIABLE)**: Tests are written, approved, and confirmed failing before any implementation code is written.
- [ ] **Simplicity**: ≤3 projects, no future-proofing, no speculative abstractions.
- [ ] **Anti-Abstraction**: Use frameworks directly; one model representation; no wrapper layers without justification.
- [ ] **Integration-First Testing**: Tests use realistic environments (real DB, real services) over mocks; contract tests mandatory.

<!-- Adjust the list above to match the constitution found at memory/constitution.md or .specify/memory/constitution.md if one exists. -->

---

## 2. User Scenarios

User stories are prioritized as user journeys, ordered by importance. Each story is **independently testable** — implementing only that story still delivers a viable MVP slice.

### User Story 1 — [Brief Title] (Priority: P1) — MVP

[One-paragraph narrative description of the user journey in plain language.]

**Why this priority**: [Why P1; what value it unlocks first]

**Independent Test**: [How to verify this story works on its own — concrete action and observable outcome]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 — [Brief Title] (Priority: P2)

[Narrative]

**Why this priority**: [...]
**Independent Test**: [...]

**Acceptance Scenarios**:

1. **Given** [...], **When** [...], **Then** [...]

---

### User Story 3 — [Brief Title] (Priority: P3)

[Narrative]

**Why this priority**: [...]
**Independent Test**: [...]

**Acceptance Scenarios**:

1. **Given** [...], **When** [...], **Then** [...]

<!-- Add more stories as needed. P1 must always be the smallest shippable MVP. -->

---

## 3. Edge Cases

- What happens when [boundary condition]?
- How does the system handle [error scenario]?
- What happens at [scale limit]?
- Behavior when [external dependency unavailable]?

---

## 4. Functional Requirements

Each requirement must be testable and unambiguous. Use `[NEEDS CLARIFICATION: <specific question>]` only when no reasonable default exists. **Maximum 3 markers across the whole document.**

- **FR-001**: System MUST [capability]
- **FR-002**: System MUST [capability]
- **FR-003**: Users MUST be able to [interaction]
- **FR-004**: System MUST [data behavior]
- **FR-005**: System MUST [policy / non-functional behavior]

<!-- Example of a justified clarification:
- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: SSO vs OAuth vs email/password — significant UX and compliance impact]
-->

---

## 5. Key Entities

Domain concepts, no implementation detail. No field types, no schemas, no SQL.

- **[Entity 1]**: [What it represents, key attributes at the conceptual level]
- **[Entity 2]**: [What it represents, relationships to other entities]

---

## 6. Success Criteria

Measurable, technology-agnostic outcomes. Each must be verifiable without knowing the implementation.

- **SC-001**: [Time / completion metric, e.g., "Users complete onboarding in under 2 minutes"]
- **SC-002**: [Volume / scale metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [Quality / satisfaction metric, e.g., "90% of users complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets in category X by 50%"]

---

## 7. Assumptions

Defaults adopted because the source idea didn't specify. The implementer can challenge any of these.

- [Assumption about target users, e.g., "Users have stable internet connectivity"]
- [Assumption about scope, e.g., "Mobile support is out of scope for this slice"]
- [Assumption about environment, e.g., "Existing authentication service will be reused"]
- [Assumption about data, e.g., "Data retention follows industry-standard 90 days"]

---

## 8. Technical Context

| Field                   | Value                                            |
|-------------------------|--------------------------------------------------|
| Language / Version      | [e.g., Python 3.12 / TypeScript 5.4 / Rust 1.75] |
| Primary Dependencies    | [e.g., FastAPI, React 18, Tokio]                 |
| Storage                 | [e.g., PostgreSQL 16 / SQLite / files / N/A]     |
| Testing Framework       | [e.g., pytest, vitest, cargo test]               |
| Target Platform         | [e.g., Linux server / Browser / iOS 17+]         |
| Project Type            | [single library / CLI / web app / mobile + API]  |
| Performance Goals       | [e.g., 1000 req/s, 60 fps, 10k lines/sec]        |
| Constraints             | [e.g., <200ms p95, <100MB RAM, offline-capable]  |
| Scale / Scope           | [e.g., 10k users, 1M LOC, 50 screens]            |

---

## 9. Project Structure

### Documentation (this feature)

```text
specs/<NNN>-<short-name>/
├── BLUEPRINT.md         # This file
└── (legacy spec-kit artifacts may live here too — they're optional)
```

### Source Code (repository root)

<!-- Render the concrete tree for the chosen project type. Pick exactly one. -->

```text
# Single project
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

```text
# Web application
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

```text
# Mobile + API
api/
└── (same as backend above)

ios/   or   android/
└── (platform-specific feature modules and tests)
```

**Structure Decision**: [State which option you picked and why, referencing real directory names you'll create]

---

## 10. Tasks

Tasks are organized by user story so each story can be built, tested, and shipped independently. Format is strict: `- [ ] T### [P?] [USx?] Description with exact file path`.

- `[P]` = parallelizable with other `[P]` tasks in the same phase (no shared files, no dependency on incomplete tasks).
- `[USx]` = required for user-story-phase tasks; forbidden in Setup, Foundational, and Polish.

### Phase 1 — Setup (Shared Infrastructure)

- [ ] T001 Create project structure per §9
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools
- [ ] T004 [P] Configure CI scaffolding (lint + test stubs)

### Phase 2 — Foundational (Blocking Prerequisites)

> **CRITICAL**: No user-story work may begin until this phase is complete.

- [ ] T005 Set up database schema and migrations framework
- [ ] T006 [P] Implement authentication / authorization framework
- [ ] T007 [P] Set up routing and middleware structure
- [ ] T008 Create base entities/models that all stories depend on
- [ ] T009 Configure error handling and structured logging
- [ ] T010 Configure environment variable loading

**Checkpoint**: Foundation ready — user-story phases can now run in parallel (if staffed).

### Phase 3 — User Story 1: [Title] (P1) 🎯 MVP

**Goal**: [What this story delivers]
**Independent Test**: [How to verify it works on its own]

#### Tests for User Story 1 (write these first; they MUST FAIL before implementation)

- [ ] T011 [P] [US1] Contract test for [interface] in tests/contract/test_<name>.py
- [ ] T012 [P] [US1] Integration test for [user journey] in tests/integration/test_<name>.py

#### Implementation for User Story 1

- [ ] T013 [P] [US1] Create [Entity1] model in src/models/<entity1>.py
- [ ] T014 [P] [US1] Create [Entity2] model in src/models/<entity2>.py
- [ ] T015 [US1] Implement [Service] in src/services/<service>.py (depends on T013, T014)
- [ ] T016 [US1] Implement [endpoint/feature] in src/<location>/<file>.py
- [ ] T017 [US1] Add validation and error handling
- [ ] T018 [US1] Add logging for User Story 1 operations

**Checkpoint**: User Story 1 is fully functional and independently testable.

### Phase 4 — User Story 2: [Title] (P2)

**Goal**: [...]
**Independent Test**: [...]

#### Tests for User Story 2 (optional — only if requested)

- [ ] T019 [P] [US2] ...

#### Implementation for User Story 2

- [ ] T020 [P] [US2] ...
- [ ] T021 [US2] ...

**Checkpoint**: User Stories 1 and 2 both work independently.

### Phase 5 — User Story 3: [Title] (P3)

[same pattern]

### Phase N — Polish & Cross-Cutting

- [ ] T0XX [P] Documentation updates in docs/
- [ ] T0XX Performance optimization across stories
- [ ] T0XX Security hardening
- [ ] T0XX Run quickstart validation against §6 Success Criteria

---

## 11. Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** — no deps; can start immediately.
- **Foundational (Phase 2)** — depends on Setup; **blocks all user stories**.
- **User Stories (Phase 3+)** — all depend on Foundational. Stories may then run in parallel or sequentially in priority order.
- **Polish (Final)** — depends on all included user stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational. No deps on other stories.
- **US2 (P2)**: Starts after Foundational. May integrate with US1 but must remain independently testable.
- **US3 (P3)**: Starts after Foundational. May integrate with US1/US2 but must remain independently testable.

### Within Each User Story

- Tests (when present) MUST be written and FAIL before implementation begins.
- Models before services; services before endpoints; core before integration.
- A story is "complete" only when its checkpoint criteria are met.

### Parallel Opportunities

- All `[P]` Setup tasks can run together.
- All `[P]` Foundational tasks can run together (within Phase 2).
- After Foundational completes, all user-story phases can run in parallel given enough capacity.
- Within a story: all `[P]` tests run together; all `[P]` models run together.

---

## 12. Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 — Setup
2. Phase 2 — Foundational
3. Phase 3 — User Story 1
4. **STOP. Validate User Story 1 independently.**
5. Ship / demo.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. + User Story 1 → ship MVP.
3. + User Story 2 → ship.
4. + User Story 3 → ship.
5. Each story adds value without breaking earlier stories.

### Parallel Team Strategy

1. Whole team completes Setup + Foundational together.
2. Once Foundational is green:
   - Dev A: User Story 1
   - Dev B: User Story 2
   - Dev C: User Story 3
3. Stories integrate independently via the contracts established in Phase 2.

---

## 13. Complexity Tracking

> Fill this **only** if a Constitutional Gate (§1) is violated and you justify the violation. Otherwise leave blank.

| Violation                  | Why Needed                  | Simpler Alternative Rejected Because |
|----------------------------|-----------------------------|---------------------------------------|
| [e.g., 4th project]        | [the actual driver]         | [why 3 projects can't work here]     |
| [e.g., Repository pattern] | [the specific problem]      | [why direct DB access falls short]    |

---

## 14. Open Questions

> Items that remain unresolved after Phase 13 self-review. Each is a `[NEEDS CLARIFICATION]` that the implementer must resolve before the corresponding tasks can begin.

- [ ] Q1: [the question, with the section it blocks]
- [ ] Q2: ...

<!-- If empty, delete this section before reporting back to the user. -->

---

## 15. Change Log

| Date       | Author | Change                                    |
|------------|--------|-------------------------------------------|
| YYYY-MM-DD | [name] | Initial blueprint generated by skill.     |
