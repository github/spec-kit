# Feature Specification: Custom Linear Ticket Format Configuration

**Feature Branch**: `001-custom-ticket-format`
**Created**: 2025-11-14
**Status**: Draft
**Input**: User description: "Enhance spec-kit `specify init` command to enable teams working on a specific project or repo to specify their linear ticket id format when running `init` for the first time. Teams should be able to specify their LINEAR TICKET ID FORMAT. E.g. for the Auror Subject Recognition team their linear tickets ids are like `AFR-1234`. This should inform speckit to create branches using the naming convention `linearticketid-branch-info` e.g. `AFR-1234-fix-bug-in-detection-ingestion` or `AFR-4321-change-yellow-buttons-to-orange`. When spec kit creates `specs`, the folder naming convention should be the same as this branch naming convention. Any commits made during development should use the format `linearticketid Describe change made` e.g. `ASR-1234 Change yellow buttons to orange`. We should provide examples and clear instructions. The Linear ticket format should be requested from the user after the step to `select script type`. This should be optional, users can provide nothing the default will be the `AUROR-XXX`/`AUROR-123` format. Consider a subsequent piece of work to allow users to update this later. Check how other `specify init` config can be changed. The README and constitution should be updated to reflect the changes we made and the context this provides for how this project will be used by other teams in their repositories."

## User Scenarios & Testing

### User Story 1 - Configure Linear Ticket Format During Initialization (Priority: P1)

A development team running `specify init` for the first time in their repository wants to configure their Linear ticket prefix (e.g., "AFR" for Auror Facial Recognition team) so that all branches, spec directories, and commit messages follow their team's ticket format.

**Why this priority**: This is the foundational capability that enables the entire feature. Without the ability to configure the format during init, no other functionality can work.

**Independent Test**: Can be fully tested by running `specify init`, providing a custom Linear ticket prefix (e.g., "AFR"), and verifying the configuration is saved and displayed back to the user.

**Acceptance Scenarios**:

1. **Given** a user runs `specify init` for the first time, **When** they reach the script type selection step and proceed, **Then** they are prompted with "Enter your Linear ticket prefix (e.g., AFR, ASR) or press Enter for default (AUROR):"
2. **Given** the Linear ticket format prompt is displayed, **When** the user enters "AFR", **Then** the system saves the configuration and confirms "Linear ticket format set to: AFR-XXXX"
3. **Given** the Linear ticket format prompt is displayed, **When** the user presses Enter without input, **Then** the system defaults to "AUROR" format and confirms "Linear ticket format set to: AUROR-XXX (default)"
4. **Given** the Linear ticket format prompt is displayed, **When** the user enters an invalid format (e.g., "AFR-123" with hyphen), **Then** the system displays an error "Invalid format. Please use only letters (e.g., AFR, ASR)" and re-prompts

---

### User Story 2 - Create Branches with Custom Format (Priority: P2)

A team member who has configured their Linear ticket format needs to create a new feature branch that follows the pattern `[PREFIX]-[NUMBER]-[description]` (e.g., `AFR-1234-fix-detection-bug`) instead of the default Auror format.

**Why this priority**: This is core functionality that directly impacts the team's daily workflow. Teams need branches that match their Linear ticket IDs for traceability.

**Independent Test**: Can be tested by configuring a custom format (e.g., "AFR"), running the branch creation command with a ticket number (e.g., 1234) and description, and verifying the branch name is `AFR-1234-description`.

**Acceptance Scenarios**:

1. **Given** Linear ticket format is configured as "AFR", **When** a user creates a new feature with ticket number 1234 and description "fix detection bug", **Then** the system creates branch `AFR-1234-fix-detection-bug`
2. **Given** Linear ticket format is configured as "ASR", **When** a user creates a new feature with ticket number 42 and description "add logging", **Then** the system creates branch `ASR-42-add-logging`
3. **Given** Linear ticket format is not configured (default), **When** a user creates a new feature, **Then** the system creates branch using `AUROR-XXX` format (e.g., `AUROR-123-feature-name`)

---

### User Story 3 - Create Spec Directories with Custom Format (Priority: P2)

A team member creating a new feature specification needs the spec directory to match their branch naming convention (e.g., `specs/AFR-1234-fix-detection-bug/`) for consistency and easy navigation.

**Why this priority**: Equally critical as branch naming - spec directories must match branch names for clarity and organization. Having mismatched naming would create confusion.

**Independent Test**: Can be tested by creating a feature with a custom format and verifying the created spec directory matches the branch name exactly.

**Acceptance Scenarios**:

