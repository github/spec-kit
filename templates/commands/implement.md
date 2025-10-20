---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
agent_scripts:
  sh: "specify guard list"
  ps: "specify guard list"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

1.5. **Load Guard Context**:
   
   **Step 1 - List all guards**:
   ```bash
   uv run specify guard list
   ```
   This shows all guards with their last run status.
   
   **Step 2 - Check specific guard history** (before running):
   ```bash
   uv run specify guard history <guard-id>
   ```
   Replace `<guard-id>` with the guard ID from the task (e.g., G001, G002).
   
   Use this for **self-healing**:
   - Review past failures and comments before running a guard
   - Apply known fixes from comment history
   - Understand common failure patterns for this guard

2. **Check checklists status** (if FEATURE_DIR/checklists/ exists):
   - Scan all checklist files in the checklists/ directory
   - For each checklist, count:
     * Total items: All lines matching `- [ ]` or `- [X]` or `- [x]`
     * Completed items: Lines matching `- [X]` or `- [x]`
     * Incomplete items: Lines matching `- [ ]`
   - Create a status table:
     ```
     | Checklist | Total | Completed | Incomplete | Status |
     |-----------|-------|-----------|------------|--------|
     | ux.md     | 12    | 12        | 0          | ✓ PASS |
     | test.md   | 8     | 5         | 3          | ✗ FAIL |
     | security.md | 6   | 6         | 0          | ✓ PASS |
     ```
   - Calculate overall status:
     * **PASS**: All checklists have 0 incomplete items
     * **FAIL**: One or more checklists have incomplete items
   
   - **If any checklist is incomplete**:
     * Display the table with incomplete item counts
     * **STOP** and ask: "Some checklists are incomplete. Do you want to proceed with implementation anyway? (yes/no)"
     * Wait for user response before continuing
     * If user says "no" or "wait" or "stop", halt execution
     * If user says "yes" or "proceed" or "continue", proceed to step 3
   
   - **If all checklists are complete**:
     * Display the table showing all checklists passed
     * Automatically proceed to step 3

3. Load and analyze the implementation context:
   - **REQUIRED**: Read tasks.md for the complete task list and execution plan
   - **REQUIRED**: Read plan.md for tech stack, architecture, and file structure
   - **IF EXISTS**: Read data-model.md for entities and relationships
   - **IF EXISTS**: Read contracts/ for API specifications and test requirements
   - **IF EXISTS**: Read research.md for technical decisions and constraints
   - **IF EXISTS**: Read quickstart.md for integration scenarios

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:
   
   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```
   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc* or eslint.config.* exists → create/verify .eslintignore
   - Check if .prettierrc* exists → create/verify .prettierignore
   - Check if .npmrc or package.json exists → create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist → create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) → create/verify .helmignore
   
   **If ignore file already exists**: Verify it contains essential patterns, append missing critical patterns only
   **If ignore file missing**: Create with full pattern set for detected technology
   
   **Common Patterns by Technology** (from plan.md tech stack):
   - **Node.js/JavaScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
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
   - **Universal**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`
   
   **Tool-Specific Patterns**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`

5. Parse tasks.md structure and extract:
   - **Task phases**: Setup, Tests, Core, Integration, Polish
   - **Task dependencies**: Sequential vs parallel execution rules
   - **Task details**: ID, description, file paths, parallel markers [P]
   - **Execution flow**: Order and dependency requirements

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together  
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. Guard validation (Constitutional Principle V):
   - **Before running guard**, check history for learnings:
     * Load guard history from agent script output
     * Review past failures and `notes` field for common issues
     * Apply proactive fixes based on learnings
   
   - **Before marking any task [X] complete**, check for guard markers:
     * Parse task description for `[Guard: G###]` pattern
     * If no guard marker found: Mark task complete normally
     * If guard marker found: Execute guard validation
   
   - **Guard execution workflow**:
     ```bash
     # 1. Check guard history first
     uv run specify guard history <guard-id>
     
     # 2. Run the guard
     uv run specify guard run <guard-id>
     
     # 3. If guard fails, add diagnostic comment
     uv run specify guard comment <guard-id> \
       --category investigation \
       --done "Implemented feature X" \
       --expected "All tests pass" \
       --todo "Fix error Y found in output"
     ```
     
     Replace `<guard-id>` with actual guard ID (e.g., G001).
   
   - **Interpret guard results**:
     * **Exit code 0** (PASS) → Mark task [X] complete, add ✓ to guard marker
     * **Exit code non-zero** (FAIL) → Do NOT mark task complete
       1. Display guard failure output
       2. Analyze failure and determine root cause
       3. Add diagnostic comment using command above
       4. Fix implementation
       5. Re-run guard
       6. Only mark complete after guard passes
   
   - **Self-healing workflow**:
     1. Read guard history before running
     2. Apply known fixes from past failures
     3. Run guard
     4. If failure: Diagnose, fix, document in notes
     5. If success: Mark complete with ✓
   
   - **Example task completion**:
     ```markdown
     Before: - [ ] T016 [US1] Implement auth endpoint in src/api/auth.py [Guard: G001]
     After:  - [X] T016 [US1] Implement auth endpoint in src/api/auth.py [Guard: G001 ✓]
     ```
   
   - **Additional Guard Helper Commands**:
     
     **View all guards and their status**:
     ```bash
     uv run specify guard list
     ```
     
     **Check what guard types are available** (when creating new guards):
     ```bash
     uv run specify guard types -v
     ```
     
     **View detailed history for a guard**:
     ```bash
     uv run specify guard history <guard-id>
     ```
     
     **Add investigation notes after failure**:
     ```bash
     uv run specify guard comment <guard-id> \
       --category root-cause \
       --done "Identified issue in module X" \
       --expected "Fix will resolve the error" \
       --todo "Refactor function Y"
     ```
     
     Comment categories: `root-cause`, `fix-applied`, `investigation`, `workaround`, `false-positive`

9. Progress tracking and error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - **IMPORTANT** For completed tasks, make sure to mark the task off as [X] in the tasks file.

10. Completion validation:
    - Verify all required tasks are completed
    - **Verify all guards have passed** (all `[Guard: G###]` markers should show ✓)
    - Check that implemented features match the original specification
    - Validate that tests pass and coverage meets requirements
    - Confirm the implementation follows the technical plan
    - Report final status with summary of completed work

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/tasks` first to regenerate the task list.

