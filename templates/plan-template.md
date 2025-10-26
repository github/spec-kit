---
feature_id: [FEATURE DIRECTORY NAME]
branch: [###-feature-name]
created_at: [DATE]
generator_version: [CLI VERSION]
constitution_version: [CONSTITUTION VERSION OR UNKNOWN]
---

# Implementation Plan: [FEATURE]

**Spec Reference**: [link to spec.md]
**Planning Status**: Draft

## Summary

[Extract key intent from spec and outline the proposed technical direction.]

## Phase Exit Criteria

| Phase | Exit Criteria | Gate Owner |
|-------|---------------|------------|
| Phase 0 – Research | [List measurable checkpoints that must be true to proceed.] | [Role] |
| Phase 1 – Architecture & Contracts | [Document required artifacts (data-model, contracts, decisions).] | [Role] |
| Phase 2 – Implementation Readiness | [Confirm tasks baseline, agent context updated, blockers cleared.] | [Role] |

> Update exit criteria if the workflow introduces additional phases.

## Technical Context

| Dimension | Decision | Confidence | Notes |
|-----------|----------|------------|-------|
| Language / Runtime | [e.g., Python 3.11 or NEEDS CLARIFICATION] | [High/Med/Low] | [Why chosen] |
| Frameworks | [Primary frameworks/libraries] | | |
| Storage | [Databases or persistence layers] | | |
| Testing Strategy | [Unit/integration/contract tools] | | |
| Deployment Target | [Platforms/environments] | | |
| Constraints | [Performance, compliance, availability] | | |

## Constitution Check

### Pre-Phase 0 Gate

| Gate | Status (PASS/FAIL/WAIVED) | Evidence | Owner |
|------|--------------------------|----------|-------|
| [Gate name] | [Status] | [Link to section/evidence] | [Role] |

### Post-Phase 1 Gate

| Gate | Status (PASS/FAIL/WAIVED) | Evidence | Owner |
|------|--------------------------|----------|-------|
| [Gate name] | [Status] | [Link to section/evidence] | [Role] |

> Fail the command if any gate remains `FAIL` without mitigation.

## Decision Log (ADR Stubs)

| ID | Decision | Context | Status | Follow-up |
|----|----------|---------|--------|-----------|
| ADR-001 | [Decision title] | [What problem this solves] | Proposed/In Review/Accepted | [Next action] |
| ADR-002 | [Decision title] | [Context] | | |

## Risk Register

| ID | Description | Probability | Impact | Owner | Mitigation | Trigger |
|----|-------------|-------------|--------|-------|------------|---------|
| R1 | [e.g., Unvalidated integration dependency] | [High/Med/Low] | [High/Med/Low] | [Role] | [Mitigation plan] | [Signal to act] |
| R2 | [Add more] | | | | | |

## Research Backlog (Phase 0)

- **Objective**: Resolve all `NEEDS CLARIFICATION` markers and knowledge gaps before design.
- **Artifacts**: `research.md` summarizing answers, decisions, and references.
- **Outstanding Items**:
  - [ ] [Research task or question]
  - [ ] [Research task or question]

## Architecture & Contracts (Phase 1)

- **Data Model**: Summarize entities that must be documented in `data-model.md`.
- **Service / API Contracts**: Outline expected files in `contracts/` (OpenAPI, GraphQL, messaging schemas, etc.).
- **Quickstart**: Note the workflow that `quickstart.md` must capture for functional validation.
- **Agent Context Refresh**: Call out which agent(s) must be updated and what new guidance they require.

## Implementation Readiness (Phase 2)

- **Tasks Alignment**: Confirm prerequisites for `/speckit.tasks` (spec, plan, research, contracts) are complete.
- **Environments**: Identify environment/setup scripts needed before implementation begins.
- **Test Data**: Define datasets or fixtures that should exist prior to development.

## Project Structure

```text
specs/[###-feature]/
├── plan.md              # This file (generated via /speckit.plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

```text
[src/ structure as defined by this plan. Replace with actual layout.]
```

**Structure Decision**: [Document the selected structure and reference concrete directories.]

## Complexity Tracking

> Use this section when constitution violations are unavoidable. Remove if unused.

| Violation | Justification | Simpler Alternative Rejected Because |
|-----------|---------------|---------------------------------------|
| [e.g., 4th project] | [Why necessary] | [Why simpler option insufficient] |
