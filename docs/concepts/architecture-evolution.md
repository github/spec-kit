# Architecture and Evolution

How system architecture grows and evolves with features.

## Architecture Versioning

System architecture is versioned like software:

- **v1.0.0**: First feature establishes foundational architecture
- **v1.1.0**: Extensions to architecture (new components, capabilities)
- **v2.0.0**: Fundamental redesign (breaking changes)

## Architectural Decisions

Each feature's implementation plan documents:
- Architecture decisions with rationale
- Technology choices and why
- System integration points
- Changes to existing architecture

## Architecture Evolution Levels

### Level 1: Work Within
Use existing architecture without changes
- Time: Minimal
- Risk: Low
- Version: Same

### Level 2: Extend
Add new components or capabilities
- Time: Moderate
- Risk: Low-Medium
- Version: Minor bump (v1.2 → v1.3)

### Level 3: Refactor
Fundamental architectural changes
- Time: Significant
- Risk: Medium-High
- Version: Major bump (v1 → v2)

## Documentation

System architecture documented in `docs/system-architecture.md`:
- Current version and date
- Core components and their interactions
- Technology choices and rationale
- System constraints and assumptions
- Scaling characteristics

## When Architecture Changes

If a feature's plan would require architectural changes:
```
/plan should mention:
- Current architecture insufficient for requirements
- What changes are needed
- Whether this is Level 2 (extend) or Level 3 (refactor)
- Migration path from current to proposed
```

This triggers discussion before implementation begins.

## Next Steps

- [Development Workflow](./development-workflow.md) - How architecture fits in workflow
- [Guides: Complex Features](../guides/complex-features.md) - Real examples