1. **Given** a branch is created as `AFR-1234-fix-detection-bug`, **When** the spec directory is initialized, **Then** the system creates directory `specs/AFR-1234-fix-detection-bug/`
2. **Given** a branch is created as `ASR-42-add-logging`, **When** the spec directory is initialized, **Then** the system creates directory `specs/ASR-42-add-logging/`
3. **Given** multiple features exist with custom format, **When** listing spec directories, **Then** all directories follow the configured format pattern

---

### User Story 4 - Follow Commit Message Convention with Custom Format (Priority: P3)

A developer making commits during feature development wants to follow their team's commit message convention using their Linear ticket prefix (e.g., "AFR-1234 Add detection validation") for consistency and ticket linkage.

**Why this priority**: Important for consistency and traceability, but lower priority than branch/spec naming since commit messages can be manually formatted if needed. This is primarily guidance/documentation.

**Independent Test**: Can be tested by reviewing documentation and examples that clearly show the expected commit format, and verifying commits can be made following this pattern.

**Acceptance Scenarios**:

1. **Given** a developer is working on branch `AFR-1234-fix-detection-bug`, **When** they review the project documentation or init output, **Then** they see clear examples showing commit format: "AFR-1234 Describe change made"
2. **Given** the Linear ticket format is "ASR", **When** documentation is displayed, **Then** examples show "ASR-42 Change button color to orange"
3. **Given** default AUROR format is used, **When** documentation is displayed, **Then** examples show "AUROR-123 Update validation logic"

---

### User Story 5 - Understand Multi-Team Usage from Documentation (Priority: P3)

A team lead evaluating spec-kit for their team needs to understand that the tool supports custom Linear ticket formats and can be adapted to their team's workflow, not just Auror's default conventions.

**Why this priority**: Important for adoption and clarity, but doesn't affect core functionality. This is a documentation update that makes the tool more accessible to different teams.

**Independent Test**: Can be tested by reading the updated README and constitution and verifying they clearly explain custom format support and multi-team usage scenarios.

**Acceptance Scenarios**:

1. **Given** a user reads the README, **When** they review the configuration section, **Then** they see documentation explaining the Linear ticket format option with examples from multiple teams (AFR, ASR, etc.)
2. **Given** a user reads the constitution, **When** they review naming conventions, **Then** they understand the tool supports custom formats and provides examples
3. **Given** a new team wants to adopt spec-kit, **When** they run `specify init`, **Then** the prompts and examples make it clear they can customize the format for their team

---

### Edge Cases

- What happens when a user enters a Linear ticket prefix with special characters (e.g., "AFR-" or "ASR_123")?
  - System should validate and reject input, allowing only alphabetic characters
  - Display clear error message with valid examples
  - Re-prompt for correct input

- What happens when a user wants to change their Linear ticket format after initial configuration?
  - Document this as future work in the specification
  - Note that investigation is needed to understand how other `specify init` config changes are handled
  - Consider providing manual configuration file editing guidance as interim solution

- What happens when ticket numbers have different lengths (e.g., AFR-1 vs AFR-1234)?
  - System should support variable-length ticket numbers
  - No padding or formatting constraints on the number portion

- What happens when no Linear ticket format is configured and user tries to create a feature?
  - System should use default AUROR format as fallback
  - This ensures backward compatibility

- What happens when different team members have different format configurations in the same repository?
  - Document that configuration should be consistent across team members
  - Consider future work to detect and warn about configuration mismatches

## Requirements

### Functional Requirements

- **FR-001**: System MUST prompt user for Linear ticket format during `specify init` execution, immediately after the script type selection step
- **FR-002**: System MUST accept alphabetic characters only as Linear ticket prefix (e.g., AFR, ASR, AUROR)
- **FR-003**: System MUST accept empty input at the format prompt and default to "AUROR" format
- **FR-004**: System MUST validate Linear ticket format input and reject special characters, numbers, or hyphens in the prefix
- **FR-005**: System MUST persist Linear ticket format configuration for future use across all feature creation operations
- **FR-006**: System MUST use configured Linear ticket format when creating branch names following pattern: `[PREFIX]-[NUMBER]-[description]`
- **FR-007**: System MUST use configured Linear ticket format when creating spec directories following pattern: `specs/[PREFIX]-[NUMBER]-[description]/`
- **FR-008**: System MUST provide clear examples during the configuration prompt showing format options (e.g., "AFR-1234", "ASR-42", "AUROR-123")
- **FR-009**: System MUST confirm the configured format to the user after input (e.g., "Linear ticket format set to: AFR-XXXX")
- **FR-010**: System MUST display appropriate error messages for invalid format input with guidance on correct format
- **FR-011**: Documentation (README) MUST explain the Linear ticket format configuration feature with examples from multiple teams
- **FR-012**: Documentation (constitution) MUST reflect that spec-kit supports multi-team usage with custom formats
- **FR-013**: Documentation MUST provide clear examples of commit message format using custom ticket prefixes
- **FR-014**: System MUST maintain backward compatibility with existing AUROR-format configurations

