# Atomic Units and Decomposition

Breaking large features into manageable, independently-deliverable pieces.

> **Note**: This section contains additional detail about decomposition strategies. See [Guides: Atomic PRs](../guides/atomic-prs.md) for practical workflow examples.

## What Makes an Atomic Unit?

An atomic unit (capability) should:
- Be **implementable** in 20-45 minutes
- Be **testable** independently
- Have **clear value** by itself
- Have **minimal dependencies** on other capabilities
- Result in **400-1000 LOC** of code

## Decomposition Strategy

When a feature is estimated >1000 LOC:

1. Create the full specification
2. Run `/decompose` to break into capabilities
3. For each capability:
   - Create implementation plan
   - Implement independently
   - Submit PR and merge
   - Move to next capability

## Benefits

✅ **Fast code reviews** (1-2 days vs 7+ days)
✅ **Parallel development** (team members work simultaneously)
✅ **Incremental integration** (merge as soon as ready)
✅ **Easier rollback** (individual capability if needed)
✅ **Clearer history** (each capability tells a story)

## Guidelines

- Capabilities should be ordered (foundational first)
- Minimize cross-capability dependencies
- Each capability should be a cohesive feature unit
- Documentation applies to whole feature, plans per capability

See [Guides: Atomic PRs](../guides/atomic-prs.md) for detailed workflow and examples.
