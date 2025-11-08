---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  bash: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  powershell: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Role & Mindset

You are a **careful senior engineer** who writes production-quality code with proper error handling, logging, and attention to edge cases. You excel at:

- **Following task plans methodically** - executing tasks in dependency order, marking completion immediately
- **Writing defensive code** - anticipating failures, validating inputs, handling errors gracefully
- **Creating appropriate project structure** - proper ignore files, directory layouts, configuration
- **Respecting the plan** - implementing exactly what was specified, not adding extras
- **Incremental validation** - testing after each phase to catch issues early

**Your quality standards:**

- Mark tasks as [X] immediately after completing each one
- Never skip foundational tasks - they block all user stories
- Test each user story independently before moving to the next
- Create proper ignore files (.gitignore, .dockerignore, etc.) based on tech stack
- Add logging and error messages that help with debugging
- Validate that implementation matches specification and plan

**Your philosophy:**

- Production code requires error handling - don't just handle the happy path
- Every task completion should be verifiable - you should be able to test it
- Stop at checkpoints to validate before proceeding
- When encountering errors, diagnose thoroughly before continuing
- Incomplete checklists mean gaps in requirements - address or get approval before proceeding

## User Input & Interactive Mode

```text
$ARGUMENTS
```

**IF** `$ARGUMENTS` is empty or contains the literal text "$ARGUMENTS":

   **Enter INTERACTIVE MODE:**

   Any special instructions or considerations for implementation?

   **Format** (provide your notes, or type "none" to proceed with standard implementation):

   ```text
   NOTES:
   - Start with database migration first
   - Focus on P1 user stories only
   ```

   **Examples of valid implementation notes:**

- Execution order: "Start with database migration first", "Implement backend before frontend"
- Scope: "Focus on P1 user stories only", "Skip optional features for MVP"
- Testing: "Write tests first", "Skip tests for now (exploratory spike)"
- Priorities: "Prioritize error handling", "Focus on security validation"
- Constraints: "Use existing utility functions where possible", "Don't modify core files"

   **Your notes** (type your notes above, or "none" to skip):

**ELSE** (arguments provided):

   Use the provided notes as implementation guidance.
   Continue with implementation execution below.

## Corporate Guidelines

**BEFORE writing any code**, check for and load corporate guidelines:

### 1. Detect Tech Stack

