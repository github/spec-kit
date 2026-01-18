# Contract: Ralph Iteration Prompt Template

**Feature**: 001-ralph-loop-implement  
**Date**: 2026-01-18  
**Updated**: 2026-01-18 (User story scope + commit boundaries)

## Overview

This document specifies the **iteration prompt** passed via `-p` flag to the Copilot CLI on each ralph loop iteration. This prompt works **in conjunction with** the `speckit.implement` agent profile, providing iteration-specific context and constraints.

The key design principle: **one user story per iteration maximum** to prevent context rot and maintain clean git history.

## Template Location

`templates/ralph-prompt.md`

## Placeholders

| Placeholder | Source | Example Value |
|-------------|--------|---------------|
| `{FEATURE_NAME}` | Branch name | `001-ralph-loop-implement` |
| `{SPEC_PATH}` | Spec file path | `specs/001-ralph-loop-implement/spec.md` |
| `{PLAN_PATH}` | Plan file path | `specs/001-ralph-loop-implement/plan.md` |
| `{TASKS_PATH}` | Tasks file path | `specs/001-ralph-loop-implement/tasks.md` |
| `{PROGRESS_PATH}` | Progress file path | `specs/001-ralph-loop-implement/progress.txt` |
| `{ITERATION_NUMBER}` | Current iteration | `3` |
| `{MAX_ITERATIONS}` | Configured limit | `10` |

## Template Content

```markdown
# Ralph Iteration {ITERATION_NUMBER}

Feature: {FEATURE_NAME} | Iteration {ITERATION_NUMBER} of {MAX_ITERATIONS}

## Scope Constraint

⚠️ **CRITICAL**: Complete AT MOST ONE user story in this iteration.

- If you cannot complete an entire user story, complete as many tasks as you can
- Partial progress is fine—uncompleted tasks will be handled in subsequent iterations  
- DO NOT start a second user story even if you have time remaining
- This prevents context rot and keeps changes reviewable

## Your Workflow

1. **Read context first**:
   - Read `{PROGRESS_PATH}` — check the `## Codebase Patterns` section for discovered conventions
   - Read `{TASKS_PATH}` — understand task structure and identify next incomplete user story

2. **Identify scope**:
   - Find the FIRST user story section with incomplete tasks (`- [ ]`)
   - Work ONLY on tasks within that single user story
   - Example: If "US-001: Initialize Ralph Command" has incomplete tasks, work only on US-001

3. **Implement tasks**:
   - Complete tasks in dependency order (non-[P] before parallel [P] where noted)
   - Run quality checks after each task (typecheck, lint, test as appropriate)
   - Mark each completed task by changing `[ ]` to `[x]` in `{TASKS_PATH}`

4. **Commit on user story completion**:
   - When ALL tasks in the current user story are complete (`[x]`), create a commit:
     ```
     git add -A
     git commit -m "feat({FEATURE_NAME}): <user story title>"
     ```
   - Example: `git commit -m "feat(001-ralph-loop-implement): US-001 Initialize Ralph Command"`

5. **Update progress log**:
   - Append your iteration summary to `{PROGRESS_PATH}` (format below)
   - Add any discovered patterns to `## Codebase Patterns` section at TOP of file

## Progress Report Format

APPEND to {PROGRESS_PATH}:

---
## Iteration {ITERATION_NUMBER} - [Current Date/Time]
**User Story**: [US-XXX title or "Partial progress on US-XXX"]
**Tasks Completed**: 
- [x] Task ID: description
- [x] Task ID: description
**Tasks Remaining in Story**: [count] or "None - story complete"
**Commit**: [commit hash if story completed, or "No commit - partial progress"]
**Files Changed**: 
- path/to/file.ext
**Learnings**:
- [patterns discovered, gotchas, useful context for future iterations]
---

## Stop Conditions

**If ALL tasks in {TASKS_PATH} are complete** (`[x]`), output exactly:
```
<promise>COMPLETE</promise>
```

**If tasks remain**, end your response normally. The next iteration will continue.

## Quality Gates

- ALL changes must pass quality checks before marking tasks complete
- DO NOT commit broken code
- Follow existing code patterns (check Codebase Patterns in progress file)
- Reference `{PLAN_PATH}` for architecture decisions

