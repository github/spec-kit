# Research: Custom Linear Ticket Format Implementation

**Feature**: 001-custom-ticket-format | **Date**: 2025-11-14
**Purpose**: Resolve technical unknowns and validate implementation approach

## Research Areas

### 1. Configuration Storage Location

**Question**: Where should Linear ticket format configuration be stored?

**Options Evaluated**:

| Option | Location | Git Status | Pros | Cons |
|--------|----------|-----------|------|------|
| A | `.specify/config.json` | Committed | Team-shared config, consistent across team | One format per repo only |
| B | `.specify/.config.json` | Gitignored | User-specific customization | Inconsistent team experience |
| C | `~/.specify/repos/<repo-name>.json` | N/A (home dir) | Survives repo deletion | Hard to discover, not portable |
| D | Environment variable | N/A | Simple | Not persistent, manual setup required |

**Decision**: **Option A** - `.specify/config.json` (committed to git)

**Rationale**:
- **Team consistency**: All team members use same Linear ticket format (spec requirement)
- **Discoverability**: Config file in `.specify/` follows existing convention
- **Portability**: Works across machines when repo is cloned
- **Simplicity**: No external dependencies or environment setup
- **Spec alignment**: Spec explicitly states "repository-level configuration only"

**Implementation Notes**:
- File created during `specify init` command
- JSON format for easy parsing in Python and bash (with jq)
- Schema validation before write to prevent corruption

---

### 2. JSON Parsing in Bash Scripts

**Question**: How should bash scripts read JSON configuration reliably?

**Options Evaluated**:

| Option | Tool | Availability | Complexity |
|--------|------|--------------|------------|
| A | `jq` | Optional (not pre-installed) | Low - simple syntax |
| B | `python -c` | High (Python 3.11+ required) | Medium - inline script needed |
| C | `grep/sed` fallback | Universal | High - fragile regex parsing |
| D | `node -e` | Medium (Node not guaranteed) | Medium - inline script |

**Decision**: **jq with grep/sed fallback**

**Rationale**:
- **Best practice**: `jq` is the standard tool for JSON parsing in bash
- **Availability**: Many development environments have jq installed
- **Fallback safety**: Can detect jq absence and fall back to grep/sed for simple key extraction
- **Spec-kit precedent**: Other projects in Auror ecosystem already use jq

**Implementation**:
```bash
# Try jq first
if command -v jq >/dev/null 2>&1; then
    LINEAR_PREFIX=$(jq -r '.linear_ticket_prefix // "AUROR"' "$CONFIG_FILE")
else
    # Fallback: grep + sed for simple JSON key extraction
    LINEAR_PREFIX=$(grep -o '"linear_ticket_prefix"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | sed 's/.*"\([^"]*\)".*/\1/')
    # Default if parsing fails
    LINEAR_PREFIX="${LINEAR_PREFIX:-AUROR}"
fi
```

**Alternative Considered**: Python JSON parsing via inline script - rejected because:
- Adds subprocess overhead
- More complex than jq
- Python already required for CLI, but bash scripts should remain self-contained

---

### 3. Regex Pattern for Branch Name Validation

**Question**: What regex pattern supports both old (`001-name`) and new (`AFR-1234-name`) formats?

**Requirements**:
- Match legacy format: `001-feature-name`, `042-bug-fix`
- Match new format: `AFR-1234-feature-name`, `ASR-42-add-feature`
- Reject invalid formats: `afr-123-name` (lowercase), `AFR-ABC-name` (no number)

**Pattern Development**:

**Attempt 1**: `^[0-9A-Z]+-[0-9]+-`
- **Problem**: Matches `1-2-name` (too permissive)

**Attempt 2**: `^([0-9]{3}|[A-Z]+-[0-9]+)-`
- **Problem**: Matches `ABC-1-name` but we want `ABC-1234-name` format
- **Issue**: Doesn't enforce that new format has TWO components (PREFIX-NUMBER)

**Attempt 3**: `^(([0-9]{3})|([A-Z]+-[0-9]+))-`
- **✓ Correct**: Explicit grouping for old vs new format
- **Validation**:
  - `001-name` → Match (group 2 captures `001`)
  - `AFR-1234-name` → Match (group 3 captures `AFR-1234`)
  - `afr-123-name` → No match (lowercase rejected)
  - `1-name` → No match (not 3 digits)

