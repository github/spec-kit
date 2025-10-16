# Capability Specification: [CAPABILITY NAME]

**Parent Feature:** [../spec.md](../spec.md)
**Capability ID:** Cap-XXX
**Estimated LOC:** Implementation XXX + Tests XXX = Total XXX (target: 400-1000 total)
**Dependencies:** [Cap-XXX, Cap-YYY | None]
**Created**: [DATE]
**Status**: Draft

## Execution Flow (main)
```
1. Verify parent spec exists at ../spec.md
   → If not found: ERROR "Parent spec required"
2. Extract scoped functional requirements from parent
   → Only requirements relevant to this capability
3. Define capability boundaries
   → What's IN scope for this capability
   → What's OUT of scope (handled by other capabilities)
4. Generate scoped user scenarios
   → Only scenarios this capability fulfills
5. Define acceptance criteria
   → Testable conditions for capability completion
6. Estimate component breakdown
   → Validate Implementation 200-500 LOC + Tests 200-500 LOC = Total 400-1000 LOC
7. Fill Context Engineering for this capability
   → Research codebase patterns specific to this scope
   → Document libraries/gotchas relevant to this capability
8. Run Review Checklist
   → If Impl >500 OR Tests >500 OR Total >1000: WARN "Exceeds budget, add justification"
9. Return: SUCCESS (ready for /plan --capability)
```

---

## ⚡ Capability Guidelines

- ✅ Focus on single bounded context (e.g., "User Auth", not "Entire User System")
- ✅ Independently testable and deployable
- ✅ Implementation 200-500 LOC + Tests 200-500 LOC = Total 400-1000 LOC (justification required if any limit exceeded)
- ❌ Avoid dependencies on uncompleted capabilities
- ❌ No cross-capability concerns (handle in separate capability)

---

## Capability Scope

### What's Included
[Explicit list of what this capability delivers]
- [Feature/function 1]
- [Feature/function 2]
- [Feature/function 3]

### What's Excluded
[Explicit list of what this capability does NOT handle - deferred to other capabilities]
- [Out of scope item 1] → Handled by Cap-XXX
- [Out of scope item 2] → Handled by Cap-YYY

### Capability Boundaries
[One paragraph defining the clear boundaries of this capability - what makes it atomic and complete]

---

## Context Engineering *(for AI agents)*

### Research & Documentation *(fill during /specify)*

```yaml
# MUST READ - Specific to this capability
- url: [URL with section anchor for this capability's needs]
  why: [Specific methods/patterns needed for THIS capability]
  critical: [Key insights for this capability's implementation]

- file: [exact/path/to/pattern/file.ext]
  why: [Pattern to follow for this capability]
  pattern: [What pattern this capability will use]
  gotcha: [Constraints specific to this capability]

- docfile: [ai_docs/relevant_to_this_capability.md]
  why: [Why this doc matters for this capability]
  section: [Specific section]
```

### Similar Features *(reference during /specify)*

List existing features relevant to THIS capability:
- **[Feature Name]** at `path/to/implementation` - [What pattern to reuse for this capability]

### External Research Notes *(fill during /specify)*

Research findings specific to this capability's scope:
- **Best Practices**: [For this capability's domain]
- **Common Pitfalls**: [For this capability type]
- **Performance Considerations**: [For this capability's operations]

---

## Functional Requirements (Scoped from Parent)

**From Parent Spec:**
- **FR-XXX** (Parent): [Full requirement from parent spec.md]
  - **Cap-XXX Scope**: [How this capability fulfills this requirement]

- **FR-YYY** (Parent): [Full requirement from parent spec.md]
  - **Cap-XXX Scope**: [Partial fulfillment - what part this capability handles]

**Capability-Specific Requirements:**
- **CFR-001**: This capability MUST [specific requirement for this scope]
- **CFR-002**: This capability MUST [specific requirement for this scope]
- **CFR-003**: Users MUST be able to [capability-specific interaction]

---

## User Scenarios & Testing *(capability-scoped)*

### Primary User Story (for this capability)
[Describe the user journey THIS capability enables - not the entire feature]

### Acceptance Scenarios (capability-scoped)
1. **Given** [initial state], **When** [capability action], **Then** [expected outcome]
2. **Given** [initial state], **When** [capability action], **Then** [expected outcome]

### Edge Cases (capability-specific)
- What happens when [boundary condition for this capability]?
- How does this capability handle [error scenario]?

---

## Key Entities *(if capability involves data)*

**Entities managed by THIS capability:**
- **[Entity 1]**: [What it represents, attributes managed by this capability]
- **[Entity 2]**: [What it represents, relationships within this capability]

**Entities referenced but not managed:**
- **[Entity X]**: [Managed by Cap-YYY, this capability only reads/references]

---

## Component Breakdown *(LOC estimation)*

| Component | Implementation LOC | Test LOC | Notes |
|-----------|-------------------|----------|-------|
| Models | XX | XX | [e.g., 2 entities × 50 LOC + validation tests] |
| Services | XX | XX | [e.g., Service layer logic + service tests] |
| API/CLI | XX | XX | [e.g., 3 endpoints × 30 LOC + contract tests] |
| Integration | XX | XX | [e.g., E2E scenarios] |
| **Subtotals** | **XXX** | **XXX** | **Total: XXX LOC** |
| **Status** | [✓ <500 \| ⚠️ >500] | [✓ <500 \| ⚠️ >500] | [✓ <1000 \| ⚠️ >1000] |

**Justification (if any limit exceeded):**
[If Implementation >500 OR Tests >500 OR Total >1000: Explain why this capability cannot be split further, what keeps it cohesive, why tests require more LOC than typical]

---

## Dependencies

### Upstream Dependencies
**This capability depends on:**
- **Cap-XXX**: [What this capability provides that we need]
  - **Why**: [Specific reason for dependency]
  - **Interfaces**: [Specific contracts/APIs we consume]

### Downstream Consumers
**Capabilities that depend on THIS capability:**
- **Cap-YYY**: [What they need from us]
  - **Contract**: [What we must provide]

### External Dependencies
- **Library/Service**: [External dependency for this capability]
- **Database**: [Data layer requirements]
- **API**: [External APIs this capability integrates with]

---

## Review & Acceptance Checklist

### Content Quality
- [ ] Scope clearly bounded (knows what it includes AND excludes)
- [ ] No implementation details (no tech stack, frameworks)
- [ ] Focused on single bounded context
- [ ] Dependencies on other capabilities documented

### Requirement Completeness
- [ ] All scoped requirements from parent spec included
- [ ] Capability-specific requirements (CFR-XXX) defined
- [ ] Requirements are testable within this capability
- [ ] Success criteria measurable for THIS capability
- [ ] LOC estimate: Implementation ≤500, Tests ≤500, Total ≤1000 (or justified if any exceeded)

### Capability Independence
- [ ] Can be implemented independently (given dependencies are met)
- [ ] Can be tested independently
- [ ] Delivers value on its own (vertical slice)
- [ ] Clear contracts with other capabilities

---

## Execution Status

*Updated during capability spec creation*

- [ ] Parent spec verified
- [ ] Capability scope defined
- [ ] Functional requirements scoped
- [ ] User scenarios extracted
- [ ] Component breakdown estimated (impl + test LOC)
- [ ] LOC budget validated (impl ≤500, tests ≤500, total ≤1000)
- [ ] Dependencies identified
- [ ] Review checklist passed

---

**Ready for:** `/plan --capability cap-XXX` to generate scoped implementation plan
