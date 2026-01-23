# Data Model: Customizable Branch Naming Templates

**Feature**: 001-custom-branch-templates  
**Date**: 2026-01-23

## Entities

### SettingsFile

A TOML configuration file containing project-level Spec Kit settings.

**Location**: `.specify/settings.toml`

**Schema**:

```toml
# Spec Kit Settings
# This file configures project-level settings for the Spec Kit workflow.

[branch]
# Template for generating feature branch names.
# Available variables:
#   {number}       - Auto-incrementing 3-digit feature number (e.g., 001, 002)
#   {short_name}   - Generated or provided short feature name (e.g., add-login-feature)
#   {username}     - Git user.name, normalized for branch names (lowercase, hyphens)
#   {email_prefix} - Portion of Git user.email before the @ symbol
#
# Examples:
#   "{number}-{short_name}"                     # Default: 001-add-login (solo developer)
#   "{username}/{number}-{short_name}"          # johndoe/001-add-login (team)
#   "feature/{username}/{number}-{short_name}" # feature/johndoe/001-add-login (team with prefix)
#   "users/{email_prefix}/{number}-{short_name}" # users/jsmith/001-add-login (enterprise)
#
template = "{number}-{short_name}"
```

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `branch.template` | string | No | `{number}-{short_name}` | Branch naming template with placeholders |

**Validation Rules**:
- File must be valid TOML syntax
- `branch.template` must contain `{number}` placeholder
- `branch.template` must contain `{short_name}` placeholder
- Template must produce valid Git branch names after resolution

---

### BranchTemplate

A string pattern defining how branch names are generated.

**Format**: String with `{variable}` placeholders

**Supported Variables**:

| Variable | Source | Normalization | Example Input | Example Output |
|----------|--------|---------------|---------------|----------------|
| `{number}` | Auto-increment from existing branches | Zero-padded 3 digits | 5 | `005` |
| `{short_name}` | Feature description or `--short-name` flag | Lowercase, hyphen-separated | "Add Login" | `add-login` |
| `{username}` | `git config user.name` → `$USER` | Lowercase, special chars → hyphens | "Jane Smith" | `jane-smith` |
| `{email_prefix}` | `git config user.email` (before @) | Lowercase | "jsmith@co.com" | `jsmith` |

**Resolution Order**:
1. Load template from settings file (or use default)
2. Resolve `{username}` from Git config or OS username
3. Resolve `{email_prefix}` from Git config email
4. Determine scope prefix (everything before `{number}`)
5. Scan existing branches/specs matching prefix
6. Resolve `{number}` as next available in sequence
7. Resolve `{short_name}` from description or `--short-name` flag
8. Validate final branch name against Git rules

---

### TemplateVariable

A placeholder token that gets replaced with a computed value.

**Format**: `{variable_name}` (curly braces, lowercase, underscores)

**State Transitions**:

```
[Unresolved] ---(resolve)---> [Resolved] ---(validate)---> [Valid/Invalid]
```

| State | Description | Example |
|-------|-------------|---------|
| Unresolved | Raw template string | `{username}/{number}-{short_name}` |
| Resolved | All placeholders replaced | `johndoe/001-add-login` |
| Valid | Passes Git branch name validation | `johndoe/001-add-login` ✅ |
| Invalid | Fails Git validation rules | `--invalid/branch` ❌ |

---

## Relationships

```
SettingsFile (1) ──contains──> (1) BranchTemplate
BranchTemplate (1) ──contains──> (0..*) TemplateVariable
BranchTemplate (1) ──resolves to──> (1) BranchName (string)
```

---

## Validation Rules

### Settings File Validation

| Rule | Error Message |
|------|---------------|
| File must be valid TOML | `Error: Settings file has syntax error at line {n}: {message}` |
| Unknown keys are warnings | `Warning: Unknown setting '{key}' in settings.toml (ignored)` |

### Template Validation

| Rule | Error Message |
|------|---------------|
| Must contain `{number}` | `Error: Template must contain {number} placeholder` |
| Must contain `{short_name}` | `Error: Template must contain {short_name} placeholder` |
| Unknown variable | `Error: Unknown template variable '{var}'. Valid: number, short_name, username, email_prefix` |
| Invalid characters in literal text | `Error: Template contains invalid Git branch characters: {chars}` |

### Branch Name Validation (post-resolution)

| Rule | Error Message |
|------|---------------|
| Cannot start with `-` | `Error: Branch name cannot start with hyphen: {name}` |
| Cannot contain `..` | `Error: Branch name cannot contain '..': {name}` |
| Cannot end with `.lock` | `Error: Branch name cannot end with '.lock': {name}` |
| Cannot exceed 244 bytes | `Warning: Branch name truncated to 244 bytes (GitHub limit)` |
| Cannot contain forbidden chars | `Error: Branch name contains invalid character '{char}': {name}` |
