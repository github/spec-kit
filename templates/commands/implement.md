---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     - Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     - Completed items: Lines matching `- [X]` or `- [x]`
     - Incomplete items: Lines matching `- [ ]`
   - Create a status table:

     ```text
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```

   - Calculate overall status:
     - **PASS**: All checklists have 0 incomplete items
     - **FAIL**: One or more checklists have incomplete items

   - **If any checklist is incomplete**:
     - Display the table with incomplete item counts
     - **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     - Wait for user response before continuing
     - If user says "no" or "wait" or "stop", halt execution
     - If user says "yes" or "proceed" or "continue", proceed to step 3

   - **If all checklists are complete**:
     - Display the table showing all checklists passed
     - Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios
   - **IF EXISTS**: Scan task-plans/ directory for task implementation guides (created by /speckit.breakdown)
   - **IF EXISTS**: Scan task-results/ directory for previous implementation results

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* exists → create/verify .eslintignore
   - Check if eslint.config.* exists → ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore

   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology

   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `Makefile`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

5.5 **CRITICAL: Load Task Plans and Previous Results**:

   **Task Plan Loading (MANDATORY when plan exists)**:
   - For each task to be implemented:
     * Extract task ID from tasks.md (e.g., T004, T051, etc.)
     * Search for plan file: `{FEATURE_DIR}/task-plans/T{number}-*.md`
     * **IF PLAN EXISTS - MUST LOAD**:
       - Read entire plan file
       - Extract: Implementation Steps, Existing Patterns, Codebase Impact, Gotchas, Dependencies, Complexity
       - Log: "✅ Loaded plan for T{number}"
     * **IF PLAN MISSING but referenced in tasks.md** ([📋 Plan](task-plans/...)):
       - Log: "⚠️ WARNING: Task T{number} references plan but file not found"
       - Proceed with task description from tasks.md only
     * **IF NO PLAN**: Proceed with task description, search codebase for similar patterns

   **Previous Task Results Loading (for context)**:
   - Check if task-results/ directory exists
   - For current task T{N}, look for related result files:
     * T{N-1}-result.md (previous task in sequence)
     * Result files for tasks listed in "Depends On" from plan
   - If found, read and extract:
     * What was actually implemented (vs what was planned)
     * Deviations from plan and reasons why
     * New files created/modified
     * Gotchas discovered during implementation
     * TODOs left for current or future tasks
     * Lessons learned (patterns that worked/didn't work)
   - Use this context to inform current task implementation

5.6 **Load Specialized Agents**:
   - Scan `.claude/agents/speckit/*.md` for available agents
   - For each agent, extract metadata: name, description, capabilities
   - Build agent registry mapping file patterns/capabilities to agents
   - Log detected agents with their specializations

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

   **When task plans are available**:
   - **Follow Implementation Steps exactly**: Execute steps in order from task plan
   - **Use reference patterns**: Copy/adapt code snippets from "Existing Patterns to Follow" section
   - **Check gotchas first**: Review "Gotchas / Special Considerations" before starting implementation
   - **Verify dependencies**: Ensure all required files/services from Dependencies section exist
   - **Follow exact file paths**: Use file paths from "Codebase Impact Analysis" section for accuracy

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

   **CRITICAL: Delegate Tasks to Specialized Agents** (MANDATORY when agents are available):

   **For EACH task in the implementation phase**:

   1. **Agent Selection**:
      - Extract file paths from task description
      - Match paths against agent registry built in step 5.6
      - Select best-matching agent based on file patterns and capabilities
      - If multiple agents match, split task into subtasks (one per agent)
      - If no agent matches, implement directly (no delegation)

   2. **Context Preparation** (what to pass to the agent):
      - **Task Description**: Full task text from tasks.md (ID, description, files affected)
      - **Task Plan**: Load task-plans/T{number}-*.md if exists (implementation steps, gotchas, patterns)
      - **Previous Results**: Load task-results/ for dependent tasks (T{number-1}, dependencies from plan)
      - **Domain Patterns**: Reference relevant CLAUDE.md patterns (backend/CLAUDE.md, frontend/CLAUDE.md, etc.)
      - **Feature Context**: Brief summary from spec.md and plan.md (what feature we're building)

   3. **Agent Invocation** (use Task tool):
      ```
      Prompt template:
      "Implement the following task for feature {feature-name}:

      **Task**: {task-id} - {task-description}

      **Files to modify**: {file-paths}

      [IF task plan exists]
      **Implementation Steps** (from task plan):
      {steps from task-plans/T{number}-*.md}

      **Existing Patterns to Follow**:
      {code snippets from task plan}

      **Gotchas**:
      {special considerations from task plan}
      [END IF]

      [IF previous task results exist]
      **Context from Previous Tasks**:
      {deviations, lessons learned, TODOs from task-results/}
      [END IF]

      **Domain Patterns** (from {domain}/CLAUDE.md):
      {relevant patterns for this task type}

      Follow the implementation steps exactly. Use the existing patterns as reference. Pay attention to gotchas.
      Report any deviations or issues discovered."

      subagent_type: {selected-agent-name}  // e.g., "backend-coder", "frontend-coder"
      ```

   4. **Result Handling**:
      - Wait for agent completion
      - Generate task-results/T{number}-result.md based on agent report
      - Mark task complete in tasks.md with result reference
      - Proceed to next task in phase

   **Task plan prioritization**:
   - **If task plan exists**: It supersedes generic implementation approach - follow plan exactly
   - **Reference code first**: Look at "Existing Patterns to Follow" code snippets before writing new code
   - **Copy/adapt pattern**: Adapt existing patterns from codebase rather than implementing from scratch
   - **Gotchas prevent bugs**: Special considerations often reveal hidden requirements (GraalVM reflection, type safety, async patterns, etc.)
   - **Use line references**: File:line references in plans point to exact existing implementations to follow

8. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed

   **After Task Implementation Complete**:
   - **Generate Result File**: Create `{FEATURE_DIR}/task-results/T{number}-result.md` with:
     * Status: ✅ Complete | ⚠️ Partial | ❌ Failed
     * Files Changed: created and modified files with line counts/ranges
     * Deviations from Plan: what changed vs plan and why
     * Gotchas Discovered: issues found and resolutions
     * TODOs Left: blockers, enhancements, technical debt
     * Debugging Results: compilation, linting, tests status
     * Lessons Learned: patterns that worked/didn't work
   - **Update tasks.md**: Mark task [X] if complete or [~] if partial, append result reference `[📊 Result](task-results/T{number}-result.md)`

   **After Phase Complete**:
   - Aggregate TODOs from all task result files in phase
   - Categorize: 🚫 blockers / 💡 enhancements / ⚠️ technical debt
   - If blockers exist: **STOP**, ask user to resolve/list/continue/stop
   - If no blockers: proceed to next phase

   **Task plan error handling**:
   - If task plan file referenced in tasks.md ([📋 Plan](task-plans/...)) but file is missing: Log warning and implement using task description
   - If task plan file exists but is malformed/unreadable: Use best-effort extraction and log issues
   - If "Implementation Steps" section is incomplete in task plan: Use available steps and supplement with task description
   - If dependent files don't exist (per task plan Dependencies): Report missing prerequisite and skip task (with clear message)

9. Completion validation:
   - Verify all required tasks are completed
   - Check that implemented features match the original specification
   - Validate that tests pass and coverage meets requirements
   - Confirm the implementation follows the technical plan
   - Report final status with summary: tasks completed, remaining TODOs (enhancements/debt only, blockers resolved), files changed, next steps

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list.
