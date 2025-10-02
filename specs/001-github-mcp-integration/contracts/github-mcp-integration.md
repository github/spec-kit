# GitHub MCP Integration Contract

**Feature**: 001-github-mcp-integration  
**Date**: 2025-10-02  
**Type**: Template Operations Contract

## Overview

This contract defines the expected behavior and structure for GitHub MCP operations integrated into Spec-Driven Development command templates. It specifies the GitHub API operations, error handling, and template modifications required for each workflow phase.

## Command: /specify

### Responsibilities
- Generate AI-powered branch name from feature description
- Create feature specification file (spec.md)
- Create GitHub Issue with spec content
- Apply semantic labels to issue

### GitHub MCP Operations

#### Issue Creation
```yaml
operation: mcp_github_create_issue
inputs:
  owner: string          # Repository owner
  repo: string           # Repository name
  title: string          # Formatted: "<Icon> [Type]: <Feature name>"
  body: string           # Spec content starting from "Primary User Story"
  labels: array<string>  # ["Specification", "<Type>"] where Type = Docs|Fix|Patch|Minor|Major

outputs:
  issue_number: integer  # Created issue number
  issue_url: string      # GitHub issue URL

error_handling:
  - Check GitHub API availability before operation
  - On failure: Report error, provide manual issue creation instructions
  - Log issue_number for subsequent commands
```

### Template Modifications Required

**File**: `templates/commands/specify.md`

**Additions**:
1. Branch name generation step (AI analysis of feature description)
2. Issue creation step using GitHub MCP
3. Icon and type determination logic
4. Label application logic
5. Error handling for GitHub API failures

**Synchronization Target**: `.github/prompts/specify.prompt.md` (already has GitHub MCP)

### Expected Behavior

**Success Case**:
1. User provides feature description via arguments
2. AI analyzes description and generates 2-4 word kebab-case branch name
3. Script creates branch with format `###-branch-name`
4. Spec file created at `specs/###-branch-name/spec.md`
5. GitHub issue created with:
   - Title: `🚀 [Feature]: GitHub MCP Integration for Spec-Driven Development`
   - Body: Spec content from "Primary User Story" section onward
   - Labels: `Specification`, `Minor`
   - Branch mentioned in description
6. User notified of issue number and URL

**Failure Case**:
1. GitHub API unavailable or rate-limited
2. Clear error message displayed
3. Manual fallback instructions provided:
   ```
   Please create issue manually:
   - Title: [generated title]
   - Body: [spec content]
   - Labels: Specification, Minor
   - Link to branch: ###-branch-name
   ```

## Command: /plan

### Responsibilities
- Generate design artifacts (research.md, data-model.md, contracts/, quickstart.md)
- Commit and push changes to feature branch
- Create draft Pull Request with plan content
- Link PR to issue
- Update issue labels

### GitHub MCP Operations

#### Pull Request Creation
```yaml
operation: mcp_github_create_pull_request
inputs:
  owner: string
  repo: string
  title: string          # Same format as issue title
  body: string           # Structured: summary + plan.md + "- Fixes #<issue>"
  head: string           # Feature branch name
  base: string           # Default branch (main)
  draft: boolean         # Always true for /plan
  labels: array<string>  # Same as issue labels

outputs:
  pr_number: integer
  pr_url: string

error_handling:
  - Verify branch pushed before PR creation
  - On failure: Report error, provide manual PR creation instructions
  - Log pr_number for subsequent commands
```

#### Issue Label Update
```yaml
operation: mcp_github_update_issue
inputs:
  owner: string
  repo: string
  issue_number: integer
  labels: array<string>  # Remove "Specification", add "Plan", keep type label

outputs:
  success: boolean

error_handling:
  - On failure: Log warning, continue (non-critical)
  - Provide manual label update instructions
```

### Template Modifications Required

**File**: `templates/commands/plan.md`

