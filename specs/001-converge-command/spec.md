# Feature Specification: Implementation Convergence Command (`/speckit.converge`)

**Feature Branch**: `001-converge-command`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "Create the spec from the plan — a built-in `/speckit.converge` command that assesses the spec, plan, and tasks against the codebase, determines which required work remains unbuilt, and appends those as new tasks to tasks.md so implement can complete them."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface remaining work as new tasks (Priority: P1)

A developer has run the spec-driven workflow through implementation, but the implementation pass did not fully satisfy everything the specification, plan, and tasks called for. The developer runs the convergence command. It reads the spec, plan, and tasks as the sole source of intent, assesses the current codebase, and determines which requirements, acceptance criteria, plan decisions, and existing tasks are still unmet, incomplete, or only partially satisfied. It then appends each piece of remaining work as a new, clearly-labeled task at the bottom of the task list so the implementation step can complete it.

**Why this priority**: This is the core value of the feature — closing the gap between what was specified and what was built, expressed as actionable tasks the existing implementation workflow can consume. Without it, gaps are only caught during manual review.

**Independent Test**: Take a feature whose code intentionally omits one specified requirement, run the command, and confirm a new task describing exactly that missing requirement is appended to the task list and that no other artifact is changed.

**Acceptance Scenarios**:

1. **Given** a feature whose code does not implement a specified requirement, **When** the developer runs the convergence command, **Then** a new task describing that requirement is appended to the task list, traceable to the originating requirement.
2. **Given** a feature whose code only partially satisfies an acceptance criterion, **When** the developer runs the convergence command, **Then** a new task describing the remaining portion is appended.
3. **Given** appended convergence tasks, **When** the developer runs the implementation step, **Then** those tasks are picked up and executed like any other task with no special handling.

---

### User Story 2 - Confirm convergence is complete (Priority: P2)

A developer wants to know whether the implementation now satisfies everything the spec, plan, and tasks require. They run the convergence command and, when nothing remains, receive a clear "converged" result with a summary of what was checked and confirmation that no tasks were appended.

**Why this priority**: Knowing the loop has terminated (the gap has reached zero) is essential for deciding the feature is ready for review. It is the natural stopping condition of the iterate-and-check loop.

**Independent Test**: Run the command against a feature whose code fully satisfies its spec, plan, and tasks, and confirm a clean result is reported and the task list is unchanged.

**Acceptance Scenarios**:

1. **Given** a feature whose code satisfies all requirements, acceptance criteria, and plan decisions, **When** the developer runs the convergence command, **Then** a clean "converged" result is reported and no tasks are appended.
2. **Given** a clean convergence result, **When** the developer reviews the output, **Then** it summarizes the counts of requirements, acceptance criteria, and plan decisions checked.

---

### User Story 3 - Trace each remaining task to its source (Priority: P3)

When the command appends tasks, a developer can see exactly which requirement, acceptance criterion, plan decision, or governing constraint each appended task exists to satisfy, and what kind of gap it represents (missing, partial, contradicts intent, or unrequested addition).

**Why this priority**: Traceability lets the developer trust and prioritize the appended work, and review the reasoning, without re-deriving why each task exists. It improves confidence but the tasks are still actionable without it.

**Independent Test**: Run the command against a feature with several distinct gaps and confirm each appended task names its originating requirement and gap type.

**Acceptance Scenarios**:

1. **Given** appended convergence tasks, **When** the developer reads them, **Then** each names the specific requirement or criterion it traces back to.
2. **Given** appended convergence tasks, **When** the developer reads them, **Then** each is labeled with the type of gap it addresses.

---

### Edge Cases

