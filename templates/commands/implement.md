---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
handoffs:
  - label: Diagnose Issues
    agent: speckit.fix
    prompt: Diagnose why implementation is failing and create a correction plan
  - label: Validate
    agent: speckit.validate
    prompt: Run integration tests to verify implementation
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

# Implementation Orchestrator

**YOUR ROLE**: Orchestrate implementation by delegating to specialized agents via Task tool. You coordinate; agents implement.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

---

## CRITICAL RULES (READ FIRST)

**YOU MUST FOLLOW THESE RULES - NO EXCEPTIONS:**

### Rule 1: Use Task Tool for Implementation
```
For EVERY implementation task:
→ Use Task tool to invoke specialized agent (backend-coder, frontend-coder, implementer, tester)
→ FORBIDDEN: Edit, Write, NotebookEdit tools in main conversation
→ Agents implement; you orchestrate
```

### Rule 2: ALWAYS Update tasks.md Immediately
```
After EACH task completion (success or failure):
→ YOU MUST update tasks.md with [X] or [~] checkbox
→ YOU MUST append result reference [📊 Result](task-results/T###-result.md)
→ DO NOT batch updates - update ONE task at a time
```

### Rule 3: ALWAYS Create Result Files
```
After EACH task implementation:
→ YOU MUST create task-results/T{number}-result.md
→ Include: status, files changed, deviations, lessons learned
→ This informs the next task's agent
```

### Rule 4: Minimal Context Loading
```
DO NOT load all context upfront:
→ Load ONLY tasks.md and plan.md initially
→ Let agents load their own context via skills
→ Pass task-specific context to each agent
```

---

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

3. **Minimal Context Loading** (per Rule 4):
   - **REQUIRED**: Read tasks.md - parse phases, task IDs, completion status
   - **REQUIRED**: Read plan.md - extract tech stack summary (1-2 lines per tech)
   - **SCAN ONLY** (don't read yet): List files in task-plans/ and task-results/
   - **DO NOT** read data-model.md, contracts/, research.md upfront
   - **Agents will load** their own context via skills and targeted reads

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
   - For each agent, extract metadata: name, description, capabilities, model
   - Build agent registry mapping file patterns/capabilities to agents with model info
   - Log detected agents with their specializations and configured model (e.g., "backend-coder: haiku")

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

7. **Task Execution Loop** - FOR EACH incomplete task in current phase:

   ### Step 7.1: Select Agent (REQUIRED)

   | File Pattern | Agent | Model |
   |--------------|-------|-------|
   | `backend/**`, `server/**`, `api/**` | backend-coder | sonnet |
   | `frontend/**`, `src/components/**`, `*.tsx` | frontend-coder | sonnet |
   | `*.test.*`, `*_test.*`, `tests/**` | tester | sonnet |
   | UI design tasks | frontend-designer | sonnet |
   | No match | implementer | sonnet |

   ### Step 7.2: Load Task Context (ONLY what agent needs)

   ```
   1. Read task-plans/T{number}-*.md IF EXISTS
   2. Read task-results/T{number-1}-result.md for previous task context
   3. Extract file paths from task description
   ```

   ### Step 7.3: Invoke Agent via Task Tool

   ```yaml
   Task:
     subagent_type: "{agent-name}"  # from Step 7.1
     model: "{agent-model}"         # from agent frontmatter, default: sonnet
     description: "Implement T{number}: {short-description}"
     prompt: |
       ## Task: T{number}
       {task-description}

       ## Files
       {file-paths from task}

       ## Implementation Steps
       {from task-plans/T{number}-*.md or "Follow standard patterns"}

       ## Previous Task Context
       {from task-results/T{number-1}-result.md or "First task in phase"}

       ## Instructions
       1. Implement the task following the steps above
       2. Use project skills for patterns
       3. Report: files created/modified, issues found, deviations
   ```

   ### Step 7.4: After Agent Returns (IMMEDIATELY - per Rule 2 & 3)

   **YOU MUST do these 3 things IMMEDIATELY after agent completes:**

   ```
   1. CREATE task-results/T{number}-result.md:
      ---
      Status: ✅ Complete | ⚠️ Partial | ❌ Failed
      Files Changed:
        - {file}: {what changed}
      Deviations: {if any}
      Lessons: {what worked/didn't}
      ---

   2. UPDATE tasks.md - find the task line and change:
      FROM: - [ ] T{number} {description}
      TO:   - [X] T{number} {description} [📊 Result](task-results/T{number}-result.md)

   3. LOG progress:
      "✅ T{number} complete. {N} tasks remaining in phase."
   ```

   ### Step 7.5: Continue or Pause

   - After every 3 tasks: Ask user "Continue? (yes/no/skip phase)"
   - If task failed: Ask user "Task T{N} failed. Retry/Skip/Stop?"
   - After phase complete: Show summary, ask about next phase

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
