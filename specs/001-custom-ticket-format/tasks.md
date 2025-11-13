# Implementation Tasks: Custom Linear Ticket Format Configuration

**Branch**: `001-custom-ticket-format` | **Date**: 2025-11-14
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Task Summary

**Total Tasks**: 23
**Parallelizable**: 8 tasks marked [P]
**User Stories**: 5 (1 P1, 2 P2, 2 P3)
**Estimated Effort**: ~6-8 hours

### Task Distribution by User Story

| User Story | Priority | Tasks | Description |
|------------|----------|-------|-------------|
| US1 | P1 | 5 | Configure format during init (CLI prompt) |
| US2-US3 | P2 | 9 | Branch and spec directory creation (bash scripts) |
| US4-US5 | P3 | 6 | Documentation updates |
| Testing | - | 3 | Integration and validation |

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)
**User Story 1 only** - Configure Linear ticket format during `specify init`. This provides the foundational capability to store team preferences.

**Value**: Teams can configure their Linear ticket prefix, which is saved to `.specify/config.json`. This enables future enhancements without requiring users to reconfigure.

### Incremental Delivery Plan

1. **First Increment (US1)**: Configuration infrastructure
   - Teams can set Linear prefix during init
   - Config persists in `.specify/config.json`
   - **Independent Test**: Run `specify init`, enter prefix, verify config file

2. **Second Increment (US2-US3)**: Core workflow integration
   - Branches and specs use configured format
   - Backward compatibility with legacy format
   - **Independent Test**: Create branch with custom format, verify naming

3. **Third Increment (US4-US5)**: Documentation and adoption
   - README and constitution updated
   - Multi-team examples provided
   - **Independent Test**: Review docs, verify clarity and completeness

---

## Dependencies

### Story Completion Order

```
US1 (P1: Configure Format)
    ↓ (blocks)
US2-US3 (P2: Use Format in Scripts)
    ↓ (independent)
US4-US5 (P3: Document Feature)
```

**Rationale**: US1 must complete first because US2-US3 read the config file that US1 creates. US4-US5 are independent documentation tasks that can proceed once the feature is understood.

### Task Dependencies Within Stories

- **US1**: Sequential (validation → save → confirm)
- **US2-US3**: Some parallelization possible (common.sh and create-new-feature.sh can be updated simultaneously by different developers)
- **US4-US5**: Fully parallel (README and constitution are separate files)

---

## Phase 1: Setup

**Goal**: Verify existing project structure (no setup tasks needed for this feature)

- [x] T001 Review current codebase structure per plan.md (Python CLI + bash scripts)

**Status**: ✅ No additional setup required - modifying existing files only

---

## Phase 2: User Story 1 - Configure Linear Ticket Format (P1)

**Goal**: Enable teams to configure their Linear ticket prefix during `specify init`

**Why P1**: Foundational capability - config must exist before scripts can read it

**Independent Test Criteria**:
```bash
# Test 1: Default format
specify init test-project
# Prompt: [Enter]
# Verify: .specify/config.json contains {"linear_ticket_prefix": "AUROR"}

# Test 2: Custom format
specify init test-project
# Prompt: AFR
# Verify: .specify/config.json contains {"linear_ticket_prefix": "AFR"}

# Test 3: Invalid input
specify init test-project
# Prompt: AFR-123
# Verify: Error displayed, re-prompted until valid
```

### Implementation Tasks

- [x] T002 [US1] Add Linear ticket format prompt after script type selection in src/specify_cli/__init__.py (line 1010)
- [x] T003 [US1] Implement prefix validation function (alphabetic only, 2-10 chars) in src/specify_cli/__init__.py
- [x] T004 [US1] Add re-prompt logic for invalid input with clear error messages in src/specify_cli/__init__.py
- [x] T005 [US1] Implement config file creation and JSON serialization to .specify/config.json in src/specify_cli/__init__.py
- [x] T006 [US1] Add confirmation message displaying configured format (e.g., "Linear ticket format set to: AFR-XXXX") in src/specify_cli/__init__.py

