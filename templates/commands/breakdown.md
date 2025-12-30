---
description: Create detailed task implementation plans phase-by-phase with user confirmation between phases to avoid lazy execution
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

### Phase 1: Context Loading and Progression Detection

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

2. **Load required context documents**:
   - **REQUIRED**: Read tasks.md for complete task list and structure
   - **REQUIRED**: Read plan.md for tech stack and architecture
   - **IF EXISTS**: Read spec.md for feature requirements
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read constitution.md for project principles
   - **IF EXISTS**: Scan contracts/ directory for API specifications
   - **IF EXISTS**: Read research.md for technical decisions

2b. **Check for specialized agents**:
   - Check if .claude/agents/speckit/researcher.md exists
   - Check if .claude/agents/speckit/planner.md exists
   - Store availability for later use (will determine which subagent_type to use)

3. **Analyze tasks.md progression**:
   - Parse all phases and their tasks
   - Identify completed tasks (marked with [X] or [x])
   - Identify incomplete tasks (marked with [ ])
   - Determine current phase: **first phase with incomplete tasks**
   - Extract task count per phase (completed / total)

4. **Scan for existing implementation results**:
   - Check if task-plans/ directory exists
   - Look for existing task plan files (T###-*.md)
   - Check if task-results/ directory exists
   - Look for task result files (T###-result.md) from previous implement runs
   - Build list of available context from completed tasks
   - **Use result files**: Extract gotchas discovered, patterns that worked/failed, deviations from plans - pass to planner agent as lessons learned

5. **Display progression status**:
   ```
   📊 Feature Progress: {feature-name}

   Phase 1: Setup - ✅ Complete (3/3 tasks)
   Phase 2: Foundational - 🔄 In Progress (5/47 tasks)  ← CURRENT PHASE
   Phase 3: User Story 1 - ⏳ Pending (0/4 tasks)
   ...

   Current Phase: Phase 2 - Foundational
   Remaining Tasks: 42
   ```

6. **Ask user for confirmation**:
   - Show: "Ready to create detailed plans for **Phase {N}: {Phase Name}** ({count} incomplete tasks)"
   - Options:
     - "yes" or "continue" → proceed with current phase
     - "next" → skip to next incomplete phase
     - "all" → process all remaining phases
     - "phase {N}" → jump to specific phase
   - **STOP and wait for user response**

### Phase 2: Research Phase (Only After User Confirmation)

This phase runs **ONLY** after user confirms which phase to process.

7. **Launch researcher agent for codebase analysis**:

   Use Task tool with:
   - If .claude/agents/speckit/researcher.md exists: subagent_type="researcher"
   - Otherwise: subagent_type="Explore" with thoroughness="medium"

   Prompt:

   ```
   You are the researcher agent for SpecKit breakdown.

   Task: Analyze the codebase to identify implementation patterns and best practices for {Phase Name}.

   Context:
   - Feature: {feature-name}
   - Phase: {phase-name}
   - Tasks to plan: {list of task IDs and descriptions}
   - Tech stack: {from plan.md}

   Your goals:
   1. Find existing code patterns relevant to these tasks
   2. Identify framework-specific best practices (be agnostic - discover patterns)
   3. Locate reference implementations in the codebase
   4. Find similar features or components already implemented
   5. Note any gotchas or special considerations from constitution.md

   Search strategies:
   - Use Glob to find files matching patterns from task descriptions
   - Use Grep to search for similar implementations
   - Read key files that show architectural patterns
   - Check .repomix/ files if they exist for reference patterns

   Deliverable: Return a structured research report with:
   - Existing patterns found (with file:line references)
   - Framework best practices discovered
   - Code snippets to reuse/adapt
   - Gotchas and special considerations
   - Dependencies and imports needed
   ```

8. **Wait for researcher agent to complete**: Store research findings for use in planning.

### Phase 3: Group-Based Task Planning (Optimized)

This phase plans tasks **by logical groups** for efficiency (fewer agent calls, less tokens).

9. **Prepare tasks for planning**:

   a. **Collect incomplete tasks**:
      - Filter tasks without existing plans (no task-plans/T{number}-*.md)
      - Log skipped tasks: "⏭️  T{number}: Plan already exists, skipping"

   b. **Group tasks by topic** (priority order):
      1. **By User Story**: Group [US1], [US2], etc. tasks together
      2. **By domain/topic**: Detect from task descriptions:
         - "model", "entity", "schema" → Data Models group
         - "api", "endpoint", "route" → API group
         - "component", "page", "view", "ui" → Frontend group
         - "service", "repository" → Backend Services group
         - "test", "spec" → Testing group
         - "config", "setup" → Configuration group
      3. **By target directory**: Group tasks targeting same folder
      4. **Ungrouped**: Tasks that don't fit above categories

   c. **Display grouping**:
      ```
      📦 Task Groups for Phase {N}:

      Group 1: Data Models (5 tasks)
        T004, T005, T006, T007, T008

      Group 2: API Endpoints (8 tasks)
        T009, T010, T011, T012, T013, T014, T015, T016

      Group 3: Frontend Components (4 tasks)
        T017, T018, T019, T020

      Group 4: Other (2 tasks)
        T021, T022
      ```

   d. **Load shared context for phase**:
      - Check for previous task results (task-results/*.md)
      - Extract lessons learned, gotchas, patterns that worked/failed
      - This context will be passed to ALL groups

10. **For each task group** (sequential groups, but all tasks in group planned together):

    a. **Launch planner agent for entire group**:

       Use Task tool with:
       - If .claude/agents/speckit/planner.md exists: subagent_type="planner"
       - Otherwise: subagent_type="general-purpose"

       Prompt:

       ```
       You are the planner agent for SpecKit breakdown.

       Task: Create implementation plans for ALL tasks in this group.

       Group: {group_name} ({count} tasks)
       Phase: {phase_name}

       Tasks to plan:
       {for each task in group:}
       - T{number}: {description} [P={yes/no}] [Story={US# or N/A}]
       {end for}

       Context Available:
       - Research findings: {summary from researcher agent}
       - Previous task results: {lessons learned from task-results/*.md}
       - Tech stack: {from plan.md}
       - Data model: {from data-model.md if relevant}
       - Contracts: {from contracts/ if relevant}

       CRITICAL: Generate a plan for EACH task. Separate plans with exactly this line:
       ---TASK_SEPARATOR---

       For EACH task, use this structure:

       # Task Plan: T{number}

       ## Task Description
       {full task description}
       **Phase**: {phase}
       **User Story**: {US# or N/A}
       **Parallel**: {Yes/No}

       ---

       ## Codebase Impact Analysis

       ### Files to Create
       - `{path}` - {purpose}

       ### Files to Modify
       - `{path}:{line}` - {what changes}

       ### Dependencies
       - **Imports**: {list}
       - **Services**: {list}
       - **Data Models**: {list}

       ---

       ## Implementation Approach

       ### Existing Patterns to Follow
       **Reference**: `{file:line}`
       **Why**: {explanation}

       ### Implementation Steps
       1. {step}
       2. {step}
       3. {step}

       ### Gotchas
       - {gotcha}

       ---

       ## Related Tasks
       **Depends On**: T{numbers}
       **Blocks**: T{numbers}
       **Can Run In Parallel With**: T{numbers}

       ---

       ## Estimated Complexity
       **Complexity**: {Simple/Moderate/Complex}
       **Estimated Time**: {5min/15min/30min/1h/2h}
       **Risk Level**: {Low/Medium/High}

       ---TASK_SEPARATOR---

       Deliverable: Return ALL task plans separated by ---TASK_SEPARATOR---
       ```

    b. **Parse and write individual plan files**:
       - Split agent response by "---TASK_SEPARATOR---"
       - For each task plan section:
         * Extract task ID from "# Task Plan: T{number}"
         * Sanitize description for filename (lowercase, hyphens, max 50 chars)
         * Create task-plans/ directory if needed
         * Write to `task-plans/T{number}-{sanitized-description}.md`
         * Log: "✅ T{number}: Plan created"

    c. **Update tasks.md with plan references**:
       - For each planned task, append: `[📋 Plan](task-plans/T{number}-{filename}.md)`
       - Example: `- [ ] T004 [P] Create JobType enum... [📋 Plan](task-plans/T004-create-jobtype-enum.md)`

    d. **Group completion log**:
       - Show: "✅ Group '{group_name}': {count} plans created"

11. **Phase completion**:
    - After all tasks in current phase are planned
    - Show summary: "✅ Phase {N} breakdown complete: {count} task plans created"
    - List all plan files created in this phase

11. **Ask about next phase**:
    - Check if there are more phases with incomplete tasks
    - If yes: Show "Phase {N} complete. Continue with Phase {N+1}: {Name}? (yes/no/summary)"
    - If no: Show "All phases complete! Generating final summary..."
    - **STOP and wait for user response**
    - If "yes", go back to Phase 1 step 7 for next incomplete phase
    - If "no" or "summary", proceed to Phase 4

### Phase 4: Final Summary

12. **Generate comprehensive summary**:
    ```
    🎯 SpecKit Breakdown Summary

    Feature: {feature-name}

    ## Phases Processed

    Phase 2: Foundational
    - Tasks planned: 42/47
    - Complexity breakdown:
      * Simple: 15 tasks (~1-2 hours)
      * Moderate: 20 tasks (~4-6 hours)
      * Complex: 7 tasks (~3-5 hours)
    - Files to create: 25
    - Files to modify: 12

    Phase 3: User Story 1
    - Tasks planned: 4/4
    - Complexity breakdown:
      * Simple: 2 tasks (~30 minutes)
      * Moderate: 2 tasks (~1 hour)
    - Files to create: 2
    - Files to modify: 3

    ## Overall Statistics

    - Total task plans created: 46
    - Estimated implementation time: 8-13 hours
    - Key dependencies identified: 12
    - Critical path tasks: T004, T018, T029, T036
    - Phases remaining: 6 (Phase 4-9)

    ## Next Steps

    1. Review task plans in task-plans/ directory
    2. Run /speckit.implement to execute implementation
    3. Plans will guide implementation with exact steps and references

    ## Key Patterns Discovered

    - {pattern 1 from research}
    - {pattern 2 from research}
    - {pattern 3 from research}

    ## Gotchas to Watch

    - {gotcha 1 from multiple plans}
    - {gotcha 2 from constitution}
    ```

## Operating Principles

### Progressive Execution

- **Phase-by-phase**: Work on current phase only, not all phases at once
- **Group-based planning**: Plan tasks in logical groups (by topic, user story, or domain)
- **Batch updates**: Update tasks.md after each group is planned
- **Context-aware**: Use results from previous tasks to inform current plans
- **Efficient token usage**: One agent call per group instead of per task

### Framework Agnosticism

- **Never assume**: Don't hardcode Scala, React, or any framework patterns
- **Always discover**: Use researcher agent to find actual patterns in codebase
- **Use what exists**: Base plans on existing code, not assumptions
- **Adapt to context**: Plans should reflect actual project architecture

### Agent Coordination

- **Researcher for discovery**: Use general-purpose agent with researcher prompt for codebase analysis
- **Planner for creation**: Use general-purpose agent with planner prompt for plan generation
- **Group execution**: Run researcher once per phase, planner once per task group
- **Context passing**: Pass research findings to planner for informed planning

### Quality Standards

- **Actionable plans**: Every plan must have exact steps, file paths, and code snippets
- **Complete references**: Include file:line for all patterns and snippets
- **Use previous results**: Check *-result.md files to learn from actual implementation
- **Prevent duplication**: Skip tasks that already have plans
- **Track dependencies**: Map task relationships accurately

## Error Handling

- **No tasks.md**: Error and suggest running `/speckit.tasks` first
- **No incomplete tasks**: Inform user all tasks are already planned
- **Agent failure**: Log error, skip group, continue with next group
- **Parse failure**: If ---TASK_SEPARATOR--- parsing fails, attempt to extract plans by # Task Plan: headers
- **File write error**: Report error, suggest manual creation
- **User cancellation**: Save progress, generate summary of work done so far

## Important Notes

- **NEVER process all phases at once** - work on current phase only
- **GROUP tasks by topic** - plan related tasks together for coherence and efficiency
- **UPDATE tasks.md after each group** - not after each individual task
- **USE result files** - learn from previous implementations
- **BE AGNOSTIC** - discover patterns, don't assume frameworks
- **USE AGENTS** - researcher for analysis, planner for groups
- **FOCUS ON CURRENT PHASE** - don't try to plan everything upfront
- **PARSE carefully** - split agent response by ---TASK_SEPARATOR--- to extract individual plans

## Context

$ARGUMENTS
