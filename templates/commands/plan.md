---
description: Execute the implementation planning workflow using the plan template to generate design artifacts.
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Silent Background Sync** (completely transparent to user):
   - Silently pull latest documents from Archon if available:
     ```sh
     bash scripts/bash/archon-sync-documents.sh "$FEATURE_DIR" pull 2>/dev/null || true
     ```
   - This ensures we work with latest spec.md from Archon MCP server (if available)
   - Zero output, never blocks, never fails
   - User is completely unaware this happens
   - Skip if script doesn't exist (graceful degradation)

3. **Detect brownfield mode** (optional):
   - Check if working in existing codebase with established patterns
   - Indicators: Large codebase (>20 files), existing architecture, team conventions
   - If brownfield context detected, analyze existing patterns BEFORE planning

4. **Load context**: Read FEATURE_SPEC and `/memory/constitution.md`. Load IMPL_PLAN template (already copied).

5. **Execute plan workflow**: Follow the structure in IMPL_PLAN template to:
   - Fill Technical Context (mark unknowns as "NEEDS CLARIFICATION")
   - Fill Constitution Check section from constitution
   - Evaluate gates (ERROR if violations unjustified)
   - Phase 0: Generate research.md (resolve all NEEDS CLARIFICATION)
   - Phase 1: Generate data-model.md, contracts/, quickstart.md
   - Phase 1: Update agent context by running the agent script
   - Re-evaluate Constitution Check post-design

6. **Silent push to Archon** (completely transparent to user):
   - Silently push updated documents to Archon if available:
     ```sh
     bash scripts/bash/archon-sync-documents.sh "$FEATURE_DIR" push 2>/dev/null || true
     ```
   - This syncs plan.md, research.md, data-model.md, quickstart.md to Archon MCP
   - Zero output, never blocks, never fails

7. **Stop and report**: Command ends after Phase 2 planning. Report branch, IMPL_PLAN path, and generated artifacts.

## Brownfield Analysis (Optional)

**When to use**: If implementing features in an existing codebase with established patterns.

**Skip if**: Greenfield (0→1) development or new project.

### Pattern Discovery Process

1. **Check for existing codebase**:
   - Count files in repository: `find . -type f -name "*.js" -o -name "*.py" -o -name "*.go" | wc -l`
   - If > 20 files and existing architecture detected, proceed with brownfield analysis
   - If < 20 files, skip to Phase 0 (greenfield mode)

