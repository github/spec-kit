---
description: Analyze codebase and specs to update architecture registry, project state context, and local __AGENT_CONTEXT_FILE__ files (module and sub-module conventions)
semantic_anchors:
  - Pattern Mining           # Extract recurring solutions from code
  - ADR                      # Architecture Decision Records, Michael Nygard
  - Code Archaeology         # Understanding existing systems through analysis
  - Conway's Law             # System structure mirrors organization structure
  - Traceability             # Link specifications to implementation artifacts
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
User can specify: "all" (full analysis), feature names, specific directories to analyze, or "specs-only" / "modules-only" for partial updates.

## Purpose

> **Activated Frameworks**: Pattern Mining for discovery, ADR for decision documentation, Code Archaeology for system understanding, Traceability for spec-to-code linking.

This command analyzes the existing codebase and specifications to learn and document:

1. **High-level patterns** → `/memory/architecture-registry.md`
   - Architectural patterns (repository, service layer, CQRS, etc.)
   - Technology decisions (frameworks, major libraries)
   - Interface contracts between modules
   - Architectural anti-patterns

2. **Project state context** → `specs/__AGENT_CONTEXT_FILE__`
   - Domain vocabulary (canonical terms across all features)
   - Data model state (all entities from all features)
   - Active interface contracts (all APIs, events, shared types)
   - Feature dependency graph
   - Business invariants extracted from specs
   - Cross-cutting concerns (auth patterns, error formats)

3. **Module conventions** → `{module}/__AGENT_CONTEXT_FILE__`
   - Module-specific coding conventions
   - Interface contracts (exposed and consumed APIs)
   - Business invariants from specs that affect this module
   - State machines / lifecycle rules
   - Guard rails (DO NOT rules)
   - Module dependency graph (internal and external)
   - Testing conventions for that module

4. **Sub-module conventions** → `{module}/{subdir}/__AGENT_CONTEXT_FILE__`
   - Layer-specific patterns (service layer vs controller vs repository)
   - Function signatures and their spec sources
   - Injected dependencies
   - Expected error types and handling patterns
   - Only generated for directories exceeding complexity threshold

## Outline

### Phase 1: Discovery

1. **Detect project structure**:
   - Identify main source directories: `src/`, `lib/`, `app/`, `packages/`
   - Detect subdirectories that represent distinct modules (frontend/, backend/, api/, shared/, etc.)
   - Look for existing __AGENT_CONTEXT_FILE__ files in subdirectories

2. **Load existing registry** (if exists):
   - Read `/memory/architecture-registry.md`
   - Extract already-registered patterns
   - Identify what needs updating

3. **Scan for implemented features**:
   - Look for `specs/*/task-results/` (completed implementations)
   - Extract patterns from plan.md and research.md files

4. **Scan specs for project state**:
   - Read all `specs/*/spec.md` for domain vocabulary, entities, user stories, invariants
   - Read all `specs/*/data-model.md` for entity definitions and relationships
   - Read all `specs/*/contracts/` for API and event contracts
   - Read all `specs/*/plan.md` for architecture decisions, cross-feature dependencies
   - Load existing `specs/__AGENT_CONTEXT_FILE__` (if exists) to identify what needs updating

5. **Evaluate sub-module complexity**:
   - For each module directory, inspect subdirectories:
     - Count source files (exclude tests, configs, generated files)
     - Count exported functions/classes/types
     - Check if directory name matches a known architectural layer
   - Record results for Phase 5 threshold evaluation

6. **Determine scope**:
   - If user specified "all": Analyze entire codebase and all specs
   - If user specified "specs-only": Only update `specs/__AGENT_CONTEXT_FILE__` (skip module analysis)
   - If user specified "modules-only": Only update module/sub-module files (skip specs context)
   - If user specified features: Analyze only those features
   - If user specified directories: Analyze those directories
   - Default: Analyze features with task-results but not in registry

### Phase 2: Specs Context Extraction

> **Purpose**: Build the project-state snapshot that guides agents working in `specs/`.
> This is NOT a duplicate of `/memory/constitution.md`. Constitution = governance rules (WHAT specs must include). Specs context = project state (WHAT exists in this project right now).

