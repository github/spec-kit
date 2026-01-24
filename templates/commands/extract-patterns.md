---
description: Extract architectural patterns from existing codebase to initialize or update the architecture registry
semantic_anchors:
  - Pattern Mining           # Extract recurring solutions from code
  - ADR                      # Architecture Decision Records, Michael Nygard
  - arc42                    # Architecture documentation template
  - Code Archaeology         # Understanding existing systems through analysis
  - Conway's Law             # System structure mirrors organization structure
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
User can specify: "all" (full extraction), feature names, or specific directories to analyze.

## Purpose

> **Activated Frameworks**: Pattern Mining for discovery, ADR for decision documentation, arc42 for structure, Code Archaeology for system understanding.

This command analyzes the existing codebase to extract architectural patterns, technology decisions, and conventions. Use this to:

1. **Initialize registry**: First-time setup for a project with existing code
2. **Update registry**: Add patterns from features not tracked in registry
3. **Audit consistency**: Detect drift between actual code and registry

## Outline

### Phase 1: Discovery

1. **Scan for existing features**:
   - Look for `specs/*/` directories (implemented features)
   - Look for `specs/*/task-results/` (completed implementations)
   - Check for common source directories: `src/`, `lib/`, `app/`, `packages/`
   - Identify feature boundaries from folder structure

2. **Load existing registry** (if exists):
   - Read `/memory/architecture-registry.md`
   - Extract already-registered patterns
   - Identify gaps (code not in registry)

3. **Determine scope**:
   - If user specified "all": Analyze entire codebase
   - If user specified features: Analyze only those features
   - If user specified directories: Analyze those directories
   - Default: Analyze features with task-results but not in registry

### Phase 2: Pattern Extraction

4. **Analyze code structure**:

   a. **Directory patterns**:
      ```bash
      # Find common directory structures
      ls -d */ 2>/dev/null | head -20
      ls -d src/*/ 2>/dev/null | head -20

      # Identify component types by location
      # services/, repositories/, controllers/, components/, hooks/, etc.
      ```

   b. **File naming conventions**:
      ```bash
      # Find naming patterns
      glob "**/src/**/*.ts" | head -50
      glob "**/src/**/*.tsx" | head -50

      # Extract patterns: PascalCase, camelCase, kebab-case, etc.
      ```

   c. **Code patterns**:
      ```bash
      # Find service patterns
      grep -r "class.*Service" --include="*.ts" | head -20

      # Find repository patterns
      grep -r "Repository\|interface.*Repo" --include="*.ts" | head -20

      # Find hook patterns
      grep -r "export.*function use[A-Z]" --include="*.ts" --include="*.tsx" | head -20

      # Find component patterns
      grep -r "export.*function.*Props" --include="*.tsx" | head -20
      ```

5. **Extract technology decisions**:

   a. **From package files**:
      - Read `package.json` for JS/TS projects
      - Read `build.sbt` for Scala projects
      - Read `go.mod` for Go projects
      - Read `Cargo.toml` for Rust projects
      - Read `requirements.txt` / `pyproject.toml` for Python

   b. **Categorize dependencies**:
      ```markdown
      | Category | Library | Used For |
      |----------|---------|----------|
      | Validation | zod | Schema validation with type inference |
      | State | zustand | Client state management |
      | Data Fetching | @tanstack/query | Server state & caching |
      | Styling | tailwindcss | Utility-first CSS |
      | Testing | vitest | Unit testing |
      ```

6. **Analyze existing features** (from specs/*/):

   a. **For each feature with task-results/**:
      - Read task-results/*.md for patterns documented
      - Read plan.md for technology decisions
      - Read research.md for reuse decisions
      - Identify what was created NEW vs REUSED

   b. **Extract feature patterns**:
      ```markdown
      ## Feature: {feature-name}

      ### Patterns Established
      - [Pattern]: [Files] - [Usage]

      ### Technology Decisions
      - [Category]: [Choice] - [Rationale]

      ### Components Created
      - [Type]: [Location] - [Naming]
      ```

### Phase 3: Cross-Feature Analysis

7. **Detect consistency patterns**:

   a. **Consistent patterns** (used in 2+ features):
      - These become "Established Patterns" in registry
      - Higher confidence in their value

   b. **Inconsistent implementations**:
      - Same problem solved differently across features
      - Flag as potential drift
      - Recommend consolidation

   c. **Anti-patterns discovered**:
      - Code that was refactored or replaced
      - Comments indicating "don't do this"
      - Patterns abandoned mid-feature

8. **Generate drift report**:

   ```markdown
   ## Consistency Analysis

   ### Consistent Patterns (Good)
   | Pattern | Used In | Files |
   |---------|---------|-------|
   | Service Layer | feat-001, feat-002, feat-003 | src/services/*.ts |

   ### Inconsistencies Detected (Drift)
   | Problem | Feature A | Feature B | Recommendation |
   |---------|-----------|-----------|----------------|
   | Validation | Uses Zod | Uses Yup | Standardize on Zod |
   | State | Uses Redux | Uses Zustand | Pick one, migrate |

   ### Potential Anti-Patterns
   | Pattern | Found In | Issue | Fix |
   |---------|----------|-------|-----|
   | Direct DB in routes | feat-001 | Tight coupling | Add repository layer |
   ```

### Phase 4: Registry Generation

9. **Generate registry content**:

   a. **If no registry exists**:
      - Create full `/memory/architecture-registry.md`
      - Populate all sections from extracted data
      - Set version 1.0.0

   b. **If registry exists**:
      - Generate diff: what's missing
      - Propose additions only
      - Do NOT overwrite existing entries

10. **Present to user for review**:

    ```markdown
    ## Architecture Registry Update Proposal

    ### New Patterns to Add ({count})
    [list with source features]

    ### New Technology Decisions to Add ({count})
    [list with rationale]

    ### New Conventions to Add ({count})
    [list with examples]

    ### Inconsistencies Requiring Decision ({count})
    [list with options]

    Apply these changes? (yes/no/selective)
    ```

11. **Apply changes** (with user confirmation):
    - Update `/memory/architecture-registry.md`
    - Log each addition with source
    - Update version and date

### Phase 5: Recommendations

12. **Generate recommendations**:

    ```markdown
    ## Recommendations

    ### Immediate Actions
    1. [High-priority consistency fix]
    2. [Anti-pattern to address]

    ### Future Features
    - Ensure new features check registry FIRST
    - Run /speckit.extract-patterns quarterly

    ### Registry Maintenance
    - Archive deprecated patterns
    - Update examples with better references
    ```

## Output Files

- `/memory/architecture-registry.md` (created or updated)
- `{FEATURE_DIR}/pattern-extraction.md` (analysis report, if analyzing specific feature)

## Key Principles

- **Extract, don't invent**: Only register patterns actually in use
- **Document sources**: Every pattern links to its origin feature
- **Preserve context**: Include rationale, not just the pattern
- **Flag inconsistency**: Highlight drift for user decision
- **Non-destructive**: Never delete existing registry entries

## Usage Examples

```bash
# Initialize registry from entire codebase
/speckit.extract-patterns all

# Extract from specific features
/speckit.extract-patterns feat-001-auth feat-002-forms

# Audit specific directories
/speckit.extract-patterns src/services src/components

# Quick check for drift
/speckit.extract-patterns --audit-only
```

## Integration with Workflow

```
First Feature:
  /speckit.implement → creates code
  /speckit.extract-patterns → initializes registry

Subsequent Features:
  /speckit.plan → loads registry, validates alignment
  /speckit.implement → follows registry, updates it

Periodic:
  /speckit.extract-patterns --audit-only → checks for drift
```
