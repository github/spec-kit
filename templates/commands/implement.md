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

3. **Minimal context loading** (agents will load their own detailed context):
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **SCAN ONLY** (don't read full content yet): List files in task-plans/ and task-results/ directories
   - **DO NOT** load data-model.md, contracts/, research.md, or quickstart.md upfront
   - Agents will load these files as needed based on their specific tasks

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

6. **Load available specialized agents** (if .claude/agents/speckit/ exists):
   - Check if directory exists: `ls .claude/agents/speckit/ 2>/dev/null`
   - If exists, list all agent files: `ls .claude/agents/speckit/*.md`
   - For each agent file found:
     * Read the file to extract frontmatter (name, description, model)
     * Parse file patterns from description or create default pattern from name
     * Add to agent registry with format: `{pattern} → {name} (model: {model})`
   - Build agent mapping based on discovered agents, example mappings:
     * `backend/**`, `server/**`, `api/**` → backend-coder
     * `frontend/**`, `src/components/**`, `*.tsx` → frontend-coder
     * `*.test.*`, `*_test.*`, `tests/**` → tester
     * UI design tasks → frontend-designer
     * No match → implementer (fallback)
   - Log detected agents: "Found N specialized agents: {list of agent names}"
   - If no agents found, log: "No specialized agents detected, using direct implementation"
   - Store agent registry for use in Step 7

   **When task plans are available** (task-plans/T{number}-*.md):
   - **Follow implementation steps exactly**: Execute steps in order from the plan
   - **Use reference patterns**: Copy/adapt code snippets from "Existing Patterns to Follow" section
   - **Check gotchas first**: Review "Gotchas / Special Considerations" before starting implementation
   - **Verify dependencies**: Ensure all required files/services from Dependencies section exist
   - **Follow exact file paths**: Use file paths from "Codebase Impact Analysis" section for accuracy

7. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

   **For each task:**

   a. **Determine execution mode** based on agent availability:
      - Extract file paths from task description
      - Match file patterns against agent mapping table
      - If matching agent exists → **Delegate mode**
      - If no matching agent → **Direct mode**

   b. **Delegate mode** (agent exists):
      - Use Task tool to invoke the specialized agent
      - Pass task number, description, and feature directory
      - Agent will autonomously:
        * Load task plan from task-plans/T{number}-*.md (if exists, handle errors gracefully)
        * Load previous results:
          - T{number-1}-result.md (previous task in sequence)
          - Results for tasks listed in "Depends On" from the plan (if specified)
        * Extract from previous results: what was implemented, deviations, gotchas, TODOs, lessons learned
        * Read relevant context files (data-model.md, contracts/, etc. as needed)
        * Implement the task using Edit/Write tools
        * Report files changed and any issues
      - After agent returns, create task-results/T{number}-result.md with structured format (see below)
      - Update tasks.md: mark [X] (complete) or [~] (partial) and append [📊 Result](task-results/T{number}-result.md)
      - Log progress

   c. **Direct mode** (no agent):
      - Load task plan from task-plans/T{number}-*.md (if exists, handle errors gracefully)
      - Load previous results:
        * T{number-1}-result.md (previous task in sequence)
        * Results for tasks listed in "Depends On" from the plan (if specified)
      - Extract from previous results: what was implemented, deviations, gotchas, TODOs, lessons learned
      - Read relevant context files (data-model.md, contracts/, etc. as needed)
      - Implement task directly using Edit/Write tools
      - Create task-results/T{number}-result.md with structured format (see below)
      - Update tasks.md: mark [X] (complete) or [~] (partial) and append result reference
      - Log progress

   **Task tool invocation format** (delegate mode):
   ```yaml
   Task:
     subagent_type: "{agent-name}"
     model: "{agent-model}"
     description: "Implement T{number}: {short-description}"
     prompt: |
       Implement task T{number} from {FEATURE_DIR}/tasks.md

       Task: {full-task-description}

       Instructions:
       1. Load task plan from {FEATURE_DIR}/task-plans/T{number}-*.md if exists (handle errors gracefully)
       2. Load previous results:
          - {FEATURE_DIR}/task-results/T{number-1}-result.md (previous task)
          - Results for tasks in "Depends On" from plan (if specified)
       3. Extract from results: what was implemented, deviations, gotchas, TODOs, lessons learned
       4. Implement following the plan's steps, or use standard patterns if no plan
       5. Report using structured format: status, files changed, deviations, gotchas, TODOs, lessons
   ```

   **Result file format** (task-results/T{number}-result.md):
   ```markdown
   Status: ✅ Complete | ⚠️ Partial | ❌ Failed
   Files Changed:
     - {file}: {description of changes, line ranges}
   Deviations from Plan: {what changed vs plan and why, or "None"}
   Gotchas Discovered: {issues found and resolutions, or "None"}
   TODOs Left:
     - 🚫 Blockers: {critical issues preventing progress}
     - 💡 Enhancements: {nice-to-have improvements}
     - ⚠️ Technical debt: {shortcuts taken, to be addressed later}
   Lessons Learned: {patterns that worked/didn't work}
   ```

   **Task plan error handling**:
   - If plan referenced in tasks.md but file missing: Log warning, implement using task description only
   - If plan file exists but malformed/unreadable: Use best-effort extraction, log issues found
   - If "Implementation Steps" incomplete in plan: Use available steps and supplement with task description
   - If dependent files don't exist (per plan's Dependencies): Report missing prerequisite and skip task with clear message

   **After phase complete**:
   - Aggregate TODOs from all task-results/T*-result.md files in completed phase
   - Categorize by type: 🚫 blockers / 💡 enhancements / ⚠️ technical debt
   - If blockers exist: **STOP** and report blockers to user, ask whether to resolve/continue/stop
   - If no blockers: Proceed to next phase

8. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

9. Progress tracking and error handling:
   - Report progress after each completed task
   - Mark tasks as [X] (complete) or [~] (partial) based on result status
   - Halt execution if any non-parallel task fails (status: ❌ Failed)
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed

10. Completion validation:
    - Verify all required tasks are completed
    - Check that implemented features match the original specification
    - Validate that tests pass and coverage meets requirements
    - Confirm the implementation follows the technical plan
    - Report final status with summary of completed work

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list.
