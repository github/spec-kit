---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

input: `/specs/[###-feature-name]/`
prereqs: plan.md, spec.md, research.md, data-model.md, contracts/

Format: `[ID] [P?] [Story] Description` | [P]=parallel | [Story]=US1,US2..

## Phase 1: Setup

- [ ] T001 Create project structure per plan
- [ ] T002 Init [language] project with [framework] deps
- [ ] T003 [P] Configure lint/format tools

## Phase 2: Foundation (blocks all stories)

- [ ] T004 Setup DB schema/migrations
- [ ] T005 [P] Implement auth framework
- [ ] T006 [P] Setup API routing/middleware
- [ ] T007 Create base models/entities
- [ ] T008 Configure error handling/logging

Checkpoint: foundation ready

## Phase 3: US1 [Title] (P1) MVP

goal: [deliverable]
test: [verification method]

- [ ] T010 [P] [US1] Create [Entity1] model src/models/[entity1].py
- [ ] T011 [P] [US1] Create [Entity2] model src/models/[entity2].py
- [ ] T012 [US1] Implement [Service] src/services/[service].py
- [ ] T013 [US1] Implement [endpoint] src/[location]/[file].py
- [ ] T014 [US1] Add validation/error handling

Checkpoint: US1 functional

## Phase 4: US2 [Title] (P2)

goal: [deliverable]
test: [verification method]

- [ ] T020 [P] [US2] Create [Entity] model
- [ ] T021 [US2] Implement [Service]
- [ ] T022 [US2] Implement [endpoint]

Checkpoint: US1+US2 functional

## Phase 5: US3 [Title] (P3)

goal: [deliverable]
test: [verification method]

- [ ] T026 [P] [US3] Create [Entity] model
- [ ] T027 [US3] Implement [Service]
- [ ] T028 [US3] Implement [endpoint]

Checkpoint: all stories functional

## Phase N: Polish

- [ ] TXXX [P] Docs updates
- [ ] TXXX Code cleanup
- [ ] TXXX Perf optimization
- [ ] TXXX Security hardening
- [ ] TXXX Run quickstart.md validation

## Dependencies

- Setup → Foundation → User Stories (parallel or P1→P2→P3) → Polish
- Within stories: models → services → endpoints
- [P] = different files, no deps