### Manual Testing Checklist

- [ ] Run `specify init` and press Enter → Verify AUROR default
- [ ] Run `specify init` and enter "AFR" → Verify AFR saved
- [ ] Run `specify init` and enter "AFR-123" → Verify error and re-prompt
- [ ] Run `specify init` and enter "a" → Verify error (too short)
- [ ] Verify config file format: `{"linear_ticket_prefix": "AFR"}`

**Exit Criteria**: Configuration can be set during init and persists to `.specify/config.json`

---

## Phase 3: User Story 2-3 - Branch and Spec Directory Creation (P2)

**Goal**: Update bash scripts to read config and create branches/specs with custom format

**Why P2**: Core workflow - teams need branches that match their ticket format

**Combined User Stories**: US2 (branches) and US3 (spec directories) use the same script (`create-new-feature.sh`), so they're implemented together for efficiency.

**Independent Test Criteria**:
```bash
# Setup: Create config with AFR prefix
echo '{"linear_ticket_prefix":"AFR"}' > .specify/config.json

# Test 1: Branch creation
.specify/scripts/bash/create-new-feature.sh "Add feature"
# Verify: Branch created as AFR-001-add-feature
# Verify: Spec dir created as specs/AFR-001-add-feature/

# Test 2: Legacy compatibility (no config)
rm .specify/config.json
.specify/scripts/bash/create-new-feature.sh "Add feature"
# Verify: Branch created as 001-add-feature (legacy format)

# Test 3: Mixed repository
# Create both old (001-) and new (AFR-) branches
# Verify: Both formats work without conflicts
```

### Foundational Tasks (Shared Utilities)

- [x] T007 [P] [US2] Add read_config_prefix() function to .specify/scripts/bash/common.sh (reads .specify/config.json with jq fallback)
- [x] T008 [P] [US2] Update get_current_branch() regex pattern to `^(([0-9]{3})|([A-Z]+-[0-9]+))-` in .specify/scripts/bash/common.sh (line 40)
- [x] T009 [P] [US2] Update check_feature_branch() validation regex and error messages for dual format in .specify/scripts/bash/common.sh (line 75)
- [x] T010 [P] [US2] Update find_feature_dir_by_prefix() prefix extraction for dual format in .specify/scripts/bash/common.sh (line 94)

### Branch Creation Tasks

- [x] T011 [US2] Add config file detection logic in .specify/scripts/bash/create-new-feature.sh (check if .specify/config.json exists)
- [x] T012 [US2] Call read_config_prefix() to get LINEAR_PREFIX or default to legacy mode in .specify/scripts/bash/create-new-feature.sh (line 131-135)
- [x] T013 [US2] Update branch name generation logic for custom format (PREFIX-NUMBER-description) in .specify/scripts/bash/create-new-feature.sh (line 213-214)
- [x] T014 [US2] Preserve legacy branch name generation (001-description) when no config exists in .specify/scripts/bash/create-new-feature.sh
- [x] T015 [US3] Verify spec directory naming matches branch name (already inherits from BRANCH_NAME variable) in .specify/scripts/bash/create-new-feature.sh (line 243)

### Manual Testing Checklist

- [ ] Create branch with AFR config → Verify AFR-001-name format
- [ ] Create branch without config → Verify 001-name legacy format
- [ ] Create multiple branches → Verify sequential numbering (AFR-001, AFR-002, etc.)
- [ ] Test with different prefixes (ASR, PROJ, AUROR) → Verify all work
- [ ] Test mixed repo (old + new branches) → Verify no conflicts
- [ ] Verify spec directories match branch names exactly

**Exit Criteria**: Branches and spec directories use configured format, with backward compatibility for legacy projects

---

## Phase 4: User Story 4-5 - Documentation (P3)

**Goal**: Document custom format feature for users and provide multi-team examples

