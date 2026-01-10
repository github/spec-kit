---
description: Generate an actionable, dependency-ordered tasks.md with intelligent parallel batch orchestration for feature implementation.
handoffs:
  - label: Analyze For Consistency
    agent: speckit.analyze
    prompt: Run a project analysis for consistency
    send: true
  - label: Implement Project
    agent: speckit.implement
    prompt: Start the implementation in phases
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Flags

Parse the following flags from user input:

| Flag | Default | Description |
|------|---------|-------------|
| `--orchestration` | false | Emit `tasks.execution.yaml` alongside `tasks.md` |
| `--max-parallel N` | 10 | Maximum concurrent subagents (hard cap enforced by Claude Code) |
| `--model` | opus-4.5 | Model for subagents (opus-4.5 = most capable, sonnet-4 = faster) |
| `--ultrathink` | true | Enable extended thinking for complex architecture tasks |
| `--async-background` | true | Allow research tasks to run as background agents (Ctrl+B) |
| `--cross-phase` | true | Allow independent user story phases to run concurrently within single session |
| `--greedy-refill` | true | Immediately start queued tasks when slots free (vs waiting for batch) |
| `--no-gates` | false | Omit validation gates (not recommended) |
| `--tdd` | false | Generate test tasks before implementation |

## Outline

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load design documents**: Read from FEATURE_DIR:
   - **Required**: plan.md (tech stack, libraries, structure), spec.md (user stories with priorities)
   - **Optional**: data-model.md (entities), contracts/ (API endpoints), research.md (decisions), quickstart.md (test scenarios)
   - Note: Not all projects have all documents. Generate tasks based on what's available.

3. **Build task dependency graph**:
   - Parse plan.md for project structure (directories, file conventions)
   - Extract user stories from spec.md with priorities (P1, P2, P3)
   - If data-model.md exists: Map entities to user stories, identify entity relationships
   - If contracts/ exists: Map endpoints to user stories and their dependent services
   - Build dependency edges:
     - Model → Service (service imports model)
     - Service → Endpoint (endpoint uses service)
     - Implementation → Test (test validates implementation, unless TDD)
     - Shared entity → All consumers (cross-story dependencies)

4. **Execute batch assignment algorithm (GREEDY PARALLEL)**:

   ```
   # GOAL: Maximize parallelism by creating widest possible batches
   # CONSTRAINT: Tasks in same batch must have no dependencies on each other

   For each phase (Setup, Foundational, UserStory1, UserStory2, ...):

     # Step 1: Extract all tasks with their dependency graph
     tasks = get_tasks_for_phase(phase)
     for task in tasks:
       task.output_file = extract_primary_output_file(task)
       task.output_dir = dirname(task.output_file)  # models/, services/, etc.
       task.dependencies = extract_dependencies(task, all_tasks)

     # Step 2: Compute dependency levels via topological sort
     # OPTIMIZATION: Minimize levels to maximize batch width
     levels = {}
     for task in topological_order(tasks):
       if not task.dependencies:
         levels[task] = 0
       else:
         # Use min+1 not max+1 when deps are in different batches
         levels[task] = max(levels[dep] for dep in task.dependencies) + 1

     # Step 3: GREEDY batch assignment - maximize tasks per level
     batches = defaultdict(list)
     for task, level in levels.items():
       batch_id = f"{phase.number}.{level + 1}"
       batches[batch_id].append(task)

     # Step 4: BATCH WIDTH OPTIMIZATION
     # If any batch has < 3 tasks, try to merge with adjacent levels
     for batch_id, batch_tasks in list(batches.items()):
       if len(batch_tasks) < 3:
         # Check if tasks can be safely moved to previous batch
         can_merge = all(
           not any(dep in batches[prev_batch] for dep in t.dependencies)
           for t in batch_tasks
           for prev_batch in [f"{phase.number}.{int(batch_id.split('.')[1])-1}"]
           if prev_batch in batches
         )
         if can_merge and prev_batch in batches:
           batches[prev_batch].extend(batch_tasks)
           del batches[batch_id]

     # Step 5: Validate file isolation within each batch
     for batch_id, batch_tasks in batches.items():
       files = [t.output_file for t in batch_tasks if t.output_file]
       if len(files) != len(set(files)):
         # Split ONLY conflicting tasks, keep others parallel
         resolve_file_conflicts_minimal(batch_id, batch_tasks)

     # Step 6: Generate validation gate for each batch
     for batch_id, batch_tasks in batches.items():
       gate = generate_gate(batch_tasks)
       # Gate validation is PARALLEL-AWARE:
       # - Run all type checks in single command (batch validation)
       # - Use && chaining, not sequential gates
   ```

   **CROSS-PHASE PARALLELISM** (when `--cross-phase` enabled):
   ```
   # After Foundational phase completes:
   # - Identify independent user story phases (no cross-story dependencies)
   # - Launch ALL independent story phases concurrently
   # - Each story progresses through its batches independently

   independent_stories = [
     phase for phase in user_story_phases
     if not has_cross_story_dependencies(phase)
   ]

   # Dispatch ALL batch 1 tasks across ALL independent stories simultaneously
   # Result: Up to (max_parallel × num_stories) concurrent subagents
   ```

