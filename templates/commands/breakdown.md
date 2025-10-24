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

### Phase 3: Incremental Task Planning (Sequential Processing)

This phase processes tasks **ONE AT A TIME** with immediate tasks.md updates.

9. **For each incomplete task in current phase** (sequential, not parallel):

   a. **Load task context**:
      - Extract task ID (e.g., T004)
      - Extract task description
      - Extract phase and user story
      - Extract parallel marker [P] if present
      - Extract file paths mentioned in description
      - Check if task plan already exists

   b. **Skip if plan already exists**:
      - If task-plans/T{number}-*.md exists, skip to next task
      - Log: "⏭️  T{number}: Plan already exists, skipping"

   c. **Check for previous task results**:
      - Look for result files: T{number-1}-result.md, dependency task results
      - If found, read and extract:
        * What was actually implemented (vs what was planned)
        * Deviations from original plan and reasons
        * New files created/modified
        * Gotchas discovered during implementation
        * Lessons learned (patterns that work/don't work, approaches that succeed/fail)
        * TODOs left for current or future tasks
      - Pass this context to planner agent as "lessons from previous implementations" to create better, more accurate plans

   d. **Launch planner agent for this specific task**:

      Use Task tool with:
      - If .claude/agents/speckit/planner.md exists: subagent_type="planner"
      - Otherwise: subagent_type="general-purpose"

      Prompt:

      ```
      You are the planner agent for SpecKit breakdown.

      Task: Create a detailed implementation plan for task T{number}.

      Task Details:
      - ID: T{number}
      - Description: {task description}
      - Phase: {phase name}
      - User Story: {user story or N/A}
      - Can run in parallel: {yes/no based on [P] marker}

      Context Available:
      - Research findings: {summary from researcher agent}
      - Previous task results: {summary from T###-result.md files - actual implementations, deviations, gotchas, lessons learned}
      - Tech stack: {from plan.md}
      - Data model: {from data-model.md if relevant}
      - Contracts: {from contracts/ if relevant}

      Your goals:
      1. Analyze the codebase impact (files to create/modify)
      2. Identify exact implementation approach using research findings
      3. Provide step-by-step implementation instructions
      4. Note gotchas and special considerations
      5. Estimate complexity and time

      Use the Task Plan Template structure:

      # Task Plan: T{number}

      ## Task Description
      {full task description}
      **Phase**: {phase}
      **User Story**: {US# or N/A}
      **Parallel**: {Yes/No}

      ---

      ## Codebase Impact Analysis

      ### Files to Create
      - `{absolute/path}` - {purpose}

      ### Files to Modify
      - `{absolute/path}:{line}` - {what changes}

      ### Dependencies
      - **Imports**: {list}
      - **Services**: {list}
      - **Data Models**: {list}
      - **Contracts**: {list}

      ---

      ## Implementation Approach

      ### Existing Patterns to Follow
      **Reference Implementation**: `{file:line}` from {source}
      ```{language}
      {code snippet}
      ```
      **Why this pattern**: {explanation}

      ### Implementation Steps
      1. {specific step with file operations}
      2. {specific step with code to write}
      3. {integration points}

      ### Gotchas / Special Considerations
      - {issue from research or constitution}
      - {framework-specific requirement}
      - {performance consideration}

      ---

      ## Related Tasks
      **Depends On**: T{numbers}
      **Blocks**: T{numbers}
      **Can Run In Parallel With**: T{numbers}

      ---

      ## References
      - **Research**: {findings}
      - **Data Model**: {entities}
      - **Contract**: {files}
      - **Constitution**: {principles}
      - **Existing Code**: {patterns}

      ---

      ## Estimated Complexity
      **Complexity**: {Simple/Moderate/Complex}
      **Estimated Time**: {5min/15min/30min/1h/2h}
      **Risk Level**: {Low/Medium/High}
      **Complexity Reasoning**: {why}

      Deliverable: Return the complete task plan markdown content.
      ```

   e. **Write task plan file**:
      - Create task-plans/ directory if it doesn't exist
      - Sanitize task description for filename (lowercase, replace spaces with hyphens, max 50 chars)
      - Write plan to `task-plans/T{number}-{sanitized-description}.md`
      - Log: "✅ Created plan for T{number}: {filename}"

   f. **Update tasks.md immediately**:
      - Find the task line in tasks.md
      - Append plan reference: `[📋 Plan](task-plans/T{number}-{sanitized-description}.md)`
      - Preserve checkbox, ID, description, and any existing markers
      - Example: `- [ ] T004 [P] Create JobType enum... [📋 Plan](task-plans/T004-create-jobtype-enum.md)`

   g. **Progress checkpoint** (every 3-5 tasks):
      - After completing 3-5 task plans, pause
      - Show progress: "Created {count} task plans so far ({remaining} remaining in this phase)"
      - Ask: "Continue with next batch? (yes/no/skip to next phase)"
      - **STOP and wait for user response**
      - If "no", jump to Phase 4 (summary)
      - If "skip", jump to Phase 1 step 6 for next phase
      - If "yes", continue with next task

10. **Phase completion**:
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
- **Incremental updates**: Update tasks.md after each plan created, not in batch
- **Regular pauses**: Ask user every 3-5 tasks to prevent lazy execution
- **Context-aware**: Use results from previous tasks to inform current plans
- **Sequential tools**: Execute ONE tool at a time, wait for completion

### Framework Agnosticism

- **Never assume**: Don't hardcode Scala, React, or any framework patterns
- **Always discover**: Use researcher agent to find actual patterns in codebase
- **Use what exists**: Base plans on existing code, not assumptions
- **Adapt to context**: Plans should reflect actual project architecture

### Agent Coordination

- **Researcher for discovery**: Use general-purpose agent with researcher prompt for codebase analysis
- **Planner for creation**: Use general-purpose agent with planner prompt for plan generation
- **Sequential execution**: Run researcher once per phase, planner once per task
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
- **Agent failure**: Log error, skip task, continue with next task
- **File write error**: Report error, suggest manual creation
- **User cancellation**: Save progress, generate summary of work done so far

## Important Notes

- **NEVER process all phases at once** - work on current phase only
- **ALWAYS update tasks.md immediately** after each plan - not in batch
- **PAUSE every 3-5 tasks** - prevent lazy execution
- **USE result files** - learn from previous implementations
- **BE AGNOSTIC** - discover patterns, don't assume frameworks
- **RUN TOOLS SEQUENTIALLY** - one at a time, wait for completion
- **USE AGENTS** - researcher for analysis, planner for creation
- **FOCUS ON CURRENT PHASE** - don't try to plan everything upfront

## Context

$ARGUMENTS