7. **Extract project-wide state from all feature specs**:

   **Skip this phase** if: `specs/` directory is empty or doesn't exist. Log: "No feature specs found — skipping specs context generation. Run `/speckit.learn` again after your first feature is specified."

   a. **Domain Vocabulary**:
      - Scan all `specs/*/spec.md` for entity names, business terms, acronyms
      - Scan all `specs/*/data-model.md` for entity definitions and field names
      - Cross-reference with `/docs/*/spec.md` (consolidated docs) if they exist
      - Build canonical term table: term → definition → source spec
      - Flag conflicting definitions across specs (same term, different meaning)
      - Identify aliases to prohibit (e.g., "Client" vs canonical "User")

   b. **Data Model State**:
      - Aggregate all entities from `specs/*/data-model.md`
      - For each entity: name, key fields, relationships, which feature owns it
      - Mark entity status:
        - ACTIVE: entity exists in code (found in source files)
        - PLANNED: entity is in spec but not yet implemented
        - DEPRECATED: entity was in spec but is no longer referenced
      - Identify shared entities (referenced by multiple features)
      - Document change impact for shared entities

   c. **Active Interface Contracts**:
      - Aggregate all contracts from `specs/*/contracts/`
      - For each endpoint/event: method, path/name, request/response types, owning feature
      - Group by: REST APIs, Events, Shared Types
      - Identify contract conflicts or overlaps across features
      - Mark status: ACTIVE (in code) or PLANNED (in spec only)

   d. **Feature Dependency Graph**:
      - Extract from each feature's spec.md: "Requires" and "Enables" sections (from feature-template.md)
      - Extract from each feature's plan.md: cross-feature dependencies
      - Build adjacency list: feature → [depends-on features]
      - Mark feature status: COMPLETE / IN_PROGRESS / PLANNED
      - **Detect circular dependencies** → flag as warnings

   e. **Business Invariants**:
      - Extract from `specs/*/spec.md`: functional requirements with MUST / MUST NOT language
      - Extract from `specs/*/spec.md`: acceptance criteria (Given/When/Then) that encode rules
      - Cross-reference with `/memory/constitution.md` Specification Principles
      - Categorize:
        - **Data invariants**: constraints on entity state (uniqueness, ranges, formats)
        - **Workflow invariants**: rules about state transitions and ordering
        - **Security invariants**: auth requirements, data protection, access control
      - Assign IDs: DI-{N}, WI-{N}, SI-{N}

   f. **Cross-Cutting Concerns**:
      - Scan codebase for auth patterns (middleware, decorators, guards, interceptors)
      - Scan for error response formats (shared error types, HTTP status conventions)
      - Scan for validation patterns (where validation happens, what library)
      - Scan for logging patterns (structured logging, log levels, correlation IDs)
      - Document each with: pattern name, file reference, applicable scope

### Phase 3: High-Level Pattern Extraction

8. **Extract architectural patterns**:

   a. **Layer patterns**:
      - Service layer, repository pattern, controller pattern
      - Domain-driven design patterns (if present)
      - Event-driven patterns, CQRS (if present)

   b. **Interface contracts**:
      - API contracts between modules (how frontend calls backend)
      - Event schemas (if event-driven)
      - Shared types between modules

   c. **Technology decisions**:
      - From package.json/requirements.txt/go.mod/Cargo.toml
      - Categorize by: framework, validation, state, data fetching, styling, testing
      - Document rationale from research.md files if available

   d. **Architectural anti-patterns**:
      - Patterns that were refactored or abandoned
      - Cross-cutting concerns handled incorrectly
      - Tight coupling between modules

### Phase 4: Module Convention Extraction

