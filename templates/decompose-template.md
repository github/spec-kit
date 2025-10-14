# Capability Decomposition: [FEATURE NAME]

**Parent Spec:** [link to parent spec.md]
**Decomposition Date:** [DATE]
**LOC Budget:** 200-500 LOC per capability (justification required >500)

## Execution Flow (main)
```
1. Load parent spec.md from Input path
   → If not found: ERROR "No parent specification found"
2. Extract functional requirements (FR-001, FR-002, ...)
   → If <3 requirements: WARN "Consider single capability"
3. Identify bounded contexts:
   → Group by: entity lifecycle, workflow stage, API clusters
   → Analyze dependencies between contexts
4. Estimate LOC per capability:
   → Contract tests: 50-100 LOC
   → Models: 50-100 LOC
   → Services: 100-200 LOC
   → Integration tests: 50-100 LOC
   → Target total: 250-500 LOC per capability
5. Order capabilities:
   → By: infrastructure dependencies + business value
   → Mark foundation capabilities (no dependencies)
6. Validate decomposition:
   → Each capability 200-500 LOC (or justified >500)
   → No circular dependencies
   → All capabilities independently testable
   → Max 10 capabilities per parent feature
7. Generate capability directories and scoped specs
8. Return: SUCCESS (ready for /plan per capability)
```

---

## Decomposition Strategy

### Analysis Checklist
- [ ] Analyzed functional requirements (FR-001 to FR-XXX)
- [ ] Identified bounded contexts
- [ ] Estimated LOC per capability
- [ ] Ordered by dependencies and business value
- [ ] Validated each capability is independently testable
- [ ] Confirmed no circular dependencies
- [ ] Verified total ≤10 capabilities

### Sizing Guidelines

**Ideal Distribution:**
- **200-300 LOC:** Simple CRUD, single entity (target 30% of capabilities)
- **300-400 LOC:** Standard workflow, 2-3 entities (target 50% of capabilities)
- **400-500 LOC:** Complex integration, multiple services (target 15% of capabilities)
- **>500 LOC:** Exceptional, requires detailed justification (<5% of capabilities)

**Justification Required for >500 LOC:**
- Tight coupling that would break if split
- Single cohesive algorithm that must stay together
- Complex rule engine with interdependent logic
- Approved by tech lead with rationale documented

---

## Capabilities

### Cap-001: [Capability Name] (Est: XXX LOC)

**Scope:** [One sentence describing what this capability delivers]

**Dependencies:** [None (foundation) | Cap-XXX, Cap-YYY]

**Business Value:** [Why this capability matters, what it unblocks]

**Functional Requirements (from parent spec):**
- FR-XXX: [Requirement scoped to this capability]
- FR-YYY: [Requirement scoped to this capability]

**Component Breakdown:**
| Component | Estimated LOC | Notes |
|-----------|---------------|-------|
| Contract tests | XX | [e.g., 4 endpoints × 20 LOC each] |
| Models | XX | [e.g., User + Profile models] |
| Services | XX | [e.g., UserService CRUD] |
| Integration tests | XX | [e.g., Auth flow scenarios] |
| **Total** | **XXX** | [✓ Within budget | ⚠️ Requires justification] |

**Justification (if >500 LOC):**
[If total >500: Explain why splitting would harm cohesion, what keeps this together, why it's a single unit of work]

**Capability Branch:** `[username]/[feature-id]-cap-001`
**PR Target:** `cap-001` branch → `main` (atomic PR, 200-500 LOC)

**Acceptance Criteria:**
- [ ] [Specific testable criterion for this capability]
- [ ] [Specific testable criterion for this capability]
- [ ] All tests pass (contract + integration)
- [ ] Code review approved
- [ ] Merged to main

---

### Cap-002: [Capability Name] (Est: XXX LOC)

[Same structure as Cap-001]

---

### Cap-00X: [Capability Name] (Est: XXX LOC)

[Repeat for each capability - target 3-8 capabilities per feature]

---

## Dependency Graph

```
Cap-001 [Foundation - no dependencies]
  ├── Cap-002 [Depends on: Cap-001]
  ├── Cap-003 [Depends on: Cap-001]
  │     └── Cap-005 [Depends on: Cap-003, Cap-004]
  └── Cap-004 [Depends on: Cap-001]
        └── Cap-005 [Depends on: Cap-003, Cap-004]

Cap-006 [Independent - no dependencies]
  └── Cap-007 [Depends on: Cap-006]
```

**Parallel Execution Opportunities:**
- **Wave 1:** Cap-001 (foundation)
- **Wave 2:** Cap-002, Cap-003, Cap-004 (all depend only on Cap-001)
- **Wave 3:** Cap-005 (depends on Cap-003 + Cap-004)
- **Parallel Track:** Cap-006 → Cap-007 (independent of main flow)

---

## Implementation Strategy

### Recommended Order

1. **Foundation First:** Cap-001 (blocks others, establishes base)
2. **Parallel Development:** Cap-002, Cap-003, Cap-004 (independent of each other)
3. **Integration:** Cap-005 (combines earlier capabilities)
4. **Polish:** Cap-006, Cap-007 (observability, tooling)

### Team Allocation (if applicable)

- **Dev 1:** Cap-001 → Cap-002 → Cap-005
- **Dev 2:** Cap-003 → Cap-006
- **Dev 3:** Cap-004 → Cap-007

### Timeline Estimate

- **Monolithic approach:** 1 PR × 7 days review = 7 days blocked
- **Capability approach:** [X] PRs × 1.5 days review = [Y] days total
- **With parallelization:** ~[Z] days (overlapping work on independent capabilities)

---

## Validation Checklist

### Decomposition Quality
- [ ] All capabilities fall within 200-500 LOC (or have documented justification)
- [ ] Each capability delivers independently testable value
- [ ] No circular dependencies in dependency graph
- [ ] Foundation capabilities identified (enable others)
- [ ] Parallel execution opportunities documented

### Capability Completeness
- [ ] Each capability has clear scope and boundaries
- [ ] All parent spec functional requirements distributed to capabilities
- [ ] No orphaned requirements (all FRs assigned to a capability)
- [ ] Each capability has measurable acceptance criteria
- [ ] Business value articulated for each capability

### Implementation Readiness
- [ ] Capability directories created (cap-001/, cap-002/, ...)
- [ ] Scoped spec.md generated in each capability directory
- [ ] Dependency graph validated (no cycles)
- [ ] Implementation order documented
- [ ] Team allocation considered (if multi-person)

---

## Execution Status

*Updated during decomposition process*

- [ ] Parent spec loaded and analyzed
- [ ] Functional requirements extracted
- [ ] Bounded contexts identified
- [ ] LOC estimates calculated
- [ ] Dependencies mapped
- [ ] Capabilities ordered by priority
- [ ] Validation checklist passed
- [ ] Capability directories created
- [ ] Scoped specs generated
- [ ] Ready for /plan per capability

---

**Total Capabilities:** [X]
**Total Estimated LOC:** [Sum of all capabilities]
**Average LOC per Capability:** [Total / X]
**Capabilities >500 LOC:** [Count requiring justification]
