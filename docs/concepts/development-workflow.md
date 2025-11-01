# The Development Workflow

The complete workflow from idea to implementation.

## The Three-Phase Process

```
🎯 Phase 1: SPECIFICATION
   Clarify what you're building (the "what" and "why")
   └─ Output: spec.md with requirements and constraints

📐 Phase 2: PLANNING
   Decide how you'll build it technically (the "how")
   └─ Output: plan.md with architecture and design decisions

📋 Phase 3: IMPLEMENTATION
   Build it according to the plan
   └─ Output: Working code + tests
```

Each phase builds on and validates the previous one.

## Phase Details

### Phase 1: Specification
**Time**: 15-30 minutes
**Goal**: Clear, testable requirements

1. Describe what you're building (`/specify`)
2. Iterate with clarifications (`/specify` again)
3. Validate completeness (review checklist)
4. Get team agreement

**Outputs**:
- `specs/[feature-id]/spec.md` - The specification
- Acceptance criteria that prove completion

### Phase 2: Planning
**Time**: 20-40 minutes
**Goal**: Detailed technical approach

1. Specify your tech stack and approach (`/plan`)
2. Review architecture decisions
3. Validate against specification
4. Address any concerns

**Outputs**:
- `specs/[feature-id]/plan.md` - Implementation plan
- `docs/system-architecture.md` - Updated system architecture
- Data models, API designs, testing strategy

### Phase 3: Implementation
**Time**: Varies
**Goal**: Working, tested implementation

1. Create task breakdown (`/tasks`)
2. Implement according to plan
3. Validate against spec acceptance criteria
4. Submit for review

**Outputs**:
- Implementation code
- Tests proving acceptance criteria
- Git commits with traceability to spec

## Adaptive Workflows: Choosing Depth

Not all features need the same process depth.

### Quick Mode (<200 LOC)
```
/specify (2 min) → /tasks (2 min) → /implement (varies)
Skip: detailed planning, research
Time: 5-10 minutes prep
Use: Bug fixes, config changes, small tweaks
```

### Lightweight Mode (200-800 LOC)
```
/specify (5 min) → /plan (10 min) → /tasks (3 min) → /implement
Skip: deep research, extensive architecture work
Time: 15-30 minutes prep
Use: Simple features, straightforward additions
```

### Full Mode (800-1000 LOC)
```
/specify (15 min) → Refine (10 min) → /plan (20 min) → /tasks (5 min) → /implement
Include: Full research, complete architecture, data models
Time: 45-60 minutes prep
Use: Complex features, new systems
```

### Decomposed Mode (>1000 LOC)
```
/specify (15 min) → /decompose (5 min) → For each capability:
  /plan --capability capN → /tasks → /implement → PR review & merge
Time: 45+ minutes + atomic PR reviews
Use: Large features, parallel development
```

## Decision Tree

```
How much code (~estimate)?

├─ <200 LOC
│  └─ Quick Mode: /specify → /tasks → /implement
│
├─ 200-800 LOC
│  └─ Lightweight: /specify → /plan → /tasks → /implement
│
├─ 800-1000 LOC
│  └─ Full: /specify → refine → /plan → /tasks → /implement
│
└─ >1000 LOC
   └─ Atomic: /specify → /decompose → Per-capability workflow
```

## Working Within vs Evolving Architecture

When planning features, you'll encounter existing architecture:

**Level 1: Work Within**
- Use existing patterns and components
- No architectural changes
- Version stays same (v1.2.0)
- Fastest implementation

**Level 2: Extend**
- Add new components or capabilities
- Architecture grows but fundamentally same
- Minor version bump (v1.2.0 → v1.3.0)
- Clear extension points

**Level 3: Refactor**
- Fundamental redesign needed
- Core structure changes
- Major version bump (v1.2.0 → v2.0.0)
- Breaking changes documented

## The Feedback Loop

```
Production
    ↓ (insights from)
Metrics & Incidents
    ↓ (inform)
Next Specification
    ↓ (drives)
Implementation
```

This creates continuous evolution where:
- Performance issues become NFR improvements
- User behavior changes requirements
- Operational learnings become constraints

## Key Principles

1. **Clarity First** - Don't code until spec is clear
2. **Plan Before Building** - Architecture prevents rework
3. **Iterative Refinement** - Specs improve through dialogue
4. **Testable Requirements** - Specs have acceptance criteria
5. **Traced Decisions** - Architecture choices reference requirements
6. **Atomic Units** - Large features break into manageable pieces
7. **Living Documentation** - Specs stay current with implementation

## Common Questions

**Q: Do I have to do all three phases?**
A: For anything >200 LOC, yes. Use Quick Mode for smaller changes.

**Q: What if requirements change mid-implementation?**
A: Update the spec, discuss changes with team, adjust plan if needed.

**Q: When should I decompose into capabilities?**
A: When you estimate >1000 LOC total.

**Q: Can I work on multiple features in parallel?**
A: Yes! Each has its own spec/plan. Use atomic PRs for fine-grained parallelism.

## Next Steps

- [Phase 1: Specification](./phase-specification.md) - Deep dive on spec creation
- [Phase 2: Planning](./phase-planning.md) - Deep dive on planning
- [Phase 3: Implementation](./phase-implementation.md) - Deep dive on implementation
- [Guides](../guides/) - Workflow examples for different scenarios