9. **For each detected module directory** (frontend/, backend/, api/, etc.):

   a. **Analyze directory structure**:
      ```bash
      # Find subdirectory patterns
      ls -d {module}/*/ 2>/dev/null
      ```

   b. **Extract naming conventions**:
      - File naming patterns (PascalCase, camelCase, kebab-case)
      - Component/function naming patterns
      - Test file patterns

   c. **Extract code patterns**:
      ```bash
      # Services
      grep -r "class.*Service\|export.*Service" {module}/ --include="*.ts" | head -10

      # Components (React)
      grep -r "export.*function\|export default" {module}/ --include="*.tsx" | head -10

      # Hooks
      grep -r "function use[A-Z]" {module}/ --include="*.ts" --include="*.tsx" | head -10
      ```

   d. **Extract error handling patterns**:
      - Try-catch patterns
      - Error boundary usage
      - Result types

   e. **Extract testing conventions**:
      - Test file location (__tests__/, *.test.ts, *.spec.ts)
      - Test framework used
      - Mocking patterns

   f. **Extract interface contracts for this module**:
      - Scan for exported functions/classes/endpoints (public API of the module)
      - Cross-reference with `specs/*/contracts/` to find which spec defines them
      - Scan imports from other project modules to identify consumed interfaces
      - Document: interface name, type (REST/Function/Event), signature, consumers/providers, spec source

   g. **Extract business invariants affecting this module**:
      - From specs that reference files in this module (via plan.md file paths or task-results/)
      - From acceptance criteria that test behavior implemented in this module
      - Document as: invariant ID (from Phase 2), enforcement mechanism in this module

   h. **Extract state machines / lifecycle rules**:
      - Scan for enum types representing states (e.g., `enum OrderStatus`)
      - Scan for transition functions or state pattern implementations
      - Look for status/state fields in data models
      - Cross-reference with spec.md state transition descriptions
      - Document: entity, states, valid transitions, invalid transitions, spec source

   i. **Extract guard rails (DO NOT rules)**:
      - From architecture-registry.md anti-patterns relevant to this module
      - From task-results/ lessons learned mentioning this module
      - From constitution.md development principles that apply to this module's domain
      - Document as: what is prohibited, why, source

   j. **Build module dependency graph**:
      - Internal: which other project modules does this module import from/export to
      - External: which third-party packages does this module depend on
      - Spec-sourced: which specs define requirements for this module

### Phase 5: Sub-Module Analysis

10. **For each module, evaluate sub-directories for granular context**:

    a. **Complexity threshold evaluation**:

       Generate a sub-module __AGENT_CONTEXT_FILE__ only when ANY of:
       - Source file count ≥ 8 files (excluding tests, configs, generated files), OR
       - Exported symbol count ≥ 15 functions/classes/types, OR
       - Directory name matches a known architectural layer:
         `services/`, `models/`, `controllers/`, `handlers/`, `repositories/`,
         `api/`, `middleware/`, `routes/`, `resolvers/`, `adapters/`, `ports/`

       **DO NOT generate if**:
       - Directory is test-only (`__tests__/`, `tests/`, `test/`)
       - Directory is config-only (`config/`, `.config/`)
       - Directory is generated (`dist/`, `build/`, `node_modules/`, `__pycache__/`)
       - Directory has fewer than 3 source files (regardless of other criteria)
       - Directory is already at depth > 3 levels from project root

    b. **For qualifying sub-directories, extract**:

       - **Layer pattern**:
         - What architectural role does this layer serve (service, repository, controller, etc.)
         - What pattern do files in this directory follow
         - One canonical code example from an existing file

       - **Function signatures with spec sources**:
         - List public functions/methods with their signatures
         - Cross-reference with `specs/*/contracts/` and `specs/*/plan.md`
         - Document: function name, signature (params → return type), spec requirement ID

       - **Injected dependencies**:
         - Constructor injection, parameter injection, module-level imports
         - For each: what it provides, where it comes from (module or package)

       - **Expected errors**:
         - Error types raised/returned by functions in this directory
         - Error handling patterns specific to this layer
         - Cross-reference with spec.md error scenarios

       - **Layer-specific guard rails**:
         - Rules specific to this architectural layer
         - Example: "Services MUST NOT access database directly — use repositories"
         - Example: "Controllers MUST NOT contain business logic"

### Phase 6: Generate/Update Files

11. **Update `/memory/architecture-registry.md`**:

    Generate HIGH-LEVEL content only:

    ```markdown
    # Architecture Registry

    > High-level architectural patterns and decisions.
    > For module-specific conventions, see `{module}/__AGENT_CONTEXT_FILE__`.
    > For project state context, see `specs/__AGENT_CONTEXT_FILE__`.

    ## Architectural Patterns

    | Pattern | Description | Modules Using | Interface |
    |---------|-------------|---------------|-----------|
    | [pattern] | [what it solves] | [which modules] | [key interfaces] |

    ## Technology Stack

    | Category | Technology | Rationale |
    |----------|------------|-----------|
    | [category] | [tech] | [why chosen] |

    ## Module Contracts

    ### {Module A} ↔ {Module B}
    - **Interface**: [how they communicate]
    - **Contract**: [API/events/shared types]
    - **Location**: [file path]

    ## Architectural Anti-Patterns

    | Anti-Pattern | Issue | Correct Approach |
    |--------------|-------|------------------|
    | [what to avoid] | [why bad] | [what to do instead] |
    ```

