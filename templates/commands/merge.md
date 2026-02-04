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

5. **Determine target domain**:

   a. **Check if domain already specified** in spec.md:
      - Look for `**Domain**:` metadata in spec header
      - If found, use that domain

   b. **If no domain specified, infer from context**:
      - Analyze feature name and spec content
      - Suggest a domain name (kebab-case, e.g., `user-auth`, `payments`, `dashboard`)
      - Common domain patterns: auth, users, payments, orders, notifications, settings, etc.

   c. **Confirm with user**:
      ```markdown
      Inferred domain: **{domain}**

      This feature will be consolidated into `/docs/{domain}/spec.md`

      Options:
      - [Enter] Accept suggested domain
      - Type new name to use different domain
      - Type existing domain name to add to existing domain spec
      ```

   d. **List existing domains** for context:
      ```bash
      ls -d docs/*/ 2>/dev/null | xargs -I {} basename {}
      ```

   **NOTE**: Domains are user-defined, not hardcoded. The command suggests but user decides.

6. **Ensure /docs structure exists**:

   ```bash
   mkdir -p docs/{domain}
   ```

7. **Consolidate spec into /docs/{domain}/spec.md** (OpenSpec-style):

   a. **If domain spec doesn't exist** → Create new spec:

   ```markdown
   # {Domain} Specification

   > Source of truth for {domain} functionality.
   > Last updated: {date}

   ## Overview

   [Domain description]

   ## Features

   ### {Feature Name}

   > Added: {date} | Source: specs/{feature-id}/

   #### User Stories

   [Extract user stories with acceptance criteria]

   #### Business Rules

   [Extract any business rules or constraints]

   #### Entities

   [Extract entities from data-model.md]

   #### API Contracts

   [Extract from contracts/]

   ---
   ```

   b. **If domain spec exists** → Merge delta (like OpenSpec):

   - **ADDED**: Append new feature section
   - **MODIFIED**: Update existing feature section (mark changes)
   - **REMOVED**: Delete feature section (rare, requires confirmation)

   Mark modifications:
   ```markdown
   ### {Feature Name}

   > Added: {original-date} | **Modified: {date}** | Source: specs/{feature-id}/
   ```

8. **Update /docs/README.md** (domain index):

   ```markdown
   # Project Documentation

   > Auto-maintained by /speckit.merge. Last updated: {date}

   ## Domains

   | Domain | Description | Features | Last Updated |
   |--------|-------------|----------|--------------|
   | [auth](auth/spec.md) | Authentication & authorization | login, signup, oauth | {date} |
   | [payments](payments/spec.md) | Payment processing | checkout, refunds | {date} |

   ## Quick Links

   - [Architecture Registry](/memory/architecture-registry.md)
   - [Constitution](/memory/constitution.md)
   ```

### Phase 3: Git Operations

9. **Merge into main**:

    ```bash
    # Switch to main
    git checkout main

    # Pull latest
    git pull origin main

    # Merge feature branch (no fast-forward to preserve history)
    git merge --no-ff {feature-branch} -m "feat: {feature-name}

    Merged from specs/{feature-id}/
    - [summary of what was implemented]

    Docs: /docs/{domain}/spec.md"
    ```

10. **Commit documentation updates** (if not already included):

    ```bash
    git add docs/
    git commit -m "docs: consolidate {feature-name} into /docs/{domain}

    - Updated docs/{domain}/spec.md
    - Updated docs/README.md"
    ```

### Phase 4: Post-Merge Actions

11. **Offer to run /speckit.learn**:

    ```markdown
    Feature merged successfully.

    Run /speckit.learn to update:
    - Architecture registry (patterns from this feature)
    - Local CLAUDE.md files (module conventions)

    Run learn? (yes/no)
    ```

    If yes → execute `/speckit.learn {feature-id}`

12. **Push to remote**:

    ```bash
    git push origin main
    ```

13. **Cleanup (optional)**:

    Ask user:
    ```markdown
    Delete feature branch locally and remotely?
    - Local: {feature-branch}
    - Remote: origin/{feature-branch}

    Delete? (yes/no/local-only)
    ```

### Phase 5: Summary

14. **Report completion**:

    ```markdown
    ## Merge Complete

    ### Git
    - Branch: {feature-branch} → main
    - Commit: {commit-hash}
    - Pushed: Yes

    ### Documentation Updated
    | File | Action |
    |------|--------|
    | docs/{domain}/spec.md | Created/Updated |
    | docs/README.md | Updated |

    ### Architecture (if learn was run)
    - Registry: {n} patterns added
    - CLAUDE.md: {modules} updated

    ### Next Steps
    - Review /docs/{domain}/spec.md for accuracy
    - Start next feature with /speckit.specify
    ```

## Output Files

- `/docs/{domain}/spec.md` - Domain specification (source of truth)
- `/docs/README.md` - Domain index

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
