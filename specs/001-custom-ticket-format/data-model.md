# Data Model: Linear Ticket Format Configuration

**Feature**: 001-custom-ticket-format | **Date**: 2025-11-14
**Purpose**: Define configuration schema, validation rules, and state management

## Overview

The Linear ticket format feature introduces a single configuration entity stored as JSON. This is **not a database schema** but a file-based configuration model. The configuration drives branch naming, spec directory creation, and commit message conventions.

---

## Configuration Entity

### Entity: ProjectConfig

**Location**: `.specify/config.json` (project root)
**Format**: JSON
**Lifecycle**: Created during `specify init`, read by workflow scripts
**Git Status**: Committed (team-shared)

**Schema**:

```json
{
  "linear_ticket_prefix": "string",
  "branch_format": "string (template)",
  "commit_format": "string (template)"
}
```

**Note**: `script_type` and `ai_assistant` are NOT saved to config. They are per-developer choices used only during `specify init` for template selection.

### Field Definitions

| Field | Type | Required | Default | Validation | Purpose |
|-------|------|----------|---------|------------|---------|
| `linear_ticket_prefix` | string | Yes | "AUROR" | Alphabetic only, 2-10 chars | Team's Linear ticket prefix (team-shared) |
| `branch_format` | string | No | "{prefix}-{number}-{description}" | Template string | Branch naming template (team-shared) |
| `commit_format` | string | No | "{prefix}-{number} {message}" | Template string | Commit message template (documentation only) |

**Field Details**:

#### `linear_ticket_prefix`

**Validation Rules**:
```python
def validate_prefix(prefix: str) -> tuple[bool, str]:
    """Validate Linear ticket prefix.

    Returns:
        (is_valid, error_message)
    """
    if not prefix:
        return True, ""  # Empty allowed (use default)

    if not prefix.isalpha():
        return False, "Prefix must contain letters only (no numbers, hyphens, or special characters)"

    if not prefix.isupper():
        return False, "Prefix must be uppercase (will be auto-converted)"

    if len(prefix) < 2:
        return False, "Prefix must be at least 2 characters"

    if len(prefix) > 10:
        return False, "Prefix must be 10 characters or less"

    return True, ""
```

**Examples**:
- ✅ Valid: `AFR`, `ASR`, `AUROR`, `PROJ`, `TEAM`
- ❌ Invalid: `AFR-`, `ASR123`, `a`, `VERYLONGPREFIX`

**Case Handling**: Automatically converted to uppercase during input

---

#### `branch_format` (Template)

**Purpose**: Define how branch names are generated

**Template Variables**:
- `{prefix}`: Linear ticket prefix (e.g., "AFR")
- `{number}`: Ticket or sequence number (e.g., "1234" or "001")
- `{description}`: Slugified feature description

**Default**: `"{prefix}-{number}-{description}"`

**Examples**:
- Input: prefix=AFR, number=1234, description="add user auth"
- Output: `AFR-1234-add-user-auth`

**Usage**: Currently not customizable in v1, reserved for future enhancement

---

#### `commit_format` (Template)

**Purpose**: Document expected commit message format

**Template Variables**:
- `{prefix}`: Linear ticket prefix
- `{number}`: Ticket number
- `{message}`: Commit message

**Default**: `"{prefix}-{number} {message}"`

**Examples**:
- Template: `{prefix}-{number} {message}`
- Actual commit: `AFR-1234 Add user authentication endpoint`

**Usage**: Documentation only (not enforced programmatically in v1)

---

## Validation Rules

### Creation-Time Validation (Python CLI)

**When**: During `specify init` before writing config file

**Rules**:
1. **Prefix format**: Alphabetic only, 2-10 characters
2. **Case normalization**: Automatically uppercase the input
3. **Re-prompt on error**: Invalid input triggers re-prompt with clear error

**Implementation Location**: `src/specify_cli/__init__.py` (lines 1010-1050)

