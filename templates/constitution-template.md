# [PROJECT_NAME] Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Vision & Direction
<!--
  The Vision is the stable, fixed objective for the project. It does not change
  with every feature. It answers: WHY this project exists, WHO it serves, and
  WHERE it is heading in the long term. Individual features added via
  `__SPECKIT_COMMAND_SPECIFY__` are incremental steps toward this Vision; the
  `__SPECKIT_COMMAND_DELTA__` command computes the gap between this Vision and
  current repo state to suggest the next feature.

  Keep this section terse, declarative, and durable — amendments here should be
  rare and follow the Governance procedure below.
-->

### North Star
<!-- One or two sentences. The single, enduring purpose of the project. -->
[NORTH_STAR_STATEMENT]
<!-- Example: Make spec-driven development the default way teams ship reliable software. -->

### Target Users & Value
<!-- Who this serves and the durable value delivered to them. -->
[TARGET_USERS_AND_VALUE]
<!-- Example: Engineering teams who want auditable, reproducible feature delivery; value = traceable path from intent to code. -->

### Long-Term Objectives
<!--
  A small set (3–7) of durable, outcome-oriented objectives. These are NOT a
  feature list — they describe *states the project should reach*. Each must be
  observable so `__SPECKIT_COMMAND_DELTA__` can assess progress against the
  current repo state.
-->
- [OBJECTIVE_1]
- [OBJECTIVE_2]
- [OBJECTIVE_3]
<!-- Example:
- Every shipped feature is traceable to a spec, a plan, and a verifiable test.
- Onboarding a new contributor to a workflow takes under 30 minutes.
- The framework supports at least three coding-agent integrations without core changes.
-->

### Non-Goals
<!-- Explicit statements of what the project will NOT pursue, to bound scope. -->
- [NON_GOAL_1]
- [NON_GOAL_2]
<!-- Example:
- Becoming a general-purpose project management tool.
- Replacing human review in the spec → implementation pipeline.
-->

## Core Principles

### [PRINCIPLE_1_NAME]
<!-- Example: I. Library-First -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->

### [PRINCIPLE_2_NAME]
<!-- Example: II. CLI Interface -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->

### [PRINCIPLE_3_NAME]
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Integration Testing -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Example: Text I/O ensures debuggability; Structured logging required; Or: MAJOR.MINOR.BUILD format; Or: Start simple, YAGNI principles -->

## [SECTION_2_NAME]
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

[SECTION_2_CONTENT]
<!-- Example: Technology stack requirements, compliance standards, deployment policies, etc. -->

## [SECTION_3_NAME]
<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->

[SECTION_3_CONTENT]
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

[GOVERNANCE_RULES]
<!-- Example: All PRs/reviews must verify compliance; Complexity must be justified; Use [GUIDANCE_FILE] for runtime development guidance -->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
