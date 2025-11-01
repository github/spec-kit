# Phase 1: Specification

Creating clear, testable requirements before implementation.

## What is a Specification?

A specification (spec) is a detailed description of what you're building:
- **What** features must exist
- **Why** they matter
- **Who** uses them
- **When** they're needed
- Acceptance criteria proving completion

## The Specification Process

1. **Create initial spec** - Describe your feature
2. **Iterate and clarify** - Ask questions, refine requirements
3. **Validate completeness** - Review acceptance checklist
4. **Get team agreement** - Ensure alignment

## What to Include

- Functional requirements (what it must do)
- Non-functional requirements (performance, security, scale)
- Technical constraints (what you must work with)
- User stories (how users interact)
- Acceptance criteria (testable proof of completion)
- Use cases (specific scenarios)
- Edge cases (unusual situations)

## Key Principle

**Requirements vs Decisions**

✅ Capture: "Must handle 1000 concurrent users"
❌ Don't capture: "Use Redis for caching"

The first describes what you need. The second is how you'll achieve it. Keep them separate.

## Spec Output

`specs/[feature-id]/spec.md` containing:
- Complete requirements
- Acceptance criteria with clear success conditions
- Review checklist (automatically included)

## Tips

- Be specific and concrete
- Use examples where helpful
- Ask clarifying questions
- Document constraints you're working within
- Think about edge cases

## Next Steps

- [Phase 2: Planning](./phase-planning.md) - Creating the implementation plan
- [Phase 3: Implementation](./phase-implementation.md) - Building the feature
- [Guides](../guides/) - Workflow examples
