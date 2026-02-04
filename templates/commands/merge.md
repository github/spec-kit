---
description: Merge feature branch into main and consolidate documentation into /docs
semantic_anchors:
  - Documentation as Code     # Treat docs like code - versioned, reviewed, maintained
  - Single Source of Truth    # One place for each piece of information
  - Living Documentation      # Docs evolve with the codebase
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
User can specify: branch name (default: current branch), or "dry-run" to preview without merging.

## Purpose

This command completes the feature lifecycle by:

1. **Verifying** all tasks are completed
2. **Merging** the feature branch into main
3. **Consolidating** feature documentation into `/docs` (persistent reference)
4. **Optionally** running `/speckit.learn` to update architecture registry and local CLAUDE.md files
5. **Pushing** main to remote

The `/docs` directory becomes the **single source of truth** for business and functional specifications, referenced by future `/speckit.specify` and `/speckit.plan` executions.

## Outline

### Phase 1: Pre-Merge Validation

1. **Identify feature**:
   - Detect current branch or use user-specified branch
   - Extract feature ID from branch name (e.g., `feat/001-user-auth` → `001-user-auth`)
   - Locate feature directory in `specs/{feature-id}/`

2. **Verify completion**:
   - Read `specs/{feature-id}/tasks.md`
   - Check all tasks are marked `[X]` (completed)
   - If incomplete tasks exist → **STOP** and report

3. **Verify artifacts exist**:
   - `spec.md` - Feature specification
   - `plan.md` - Implementation plan
   - `tasks.md` - Task breakdown
   - `task-results/` - At least one result file
   - If missing critical files → **WARN** user

4. **Check git status**:
   - Ensure working directory is clean
   - Ensure branch is up-to-date with remote
   - If dirty or behind → **STOP** and report

### Phase 2: Documentation Consolidation

5. **Ensure /docs structure exists**:

   ```bash
   mkdir -p docs/features docs/domain docs/api
   ```

6. **Extract and consolidate from spec.md → /docs/features/{feature}.md**:

   Create a clean, reusable specification:

   ```markdown
   # {Feature Name}

   > Consolidated from specs/{feature-id}/ on {date}

   ## Overview

   [Extract summary from spec.md]

   ## User Stories

   [Extract user stories with acceptance criteria]

   ## Business Rules

   [Extract any business rules or constraints]

   ## Error Scenarios

   [Extract error handling requirements]

   ## Related Features

   - [Links to dependent/related features in /docs/features/]
   ```

7. **Extract entities from data-model.md → /docs/domain/entities.md**:

   Append new entities (avoid duplicates):

   ```markdown
   ## {Entity Name}

   > Added by feature: {feature-id}

   ### Fields
   | Field | Type | Constraints |
   |-------|------|-------------|

   ### Relationships
   [Entity relationships]

   ### Validation Rules
   [Business validation]
   ```

8. **Extract contracts from contracts/ → /docs/api/**:

   For each contract file:
   - If endpoint already exists → update with changes
   - If new endpoint → add to appropriate API doc
   - Maintain OpenAPI/GraphQL format if present

9. **Update /docs/README.md** (index):

   ```markdown
   # Project Documentation

   > Auto-maintained by /speckit.merge. Last updated: {date}

   ## Features

   | Feature | Status | Added |
   |---------|--------|-------|
   | [{feature}](features/{feature}.md) | Implemented | {date} |

   ## Domain Model

   See [entities.md](domain/entities.md) for the complete data model.

   ## API Reference

   See [api/](api/) for endpoint documentation.
   ```

### Phase 3: Git Operations

10. **Merge into main**:

    ```bash
    # Switch to main
    git checkout main

    # Pull latest
    git pull origin main

    # Merge feature branch (no fast-forward to preserve history)
    git merge --no-ff {feature-branch} -m "feat: {feature-name}

    Merged from specs/{feature-id}/
    - [summary of what was implemented]

    Docs: /docs/features/{feature}.md"
    ```

11. **Commit documentation updates** (if not already included):

    ```bash
    git add docs/
    git commit -m "docs: consolidate {feature-name} into /docs

    - Added docs/features/{feature}.md
    - Updated docs/domain/entities.md
    - Updated docs/api/ contracts"
    ```

### Phase 4: Post-Merge Actions

12. **Offer to run /speckit.learn**:

    ```markdown
    Feature merged successfully.

    Run /speckit.learn to update:
    - Architecture registry (patterns from this feature)
    - Local CLAUDE.md files (module conventions)

    Run learn? (yes/no)
    ```

    If yes → execute `/speckit.learn {feature-id}`

13. **Push to remote**:

    ```bash
    git push origin main
    ```

14. **Cleanup (optional)**:

    Ask user:
    ```markdown
    Delete feature branch locally and remotely?
    - Local: {feature-branch}
    - Remote: origin/{feature-branch}

    Delete? (yes/no/local-only)
    ```

### Phase 5: Summary

15. **Report completion**:

    ```markdown
    ## Merge Complete

    ### Git
    - Branch: {feature-branch} → main
    - Commit: {commit-hash}
    - Pushed: Yes

    ### Documentation Updated
    | File | Action |
    |------|--------|
    | docs/features/{feature}.md | Created |
    | docs/domain/entities.md | Updated (+{n} entities) |
    | docs/api/{endpoint}.md | Updated |
    | docs/README.md | Updated |

    ### Architecture (if learn was run)
    - Registry: {n} patterns added
    - CLAUDE.md: {modules} updated

    ### Next Steps
    - Review /docs/features/{feature}.md for accuracy
    - Start next feature with /speckit.specify
    ```

## Output Files

- `/docs/features/{feature}.md` - Consolidated feature specification
- `/docs/domain/entities.md` - Updated entity definitions
- `/docs/api/*.md` - Updated API contracts
- `/docs/README.md` - Updated index

## Key Principles

- **Consolidate, don't duplicate**: Extract essence, not copy verbatim
- **Single source of truth**: /docs becomes THE reference for business specs
- **Preserve history**: Use --no-ff merge to keep feature branch history
- **Living documentation**: Each merge enriches the project knowledge base
- **Clean working specs**: specs/{feature}/ remains as working directory, /docs/ is the clean reference

## Usage Examples

```bash
# Merge current branch
/speckit.merge

# Merge specific branch
/speckit.merge feat/001-user-auth

# Preview without merging
/speckit.merge dry-run

# Merge and run learn
/speckit.merge --learn
```

## Integration with Workflow

```
/speckit.specify  → Creates specs/{feature}/spec.md
/speckit.plan     → Creates plan.md, contracts/, data-model.md
/speckit.tasks    → Creates tasks.md
/speckit.implement → Creates task-results/

/speckit.merge    → Consolidates into /docs, merges to main
                  → /docs/ now contains business specs for this feature

Next feature:
/speckit.specify  → Reads /docs/ for context and consistency
/speckit.plan     → Reads /docs/ + architecture-registry.md
```

## Dry Run Mode

When `dry-run` is specified:

1. Show what would be merged
2. Show what documentation would be created/updated
3. Show diff preview of /docs changes
4. Do NOT execute any git commands
5. Do NOT write any files

```markdown
## Dry Run Preview

### Would Merge
- {feature-branch} → main

### Would Create/Update
| File | Action | Preview |
|------|--------|---------|
| docs/features/{feature}.md | Create | [show excerpt] |
| docs/domain/entities.md | Append | [show new entities] |

### Would NOT Do
- No git operations
- No file writes

Run without dry-run to execute.
```