**Additions**:
1. Git commit and push operations
2. Draft PR creation with structured description
3. PR title formatting logic
4. Issue linking with "Fixes #" keyword
5. Label update logic
6. Error handling for Git and GitHub API operations

**Synchronization Target**: `.github/prompts/plan.prompt.md` (already has GitHub MCP)

### Expected Behavior

**Success Case**:
1. Planning artifacts generated (research.md, data-model.md, etc.)
2. Changes committed with descriptive message
3. Branch pushed to remote
4. Draft PR created with:
   - Title: Same as issue
   - Body: Summary paragraph + plan.md content + "- Fixes #<issue-number>"
   - Draft: true
   - Labels: Same as issue (type label)
5. Issue labels updated: Remove `Specification`, add `Plan`
6. User notified of PR number and URL

**Failure Case**:
1. Git push fails: Report error, check network/permissions
2. PR creation fails: Provide manual PR creation instructions
3. Label update fails: Log warning, note manual update needed

## Command: /tasks

### Responsibilities
- Generate task breakdown (tasks.md)
- Update PR description with tasks content
- Maintain existing PR content

### GitHub MCP Operations

#### Pull Request Update
```yaml
operation: mcp_github_update_pull_request
inputs:
  owner: string
  repo: string
  pr_number: integer
  body: string           # Existing content + "\n\n" + tasks.md with checkboxes

outputs:
  success: boolean

error_handling:
  - Fetch current PR description first
  - On failure: Report error, provide manual PR update instructions
  - Preserve existing content on append operation
```

### Template Modifications Required

**File**: `templates/commands/tasks.md`

**Additions**:
1. PR description fetch operation
2. tasks.md content formatting with checkboxes
3. PR description append operation
4. Error handling for GitHub API operations

**Synchronization Target**: `.github/prompts/tasks.prompt.md` (already has GitHub MCP)

### Expected Behavior

**Success Case**:
1. tasks.md generated from plan artifacts
2. Current PR description fetched
3. PR description updated with:
   - All existing content preserved
   - tasks.md content appended with checkboxes
   - Format: `- [ ] T001: Task description`
4. User notified of PR update

**Failure Case**:
1. PR not found: Report error, check feature branch
2. Description update fails: Provide manual update instructions
3. Show tasks.md content for manual copying

## Command: /implement

### Responsibilities
- Execute implementation tasks
- Progressively update PR description checkboxes
- Mark PR ready for review
- Update issue labels
- Update project constitution

### GitHub MCP Operations

#### Pull Request Description Update (Progressive)
```yaml
operation: mcp_github_update_pull_request
inputs:
  owner: string
  repo: string
  pr_number: integer
  body: string           # Current content with updated checkboxes: - [x]

frequency: After each task section completion

error_handling:
  - On failure: Log warning, continue implementation
  - Final update attempt at end
  - Provide manual checkbox update instructions if needed
```

#### Pull Request Ready Status
```yaml
operation: mcp_github_update_pull_request
inputs:
  owner: string
  repo: string
  pr_number: integer
  draft: boolean         # Set to false

outputs:
  success: boolean

error_handling:
  - On failure: Report error, provide manual ready-for-review instructions
```

#### Issue Label Update
```yaml
operation: mcp_github_update_issue
inputs:
  owner: string
  repo: string
  issue_number: integer
  labels: array<string>  # Add "Implementation", keep "Plan" and type label

outputs:
  success: boolean

error_handling:
  - On failure: Log warning, provide manual label update instructions
```

#### Constitution Update
```yaml
operation: file_write
inputs:
  path: .specify/memory/constitution.md
  content: string        # Appended with new feature capabilities

error_handling:
  - Backup constitution before update
  - On failure: Report error, provide recovery instructions
  - Commit constitution update with implementation
```

### Template Modifications Required

**File**: `templates/commands/implement.md`