### Key Entities

- **Linear Ticket Configuration**: Stores the team's chosen ticket prefix format (e.g., "AFR", "ASR", "AUROR"). Attributes include:
  - Prefix (string, alphabetic only)
  - Example format for display (e.g., "AFR-XXXX")
  - Default status (boolean indicating if using default AUROR format)

- **Feature Branch**: Represents a git branch created for feature development. Naming follows the pattern `[configured-prefix]-[ticket-number]-[description]`

- **Feature Spec Directory**: Represents a directory containing feature specifications. Naming mirrors branch naming for consistency

## Success Criteria

### Measurable Outcomes

- **SC-001**: Teams can configure custom Linear ticket format during `specify init` in under 1 minute with clear prompts and examples
- **SC-002**: Branches and spec directories use configured format 100% of the time after configuration is set
- **SC-003**: Configuration persists across terminal sessions and multiple feature creation operations without requiring reconfiguration
- **SC-004**: Input validation prevents 100% of invalid format configurations (special characters, numbers in prefix)
- **SC-005**: Documentation includes at least 3 examples from different team formats (AFR, ASR, AUROR) making multi-team usage clear
- **SC-006**: Default AUROR format works when no custom format is configured, ensuring zero breaking changes for existing users
- **SC-007**: Error messages for invalid input provide clear guidance, reducing re-prompts due to confusion to near zero

## Assumptions

- Teams using spec-kit have Linear project management system with consistent ticket ID formats
- Linear ticket IDs follow pattern of alphabetic prefix + hyphen + number (e.g., AFR-1234)
- Team members within a single repository will use consistent Linear ticket format configuration
- Commit message format adherence will be enforced through team conventions and documentation, not technical validation
- Configuration storage mechanism exists or will be created to persist settings between commands
- The existing `specify init` command has a defined step order that includes script type selection
- Teams want branch names, spec directories, and commit messages to all use consistent ticket format

## Out of Scope

- **Updating Linear ticket format after initial configuration**: Marked as future work. Investigation needed to understand how other `specify init` configurations are changed
- **Automatic commit message validation or enforcement**: Only documentation and examples provided
- **Support for multiple ticket formats within a single repository**: Single format per repository assumed
- **Integration with Linear API to validate ticket IDs**: No external validation of ticket numbers
- **Migration of existing branches/specs to new format**: Only affects new features created after configuration
- **Configuration at team member level**: Repository-level configuration only

## Dependencies

- **`src/specify_cli/__init__.py`** - Python CLI implementation of `specify init` command
  - Lines 866-1162: init() function that orchestrates project initialization
  - Lines 998-1010: Script type selection logic (Linear format prompt goes after this)
  - Needs mechanism to store Linear ticket format configuration

- **`.specify/scripts/bash/create-new-feature.sh`** - Feature creation script
  - Lines 183-214: Branch name generation and numbering logic
  - Currently creates branches as `001-feature-name`
  - Must read config and create branches as `PREFIX-NUMBER-feature-name`

- **`.specify/scripts/bash/common.sh`** - Shared bash functions
  - Lines 40-48: `get_current_branch()` - regex pattern `^([0-9]{3})-` needs custom format support
  - Lines 75-79: `check_feature_branch()` - validation logic needs custom format support
  - Lines 94-100: `find_feature_dir_by_prefix()` - prefix extraction needs custom format support

- **`.specify/scripts/bash/setup-plan.sh`** - Plan setup script
  - Uses common.sh functions (will inherit fixes automatically)
  - No direct changes needed

- **README.md** - Project documentation
  - Needs examples showing custom Linear ticket formats

- **`.specify/templates/constitution-template.md`** - Constitution template
  - Needs section explaining Linear ticket format conventions

## Technical Implementation Requirements

### Configuration Storage

A configuration file must be created to persist the Linear ticket format. Recommended approach:

- **Location**: `.specify/config.json` (gitignored, user-specific) or `.specify/project-config.json` (committed, team-shared)
- **Format**: JSON with structure:
  ```json
  {
    "linear_ticket_prefix": "AFR",
    "branch_format": "{prefix}-{number}-{description}",
    "commit_format": "{prefix}-{number} {message}"
  }
  ```

### Script Updates Required

#### 1. `src/specify_cli/__init__.py` Updates

**Location to add prompt**: After line 1010 (after script type selection)

