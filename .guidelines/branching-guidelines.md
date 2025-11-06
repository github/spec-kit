# Branch Naming Guidelines

This file documents corporate branch naming conventions for this project.

## Current Strategy

**Format**: `feature/<number>-<jira>-<short-name>`

**Example**: `feature/001-C12345-7890-user-authentication`

## Components

### 1. Prefix

**Value**: `feature/`

**Purpose**: Categorizes branch type (feature vs bugfix vs hotfix)

**Alternatives** (customize as needed):

- `feature/` - New functionality
- `bugfix/` - Bug fixes
- `hotfix/` - Emergency production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

### 2. Number

**Format**: 3-digit zero-padded number (e.g., `001`, `002`, `137`)

**Purpose**: Provides unique sequential identifier and easy sorting

**Auto-generated**: Spec Kit automatically finds highest existing number and increments

**How it works**:

```bash
# Checks all sources for highest number:
# - Remote branches: git ls-remote --heads origin
# - Local branches: git branch
# - Specs directories: ls specs/
# Then uses N+1 for new branch
```

### 3. Jira Number

**Format**: `C<5 digits>-<4 digits>`

**Example**: `C12345-7890`

**Purpose**: Links branch to Jira ticket for traceability

**Validation**: Must match regex `^C[0-9]{5}-[0-9]{4}$`

**Customization**:

Replace `C12345-7890` pattern with your organization's ticket format:

- **Jira**: `PROJ-1234` → Update regex to `^[A-Z]+-[0-9]+$`
- **Azure DevOps**: `AB#12345` → Update regex to `^[A-Z]+#[0-9]+$`
- **GitHub Issues**: `#123` → Update regex to `^#[0-9]+$`
- **Linear**: `LIN-123` → Update regex to `^[A-Z]+-[0-9]+$`

**Current validation location**:

- Bash: `scripts/bash/create-new-feature.sh`
- PowerShell: `scripts/powershell/create-new-feature.ps1`

### 4. Short Name

**Format**: 2-4 words, kebab-case, lowercase

**Example**: `user-authentication`, `payment-processing-fix`, `analytics-dashboard`

**Purpose**: Human-readable description of feature

**Best practices**:

- Use action-noun format: `add-oauth2`, `fix-payment-bug`
- Keep technical terms: `oauth2-integration`, `jwt-validation`
- 2-4 words maximum
- No special characters except hyphens

## Full Examples

### Feature Development

```text
feature/001-C12345-7890-user-authentication
feature/002-C12345-7891-payment-processing
feature/003-C12345-7892-analytics-dashboard
```

### Bug Fixes

```text
bugfix/004-C12345-7893-fix-login-timeout
bugfix/005-C12345-7894-fix-payment-validation
```

### Hotfixes

```text
hotfix/006-C12345-7895-fix-critical-security-issue
```

## Directory Structure

When branch is created, corresponding directory is created in `specs/` **without** the prefix:

**Branch**: `feature/001-C12345-7890-user-auth`

**Directory**: `specs/001-C12345-7890-user-auth/`

**Why**: Keeps specs directory flat and easy to navigate.

## Workflow

### 1. Interactive Mode

When running `/specify` without arguments:

```text
JIRA: C12345-7890
FEATURE: Add user authentication with OAuth2
```

**Result**:

- Branch created: `feature/001-C12345-7890-user-auth`
- Directory created: `specs/001-C12345-7890-user-auth/`

### 2. Direct Mode

When running `/specify` with arguments:

```bash
/specify C12345-7890 Add user authentication with OAuth2
```

**Result**: Same as interactive mode

### 3. Number Auto-Increment

Spec Kit automatically:

1. Fetches all remote branches
2. Lists all local branches
3. Scans specs directories
4. Finds highest number across all sources
5. Uses N+1 for new branch

**Example**:

```text
Existing branches:
- feature/001-C12345-7890-user-auth
- feature/002-C12345-7891-payments
- bugfix/003-C12345-7892-fix-login

New branch will be: feature/004-C12345-7893-analytics
```

## Customization (Phase 2)

**Status**: Planned for Phase 2 implementation

**Future capability**: Branch naming will be configurable via JSON file.

**Planned file**: `.guidelines/branch-config.json`

**Example configuration**:

```json
{
  "version": "1.0",
  "patterns": {
    "feature": {
      "format": "feature/{number}-{jira}-{short-name}",
      "numberFormat": "000",
      "jiraPattern": "^[A-Z]+-[0-9]+$",
      "jiraExample": "PROJ-1234"
    },
    "bugfix": {
      "format": "bugfix/{number}-{jira}-{short-name}",
      "numberFormat": "000",
      "jiraPattern": "^[A-Z]+-[0-9]+$",
      "jiraExample": "PROJ-1234"
    }
  },
  "specsDirectory": "specs",
  "includePrefix": false
}
```