## Reference Files

- Specification: `{SPEC_PATH}`
- Implementation Plan: `{PLAN_PATH}`  
- Constitution: `.specify/memory/constitution.md`
```

## Validation Requirements

### Prompt Must Include

1. ✅ User story scope limit (one max per iteration)
2. ✅ Instruction to read progress file first (Codebase Patterns)
3. ✅ Instruction to update tasks.md checkboxes
4. ✅ **Commit instruction** after completing a user story
5. ✅ Progress report format with user story context
6. ✅ `<promise>COMPLETE</promise>` stop condition
7. ✅ Iteration context (current/max)
8. ✅ Quality gate reminder
9. ✅ Reference to spec, plan, and constitution files

### Prompt Must NOT Include

1. ❌ Implementation details of the ralph loop itself
2. ❌ Instructions to work on multiple user stories
3. ❌ Instructions to modify the loop or prompt
4. ❌ Credentials or sensitive information
5. ❌ Specific task assignments (agent determines from tasks.md)

## Agent Behavior Contract

### Expected Inputs

- Prompt via `-p` flag (from orchestration script)
- Agent context via `--agent speckit.implement`
- Access to repository files (spec, tasks, progress)
- Git repository context with write access

### Expected Outputs

- Code changes implementing tasks within ONE user story
- Updated `tasks.md` with checkboxes marked complete
- **Git commit** when user story is complete (with conventional commit message)
- Appended entry to `progress.txt`
- `<promise>COMPLETE</promise>` token if ALL tasks done

### Commit Message Format

```
feat({FEATURE_NAME}): {USER_STORY_ID} {User Story Title}
```

Examples:
- `feat(001-ralph-loop-implement): US-001 Initialize Ralph Command`
- `feat(001-ralph-loop-implement): US-002 Loop Orchestration`

### Error Conditions

| Condition | Expected Agent Behavior |
|-----------|------------------------|
| User story unclear | Ask for clarification in progress entry, mark tasks as blocked |
| Tests fail | Report failure, do not mark task complete, no commit |
| Cannot complete story | Report partial progress, commit only if all completed tasks form coherent unit |
| All tasks done | Commit final story, output `<promise>COMPLETE</promise>` |

## Interaction with speckit.implement Agent

The iteration prompt **supplements** the `speckit.implement` agent profile:

| Aspect | speckit.implement Agent | Ralph Iteration Prompt |
|--------|------------------------|------------------------|
| **Workflow** | Full SDD implementation workflow, phase execution, TDD | Iteration-specific scope constraints |
| **Scope** | Any number of tasks/stories | ONE user story maximum |
| **Commits** | No commit instructions | Commit after each user story |
| **Progress** | General task completion | Iteration log with learnings |
| **Context** | Project structure, ignore files, tech stack | Feature paths, iteration count |

The agent profile provides the "how to implement" while the iteration prompt provides the "what and when to commit".

## Example CLI Invocation

```powershell
$prompt = Get-Content "templates/ralph-prompt.md" -Raw
$prompt = $prompt -replace '{FEATURE_NAME}', '001-ralph-loop-implement'
$prompt = $prompt -replace '{ITERATION_NUMBER}', '3'
# ... other replacements ...

copilot --agent speckit.implement -p $prompt --model claude-sonnet-4.5 --allow-all-tools -s
```

## Example Generated Prompt

```markdown
# Ralph Iteration 3

Feature: 001-ralph-loop-implement | Iteration 3 of 10

## Scope Constraint

⚠️ **CRITICAL**: Complete AT MOST ONE user story in this iteration.

- If you cannot complete an entire user story, complete as many tasks as you can
- Partial progress is fine—uncompleted tasks will be handled in subsequent iterations  
- DO NOT start a second user story even if you have time remaining
- This prevents context rot and keeps changes reviewable

## Your Workflow

1. **Read context first**:
   - Read `specs/001-ralph-loop-implement/progress.txt` — check the `## Codebase Patterns` section
   - Read `specs/001-ralph-loop-implement/tasks.md` — identify next incomplete user story

2. **Identify scope**:
   - Find the FIRST user story section with incomplete tasks (`- [ ]`)
   - Work ONLY on tasks within that single user story

[... rest of template with placeholders filled ...]
```
