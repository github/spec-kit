---
description: Initialize or migrate project documentation to domain-based /docs structure
semantic_anchors:
  - Code Archaeology         # Understanding existing systems through analysis
  - Domain-Driven Design     # Bounded contexts, ubiquitous language
  - Living Documentation     # Docs evolve with the codebase
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
User can specify: "from-code", "from-docs", "from-specs", or a specific source path.

## Purpose

Initialize the `/docs/{domain}/` structure for a project. This command handles:

1. **Greenfield**: No existing documentation → discover domains from code
2. **From existing docs**: README, wiki, markdown → convert to domain structure
3. **From spec-kit legacy**: `specs/{feature}/` → consolidate into domains
4. **Hybrid**: Combine multiple sources

## Outline

### Phase 1: Discovery

1. **Detect project state**:

   ```bash
   # Check for existing documentation sources
   [ -d "docs" ] && echo "HAS_DOCS"
   [ -d "specs" ] && echo "HAS_SPECS"
   [ -f "README.md" ] && echo "HAS_README"
   [ -d "wiki" ] && echo "HAS_WIKI"
   ```

2. **Analyze codebase structure** (if no docs):

   ```bash
   # Find main source directories
   ls -d src/*/ app/*/ lib/*/ packages/*/ 2>/dev/null

   # Find route/endpoint definitions (domain hints)
   grep -r "router\|@Controller\|@Get\|@Post" --include="*.ts" --include="*.py" -l

   # Find entity/model definitions
   grep -r "class.*Entity\|@Entity\|model\s+" --include="*.ts" --include="*.py" -l
   ```

3. **Inventory existing specs** (if `specs/` exists):

   ```bash
   # List all feature specs
   ls specs/*/spec.md 2>/dev/null

   # Count features
   ls -d specs/*/ 2>/dev/null | wc -l
   ```

4. **Report findings**:

   ```markdown
   ## Project Analysis

   ### Sources Found
   | Source | Status | Items |
   |--------|--------|-------|
   | Code | ✓/✗ | {n} modules |
   | specs/ | ✓/✗ | {n} features |
   | README.md | ✓/✗ | - |
   | docs/ | ✓/✗ | {n} files |

   ### Suggested Domains (from analysis)
   | Domain | Evidence | Features/Modules |
   |--------|----------|------------------|
   | {domain} | {why suggested} | {what belongs} |
   ```

### Phase 2: Domain Mapping

5. **If from code** (greenfield):

   a. Analyze code structure for domain boundaries:
      - Route groups → domain hints (e.g., `/api/auth/*` → `auth`)
      - Module folders → domain hints (e.g., `src/payments/` → `payments`)
      - Entity clusters → domain hints (e.g., User, Role, Permission → `auth`)

   b. Suggest domain groupings:
      ```markdown
      ## Suggested Domain Structure

      ### auth
      - Modules: src/auth/, src/users/
      - Entities: User, Role, Permission, Session
      - Routes: /api/auth/*, /api/users/*

      ### payments
      - Modules: src/payments/, src/billing/
      - Entities: Payment, Invoice, Subscription
      - Routes: /api/payments/*, /api/billing/*
      ```

   c. Ask user to confirm/modify:
      ```markdown
      Accept this domain structure? (yes/modify)

      To modify, specify:
      - Merge: "merge auth users" → combines into single domain
      - Split: "split payments billing" → separates into two domains
      - Rename: "rename auth to identity"
      - Add: "add admin" → creates new empty domain
      ```

6. **If from existing docs** (README, wiki):

   a. Parse existing documentation:
      - Extract sections/headers as potential domains
      - Identify feature descriptions
      - Extract entity definitions
      - Find API documentation

   b. Map to domains:
      ```markdown
      ## Documentation Analysis

      ### From README.md
      | Section | Suggested Domain | Content Type |
      |---------|------------------|--------------|
      | "Authentication" | auth | Feature description |
      | "API Reference" | (multiple) | API contracts |

      ### Mapping Plan
      - "Authentication" section → docs/auth/spec.md
      - "User Management" section → docs/auth/spec.md (merge)
      - "Payments" section → docs/payments/spec.md
      ```

7. **If from specs/ legacy** (spec-kit migration):

   a. Inventory all features:
      ```markdown
      ## Specs Migration Plan

      | Feature | spec.md | Domain (inferred) | Status |
      |---------|---------|-------------------|--------|
      | 001-user-auth | ✓ | auth | Ready |
      | 002-login-flow | ✓ | auth | Ready |
      | 003-payment-setup | ✓ | payments | Ready |
      | 004-dashboard | ✓ | dashboard | Ready |
      ```

   b. Group by domain:
      ```markdown
      ### Domain: auth
      - 001-user-auth (primary)
      - 002-login-flow (extends)

      ### Domain: payments
      - 003-payment-setup

      ### Domain: dashboard
      - 004-dashboard
      ```

   c. Ask user to confirm groupings

### Phase 3: Generation

8. **Create /docs structure**:

   ```bash
   mkdir -p docs/{domain1} docs/{domain2} ...
   ```