5. **Determine context scope for each task**:

   | Task Type | Required Context |
   |-----------|------------------|
   | Project setup | plan.md (full) |
   | Config/infra | plan.md#config, research.md#decisions |
   | Model | plan.md#models, data-model.md#{entity_name} |
   | Service | plan.md#services, dependent model files, contracts/{endpoint}.yaml |
   | Endpoint/Route | plan.md#endpoints, service interfaces, contracts/{endpoint}.yaml |
   | Test (unit) | Implementation file under test |
   | Test (contract) | contracts/{endpoint}.yaml |
   | Test (integration) | spec.md#{user_story}, relevant implementation files |

6. **Generate tasks.md**: Use `.specify/templates/tasks-template.md` as structure, fill with:
   - Feature name from plan.md
   - Execution constraints section
   - Phase 1: Setup tasks (project initialization)
   - Phase 2: Foundational tasks (blocking prerequisites for all user stories)
   - Phase 3+: One phase per user story (in priority order from spec.md)
     - Organize tasks into batches with `[P:X.Y]` notation
     - Insert validation gate after each batch
     - Include batch-level context hints
   - Final Phase: Polish & cross-cutting concerns
   - Parallel Execution Summary table
   - Quick Start section (sequential vs parallel paths)
   - Dependencies section with critical path analysis
   - Recovery Playbook

7. **Generate tasks.execution.yaml** (if --orchestration flag):
   - Machine-readable manifest with:
     - Feature metadata
     - Execution constraints
     - Phase definitions with batch lists
     - Task definitions with context scope, timeout, output files
     - Gate definitions with commands and failure actions
     - Dependency graph edges

8. **Generate Dependency Visualization** (include in tasks.md):

   Create a Mermaid flowchart showing task dependencies:

   ```markdown
   ## Dependency Graph

   ```mermaid
   graph LR
       subgraph Phase 1: Setup
           T001[T001: Project structure]
           T002[T002: Dependencies]
       end

       subgraph Phase 2: Foundational
           T003[T003: Database setup]
           T004[T004: Auth framework]
       end

       subgraph Phase 3: US1
           T012[T012: User model]
           T014[T014: UserService]
           T016[T016: User endpoint]
       end

       T001 --> T003
       T002 --> T003
       T003 --> T012
       T012 --> T014
       T014 --> T016

       style T001 fill:#90EE90
       style T016 fill:#FFB6C1
   ```
   ```

   **Styling rules**:
   - Green (`#90EE90`): Tasks with no dependencies (can start immediately)
   - Red/Pink (`#FFB6C1`): Critical path tasks (longest chain)
   - Default: All other tasks

9. **Generate Parallelism Metrics** (include in tasks.md):

   ```markdown
   ## Parallelism Analysis

   | Phase | Batches | Tasks | Max Parallel | Speedup |
   |-------|---------|-------|--------------|---------|
   | Setup | 1 | 3 | 3 | 3.0x |
   | Foundational | 2 | 6 | 3 | 3.0x |
   | US1 | 3 | 8 | 4 | 2.7x |
   | US2 | 3 | 6 | 3 | 2.0x |
   | Polish | 1 | 2 | 2 | 2.0x |

   **Critical Path**: T001 → T003 → T012 → T014 → T016 (5 tasks)
   **Parallelism Factor**: 5.0x (25 tasks / 5 critical path)
   **Max Concurrent**: 10 (Claude Code hard cap)
   ```

   Calculate metrics:
   - **Max Parallel per phase**: Largest batch size in that phase
   - **Speedup per phase**: Total tasks in phase / number of batches
   - **Critical Path**: Longest chain of dependent tasks across all phases
   - **Parallelism Factor**: Total tasks / critical path length

