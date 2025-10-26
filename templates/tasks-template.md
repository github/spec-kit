---

description: "Task list template for initiative execution"
---

# Tasks: [INITIATIVE NAME]

**Input**: Planning documents from `/specs/[###-initiative-name]/`
**Prerequisites**: plan.md (required), spec.md (required for scenarios), stakeholder-analysis.md, communication-plan.md, execution-guide.md

**Organization**: Tasks are grouped by initiative scenario (from spec.md) to enable independent execution and validation of each business outcome.

## Format: `[ID] [P?] [Scenario] Description`

- **[P]**: Can run in parallel (different owners, no dependencies)
- **[Scenario]**: Which business scenario this task belongs to (e.g., S1, S2, S3)
- Include exact deliverable names and owners in descriptions

<!-- 
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.
  
  The /speckit.tasks command MUST replace these with actual tasks based on:
  - Business scenarios from spec.md (with their priorities P1, P2, P3...)
  - Initiative requirements from plan.md
  - Stakeholder needs from stakeholder-analysis.md
  - Communication activities from communication-plan.md
  
  Tasks MUST be organized by business scenario so each scenario can be:
  - Executed independently
  - Validated independently
  - Delivered as an incremental value add
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Initiative Setup & Planning

**Purpose**: Foundation setup and stakeholder alignment

- [ ] T001 Schedule and conduct initiative kickoff meeting with core team and executive sponsor
- [ ] T002 Set up initiative tracking dashboard or workspace (e.g., project management tool, shared drive)
- [ ] T003 [P] Establish communication channels (Slack channel, email distribution list, meeting series)
- [ ] T004 [P] Create and distribute initiative charter to all stakeholders
- [ ] T005 Finalize and get approval on initiative plan.md from executive sponsor

---

## Phase 2: Foundational Activities (Blocking Prerequisites)

**Purpose**: Core enablement that MUST be complete before ANY business scenario can be executed

**⚠️ CRITICAL**: No scenario work can begin until this phase is complete

Examples of foundational tasks (adjust based on your initiative):

- [ ] T006 Conduct stakeholder workshop to validate current state and gather requirements
- [ ] T007 [P] Complete baseline data collection for all Key Results
- [ ] T008 [P] Secure budget approval and resource commitments from all teams
- [ ] T009 Document current state processes and identify gaps (create process-maps.md if relevant)
- [ ] T010 Establish governance structure (steering committee, decision rights, escalation paths)
- [ ] T011 Complete regulatory/compliance review and obtain required approvals
- [ ] T012 [P] Set up measurement framework and reporting mechanisms for KPIs

**Checkpoint**: Foundation ready - scenario execution can now begin in parallel (or sequentially by priority)

---

## Phase 3: Scenario 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this scenario delivers]

**Independent Validation**: [How to verify this scenario achieves its outcome]

### Planning & Design for Scenario 1

- [ ] T013 [P] [S1] Conduct working session with [stakeholder group] to define detailed requirements
- [ ] T014 [S1] Create process flow diagram showing current state → future state for [specific process]
- [ ] T015 [S1] Draft policy/procedure document for [specific change]
- [ ] T016 [P] [S1] Design forms, templates, or tools needed for [process/outcome]

### Communication & Change Management for Scenario 1

- [ ] T017 [P] [S1] Create communication materials (email template, FAQ, talking points) for [stakeholder group]
- [ ] T018 [S1] Conduct town hall or information session for [affected group]
- [ ] T019 [P] [S1] Set up feedback mechanism (survey, office hours, feedback form)
- [ ] T020 [S1] Train managers/leaders on [new process/policy/system]

### Documentation & Approvals for Scenario 1

- [ ] T021 [S1] Draft and circulate policy/procedure for review to [approval group]
- [ ] T022 [S1] Incorporate feedback and revise documentation
- [ ] T023 [S1] Obtain formal approval from [authority/committee]
- [ ] T024 [P] [S1] Publish approved documentation to [location/system]

### Execution & Rollout for Scenario 1

- [ ] T025 [S1] Conduct pilot with [pilot group] (if applicable)
- [ ] T026 [S1] Gather pilot feedback and make adjustments
- [ ] T027 [P] [S1] Deliver training to [user group 1]
- [ ] T028 [P] [S1] Deliver training to [user group 2]
- [ ] T029 [S1] Execute go-live communication plan
- [ ] T030 [S1] Launch [process/system/policy] to [target audience]

### Validation & Measurement for Scenario 1

- [ ] T031 [P] [S1] Collect adoption metrics (e.g., % of team using new process)
- [ ] T032 [P] [S1] Conduct post-implementation survey with [user group]
- [ ] T033 [S1] Hold retrospective with core team to identify improvements
- [ ] T034 [S1] Report results against Scenario 1 validation criteria from spec.md

**Checkpoint**: At this point, Scenario 1 should be fully executed and validated independently

---

## Phase 4: Scenario 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this scenario delivers]

**Independent Validation**: [How to verify this scenario achieves its outcome]

### Planning & Design for Scenario 2

- [ ] T035 [P] [S2] Conduct working session with [stakeholder group] to define requirements
- [ ] T036 [S2] Create detailed plan for [specific deliverable]
- [ ] T037 [P] [S2] Design materials or tools needed for [outcome]

### Communication & Change Management for Scenario 2

- [ ] T038 [P] [S2] Create targeted communication for [stakeholder group]
- [ ] T039 [S2] Conduct workshop or training session for [affected group]
- [ ] T040 [P] [S2] Establish feedback loop and support channel

### Documentation & Approvals for Scenario 2