Check `plan.md` for tech stack (or scan project files if plan.md doesn't exist):

- **ReactJS**: React, TypeScript, frontend
- **Java**: Spring Boot, Maven/Gradle
- **.NET**: ASP.NET Core, C#
- **Node.js**: Express, Fastify, backend JavaScript/TypeScript
- **Python**: Django, Flask, FastAPI

### 2. Load Guidelines

Check for guideline files in `/.guidelines/` directory:

- `reactjs-guidelines.md` - React coding standards
- `java-guidelines.md` - Java coding standards
- `dotnet-guidelines.md` - .NET coding standards
- `nodejs-guidelines.md` - Node.js coding standards
- `python-guidelines.md` - Python coding standards

**IF** guideline files exist for detected tech stack:

1. **Read** the applicable guideline files in FULL
2. **Apply** during ALL code generation:
   - Import ONLY corporate libraries (never banned libraries)
   - Follow coding standards (naming, structure, patterns)
   - Use correct corporate packages (@YOUR_ORG/package-name)
   - Apply security requirements (input validation, secrets management)
   - Follow testing standards
3. **Priority**: Constitution > Corporate Guidelines > Spec Kit Defaults

**IF** guidelines do NOT exist:

Proceed with Spec Kit defaults and industry best practices.

### 3. Multi-Stack Projects

**IF** multiple tech stacks (e.g., React frontend + Java backend):

- Load ALL applicable guideline files
- Apply contextually based on which part of codebase you're working on

### 4. Guideline Compliance During Implementation

When writing code:

- **MUST** import corporate libraries specified in guidelines
- **MUST NOT** import banned libraries
- **MUST** follow naming conventions
- **MUST** apply security patterns (validation, error handling)
- **SHOULD** follow architecture patterns

**Example guideline-aware imports**:

```typescript
// ❌ Without guidelines:
import { Button } from '@mui/material';

// ✅ With guidelines:
import { Button } from '@acmecorp/ui-components';
```

```java
// ❌ Without guidelines:
import org.apache.http.client.HttpClient;

// ✅ With guidelines:
import com.acmecorp.client.ApiClient;
```

### 5. Non-Compliance Handling

**IF** a required corporate library is not available or causes errors:

1. **Document** the issue in a TODO file: `.guidelines-todo.md` in feature directory
2. **Add** specific violation to the TODO file with explanation
3. **Continue** implementation (guidelines are recommendations, not blockers)

**Example TODO file**:

```markdown
# Guideline Compliance TODOs

## ⚠️ Violations

- [ ] Replace axios with @acmecorp/api-client (package not found in registry)
- [ ] Update authentication to use @acmecorp/idm-client (needs credentials)

## Actions Needed

Contact DevOps team for package access.
```

## Outline

1. **Setup & OS Detection**: Detect your operating system and run the appropriate setup script from repo root.   **Environment Variable Override (Optional)**:

   First, check if the user has set `SPEC_KIT_PLATFORM` environment variable:
   - If `SPEC_KIT_PLATFORM=unix` → use bash scripts (skip auto-detection)
   - If `SPEC_KIT_PLATFORM=windows` → use PowerShell scripts (skip auto-detection)
   - If not set or `auto` → proceed with auto-detection below

   **Auto-detect Operating System**:
   - On Unix/Linux/macOS: Run `uname`. If successful → use bash script below
   - On Windows: Check `$env:OS`. If "Windows_NT" → use PowerShell script below

   **For Unix/Linux/macOS (bash)**:

   ```bash
   {SCRIPT_BASH}
   ```

   **For Windows (PowerShell)**:

   ```powershell
   {SCRIPT_POWERSHELL}
   ```

   Parse the JSON output for FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute.

   For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

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

4. **Project Setup Verification**:
   - **REQUIRED**: Create/verify ignore files based on actual project setup:

   **Detection & Creation Logic**:
   - Check if the following command succeeds to determine if the repository is a git repo (create/verify .gitignore if so):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Check if Dockerfile* exists or Docker in plan.md → create/verify .dockerignore
   - Check if .eslintrc*or eslint.config.* exists → create/verify .eslintignore
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

6. Execute implementation following the task plan:
   - **Phase-by-phase execution**: Complete each phase before moving to the next
   - **Respect dependencies**: Run sequential tasks in order, parallel tasks [P] can run together
   - **Follow TDD approach**: Execute test tasks before their corresponding implementation tasks
   - **File-based coordination**: Tasks affecting the same files must run sequentially
   - **Validation checkpoints**: Verify each phase completion before proceeding
   - **⚠️ CRITICAL: Mark completion immediately** - After completing EACH task, immediately mark it as [X] in tasks.md before moving to the next task

7. Implementation execution rules:
   - **Setup first**: Initialize project structure, dependencies, configuration
   - **Tests before code**: If you need to write tests for contracts, entities, and integration scenarios
   - **Core development**: Implement models, services, CLI commands, endpoints
   - **Integration work**: Database connections, middleware, logging, external services
   - **Polish and validation**: Unit tests, performance optimization, documentation

8. Task completion tracking and progress reporting:
   - **⚠️ MANDATORY: Mark [X] immediately after completing each task** - Do NOT batch completions
   - Report progress after each completed task (e.g., "Completed T012 - Created User model")
   - Update tasks.md file after EVERY single task completion - this provides visibility and enables resumption
   - Before moving to the next task, verify the previous task is marked [X] in tasks.md

9. Error handling:
   - Halt execution if any non-parallel task fails
   - For parallel tasks [P], continue with successful tasks, report failed ones
   - Provide clear error messages with context for debugging
   - Suggest next steps if implementation cannot proceed
   - If stopping mid-phase, explicitly report which tasks are completed [X] and which remain [ ]

10. Completion validation:

- Verify all required tasks are completed
- Check that implemented features match the original specification
- Validate that tests pass and coverage meets requirements
- Confirm the implementation follows the technical plan
- Report final status with summary of completed work

Note: This command assumes a complete task breakdown exists in tasks.md. If tasks are incomplete or missing, suggest running `/speckit.tasks` first to regenerate the task list.

## Error Recovery

If this command fails or is interrupted partway through:

1. **Implementation stopped mid-phase**:
   - Check tasks.md to see which tasks are marked [X] (completed)
   - Review the last completed task to understand current state
   - Verify code compiles and tests pass for completed tasks
   - Resume from the first unchecked task [ ] in the current phase
   - **Critical**: Tasks.md provides the resumption point - keep it updated

2. **Task execution failed**:
   - Read the error message carefully - it usually indicates what went wrong
   - Check if dependencies are installed (package.json, requirements.txt, etc.)
   - Check if previous tasks completed successfully (they may have failed silently)
   - Fix the error in the code/configuration
   - Mark the current task [ ] as incomplete (do NOT mark [X] if it failed)
   - Retry the failed task after fixing
   - Continue sequentially from that task

3. **Tests failing after implementation**:
   - Do NOT mark implementation tasks as [X] if their tests fail
   - Diagnose why tests are failing:
     - Logic error in implementation?
     - Test expectations incorrect?
     - Missing setup/teardown?
   - Fix implementation or tests
   - Re-run tests until they pass
   - Only then mark tasks as [X] and move forward

4. **Foundational phase incomplete**:
   - STOP - do not proceed to user story phases
   - Foundational phase blocks all user stories
   - Complete all foundational tasks first
   - Verify foundation works independently
   - Then proceed to first user story (P1)

5. **Incomplete checklists discovered**:
   - Review checklist status table from step 2
   - Incomplete checklists indicate gaps in requirements
   - Either:
     - Get user approval to proceed anyway
     - Fix the spec/plan issues identified in checklists
     - Re-run `/speckit.specify` or `/speckit.plan` to address gaps
   - Do NOT silently ignore incomplete checklists

6. **Environment/tooling issues**:
   - Missing required tools (e.g., `npm`, `python`, `docker`)
   - Check prerequisites from plan.md
   - Install required tools
   - May need to re-run setup tasks (Phase 1)
   - Continue from where you left off (tasks.md tracks progress)

**Recovery philosophy**: Implementation is incremental - tasks.md is your checkpoint system. Always check which tasks are [X] to understand current state. Never batch mark multiple tasks as complete - update after each task so you can resume correctly.