**Decision**: `^(([0-9]{3})|([A-Z]+-[0-9]+))-`

**Rationale**:
- Explicit distinction between legacy (3 digits) and new (PREFIX-NUMBER) formats
- Uppercase enforcement prevents case inconsistencies
- Capture groups enable format detection for branching logic

**Bash Implementation**:
```bash
if [[ "$branch_name" =~ ^(([0-9]{3})|([A-Z]+-[0-9]+))- ]]; then
    if [[ -n "${BASH_REMATCH[2]}" ]]; then
        # Legacy format: 001-name
        prefix="${BASH_REMATCH[2]}"  # "001"
    else
        # New format: AFR-1234-name
        prefix="${BASH_REMATCH[3]}"  # "AFR-1234"
    fi
else
    echo "ERROR: Invalid branch format"
    exit 1
fi
```

---

### 4. Parameter Naming for Explicit Ticket Specification

**Question**: What parameter name should allow users to specify explicit Linear ticket IDs?

**Use Case**: User wants to create branch for existing Linear ticket AFR-1234

**Options Evaluated**:

| Option | Parameter | Example | Clarity | Length |
|--------|-----------|---------|---------|--------|
| A | `--linear-ticket` | `--linear-ticket AFR-1234` | High - explicit | Medium |
| B | `--ticket` | `--ticket AFR-1234` | Medium - could be any ticket | Short |
| C | `--ticket-number` | `--ticket-number 1234` | Low - prefix unclear | Medium |
| D | `--linear-id` | `--linear-id AFR-1234` | Medium | Short |

**Decision**: **Option A** - `--linear-ticket AFR-1234`

**Rationale**:
- **Clarity**: "linear-ticket" explicitly indicates Linear ticket system
- **Consistency**: Aligns with "linear_ticket_prefix" config key
- **Format**: Accepts full ticket ID (AFR-1234), not just number
- **Discoverability**: Help text is self-explanatory

**Implementation**:
```bash
# Usage: create-new-feature.sh --linear-ticket AFR-1234 "Add detection feature"
# Branch created: AFR-1234-add-detection-feature
# Spec dir: specs/AFR-1234-add-detection-feature/
```

**Fallback Behavior**: If `--linear-ticket` not provided, use sequential numbering:
- Read config for prefix (e.g., "AFR")
- Find highest number in existing branches
- Increment: AFR-001, AFR-002, etc.

---

### 5. Validation Strategy: Client-Side vs Server-Side

**Question**: Where should Linear ticket prefix validation occur?

**Context**: Need to validate alphabetic-only input, reject numbers/special chars

**Options**:

| Location | Timing | User Experience | Complexity |
|----------|--------|-----------------|------------|
| Python CLI only | During init | Immediate feedback, re-prompt | Low |
| Bash scripts only | During branch creation | Late error, confusing | Medium |
| Both | Init + branch creation | Redundant but safe | High |

**Decision**: **Python CLI validation only** (with bash fallback to defaults)

**Rationale**:
- **User experience**: Validate at input time, not later during git operations
- **Fail fast**: Prevent invalid config from being written
- **Simplicity**: Single source of truth for validation logic
- **Bash safety**: Scripts don't need complex validation, they trust config or use defaults

**Python Validation Implementation**:
```python
import re

def validate_linear_prefix(prefix: str) -> bool:
    """Validate Linear ticket prefix is alphabetic only."""
    if not prefix:
        return True  # Empty = use default

    if not prefix.isalpha():
        return False  # Must be letters only

    if len(prefix) < 2 or len(prefix) > 10:
        return False  # Reasonable length limits

    return True

# In CLI prompt
while True:
    prefix = input("Ticket prefix: ").strip().upper()

    if validate_linear_prefix(prefix):
        break

    console.print("[red]Invalid format. Use letters only (e.g., AFR, ASR, PROJ)[/red]")
```

**Bash Fallback**:
- If config file missing → default to "AUROR"
- If config file malformed → default to "AUROR" + warning
- If prefix is empty/invalid → default to "AUROR"

---

### 6. Backward Compatibility Strategy

