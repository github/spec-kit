# How-To Guides

Task-focused guides for common development scenarios. Start by finding the workflow that matches your situation.

## By Feature Complexity

### Simple Features (<200 LOC)
**When**: Bug fixes, small tweaks, configuration changes

→ [Quick Mode Guide](./simple-features.md) - 5-10 minute workflow
- Minimal spec
- Skip research and planning
- Go straight to tasks

### Standard Features (200-800 LOC)
**When**: New features, straightforward additions, brownfield modifications

→ [Standard Workflow Guide](./standard-features.md) - 15-30 minute workflow
- Lightweight spec
- Compact planning
- Clear task breakdown

### Complex Features (800-1000 LOC)
**When**: New systems, critical features, major refactors

→ [Complex Feature Guide](./complex-features.md) - 45-60 minute workflow
- Full specification with research
- Detailed implementation planning
- Architecture documentation

### Massive Features (>1000 LOC)
**When**: Large systems that need atomic PRs for fast reviews

→ [Atomic PRs & Capabilities](./atomic-prs.md) - Multiple PRs approach
- Break into 400-1000 LOC capabilities
- Parallel development
- Fast reviews (1-2 days per PR)

## By Use Case

### Multi-Repository Projects
**When**: Coordinating specs across multiple repos

→ [Multi-Repo Workspaces](./multi-repo-workspaces.md) - Full multi-repo guide
- Setting up workspace structure
- Convention-based routing
- Per-repo requirements

### Adding Features to Existing Products
**When**: Extending a system that already has specifications and architecture

→ [Brownfield Development](./brownfield-features.md) - Extending existing systems
- Working within existing architecture
- Respecting system constraints
- Maintaining consistency

### Team Development
**When**: Working with multiple developers on specs and code

→ [Team Collaboration](./team-workflows.md) - Collaborative workflows
- Spec review processes
- Branch strategies
- Merging specifications and implementations

### Performance-Critical Features
**When**: Features with specific performance targets

→ [Performance-Driven Development](./performance-features.md) - Performance-focused approach
- Capturing performance requirements
- Architecture for scale
- Validation and testing

## By Technology Stack

### Frontend Development
→ [Frontend Guide](./frontend-development.md)

### Backend Services
→ [Backend Guide](./backend-development.md)

### Full-Stack Features
→ [Full-Stack Guide](./fullstack-development.md)

## Quick Decision Tree

```
What are you building?

├─ Bug fix or tiny change?
│  └─→ Simple Features (Quick Mode)
│
├─ New feature for existing product?
│  └─→ Brownfield Development
│
├─ Large system (>1000 LOC)?
│  └─→ Atomic PRs & Capabilities
│
├─ Coordinating multiple repos?
│  └─→ Multi-Repo Workspaces
│
├─ Working with a team?
│  └─→ Team Collaboration
│
└─ Otherwise?
   └─→ Standard or Complex Features
      (depends on your estimation)
```

## Common Patterns

### Pattern: Sequential Simple Features
Building several small features in sequence

1. Create spec for feature 1
2. Plan feature 1
3. Implement feature 1
4. Merge to main
5. Repeat for features 2, 3, 4...

→ Best for: Steady feature development on established systems

### Pattern: Decomposed Complex Feature
Breaking a large feature into atomic PRs

1. Create spec for entire feature
2. Run `/decompose` to break into capabilities
3. For each capability:
   - Plan capability 1, 2, 3...
   - Implement as separate PR
   - Merge immediately
   - Each reviewed in 1-2 days

→ Best for: Large features, faster code reviews

### Pattern: Architecture Evolution
Adding a new system that requires architectural changes

1. Create product vision (if not exists)
2. Specify feature with architectural implications
3. Plan feature (updates system-architecture.md)
4. Implement with new architecture
5. Document changes and migration path

→ Best for: Major new capabilities, platform improvements

## Tips & Tricks

**Refinement Loop**: It's normal to iterate multiple times on specs before planning. Use `/specify` with follow-ups to clarify requirements.

**Plan Review**: Always review the implementation plan before starting coding. Ask the AI: "What could go wrong?" or "Are we missing anything?"

**Atomic Commits**: Use `/smart-commit` for intelligent commit messages that tell the development story.

**Architecture Tracking**: Keep `docs/system-architecture.md` updated as features evolve the system.

**Documentation**: Update relevant docs after implementation. Specs are your source of truth.

## Next Steps

- Pick a guide that matches your situation
- Follow the workflow step-by-step
- For deeper understanding, check [Concepts](/concepts/)
- For detailed references, see [Reference](/reference/)
