# Affected Files for Custom Linear Ticket Format Feature

## Summary

This document lists all files that need to be modified or created to implement the custom Linear ticket format feature.

## Files to Modify

### 1. Core Scripts (CRITICAL)

#### [src/specify_cli/__init__.py](../../src/specify_cli/__init__.py)
**Purpose**: Add Linear ticket format prompt during `specify init`

**Changes**:
- Lines 1010-1013: Add prompt after script type selection
- Add validation for alphabetic-only input
- Create/update `.specify/config.json` with linear_ticket_prefix
- Update completion messages to show configured format

**Effort**: Medium (50-80 lines)

---

#### [.specify/scripts/bash/create-new-feature.sh](../../.specify/scripts/bash/create-new-feature.sh)
**Purpose**: Read config and create branches with custom format

**Changes**:
- Lines 1-68: Add parameter parsing for `--linear-ticket` or `--ticket-number`
- Lines 131-134: Read `.specify/config.json` for `linear_ticket_prefix`
- Lines 183-214: Update branch name generation:
  - If ticket number provided: `PREFIX-NUMBER-description`
  - If not provided: Fall back to sequential `PREFIX-001-description`
- Lines 84-112: Update `check_existing_branches()` to handle both formats
- Add jq dependency check or fallback parsing

**Effort**: High (100-150 lines)

---

#### [.specify/scripts/bash/common.sh](../../.specify/scripts/bash/common.sh)
**Purpose**: Update shared functions to support both old and new formats

**Changes**:
- Line 40: `get_current_branch()` - Update regex from `^([0-9]{3})-` to `^(([A-Z]+-[0-9]+)|([0-9]{3}))-`
- Line 75: `check_feature_branch()` - Update validation regex and error messages
- Line 94: `find_feature_dir_by_prefix()` - Update prefix extraction regex
- Add config reading utility function
- Support both legacy (`001-`) and new (`AFR-1234-`) formats

**Effort**: Medium (40-60 lines)

---

### 2. Documentation Files

#### [README.md](../../README.md)
**Purpose**: Document custom Linear ticket format feature

**Changes**:
- Add section explaining Linear ticket format configuration
- Provide examples from multiple teams (AFR, ASR, AUROR)
- Document branch naming convention: `PREFIX-NUMBER-description`
- Document commit message convention: `PREFIX-NUMBER Description`
- Add troubleshooting section for format issues

**Effort**: Low (20-40 lines)

---

#### [.specify/templates/constitution-template.md](../../.specify/templates/constitution-template.md)
**Purpose**: Include Linear ticket format in project constitution

**Changes**:
- Add section under "Naming Conventions" or "Git Workflow"
- Explain configured ticket format for the project
- Provide team-specific examples
- Document expected branch and commit formats

**Effort**: Low (15-30 lines)

---

## Files to Create

### [.specify/config.json](../../.specify/config.json)
**Purpose**: Store Linear ticket format configuration

**Format**:
```json
{
  "linear_ticket_prefix": "AFR",
  "script_type": "sh",
  "ai_assistant": "claude",
  "branch_format": "{prefix}-{number}-{description}",
  "commit_format": "{prefix}-{number} {message}"
}
```

**Created by**: `specify init` command
**Git status**: Should be gitignored (team uses same config) OR committed (team shares config)

---

## Files That Auto-Inherit Changes

### [.specify/scripts/bash/setup-plan.sh](../../.specify/scripts/bash/setup-plan.sh)
**No changes needed** - Uses `common.sh` functions, will automatically support new format once `common.sh` is updated

---

## Testing Files Needed

### New Test Files

1. **`tests/test_linear_ticket_format.sh`** - Integration tests for feature creation with custom formats
2. **`tests/test_backward_compatibility.sh`** - Tests for legacy `001-` format support
3. **`tests/test_config_validation.sh`** - Tests for config validation and error handling

---

## Implementation Order

**Phase 1: Configuration** (P1)
1. Update `src/specify_cli/__init__.py` - Add prompt and config saving
2. Test config creation manually

**Phase 2: Core Scripts** (P2)
3. Update `.specify/scripts/bash/common.sh` - Shared functions
4. Update `.specify/scripts/bash/create-new-feature.sh` - Feature creation
5. Test branch creation with both formats

**Phase 3: Documentation** (P3)
6. Update `README.md`
7. Update `.specify/templates/constitution-template.md`

**Phase 4: Validation** (P4)
8. Create integration tests
9. Test backward compatibility
10. Test edge cases

---

## Backward Compatibility Notes

All modified scripts MUST support both formats:
- **Legacy**: `001-feature-name`, `002-bug-fix`
- **New**: `AFR-1234-feature-name`, `ASR-42-bug-fix`

Detection strategy:
- If `.specify/config.json` exists → use configured format
- If no config file → assume legacy format
- Regex patterns match both formats

---

## Risk Assessment

**Low Risk**:
- README.md updates
- constitution-template.md updates

**Medium Risk**:
- src/specify_cli/__init__.py - Well-tested init command, adding new section
- common.sh - Heavily used but changes are isolated to regex patterns

**High Risk**:
- create-new-feature.sh - Complex logic, many edge cases to handle
- Backward compatibility - Must not break existing workflows

---

## Validation Checklist

Before considering implementation complete:

- [ ] New projects can configure custom Linear ticket format
- [ ] Branches created with custom format (e.g., `AFR-1234-feature-name`)
- [ ] Spec directories match branch names
- [ ] Legacy projects (no config) continue working with `001-` format
- [ ] Mixed repositories support both old and new branch formats
- [ ] Invalid input (numbers, special chars) rejected with clear errors
- [ ] README includes multi-team examples
- [ ] Constitution template updated
- [ ] Config persists across terminal sessions
- [ ] Error messages show correct format examples
