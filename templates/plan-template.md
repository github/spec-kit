# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [single/web/mobile - determines source structure]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Design System Check

*GATE: Verify alignment with design system (if exists). Skip if no design system defined.*

**Reference**: `.specify/memory/design-system.md`

<!--
  ACTION REQUIRED: If a design system exists at .specify/memory/design-system.md,
  fill this section to ensure the feature follows established design patterns.
  If no design system exists, this section can be removed or marked as N/A.
-->

[DESIGN_SYSTEM_VALIDATION]
<!-- Example:

- [ ] **Components follow design system patterns**
  - Using Button component (primary variant for CTAs, secondary for less important actions)
  - Using Card component for content grouping
  - Using Form pattern (vertical layout, proper spacing, validation states)

- [ ] **Colors use defined palette**
  - Primary color for CTAs and important actions
  - Semantic colors for success/warning/error messages
  - Neutral colors for text and backgrounds
  - No custom colors introduced without justification

- [ ] **Typography follows scale**
  - Headings use defined type scale (2xl for h1, xl for h2, etc.)
  - Body text uses base size (16px)
  - Font weights consistent (semibold for headings, regular for body)

- [ ] **Spacing follows system**
  - Using spacing scale (4, 6, 8 for standard spacing)
  - Consistent padding/margin throughout feature
  - Proper component spacing (cards, sections, etc.)

- [ ] **Accessibility standards met**
  - WCAG AA compliance (4.5:1 contrast minimum)
  - Keyboard navigation implemented
  - Screen reader labels for icon-only buttons
  - Focus indicators visible

- [ ] **Responsive design implemented**
  - Mobile-first approach (single column on mobile)
  - Uses defined breakpoints (sm: 640px, md: 768px, lg: 1024px)
  - Touch-optimized on mobile (44x44px minimum touch targets)
  - Proper responsive behavior for all components

**Deviations from Design System** (if any):
- [List any intentional deviations from the design system]
- [Provide justification for each deviation]
- [Ensure deviations align with constitution principles]
- [Consider if deviations should be added back to design system]

**New Patterns Introduced** (if any):
- [List any new UI patterns not covered by design system]
- [Justify need for new pattern]
- [Consider if pattern should be added to design system for reuse]

-->

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

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
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

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
