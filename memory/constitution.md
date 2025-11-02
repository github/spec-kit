# [PROJECT_NAME] Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

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
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced; Follow `~/.claude/instructions/standards/python/testing.md` for test patterns (Layer 1: 90% coverage, pytest-style primary; Layer 2: Outside-in TDD workflow) -->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Integration Testing -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Observability -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Example: Text I/O ensures debuggability; Structured logging required; Error context with correlation IDs -->

### [PRINCIPLE_6_NAME]
<!-- Example: VI. Versioning & Breaking Changes -->
[PRINCIPLE_6_DESCRIPTION]
<!-- Example: MAJOR.MINOR.BUILD format; Breaking changes require migration plans; Semantic versioning strictly followed -->

### [PRINCIPLE_7_NAME]
<!-- Example: VII. Simplicity -->
[PRINCIPLE_7_DESCRIPTION]
<!-- Example: Start simple, YAGNI principles; No premature optimization; Composition over inheritance -->

### [PRINCIPLE_8_NAME]
<!-- Example: VIII. Atomic Development & Scope Management -->
[PRINCIPLE_8_DESCRIPTION]
<!-- Example: Target per capability/PR: Implementation 200-500 LOC + Tests 200-500 LOC = Total 400-1000 LOC; Use /decompose for features >1000 LOC total; Benefits: faster reviews (1-2 days vs 7+ days), manageable TDD scope, parallel development, bounded test growth; Justification required if Implementation >500 OR Tests >500 OR Total >1000 with approval -->

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