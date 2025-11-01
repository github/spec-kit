# Team and Process Patterns

How teams use Spec-Driven Development at scale.

## Individual Contributor Pattern

Single developer working on features:
1. Create spec
2. Create plan
3. Implement

**Cadence**: New feature every 1-2 weeks

## Code Review Pattern

Spec-driven reviews for clarity:
1. Spec review - Clarify requirements
2. Plan review - Validate architecture
3. Code review - Validate implementation

Each review focuses on its phase, avoiding confusion.

## Pair Development Pattern

Two developers on same feature:
- One writes spec, other reviews
- Both create plan together
- Paired implementation with periodic reviews

**Benefits**: Knowledge sharing, catch issues early

## Parallel Capability Pattern

Large features split across team:
1. All create spec together
2. Each takes capability
3. Each plans and implements independently
4. Merge as each completes

**Benefits**: Faster completion, parallel work, faster reviews

## Spec Review Process

Best practices for spec reviews:
- Focus on requirements clarity, not implementation
- Ask: "Is this unambiguous?" not "How would you code this?"
- Document assumptions and constraints
- Ensure acceptance criteria are testable

## Plan Review Process

Best practices for plan reviews:
- Validate tech choices address spec requirements
- Check for architectural consistency
- Identify integration points and potential issues
- Ensure testing strategy is sound

## Code Review Integration

With clear specs and plans:
- Code reviews become faster (context is clear)
- Fewer "why did you..." questions
- Focus on quality, not understanding requirements

## Branching Strategy

Recommended git branching:

```
main                          # Production code
├── username/feature-name     # Feature branch
│   ├── capability-cap-001    # Capability branches
│   ├── capability-cap-002
│   └── capability-cap-003
└── ...
```

## Release Strategy

Releasing with specs:
- Specifications document what's in each release
- Version numbers align with architecture versions
- Changelog generated from specs

## Cross-Team Coordination

Specs enable async communication:
- Team A writes spec for their feature
- Team B reads spec to understand impact
- Minimal synchronous meetings needed
- Clear definition of integration points

## Documentation

Specs become living documentation:
- New team members read specs to understand why features exist
- Onboarding becomes faster
- Decisions are recorded, not scattered in code

## Anti-Patterns

❌ **Spec written without team input**
- Team doesn't buy in
- Missing constraints and edge cases

✅ **Spec review before planning**

❌ **Giant specs changed mid-implementation**
- Causes rework and confusion

✅ **Spec updates formalized and communicated**

❌ **Architecture decisions hidden in code**
- Maintenance nightmare

✅ **Architecture decisions documented in plan**

## Next Steps

- [Development Workflow](./development-workflow.md) - How phases work
- [Guides: Team Collaboration](../guides/) - Detailed team workflows
- [Getting Started](../getting-started/) - Hands-on tutorials