**Why P3**: Important for adoption but not blocking - feature works without documentation updates

**Combined User Stories**: US4 (commit conventions) and US5 (multi-team usage) both involve documentation updates.

**Independent Test Criteria**:
```bash
# Test 1: README completeness
grep -i "linear ticket" README.md
# Verify: Section exists with AFR, ASR, AUROR examples

# Test 2: Constitution completeness
grep -i "linear" .specify/templates/constitution-template.md
# Verify: Naming conventions documented

# Test 3: Example clarity
# Manual review: Examples are copy-pasteable and clear
```

### Documentation Tasks

- [x] T016 [P] [US5] Add "Linear Ticket Configuration" section to README.md with feature overview
- [x] T017 [P] [US5] Add multi-team examples (AFR, ASR, AUROR) to README.md showing different prefixes in action
- [x] T018 [P] [US4] Document branch naming convention (PREFIX-NUMBER-description) with examples in README.md
- [x] T019 [P] [US4] Document commit message format (PREFIX-NUMBER Description) with examples in README.md
- [x] T020 [P] [US5] Update .specify/memory/constitution.md with Linear format naming conventions (Principle VII and Branch Management sections)
- [x] T021 [P] [US4] Add troubleshooting section to README.md for common format issues (invalid input, config missing, etc.)

### Manual Testing Checklist

- [ ] README includes at least 3 team examples (AFR, ASR, AUROR)
- [ ] Branch naming convention clearly documented with examples
- [ ] Commit format clearly documented with examples
- [ ] Constitution template has Linear format section
- [ ] Troubleshooting section covers common issues
- [ ] All examples are copy-pasteable and syntactically correct

**Exit Criteria**: Documentation is complete, clear, and includes multi-team examples

---

## Phase 5: Integration & Testing

**Goal**: Verify end-to-end workflows, backward compatibility, and all success criteria

**Manual Testing**: This feature uses manual testing per the plan (Python/Bash code, not .NET xUnit)

### Integration Testing Tasks

- [ ] T022 Execute all 6 testing scenarios from spec.md (new project default, new project custom, legacy project, mixed repo, invalid input, config persistence)
- [ ] T023 Verify all 7 success criteria from spec.md are met (SC-001 through SC-007)

### Testing Scenarios (from spec.md)

**Scenario 1: New project with default format**
```bash
specify init test-default
# Prompt: [Enter]
# Expected: AUROR prefix used
# Verify: cat .specify/config.json shows "AUROR"
```

**Scenario 2: New project with custom format**
```bash
specify init test-custom
# Prompt: AFR
# Expected: AFR prefix used
# Verify: cat .specify/config.json shows "AFR"
```

**Scenario 3: Legacy project (no config)**
```bash
# In repo without .specify/config.json
.specify/scripts/bash/create-new-feature.sh "Test"
# Expected: Branch created as 001-test (legacy format)
# Verify: Branch name matches legacy pattern
```

**Scenario 4: Mixed repository**
```bash
# Create old branch: 001-old-feature
# Create config with AFR
# Create new branch: AFR-001-new-feature
# Expected: Both formats coexist without errors
# Verify: Both branches work in all scripts
```

**Scenario 5: Invalid input handling**
```bash
specify init test-invalid
# Prompt: AFR-123 (invalid)
# Expected: Error message, re-prompt
# Verify: User sees "Invalid format. Use letters only (e.g., AFR, ASR, PROJ)"
```

**Scenario 6: Config persistence**
```bash
specify init test-persist
# Prompt: AFR
# Close terminal, reopen
.specify/scripts/bash/create-new-feature.sh "Test"
# Expected: Uses AFR prefix (config persists)
# Verify: Branch created as AFR-001-test
```

### Success Criteria Validation (from spec.md)

