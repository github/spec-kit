# spec-kit-amend

A Spec Kit extension for targeted post-implementation amendments.

## Overview

`speckit.amend` fills a gap in the standard spec-kit workflow: when an edge case, missing scenario, or behavioral correction is discovered **after implementation**, this extension provides a focused micro-cycle that cascades the change through spec, tests, and code — without re-running the full pipeline.

## Installation

```bash
specify extension add --dev extensions/amend/
```

## Commands

### `/speckit.amend <description>`

Alias: `/speckit.amend.amend`

Apply a targeted amendment to a feature that has completed the full spec-kit cycle.

**Examples**:

```
/speckit.amend "empty string IDs should be treated as null"
/speckit.amend "rate limit should return 429 not 400 when quota exceeded"
/speckit.amend "user with expired token should be redirected to login, not shown 500"
```

## Workflow

```
/speckit.specify  →  Initial feature creation
/speckit.clarify  →  Pre-implementation refinement
/speckit.plan     →  Technical planning
/speckit.tasks    →  Task generation
/speckit.implement → Execution
/speckit.amend    →  Post-implementation amendments  ← this extension
/speckit.analyze  →  Consistency verification
```

The amendment micro-cycle:

```
/speckit.amend "<description>"
    │
    ├── Phase 1: Load context (spec, plan, tasks)
    ├── Phase 2: Update spec.md (clarification + acceptance scenario + edge case)
    ├── Phase 3: Locate affected test and implementation files
    ├── Phase 4: Add failing test (RED)
    ├── Phase 5: Make targeted code change (GREEN)
    └── Phase 6: Update tasks.md traceability
```

## When to Use vs. Alternatives

| Scenario | Command |
|----------|---------|
| Post-implementation edge case | `/speckit.amend` |
| Pre-implementation change | `/speckit.clarify` |
| Large scope change | `/speckit.specify` (new feature) |
| Verify consistency | `/speckit.analyze` |

## Design Principles

- **Spec is always first**: Never modifies tests or code before updating spec.md
- **Minimal blast radius**: Only touches files directly affected by the amendment
- **Test before implement**: Follows RED → GREEN cycle for the new scenario
- **One amendment per invocation**: Keeps changes focused and reviewable
- **User confirmation**: Presents an impact map before making changes
- **Fail-safe**: Halts cleanly if any phase encounters an error

## Requirements

- spec-kit `>=0.1.0`
- A project that has completed `/speckit.implement` (tasks.md with at least one completed task)
