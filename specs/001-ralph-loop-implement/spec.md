# Feature Specification: Ralph Loop Implementation Support

**Feature Branch**: `001-ralph-loop-implement`  
**Created**: 2026-01-18  
**Status**: Draft  
**Input**: User description: "Add Ralph loop support to the speckit.implement phase as a CLI command that orchestrates agent CLI calls in an autonomous loop for context-controlled implementation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Ralph Loop Execution (Priority: P1)

As a developer using Spec Kit, I want to run a single CLI command that automatically implements my feature by iterating through tasks in a controlled loop, so that I can leverage autonomous AI implementation while maintaining clean context boundaries.

**Why this priority**: This is the core value proposition - enabling autonomous implementation through controlled iteration. Without this, there is no Ralph loop functionality.

**Independent Test**: Can be fully tested by running the command on a project with a completed tasks.md and observing that the agent iterates through tasks until completion or iteration limit is reached.

**Acceptance Scenarios**:

1. **Given** a project with completed spec.md, plan.md, and tasks.md in the specs folder, **When** I run the ralph loop command, **Then** the system initiates the agent CLI and begins processing the first incomplete task
2. **Given** a ralph loop is running and the current task is completed, **When** the agent marks the task as done, **Then** the system spawns a fresh agent context and proceeds to the next incomplete task
1. **Given** a ralph loop is running, **When** the agent outputs `<promise>COMPLETE</promise>` after verifying all tasks are complete, **Then** the loop terminates with a success message indicating completion
4. **Given** a ralph loop is running, **When** the maximum iteration count is reached, **Then** the loop terminates gracefully with a status report of completed vs remaining tasks

---

### User Story 2 - Progress Tracking and Learning Persistence (Priority: P2)

As a developer, I want the ralph loop to maintain a progress log across iterations so that each fresh agent context can learn from previous iterations' discoveries and avoid repeating mistakes.

**Why this priority**: Context management is what differentiates ralph loop from just running the agent repeatedly. Without progress tracking, each iteration loses valuable learnings.

**Independent Test**: Can be tested by running multiple iterations and verifying that a progress file is updated after each iteration and is readable by subsequent iterations.

**Acceptance Scenarios**:

1. **Given** a ralph loop iteration completes a task, **When** the iteration ends, **Then** the system appends a progress entry with task completed, files changed, and any learnings discovered
2. **Given** a new ralph loop iteration starts, **When** the agent begins work, **Then** the agent prompt includes instructions to read the progress file for previous context
3. **Given** multiple iterations have run, **When** I inspect the progress file, **Then** I see a chronological log of all completed work with timestamps and learnings

---

### User Story 3 - Task Status Synchronization (Priority: P2)

As a developer, I want the ralph loop to track which tasks have been completed so that iterations can pick up where previous ones left off without re-doing work.

**Why this priority**: Without task status tracking, the system cannot determine which tasks are done and which remain, making autonomous iteration impossible.

**Independent Test**: Can be tested by completing one task manually, then starting the ralph loop and verifying it picks up the next incomplete task.

**Acceptance Scenarios**:

1. **Given** a tasks.md file exists with incomplete tasks, **When** the ralph loop starts, **Then** it generates/updates a tracking file that mirrors task completion status
2. **Given** an iteration successfully completes a task, **When** the iteration ends, **Then** the tracking file is updated to mark that task as complete
3. **Given** some tasks are already marked complete, **When** a new iteration starts, **Then** it selects the highest priority incomplete task to work on

---

### User Story 4 - Configurable Iteration Limits (Priority: P3)

As a developer, I want to control the maximum number of iterations the ralph loop can execute so that I can prevent runaway execution and manage resource usage.

**Why this priority**: Safety controls are important but not critical to core functionality. A reasonable default can be hardcoded initially.

**Independent Test**: Can be tested by setting a low iteration limit and verifying the loop stops after that many iterations regardless of task completion status.

**Acceptance Scenarios**:

1. **Given** I run the ralph loop command with an iteration limit parameter, **When** that many iterations complete, **Then** the loop terminates even if tasks remain incomplete
2. **Given** I run the ralph loop command without specifying a limit, **When** the loop runs, **Then** it uses a default limit of 10 iterations
3. **Given** tasks complete before the iteration limit, **When** all tasks pass, **Then** the loop terminates early with a success message

---

### User Story 5 - Multi-Agent CLI Support (Priority: P3)

As a developer using different AI agents, I want the ralph loop to work with whichever agent CLI I have configured in my project so that I can use my preferred tool (Claude Code, Gemini, Amp, etc.).

**Why this priority**: Agent flexibility extends the feature to more users but is not required for initial MVP which can target a single agent.

**Independent Test**: Can be tested by configuring different agents and verifying the ralph loop invokes the correct CLI for each.