- [ ] T041 [S2] Draft required documentation or policy updates
- [ ] T042 [S2] Obtain approvals from [authority]
- [ ] T043 [P] [S2] Publish and distribute approved materials

### Execution & Rollout for Scenario 2

- [ ] T044 [S2] Execute rollout plan for [deliverable]
- [ ] T045 [P] [S2] Deliver enablement/training as needed
- [ ] T046 [S2] Monitor adoption and provide support

### Validation & Measurement for Scenario 2

- [ ] T047 [P] [S2] Measure outcomes against Scenario 2 validation criteria
- [ ] T048 [S2] Gather stakeholder feedback
- [ ] T049 [S2] Report results and lessons learned

**Checkpoint**: At this point, Scenarios 1 AND 2 should both be validated independently

---

## Phase 5: Scenario 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this scenario delivers]

**Independent Validation**: [How to verify this scenario achieves its outcome]

### Planning & Design for Scenario 3

- [ ] T050 [P] [S3] Conduct stakeholder working session
- [ ] T051 [S3] Design approach and deliverables
- [ ] T052 [P] [S3] Create supporting materials

### Communication & Change Management for Scenario 3

- [ ] T053 [P] [S3] Develop communication plan and materials
- [ ] T054 [S3] Execute stakeholder engagement activities
- [ ] T055 [P] [S3] Provide training and enablement

### Documentation & Approvals for Scenario 3

- [ ] T056 [S3] Create and approve documentation
- [ ] T057 [P] [S3] Publish materials

### Execution & Rollout for Scenario 3

- [ ] T058 [S3] Execute rollout
- [ ] T059 [P] [S3] Monitor and support adoption

### Validation & Measurement for Scenario 3

- [ ] T060 [P] [S3] Measure and validate outcomes
- [ ] T061 [S3] Report results

**Checkpoint**: All scenarios should now be independently validated

---

[Add more scenario phases as needed, following the same pattern]

---

## Phase N: Closure & Sustainment

**Purpose**: Ensure lasting impact and continuous improvement

- [ ] TXXX [P] Conduct 30-day post-launch review meeting with core team
- [ ] TXXX [P] Complete lessons learned documentation
- [ ] TXXX Measure all Key Results and compare to baseline (create final KPI report)
- [ ] TXXX [P] Conduct stakeholder satisfaction survey
- [ ] TXXX Present final results and outcomes to executive sponsor and steering committee
- [ ] TXXX [P] Create sustainment plan (ongoing ownership, monitoring, optimization)
- [ ] TXXX Transition initiative to BAU (business-as-usual) operations with designated owner
- [ ] TXXX [P] Celebrate success and recognize team contributions
- [ ] TXXX Schedule 90-day sustainability check
- [ ] TXXX Archive initiative artifacts and update organizational knowledge base

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all scenarios
- **Business Scenarios (Phase 3+)**: All depend on Foundational phase completion
  - Scenarios can then proceed in parallel (if resources allow)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Closure & Sustainment (Final Phase)**: Depends on all desired scenarios being complete

### Scenario Dependencies

- **Scenario 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other scenarios
- **Scenario 2 (P2)**: Can start after Foundational (Phase 2) - May build on S1 but should be independently validatable
- **Scenario 3 (P3)**: Can start after Foundational (Phase 2) - May leverage S1/S2 learnings but should be independently validatable

### Within Each Scenario

- Planning & design before execution
- Documentation & approvals before rollout
- Communication & training before/during rollout
- Validation after execution complete
- Feedback loops throughout

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all scenarios can start in parallel (if team capacity allows)
- Within each scenario, tasks marked [P] can run in parallel
- Different scenarios can be worked on in parallel by different team members

---

## Parallel Example: Scenario 1

```text
# Launch all planning activities for Scenario 1 together:
Task: "Conduct working session with [stakeholder group]"
Task: "Design forms, templates, or tools needed"
Task: "Create communication materials"

# Launch all training delivery in parallel:
Task: "Deliver training to [user group 1]"
Task: "Deliver training to [user group 2]"
```

---

## Execution Strategy

### MVP First (Scenario 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all scenarios)
3. Complete Phase 3: Scenario 1
4. **STOP and VALIDATE**: Measure Scenario 1 outcomes against validation criteria
5. Review results with stakeholders before proceeding

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Execute Scenario 1 → Validate independently → Review results (MVP!)
3. Execute Scenario 2 → Validate independently → Review results
4. Execute Scenario 3 → Validate independently → Review results
5. Each scenario adds value without disrupting previous scenarios

### Parallel Team Strategy

With multiple team members or workstreams:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Team Member A / Workstream 1: Scenario 1
   - Team Member B / Workstream 2: Scenario 2
   - Team Member C / Workstream 3: Scenario 3
3. Scenarios complete and validate independently with coordination touchpoints

---

## Notes

- [P] tasks = different owners/workstreams, no dependencies
- [Scenario] label maps task to specific business scenario for traceability
- Each scenario should be independently completable and validatable
- Gather stakeholder feedback continuously throughout execution
- Adjust course based on data and feedback
- Stop at any checkpoint to validate scenario independently before proceeding
- Avoid: vague tasks, overlapping responsibilities, scenario dependencies that break independence

## Task Execution Best Practices

1. **Clear Ownership**: Every task should have a named owner
2. **Definition of Done**: Each task should have clear completion criteria
3. **Stakeholder Engagement**: Involve right people at right time
4. **Documentation**: Keep records of decisions, feedback, and changes
5. **Communication**: Update stakeholders regularly on progress
6. **Measurement**: Track metrics continuously, not just at the end
7. **Flexibility**: Be prepared to adjust based on feedback and learnings
8. **Celebrate Wins**: Acknowledge progress and successes along the way