**See**: `GUIDELINES-IMPLEMENTATION-PLAN.md` Phase 2 for details.

## Validation

### Pre-Creation Checks

Before creating branch, Spec Kit validates:

1. **Jira format**: Must match regex pattern
2. **Short name**: Must be 2-4 words, valid characters
3. **Uniqueness**: Branch name not already in use
4. **Specs directory**: Not already exists

### Post-Creation Verification

After creating branch, Spec Kit verifies:

1. Branch exists locally: `git branch | grep <name>`
2. Specs directory created: `ls specs/<name>`
3. Spec file initialized: `ls specs/<name>/spec.md`

## Troubleshooting

### Issue: Wrong Jira Format

**Error**:

```text
Error: Jira number must match format C12345-7890
```

**Solution**: Update Jira number to match `C<5 digits>-<4 digits>` format.

**Customization**: Edit regex validation in scripts (see "Jira Number" section above).

### Issue: Branch Already Exists

**Error**:

```text
Error: Branch feature/001-C12345-7890-user-auth already exists
```

**Solution**:

- If continuing work: `git checkout feature/001-C12345-7890-user-auth`
- If new feature: Use different short name or Jira number

### Issue: Wrong Number Assigned

**Symptom**: Expected `feature/005-...` but got `feature/008-...`

**Cause**: Other branches exist that you didn't see (remote branches or other specs directories).

**Solution**: This is correct behavior - Spec Kit checks all sources to avoid conflicts.

### Issue: Specs Folder Created with Prefix

**Symptom**: Directory created as `specs/feature/001-...` instead of `specs/001-...`

**Cause**: Known bug in older Claude versions when running `/specify plan`.

**Status**: Fixed in Phase 1 (this PR).

**Solution**: Ensure only `/specify` command creates specs folders, not `/specify plan`.

## Git Operations

### Branch Creation

```bash
# Automatic via /specify command (recommended)
/specify C12345-7890 Add user authentication

# Manual (not recommended - bypasses validation)
git checkout -b feature/001-C12345-7890-user-auth
mkdir -p specs/001-C12345-7890-user-auth
```

### Branch Switching

```bash
git checkout feature/001-C12345-7890-user-auth
```

### Branch Deletion

```bash
# Delete local branch
git branch -d feature/001-C12345-7890-user-auth

# Delete remote branch
git push origin --delete feature/001-C12345-7890-user-auth

# Clean up specs directory (manual)
rm -rf specs/001-C12345-7890-user-auth
```

## Corporate Requirements

### Jira Integration

**Current**: Jira number required in branch name for traceability

**Purpose**:

- Links code to requirements
- Enables automated reporting
- Facilitates code review
- Supports release notes generation

**Enforcement**: Validated by regex in scripts

### Naming Convention

**Current**: `feature/<num>-<jira>-<short-name>`

**Rationale**:

- **Prefix**: Enables Git branch filtering and policies
- **Number**: Provides unique ID and chronological ordering
- **Jira**: Links to work tracking system
- **Short name**: Human-readable at a glance

### Alternative Patterns

If your organization uses different patterns, customize in Phase 2:

**Pattern 1**: `<type>/<jira>-<description>`

```text
feature/PROJ-1234-user-authentication
bugfix/PROJ-1235-fix-payment-bug
```

**Pattern 2**: `<developer>/<type>/<jira>-<description>`

```text
jsmith/feature/PROJ-1234-user-auth
jdoe/bugfix/PROJ-1235-payment-fix
```

**Pattern 3**: `<jira>-<description>` (no prefix)

```text
PROJ-1234-user-authentication
PROJ-1235-fix-payment-bug
```

## Best Practices

### DO

- ✅ Use descriptive short names (action + noun)
- ✅ Keep technical terms (OAuth2, JWT, API)
- ✅ Validate Jira number before creating branch
- ✅ Let Spec Kit auto-generate numbers
- ✅ Use consistent casing (lowercase with hyphens)

### DON'T

- ❌ Use vague names ("update", "fix-bug", "changes")
- ❌ Include spaces or special characters
- ❌ Manually assign numbers (let auto-increment handle it)
- ❌ Reuse branch names after deletion
- ❌ Use camelCase or snake_case (use kebab-case)

## See Also

- `GUIDELINES-IMPLEMENTATION-PLAN.md` - Phase 2 planning for configurable branch naming
- `scripts/bash/create-new-feature.sh` - Bash implementation
- `scripts/powershell/create-new-feature.ps1` - PowerShell implementation
- `templates/commands/specify.md` - Interactive prompt for branch creation
