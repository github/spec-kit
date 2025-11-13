# Quickstart: Custom Linear Ticket Format

**Feature**: 001-custom-ticket-format
**For**: Developers implementing or using this feature

## TL;DR

Teams can configure their Linear ticket prefix (e.g., AFR, ASR) during `specify init`. This drives branch names, spec directories, and commit conventions.

**Example**:
```bash
# During init, when prompted:
Ticket prefix: AFR

# Creates config:
.specify/config.json → {"linear_ticket_prefix": "AFR", ...}

# Future branches:
AFR-1234-add-feature
AFR-1235-fix-bug

# Spec directories:
specs/AFR-1234-add-feature/
specs/AFR-1235-fix-bug/
```

---

## For Users: Using Custom Format

### Initial Setup (New Project)

```bash
# Initialize new project
$ specify init my-project

# When prompted for ticket prefix:
Ticket prefix: AFR

✓ Linear ticket format set to: AFR-XXXX

# Config created: .specify/config.json
```

**Default**: Press Enter without input → uses `AUROR` prefix

---

### Creating Features with Custom Format

**Automatic numbering**:
```bash
$ cd my-project
$ .specify/scripts/bash/create-new-feature.sh "Add user authentication"

# Branch created: AFR-001-add-user-authentication
# Spec dir: specs/AFR-001-add-user-authentication/
```

**Explicit ticket number** (future enhancement):
```bash
$ .specify/scripts/bash/create-new-feature.sh --linear-ticket AFR-1234 "Add user authentication"

# Branch created: AFR-1234-add-user-authentication
# Spec dir: specs/AFR-1234-add-user-authentication/
```

---

### Commit Message Convention

Use the format: `PREFIX-NUMBER Description`

**Examples**:
```bash
git commit -m "AFR-1234 Add authentication endpoint"
git commit -m "AFR-1234 Update validation logic"
git commit -m "AFR-1234 Fix type error in auth service"
```

**Note**: Commit format is documentation only (not programmatically enforced in v1)

---

### Team Examples

**Auror Facial Recognition (AFR)**:
```
Branches: AFR-1234-add-detection, AFR-1235-fix-enrollment
Commits: AFR-1234 Add detection endpoint
```

**Auror Subject Recognition (ASR)**:
```
Branches: ASR-42-improve-accuracy, ASR-43-add-logging
Commits: ASR-42 Improve detection accuracy
```

**Default (AUROR)**:
```
Branches: AUROR-123-new-feature, AUROR-124-bug-fix
Commits: AUROR-123 Add new feature
```

---

## For Developers: Implementation Reference

### Files Modified

| File | Purpose | Changes |
|------|---------|---------|
| `src/specify_cli/__init__.py` | CLI | Add prompt after script selection (~40 lines) |
| `.specify/scripts/bash/create-new-feature.sh` | Feature creation | Read config, custom naming (~60 lines) |
| `.specify/scripts/bash/common.sh` | Shared functions | Dual regex patterns (~30 lines) |
| `README.md` | Documentation | Add config section (~50 lines) |
| `.specify/templates/constitution-template.md` | Template | Linear format conventions (~30 lines) |

---

### Config File Structure

**Location**: `.specify/config.json` (project root)
**Git Status**: Committed (team-shared)

**Minimal config**:
```json
{
  "linear_ticket_prefix": "AFR"
}
```

**Full config** (with optional fields):
```json
{
  "linear_ticket_prefix": "AFR",
  "branch_format": "{prefix}-{number}-{description}",
  "commit_format": "{prefix}-{number} {message}"
}
```

**Schema**: See [contracts/config-schema.json](./contracts/config-schema.json)

---

### Python CLI Integration

**Location**: `src/specify_cli/__init__.py` lines 1010-1050

**Pseudo-code**:
```python
# After script type selection
console.print("\n[cyan]Linear Ticket Format Configuration[/cyan]")
linear_prefix = input("Ticket prefix: ").strip().upper()

# Validate
while not validate_prefix(linear_prefix):
    console.print("[red]Invalid format. Letters only (e.g., AFR, ASR)[/red]")
    linear_prefix = input("Ticket prefix: ").strip().upper()

# Default handling
if not linear_prefix:
    linear_prefix = "AUROR"

# Save to config
config_file = project_path / ".specify" / "config.json"
config_data = {"linear_ticket_prefix": linear_prefix}
config_file.write_text(json.dumps(config_data, indent=2))

console.print(f"[green]✓[/green] Linear ticket format set to: {linear_prefix}-XXXX")
```

---

### Bash Script Integration

**Config Reading** (add to `common.sh`):
```bash
read_config_prefix() {
    local config_file="$REPO_ROOT/.specify/config.json"
    local default="AUROR"

    # File doesn't exist → legacy mode
    [ ! -f "$config_file" ] && echo "$default" && return

    # Try jq first
    if command -v jq >/dev/null 2>&1; then
        prefix=$(jq -r '.linear_ticket_prefix // empty' "$config_file" 2>/dev/null)
    else
        # Fallback: grep + sed
        prefix=$(grep -o '"linear_ticket_prefix"[[:space:]]*:[[:space:]]*"[^"]*"' "$config_file" | sed 's/.*"\([^"]*\)".*/\1/')
    fi

    # Validate and default
    [ -z "$prefix" ] || ! [[ "$prefix" =~ ^[A-Z]+$ ]] && prefix="$default"

    echo "$prefix"
}
```