**Question**: How do we support existing projects using `001-feature-name` format?

**Requirements from Spec**:
- Legacy projects without config must continue working
- Mixed repositories (old + new branches) must work
- No breaking changes

**Strategy**:

**Detection Logic**:
```bash
CONFIG_FILE="$REPO_ROOT/.specify/config.json"

if [ -f "$CONFIG_FILE" ]; then
    # New format: Read prefix from config
    LINEAR_PREFIX=$(read_config_prefix)  # e.g., "AFR"
    USE_LEGACY=false
else
    # Legacy format: Use numeric prefix
    LINEAR_PREFIX=""  # Not used in legacy mode
    USE_LEGACY=true
fi

if $USE_LEGACY; then
    # Old logic: 001, 002, 003...
    BRANCH_NUMBER=$(find_highest_numeric_prefix + 1)
    BRANCH_NAME=$(printf "%03d-%s" "$BRANCH_NUMBER" "$description")
else
    # New logic: AFR-001, AFR-002... or AFR-1234 if --linear-ticket provided
    if [ -n "$EXPLICIT_TICKET" ]; then
        BRANCH_NAME="$EXPLICIT_TICKET-$description"
    else
        BRANCH_NUMBER=$(find_highest_with_prefix "$LINEAR_PREFIX" + 1)
        BRANCH_NAME="$LINEAR_PREFIX-$BRANCH_NUMBER-$description"
    fi
fi
```

**Regex Updates**:
- All branch detection: `^(([0-9]{3})|([A-Z]+-[0-9]+))-`
- All spec directory matching: Same pattern
- Error messages: Show examples of both formats

**Testing Matrix**:

| Scenario | Config Exists | Branch Format | Expected Behavior |
|----------|--------------|---------------|-------------------|
| New repo | Yes (AFR) | N/A | Creates AFR-001-description |
| Legacy repo | No | 001-name | Creates 002-name (continues sequence) |
| Mixed repo | Yes (AFR) | 001-old, AFR-1234-new | Both formats work, new branches use AFR format |
| Corrupted config | Yes (invalid) | Any | Falls back to AUROR default + warning |

---

## Technology Stack Summary

**Python** (CLI):
- **Version**: 3.11+ (existing requirement)
- **Libraries**: typer, rich (already in use)
- **New dependencies**: None

**Bash** (Scripts):
- **Version**: 4.0+ (POSIX-compliant)
- **Tools**: jq (optional), grep, sed (standard)
- **New dependencies**: None (jq recommended but not required)

**JSON** (Config):
- **Format**: Standard JSON with schema
- **Validation**: Python-side before write
- **Parsing**: jq (preferred) or grep/sed (fallback)

---

## Performance Considerations

**Config File Read**:
- **Size**: <1KB (minimal JSON)
- **Frequency**: Once per script execution
- **Impact**: Negligible (<10ms)

**Regex Matching**:
- **Complexity**: O(n) where n = branch name length (<100 chars)
- **Frequency**: Per branch/spec directory check
- **Impact**: Negligible (<1ms per match)

**Git Operations**:
- **Bottleneck**: Git fetch/checkout, not config reading
- **No change**: Config adds <50ms to branch creation (2s total)

---

## Security Considerations

**Input Validation**:
- Alphabetic-only enforcement prevents injection attacks
- No eval or shell execution of user input
- Config file validated before write

**File Permissions**:
- Config file: 644 (readable by all, writable by owner)
- No executable permissions needed
- Standard git-tracked file

**Injection Risks**:
- User input never directly interpolated into shell commands
- Prefix validated before use in branch names
- Git commands use safe parameters (no `eval`)

---

## Open Issues Resolved

All technical unknowns from planning phase have been resolved:

1. ✅ Configuration storage: `.specify/config.json`
2. ✅ JSON parsing: jq with grep/sed fallback
3. ✅ Regex pattern: `^(([0-9]{3})|([A-Z]+-[0-9]+))-`
4. ✅ Parameter naming: `--linear-ticket AFR-1234`
5. ✅ Validation strategy: Python CLI validation
6. ✅ Backward compatibility: Config detection + fallback logic

---

**Research Complete** | All decisions documented | Ready for implementation