**Additions**:
1. Progressive PR description updates after task sections
2. Draft status removal logic
3. Issue label update logic
4. Constitution update logic
5. Comprehensive error handling

**Synchronization Target**: `.github/prompts/implement.prompt.md` (already has GitHub MCP)

### Expected Behavior

**Success Case**:
1. Implementation tasks executed following TDD
2. After each major task section:
   - PR checkboxes updated: `- [ ]` → `- [x]`
3. All tasks complete:
   - PR marked ready for review (draft = false)
   - Issue labels updated: Add `Implementation`
   - Constitution updated with new capabilities
4. User notified of completion, PR ready for review

**Failure Case**:
1. Checkbox update fails: Log warning, continue
2. Ready status fails: Provide manual instructions
3. Label update fails: Provide manual instructions
4. Constitution update fails: Report error, provide recovery steps

## Template Synchronization Contract

### Required Synchronization

**Source of Truth**: `.github/prompts/*.prompt.md` (GitHub Copilot reference implementation)

**Sync Targets**: `templates/commands/*.md` (Generic agent templates)

**Files to Synchronize**:
1. `specify.prompt.md` → `specify.md`
2. `plan.prompt.md` → `plan.md`
3. `tasks.prompt.md` → `tasks.md`
4. `implement.prompt.md` → `implement.md`

### Synchronization Requirements

**Must Match**:
- GitHub MCP operation names and parameters
- Error handling logic
- Execution flow steps
- PR/Issue formatting rules
- Label management logic

**Can Differ**:
- Agent-specific syntax (`$ARGUMENTS` vs `{{args}}`)
- File headers and metadata
- Agent-specific instructions

### Verification Checklist

For each template pair:
- [ ] GitHub MCP operations present in both
- [ ] Error handling equivalent
- [ ] PR/Issue format rules identical
- [ ] Label logic synchronized
- [ ] Execution flow steps aligned

## Error Handling Contract

### GitHub API Errors

**Rate Limiting**:
```
Error: GitHub API rate limit exceeded
Recovery:
1. Wait for rate limit reset (shown in error message)
2. Resume operation manually
3. Or create issue/PR manually per instructions
```

**Network Errors**:
```
Error: Cannot connect to GitHub API
Recovery:
1. Check network connectivity
2. Verify GitHub status at status.github.com
3. Retry operation or proceed manually
```

**Authentication Errors**:
```
Error: GitHub authentication failed
Recovery:
1. Verify AI agent has GitHub access
2. Check repository permissions
3. Retry operation with proper credentials
```

**Not Found Errors**:
```
Error: Repository/Issue/PR not found
Recovery:
1. Verify repository name and owner
2. Check if issue/PR exists
3. Verify feature branch pushed to remote
```

### Git Operation Errors

**Push Failures**:
```
Error: Failed to push branch
Recovery:
1. Check network connectivity
2. Verify repository permissions
3. Pull latest changes if branch diverged
4. Retry push operation
```

### File Operation Errors

**Constitution Update Failures**:
```
Error: Cannot update constitution.md
Recovery:
1. Verify file exists at .specify/memory/constitution.md
2. Check write permissions
3. Backup and restore if corrupted
4. Update manually with provided content
```

## Testing Requirements

Each template with GitHub MCP operations must be validated for:

1. **Happy Path**: All operations succeed
2. **API Failure**: GitHub API unavailable
3. **Rate Limiting**: API rate limit exceeded
4. **Network Failure**: No internet connectivity
5. **Permission Errors**: Insufficient repository permissions
6. **Partial Failures**: Some operations succeed, others fail
7. **Manual Recovery**: User can complete workflow manually

## Success Criteria

This contract is satisfied when:

1. All four command templates have GitHub MCP operations
2. Operations match reference implementation in `.github/prompts/`
3. Error handling is comprehensive and user-friendly
4. Manual fallback procedures are documented
5. Template synchronization is documented in constitution
6. All test scenarios pass validation