**Error Messages**:

| Invalid Input | Error Message | Suggested Action |
|--------------|---------------|------------------|
| `AFR-123` | "Invalid format. Use letters only (e.g., AFR, ASR, PROJ)" | Re-prompt |
| `a` | "Prefix must be at least 2 characters" | Re-prompt |
| `VERYLONGPREFIX` | "Prefix must be 10 characters or less" | Re-prompt |
| `123` | "Invalid format. Use letters only (e.g., AFR, ASR, PROJ)" | Re-prompt |

---

### Read-Time Validation (Bash Scripts)

**When**: During branch creation, script execution

**Rules**:
1. **File existence**: Check if `.specify/config.json` exists
2. **JSON parsing**: Attempt to parse with jq or fallback
3. **Default fallback**: If file missing or malformed, default to "AUROR"
4. **Warning output**: Emit warning if config is malformed (stderr)

**Implementation Location**: `.specify/scripts/bash/common.sh` (new function)

**Bash Validation Example**:
```bash
read_config_prefix() {
    local config_file="$1"
    local default="AUROR"

    # Check file exists
    if [ ! -f "$config_file" ]; then
        echo "$default"
        return
    fi

    # Try jq first
    if command -v jq >/dev/null 2>&1; then
        prefix=$(jq -r '.linear_ticket_prefix // empty' "$config_file" 2>/dev/null)
    else
        # Fallback: grep + sed
        prefix=$(grep -o '"linear_ticket_prefix"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_file" 2>/dev/null | sed 's/.*"\([^"]*\)".*/\1/')
    fi

    # Validate prefix is non-empty and alphabetic
    if [ -z "$prefix" ] || ! [[ "$prefix" =~ ^[A-Z]+$ ]]; then
        echo "$default" >&2
        echo "Warning: Invalid or missing linear_ticket_prefix in config, using default: $default" >&2
        echo "$default"
        return
    fi

    echo "$prefix"
}
```

---

## State Transitions

### Configuration Lifecycle

```
[No Config]
    |
    | specify init (user prompted)
    |
    v
[Config Created] (.specify/config.json written)
    |
    | Git commit
    |
    v
[Config Committed] (shared with team)
    |
    | Team member clones repo
    |
    v
[Config Available] (workflow scripts read prefix)
    |
    | create-new-feature.sh execution
    |
    v
[Prefix Applied] (branch created as PREFIX-NUMBER-description)
```

### Legacy Migration Path

```
[Legacy Repo] (no config)
    |
    | User runs workflow script
    |
    v
[Fallback Triggered] (scripts use 001- format)
    |
    | User manually creates .specify/config.json
    |   OR
    | User re-runs specify init (if supported in future)
    |
    v
[Config Available] (new branches use custom format)
    |
    v
[Mixed Format Repo] (old: 001-, new: AFR-1234-)
```

---

## Data Relationships

### Config → Branch Name

```
ProjectConfig
  .linear_ticket_prefix = "AFR"
           ↓
  create-new-feature.sh reads config
           ↓
  Branch name generation: "AFR-{number}-{description}"
           ↓
  Git branch created: "AFR-1234-add-user-auth"
```

### Config → Spec Directory

```
ProjectConfig
  .linear_ticket_prefix = "AFR"
           ↓
  Branch name: "AFR-1234-add-user-auth"
           ↓
  Spec directory: "specs/AFR-1234-add-user-auth/"
           ↓
  Feature artifacts: spec.md, plan.md, tasks.md
```

### Config → Commit Messages (Documentation Only)

```
ProjectConfig
  .commit_format = "{prefix}-{number} {message}"
           ↓
  Documentation (README, constitution)
           ↓
  Developer reads format guidance
           ↓
  Manual commit: "git commit -m 'AFR-1234 Add auth endpoint'"
```

**Note**: Commit format is **not programmatically enforced** in v1, only documented for team guidance.