12. **Create/Update `specs/__AGENT_CONTEXT_FILE__`**:

    Use template structure from `templates/specs-context-template.md`.
    Fill sections from Phase 2 extraction results.
    Preserve content between `<!-- MANUAL ADDITIONS START -->` and `<!-- MANUAL ADDITIONS END -->` markers.

    **If specs/ is empty**: Skip this step (logged in Phase 2).

13. **Create/Update `{module}/__AGENT_CONTEXT_FILE__`** for each detected module:

    Use template structure from `templates/module-claude-template.md`.
    Fill existing sections (Overview, Structure, Naming, Patterns, Components, Error Handling, Testing, Dependencies, Gotchas, Related Modules) from Phase 4 steps 9a-9e.
    Fill new sections (Interface Contracts, Business Invariants, State Machines, Guard Rails, Module Dependency Graph) from Phase 4 steps 9f-9j.
    Preserve content between `<!-- MANUAL ADDITIONS START -->` and `<!-- MANUAL ADDITIONS END -->` markers.

    ```markdown
    # {Module} Development Guidelines

    > Auto-generated by /speckit.learn. Manual additions preserved between markers.

    ## Directory Structure
    [from step 9a]

    ## Naming Conventions
    [from step 9b]

    ## Code Patterns
    [from step 9c]

    ## Error Handling
    [from step 9d]

    ## Testing
    [from step 9e]

    ## Interface Contracts
    [from step 9f — exposed and consumed interfaces with spec sources]

    ## Business Invariants
    [from step 9g — invariant rules this module must enforce]

    ## State Machines & Lifecycle Rules
    [from step 9h — entities with state transitions, valid/invalid transitions]

    ## Guard Rails
    [from step 9i — DO NOT rules specific to this module]

    ## Module Dependency Graph
    [from step 9j — internal modules, external packages, spec sources]

    ## Gotchas
    [from step 9e + discovered issues]

    <!-- MANUAL ADDITIONS START -->
    <!-- MANUAL ADDITIONS END -->
    ```

14. **Create/Update `{module}/{subdir}/__AGENT_CONTEXT_FILE__`** for qualifying sub-directories:

    Only for directories that passed Phase 5 threshold evaluation.
    Generate with this structure (no separate template — content varies by layer type):

    ```markdown
    # {SubDir} Layer Guidelines

    > Auto-generated by /speckit.learn on {DATE}
    > Layer: {layer_type} | Parent module: {module_path}
    > Manual additions preserved between markers.

    ## Layer Pattern

    **Role**: {what this layer does}
    **Convention**: {the pattern files follow}

    ```{lang}
    // Canonical example from codebase
    {actual code snippet}
    ```

    **File reference**: `{example_file_path}`

    ## Function Signatures & Spec Sources

    | Function/Method | Signature | Spec Requirement |
    |----------------|-----------|------------------|
    | {function} | {params} → {return} | specs/{feature}/spec.md: {FR-xxx} |

    ## Injected Dependencies

    | Dependency | Type | Provided By |
    |-----------|------|-------------|
    | {dep} | {interface_or_class} | {source_module_or_config} |

    ## Expected Errors

    | Error Type | When Raised | Handling Pattern |
    |-----------|-------------|------------------|
    | {error} | {condition} | {how callers should handle} |

    ## Guard Rails

    - DO NOT {layer-specific rule}

    <!-- MANUAL ADDITIONS START -->
    <!-- MANUAL ADDITIONS END -->
    ```

    Preserve content between MANUAL ADDITIONS markers if file already exists.

### Phase 7: Review and Apply

