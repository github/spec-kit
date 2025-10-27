# Implementation Plan (Lightweight Mode): [FEATURE NAME]

**Feature Branch**: `[BRANCH_NAME]`
**Created**: [DATE]
**Status**: Draft
**Mode**: Lightweight (200-800 LOC total)
**Input**: Technical details: "$ARGUMENTS"

---

## Technology Stack

**Language**: [Primary language]
**Framework**: [Web framework, if applicable]
**Database**: [Database system, if applicable]
**Key Libraries**: [Critical dependencies]

---

## System Architecture Context

<!-- If docs/system-architecture.md exists, reference it -->
**Current Architecture Version**: [version from system-architecture.md]
**Integration Points**: [APIs/services this feature interacts with]
**Deployment Model**: [How this will be deployed]

---

## Implementation Approach

### High-Level Design
[2-3 paragraphs describing the technical approach]

### Components

#### Component 1: [NAME]
**Purpose**: [What it does]
**Key Functions**: [Main operations]
**Estimated LOC**: [implementation + tests]

#### Component 2: [NAME]
**Purpose**: [What it does]
**Key Functions**: [Main operations]
**Estimated LOC**: [implementation + tests]

<!-- 2-4 components typical for lightweight mode -->

---

## Data Model

<!-- Only if database changes required -->

### Table/Collection: [NAME]
```
[attribute]: [type]  # Purpose
[attribute]: [type]  # Purpose
```

### Relationships
- [Describe key relationships]

---

## API Contracts

<!-- Only if API changes required -->

### Endpoint: [METHOD] /path
**Purpose**: [What it does]
**Request**: [Key fields]
**Response**: [Key fields]
**Status Codes**: [Expected codes]

---

## LOC Budget Tracking

**Target**: 200-800 LOC total (implementation + tests)

| Component | Implementation LOC | Test LOC | Total |
|-----------|-------------------|----------|-------|
| [Component 1] | ~X | ~Y | ~Z |
| [Component 2] | ~X | ~Y | ~Z |
| **TOTAL** | **~XXX** | **~XXX** | **~XXX** |

**Status**: [ ] Within budget | [ ] Needs review

---

## Implementation Sequence

1. [Step 1: Setup/scaffolding]
2. [Step 2: Core implementation]
3. [Step 3: Integration]
4. [Step 4: Testing]
5. [Step 5: Documentation]

---

## Testing Strategy

### Unit Tests
- [Component 1 test coverage]
- [Component 2 test coverage]

### Integration Tests
- [Key integration scenarios]

### Manual Testing
- [Critical user flows to verify]

---

## Dependencies

**External**: [Third-party services/APIs]
**Internal**: [Other features/components this depends on]
**Blocking**: [Must be completed first]

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | [High/Med/Low] | [How to address] |
| [Risk 2] | [High/Med/Low] | [How to address] |

---

## Review Checklist

- [ ] Technology stack aligns with system architecture
- [ ] LOC budget realistic (200-800 LOC total)
- [ ] All components have clear purpose
- [ ] Testing strategy adequate
- [ ] Dependencies identified
- [ ] Risks documented with mitigations

---

**Next Step**: Run `/tasks` to generate detailed implementation task list