10. **Report**: Output path(s) to generated file(s) and summary:
   - Total task count
   - Batch count per phase
   - Critical path (longest sequential chain with task IDs)
   - Parallelism factor (total tasks / critical path length)
   - Max parallelism per phase
   - Estimated time savings (if tasks have timeout estimates)
   - Format validation: Confirm ALL tasks have batch IDs and gates present

Context for task generation: $ARGUMENTS

The tasks.md should be immediately executable - each task must be specific enough that an LLM can complete it without additional context.

---

## Task Generation Rules

**CRITICAL**: Tasks MUST be organized by user story AND grouped into parallelizable batches to enable efficient subagent execution.

**Tests are OPTIONAL**: Only generate test tasks if `--tdd` flag is set or explicitly requested in the feature specification.

### Checklist Format (REQUIRED)

Every task MUST strictly follow this format:

```text
- [ ] [TaskID] [P:batch-id?] [Story?] Description with file path
```

**Format Components**:

1. **Checkbox**: ALWAYS start with `- [ ]` (markdown checkbox)
2. **Task ID**: Sequential number (T001, T002, T003...) in execution order
3. **[P:X.Y] marker**: Batch identifier for parallel execution
   - X = phase number (1 = Setup, 2 = Foundational, 3+ = User Stories)
   - Y = batch within phase (1, 2, 3...)
   - Tasks with SAME batch ID can run in parallel
   - OMIT entirely if task cannot be parallelized (rare)
4. **[Story] label**: REQUIRED for user story phase tasks only
   - Format: [US1], [US2], [US3], etc. (maps to user stories from spec.md)
   - Setup phase: NO story label
   - Foundational phase: NO story label
   - User Story phases: MUST have story label
   - Polish phase: NO story label
5. **Description**: Clear action with exact file path

**Examples**:

- ✅ CORRECT: `- [ ] T001 [P:1.1] Create project structure per implementation plan`
- ✅ CORRECT: `- [ ] T005 [P:2.1] Implement authentication middleware in src/middleware/auth.py`
- ✅ CORRECT: `- [ ] T012 [P:3.1] [US1] Create User model in src/models/user.py`
- ✅ CORRECT: `- [ ] T014 [P:3.2] [US1] Implement UserService in src/services/user_service.py`
- ✅ CORRECT: `- [ ] T020 [US2] Implement OrderService in src/services/order_service.py` (not parallelizable)
- ❌ WRONG: `- [ ] T012 [P] [US1] Create User model` (missing batch ID, missing file path)
- ❌ WRONG: `- [ ] Create User model` (missing ID, batch, story label)
- ❌ WRONG: `T001 [P:1.1] Create model` (missing checkbox)

### Batch Organization Rules

1. **Same batch = truly parallel**:
   - Different output files (no merge conflicts)
   - No dependencies on each other
   - Can execute simultaneously without coordination

2. **Batch ordering**:
   - Lower batch number executes first: 3.1 → 3.2 → 3.3
   - All tasks in batch N must complete before batch N+1 starts
   - Gate validation runs between batches

3. **Typical batch patterns per phase**:

   | Batch | Typical Contents | Gate |
   |-------|------------------|------|
   | X.1 | Models, schemas, types | Type check |
   | X.2 | Services, business logic | Type check + import |
   | X.3 | Endpoints, routes, handlers | Type check + route test |
   | X.4 | Integration, wiring | Smoke test |

4. **Cross-story dependencies**:
   - If US2 needs an entity from US1, that entity goes in Foundational phase
   - Or: US2 explicitly depends on US1 completion (document in Dependencies section)
   - Goal: Each user story phase is independently executable after Foundational

### Gate Definitions

Insert a gate section after each batch:

```markdown
#### Gate X.Y
```bash
# Validation command(s)
ty src/models/*.py
python -c "from src.models import User, Order"
```
**On-Fail**: [Specific recovery guidance for this batch]
```

**Gate types by task type**:

| Task Type | Gate Command | On-Fail Guidance |
|-----------|--------------|------------------|
| Models | `ty {files}` + import test | Check data-model.md definitions |
| Services | `ty {files}` + import test | Verify model dependencies exist |
| Endpoints | `ty {files}` + route registration | Check service interfaces |
| Tests | `pytest --collect-only {files}` | Verify test discovery |
| Config | Config validation script | Check environment variables |

### Fault Tolerance Configuration

Gates should include recovery hints for common failure patterns:

```markdown
#### Gate 3.1
```bash
ty src/models/*.py && python -c "from src.models import User, Session"
```
**On-Fail**:
- `Cannot find module` → Install missing dependency or check import path
- `Property .* does not exist` → Verify field names match data-model.md
- `has no exported member` → Check export statement in source file
- `SyntaxError` → Fix syntax error in generated code (do not retry)
```

**Retry policy** (in tasks.execution.yaml):
```yaml
retry_policy:
  max_attempts: 3
  strategy: exponential      # exponential, linear, constant
  initial_delay_seconds: 5
  max_delay_seconds: 60
  retry_on:
    - timeout
    - rate_limit
  fail_fast_on:              # Do NOT retry these
    - syntax_error
    - import_error
    - type_error
```

**Circuit breaker** (stops execution on repeated failures):
```yaml
circuit_breaker:
  - at_failures: 3
    action: pause_batch      # Stop current batch, ask user
  - at_failures: 5
    action: pause_phase      # Stop entire phase
  - at_failures: 10
    action: abort            # Stop everything, rollback option
```

### Context Scope Specification

For each task, determine what context a subagent needs:

```markdown
<!-- Context: plan.md#models, data-model.md#User -->
- [ ] T012 [P:3.1] [US1] Create User model in src/models/user.py
```

Context hints are OPTIONAL in tasks.md but REQUIRED in tasks.execution.yaml.

Use the following scoping rules:

1. **Minimal context**: Only what's needed for this specific task
2. **No full files**: Reference sections, not entire documents
3. **Include dependencies**: If task uses output of T010, include T010's output file
4. **Contracts are precise**: `contracts/users.yaml` not `contracts/`

### File-Based Shared Memory (Parallel Mode)

When `--orchestration` flag is set, tasks.execution.yaml includes workspace configuration for inter-agent communication:

**Workspace structure** (created by `/speckit.implement` in parallel mode):
```
.claude/workspace/
├── context.md              # Shared context written by parent agent
├── results/
│   ├── T001-result.md      # Task completion summaries
│   ├── T002-result.md
│   └── ...
└── gates/
    ├── gate-1.1.md         # Gate validation results
    └── gate-2.1.md
```

**How it works**:
1. Parent agent writes shared project context to `context.md` once per phase
2. Subagents READ from workspace (context.md + dependency results) instead of receiving full context in prompt
3. Subagents WRITE their results to `results/{task_id}-result.md`
4. Parent reads only summaries, not full conversation history
5. Gate results are logged to `gates/` for debugging

**Benefit**: 50-60% token savings compared to passing full context to each subagent.

**Result file format** (written by subagent):
```markdown
# T012 Result

## Status: SUCCESS | PARTIAL | FAILED

## Output Files
- src/models/user.py (created)

## Summary
Created User model with fields: id, email, password_hash, created_at.
Implemented password hashing with bcrypt.

## Notes
- Used UUID for id per data-model.md
- Added index on email field
```

---

## Task Organization by Phase

### Phase 1: Setup (Batch 1.1 typically)

- Project structure creation
- Dependency installation
- Tooling configuration (linting, formatting, type checking)
- Usually all parallelizable in single batch

### Phase 2: Foundational (Batches 2.1, 2.2, ...)

- Database/storage setup
- Authentication/authorization framework
- Base models shared across stories
- API scaffolding, middleware
- Error handling, logging infrastructure
- **CRITICAL**: Nothing in user story phases can start until Phase 2 completes

### Phase 3+: User Stories (Batches 3.1, 3.2, ... per story)

- One phase per user story, in priority order (P1, P2, P3)
- Each phase contains:
  - Batch X.1: Tests (if TDD) OR Models
  - Batch X.2: Services
  - Batch X.3: Endpoints/UI
  - Batch X.4: Integration/wiring
- Each phase ends with story-level checkpoint

### Final Phase: Polish

- Documentation
- Performance optimization
- Security hardening
- Cross-cutting refactors
- Quickstart validation

---

## Output Artifacts

### tasks.md (Always Generated)

Human-readable task list with:
- Execution constraints
- Batched tasks with `[P:X.Y]` notation
- Validation gates
- Parallel execution summary
- Quick start guide
- Recovery playbook

### tasks.execution.yaml (If --orchestration)

Machine-readable manifest:

```yaml
version: "1.0"
feature: feature-name
generated: "2025-01-15T10:30:00Z"

execution_constraints:
  # Claude Code MAXIMUM POWER (Jan 2026 - Claude Max 20x)
  model: opus-4.5                        # Most capable model
  max_parallel_subagents: 10             # Hard cap enforced by Claude Code
  default_task_timeout_seconds: 600      # 10min for Opus deep reasoning
  gate_timeout_seconds: 120              # 2min for complex validation
  subagent_timeout_seconds: 900          # 15min for extended tasks

  # Dispatch Strategy
  dispatch_strategy: greedy_queue        # Launch 10, queue overflow, refill on complete
  cross_phase_parallelism: true          # Independent stories run concurrently
  greedy_refill: true                    # Start queued task immediately when slot frees

  # Async/Background (v2.0.60+)
  async_background:
    enabled: true
    background_research_tasks: true      # Auto-background exploration
    wake_on_complete: true               # v2.0.64: agents wake main

  # Batch Optimization
  batch_sizing:
    prefer_wider_batches: true           # More parallel over deeper chains
    merge_small_batches: true            # Combine <3 task batches when safe
    max_batch_size: 10                   # Match hard cap

  # Extended Thinking
  extended_thinking:
    enabled: true
    ultrathink_for: [architecture, design, complex_logic]

  # Fault Tolerance
  retry_policy:
    max_attempts: 3
    strategy: exponential
    initial_delay_seconds: 5
    max_delay_seconds: 60
    retry_on: [timeout, rate_limit]
    fail_fast_on: [syntax_error, import_error, type_error]

  circuit_breaker:
    - at_failures: 3
      action: pause_batch
    - at_failures: 5
      action: pause_phase
    - at_failures: 10
      action: abort

  # Context
  context_per_subagent: 200k             # Full 200k window per agent

phases:
  - id: phase-1
    name: Setup
    batches:
      - id: "1.1"
        parallel: true
        tasks:
          - id: T001
            description: "Create project structure per implementation plan"
            output_file: null  # No single file
            context_scope:
              - plan.md
            timeout_seconds: 300
          - id: T002
            description: "Initialize Python project with FastAPI dependencies"
            output_file: pyproject.toml
            context_scope:
              - plan.md#dependencies
            timeout_seconds: 180
        gate:
          command: "test -f pyproject.toml && test -d src"
          on_fail: "Verify plan.md project structure section"

  - id: phase-3
    name: "User Story 1 - User Registration"
    depends_on: [phase-2]
    batches:
      - id: "3.1"
        parallel: true
        tasks:
          - id: T012
            description: "Create User model in src/models/user.py"
            output_file: src/models/user.py
            context_scope:
              - plan.md#models
              - data-model.md#User
            timeout_seconds: 300
          - id: T013
            description: "Create Session model in src/models/session.py"
            output_file: src/models/session.py
            context_scope:
              - plan.md#models
              - data-model.md#Session
            timeout_seconds: 300
        gate:
          command: "ty src/models/user.py src/models/session.py && python -c 'from src.models.user import User; from src.models.session import Session'"
          on_fail: "Check data-model.md entity definitions match code"

      - id: "3.2"
        parallel: true
        depends_on: ["3.1"]
        tasks:
          - id: T014
            description: "Implement UserService in src/services/user_service.py"
            output_file: src/services/user_service.py
            context_scope:
              - plan.md#services
              - src/models/user.py
              - contracts/users.yaml
            timeout_seconds: 300
        gate:
          command: "ty src/services/user_service.py && python -c 'from src.services.user_service import UserService'"
          on_fail: "Verify User model exists and is importable"

dependency_graph:
  edges:
    - from: T014
      to: T012
      type: imports
    - from: T015
      to: T014
      type: uses

critical_path:
  tasks: [T001, T004, T007, T012, T014, T016]
  estimated_duration_seconds: 1800

parallelism_analysis:
  total_tasks: 25
  critical_path_length: 6
  parallelism_factor: 4.17
  theoretical_speedup: 4.17x              # With unlimited parallelism
  practical_speedup: 3.8x                 # With max_parallel=10 + greedy refill
  max_concurrent_subagents: 10            # Hard cap per Claude session
  queue_overflow_capacity: unlimited      # Tasks beyond 10 auto-queue
  max_parallelism_by_phase:
    phase-1: 3
    phase-2: 6
    phase-3: 10                           # Full parallelism (hard cap)
    phase-4: 10
    phase-5: 10
  cross_phase_execution:
    strategy: interleaved                 # US1 + US2 tasks share 10 slots
    example: "5 US1 tasks + 5 US2 tasks = 10 concurrent"
```

---

## Execution Model

### Sequential Execution (Default)

Developer executes tasks T001 → T002 → ... in order:
- Simple, predictable
- No coordination needed
- Batch hints indicate safe parallelization opportunities

### Massive Parallel Execution (Recommended) 🚀

Orchestrator uses GREEDY PARALLEL dispatch for maximum throughput:

```python
async def execute_all_phases(manifest: dict):
    """Execute with cross-phase parallelism for independent stories."""

    # Phase 1 & 2: Sequential (Setup → Foundational)
    await execute_phase(manifest, "phase-1")
    await execute_phase(manifest, "phase-2")

    # Phase 3+: PARALLEL execution of independent user stories
    independent_stories = [
        p for p in manifest["phases"]
        if p["id"].startswith("phase-") and int(p["id"].split("-")[1]) >= 3
        and not p.get("depends_on_story")
    ]

    # Launch ALL story phases concurrently
    await asyncio.gather(*[
        execute_phase_with_streaming(manifest, phase["id"])
        for phase in independent_stories
    ])

    # Final phase: Polish (after all stories complete)
    await execute_phase(manifest, "phase-n")


async def execute_phase_with_streaming(manifest: dict, phase_id: str):
    """GREEDY execution: launch all eligible, stream results."""
    phase = get_phase(manifest, phase_id)
    max_parallel = manifest["execution_constraints"]["max_parallel_subagents"]

    for batch in phase["batches"]:
        # GREEDY DISPATCH: Launch ALL tasks immediately
        semaphore = asyncio.Semaphore(max_parallel)
        tasks = []

        for task_def in batch["tasks"]:
            async def run_with_limit(t):
                async with semaphore:
                    context = load_minimal_context(t["context_scope"])
                    return await spawn_subagent(t, context)

            tasks.append(run_with_limit(task_def))

        # STREAMING: Process results as they complete (don't wait for slowest)
        results = []
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            # Stream progress: "T012 complete (3/8 in batch 3.1)"

        # Gate validation AFTER all batch tasks complete
        gate_result = await run_gate(batch["gate"])
        if not gate_result.success:
            handle_gate_failure(batch, gate_result)
            return

        # Auto-commit on gate success
        git_commit(f"[speckit] Gate {batch['id']} passed")
```

### Failure Handling

1. **Task failure**: Retry per policy, then mark failed
2. **Batch failure (2+ tasks)**: Pause execution, report status
3. **Gate failure**: Pause, surface error, provide recovery guidance
4. **Rollback**: `git checkout speckit-gate-{last_successful_batch}`

---

## Report Format

```
## Task Generation Report

**Feature**: [feature-name]
**Generated**: [timestamp]

### Summary
- Total tasks: 25
- Phases: 5
- Batches: 12

### Parallelism Analysis
| Phase | Batches | Tasks | Max Parallel | Critical Path |
|-------|---------|-------|--------------|---------------|
| Setup | 1 | 3 | 3 | T001 |
| Foundational | 2 | 6 | 2 | T004 → T007 |
| US1 | 3 | 8 | 2 | T012 → T014 → T016 |
| US2 | 3 | 6 | 2 | T018 → T020 → T022 |
| Polish | 3 | 2 | 2 | T024 |

### Critical Path
T001 → T004 → T007 → T012 → T014 → T016
**Length**: 6 tasks
**Parallelism Factor**: 4.17x (25 tasks / 6 critical)

### Validation
✅ All tasks have batch IDs
✅ All batches have gates
✅ All user story tasks have [USn] labels
✅ No file conflicts within batches
✅ Dependency graph is acyclic

### Output Files
- /specs/001-feature-name/tasks.md
- /specs/001-feature-name/tasks.execution.yaml (if --orchestration)
```