# Guard CLI Plan Update - Bridging the Gap

**Date**: 2025-10-19  
**Status**: Implementation 34% complete, needs clarification and workflow integration

## Analysis Findings

Based on `/analyze` output:
- **33/96 tasks marked complete** (34%) but actual implementation ~43/96 (45%)
- **All 5 MVP guard types functional** but tasks.md is stale
- **18/18 unit tests passing**
- **CRITICAL**: Guard CLI works but isn't integrated into Spec Kit workflows per Constitution Principle V

## Problem Clarification

You've identified two problems correctly:

### Problem 1: Guard CLI Implementation (THIS FEATURE)
Complete the guard CLI and integrate it into Spec Kit workflows so guards become a natural part of spec-driven development.

### Problem 2: Spec Kit Upgrade Model (SEPARATE FEATURE)
Create a mechanism to upgrade Spec Kit files in existing repos when CLI version != project version. **This is out of scope for guard CLI feature.**

**Decision**: Focus on Problem 1. Problem 2 should be a separate feature specification.

## What Guards Are (Clarified)

**Guards are CLI tools** provided by the `specify-cli` uv package:

```bash
# Install Spec Kit CLI
uv tool install specify-cli

# Guards become available as subcommands
specify guard types              # Discover guard types
specify guard create --type api  # Bootstrap test code
specify guard run G001          # Execute validation
specify guard list              # See all guards
```