9. **Generate domain specs**:

   For each domain:

   a. **If from code** → Generate skeleton:
      ```markdown
      # {Domain} Specification

      > Source of truth for {domain} functionality.
      > Generated by /speckit.bootstrap on {date}
      > **Status**: Draft - needs review

      ## Overview

      [Auto-extracted from code analysis]

      ## Entities

      ### {Entity}
      > Discovered in: {file path}

      | Field | Type | Description |
      |-------|------|-------------|
      | {field} | {type} | [NEEDS DESCRIPTION] |

      ## API Endpoints

      ### {Endpoint}
      > Discovered in: {file path}

      - **Method**: {method}
      - **Path**: {path}
      - **Description**: [NEEDS DESCRIPTION]

      ## Features

      [No features documented yet - use /speckit.specify to add]

      ---

      > **Next Steps**:
      > 1. Review and complete entity descriptions
      > 2. Document business rules
      > 3. Add features via /speckit.specify → /speckit.merge
      ```

   b. **If from existing docs** → Convert and structure:
      ```markdown
      # {Domain} Specification

      > Source of truth for {domain} functionality.
      > Migrated from {source} on {date}

      ## Overview

      [Extracted from original documentation]

      ## Features

      ### {Feature from original docs}
      > Migrated from: {source section}

      [Content converted to spec format]

      ---
      ```

   c. **If from specs/** → Consolidate features:
      ```markdown
      # {Domain} Specification

      > Source of truth for {domain} functionality.
      > Consolidated from specs/ on {date}

      ## Overview

      [Generated from feature specs]

      ## Features

      ### {Feature 1}
      > Source: specs/001-feature-name/spec.md

      #### User Stories
      [Extracted from spec.md]

      #### Business Rules
      [Extracted from spec.md]

      #### Entities
      [Extracted from data-model.md]

      #### API Contracts
      [Extracted from contracts/]

      ---

      ### {Feature 2}
      > Source: specs/002-other-feature/spec.md

      [...]
      ```

10. **Generate /docs/README.md**:

    ```markdown
    # Project Documentation

    > Auto-generated by /speckit.bootstrap on {date}
    > Source: {from-code|from-docs|from-specs|hybrid}

    ## Domains

    | Domain | Description | Features | Status |
    |--------|-------------|----------|--------|
    | [{domain}]({domain}/spec.md) | {description} | {count} | Draft/Complete |

    ## Quick Links

    - [Architecture Registry](/memory/architecture-registry.md)
    - [Constitution](/memory/constitution.md)

    ## Migration Notes

    {Any notes about what was migrated and what needs review}
    ```

### Phase 4: Validation & Cleanup

11. **Validate generated structure**:

    ```bash
    # Check all domain specs exist
    for domain in $(ls -d docs/*/); do
      [ -f "$domain/spec.md" ] || echo "MISSING: $domain/spec.md"
    done
    ```

12. **Offer to run /speckit.learn** (if from code):

    ```markdown
    Documentation structure created.

    Run /speckit.learn to:
    - Extract architecture patterns
    - Generate module CLAUDE.md files

    Run learn? (yes/no)
    ```

13. **Report completion**:

    ```markdown
    ## Bootstrap Complete

    ### Structure Created
    | Domain | Features | Status |
    |--------|----------|--------|
    | {domain} | {count} | Draft/Complete |

    ### Files Generated
    - docs/README.md
    - docs/{domain}/spec.md (× {n})

    ### Next Steps

    **If from code (Draft specs)**:
    1. Review each docs/{domain}/spec.md
    2. Complete [NEEDS DESCRIPTION] placeholders
    3. Add business rules and constraints
    4. Run /speckit.specify for new features

    **If from specs/ (Migration)**:
    1. Review consolidated domain specs
    2. Archive or delete old specs/ if satisfied
    3. Update workflows to use /speckit.merge

    **For all**:
    - Run /speckit.learn to extract patterns
    - Use /speckit.specify → /speckit.merge for new features
    ```

## Usage Examples

```bash
# Auto-detect and bootstrap
/speckit.bootstrap

# Explicitly from code analysis
/speckit.bootstrap from-code

# From existing documentation
/speckit.bootstrap from-docs README.md

# Migrate from legacy specs/
/speckit.bootstrap from-specs

# From specific directory
/speckit.bootstrap from-docs wiki/

# Hybrid: combine code + existing specs
/speckit.bootstrap from-code from-specs
```

## Key Principles

- **Non-destructive**: Never delete existing files, only create new ones
- **User-confirmed**: Always ask before finalizing domain structure
- **Draft status**: Generated specs marked as "Draft" for review
- **Traceable**: Every generated section includes its source
- **Incremental**: Can be run multiple times to add new domains

## Integration with Workflow

```
Existing project:
  /speckit.bootstrap → Creates /docs/{domain}/spec.md

New features:
  /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
       ↓
  /speckit.merge → Updates /docs/{domain}/spec.md

Pattern learning:
  /speckit.learn → Updates architecture-registry + CLAUDE.md
```
