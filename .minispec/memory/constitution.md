# [PROJECT_NAME] Constitution
<!-- Example: PhotoAlbum Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### [PRINCIPLE_1_NAME]
<!-- Example: I. Code Quality -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Example: All code must be readable, maintainable, and follow established patterns; No magic numbers; Meaningful names; Single responsibility -->

### [PRINCIPLE_2_NAME]
<!-- Example: II. Testing Standards -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Example: Unit tests for business logic; Integration tests for APIs; E2E tests for critical paths; Minimum 80% coverage on new code -->

### [PRINCIPLE_3_NAME]
<!-- Example: III. Documentation -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Example: Public APIs must be documented; Complex logic requires inline comments; Architecture decisions recorded -->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Security -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Example: No secrets in code; Input validation on all boundaries; Principle of least privilege -->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Performance, VI. Accessibility, VII. Error Handling -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Example: Lazy loading for large datasets; Core Web Vitals targets; Graceful degradation -->

## [SECTION_2_NAME]
<!-- Example: Technology Stack, Constraints, Standards -->

[SECTION_2_CONTENT]
<!-- Example: React 18+, TypeScript strict mode, PostgreSQL, deployed on AWS -->

## [SECTION_3_NAME]
<!-- Example: Development Workflow, Review Process -->

[SECTION_3_CONTENT]
<!-- Example: Feature branches, PR reviews required, CI must pass -->

---

## MiniSpec Preferences

<!--
This section configures how MiniSpec's pair programming workflow operates.
These preferences shape the collaboration between engineer and AI.
-->

### Review Chunk Size

[CHUNK_SIZE_PREFERENCE]
<!--
Options:
- small: 20-40 lines per chunk (maximum engagement, best for learning new codebases)
- medium: 40-80 lines per chunk (balanced pace, recommended default)
- large: 80-150 lines per chunk (for experienced engineers comfortable with larger reviews)
- adaptive: AI assesses complexity and suggests appropriate size per task
-->

### Documentation Review Policy

[DOC_REVIEW_POLICY]
<!--
Options:
- review-all: Engineer reviews all documentation changes before commit
- review-decisions: Engineer reviews decisions/ only, AI trusted for patterns/modules
- trust-ai: AI handles all documentation autonomously (recommended for velocity)
-->

### Autonomy Level

[AUTONOMY_LEVEL]
<!--
Options:
- always-confirm: AI always pauses for engineer approval before proceeding
- tests-passing: AI proceeds automatically if tests pass, pauses on failure
- familiar-areas: AI proceeds in code areas already reviewed this session
- explicit-batch: AI only batches when engineer explicitly says "next N"
-->

### Design Evolution Handling

[DESIGN_EVOLUTION_POLICY]
<!--
Options:
- always-discuss: AI stops implementation to discuss any design deviation
- flag-and-continue: AI flags issues, proposes spec updates, continues if minor
- auto-update: AI updates specs automatically, notifies engineer after (experienced teams)
-->

### Walkthrough Depth

[WALKTHROUGH_DEPTH]
<!--
Options:
- quick: High-level architecture overview (5-10 min)
- standard: Architecture + key patterns + conventions (15-20 min)
- deep: Full codebase tour with all modules explained (30+ min)
-->

---

## Governance

[GOVERNANCE_RULES]
<!-- Example: Constitution supersedes all other practices; Amendments require team discussion; MiniSpec preferences can be adjusted per-feature if needed -->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 1.0.0 | Ratified: 2025-02-01 | Last Amended: 2025-02-01 -->
