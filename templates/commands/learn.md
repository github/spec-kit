---
description: Analyze codebase to update architecture registry (high-level) and local CLAUDE.md files (module-specific conventions)
semantic_anchors:
  - Pattern Mining           # Extract recurring solutions from code
  - ADR                      # Architecture Decision Records, Michael Nygard
  - Code Archaeology         # Understanding existing systems through analysis
  - Conway's Law             # System structure mirrors organization structure
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
User can specify: "all" (full analysis), feature names, or specific directories to analyze.

## Purpose

> **Activated Frameworks**: Pattern Mining for discovery, ADR for decision documentation, Code Archaeology for system understanding.

This command analyzes the existing codebase to learn and document:

1. **High-level patterns** → `/memory/architecture-registry.md`
   - Architectural patterns (repository, service layer, CQRS, etc.)
   - Technology decisions (frameworks, major libraries)
   - Interface contracts between modules
   - Architectural anti-patterns

2. **Local conventions** → `{subdir}/CLAUDE.md`
   - Module-specific coding conventions
   - Naming patterns for that directory
   - Local gotchas and examples
   - Testing conventions for that module

## Outline

### Phase 1: Discovery

1. **Detect project structure**:
   - Identify main source directories: `src/`, `lib/`, `app/`, `packages/`
   - Detect subdirectories that represent distinct modules (frontend/, backend/, api/, shared/, etc.)
   - Look for existing CLAUDE.md files in subdirectories

2. **Load existing registry** (if exists):
   - Read `/memory/architecture-registry.md`
   - Extract already-registered patterns
   - Identify what needs updating

3. **Scan for implemented features**:
   - Look for `specs/*/task-results/` (completed implementations)
   - Extract patterns from plan.md and research.md files

4. **Determine scope**:
   - If user specified "all": Analyze entire codebase
   - If user specified features: Analyze only those features
   - If user specified directories: Analyze those directories
   - Default: Analyze features with task-results but not in registry

### Phase 2: High-Level Pattern Extraction

5. **Extract architectural patterns**:

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

### Phase 3: Local Convention Extraction

6. **For each detected module directory** (frontend/, backend/, api/, etc.):

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

### Phase 4: Generate/Update Files

7. **Update `/memory/architecture-registry.md`**:

   Generate HIGH-LEVEL content only:

   ```markdown
   # Architecture Registry

   > High-level architectural patterns and decisions.
   > For module-specific conventions, see `{module}/CLAUDE.md`.

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

8. **Create/Update `{module}/CLAUDE.md`** for each detected module:

   ```markdown
   # {Module} Development Guidelines

   > Auto-generated by /speckit.learn. Manual additions preserved between markers.

   ## Directory Structure

   ```
   {module}/
   ├── [detected structure]
   ```

   ## Naming Conventions

   | Element | Convention | Example |
   |---------|------------|---------|
   | Files | [pattern] | [example] |
   | Functions | [pattern] | [example] |
   | Components | [pattern] | [example] |

   ## Code Patterns

   ### [Pattern Name]
   ```[lang]
   // Example from codebase
   [actual code snippet]
   ```

   ## Error Handling

   [Module-specific error handling approach]

   ## Testing

   - **Location**: [test file location pattern]
   - **Framework**: [framework]
   - **Pattern**: [describe testing pattern]

   ## Gotchas

   - [Known issue or quirk specific to this module]

   <!-- MANUAL ADDITIONS START -->
   <!-- Add custom guidelines here - they will be preserved -->
   <!-- MANUAL ADDITIONS END -->
   ```

### Phase 5: Review and Apply

9. **Present changes to user**:

   ```markdown
   ## Learn Summary

   ### Architecture Registry Updates
   - [N] patterns added/updated
   - [N] technology decisions documented
   - [N] module contracts defined

   ### Local CLAUDE.md Files
   | Module | Status | Conventions Found |
   |--------|--------|-------------------|
   | frontend/ | Created/Updated | [count] |
   | backend/ | Created/Updated | [count] |

   ### Recommendations
   - [Any inconsistencies to address]
   - [Missing documentation to add manually]

   Apply changes? (yes/no/selective)
   ```

10. **Apply changes** (with user confirmation):
    - Update `/memory/architecture-registry.md`
    - Create/Update each `{module}/CLAUDE.md`
    - Preserve manual additions between markers
    - Log changes made

## Output Files

- `/memory/architecture-registry.md` (high-level patterns)
- `{module}/CLAUDE.md` for each detected module (local conventions)

## Key Principles

- **High-level vs Local**: Architecture registry = cross-cutting, CLAUDE.md = module-specific
- **Extract, don't invent**: Only document patterns actually in use
- **Preserve manual additions**: Never overwrite content between MANUAL markers
- **Non-destructive**: Update, don't replace existing documentation
- **Auto-loaded context**: Local CLAUDE.md files are automatically loaded by Claude Code when working in that directory

## Usage Examples

```bash
# Full codebase analysis
/speckit.learn all

# Learn from specific features
/speckit.learn feat-001-auth feat-002-dashboard

# Analyze specific directories only
/speckit.learn src/frontend src/backend

# Quick update after implementation
/speckit.learn
```

## Integration with Workflow

```
After /speckit.merge:
  /speckit.learn → updates registry + local CLAUDE.md files

During /speckit.implement:
  Claude Code auto-loads {module}/CLAUDE.md when editing files in that module

During /speckit.plan:
  Loads architecture-registry.md for alignment validation
```