**Acceptance Scenarios**:

1. **Given** my project is initialized with GitHub Copilot (`--ai copilot`), **When** I run the ralph loop, **Then** it invokes the Copilot agent for each iteration
2. **Given** my project is initialized with an agent other than Copilot, **When** I run the ralph loop, **Then** it displays an error indicating only Copilot is supported in the current release
3. **Given** Copilot support is successful, **When** future releases add more agents, **Then** the architecture supports adding CLI-based agents (Claude, Gemini, Amp) without major refactoring

---

### Edge Cases

- What happens when tasks.md does not exist or is empty? → Display error message guiding user to run `/speckit.tasks` first
- What happens when an iteration fails to complete (agent crashes or times out)? → Log the failure, increment iteration count, and attempt next iteration
- What happens when there are circular dependencies in tasks? → Agent should detect and report; loop continues with next available task
- What happens when the user interrupts the loop (Ctrl+C)? → Gracefully stop, preserve progress file, report current status
- What happens when git is in a dirty state with uncommitted changes? → Warn user but allow continuation (agent will commit its changes)
- What happens when a task repeatedly fails across multiple iterations? → After 3 consecutive failures on the same task, skip to next task and log warning

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a CLI command to initiate ralph loop execution (e.g., `specify ralph` or `specify implement --ralph`)
- **FR-002**: System MUST spawn fresh agent CLI instances for each iteration to ensure clean context
- **FR-003**: System MUST maintain a progress file that persists learnings across iterations
- **FR-004**: System MUST track task completion status by monitoring checkbox state changes in tasks.md
- **FR-005**: System MUST respect configurable iteration limits with a sensible default
- **FR-006**: System MUST terminate the loop when the agent outputs `<promise>COMPLETE</promise>` token indicating all tasks are complete
- **FR-007**: System MUST provide a prompt template that instructs the agent to: (a) mark individual tasks complete by updating checkboxes in tasks.md, and (b) output `<promise>COMPLETE</promise>` when all tasks pass
- **FR-008**: System MUST support graceful interruption (Ctrl+C) without losing progress
- **FR-009**: System MUST display summary-level progress after each iteration (iteration number, task attempted, pass/fail outcome)
- **FR-010**: System MUST generate the prompt by combining the prompt template with current task context
- **FR-011**: System MUST detect and use the agent CLI configured for the project

### Key Entities

- **Ralph Session**: A single execution of the ralph loop command; has iteration count, start time, status (running/completed/interrupted/failed)
- **Iteration**: One invocation of the agent CLI within a session; has number, task attempted, outcome (success/failure), duration
- **Progress Log**: Append-only file tracking all iterations; entries include timestamp, task ID, files changed, learnings discovered
- **Task Tracking**: Structure mapping task IDs to completion status; synced with tasks.md but in machine-readable format
- **Prompt Template**: Instructions given to each agent iteration; includes ralph-specific behavior guidance

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate ralph loop with a single command and no additional configuration
- **SC-002**: A feature with 5-10 tasks can be implemented autonomously in under 30 minutes of wall-clock time
- **SC-003**: Each iteration starts within 2 seconds of the previous iteration completing
- **SC-004**: Progress file accurately reflects all completed work, verifiable by user inspection
- **SC-005**: Loop terminates correctly in 100% of cases where all tasks are complete
- **SC-006**: Interruption preserves all progress made up to that point
- **SC-007**: Users can resume a partially completed ralph loop and it picks up from where it left off

## Assumptions

- Users have already completed the spec, plan, and tasks phases before running ralph loop
- GitHub CLI (`gh`) is installed with the Copilot extension (`gh copilot`) available and authenticated
- Tasks in tasks.md are appropriately sized for single-context completion (per Ralph methodology)
- Git is available and the project is a git repository (for commit tracking between iterations)
- The `gh copilot` CLI supports accepting prompts for code generation tasks

## Clarifications

### Session 2026-01-18

- Q: How should the agent signal that a task has been completed within an iteration? → A: Agent updates tasks.md directly; loop watches for checkbox changes
- Q: What should the default maximum iteration limit be? → A: 10 iterations (matches reference implementation)
- Q: Which agent CLIs should be supported in the initial release (MVP)? → A: GitHub Copilot only
- Q: How should the ralph loop invoke GitHub Copilot for each iteration? → A: Use Copilot CLI (`gh copilot`) for command-line integration
- Q: What observability/logging level should be provided during ralph loop execution? → A: Summary level (iteration count, task attempted, pass/fail per iteration)
- Q: How should the loop detect that ALL tasks are complete and terminate? → A: Agent outputs `<promise>COMPLETE</promise>` token when all tasks pass; loop detects this in stdout and exits
