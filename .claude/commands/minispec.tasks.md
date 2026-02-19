---
description: Interactively break down a design into reviewable implementation chunks sized for pair programming.
---

## User Input

```text
$ARGUMENTS
```

You are helping break down a design into **implementable tasks** through conversation. Tasks should be sized according to the engineer's review chunk preference from the constitution.

## Philosophy

Task breakdown is not just about creating a list—it's about:

- Understanding the implementation sequence
- Identifying dependencies and parallelization opportunities
- Sizing chunks for comfortable review
- Ensuring the engineer understands what each task involves

## Prerequisites

Before starting, verify:

1. **Constitution exists** at `.minispec.minispec/memory/constitution.md`
   - Read the `Review Chunk Size` preference (small/medium/large/adaptive)
   - This determines target lines per task

2. **Design exists** - Look for:
   - `.minispec/specs/[feature-name]/design.md`
   - If `$ARGUMENTS` specifies a feature, use that
   - If not, check for recent designs or ask which feature

If no design exists:
> "I don't see a design for this feature yet. Want to run `/minispec.design` first, or give me a quick overview of what we're building?"

## Chunk Size Guidelines

Based on constitution preference:

| Preference | Target Lines | Typical Scope |
| --- | --- | --- |
| Small | 20-40 lines | Single function, one test |
| Medium | 40-80 lines | Related functions, model + migration |
| Large | 80-150 lines | Full component, endpoint + tests |
| Adaptive | Varies | AI suggests based on complexity |

## Execution Flow

### Phase 1: Load Context

1. **Read the design document**:
   - Understand components, data model, API
   - Note any open questions or deferred decisions

2. **Read related decisions** from `.minispec/knowledge/decisions/`

3. **Check existing codebase**:
   - How are similar features structured?
   - What's the typical test-to-implementation ratio?
   - Are there shared utilities to leverage?

4. **Acknowledge the starting point**:
   > "I've read the design for [feature]. You've got [N] components to build:
   > - [Component 1]
   > - [Component 2]
   > - ...
   >
   > Your chunk size preference is [size] (~[N] lines per task).
   > Let me propose a breakdown."

### Phase 2: Propose Task Breakdown

Present an initial breakdown organized by implementation phase:

```text
## Proposed Task Breakdown

### Foundation (do first)
These tasks set up the base that other tasks depend on.

1. **[Task name]** (~[N] lines)
   - [What it creates/changes]
   - Files: `path/to/file.ts`

2. **[Task name]** (~[N] lines)
   - [What it creates/changes]
   - Files: `path/to/file.ts`

### Core Implementation
These can potentially run in parallel (marked with [P]).

3. **[Task name]** (~[N] lines) [P]
   - [What it creates/changes]
   - Files: `path/to/file.ts`

4. **[Task name]** (~[N] lines) [P]
   - [What it creates/changes]
   - Files: `path/to/file.ts`

5. **[Task name]** (~[N] lines)
   - Depends on: Task 3, 4
   - [What it creates/changes]
   - Files: `path/to/file.ts`

### Integration & Polish
Final tasks that bring everything together.

6. **[Task name]** (~[N] lines)
   - [What it creates/changes]
   - Files: `path/to/file.ts`

---

Total: [N] tasks, estimated ~[N] lines of code

What would you like to adjust?
```

### Phase 3: Collaborative Refinement

Invite feedback and adjust:

**If they want to combine tasks:**
> "Sure, I can combine [Task A] and [Task B]. That brings it to ~[N] lines—still comfortable for review?"

**If they want to split tasks:**
> "Good idea. I'll split [Task] into:
>
> - [Task A]: [scope] (~[N] lines)
> - [Task B]: [scope] (~[N] lines)"

**If they question the order:**
> "You're right, [Task B] could come before [Task A] because [reason]. Want me to reorder?"

**If they want to defer something:**
> "Okay, I'll mark [Task] as 'future' and remove it from this implementation. We can pick it up later."

**If a task seems too vague:**
> "Let me be more specific about [Task]. It would involve:
>
> 1. [Step 1]
> 2. [Step 2]
> 3. [Step 3]
>
> Does that clarify it?"

### Phase 4: Identify Dependencies and Parallel Opportunities

Make dependencies explicit:

> "Looking at the tasks:
>
> **Parallel groups:**
>
> - Tasks 3, 4 can run simultaneously (no shared dependencies)
> - Tasks 6, 7 can run simultaneously
>
> **Sequential requirements:**
>
> - Task 5 needs Tasks 3, 4 complete first
> - Task 8 needs everything else done
>
> This means you could batch 'next 2' for the parallel groups if you're comfortable. Make sense?"

### Phase 5: Testing Strategy

Discuss how testing fits in:

> "For testing, I suggest:
>
> - Tasks 1-2 (foundation): Include unit tests in the same task
> - Tasks 3-5 (core): Tests bundled with implementation
> - Task 6: Dedicated integration test task
>
> Or would you prefer separate test tasks? Some engineers like to review tests separately."

Adjust based on their preference.

### Phase 6: Finalize and Save

Once agreed:

1. **Confirm the final list**:
   > "Final task breakdown:
   >
   > 1. [Task] (~N lines)
   > 2. [Task] (~N lines)
   > ...
   >
   > [N] tasks total. Ready to save?"

2. **Write tasks to file** at `.minispec/specs/[feature-name]/tasks.md`:

```markdown
---
feature: [feature-name]
status: planned
created: [YYYY-MM-DD]
chunk_size: [small|medium|large|adaptive]
total_tasks: [N]
estimated_lines: [N]
---

# [Feature Name] Tasks

## Overview
[Brief description of what this task list implements]

## Task List

### Foundation

#### Task 1: [Task Name]
- **Estimate:** ~[N] lines
- **Files:** `path/to/file.ts`
- **Description:** [What this task accomplishes]
- **Depends on:** None
- **Acceptance:** [How to verify it's done]

#### Task 2: [Task Name]
- **Estimate:** ~[N] lines
- **Files:** `path/to/file.ts`, `path/to/other.ts`
- **Description:** [What this task accomplishes]
- **Depends on:** Task 1
- **Acceptance:** [How to verify it's done]

### Core Implementation

#### Task 3: [Task Name] [P]
- **Estimate:** ~[N] lines
- **Parallel:** Can run with Task 4
- **Files:** `path/to/file.ts`
- **Description:** [What this task accomplishes]
- **Depends on:** Task 2
- **Acceptance:** [How to verify it's done]

[... continue for all tasks ...]

## Notes
- [Any implementation notes or gotchas discussed]
- [Deferred items for future work]

## Progress
- [ ] Task 1: [Task Name]
- [ ] Task 2: [Task Name]
- [ ] Task 3: [Task Name]
[... checklist for tracking ...]
```

1. **Update design status**:
   - Change design.md status from `designed` to `planned`

### Phase 7: Handoff

> "Tasks saved to `.minispec/specs/[feature-name]/tasks.md`
>
> **Summary:**
>
> - [N] tasks total
> - ~[N] estimated lines
> - [N] parallel opportunities
>
> **Next steps:**
>
> - `/minispec.analyze` - Validate design-task alignment
> - `/minispec.next` - Start implementing
>
> Ready when you are."

## Important Guidelines

- **Size matters**: Tasks too big = review fatigue; too small = overhead. Respect preferences.
- **Dependencies are critical**: Getting the order wrong wastes time
- **Parallel opportunities save time**: Identify where the engineer can batch
- **Tests aren't optional**: Include them in task estimates
- **Be specific about files**: Engineers should know exactly what's changing
- **Acceptance criteria**: Each task should have a clear "done" state

## Handling Edge Cases

**Design has open questions:**
> "The design has some open questions about [X]. Should we:
> a) Resolve them now before creating tasks
> b) Create a 'spike' task to investigate
> c) Make an assumption and note it"

**Feature is too large:**
> "This feature might be [N]+ tasks. Consider splitting into phases:
>
> - Phase 1: [Core functionality]
> - Phase 2: [Enhanced features]
> - Phase 3: [Polish and edge cases]
>
> Want to scope Phase 1 first?"

**Unclear complexity:**
> "I'm not sure how complex [component] will be. Want me to:
> a) Estimate conservatively (might be smaller tasks than needed)
> b) Create a spike task to investigate first
> c) Start with one task and split during implementation if needed"

## Output Artifacts

By the end of this command, you will have created/updated:

1. `.minispec/specs/[feature-name]/tasks.md` - The task breakdown
2. `.minispec/specs/[feature-name]/design.md` - Status updated to `planned`