```python
# Prompt for Linear ticket format
linear_prefix = None
if sys.stdin.isatty():
    console.print("\n[cyan]Linear Ticket Format Configuration[/cyan]")
    console.print("[dim]Enter your Linear ticket prefix (e.g., AFR, ASR, PROJ) or press Enter for default (AUROR)[/dim]")
    linear_prefix = input("Ticket prefix: ").strip().upper()

    # Validate: only alphabetic characters
    if linear_prefix and not linear_prefix.isalpha():
        console.print("[red]Invalid format. Only letters allowed.[/red]")
        # Re-prompt or exit

    if not linear_prefix:
        linear_prefix = "AUROR"
        console.print(f"[dim]Using default: AUROR-XXX[/dim]")
    else:
        console.print(f"[green]✓[/green] Linear ticket format set to: {linear_prefix}-XXXX")

# Save config after project extraction
config_file = project_path / ".specify" / "config.json"
config_data = {
    "linear_ticket_prefix": linear_prefix,
    "script_type": selected_script,
    "ai_assistant": selected_ai
}
config_file.write_text(json.dumps(config_data, indent=2))
```

#### 2. `create-new-feature.sh` Updates

**Changes needed**:
- Read `.specify/config.json` to get `linear_ticket_prefix`
- Accept `--ticket-number` or `--linear-ticket` parameter for ticket number (e.g., `AFR-1234`)
- Modify branch name format from `001-feature-name` to `PREFIX-NUMBER-feature-name`
- Update branch detection logic in `check_existing_branches()` to handle new format

**Example**:
```bash
# Read config
CONFIG_FILE="$REPO_ROOT/.specify/config.json"
if [ -f "$CONFIG_FILE" ]; then
    LINEAR_PREFIX=$(jq -r '.linear_ticket_prefix // "AUROR"' "$CONFIG_FILE")
else
    LINEAR_PREFIX="AUROR"
fi

# Parse --linear-ticket or --ticket-number parameter
# If provided: use format PREFIX-NUMBER-description
# If not provided: fall back to sequential numbering PREFIX-001-description
```

#### 3. `common.sh` Updates

**Changes needed**:
- Update regex patterns to match both old format (`001-name`) and new format (`AFR-1234-name`)
- Read config to determine expected format
- Validate branches against configured format

**Example updates**:
```bash
# Line 40: get_current_branch() - update regex
if [[ "$dirname" =~ ^([A-Z]+-[0-9]+|[0-9]{3})- ]]; then

# Line 75: check_feature_branch() - update validation
if [[ ! "$branch" =~ ^([A-Z]+-[0-9]+|[0-9]{3})- ]]; then
    echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
    echo "Feature branches should be named like: AFR-1234-feature-name or 001-feature-name" >&2

# Line 94: find_feature_dir_by_prefix() - update prefix extraction
if [[ ! "$branch_name" =~ ^(([A-Z]+)-([0-9]+)|([0-9]{3}))- ]]; then
```

### Backward Compatibility Strategy

All script updates must maintain backward compatibility with existing projects using the `001-feature-name` format:

1. **Config file check**: If `.specify/config.json` doesn't exist, assume legacy format (`001-`, `002-`, etc.)
2. **Dual regex patterns**: All regex patterns must accept both formats:
   - Legacy: `^[0-9]{3}-` (e.g., `001-feature-name`)
   - New: `^[A-Z]+-[0-9]+-` (e.g., `AFR-1234-feature-name`)
3. **Graceful degradation**: If config is malformed or unreadable, default to `AUROR` prefix
4. **Error messages**: Update error messages to show examples of both formats

### Testing Requirements

The following scenarios must be tested:

1. **New project with default format**: `specify init` with empty input → uses `AUROR` prefix
2. **New project with custom format**: `specify init` with "AFR" input → uses `AFR` prefix
3. **Existing project (no config)**: Scripts work with `001-feature-name` branches
4. **Mixed branches**: Repository with both `001-old-feature` and `AFR-1234-new-feature` branches
5. **Invalid input**: Reject inputs with numbers, special characters, or hyphens in prefix
6. **Config persistence**: Linear ticket format persists across terminal sessions

## Future Considerations

- **FR-FUTURE-001**: Allow users to update Linear ticket format configuration after initial setup
  - Investigation needed: Review how other `specify init` configurations can be changed (config file editing, re-running init, dedicated update command)
  - Potential approaches: Configuration file with manual editing documentation, `specify config update` command, or `specify init --reconfigure` flag

- **FR-FUTURE-002**: Provide warning or detection when team members have mismatched format configurations
  - Could compare configuration across git commits or team member setups
  - Help maintain consistency in team workflows

- **FR-FUTURE-003**: Support for multiple ticket format patterns (different teams contributing to same repo)
  - Allow specifying format per feature or per contributor
  - More complex configuration management needed
