# Atomic PRs: Large Features as Multiple PRs

For features >1000 LOC estimated. Break into 400-1000 LOC capabilities for fast reviews and parallel development.

## Why Atomic PRs?

**Traditional large PR**: One 2500 LOC PR
- Takes 7+ days to review
- Hard to understand scope
- Blocks team progress
- Difficult to revert if issues found

**Atomic PRs** (Spec Kit way): Five 400-500 LOC PRs
- Each reviewed in 1-2 days
- Clear scope per PR
- Can merge as soon as ready
- Easy to revert individual capability if needed
- Team can work on different capabilities in parallel

## The Atomic PR Workflow

### Phase 1: Create the Full Specification (20 minutes)

Spec the entire feature as one unit:

```
/specify Build a real-time collaborative document editor that supports:
- Multiple users editing simultaneously
- Operational transformation for conflict resolution
- Rich text formatting (bold, italic, etc.)
- Comments and suggestions
- Version history with timestamps
- Automatic saving every 30 seconds
- Works offline with sync when reconnected
```

This single spec covers the whole system. Don't decompose yet.

### Phase 2: Decompose into Capabilities (5 minutes)

```
/decompose
```

The AI breaks down the spec into atomic capabilities:

- **cap-001-editor-core** (450 LOC) - Basic editor with text input
- **cap-002-formatting** (420 LOC) - Bold, italic, underline support
- **cap-003-real-time** (480 LOC) - WebSocket sync and operational transform
- **cap-004-collaboration** (390 LOC) - Multiple users, cursors, awareness
- **cap-005-history** (410 LOC) - Version history and undo/redo

Output structure:
```
specs/proj-123.document-editor/
├── spec.md                    [Full spec - shared by all]
├── cap-001-editor-core/
│   └── plan.md
├── cap-002-formatting/
│   └── plan.md
├── cap-003-real-time/
│   └── plan.md
├── cap-004-collaboration/
│   └── plan.md
└── cap-005-history/
    └── plan.md
```

### Phase 3: Plan Each Capability (5 minutes each)

Create a branch for each capability:

```
git checkout -b username/proj-123.document-editor
```

Plan the first capability:

```
/plan --capability cap-001
```

This:
1. Creates a new branch: `username/proj-123.document-editor-cap-001`
2. Generates `plan.md` for just this capability
3. Keeps the scope focused (400-1000 LOC)

### Phase 4: Implement Each Capability (20-40 minutes each)

For the first capability:

```
/tasks
implement specs/proj-123.document-editor/cap-001-editor-core/plan.md
```

Implementation happens on the capability branch.

### Phase 5: PR → Review → Merge (1-2 days each)

Create PR for cap-001:

```
git push origin username/proj-123.document-editor-cap-001
gh pr create --title "feat: add basic editor core (cap-001)" \
  --body "See specs/proj-123.document-editor/cap-001-editor-core/plan.md"
```

**Benefits at this stage:**
- Small, focused PR (450 LOC)
- Clear scope in spec and plan
- Reviewed in 1-2 days
- Can merge immediately
- Team sees progress

### Phase 6: Repeat for Next Capability

Once cap-001 is merged:

```
git checkout username/proj-123.document-editor
git pull origin main
/plan --capability cap-002
/tasks
implement specs/proj-123.document-editor/cap-002-formatting/plan.md
```

Create and merge cap-002 PR. Repeat for cap-003, cap-004, cap-005.

## Timeline Comparison

### Traditional Approach
```
Day 1: Spec & plan entire feature
Day 2-3: Implement all features
Day 4-10: Code review (7 days)
Day 11: Merge
Total: 11 days (but blocked from day 1-10)
```

### Atomic PR Approach
```
Day 1: Spec entire feature (20 min) + decompose (5 min)
  Then 5 parallel work streams:

Stream 1: Plan cap-001 → Implement → PR → Review (2 days) → Merge
Stream 2: Plan cap-002 → Implement → PR → Review (2 days) → Merge  [start day 3]
Stream 3: Plan cap-003 → Implement → PR → Review (2 days) → Merge  [start day 5]
...

All done by day 9 (instead of 11), with continuous merging
```

**Even better with team**: Team members work on different capabilities in parallel!

## Guidelines for Good Capabilities

### Size
- Each 400-1000 LOC
- 20-45 minutes to implement
- Requires 1-2 days to review

### Scope
- **One clear feature** per capability
- Can be integrated independently
- Has its own tests and acceptance criteria
- Documented in its own plan.md

### Dependencies
- Each can (ideally) be reviewed independently
- If dependencies exist, document them clearly
- Plan order accordingly (foundational first)

### Good vs Bad Decompositions

❌ **Bad**: Random line-count splitting
```
cap-001: 1000 LOC of the auth system
cap-002: 1000 LOC of the auth system
(Both incomplete, need each other)
```

✅ **Good**: Feature-based splitting
```
cap-001: Email/password authentication (420 LOC)
cap-002: OAuth2 integration (380 LOC)
cap-003: Session management (410 LOC)
(Each complete, can be reviewed independently)
```

## Real-World Example: User Management System

Full feature: 2400 LOC estimated

### Decomposition
- **cap-001-models** (320 LOC) - User model, DB schema
- **cap-002-auth** (450 LOC) - Login/registration endpoints
- **cap-003-profiles** (480 LOC) - Profile viewing/editing
- **cap-004-permissions** (380 LOC) - Role-based access control
- **cap-005-admin** (270 LOC) - Admin management interface

### Timeline
1. Plan cap-001 (5 min) → Implement (15 min) → PR → Merge (1-2 days)
2. Plan cap-002 (5 min) → Implement (25 min) → PR → Merge (1-2 days)
3. Plan cap-003 (5 min) → Implement (25 min) → PR → Merge (1-2 days)
4. Plan cap-004 (5 min) → Implement (20 min) → PR → Merge (1-2 days)
5. Plan cap-005 (5 min) → Implement (15 min) → PR → Merge (1-2 days)

Total: **~10 days** with continuous integration (vs 14+ days with one giant PR)

## Tips for Atomic PRs

1. **Start with core** - Plan foundational capabilities first
2. **Test each capability** - Don't skip tests for "small" capabilities
3. **Document dependencies** - Make clear what builds on what
4. **Keep specifications shared** - One spec for the whole feature
5. **Individual plans for each** - Each cap has its own plan.md
6. **Consistent naming** - Use cap-001, cap-002, etc. consistently
7. **Write good PR descriptions** - Reference the plan.md file

## When to Use Regular PRs vs Atomic PRs

**Regular PR (single feature <1000 LOC)**:
```
/specify → /plan → /tasks → /implement → Single PR
```

**Atomic PRs (feature >1000 LOC)**:
```
/specify → /decompose → Loop:
  /plan --capability capN → /tasks → /implement → Merge cap-N PR
```

## Parallel Development Example

With a 2-person team:

```
Person A works on cap-001 (15 min)
  ↓ (merged to main after 1 day)
Person B pulls main, starts cap-002 (20 min)
  ↓ (while B is implementing, A starts cap-003)
Person A works on cap-003 (25 min)
  ↓ (B's cap-002 PR reviewed in parallel)
Both continue on different capabilities
```

Much better than one person blocking the other for a week!

## Escalation

If after decomposition, a single capability still seems >1000 LOC:

```
/decompose --for cap-001

This further breaks down problematic capabilities
```

Continue until all capabilities are 400-1000 LOC.