15. **Present changes to user**:

    ```markdown
    ## Learn Summary

    ### Architecture Registry Updates
    - [N] patterns added/updated
    - [N] technology decisions documented
    - [N] module contracts defined

    ### Specs Context (specs/__AGENT_CONTEXT_FILE__)
    | Section | Items | Status |
    |---------|-------|--------|
    | Domain Vocabulary | [count] terms | Created/Updated |
    | Data Model State | [count] entities | Created/Updated |
    | Interface Contracts | [count] endpoints/events | Created/Updated |
    | Feature Dependencies | [count] edges | Created/Updated |
    | Business Invariants | [count] rules | Created/Updated |
    | Cross-Cutting Concerns | [count] patterns | Created/Updated |

    ### Module __AGENT_CONTEXT_FILE__ Files
    | Module | Status | Conventions | Contracts | Invariants | Guard Rails |
    |--------|--------|-------------|-----------|------------|-------------|
    | backend/ | Created/Updated | [count] | [count] | [count] | [count] |
    | frontend/ | Created/Updated | [count] | [count] | [count] | [count] |

    ### Sub-Module __AGENT_CONTEXT_FILE__ Files
    | Sub-Module | Threshold Met | Items |
    |------------|---------------|-------|
    | backend/src/services/ | 12 files, layer match | [count] |
    | backend/src/models/ | layer match | [count] |

    ### Cross-Spec Warnings
    - [Conflicting vocabulary across specs]
    - [Circular feature dependencies detected]
    - [Overlapping contract definitions]

    ### Recommendations
    - [Missing documentation to add manually]
    - [Suggested MANUAL ADDITIONS]

    Apply changes? (yes/no/selective)
    ```

16. **Apply changes** (with user confirmation):
    - Update `/memory/architecture-registry.md`
    - Create/Update `specs/__AGENT_CONTEXT_FILE__`
    - Create/Update each `{module}/__AGENT_CONTEXT_FILE__`
    - Create/Update qualifying `{module}/{subdir}/__AGENT_CONTEXT_FILE__`
    - Preserve manual additions between markers in all files
    - Log changes made

## Output Files

- `/memory/architecture-registry.md` (high-level architectural patterns)
- `specs/__AGENT_CONTEXT_FILE__` (project state context for spec agents)
- `{module}/__AGENT_CONTEXT_FILE__` for each detected module (module conventions + contracts + invariants)
- `{module}/{subdir}/__AGENT_CONTEXT_FILE__` for qualifying sub-directories (layer-specific context)

## Key Principles

- **High-level vs Local**: Architecture registry = cross-cutting patterns, module files = module-specific, specs context = project state
- **Specs context ≠ Constitution**: Constitution = governance rules (WHAT specs must include). Specs context = project state (WHAT exists in this project right now)
- **Extract, don't invent**: Only document patterns, contracts, and invariants actually present in code/specs
- **Aggregate, don't duplicate**: Specs context aggregates from individual specs; it does not copy verbatim
- **Preserve manual additions**: Never overwrite content between MANUAL markers
- **Non-destructive**: Update, don't replace existing documentation
- **Sub-module is conditional**: Only generate sub-module files when complexity warrants it (threshold: ≥8 files, ≥15 exports, or known layer name)
- **Spec-sourced**: Interface contracts, invariants, and state machines reference their source spec ID
- **Auto-loaded context**: Local __AGENT_CONTEXT_FILE__ files are automatically loaded by the AI agent when working in that directory

## Usage Examples

```bash
# Full codebase + specs analysis
/speckit.learn all

# Learn from specific features
/speckit.learn feat-001-auth feat-002-dashboard

# Analyze specific directories only
/speckit.learn src/frontend src/backend

# Update only the specs context file
/speckit.learn specs-only

# Update only module/sub-module files
/speckit.learn modules-only

# Quick update after implementation
/speckit.learn
```

## Integration with Workflow

```
After /speckit.merge:
  /speckit.learn → updates all context files (registry + specs + modules + sub-modules)

During /speckit.specify:
  Agent auto-loads specs/__AGENT_CONTEXT_FILE__ for vocabulary consistency,
  existing entities, active contracts — prevents inventing conflicting terms

During /speckit.plan:
  Loads architecture-registry.md for alignment validation
  Agent auto-loads specs/__AGENT_CONTEXT_FILE__ for contract and invariant awareness

During /speckit.implement:
  Agent auto-loads {module}/__AGENT_CONTEXT_FILE__ when editing files in that module
  Agent auto-loads {module}/{subdir}/__AGENT_CONTEXT_FILE__ for layer-specific guidance
  Contracts and invariants reduce functional drift during coding

During /speckit.clarify:
  Agent auto-loads specs/__AGENT_CONTEXT_FILE__ to ask questions in the right domain vocabulary
```
