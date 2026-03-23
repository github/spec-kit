---
description: Show current progress, what's next, and overall project state.
---

## User Input

```text
$ARGUMENTS
```

You are providing a **quick status update** on where things stand. This is the "dashboard view" of the MiniSpec workflow.

## Philosophy

Engineers should be able to:

- Quickly understand where they are in the process
- See what's done and what's remaining
- Know the next action to take
- Get context after stepping away

Keep it concise but complete.

## Execution Flow

### Phase 1: Gather State

Read current state from:

1. **Constitution** (`.minispec/memory/constitution.md`)
   - Project name
   - MiniSpec preferences

2. **Active features** (`specs/*/`)
   - Which features are in progress
   - Status of each (designed/planned/implementing/complete)

3. **Current feature details** (if one is active)
   - Design status
   - Task progress
   - Recent activity

4. **Knowledge base** (`.minispec/knowledge/`)
   - Number of decisions
   - Last updates

### Phase 2: Determine Context

Figure out what to show based on state:

**No features yet:**
> Project is set up but no features started

**Feature in design:**
> Currently designing [feature], not yet planned

**Feature planned, not started:**
> [Feature] is planned with [N] tasks, ready to implement

**Feature in progress:**
> Implementing [feature], [N]/[M] tasks complete

**Feature complete:**
> [Feature] complete, no active work

### Phase 3: Display Status

#### Compact Status (Default)

```text
📍 MiniSpec Status

Project: [Project Name]
Active Feature: [Feature Name] (or "None")
Phase: [Design | Planning | Implementation | Idle]

Progress: [N]/[M] tasks ([%]%)
████████░░░░

Next: [Description of next action]
     Run: /minispec.[command]

Last activity: [Time ago] - [What was done]
```

#### Detailed Status (if requested or complex state)

```text
📍 MiniSpec Status: [Project Name]

═══════════════════════════════════════════

CURRENT FEATURE: [Feature Name]
Status: [Designing | Planned | Implementing | Complete]

┌─ Design ─────────────────────────────────
│ ✅ Complete
│ Decisions: 3 documented
│ Components: 4 defined
└──────────────────────────────────────────

┌─ Tasks ──────────────────────────────────
│ Total: 8 tasks (~320 lines)
│ Complete: 3 ✅
│ In Progress: 1 🔄
│ Remaining: 4 ⏳
│
│ Progress: ████████░░░░░░░░ 37%
│
│ Current: Task 4 - Auth middleware
│ Next: Task 5 - Protected routes
└──────────────────────────────────────────

┌─ Recent Activity ────────────────────────
│ 2h ago: Completed Task 3 (Login endpoint)
│ 3h ago: Completed Task 2 (User model)
│ Yesterday: Design approved
└──────────────────────────────────────────

KNOWLEDGE BASE
├─ Decisions: 5 (2 new this feature)
├─ Patterns: 3
├─ Modules: 2
└─ Last validated: [Date]

NEXT ACTION
→ Continue implementation: /minispec.next
  Task 4: Auth middleware (~50 lines)

═══════════════════════════════════════════
```

### Phase 4: Contextual Suggestions

Based on state, suggest next action:

**If no constitution:**
> "Project not set up yet. Run `/minispec.constitution` to get started."

**If constitution but no features:**
> "Ready to start! Run `/minispec.design [feature]` to design your first feature."

**If feature designed, no tasks:**
> "Design complete. Run `/minispec.tasks` to break it into implementable chunks."

**If tasks created, not validated:**
> "Tasks ready. Run `/minispec.analyze` to validate before implementing."

**If ready to implement:**
> "Ready to implement. Run `/minispec.next` to start Task [N]."

**If mid-implementation:**
> "Continue with `/minispec.next` for Task [N]: [Name]"

**If feature complete:**
> "Feature complete! Start a new feature with `/minispec.design`."

**If docs might be stale:**
> "It's been a while since docs were validated. Consider `/minispec.validate-docs`."

## Additional Status Views

### Feature-Specific (with argument)

If `$ARGUMENTS` contains a feature name:

> "Status for **[Feature Name]**:
>
> Phase: [Current phase]
> Tasks: [N]/[M] complete
> Decisions: [N]
> Last activity: [Time/action]
>
> [Details specific to that feature]"

### All Features Overview

If `$ARGUMENTS` is "all" or "features":

```text
All Features

| Feature | Status | Progress | Last Activity |
|---------|--------|----------|---------------|
| auth | Implementing | 3/8 (37%) | 2h ago |
| payments | Designed | 0/0 | 3d ago |
| dashboard | Complete | 12/12 | 1w ago |
```

### Knowledge Base Status

If `$ARGUMENTS` is "docs" or "knowledge":

```text
Knowledge Base Status

Decisions: 8 total
├─ Active: 6
├─ Superseded: 2
└─ Last added: 001-jwt-auth (2d ago)

Patterns: 4 documented
└─ Last updated: api-response (1d ago)

Modules: 3 documented
├─ auth ✅ current
├─ payments ⚠️ needs update
└─ core ✅ current

Architecture.md: Updated 3d ago
Conventions.md: Updated 1w ago

Validation: Last run 2d ago, no issues
```

## Handling Edge Cases

### Multiple Active Features

If working on multiple features:

> "You have multiple features in progress:
>
> 1. **auth** - Implementing (3/8 tasks)
> 2. **notifications** - Designed, not started
>
> Which would you like to focus on?
>
> - `/minispec.next` continues with auth
> - `/minispec.status notifications` shows notification details"

### Stale/Abandoned Work

If a feature has been inactive:

> "Feature **[name]** hasn't had activity in [N] days.
>
> Status: [X]/[Y] tasks complete
>
> Options:
>
> - Continue: `/minispec.next`
> - Review state: `/minispec.walkthrough [feature]`
> - Archive: Mark as paused and start something new"

### Git State

Optionally include git context:

> "Git: On branch `feature/auth`, 3 commits ahead of main
> Last commit: 2h ago - 'Add login endpoint'"

## Important Guidelines

- **Be quick**: This should be glanceable
- **Be accurate**: Don't guess—read actual state
- **Be actionable**: Always suggest next step
- **Be helpful**: If something seems off, mention it
- **Respect context**: Detailed when needed, brief when not

## Output

This command is **read-only**. It only displays information and suggests actions—it doesn't modify any files.
