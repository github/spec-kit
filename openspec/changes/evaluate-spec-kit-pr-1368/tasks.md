# Tasks: Evaluate Spec-Kit PR #1368

**Change ID:** `evaluate-spec-kit-pr-1368`  
**Phase:** Implementation  
**Date:** 2026-01-04

---

## Task Organization

Tasks are organized by phase and include dependency markers:

- **[P]** = Can be parallelized with other [P] tasks
- **[D: Task #]** = Depends on completion of specified task(s)
- **Checkpoint** = Validation point before proceeding

---

## Phase 1: Preparation & Analysis

### Task 1.1: Set Up Working Environment

**File:** N/A (repository setup)  
**Dependencies:** None  
**Description:** Create isolated testing environment for PR evaluation

**Steps:**

1. Confirm working branch `feat/evaluate-spec-kit-pr-1368` is active
2. Create backup of current spec-kit installation
3. Document current spec-kit version/commit hash
4. Set up testing directories

**Acceptance Criteria:**

- ✅ Working branch created and checked out
- ✅ Backup of `/frameworks/spec-kit` created
- ✅ Current version documented

**Estimated Time:** 15 minutes

---

### Task 1.2: Download PR Patches

**File:** N/A (external download)  
**Dependencies:** None  
**Parallel:** [P] with Task 1.3  
**Description:** Fetch PR patch files for analysis and application

**Steps:**

1. Download patch file: `curl -L https://github.com/github/spec-kit/pull/1368.patch -o /tmp/pr-1368.patch`
2. Download diff file: `curl -L https://github.com/github/spec-kit/pull/1368.diff -o /tmp/pr-1368.diff`
3. Verify download integrity (check file sizes, content)

**Acceptance Criteria:**

- ✅ Patch files downloaded successfully
- ✅ Files contain expected PR content
- ✅ Both commits (f3ba03e and a8c6570) are present

**Estimated Time:** 5 minutes

---

### Task 1.3: Install Required Tools

**File:** N/A (system setup)  
**Dependencies:** None  
**Parallel:** [P] with Task 1.2  
**Description:** Ensure all testing tools are available

**Steps:**

1. Verify `shellcheck` is installed: `shellcheck --version`
2. If not installed: `sudo apt-get install shellcheck` (or equivalent)
3. Verify Python 3.11+: `python --version`
4. Verify `uv` package manager: `uv --version`

**Acceptance Criteria:**

- ✅ shellcheck available and version >= 0.7.0
- ✅ Python version >= 3.11
- ✅ uv package manager functional

**Estimated Time:** 10 minutes

---

### **Checkpoint 1:** Preparation Complete

- [ ] Working environment set up
- [ ] PR patches downloaded
- [ ] Required tools installed

---

## Phase 2: Static Code Analysis

### Task 2.1: Analyze Patch Content

**File:** `/tmp/pr-1368.patch`  
**Dependencies:** [D: 1.2]  
**Description:** Detailed analysis of all changes in the PR

**Steps:**

1. Review each of the 10 modified files
2. Document all code changes (additions, deletions, modifications)
3. Identify potential issues or inconsistencies
4. Create analysis report

**Acceptance Criteria:**

- ✅ All 10 files reviewed
- ✅ Changes categorized by type (config, docs, scripts)
- ✅ Initial issue list created

**Estimated Time:** 30 minutes

---

### Task 2.2: Validate Bash Scripts

**File:** `scripts/bash/update-agent-context.sh`  
**Dependencies:** [D: 1.3, 2.1]  
**Parallel:** [P] with Tasks 2.3, 2.4  
**Description:** Run shellcheck on modified bash scripts

**Steps:**

1. Extract modified bash script sections from patch
2. Run: `shellcheck scripts/bash/update-agent-context.sh` (after applying patch)
3. Run: `shellcheck .github/workflows/scripts/create-release-packages.sh`
4. Run: `shellcheck .github/workflows/scripts/create-github-release.sh`
5. Document any warnings or errors

**Acceptance Criteria:**

- ✅ shellcheck runs successfully on all scripts
- ✅ No critical errors found
- ✅ Any warnings documented and assessed

**Estimated Time:** 15 minutes

---

### Task 2.3: Validate PowerShell Scripts

**File:** `scripts/powershell/update-agent-context.ps1`  
**Dependencies:** [D: 2.1]  
**Parallel:** [P] with Tasks 2.2, 2.4  
**Description:** Validate PowerShell syntax (if PowerShell available)

**Steps:**

1. Check if PowerShell is available: `pwsh --version`
2. If available, validate syntax:
   - `pwsh -NoProfile -Command "Get-Content scripts/powershell/update-agent-context.ps1 | Out-Null"`
   - `pwsh -NoProfile -Command "Get-Content .github/workflows/scripts/create-release-packages.ps1 | Out-Null"`
3. Document any syntax errors

**Acceptance Criteria:**

- ✅ PowerShell syntax validated (or marked N/A if not available)
- ✅ No syntax errors found
- ✅ Script structure consistent with bash version

**Estimated Time:** 15 minutes

---

### Task 2.4: Validate Python Configuration

**File:** `src/specify_cli/__init__.py`  
**Dependencies:** [D: 2.1]  
**Parallel:** [P] with Tasks 2.2, 2.3  
**Description:** Validate Python syntax and configuration structure

**Steps:**

1. Extract AGENT_CONFIG changes from patch
2. Verify dictionary syntax is valid Python
3. Check for typos in keys, values
4. Compare structure with existing agents (cursor-agent, windsurf, bob)
5. Validate `requires_cli: False` is correct for IDE-based agent

**Acceptance Criteria:**

- ✅ Python syntax is valid
- ✅ `AGENT_CONFIG["antigravity"]` structure matches pattern
- ✅ No typos in configuration keys
- ✅ IDE-based classification confirmed correct

**Estimated Time:** 15 minutes

---

### Task 2.5: Directory Path Analysis

**File:** Multiple (see detailed list in proposal)  
**Dependencies:** [D: 2.1]  
**Description:** **CRITICAL** - Analyze directory path inconsistency issue

**Steps:**

1. Document all directory paths referenced across files:
   - AGENTS.md: `.agent/workflows/`
   - create-release-packages.sh: `.agent/workflows/`
   - create-release-packages.ps1: `.agent/workflows/`
   - update-agent-context.sh: `.agent/rules/specify-rules.md`
   - update-agent-context.ps1: `.agent/rules/specify-rules.md`
2. Compare with pattern used by similar IDE agents:
   - Windsurf: `.windsurf/workflows/` (docs) and `.windsurf/rules/specify-rules.md` (scripts)
   - Cursor: `.cursor/commands/` (docs) and `.cursor/rules/specify-rules.mdc` (scripts)
   - IBM Bob: (research actual paths)
3. Determine correct resolution
4. Create fix specification

**Acceptance Criteria:**

- ✅ All directory references documented
- ✅ Inconsistency confirmed and impact assessed
- ✅ Resolution approach defined (align all to `.agent/workflows/` or use dual structure)
- ✅ Fix specification created

**Estimated Time:** 30 minutes

---

### **Checkpoint 2:** Static Analysis Complete

- [ ] All scripts validated
- [ ] Python configuration checked
- [ ] Directory path issue fully analyzed and fix designed

---

## Phase 3: Patch Application & Issue Resolution

### Task 3.1: Apply PR Patch to Spec-Kit

**File:** `/frameworks/spec-kit/` (10 files modified)  
**Dependencies:** [D: Checkpoint 2]  
**Description:** Apply the PR patch to local spec-kit installation

**Steps:**

1. Navigate to spec-kit directory
2. Create backup: `cp -r /frameworks/spec-kit /tmp/spec-kit-backup-$(date +%Y%m%d)`
3. Apply patch: `git apply --check /tmp/pr-1368.patch` (dry run)
4. If dry run succeeds: `git apply /tmp/pr-1368.patch`
5. Verify all 10 files modified correctly
6. Review git diff to confirm changes match PR

**Acceptance Criteria:**

- ✅ Patch applies cleanly without conflicts
- ✅ All 10 files modified as expected
- ✅ Git diff matches PR content
- ✅ No unexpected changes introduced

**Estimated Time:** 15 minutes

---

### Task 3.2: Create Directory Path Fix

**File:** `scripts/bash/update-agent-context.sh`, `scripts/powershell/update-agent-context.ps1`  
**Dependencies:** [D: 2.5, 3.1]  
**Description:** Implement fix for directory path inconsistency

**Approach:** Based on Task 2.5 analysis, implement chosen resolution

**Option A: Single Workflow-Based Structure** (if analysis recommends)

```bash
# Change scripts to use .agent/workflows/ instead of .agent/rules/
ANTIGRAVITY_FILE="$REPO_ROOT/.agent/workflows/specify-rules.md"
```

**Option B: Dual Structure** (match Windsurf/Cursor pattern)

- Keep `.agent/workflows/` for command files
- Use `.agent/rules/specify-rules.md` for agent instructions
- Update release scripts to generate both directories

**Steps:**

1. Implement chosen resolution in bash script
2. Mirror changes in PowerShell script
3. Update any affected documentation
4. Test directory creation logic

**Acceptance Criteria:**

- ✅ Scripts use consistent, correct paths
- ✅ Path selection matches established agent patterns
- ✅ Both bash and PowerShell scripts aligned
- ✅ Documentation updated to reflect correct structure

**Estimated Time:** 20 minutes

---

### Task 3.3: Validate Applied Changes

**File:** All modified files  
**Dependencies:** [D: 3.1, 3.2]  
**Description:** Comprehensive review of applied patch plus fixes

**Steps:**

1. Review each modified file in spec-kit
2. Verify version bump (0.0.22 → 0.0.23)
3. Check CHANGELOG entry format and content
4. Confirm all agent lists updated consistently
5. Validate directory path fix is complete
6. Run: `git diff` and review all changes

**Acceptance Criteria:**

- ✅ All changes reviewed and verified correct
- ✅ No merge artifacts or corruption
- ✅ Directory path fix properly integrated
- ✅ Ready for integration testing

**Estimated Time:** 20 minutes

---

### **Checkpoint 3:** Patch Applied and Fixed

- [ ] PR patch successfully applied
- [ ] Directory path issue resolved
- [ ] All changes validated

---

## Phase 4: Integration Testing (Linux/Bash)

### Task 4.1: Test Fresh Installation

**File:** N/A (command execution)  
**Dependencies:** [D: Checkpoint 3]  
**Description:** Test `specify init` with Antigravity agent

**Steps:**

1. Create clean test directory: `mkdir -p /tmp/test-antigravity && cd /tmp/test-antigravity`
2. Run: `specify init test-project --ai antigravity --script sh --debug`
3. Observe output for errors or warnings
4. Verify directory structure created:
   - `.agent/` directory exists
   - `.agent/workflows/` directory exists
   - Workflow files (`.md`) generated
5. Verify `.agent/rules/` if dual structure (check specify-rules.md exists)
6. Check file permissions (should be readable/executable as appropriate)
7. Review generated workflow file content

**Acceptance Criteria:**

- ✅ `specify init` completes successfully
- ✅ `.agent/` directory structure created correctly
- ✅ Workflow files generated with correct format
- ✅ No errors or warnings in output
- ✅ File permissions correct
- ✅ Generated files contain valid markdown and speckit commands

**Estimated Time:** 20 minutes

---

### Task 4.2: Test Context Update Script (Bash)

**File:** `scripts/bash/update-agent-context.sh`  
**Dependencies:** [D: 4.1]  
**Description:** Test agent context update for Antigravity

**Steps:**

1. Navigate to spec-kit directory (or test project from 4.1)
2. Run explicit update: `./scripts/bash/update-agent-context.sh antigravity`
3. Verify script completes without errors
4. Check that `.agent/rules/specify-rules.md` (or correct path) is created/updated
5. Review file content for completeness
6. Test "update all" mode: `./scripts/bash/update-agent-context.sh` (no args)
7. Verify Antigravity is included in "all" update

**Acceptance Criteria:**

- ✅ Script runs successfully for `antigravity` argument
- ✅ Agent file created in correct location
- ✅ File content is complete and properly formatted
- ✅ "Update all" mode includes Antigravity
- ✅ No script errors or warnings

**Estimated Time:** 15 minutes

---

### Task 4.3: Test Release Package Generation (Bash)

**File:** `.github/workflows/scripts/create-release-packages.sh`  
**Dependencies:** [D: Checkpoint 3]  
**Parallel:** [P] with Task 4.2  
**Description:** Verify Antigravity template package creation

**Note:** This may require mock release environment or may skip if environment unavailable

**Steps:**

1. Attempt to run package script (may need ENV setup):
   ```bash
   VERSION="0.0.23-test" ./.github/workflows/scripts/create-release-packages.sh \
     --agents antigravity --scripts sh
   ```
2. If environment allows, verify package created in `.genreleases/`
3. Extract and inspect package contents:
   - Correct directory structure (`.agent/workflows/`)
   - Workflow files present
   - Proper naming convention
4. Document any missing dependencies or environment issues

**Acceptance Criteria:**

- ✅ Script executes (or skip rationale documented)
- ✅ Package created with correct naming: `spec-kit-template-antigravity-sh-VERSION.zip`
- ✅ Package contents verified (or marked as ENV limitation)
- ✅ Any issues documented for future reference

**Estimated Time:** 20 minutes (or 5 min if skipped due to ENV)

---

### Task 4.4: Test Specify Check Command

**File:** `src/specify_cli/__init__.py`  
**Dependencies:** [D: 3.1]  
**Parallel:** [P] with Tasks 4.2, 4.3  
**Description:** Verify `specify check` command includes Antigravity

**Steps:**

1. Run: `specify check`
2. Review output for agent tool checks
3. Verify Antigravity is NOT checked (it's IDE-based, `requires_cli: False`)
4. Confirm output matches expectation (should not show "antigravity CLI not found")

**Acceptance Criteria:**

- ✅ `specify check` runs successfully
- ✅ Antigravity correctly treated as IDE-based (no CLI check)
- ✅ Other agents checked correctly
- ✅ Command output clear and accurate

**Estimated Time:** 5 minutes

---

### **Checkpoint 4:** Linux Integration Tests Complete

- [ ] Fresh installation tested
- [ ] Context update script validated
- [ ] Release package generation verified (or skip rationale documented)
- [ ] Check command tested

---

## Phase 5: Regression & Comparison Testing

### Task 5.1: Test Existing Agents

**File:** N/A (system test)  
**Dependencies:** [D: Checkpoint 4]  
**Description:** Verify no regressions in existing agent support

**Steps:**

1. Test Claude agent: `specify init /tmp/test-claude --ai claude --script sh`
2. Test Gemini agent: `specify init /tmp/test-gemini --ai gemini --script sh`
3. Test Copilot agent: `specify init /tmp/test-copilot --ai copilot --script sh`
4. Test Cursor agent: `specify init /tmp/test-cursor --ai cursor-agent --script sh`
5. Verify each completes successfully
6. Spot-check directory structures for each

**Acceptance Criteria:**

- ✅ All tested agents initialize correctly
- ✅ No errors or warnings introduced by Antigravity changes
- ✅ Existing functionality intact
- ✅ No broken references or imports

**Estimated Time:** 15 minutes

---

### Task 5.2: Compare Implementation Patterns

**File:** Multiple (comparative analysis)  
**Dependencies:** [D: 4.1]  
**Description:** Validate Antigravity matches IDE-based agent patterns

**Steps:**

1. Compare Antigravity with Windsurf (both IDE-based):
   - Directory structure: `.agent/` vs `.windsurf/`
   - File formats: both Markdown
   - Arg format: `$ARGUMENTS` (verify)
   - `requires_cli: False` for both
2. Compare with Cursor:
   - Directory: `.cursor/commands/` vs `.agent/workflows/`
   - Rules file: `.cursor/rules/specify-rules.mdc` vs `.agent/rules/specify-rules.md`
3. Compare with IBM Bob (IDE-based)
4. Document any significant deviations or consistency issues

**Acceptance Criteria:**

- ✅ Pattern analysis completed for all relevant agents
- ✅ Antigravity follows established IDE-based conventions
- ✅ Any deviations documented with rationale
- ✅ Consistency report created

**Estimated Time:** 20 minutes

---

### Task 5.3: Documentation Accuracy Review

**File:** `README.md`, `AGENTS.md`, `CHANGELOG.md`  
**Dependencies:** [D: 3.3]  
**Description:** Verify all documentation is accurate and complete

**Steps:**

1. Review README.md:
   - Supported agents table includes Antigravity
   - `--ai` option lists antigravity
   - `check` command description includes antigravity
   - Examples updated if needed
2. Review AGENTS.md:
   - Table entry correct (Antigravity IDE, `.agent/workflows/`, Markdown, N/A (IDE-based))
   - Help text updated
   - Agent addition instructions reference Antigravity correctly
3. Review CHANGELOG.md:
   - Version 0.0.23 entry present
   - Date correct (2025-12-21)
   - Description accurate

**Acceptance Criteria:**

- ✅ All documentation accurate
- ✅ No orphaned references to old names or paths
- ✅ Consistent terminology throughout
- ✅ CHANGELOG follows format conventions

**Estimated Time:** 15 minutes

---

### **Checkpoint 5:** Regression & Comparison Complete

- [ ] Existing agents tested (no regressions)
- [ ] Pattern consistency validated
- [ ] Documentation verified

---

## Phase 6: Windows/PowerShell Testing (Optional)

**Note:** These tasks can be skipped if Windows environment is unavailable. Mark as "ENV N/A" in that case.

### Task 6.1: Test Fresh Installation (PowerShell)

**File:** N/A  
**Dependencies:** [D: Checkpoint 5]  
**Description:** Test `specify init` with PowerShell variant

**Steps:**

1. Run on Windows: `specify init test-project --ai antigravity --script ps --debug`
2. Verify directory structure created correctly
3. Check workflow files generated
4. Compare with bash results for consistency

**Acceptance Criteria:**

- ✅ Installation succeeds on Windows (or marked ENV N/A)
- ✅ Directory structure matches bash variant
- ✅ Workflow files generated correctly

**Estimated Time:** 15 minutes (or mark ENV N/A)

---

### Task 6.2: Test Context Update Script (PowerShell)

**File:** `scripts/powershell/update-agent-context.ps1`  
**Dependencies:** [D: 6.1]  
**Description:** Test PowerShell agent context update

**Steps:**

1. Run: `.\scripts\powershell\update-agent-context.ps1 -AgentType antigravity`
2. Verify script completes successfully
3. Check agent file created/updated correctly
4. Test "update all" mode: `.\scripts\powershell\update-agent-context.ps1`

**Acceptance Criteria:**

- ✅ Script runs successfully (or marked ENV N/A)
- ✅ Behavior matches bash script
- ✅ Files created in correct locations

**Estimated Time:** 10 minutes (or mark ENV N/A)

---

### Task 6.3: Cross-Platform Consistency Check

**File:** N/A (comparative test)  
**Dependencies:** [D: 6.1, 6.2]  
**Description:** Verify bash and PowerShell produce identical results

**Steps:**

1. Compare directory structures created by bash vs PowerShell
2. Compare file contents (workflow files, rules files)
3. Verify same behavior for edge cases
4. Document any platform-specific differences

**Acceptance Criteria:**

- ✅ Bash and PowerShell produce equivalent results (or marked ENV N/A)
- ✅ Any differences documented and justified
- ✅ No functional discrepancies

**Estimated Time:** 10 minutes (or mark ENV N/A)

---

### **Checkpoint 6:** Windows Testing Complete (or Skipped)

- [ ] PowerShell installation tested (or ENV N/A)
- [ ] PowerShell scripts validated (or ENV N/A)
- [ ] Cross-platform consistency confirmed (or ENV N/A)

---

## Phase 7: Final Validation & Reporting

### Task 7.1: Create Test Results Summary

**File:** `/docs/docs-local/2026-01-04/spec-kit-pr-1368-test-results.md`  
**Dependencies:** [D: Checkpoint 6]  
**Description:** Compile comprehensive test results documentation

**Steps:**

1. Summarize all test phases and results
2. Document any issues found and resolutions
3. List any tests skipped with rationale
4. Provide recommendation: APPROVE, REJECT, or APPROVE WITH FIXES
5. Include evidence (screenshots, logs) as appropriate

**Acceptance Criteria:**

- ✅ Complete test summary created
- ✅ All phases documented
- ✅ Clear recommendation provided
- ✅ Supporting evidence included

**Estimated Time:** 30 minutes

---

### Task 7.2: Create Issue Report for Upstream

**File:** `/docs/docs-local/2026-01-04/spec-kit-pr-1368-upstream-feedback.md`  
**Dependencies:** [D: 7.1]  
**Description:** Document issues to report back to PR #1368

**Steps:**

1. List all issues identified:
   - Directory path inconsistency (critical)
   - Any other bugs or improvements found
2. Provide clear reproduction steps
3. Suggest fixes or code patches
4. Format as GitHub-friendly markdown for posting as PR comment

**Acceptance Criteria:**

- ✅ Issue report created with all findings
- ✅ Clear, actionable feedback provided
- ✅ Formatted for GitHub PR comment
- ✅ Professional and constructive tone

**Estimated Time:** 20 minutes

---

### Task 7.3: Document Local Modifications

**File:** `/frameworks/spec-kit/LOCAL_MODIFICATIONS.md`  
**Dependencies:** [D: 3.2]  
**Description:** Create record of our local changes vs upstream PR

**Steps:**

1. Document PR #1368 as base
2. List all fixes/modifications we applied
3. Provide commit hashes or patch files
4. Include rationale for each change
5. Note sync strategy for when upstream merges PR

**Acceptance Criteria:**

- ✅ All local modifications documented
- ✅ Clear diff from upstream PR
- ✅ Sync strategy defined
- ✅ Future maintainers can understand our changes

**Estimated Time:** 15 minutes

---

### Task 7.4: Update Framework Comparison Docs

**File:** `/docs/docs-local/2026-01-04/spec-kit-pr-1368-evaluation-report.md`  
**Dependencies:** [D: 7.1, 7.2, 7.3]  
**Description:** Create final evaluation report for project documentation

**Steps:**

1. Summarize the proposal
2. Document implementation process
3. Include test results summary
4. List key findings and decisions
5. Provide lessons learned
6. Archive in daily docs folder with timestamp

**Acceptance Criteria:**

- ✅ Comprehensive evaluation report created
- ✅ Follows project documentation standards (per user rules Rule #4)
- ✅ Includes all required sections:
  - Initial project state
  - Changes made
  - Summary of user's request
  - Reference files
- ✅ Archived in `/docs/docs-local/2026-01-04/`

**Estimated Time:** 30 minutes

---

### Task 7.5: Commit and Prepare for Merge

**File:** All modified files in repo  
**Dependencies:** [D: 7.4]  
**Description:** Prepare changes for potential merge to main

**Steps:**

1. Review all changes: `git status`, `git diff`
2. Stage changes: `git add openspec/ frameworks/spec-kit/ docs/`
3. Commit with descriptive message:

   ```
   feat: Evaluate and apply spec-kit PR #1368 (Antigravity support)

   - Applied PR #1368 patches to local spec-kit
   - Fixed directory path inconsistency (.agent/workflows/ vs .agent/rules/)
   - Comprehensive testing completed (Linux bash, static analysis)
   - Created OpenSpec proposal and tasks documentation
   - Generated evaluation report

   Fixes: Directory path mismatch in update-agent-context scripts
   Relates: upstream github/spec-kit#1368
   ```

4. Verify commit includes all expected files
5. DO NOT merge to main yet - await user approval

**Acceptance Criteria:**

- ✅ All changes committed to feature branch
- ✅ Commit message clear and descriptive
- ✅ No uncommitted changes remain
- ✅ Branch ready for review/merge
- ✅ NOT merged to main (awaiting approval per user rules Rule #7)

**Estimated Time:** 10 minutes

---

### **Checkpoint 7 (FINAL):** Evaluation Complete

- [ ] Test results documented
- [ ] Upstream feedback prepared
- [ ] Local modifications tracked
- [ ] Evaluation report created
- [ ] Changes committed to feature branch
- [ ] Ready for user approval and merge

---

## Summary Statistics

**Total Tasks:** 35 tasks across 7 phases  
**Estimated Total Time:** ~7.5 hours  
**Parallelizable Tasks:** 8 tasks can run in parallel  
**Critical Path Tasks:** 27 tasks  
**Environment-Dependent Tasks:** 3 tasks (Windows/PowerShell, may skip)

**Key Milestones:**

1. Preparation complete (~30 min)
2. Static analysis complete (~2 hours)
3. Patch applied and fixed (~1 hour)
4. Linux integration testing complete (~1.5 hours)
5. Regression testing complete (~1 hour)
6. Windows testing complete or skipped (~30 min or skip)
7. Final documentation and commit (~2 hours)

**Risk Areas:**

- Task 2.5: Directory path resolution (critical decision point)
- Task 3.1: Patch application (may have conflicts)
- Task 4.3: Release package testing (environment-dependent)
- Tasks 6.x: Windows testing (environment availability)

---

**Tasks Version:** 1.0  
**Last Updated:** 2026-01-04T20:45:59-04:00