- **No prior implementation exists**: If little or no code has been written yet, the command treats the entire specified scope as remaining work rather than failing.
- **Code contains work not called for by the spec, plan, or tasks**: Unrequested additions are surfaced as findings so the developer is aware, but the command does not delete code — it only appends tasks.
- **Required artifacts are missing**: If the plan or tasks are absent, the command stops with a clear message pointing the developer to the prerequisite step rather than producing partial output.
- **A governing constraint is violated by the code**: A constraint violation is treated as the highest-severity finding and produces a corresponding remediation task.
- **Nothing remains to do**: The command reports a clean result and leaves the task list untouched.
- **The same command is run repeatedly**: Each run reflects the current state of the code; as the developer completes appended tasks, subsequent runs find fewer remaining items.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST treat the feature's specification, plan, and tasks as the sole source of intent when assessing remaining work, and MUST NOT infer scope beyond what those artifacts define.
- **FR-002**: The command MUST treat the project's governing constraints (constitution) as non-negotiable and assess the codebase against them.
- **FR-003**: The command MUST assess the current state of the codebase to determine which specified requirements, acceptance criteria, plan decisions, and existing tasks are unmet, incomplete, or only partially satisfied.
- **FR-004**: The command MUST classify each finding by the kind of gap it represents: missing work, partially completed work, work that contradicts stated intent, or work present in the code that was not requested.
- **FR-005**: For each piece of remaining work, the command MUST append a corresponding task to the feature's task list so that the implementation step can complete it.
- **FR-006**: Appended tasks MUST continue the existing task-numbering scheme, incrementing from the highest existing task number, and MUST be grouped under a clearly identified convergence section.
- **FR-007**: Each appended task MUST be traceable to the specific requirement, acceptance criterion, plan decision, or governing constraint it exists to satisfy, and MUST indicate its gap type.
- **FR-008**: The command MUST NOT modify the specification or the plan.
- **FR-009**: The command MUST NOT rewrite or delete existing tasks; it may only append new ones.
- **FR-010**: The command MUST NOT modify application code directly; completing the appended tasks is the responsibility of the implementation step.
- **FR-011**: When the codebase already satisfies everything the spec, plan, and tasks require, the command MUST report a clean "converged" result and leave the task list unchanged.
- **FR-012**: The command MUST present a human-readable summary of its findings, including what was checked and what remains.
- **FR-013**: The command MUST stop with a clear, actionable message when required input artifacts (plan or tasks) are missing, naming the prerequisite step to run.
- **FR-014**: The command MUST suggest the appropriate next step after running — continuing implementation when tasks were appended, or proceeding to review when converged.
- **FR-015**: The command MUST expose extension points that run before the assessment and after the result is produced, and the post-assessment extension point MUST be able to distinguish a converged result from one where tasks were appended.
- **FR-016**: The command MUST be available across all supported coding-agent integrations using the same invocation convention as the other core commands.
- **FR-017**: The command MUST be discoverable in the post-initialization guidance as a step that follows implementation.

### Key Entities *(include if feature involves data)*

- **Finding**: A single assessed gap between specified intent and the codebase. Attributes: the source it traces to (requirement, acceptance criterion, plan decision, or constraint), the gap type (missing, partial, contradicts intent, unrequested addition), a severity, and a human-readable description.
- **Convergence task**: A new task appended to the task list to close a finding. Attributes: an identifier continuing the existing numbering, a description, the source reference it satisfies, and its gap-type label.
- **Convergence result**: The outcome of a single run. Either "converged" (nothing remaining) or "tasks appended", along with summary counts of what was checked.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a feature whose code omits one or more specified requirements, 100% of those omitted requirements appear as appended tasks after a single run.
- **SC-002**: When the codebase fully satisfies the spec, plan, and tasks, the command reports a clean result and appends zero tasks.
- **SC-003**: Every appended task names the specific source it traces to, verifiable by inspection of the task list.
- **SC-004**: Running the command never alters the specification, the plan, or any pre-existing task — verifiable by confirming those artifacts are byte-for-byte unchanged except for the appended convergence section in the task list.
- **SC-005**: Appended tasks are completed by the standard implementation step with no manual reformatting, and a follow-up run finds fewer or no remaining items.
- **SC-006**: A developer can go from "implementation finished" to "knowing exactly what work remains, as tasks" in a single command invocation.

## Assumptions

- **Append without a separate confirmation gate**: Because the explicit purpose of the command is to produce the remaining tasks and add them, the command appends the convergence tasks as part of its normal run and shows the findings summary, rather than requiring a separate approval step before appending. The artifacts it must never touch (spec, plan, existing tasks, code) protect against unwanted changes.
- **Single-feature scope**: The command assesses one feature at a time. Detecting conflicts across multiple features is out of scope.
- **No source-control dependency**: Assessment is based on reading the current state of the codebase relative to the feature's artifacts, not on comparing branches or tracking changes over time.
- **Reuses the existing implementation workflow**: Appended tasks are ordinary tasks; no new execution mode is introduced to complete them.
- **Findings are reported in the session, not persisted as a separate report artifact**: The human-readable summary is surfaced to the developer rather than written to a standalone file.
- **The constitution may be a template**: If the project's governing constraints are not yet defined, constraint assessment is skipped gracefully rather than failing.

## Out of Scope

- Rewriting or "backfilling" the specification or plan to match the code.
- Generating a specification from un-specified code (code-first workflows).
- Automatically fixing or editing application code.
- Detecting conflicts or overlaps across multiple features.
- Tracking convergence metrics or deltas across runs over time.
- Acting as a continuous-integration merge gate (left to dedicated extensions).
