---
description: Migrate existing local project memory to Hindsight MCP for persistent, semantic search capabilities.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Migrate an existing Spec Kit project from local file-based memory (`/memory/constitution.md`) to Hindsight MCP, enabling semantic search and cross-session persistence.

## Prerequisites

- Project must have been initialized with `specify init`
- Hindsight MCP server must be configured and accessible
- Existing `/memory/constitution.md` file (optional but recommended)

## Execution Steps

### 1. Verify Hindsight Availability

First, verify that Hindsight MCP tools are accessible:

```
mcp__hindsight__list_banks()
```

If this fails, inform the user:
- "Hindsight MCP is not available. Please ensure the Hindsight server is running and configured in your AI agent."
- Provide setup instructions or link to Hindsight documentation
- **STOP** execution

### 2. Determine Bank ID

Check for user-provided bank ID in arguments, or generate default:

- If user specified: Use that bank ID
- If not specified: Generate `speckit-{project-directory-name}` (lowercase, hyphens)

Example: Project in `/Users/dev/my-awesome-app` → bank ID: `speckit-my-awesome-app`

### 3. Create or Verify Hindsight Bank

```
mcp__hindsight__create_bank(
  bank_id: {determined bank ID},
  name: "Spec Kit - {project name}",
  background: "Project memory for Spec Kit SDD workflow. Contains constitution, tech decisions, feature specs, implementation learnings, and code patterns."
)
```

### 4. Update Project Configuration

Create or update `.specify/config.json`:

```json
{
  "version": "1.0.0",
  "memory": {
    "provider": "hindsight",
    "hindsight": {
      "bank_id": "{determined bank ID}"
    }
  }
}
```

If config already exists with `provider: "local"`, update it. If already `provider: "hindsight"`, warn user and ask if they want to re-migrate.

### 5. Migrate Constitution (if exists)

If `/memory/constitution.md` exists:

1. **Parse constitution content**:
   - Extract project metadata (name, version, dates)
   - Extract each principle (name, description, rationale)
   - Extract governance rules

2. **Store in Hindsight**:

   a. **Project metadata**:
   ```
   mcp__hindsight__retain(
     content: "Project: {PROJECT_NAME}, Version: {VERSION}, Ratified: {RATIFICATION_DATE}, Last Amended: {LAST_AMENDED_DATE}",
     context: "constitution-metadata",
     bank_id: {bank ID}
   )
   ```

   b. **Each principle**:
   ```
   mcp__hindsight__retain(
     content: "Principle {N}: {NAME}\n{DESCRIPTION}\nRationale: {RATIONALE}",
     context: "constitution-principle",
     bank_id: {bank ID}
   )
   ```

   c. **Governance rules**:
   ```
   mcp__hindsight__retain(
     content: "{Full governance section}",
     context: "constitution-governance",
     bank_id: {bank ID}
   )
   ```

### 6. Migrate Existing Specs

Scan for existing feature specifications in `specs/*/spec.md`:

For each spec found, create a summary and store:

```
mcp__hindsight__retain(
  content: "Feature: {feature name from spec}\nPath: {spec file path}\nSummary: {2-3 sentence summary}\nKey Requirements: {top 3 requirements}",
  context: "feature-spec",
  bank_id: {bank ID}
)
```

Limit to 10 most recent specs to avoid overwhelming the bank.

### 7. Verify Migration

Verify the migration by recalling stored content:

```
mcp__hindsight__recall(
  query: "constitution principles project metadata",
  bank_id: {bank ID}
)
```

Check that:
- Constitution metadata is retrievable
- At least one principle is retrievable
- Response is coherent and matches source content

### 8. Report Results

Output a migration summary:

```markdown
## Migration Complete

**Bank ID**: {bank ID}
**Config Updated**: .specify/config.json

### Migrated Content

| Content Type | Count | Status |
|--------------|-------|--------|
| Constitution Metadata | 1 | ✓ |
| Principles | {N} | ✓ |
| Governance | 1 | ✓ |
| Feature Specs | {N} | ✓ |

### Verification

Constitution recall: ✓ Success

### Next Steps

1. All `/speckit.*` commands will now use Hindsight for memory
2. Run `/speckit.constitution` to update principles - they'll be stored in Hindsight
3. New feature specs will be searchable across sessions
4. Implementation decisions and learnings will accumulate over time

### Local Files

Local files (`/memory/constitution.md`) are preserved as backup.
Hindsight is now the primary memory source.
```

## Error Handling

- **Hindsight unavailable**: Stop and provide setup instructions
- **Bank creation fails**: Report error, suggest checking permissions
- **Partial migration**: Report which items succeeded/failed, allow retry
- **Config write fails**: Report error, provide manual config content

## Rollback

To revert to local memory:
1. Edit `.specify/config.json`
2. Change `"provider": "hindsight"` to `"provider": "local"`
3. Local files remain intact and will be used again

## Notes

- Migration is additive - it doesn't delete local files
- Re-running migration will add duplicate entries (warn user)
- Bank can be shared across multiple projects if desired (advanced use case)
