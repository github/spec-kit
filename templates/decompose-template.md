# Capability Decomposition: [FEATURE NAME]

**Parent Spec:** [link to parent spec.md]
**Decomposition Date:** [DATE]
**LOC Budget per Capability:** Implementation 200-500 + Tests 200-500 = Total 400-1000 LOC (justification required if any limit exceeded)

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
   → Implementation: Models (50-100) + Services (100-200) + API/CLI (50-100) = 200-400 LOC
   → Tests: Contract tests (50-100) + Integration tests (50-100) + Unit tests (100-200) = 200-400 LOC
   → Target total: 400-800 LOC per capability (max 1000 with justification)
5. Order capabilities:
   → By: infrastructure dependencies + business value
   → Mark foundation capabilities (no dependencies)
6. Validate decomposition:
   → Each capability: Impl ≤500, Tests ≤500, Total ≤1000 (or justified if any exceeded)
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
- [ ] Estimated LOC per capability (impl + test)
- [ ] Ordered by dependencies and business value
- [ ] Validated each capability is independently testable
- [ ] Confirmed no circular dependencies
- [ ] Verified total ≤10 capabilities

### Sizing Guidelines

**Ideal Distribution (Total LOC including tests):**
- **400-600 LOC:** Simple CRUD, single entity (200-300 impl + 200-300 tests) - target 30% of capabilities
- **600-800 LOC:** Standard workflow, 2-3 entities (300-400 impl + 300-400 tests) - target 50% of capabilities
- **800-1000 LOC:** Complex integration, multiple services (400-500 impl + 400-500 tests) - target 15% of capabilities
- **>1000 LOC:** Exceptional, requires detailed justification (<5% of capabilities)

**Justification Required if Implementation >500 OR Tests >500 OR Total >1000:**
- Tight coupling that would break if split
- Single cohesive algorithm that must stay together
- Complex rule engine with interdependent logic
- For tests >500: Extensive edge cases, complex integration scenarios requiring detailed testing
- Approved by tech lead with rationale documented

---

## Capabilities

### Cap-001: [Capability Name] (Est: XXX total LOC)

**Scope:** [One sentence describing what this capability delivers]

**Dependencies:** [None (foundation) | Cap-XXX, Cap-YYY]

**Business Value:** [Why this capability matters, what it unblocks]

**Functional Requirements (from parent spec):**
- FR-XXX: [Requirement scoped to this capability]
- FR-YYY: [Requirement scoped to this capability]

**Component Breakdown:**
| Component | Implementation LOC | Test LOC | Notes |
|-----------|-------------------|----------|-------|
| Models | XX | XX | [e.g., User + Profile entities + validation tests] |
| Services | XX | XX | [e.g., UserService CRUD + service tests] |
| API/CLI | XX | XX | [e.g., 4 endpoints + contract tests] |
| Integration | XX | XX | [e.g., E2E test scenarios] |
| **Subtotals** | **XXX** | **XXX** | **Total: XXX LOC** |
| **Status** | [✓ ≤500 \| ⚠️ >500] | [✓ ≤500 \| ⚠️ >500] | [✓ ≤1000 \| ⚠️ >1000] |

**Justification (if any limit exceeded):**
[If Impl >500 OR Tests >500 OR Total >1000: Explain why splitting would harm cohesion, what keeps this together, why it's a single unit of work, why tests require extensive LOC]

**Capability Branch:** `[username]/[jira-key].[feature-name]-cap-001`
**PR Target:** `cap-001` branch → `main` (atomic PR, 400-1000 LOC total)

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
- [ ] All capabilities: Impl ≤500, Tests ≤500, Total ≤1000 (or have documented justification)
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
**Total Estimated LOC:** [Sum of all capabilities - implementation + tests]
**Average LOC per Capability:** [Total / X]
**Capabilities Exceeding Limits:** [Count requiring justification (impl >500 OR tests >500 OR total >1000)]
