---
description: Generate quality checklists that validate design completeness, clarity, and consistency - "unit tests for requirements."
---

## User Input

```text
$ARGUMENTS
```

## Checklist Purpose: "Unit Tests for Requirements"

**CRITICAL CONCEPT**: Checklists are **UNIT TESTS FOR REQUIREMENTS WRITING** - they validate the quality, clarity, and completeness of requirements in a given domain.

**NOT for verification/testing**:
- ❌ NOT "Verify the button clicks correctly"
- ❌ NOT "Test error handling works"
- ❌ NOT "Confirm the API returns 200"

**FOR requirements quality validation**:
- ✅ "Are visual hierarchy requirements defined for all card types?" (completeness)
- ✅ "Is 'prominent display' quantified with specific sizing/positioning?" (clarity)
- ✅ "Are hover state requirements consistent across all interactive elements?" (consistency)
- ✅ "Does the design define what happens when the image fails to load?" (edge cases)

**Metaphor**: If your design is code written in English, the checklist is its unit test suite.

## Prerequisites

Check for design artifacts:

1. **Design** at `.minispec/specs/[feature-name]/design.md`
2. **Decisions** in `.minispec/knowledge/decisions/`
3. **Tasks** at `.minispec/specs/[feature-name]/tasks.md` (if exists)

If no design exists:
> "No design found. Run `/minispec.design` first to create requirements to validate."

## Execution Flow

### Phase 1: Understand Context

1. **Parse user input** from `$ARGUMENTS`:
   - What domain/focus? (security, ux, api, performance, etc.)
   - What depth? (quick check vs thorough audit)
   - What specific concerns?

2. **Ask clarifying questions** if needed (max 3):
   > "What aspect of the design should I focus on?
   > - **UX**: Visual hierarchy, interactions, states
   > - **API**: Contracts, error handling, consistency
   > - **Security**: Auth, data protection, threats
   > - **Performance**: Latency, scale, resources
   > - **General**: Completeness and clarity across the board"

### Phase 2: Load Design Context

Read from `.minispec/specs/[feature-name]/`:
- `design.md`: Components, data model, API, user stories
- `tasks.md`: Implementation breakdown (if exists)

Read from `.minispec/knowledge/`:
- `decisions/`: Documented decisions
- `conventions.md`: Established patterns

**Load efficiently**: Extract relevant sections, don't dump entire files.

### Phase 3: Generate Checklist

Create checklist at `.minispec/specs/[feature-name]/checklists/[domain].md`

**Structure**:
```markdown
---
type: checklist
domain: [ux|api|security|performance|general]
feature: [feature-name]
created: [YYYY-MM-DD]
status: [draft|active|completed]
---

# [Domain] Requirements Quality Checklist

**Purpose:** Validate [domain] requirements are complete, clear, and consistent.
**Feature:** [feature-name]

## Completeness

- [ ] CHK001 - Are [requirement type] defined for [scenario]? [Gap]
- [ ] CHK002 - Are [edge case] requirements specified? [Completeness]

## Clarity

- [ ] CHK003 - Is '[vague term]' quantified with specific criteria? [Clarity, Design §X]
- [ ] CHK004 - Are [requirements] unambiguous? [Clarity]

## Consistency

- [ ] CHK005 - Do [requirements A] align with [requirements B]? [Consistency]
- [ ] CHK006 - Are [patterns] consistent across [scope]? [Consistency]

## Measurability

- [ ] CHK007 - Can [requirement] be objectively verified? [Measurability]
- [ ] CHK008 - Are acceptance criteria defined for [feature]? [Acceptance]

## Coverage

- [ ] CHK009 - Are [scenario type] requirements addressed? [Coverage]
- [ ] CHK010 - Are error/failure cases defined? [Edge Case]

## Summary

- **Total Items:** [N]
- **Focus Areas:** [list]
- **Key Gaps Identified:** [list if any obvious ones]
```

### Item Writing Rules

**✅ CORRECT patterns** (test requirements quality):
- "Are [requirement type] defined/specified/documented for [scenario]?"
- "Is [vague term] quantified/clarified with specific criteria?"
- "Are requirements consistent between [section A] and [section B]?"
- "Can [requirement] be objectively measured/verified?"
- "Are [edge cases/scenarios] addressed in requirements?"
- "Does the design define [missing aspect]?"

**❌ PROHIBITED patterns** (test implementation):
- Starting with "Verify", "Test", "Confirm", "Check" + behavior
- References to code execution, user actions, system behavior
- "Displays correctly", "works properly", "functions as expected"
- Implementation details

### Quality Dimensions

Group items by what they validate:

| Dimension | What It Checks |
|-----------|----------------|
| Completeness | Are all necessary requirements present? |
| Clarity | Are requirements unambiguous and specific? |
| Consistency | Do requirements align without conflicts? |
| Measurability | Can requirements be objectively verified? |
| Coverage | Are all scenarios/edge cases addressed? |

### Domain-Specific Focus

**UX Checklist** (`ux.md`):
- Visual hierarchy specifications
- Interaction state definitions
- Accessibility requirements
- Responsive behavior
- Error/empty/loading states

**API Checklist** (`api.md`):
- Contract completeness
- Error response specifications
- Authentication requirements
- Rate limiting definitions
- Versioning strategy

**Security Checklist** (`security.md`):
- Authentication requirements
- Authorization definitions
- Data protection specifications
- Threat model coverage
- Compliance alignment

**Performance Checklist** (`performance.md`):
- Latency requirements
- Scale specifications
- Resource constraints
- Degradation behavior
- Monitoring requirements

### Phase 4: Present and Refine

Show the generated checklist:

> "Generated **[Domain] Requirements Quality Checklist** with [N] items.
>
> **Focus areas:**
> - [Area 1]: [N] items
> - [Area 2]: [N] items
>
> **Potential gaps I noticed:**
> - [Gap 1]
> - [Gap 2]
>
> Review the checklist above. Want me to:
> - Add items for specific concerns?
> - Adjust the focus areas?
> - Save it and move on?"

### Phase 5: Save

Once approved:
1. Create `.minispec/specs/[feature]/checklists/` directory if needed
2. Save checklist file
3. Confirm location

> "Checklist saved to `.minispec/specs/[feature]/checklists/[domain].md`
>
> Use this to validate your design before implementation.
> Run `/minispec.analyze` to check design-task alignment."

## Important Guidelines

- **Focus on requirements, not implementation**
- **Be specific**: Reference design sections
- **Be actionable**: Each item should have a clear resolution
- **Don't overwhelm**: 15-25 items is usually sufficient
- **Prioritize by risk**: Critical gaps first

## Examples

**❌ WRONG** (tests implementation):
```
- [ ] CHK001 - Verify landing page displays 3 cards
- [ ] CHK002 - Test hover states work on desktop
```

**✅ CORRECT** (tests requirements):
```
- [ ] CHK001 - Is the number of featured cards explicitly specified? [Completeness]
- [ ] CHK002 - Are hover state requirements defined for all interactive elements? [Coverage]
```

## Output Artifacts

Creates:
1. `.minispec/specs/[feature]/checklists/[domain].md` - The checklist file

Multiple checklists can coexist (ux.md, api.md, security.md, etc.)
