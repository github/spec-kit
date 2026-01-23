# Feature Specification: Customizable Branch Naming Templates

**Feature Branch**: `001-custom-branch-templates`  
**Created**: 2026-01-23  
**Status**: Draft  
**Input**: User description: "Customizable branch naming templates for team workflows - allow settings file configuration for branch name patterns like username/<num>-<name> or feature/username-<num>-<name>"

## Clarifications

### Session 2026-01-23

- Q: How should number sequences be scoped when templates include user prefixes? → A: Per-user prefix scoping (each user gets independent sequence)
- Q: What happens when Git has no user.name and template requires {username}? → A: OS username fallback (use $USER / $env:USERNAME silently)
- Q: Which CLI approach for initializing settings file? → A: Extend init with `specify init --settings` flag

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Team Branch Template (Priority: P1)

As a team lead setting up Spec Kit for a shared repository, I want to configure a branch naming template so that all team members create branches following our team's conventions without manual coordination.

**Why this priority**: This is the core value proposition - without the ability to configure templates, the feature has no utility. Teams cannot collaborate effectively with conflicting branch names.

**Independent Test**: Can be fully tested by creating a settings file with a custom template, running `/speckit.specify`, and verifying the branch name matches the configured pattern.

**Acceptance Scenarios**:

1. **Given** a settings file exists with `branch_template: "feature/{username}/{number}-{short_name}"`, **When** a user runs `/speckit.specify Add login feature`, **Then** a branch named `feature/johndoe/001-add-login-feature` is created (where johndoe is the Git-configured username)

2. **Given** a settings file exists with `branch_template: "{username}/{number}-{short_name}"`, **When** a user runs `/speckit.specify Implement caching`, **Then** a branch named `johndoe/001-implement-caching` is created

3. **Given** no settings file exists, **When** a user runs `/speckit.specify Add feature`, **Then** the current default behavior `{number}-{short_name}` is used (backward compatible)

---

### User Story 2 - Use Default Template Without Configuration (Priority: P2)

As a solo developer using Spec Kit, I want the system to work without any configuration so that I can continue using the simple `###-feature-name` format without additional setup.

**Why this priority**: Backward compatibility ensures existing users are not disrupted. Solo developers benefit from simplicity.

**Independent Test**: Can be fully tested by running `/speckit.specify` without any settings file and verifying the branch follows the original `###-feature-name` pattern.

**Acceptance Scenarios**:

1. **Given** no settings file exists in the project, **When** a user runs `/speckit.specify Create dashboard`, **Then** a branch named `001-create-dashboard` is created (current behavior preserved)

2. **Given** a settings file exists but has no `branch_template` key, **When** a user runs `/speckit.specify Add notifications`, **Then** the default template `{number}-{short_name}` is used

---

### User Story 3 - Resolve Username from Git Config (Priority: P3)

As a developer on a team, I want the system to automatically detect my username from my Git configuration so that I don't need to manually specify it each time I create a branch.

**Why this priority**: Automation of username detection removes friction and reduces errors from manual entry.

**Independent Test**: Can be fully tested by configuring `git config user.name`, creating a settings file with `{username}` in the template, running `/speckit.specify`, and verifying the username appears in the branch name.

**Acceptance Scenarios**:

1. **Given** Git config has `user.name = "Jane Smith"`, **When** a template contains `{username}`, **Then** the username is normalized to `jane-smith` (lowercase, spaces replaced with hyphens)

2. **Given** Git config has `user.email = "jsmith@company.com"`, **When** a template contains `{email_prefix}`, **Then** the email prefix `jsmith` is extracted and used

3. **Given** Git config has no user.name set, **When** a template contains `{username}`, **Then** the system silently uses the OS username (`$USER` on Unix, `$env:USERNAME` on Windows) without prompting

---

### User Story 4 - Initialize Settings File (Priority: P4)

As a team lead, I want to initialize a settings file with example templates so that I can quickly configure branch naming for my team.

**Why this priority**: Discoverability and ease of setup improve adoption, but teams can manually create the settings file if needed.

**Independent Test**: Can be fully tested by running a CLI command to generate the settings file and verifying it contains documented template options.

**Acceptance Scenarios**:

1. **Given** no settings file exists, **When** a user runs `specify init --settings`, **Then** a settings file is created at `.specify/settings.toml` with commented examples of common templates

2. **Given** a settings file already exists, **When** a user runs `specify init --settings`, **Then** the system warns about overwriting and requires confirmation (or use `--force` to skip)

---

### Edge Cases

- What happens when the template produces an invalid Git branch name (e.g., contains `..` or starts with `-`)?
  - System MUST validate the generated branch name and report clear errors
- What happens when two developers using the same template create branches simultaneously with the same number?
  - Each developer's number sequence is scoped to their username prefix, OR the system detects conflicts and increments
- What happens when the settings file contains syntax errors?
  - System MUST report the parsing error with file location and continue with default template
- What happens when the username contains special characters not allowed in branch names?
  - System MUST sanitize the username (remove/replace invalid characters)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a settings file (`.specify/settings.toml`) with a `branch.template` key for branch template configuration
- **FR-002**: System MUST support the following template variables:
  - `{number}` - Auto-incrementing 3-digit feature number (e.g., `001`, `002`)
  - `{short_name}` - Generated or provided short feature name (e.g., `add-login-feature`)
  - `{username}` - Git user.name, normalized for branch names (falls back to OS username)
  - `{email_prefix}` - Portion of Git user.email before the `@` symbol (returns empty string if email not configured; validation will catch invalid branch names)
- **FR-003**: System MUST use the default template `{number}-{short_name}` when no settings file exists or no `branch.template` is configured (backward compatibility)
- **FR-004**: System MUST validate generated branch names against Git branch naming rules (no `..`, no leading `-`, no trailing `.lock`, etc.)
- **FR-005**: System MUST sanitize username values by converting to lowercase and replacing spaces/special characters with hyphens
- **FR-006**: System MUST report clear error messages when:
  - The settings file has syntax errors (with line number if possible)
  - The template produces an invalid branch name
  - A required template variable cannot be resolved
- **FR-007**: System MUST support literal text in templates (e.g., `feature/`, `users/`)
- **FR-008**: System MUST scope the number sequence to the template prefix when the template includes `{username}` or a static prefix. Each user's prefix creates an independent number sequence (e.g., `johndoe/001`, `johndoe/002` while `janedoe/001`, `janedoe/002` can exist simultaneously)
- **FR-009**: Both Bash (`create-new-feature.sh`) and PowerShell (`create-new-feature.ps1`) scripts MUST support the settings file

### Key Entities

- **Settings File**: A TOML configuration file at `.specify/settings.toml` containing project-level Spec Kit settings, including `branch_template`
- **Branch Template**: A string pattern with placeholders (e.g., `{username}/{number}-{short_name}`) that defines how branch names are generated
- **Template Variable**: A placeholder in the format `{variable_name}` that is replaced with a computed value during branch creation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Teams with 3+ developers can create feature branches simultaneously without naming conflicts when using username-prefixed templates
- **SC-002**: Existing Spec Kit users experience zero breaking changes - projects without settings files work identically to before
- **SC-003**: Users can configure and apply a custom branch template in under 2 minutes
- **SC-004**: 100% of template variables resolve correctly across macOS, Linux, and Windows environments

## Assumptions

- Git is installed and configured with `user.name` and/or `user.email` for username resolution
- The `.specify/` directory already exists in projects initialized with Spec Kit
- TOML is an appropriate settings format (widely supported, human-readable, supports comments)
- Teams will document their chosen branch template in their contributing guidelines