**Branch Creation** (modify `create-new-feature.sh`):
```bash
# Read config
LINEAR_PREFIX=$(read_config_prefix)

# Determine if legacy mode (no config file)
CONFIG_FILE="$REPO_ROOT/.specify/config.json"
if [ -f "$CONFIG_FILE" ]; then
    USE_CUSTOM_FORMAT=true
else
    USE_CUSTOM_FORMAT=false
fi

# Generate branch name
if $USE_CUSTOM_FORMAT; then
    # New format: AFR-001-description
    HIGHEST=$(find_highest_with_prefix "$LINEAR_PREFIX")
    BRANCH_NUMBER=$((HIGHEST + 1))
    BRANCH_NAME="${LINEAR_PREFIX}-${BRANCH_NUMBER}-${description}"
else
    # Legacy format: 001-description
    HIGHEST=$(find_highest_numeric)
    BRANCH_NUMBER=$(printf "%03d" $((HIGHEST + 1)))
    BRANCH_NAME="${BRANCH_NUMBER}-${description}"
fi
```

**Regex Updates** (modify `common.sh`):
```bash
# Old regex: ^([0-9]{3})-
# New regex: ^(([0-9]{3})|([A-Z]+-[0-9]+))-

# get_current_branch() - Line 40
if [[ "$dirname" =~ ^(([0-9]{3})|([A-Z]+-[0-9]+))- ]]; then
    # Extract number...
fi

# check_feature_branch() - Line 75
if [[ ! "$branch" =~ ^(([0-9]{3})|([A-Z]+-[0-9]+))- ]]; then
    echo "ERROR: Not on a feature branch" >&2
    echo "Expected format: 001-name or AFR-1234-name" >&2
    exit 1
fi
```

---

### Backward Compatibility

**Legacy Projects** (no config file):
- Scripts detect missing `.specify/config.json`
- Fall back to numeric format: `001-`, `002-`, `003-`
- No breaking changes

**Mixed Repositories**:
- Old branches: `001-feature`, `002-bugfix`
- New branches: `AFR-1234-feature`, `AFR-1235-bugfix`
- Both formats work simultaneously

**Migration**:
```bash
# Option 1: Manual config creation
echo '{"linear_ticket_prefix":"AFR"}' > .specify/config.json
git add .specify/config.json
git commit -m "Configure Linear ticket format: AFR"

# Option 2: Re-run init (future enhancement)
specify init --reconfigure
```

---

## Testing Scenarios

### Scenario 1: New Project (Default)

```bash
$ specify init test-project
# Prompt: Ticket prefix: [Enter]
# Result: AUROR prefix

$ cat .specify/config.json
{"linear_ticket_prefix": "AUROR"}

$ .specify/scripts/bash/create-new-feature.sh "Test feature"
# Branch: AUROR-001-test-feature
```

---

### Scenario 2: New Project (Custom)

```bash
$ specify init test-project
# Prompt: Ticket prefix: AFR
# Result: AFR prefix

$ cat .specify/config.json
{"linear_ticket_prefix": "AFR"}

$ .specify/scripts/bash/create-new-feature.sh "Test feature"
# Branch: AFR-001-test-feature
```

---

### Scenario 3: Legacy Project

```bash
$ ls .specify/
# No config.json file

$ .specify/scripts/bash/create-new-feature.sh "Test feature"
# Branch: 001-test-feature (legacy format)
```

---

### Scenario 4: Invalid Input

```bash
$ specify init test-project
# Prompt: Ticket prefix: AFR-123
# Error: Invalid format. Use letters only (e.g., AFR, ASR, PROJ)
# Re-prompt: Ticket prefix: AFR
# Result: AFR prefix saved
```

---

## Troubleshooting

### Problem: Branches still using `001-` format after config

**Solution**:
```bash
# Verify config exists and is valid
$ cat .specify/config.json
{"linear_ticket_prefix": "AFR"}

# Check bash can read it
$ jq -r '.linear_ticket_prefix' .specify/config.json
AFR

# If jq not installed, install it:
# macOS: brew install jq
# Linux: apt-get install jq / yum install jq
# Windows (Git Bash): choco install jq or scoop install jq
```

---

### Problem: Config file missing

**Solution**:
```bash
# Create minimal config manually
$ echo '{"linear_ticket_prefix":"AFR"}' > .specify/config.json

# Or run init again (if re-init supported)
$ specify init --here
```

---

### Problem: Mixed formats in repository

**This is expected and supported!**

Old branches (`001-`, `002-`) continue working.
New branches use custom format (`AFR-1234-`).
Both coexist without conflicts.

---

## Reference

- **Spec**: [spec.md](./spec.md)
- **Plan**: [plan.md](./plan.md)
- **Research**: [research.md](./research.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Schema**: [contracts/config-schema.json](./contracts/config-schema.json)
- **Affected Files**: [affected-files.md](./affected-files.md)

---

**Ready to implement!** See [tasks.md](./tasks.md) for actionable task list (run `/speckit.tasks`)