**Guards are NOT**:
- Templates to fill in (they generate 200+ lines of working code)
- IDE-specific (they're CLI commands, any agent can use them)
- Optional (Constitution mandates them)

**Guards ARE**:
- Test bootstrapping tools (generate complete pytest/playwright/etc. code)
- Hard completion boundaries (exit 0 = pass, task can complete)
- Planning-phase artifacts (defined during `/tasks`, executed during `/implement`)
- Objec tive validation (no "looks good to me")

## Workflow Integration Gap

**Current Reality**:
- Guards work as standalone CLI commands ✓
- Constitution requires guards in workflow ✓
- Workflow templates DON'T reference guards ✗

**Constitutional Violation**:
Principle V states:
> "Guards MUST be generated during planning phase via `specify guard` command"
> "Guard IDs MUST be registered alongside tasks in tasks.md"
> "AI agents MUST execute guards before marking tasks complete"

But the `/tasks` and `/implement` command templates don't do this.

## Required Workflow Integration

### 1. `/tasks` Command Integration

**File**: `templates/commands/tasks.md`

**Add Step 4.5** (after task generation, before output):

```markdown
## Step 4.5: Suggest Guards for Critical Tasks

For each user story, identify validation checkpoints and suggest guards:

1. Scan functional requirements for validation needs:
   - API endpoints → suggest `specify guard create --type api --name <endpoint>`
   - Database changes → suggest `specify guard create --type database --name <migration>`
   - UI workflows → suggest `specify guard create --type docker-playwright --name <flow>`
   - Business logic → suggest `specify guard create --type unit-pytest --name <component>`
   - Code quality → suggest `specify guard create --type lint-ruff --name <module>`

2. Output guard creation commands in tasks.md:
   ```markdown
   ## Guards for User Story 1
   
   Create these guards during implementation:
   - `specify guard create --type api --name user-auth` → G001
   - `specify guard create --type unit-pytest --name session-logic` → G002
   
   Tasks with guard validation:
   - [ ] T012 [US1] Implement /auth/login endpoint [Guard: G001]
   - [ ] T015 [US1] Implement session management [Guard: G002]
   ```

3. Register guard IDs inline with tasks using `[Guard: G###]` marker
```

### 2. `/implement` Command Integration

**File**: `templates/commands/implement.md`

**Update Step 8** (task completion):

```markdown
## Step 8: Task Completion with Guard Validation

Before marking any task as [X]:

1. Check for guard marker in task description:
   ```regex
   \[Guard: (G\d{3})\]
   ```

2. If guard marker found:
   a. Execute guard: `specify guard run G###`
   b. Check exit code:
      - Exit 0 → Mark task [X], proceed
      - Non-zero → Report failure, suggest fixes, do NOT mark complete
   c. Update task with guard status:
      ```markdown
      - [X] T012 [US1] Implement endpoint [Guard: G001 ✓]
      ```

3. If no guard marker:
   - Proceed with normal completion (mark [X])
   - Consider if guard should have been created
```

### 3. `/plan` Command Integration

**File**: `templates/commands/plan.md`

**Update Constitution Check** for Principle V:

```markdown
**Guard-Driven Task Validation (Principle V)**:
- [ ] Critical validation checkpoints identified from functional requirements
- [ ] Guard types selected for each checkpoint (api, database, docker-playwright, unit-pytest, lint-ruff)
- [ ] Guard creation plan documented (which guards for which tasks)
- [ ] Guard execution workflow defined (when guards run, what happens on failure)
- [ ] Guards will be suggested in `/tasks` command output
- [ ] Guards will be validated in `/implement` command before task completion
```

## Implementation Tasks (Missing from Original Plan)

Add these tasks to complete workflow integration:

### Phase 8: Workflow Integration (NEW)

- [ ] T090 [WF] Update templates/commands/tasks.md to add guard suggestion step (Step 4.5)
- [ ] T091 [WF] Update templates/commands/implement.md to add guard validation before completion (Step 8)
- [ ] T092 [WF] Update templates/commands/plan.md constitution check for Principle V
- [ ] T093 [WF] Create example workflow showing guard integration end-to-end
- [ ] T094 [WF] Test workflow: Create sample feature, verify guards suggested in /tasks
- [ ] T095 [WF] Test workflow: Implement sample feature, verify guards validated in /implement
- [ ] T096 [WF] Document guard workflow in main README.md

### Phase 9: Documentation & Polish (EXPANDED)

- [ ] T097 Add guard CLI usage to main README.md with examples
- [ ] T098 Create docs/guards.md explaining guard system architecture
- [ ] T099 Add troubleshooting section for common guard issues
- [ ] T100 Verify all 5 guard types have README.md and examples/
- [ ] T101 Run integration tests end-to-end
- [ ] T102 Update CHANGELOG.md for guard CLI feature
- [ ] T103 Tag release with guard system

## Success Criteria Update

**Original SC-008**: At least 5 core guard types implemented and functional ✓ DONE

**New Criteria**:
- **SC-009**: Guards automatically suggested during `/tasks` command execution
- **SC-010**: Guards automatically validated during `/implement` command execution
- **SC-011**: Constitution Principle V fully enforced through workflow templates
- **SC-012**: End-to-end workflow test passes (create feature → plan → tasks → implement with guards)

## Next Steps

1. **Update tasks.md** to reflect actual implementation state (mark T021-T034 complete)
2. **Add Phase 8 tasks** (workflow integration)
3. **Implement template updates** for `/tasks`, `/implement`, `/plan` commands
4. **Test end-to-end** workflow with guard integration
5. **Document** guard system comprehensively

## Note on Problem 2 (Spec Kit Upgrades)

The "upgrade Spec Kit files when versions differ" problem is real but **separate**:

**Proposal**: Create new feature `002-speckit-upgrade` with:
- Detect Spec Kit CLI version vs. project Spec Kit file version
- Compare templates (constitution, commands, etc.)
- Offer upgrade: "Spec Kit v0.0.21 detected, project uses v0.0.20. Upgrade? (y/n)"
- Safely merge changes (preserve customizations, update standard sections)
- Version pin in project metadata

This deserves its own spec, plan, and implementation cycle.

## Recommendation

**For Guard CLI Feature**:
1. Complete workflow integration (Phase 8 tasks above)
2. Update existing templates to reference guards
3. Test end-to-end to ensure Constitution Principle V is enforced
4. Document guard workflow thoroughly

**For Spec Kit Upgrade Feature**:
1. Create separate `002-speckit-upgrade` spec
2. Design upgrade mechanism (version detection, safe merging, testing)
3. Implement after guard CLI is complete and stable

**Do NOT** mix these two features in one implementation cycle.
