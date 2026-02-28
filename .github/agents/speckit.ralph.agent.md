---
description: Execute ONE work unit from tasks.md (smallest of one phase, one user story, or one task group)
---

## Scope Constraint

**CRITICAL**: This agent completes AT MOST ONE work unit per invocation.

A "work unit" is the SMALLEST of:
- One phase (e.g., "Phase 1: Project Setup")
- One user story (e.g., "US-001: Initialize Command")
- One logical grouping of tasks

**Rules**:
- Find the FIRST incomplete work unit in tasks.md
- Complete ONLY tasks within that single work unit
- DO NOT start a second work unit even if time remains
- If you cannot complete the entire work unit, complete as many tasks as possible
- Partial progress is acceptable - remaining tasks continue in subsequent iterations

**Why**: This prevents context degradation and keeps changes reviewable.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. Run `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

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
     | ux.md     | 12    | 12        | 0          | PASS   |
     | test.md   | 8     | 5         | 3          | FAIL   |
     | security.md | 6   | 6         | 0          | PASS   |
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
   - **IF EXISTS**: Read progress.md for previously discovered patterns and iteration history
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

   - Check if Dockerfile* exists or Docker in plan.md -> create/verify .dockerignore
   - Check if .eslintrc* exists -> create/verify .eslintignore
   - Check if eslint.config.* exists -> ensure the config's `ignores` entries cover required patterns
   - Check if .prettierrc* exists -> create/verify .prettierignore
   - Check if .npmrc or package.json exists -> create/verify .npmignore (if publishing)
   - Check if terraform files (*.tf) exist -> create/verify .terraformignore
   - Check if .helmignore needed (helm charts present) -> create/verify .helmignore

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

5. **Identify the current work unit** (SCOPE CONSTRAINT):
   - Parse tasks.md to find the FIRST section with incomplete tasks (`- [ ]`)
   - Determine the work unit type:
     - If tasks are organized by phases -> work unit = one phase
     - If tasks are organized by user stories -> work unit = one user story
     - Otherwise -> work unit = first logical grouping of incomplete tasks
   - **Record the work unit boundaries** - you will ONLY work within these bounds
   - Example: If "Phase 2: Core Implementation" is the first with incomplete tasks, STOP at Phase 2's end

6. Execute implementation for the CURRENT WORK UNIT ONLY:
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **STOP at work unit boundary**: Do not continue to the next phase/story/group

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. **Progress tracking** - Create/update `progress.md` in FEATURE_DIR:
   - **If `progress.md` does not exist**, create it with header: `# Implementation Progress`
   - **Append an iteration entry** using this format:
     ```markdown
     ## Iteration [N] - [YYYY-MM-DD HH:MM]
     **Work Unit**: [Phase/Story/Task group title]
     **Tasks Completed**:
     - [x] Task ID: description
     - [x] Task ID: description
     **Tasks Remaining in Work Unit**: [count] or "None - work unit complete"
     **Commit**: [git hash] or "No commit - partial progress"
     **Files Changed**:
     - path/to/file.ext (created/modified/deleted)
     **Learnings**:
     - [patterns discovered, gotchas, useful context for future iterations]
     ```
   - **IMPORTANT**: Mark each completed task as `[x]` in tasks.md immediately

9. Error handling:
   - Report progress after each completed task
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging

10. **Work unit completion**:
    - When ALL tasks in the current work unit are complete:
      - Verify implemented features match the original specification
      - Validate that tests pass and coverage meets requirements
      - Confirm the implementation follows the technical plan
      - Create a commit:
        ```
        git add -A
        git commit -m "feat(<feature-name>): <work unit title>"
        ```
    - If only partial progress was made, do NOT commit (next iteration will continue)

11. **Completion signal**:
    - **If ALL tasks in tasks.md are complete** (no `- [ ]` remaining), output exactly:
      ```
      <promise>COMPLETE</promise>
      ```
    - If tasks remain in other work units, end normally (next iteration continues)

Note: This agent is designed for automated iteration loops. It completes one work unit per invocation to prevent context degradation and maintain reviewable change sets. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list.
