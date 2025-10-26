# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + implementation approach from research]

## implementation Context

<!--
  ACTION REQUIRED: Replace the content in this section with the implementation details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Team Dependencies**: [e.g., Finance team or NEEDS CLARIFICATION]  
**Important deadlines**: [e.g., Before commercial review week or NEEDS CLARIFICATION]
**Project Type**: [legal/HR/operations/other - determines source structure]  
**Key Performance Indicators (KPI)**: [Number of user requests decreased by 10% or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., legal regulations or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., team, department, country or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation           | Why Needed | Simpler Alternative Rejected Because |
|---------------------|------------|----------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., UK law]      | [specific problem] | [why direct access insufficient] |