- [ ] **SC-001**: Teams can configure format in <1 minute with clear prompts
- [ ] **SC-002**: 100% format consistency in branches and specs
- [ ] **SC-003**: Config persists across terminal sessions
- [ ] **SC-004**: 100% invalid input rejection (validation works)
- [ ] **SC-005**: Documentation has 3+ team examples
- [ ] **SC-006**: Zero breaking changes for legacy projects
- [ ] **SC-007**: Clear error messages reduce confusion

**Exit Criteria**: All scenarios pass, all success criteria met, no regressions

---

## Parallel Execution Opportunities

### Within User Story 1 (US1)
**None** - CLI tasks must be sequential (prompt → validate → save → confirm)

### Within User Story 2-3 (US2-US3)
**High parallelization** - Multiple developers can work simultaneously:

**Developer A** (common.sh):
- T007 (config reader)
- T008 (get_current_branch)
- T009 (check_feature_branch)
- T010 (find_feature_dir_by_prefix)

**Developer B** (create-new-feature.sh):
- T011 (config detection)
- T012 (read config)
- T013 (custom format logic)
- T014 (legacy format logic)
- T015 (spec directory verification)

**Coordination Point**: Both developers need T007 (read_config_prefix) implemented first, but can work on other tasks in parallel.

### Within User Story 4-5 (US4-US5)
**Full parallelization** - All documentation tasks are independent:

**Developer A**:
- T016, T017, T018, T019, T021 (README updates)

**Developer B**:
- T020 (Constitution template update)

---

## File Change Summary

| File | User Story | Lines Changed | Tasks |
|------|-----------|---------------|-------|
| `src/specify_cli/__init__.py` | US1 | ~40 | T002-T006 |
| `.specify/scripts/bash/common.sh` | US2-US3 | ~30 | T007-T010 |
| `.specify/scripts/bash/create-new-feature.sh` | US2-US3 | ~60 | T011-T015 |
| `README.md` | US4-US5 | ~50 | T016-T019, T021 |
| `.specify/templates/constitution-template.md` | US4-US5 | ~30 | T020 |

**Total**: ~210 lines of changes across 5 files

---

## Implementation Notes

### Code Review Checkpoints

**After US1 (T002-T006)**:
- Config file format is correct (minimal JSON with only linear_ticket_prefix)
- Validation rejects all invalid inputs
- Error messages are clear and helpful
- Non-interactive mode defaults to AUROR

**After US2-US3 (T007-T015)**:
- Regex patterns match both old and new formats correctly
- Config reader has jq fallback for portability
- Legacy projects continue working (backward compatibility)
- Branch and spec naming are consistent

**After US4-US5 (T016-T021)**:
- All examples are syntactically correct and copy-pasteable
- At least 3 team examples provided (AFR, ASR, AUROR)
- Troubleshooting section covers common issues
- Documentation is clear for non-technical users

### Risk Mitigation

**High Risk Items**:
1. **Regex changes in common.sh** (T008-T010)
   - **Mitigation**: Test with sample branch names before committing
   - **Validation**: Create test script with old and new format examples

2. **Backward compatibility** (T014)
   - **Mitigation**: Extensive testing with repos that have no config
   - **Validation**: Ensure 001- format still works

**Medium Risk Items**:
1. **Config file corruption** (T005)
   - **Mitigation**: Validate JSON before writing
   - **Validation**: Test with malformed config, verify graceful fallback

2. **Cross-platform compatibility** (T007)
   - **Mitigation**: Use jq with grep/sed fallback
   - **Validation**: Test on macOS and Linux

---

## Next Steps After Completion

1. **Commit changes**: Follow format `001 Implement custom Linear ticket format`
2. **Create PR**: Title "Custom Linear Ticket Format Configuration"
3. **Manual testing**: Run through all 6 scenarios before requesting review
4. **Documentation review**: Have team lead review README and constitution updates
5. **Rollout**: Start with Auror Facial Recognition team (AFR prefix)

---

**Tasks Ready for Implementation** | Use `/speckit.implement` to begin execution