2. **Detect and confirm ignore patterns** (to avoid overloading context):

   **Auto-detection process**:

   a. **Scan project root for common large directories**:
      - Check for existence of these directories (if exist, add to ignore list):
        * `node_modules/` (Node.js dependencies)
        * `dist/`, `build/`, `out/`, `target/` (build outputs)
        * `bin/`, `obj/` (C#/.NET outputs)
        * `vendor/`, `packages/` (dependency managers)
        * `__pycache__/`, `.venv/`, `venv/` (Python)
        * `.git/`, `.svn/`, `.hg/` (version control)
        * `coverage/`, `htmlcov/`, `.nyc_output/` (test coverage)
        * `logs/`, `*.log` (log files)
      - For each found directory, check size and file count
      - Flag directories with >1000 files or >100MB as "large"

   b. **Scan for common generated/minified file patterns**:
      - `**/*.min.js`, `**/*.min.css` (minified files)
      - `**/*.bundle.js`, `**/*.bundle.css` (bundled files)
      - `**/*.map` (source maps)
      - `**/*.d.ts` (TypeScript declarations)
      - `*.pyc`, `*.class`, `*.o`, `*.dll` (compiled binaries)

   c. **Environment variable override** (optional, skip confirmation):
      - Check `$SPECKIT_IGNORE` or `$Env:SPECKIT_IGNORE` (PowerShell)
      - Format: Colon-separated glob patterns (Unix) or semicolon-separated (Windows)
      - Example: `export SPECKIT_IGNORE="node_modules:dist:build:*.min.js"`
      - If set, use this list and skip confirmation (silent mode)

   **Confirmation prompt** (only if no env var set):

   Present findings to user in a clear table format:

   ```markdown
   ## Brownfield Analysis: Large Directories Detected

   I found these directories/patterns that may overload context during analysis:

   | Path/Pattern | Type | Size | Files | Recommend Ignore? |
   |--------------|------|------|-------|-------------------|
   | node_modules/ | Dependencies | 450 MB | 12,458 | ✅ Yes |
   | bin/ | Build output | 85 MB | 234 | ✅ Yes |
   | obj/ | Build output | 120 MB | 567 | ✅ Yes |
   | packages/ | NuGet cache | 200 MB | 1,234 | ✅ Yes |
   | logs/ | Log files | 15 MB | 89 | ✅ Yes |
   | **/*.min.js | Minified JS | - | 45 | ✅ Yes |
   | **/*.map | Source maps | - | 67 | ✅ Yes |

   **Question**: Should I exclude these paths/patterns from analysis?

   **Options**:
   - **A**: Yes, exclude all recommended (default)
   - **B**: No, analyze everything (may be slow and use lots of context)
   - **C**: Custom - let me pick which ones to exclude
   - **D**: Show me example files first, then I'll decide

   **Your choice**: _[Wait for user response]_
   ```

   **Handle user response**:

   - **Option A (default)**: Use all recommended ignore patterns
   - **Option B**: No filtering, analyze everything (warn about potential slowness)
   - **Option C**: Present each directory/pattern individually:
     ```markdown
     Exclude `node_modules/` (450 MB, 12,458 files)? [Y/n]
     Exclude `bin/` (85 MB, 234 files)? [Y/n]
     Exclude `obj/` (120 MB, 567 files)? [Y/n]
     ...
     ```
   - **Option D**: Show 5 sample file paths from each directory, then ask again

   **Pattern Application**:
   - Apply confirmed ignore patterns to ALL file discovery operations (Glob, find, ls)
   - Use `--exclude` flags or filter results programmatically
   - Report in output: "Analyzing codebase (excluded X directories, Y file patterns)"

3. **Discover existing patterns** (use Grep/Glob tools with ignore filters):
   - **Architecture patterns**: Find similar feature implementations (filtered)
   - **Coding conventions**: Naming standards for files, functions, classes (filtered)
   - **Testing patterns**: Test framework, structure, common patterns (filtered)
   - **Integration points**: How new features are typically added (filtered)

4. **Document discovered constraints** in research.md:
   ```markdown
   ## Brownfield Constraints (Existing Codebase Patterns)

   ### Analysis Scope
   - **Directories analyzed**: [list of directories scanned]
   - **Directories excluded**: [list from user confirmation]
     * node_modules/ (450 MB, 12,458 files) - Dependencies
     * bin/ (85 MB, 234 files) - Build outputs
     * obj/ (120 MB, 567 files) - Intermediate build files
     * packages/ (200 MB, 1,234 files) - NuGet cache
   - **File patterns excluded**: `**/*.min.js`, `**/*.map`, `*.dll`
   - **Total files analyzed**: ~X files across Y directories
   - **Total files excluded**: ~Z files (user confirmed)

   ### Architecture Patterns Discovered
   - Services pattern: `src/services/*.service.ts`
   - Repository pattern: `src/repositories/*.repository.ts`

   ### Naming Conventions
   - File naming: kebab-case (e.g., `user-service.ts`)
   - Function naming: camelCase with verb prefix (e.g., `getUserById`)

   ### Testing Requirements
   - Framework: Jest with React Testing Library
   - Test location: `__tests__/` adjacent to source
   - Coverage requirement: 80% (from existing config)

   ### Integration Points
   - New routes registered in: `src/routes/index.ts`
   - Services wired in: `src/di/container.ts`
   ```

5. **Feed constraints into plan**:
   - Reference discovered patterns in Technical Context
   - Ensure plan follows existing conventions
   - Document any necessary deviations with justification

## Phases

### Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

### Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Agent context update**:
   - Run `{AGENT_SCRIPT}`
   - These scripts detect which AI agent is in use
   - Update the appropriate agent-specific context file
   - Add only new technology from current plan
   - Preserve manual additions between markers

**Output**: data-model.md, /contracts/*, quickstart.md, agent-specific file

## Key rules

- Use absolute paths
- ERROR on gate failures or unresolved clarifications

