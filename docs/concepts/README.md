# Core Concepts

Deep dives into the philosophy, principles, and architecture of Spec-Driven Development.

## Understanding Spec-Driven Development

### [Spec-Driven Development Philosophy](./spec-driven-philosophy.md)
The foundational ideas behind the methodology
- Why specifications matter
- The power inversion: specs over code
- Intent-driven development
- Elimination of the spec-code gap

### [The Three-Tier Hierarchy](./three-tier-hierarchy.md)
How product vision, specifications, and implementation plans work together
- Product Vision (strategic layer)
- Feature Specifications (requirements layer)
- Implementation Plans (architecture layer)
- Workflow integration across tiers

### [The Development Workflow](./development-workflow.md)
How the pieces fit together in practice
- The three-phase process: Specify → Plan → Execute
- Adaptive workflows for different complexities
- Quick, Lightweight, Full, and Decomposed modes
- Architecture evolution and versioning

## Key Principles

### [Spec Quality Principles](./spec-quality.md)
What makes a good specification
- Clarity and precision
- Requirements vs decisions
- Testability and acceptance criteria
- Documentation for future developers

### [Atomic Units and Decomposition](./atomic-decomposition.md)
Breaking large features into manageable pieces
- What makes a good capability
- Dependency patterns
- Parallel development strategies
- Merging atomic PRs

### [Architecture and Evolution](./architecture-evolution.md)
How architecture grows with your system
- Version tracking (v1.0.0, v1.1.0, v2.0.0)
- When to work within architecture
- When to extend
- When to refactor
- Documenting decisions

## Development Phases

### [Phase 1: Specification](./phase-specification.md)
The requirements gathering and validation phase
- What a spec contains
- Acceptance criteria
- Technical constraints
- Iterative refinement

### [Phase 2: Planning](./phase-planning.md)
The architecture and design phase
- Making technical decisions
- Technology selection rationale
- Data modeling
- System integration

### [Phase 3: Implementation](./phase-implementation.md)
The coding and validation phase
- Converting plans to code
- Testing strategies
- Deployment considerations
- Validation against spec

## Advanced Topics

### [Multi-Repository Architecture](./multi-repo-architecture.md)
Managing specifications across multiple codebases
- Workspace structure
- Convention-based routing
- Per-repo requirements
- Centralized specification

### [Working with Existing Systems](./brownfield-development.md)
Adding to established codebases
- Respecting constraints
- Incremental architecture evolution
- Managing technical debt
- Backward compatibility

### [Team and Process Patterns](./team-patterns.md)
How teams use Spec-Driven Development
- Spec review processes
- Branch strategies
- Collaborative workflows
- Scaling across teams

## FAQ

**Q: Why not just write code?**
A: Writing specifications first helps you think clearly about what you're building before getting lost in implementation details. It's like creating blueprints before construction—it saves time and prevents mistakes.

**Q: Doesn't this add overhead?**
A: Initially it might feel like more work, but it reduces total time by:
- Eliminating rework from ambiguous requirements
- Making code reviews faster (clear scope)
- Providing documentation that stays current
- Reducing bugs caught late in development

**Q: How does this work for small changes?**
A: Use [Quick Mode](../guides/simple-features.md)—create a minimal spec (2 minutes), skip planning, go straight to tasks.

**Q: Can I use this with existing projects?**
A: Yes! It works great for:
- Adding new features to existing systems
- Understanding and documenting existing code
- Planning major refactors
- Coordinating across teams

**Q: What if requirements change?**
A: Update the specification and re-plan if needed. Specifications are living documents that evolve with your understanding. This is actually an advantage—changes are captured at the right level rather than scattered through code.

## Terminology

**Specification** - Detailed description of what you're building (the "what" and "why")

**Implementation Plan** - Technical approach and architecture decisions (the "how")

**Capability** - An atomic unit of work (400-1000 LOC) that can be implemented and reviewed independently

**Decomposition** - Breaking a large feature (>1000 LOC) into smaller capabilities

**Acceptance Criteria** - Testable conditions that prove a requirement is met

**Technical Constraint** - Something you must work with (existing database, library, API)

**Architectural Decision** - How you'll solve a problem (Redis for caching, PostgreSQL for data)

## Getting Started with Concepts

1. **New to spec-driven development?** Start with [Spec-Driven Development Philosophy](./spec-driven-philosophy.md)
2. **Want to understand the structure?** Read [The Three-Tier Hierarchy](./three-tier-hierarchy.md)
3. **Ready to learn the workflow?** See [The Development Workflow](./development-workflow.md)
4. **Need to understand a specific phase?** Check [Phase 1](./phase-specification.md), [Phase 2](./phase-planning.md), or [Phase 3](./phase-implementation.md)
5. **Working with teams or multi-repo?** See [Team Patterns](./team-patterns.md) or [Multi-Repository Architecture](./multi-repo-architecture.md)

## Next Steps

- **Learn by doing**: Go to [Getting Started](../getting-started/) for tutorials
- **Find how-to guides**: Check [Guides](../guides/) for task-focused workflows
- **Look up details**: See [Reference](../reference/) for command and configuration documentation