---

## Backward Compatibility

### Format Detection Logic

```
Repository Root
    |
    +-- .specify/config.json exists?
            |
            YES ─→ [New Format Mode]
            |         ↓
            |     Read linear_ticket_prefix
            |         ↓
            |     Create branches as PREFIX-NUMBER-description
            |
            NO ──→ [Legacy Format Mode]
                      ↓
                  Use numeric prefix (001, 002, 003...)
                      ↓
                  Create branches as NNN-description
```

### Mixed Format Support

**Scenario**: Repository has both old and new format branches

**Branch List Example**:
```
001-initial-feature      (legacy)
002-bug-fix             (legacy)
AFR-1234-new-feature    (new format)
AFR-1235-another-feature (new format)
```

**Script Behavior**:
- **common.sh** regex matches both formats
- **find_feature_dir_by_prefix()** works with both patterns
- **check_feature_branch()** validates both formats
- No conflicts or errors

---

## Validation Examples

### Example 1: Valid Configuration

**Input during `specify init`**:
```
Ticket prefix: AFR
```

**Config Written**:
```json
{
  "linear_ticket_prefix": "AFR"
}
```

*Note: Minimal config. Optional fields (`branch_format`, `commit_format`) use defaults if not specified.*

**Result**: ✅ Config created, branches use AFR-NNN- format

---

### Example 2: Invalid Input (Re-prompt)

**Input during `specify init`**:
```
Ticket prefix: AFR-123
```

**CLI Response**:
```
[red]Invalid format. Use letters only (e.g., AFR, ASR, PROJ)[/red]
Ticket prefix: _
```

**Result**: User re-prompted until valid input

---

### Example 3: Empty Input (Default)

**Input during `specify init`**:
```
Ticket prefix: [Enter]
```

**CLI Response**:
```
[dim]Using default: AUROR-XXX[/dim]
```

**Config Written**:
```json
{
  "linear_ticket_prefix": "AUROR"
}
```

**Result**: ✅ Default prefix applied

---

### Example 4: Malformed Config (Fallback)

**Config File** (corrupted):
```json
{
  "linear_ticket_prefix": "AFR
  "script_type": "sh"
}
```

**Script Behavior**:
```bash
$ ./create-new-feature.sh "Add feature"
Warning: Invalid or missing linear_ticket_prefix in config, using default: AUROR
Branch created: AUROR-001-add-feature
```

**Result**: ✅ Graceful degradation to default

---

## Schema Contract

See [contracts/config-schema.json](./contracts/config-schema.json) for formal JSON Schema definition.

**Key Constraints**:
- `linear_ticket_prefix`: Required, string, pattern `^[A-Z]{2,10}$`
- `script_type`: Required, enum `["sh", "ps"]`
- `ai_assistant`: Required, string
- `branch_format`: Optional, string (default provided)
- `commit_format`: Optional, string (default provided)

---

## Future Enhancements

### Version 2: Configurable Templates

Allow users to customize `branch_format` and `commit_format` templates:

```json
{
  "linear_ticket_prefix": "AFR",
  "branch_format": "{prefix}/{number}/{description}",  // Custom: AFR/1234/feature-name
  "commit_format": "[{prefix}-{number}] {message}"      // Custom: [AFR-1234] message
}
```

**Impact**: Requires template engine in bash scripts

---

### Version 3: Multiple Ticket Systems

Support multiple ticket systems simultaneously:

```json
{
  "ticket_systems": {
    "linear": {
      "prefix": "AFR",
      "pattern": "{prefix}-{number}-{description}"
    },
    "jira": {
      "prefix": "PROJ",
      "pattern": "{prefix}-{number}-{description}"
    }
  },
  "default_system": "linear"
}
```

**Impact**: More complex config schema, system selection during feature creation

---

**Data Model Complete** | Schema defined | Validation rules documented
