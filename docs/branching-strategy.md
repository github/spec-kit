# Branch Naming Guidelines

Corporate branch naming conventions for this project.

## Format

**Current strategy**: `feature/<number>-<jira>-<short-name>`

**Example**: `feature/001-C12345-7890-user-authentication`

## Components

### 1. Prefix

**Value**: `feature/`

**Alternatives**:

- `feature/` - New functionality
- `bugfix/` - Bug fixes
- `hotfix/` - Emergency production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

### 2. Number

**Format**: 3-digit zero-padded (e.g., `001`, `002`, `137`)

**Auto-generated**: Spec Kit finds highest existing number and increments.

Checks: Remote branches, local branches, specs directories

### 3. Jira Number

**Format**: `C<5 digits>-<4 digits>`

**Example**: `C12345-7890`

**Validation**: Must match regex `^C[0-9]{5}-[0-9]{4}$`

**Customization examples**:

- Jira: `PROJ-1234` → Regex: `^[A-Z]+-[0-9]+$`
- Azure DevOps: `AB#12345` → Regex: `^[A-Z]+#[0-9]+$`
- GitHub Issues: `#123` → Regex: `^#[0-9]+$`
- Linear: `LIN-123` → Regex: `^[A-Z]+-[0-9]+$`

### 4. Short Name

**Format**: 2-4 words, kebab-case, lowercase

**Examples**: `user-authentication`, `payment-processing-fix`, `analytics-dashboard`

**Best practices**:

- Use action-noun format: `add-oauth2`, `fix-payment-bug`
- Keep technical terms: `oauth2-integration`, `jwt-validation`
- 2-4 words maximum
- No special characters except hyphens

## Directory Structure

**Branch**: `feature/001-C12345-7890-user-auth`

**Directory**: `specs/001-C12345-7890-user-auth/` (prefix removed)

## Validation

Pre-creation checks:

1. Jira format matches regex
2. Short name is 2-4 words, valid characters
3. Branch name not already in use
4. Specs directory doesn't exist

## Git Operations

**Create branch** (recommended):

```bash
/specify C12345-7890 Add user authentication
```

**Switch branch**:

```bash
git checkout feature/001-C12345-7890-user-auth
```

**Delete branch**:

```bash
git branch -d feature/001-C12345-7890-user-auth
git push origin --delete feature/001-C12345-7890-user-auth
rm -rf specs/001-C12345-7890-user-auth
```

## Best Practices

**DO**:

- Use descriptive short names (action + noun)
- Keep technical terms (OAuth2, JWT, API)
- Use consistent casing (lowercase with hyphens)
- Let Spec Kit auto-generate numbers

**DON'T**:

- Use vague names ("update", "fix-bug", "changes")
- Include spaces or special characters
- Manually assign numbers
- Reuse branch names after deletion
- Use camelCase or snake_case
